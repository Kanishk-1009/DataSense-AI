# Smart Dataset Understanding Agent

An automated dataset analysis system that combines deterministic Exploratory
Data Analysis (EDA) with LLM-based interpretation to help users understand
datasets before building machine learning models.

## Project Overview

The Smart Dataset Understanding Agent analyses uploaded CSV datasets and
produces structured insights — column metadata, missing-value patterns,
statistical outliers, correlation analysis, feature importance, data quality
scores, and ML task recommendations. The project is developed incrementally:
a deterministic profiling pipeline forms the shared input for both a
single-agent (LangChain) and a multi-agent (LangGraph) system, enabling a
fair and reproducible evaluation.

## Current Progress

* [x] M1 Project Setup
* [x] M2 CSV Ingestion & Profiling
* [x] M3 Deterministic EDA Engine
* [x] M4 Single-Agent Pipeline (LangChain + Ollama baseline)
* [x] M5 Multi-Agent Pipeline (LangGraph — 7 specialist nodes)
* [x] M6 Evaluation
* [ ] Frontend
* [ ] Research Experiments

## Features Implemented

**Deterministic EDA (M2 & M3)**

* CSV upload and validation through FastAPI
* Dataset profiling (rows, columns, dtypes, duplicates)
* Column type detection (numeric, categorical, binary, datetime)
* Missing value analysis with MCAR/MAR heuristic indicators
* Numeric statistics (mean, median, std, skewness, kurtosis, quartiles)
* Pearson correlation matrix + Cramér's V (categorical) + Point-Biserial (binary↔numeric)
* Outlier detection — IQR, Z-Score, and Isolation Forest (with consensus count)
* Target variable analysis and class distribution
* Feature importance — Random Forest + Mutual Information (ranked)
* Data quality score (0–100) with grade, strengths, and issues
* Rule-based preprocessing recommendations
* Unified per-run report
* Result persistence to `results/raw/` (timestamped, content-addressed JSON)

**Multi-Agent Pipeline (M5)**

* LangGraph `StateGraph` with parallel fan-out (Missing Value, Correlation, Outlier) and sequential fan-in
* 7 specialist nodes — each makes one focused LLM call on its own EDA slice
* `Annotated` reducers for safe concurrent state merging
* Critic/Synthesizer synthesises all specialist outputs into a unified `AgentResponse`
* `POST /analyze/multi-agent` endpoint
* Per-node timing (`per_node_time`) and total LLM call count (`llm_call_count`) tracked in `extra`
* Same `AgentResponse` schema as M4 — directly comparable
* Same persistence mechanism as M4

**Testing**

* All existing and newly added tests pass via `pytest`
* Tests cover every module including mocked LLM calls

## Project Structure

```text
smart-dataset-agent/
│
├── backend/
│   ├── agents/
│   │   ├── schemas.py               # Shared AgentResponse Pydantic model
│   │   ├── single_agent.py          # M4: LangChain single-agent pipeline
│   │   └── multi_agent/
│   │       ├── __init__.py
│   │       ├── state.py             # MultiAgentState TypedDict + reducers
│   │       ├── prompts.py           # Focused system prompts (7 agents)
│   │       ├── nodes.py             # 7 node functions
│   │       └── graph.py             # LangGraph assembly + run_multi_agent()
│   ├── core/
│   │   ├── eda/
│   │   │   ├── correlation.py       # Pearson + Cramér's V + Point-Biserial
│   │   │   ├── feature_importance.py # RF + Mutual Information
│   │   │   ├── missingness.py       # MCAR/MAR heuristic indicators
│   │   │   ├── outliers.py          # IQR + Z-Score + Isolation Forest
│   │   │   ├── quality_score.py
│   │   │   ├── preprocessing.py
│   │   │   ├── ml_task_detection.py
│   │   │   ├── ml_recommendation.py
│   │   │   ├── insights.py
│   │   │   ├── feature_summary.py
│   │   │   ├── report.py
│   │   │   └── engine.py
│   │   ├── persistence.py      # Save results to results/raw/
│   │   ├── profiler.py
│   │   └── validator.py
│   ├── evaluation/             # M6 controlled experiment framework
│   │   ├── evaluator.py        # run_evaluation() — M4 vs M5 on identical EDA
│   │   ├── metrics.py          # Metric scorers (structural/descriptive/…)
│   │   ├── rubric.py           # Ground-truth correctness rubric (M6-B)
│   │   ├── schemas.py          # PipelineMetrics / EvaluationResult
│   │   └── runner.py           # CLI runner (--dry-run supported)
│   ├── tests/                  # pytest suite (mocked LLM — no Ollama needed)
│   └── main.py
│
├── datasets/
│   ├── iris.csv
│   ├── wine.csv
│   ├── california_housing.csv
│   ├── titanic.csv
│   ├── adult_income.csv
│   └── test.csv
│
├── results/
│   ├── raw/      ← frozen experiment outputs (auto-generated)
│   └── metrics/  ← evaluation metrics (M6)
│
├── research/
├── README.md
├── pyproject.toml        # UV-managed project configuration
├── uv.lock               # Reproducible dependency lock (UV)
└── .gitignore
```

## Tech Stack

* Python 3.14 (managed by UV)
* FastAPI + Uvicorn
* Pandas, NumPy, SciPy, scikit-learn
* LangChain + langchain-ollama (Ollama backend)
* LangGraph
* Pytest

## Run Backend

The project is managed with [UV](https://docs.astral.sh/uv/). UV manages the
Python interpreter (3.14), the virtual environment, and all dependencies.

Install dependencies and create the environment:

```bash
uv sync
```

> UV installs a managed Python 3.14 interpreter automatically if one is not
> present on your machine.

Start the FastAPI server:

```bash
uv run uvicorn backend.main:app --reload
```

Open the interactive API docs:

```
http://127.0.0.1:8000/docs
```

## LLM requirement (Ollama)

The deterministic endpoints **do not require Ollama**:

| Endpoint | Requires Ollama? |
|---|---|
| `GET /` | No |
| `GET /health` | No |
| `POST /upload` | No |
| `POST /eda` | No |
| `POST /analyze/single-agent` | **Yes** — 1 LLM call |
| `POST /analyze/multi-agent` | **Yes** — 7 LLM calls |
| `POST /evaluate` | **Yes** — runs both agent pipelines |

If Ollama is **not** running, `/analyze/single-agent`, `/analyze/multi-agent`,
and `/evaluate` return `status: "error"` with a connection error — the EDA
result is still returned. Only the LLM interpretation is skipped. The FastAPI
process never crashes.

Install and start Ollama for the agent endpoints:

```bash
# https://ollama.com
ollama pull llama3.1:8b
ollama serve          # defaults to http://localhost:11434
```

The default model is `llama3.1:8b`. Override it (and the Ollama URL) per
request via the `model` and `ollama_url` form fields.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/health` | Health check |
| `POST` | `/upload` | CSV profiling (M2) |
| `POST` | `/eda` | Full deterministic EDA (M3) |
| `POST` | `/analyze/single-agent` | EDA + single LLM call (M4) |
| `POST` | `/analyze/multi-agent` | EDA + 7-node LangGraph pipeline (M5) |
| `POST` | `/evaluate` | M4 vs M5 controlled experiment (M6) |

All `POST` endpoints take a multipart `file` (CSV). The agent/evaluate
endpoints also accept optional `target`, `model`, and `ollama_url` form
fields.

## Run Tests

```bash
uv run pytest
```

All tests mock LLM calls, so they run **without Ollama**. The suite covers
every module plus FastAPI HTTP smoke tests (`/`, `/health`, `/upload`, `/eda`).

## Run the M6 Evaluation CLI

A dry-run (mocked LLM, no Ollama needed) validates the full evaluation
pipeline structure:

```bash
uv run python -m backend.evaluation.runner --csv datasets/titanic.csv --target Survived --dry-run
```

A real experiment requires Ollama:

```bash
uv run python -m backend.evaluation.runner --csv datasets/titanic.csv --target Survived
```

## Development Roadmap

### Next Steps

* Frontend for the API (upload → EDA → agent interpretation → evaluation dashboard)
* Research experiments comparing M4 vs M5 across benchmark datasets
* Explainability improvements for the multi-agent pipeline

## Research Goal

This project supports research on intelligent dataset understanding by
comparing deterministic analysis with AI-driven interpretation. A stable,
reproducible deterministic profiling pipeline serves as the common input
for both the single-agent and multi-agent systems, enabling a fair evaluation.
