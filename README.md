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
* [ ] M6 Evaluation
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
│   ├── tests/
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
├── requirements.txt
└── .gitignore
```

## Tech Stack

* Python 3.14
* FastAPI + Uvicorn
* Pandas, NumPy, SciPy, scikit-learn
* LangChain + langchain-ollama (Ollama backend)
* Pytest

## Run Backend

Install dependencies:

```bash
pip install -r requirements.txt
```

> **LLM requirement**: install [Ollama](https://ollama.com) and pull a model:
> ```bash
> ollama pull llama3.1:8b
> ```
> The `/eda` endpoint works without Ollama. Only `/analyze/single-agent`
> requires it.

Start the FastAPI server:

```bash
uvicorn backend.main:app --reload
```

Open the interactive API docs:

```
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/health` | Health check |
| `POST` | `/upload` | CSV profiling (M2) |
| `POST` | `/eda` | Full deterministic EDA (M3) |
| `POST` | `/analyze/single-agent` | EDA + single LLM call (M4) |
| `POST` | `/analyze/multi-agent` | EDA + 7-node LangGraph pipeline (M5) |

## Run Tests

```bash
pytest
```

All existing and newly added tests must pass.

## Development Roadmap

### M5 – Multi-Agent Pipeline

* LangGraph-based multi-agent workflow
* Specialised analysis agents (Missing, Correlation, Outlier, Importance, Preprocessing, ML Recommender, Critic/Synthesizer)
* Explainability improvements

### M6 – Evaluation

* Compare single-agent vs multi-agent output against `AgentResponse` schema
* Measure and compare execution times
* Evaluate explainability and recommendation quality
* Use benchmark datasets: Iris, Wine, California Housing, Titanic, Adult Income

## Research Goal

This project supports research on intelligent dataset understanding by
comparing deterministic analysis with AI-driven interpretation. A stable,
reproducible deterministic profiling pipeline serves as the common input
for both the single-agent and multi-agent systems, enabling a fair evaluation.
