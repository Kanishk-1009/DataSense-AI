# Smart Dataset Understanding Agent

An automated dataset analysis system that combines deterministic Exploratory Data Analysis (EDA) with LLM-based interpretation to help users understand datasets before building machine learning models.

## Project Overview

The Smart Dataset Understanding Agent analyzes uploaded CSV datasets and generates structured insights such as dataset information, column metadata, missing values, categorical statistics, and data quality warnings. The project is being developed incrementally, with deterministic profiling forming the foundation for future AI-powered analysis and recommendations.

## Current Progress

* [x] M1 Project Setup
* [x] M2 CSV Ingestion & Profiling
* [ ] M3 Deterministic EDA Engine
* [ ] M4 Single-Agent Pipeline
* [ ] M5 Multi-Agent Pipeline
* [ ] M6 Evaluation
* [ ] Frontend
* [ ] Research Experiments

## Features Implemented

* CSV upload through FastAPI
* Dataset validation
* Dataset profiling
* Column type detection
* Missing value analysis
* Categorical statistics
* Rule-based quality warnings
* Automated unit tests using pytest

## Project Structure

```text
smart-dataset-agent/
│
├── backend/
│   ├── core/
│   ├── tests/
│   └── main.py
│
├── datasets/
├── results/
│   ├── raw/
│   ├── metrics/
│   └── sample_profile.json
│
├── research/
│
├── README.md
├── requirements.txt
└── .gitignore
```

## Tech Stack

* Python
* FastAPI
* Pandas
* Pytest
* Uvicorn

## Run Backend

Install the dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn backend.main:app --reload
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

## Run Tests

```bash
pytest
```

## Development Roadmap

### M3 – Deterministic EDA Engine

* Numeric statistics
* Correlation analysis
* Outlier detection
* Target variable analysis
* Feature importance

### M4 – Single-Agent Pipeline

* LLM-powered interpretation
* Preprocessing recommendations
* Model suggestions

### M5 – Multi-Agent Pipeline

* LangGraph-based multi-agent workflow
* Specialized analysis agents
* Explainability improvements

### M6 – Evaluation

* Compare single-agent and multi-agent architectures
* Measure execution time
* Evaluate explainability
* Analyze recommendation quality

## Research Goal

This project supports research on intelligent dataset understanding by comparing deterministic analysis with AI-driven interpretation. A stable deterministic profiling pipeline serves as the common input for both the single-agent and multi-agent systems, enabling a fair and reproducible evaluation.
