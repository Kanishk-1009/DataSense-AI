# DataSense AI
### Smart Dataset Understanding Agent

An intelligent, AI-powered platform for automated dataset profiling, exploratory data analysis, data-quality assessment, machine-learning readiness analysis, and multi-agent dataset interpretation.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-Frontend-3178C6?logo=typescript)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-Machine%20Learning-F7931E?logo=scikit-learn)
![LangChain](https://img.shields.io/badge/LangChain-LLM%20Framework-1C3C3C)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange)
![Ollama](https://img.shields.io/badge/Ollama-LLM-black)

---

## Overview

DataSense AI is a Smart Dataset Understanding Agent designed to automate the initial and often time-consuming stages of a machine-learning workflow.

When a new dataset is received, data scientists and ML practitioners typically need to manually inspect:

- Dataset structure and data types
- Missing values and duplicate records
- Statistical distributions and correlations
- Outliers and feature characteristics
- Potential target variables
- Machine-learning task types
- Preprocessing requirements
- Model recommendations
- Overall dataset quality

DataSense AI brings these processes together into a single intelligent platform.

The system combines **deterministic data analysis** with **LLM-powered interpretation** to provide structured, reproducible analysis while allowing AI agents to explain findings in natural language.

## Key Features

### 1. Automated Dataset Profiling

Upload a CSV dataset and automatically obtain:

- Number of rows and columns
- Column names and data types
- Missing-value statistics
- Unique-value information
- Numerical statistics
- Categorical statistics
- Dataset warnings
- Structural information

### 2. Exploratory Data Analysis

DataSense AI performs automated EDA including:

- Numerical statistics
- Feature summaries
- Correlation analysis
- Missingness analysis
- Outlier detection
- Target analysis
- Feature importance
- Dataset-level insights
- Preprocessing recommendations

The analysis is performed programmatically using Python data-analysis libraries before AI interpretation.

### 3. Data Quality Analysis

The platform evaluates common dataset-quality problems such as:

- Missing values
- Duplicate records
- Outliers
- Invalid or inconsistent data
- Feature-quality issues
- Potential preprocessing requirements

A quality-scoring mechanism provides a structured representation of dataset quality.

### 4. Machine Learning Readiness

DataSense AI analyzes whether a dataset appears suitable for machine-learning workflows.

The system can identify:

- Potential ML task type
- Candidate target variables
- Feature characteristics
- Class distribution
- Missing-data concerns
- Outlier risks
- Preprocessing requirements
- ML recommendations

The ML-readiness analysis assists users before model development begins.

### 5. AI-Powered Dataset Interpretation

The platform integrates AI agents to interpret deterministic analysis results.

Two analysis architectures are supported:

**Single-Agent Architecture (M4)**

A centralized AI agent receives structured dataset analysis and generates an overall interpretation.

```text
Dataset
   ↓
Deterministic Analysis
   ↓
Structured EDA Results
   ↓
Single AI Agent
   ↓
Natural-Language Analysis
```

**Multi-Agent Architecture (M5)**

A LangGraph-based architecture uses specialized agents to analyze different aspects of a dataset. Specialist nodes process missing values, outliers, and correlations concurrently, followed by downstream synthesis and interpretation stages.

```text
                  Dataset
                     ↓
             Deterministic EDA
                     ↓
             Structured Evidence
                     ↓
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Missing     Outlier   Correlation
        Agent       Agent       Agent
          └──────────┼──────────┘
                     ↓
              Analysis Stages
                     ↓
                Critic Agent
                     ↓
              Final Synthesis
                     ↓
             Dataset Insights
```

### 6. Controlled Evaluation Framework

The project includes an evaluation framework for comparing the Single-Agent and Multi-Agent architectures.

It evaluates:

- Recommendation accuracy
- Structural completeness
- Execution time
- LLM call count

The comparison uses the same deterministic EDA evidence for both architectures.

---

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Data Processing | Pandas, NumPy, SciPy |
| Machine Learning | Scikit-learn |
| AI Framework | LangChain, LangGraph |
| LLM Runtime | Ollama |
| Model | Llama 3.1 8B |
| Testing | Pytest |
| Deployment | Docker, Docker Compose |

---

## Project Structure

```text
smart-dataset-agent/
│
├── backend/
│   ├── core/
│   │   ├── eda/
│   │   └── profiler/
│   ├── tests/
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── evaluation/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirements.txt
└── README.md
```

---

## Running the Application

### 1. Prerequisites

Install the following:

- Python 3.12
- Node.js 20 or later
- Git
- Ollama (for local LLM functionality)
- Docker Desktop (for containerized deployment)

### 2. Local Development — React + FastAPI

Run the backend and frontend in separate terminals.

**Terminal 1 — Backend (FastAPI)**

```bash
# Activate virtual environment on Windows
.\venv\Scripts\Activate.ps1

# Linux/macOS
# source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Start FastAPI
uvicorn backend.main:app --reload --port 8000
```

API documentation:

`http://localhost:8000/docs`

**Terminal 2 — Frontend (React + Vite)**

```bash
cd frontend

npm install
npm run dev
```

Frontend:

`http://localhost:5173`

Vite proxies configured API requests to the local FastAPI backend.

---

## Production Deployment

DataSense AI supports unified deployment, where FastAPI serves both the production-built React application and backend API endpoints.

### 1. Unified Production Deployment

Build the React frontend:

```bash
cd frontend
npm install
npm run build
cd ..
```

Start the FastAPI server:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Application:

`http://localhost:8000`

API documentation:

`http://localhost:8000/docs`

### 2. Docker Deployment

The project includes a multi-stage Dockerfile that builds the React frontend and packages it with the Python backend.

Build and start the application:

```bash
docker compose up --build -d
```

Access the application:

`http://localhost:8000`

Check running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Stop the application:

```bash
docker compose down
```

### 3. Cloud Deployment

The unified Docker application can be deployed to a container-compatible hosting platform.

**Render deployment:**

1. Push the project to GitHub.
2. Open [Render](https://render.com/).
3. Create a new Web Service.
4. Connect the `smart-dataset-agent` repository.
5. Select the Docker environment.
6. Choose the `main` branch.
7. Configure the service and deploy.

Ensure that the application listens on `0.0.0.0` and the port assigned by the hosting platform.

**Important:** LLM functionality requires an accessible inference service. A local Ollama instance running on a developer's computer is not automatically accessible to a cloud deployment.

---

## Running Tests

Run backend tests:

```bash
pytest backend/tests/ -v
```

Run the complete test suite, if configured:

```bash
pytest -v
```

---

## Research and Evaluation

DataSense AI explores the differences between centralized Single-Agent and coordinated Multi-Agent architectures for automated dataset understanding.

The experimental framework evaluates both approaches using benchmark datasets and common evaluation metrics.

The central design principle is to separate deterministic statistical computation from LLM-based interpretation, improving reproducibility and making the evidence used by AI agents explicit.

---

## Future Scope

Potential future enhancements include:

- Support for additional dataset formats
- More advanced data-quality diagnostics
- Expanded ML model recommendations
- Improved explainability and agent traceability
- Additional benchmark datasets
- Performance and scalability optimization
- Integration with additional LLM providers

---

## License

This project is distributed under the MIT License. See the `LICENSE` file for details.

---

**DataSense AI — Making datasets easier to understand, analyze, and prepare for machine learning.**