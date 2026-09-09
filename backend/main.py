from io import BytesIO

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.core.eda import run_eda
from backend.core.profiler import profile_dataset
from backend.core.validator import validate_csv
from backend.agents.single_agent import run_single_agent
from backend.agents.multi_agent.graph import run_multi_agent
from backend.core.persistence import save_result
from backend.evaluation.evaluator import run_evaluation


# Development-friendly CORS: the frontend is not part of this repository yet,
# so every origin is allowed during local development.  Tighten this list to
# explicit origins before deploying to production.
ALLOWED_ORIGINS = ["*"]

app = FastAPI(
    title="Smart Dataset Understanding Agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _read_uploaded_csv(file: UploadFile) -> tuple[pd.DataFrame, bytes]:

    validate_csv(file)

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded CSV is empty."
            )

        df = pd.read_csv(BytesIO(contents))

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read CSV: {str(e)}"
        )

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Dataset contains no rows."
        )

    return df, contents


@app.get("/")
def root():
    return {
        "message": "Smart Dataset Understanding Agent API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    df, _ = await _read_uploaded_csv(file)
    return profile_dataset(df)


@app.post("/eda")
async def eda_dataset(
    file: UploadFile = File(...),
    target: str = Form(None)
):
    df, contents = await _read_uploaded_csv(file)

    eda_result = run_eda(df, target=target)

    try:
        save_result(
            pipeline="eda_only",
            csv_bytes=contents,
            eda_result=eda_result,
            metadata={"target": target, "filename": file.filename},
        )
    except Exception:
        pass  # persistence errors must never break the API response

    return eda_result


@app.post("/analyze/single-agent")
async def analyze_single_agent(
    file: UploadFile = File(...),
    target: str = Form(None),
    model: str = Form("llama3.1:8b"),
    ollama_url: str = Form("http://localhost:11434"),
):
    """
    Run the full EDA pipeline then interpret results with a single
    LangChain + Ollama LLM call.

    - **file**: CSV dataset to analyse.
    - **target**: Optional target column name for supervised analysis.
    - **model**: Ollama model to use (must be pulled locally).
    - **ollama_url**: URL of the running Ollama server.
    """
    df, contents = await _read_uploaded_csv(file)

    eda_result = run_eda(df, target=target)

    agent_result = run_single_agent(
        eda_result,
        model=model,
        base_url=ollama_url,
    )

    try:
        save_result(
            pipeline="single_agent",
            csv_bytes=contents,
            eda_result=eda_result,
            agent_result=agent_result,
            metadata={
                "target": target,
                "filename": file.filename,
                "model": model,
            },
        )
    except Exception:
        pass  # persistence errors must never break the API response

    return {
        "eda": eda_result,
        "agent": agent_result,
    }


@app.post("/analyze/multi-agent")
async def analyze_multi_agent(
    file: UploadFile = File(...),
    target: str = Form(None),
    model: str = Form("llama3.1:8b"),
    ollama_url: str = Form("http://localhost:11434"),
):
    """
    Run the full EDA pipeline then interpret results with the multi-agent
    LangGraph pipeline (7 specialist nodes + Critic/Synthesizer).

    Uses the **same EDA input as** ``/analyze/single-agent`` so results
    are directly comparable for research purposes.

    - **file**: CSV dataset to analyse.
    - **target**: Optional target column name for supervised analysis.
    - **model**: Ollama model to use (must be pulled locally).
    - **ollama_url**: URL of the running Ollama server.
    """
    df, contents = await _read_uploaded_csv(file)

    eda_result = run_eda(df, target=target)

    agent_result = run_multi_agent(
        eda_result,
        model=model,
        base_url=ollama_url,
        target=target,
    )

    try:
        save_result(
            pipeline="multi_agent",
            csv_bytes=contents,
            eda_result=eda_result,
            agent_result=agent_result,
            metadata={
                "target": target,
                "filename": file.filename,
                "model": model,
            },
        )
    except Exception:
        pass  # persistence errors must never break the API response

    return {
        "eda": eda_result,
        "agent": agent_result,
    }


@app.post("/evaluate")
async def evaluate_pipelines(
    file: UploadFile = File(...),
    target: str = Form(None),
    model: str = Form("llama3.1:8b"),
    ollama_url: str = Form("http://localhost:11434"),
):
    """
    M6 Controlled Experiment endpoint.

    Runs the full EDA pipeline **once**, then passes the identical EDA result
    to both the single-agent (M4) and multi-agent (M5) pipelines.  Returns a
    structured ``EvaluationResult`` with a per-metric comparison table.

    This is the primary research endpoint: it guarantees that both pipelines
    receive byte-for-byte identical input so that the pipeline architecture
    is the sole experimental variable.

    - **file**: CSV dataset to analyse.
    - **target**: Optional target column name for supervised analysis.
    - **model**: Ollama model to use (must be pulled locally).
    - **ollama_url**: URL of the running Ollama server.
    """
    df, contents = await _read_uploaded_csv(file)

    # EDA computed ONCE — same object passed to both pipelines
    eda_result = run_eda(df, target=target)

    eval_result = run_evaluation(
        eda_result=eda_result,
        dataset_name=file.filename or "unknown",
        csv_bytes=contents,
        model=model,
        base_url=ollama_url,
        target=target,
        persist=True,
    )

    return eval_result.model_dump()
