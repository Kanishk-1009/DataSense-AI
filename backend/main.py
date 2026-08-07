from io import BytesIO

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from backend.core.eda import run_eda
from backend.core.profiler import profile_dataset
from backend.core.validator import validate_csv


app = FastAPI(
    title="Smart Dataset Understanding Agent",
    version="0.1.0"
)


async def _read_uploaded_csv(file: UploadFile) -> pd.DataFrame:

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

    return df


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
    df = await _read_uploaded_csv(file)
    return profile_dataset(df)


@app.post("/eda")
async def eda_dataset(
    file: UploadFile = File(...),
    target: str = Form(None)
):
    df = await _read_uploaded_csv(file)
    return run_eda(df, target=target)