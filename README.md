# DataSense AI

### Smart Dataset Understanding Agent

> An intelligent, AI-powered platform for automated dataset profiling, exploratory data analysis, data-quality assessment, machine-learning readiness analysis, and multi-agent dataset interpretation.

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-Frontend-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas)](https://pandas.pydata.org/)
[![Scikit--learn](https://img.shields.io/badge/Scikit--learn-Machine%20Learning-F7931E?logo=scikit-learn)](https://scikit-learn.org/)
[![Ollama](https://img.shields.io/badge/Ollama-LLM-black)](https://ollama.com/)

---

## Overview

DataSense AI is a Smart Dataset Understanding Agent designed to automate the initial and often time-consuming stages of a machine-learning workflow.

When a new dataset is received, data scientists and ML practitioners typically need to manually inspect:

- Dataset structure
- Data types
- Missing values
- Duplicate records
- Statistical distributions
- Correlations
- Outliers
- Feature characteristics
- Potential target variables
- Machine-learning task type
- Preprocessing requirements
- Model recommendations
- Overall dataset quality

DataSense AI brings these processes together into a single intelligent platform.

The system combines **deterministic data analysis** with **LLM-powered interpretation** to provide structured, reproducible analysis while allowing AI agents to explain findings in natural language.

---

# Key Features

## 1. Automated Dataset Profiling

Upload a CSV dataset and automatically obtain:

- Number of rows and columns
- Column names
- Data types
- Missing-value statistics
- Unique-value information
- Numerical statistics
- Categorical statistics
- Dataset warnings
- Structural information

---

## 2. Exploratory Data Analysis

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

---

## 3. Data Quality Analysis

The platform evaluates common dataset-quality problems such as:

- Missing values
- Duplicate records
- Outliers
- Invalid or inconsistent data
- Feature-quality issues
- Potential preprocessing requirements

A quality scoring mechanism is also included to provide a structured representation of dataset quality.

---

## 4. Machine Learning Readiness

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

The ML-readiness analysis is intended to assist users before model development begins.

---

## 5. AI-Powered Dataset Interpretation

The platform integrates AI agents to interpret deterministic analysis results.

Two analysis architectures are supported:

### Single-Agent Architecture

A centralized AI agent receives the structured dataset analysis and generates an overall interpretation.

```text
Dataset
   ↓
Deterministic Analysis
   ↓
Structured EDA Results
   ↓
Single AI Agent (LangChain)
   ↓
Natural-Language Analysis & Recommendations
```

### Multi-Agent Specialist Architecture (LangGraph)

A specialized multi-agent graph partitions the analysis into focused specialist nodes that run with parallel fan-out / fan-in and feed into a synthesis critic:

```text
                       START
                         │
          ┌──────────────┼──────────────┐   (Parallel Fan-Out)
          ▼              ▼              ▼
   Missing Value    Correlation      Outlier
      Agent            Agent          Agent
          │              │              │
          └──────────────┼──────────────┘   (Fan-In: Join)
                         ▼
             Feature Importance Agent
                         ▼
            Preprocessing Planner Agent
                         ▼
          Algorithm Recommendation Agent
                         ▼
             Critic & Synthesizer Agent
                         │
                        END
```

---

## Getting Started & How to Run

### Prerequisites
- **Python**: 3.10+ (tested on Python 3.13 / 3.14)
- **Node.js**: 18+ (tested on Node v20 / v22) and npm
- **Ollama**: Local install or remote GPU (e.g. Google Colab) with `llama3.1:8b` model pulled

---

### Step 1: Backend Setup & Run

1. Clone repository and navigate to the project root:
   ```bash
   cd DataSense-AI
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate    # On Windows: .venv\Scripts\activate
   ```

3. Install backend dependencies in editable mode:
   ```bash
   pip install -e .
   ```

4. Start the FastAPI backend server:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
   Backend will be running at `http://localhost:8000` (API documentation available at `http://localhost:8000/docs`).

---

### Step 2: Frontend Setup & Run

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd DataSense-AI/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open your browser and navigate to `http://localhost:5173`.

---

### Step 3: Ollama Setup (LLM Engine)

You can run Ollama either locally or on Google Colab (Free T4 GPU):

#### Option A: Running Ollama Locally
```bash
# Pull the model (one-time)
ollama pull llama3.1:8b

# Start Ollama server
ollama serve
```
In the DataSense AI UI, keep the default Ollama Server URL: `http://localhost:11434`.

#### Option B: Running Ollama on Google Colab (GPU Acceleration)
If you don't have a local GPU, run Ollama on Google Colab with Cloudflare Tunnel:
1. Open a Colab notebook with a **T4 GPU** runtime.
2. In a code cell, execute:
   ```bash
   !curl -fsSL https://ollama.com/install.sh | sh
   !ollama serve > ollama.log 2>&1 &
   !sleep 3
   !ollama pull llama3.1:8b
   !wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   !dpkg -i cloudflared-linux-amd64.deb
   !cloudflared tunnel --url http://localhost:11434 --logfile tunnel.log > tunnel.log 2>&1 &
   !sleep 5
   !grep -o 'https://[-a-zA-Z0-9.]*trycloudflare.com' tunnel.log | head -n 1
   ```
3. Copy the printed Cloudflare URL (e.g. `https://xxxx.trycloudflare.com`).
4. In the DataSense AI Frontend, paste this URL into the **Ollama Server URL** field.

---

### Step 4: Running Automated Tests

To run the unit test suite verifying EDA profiling, JSON parsing, and fallback mechanisms:
```bash
.venv/bin/python -m unittest discover -s backend/tests -p "test_*.py"
```
Or run the JSON parsing and prompt compaction test specifically:
```bash
.venv/bin/python -m unittest backend/tests/test_json_parsing.py
```

---

## Project Structure

```text
DataSense-AI/
├── backend/                   # FastAPI Backend
│   ├── agents/                # AI Agent implementations
│   │   ├── single_agent.py    # Baseline Single-Agent pipeline (LangChain)
│   │   └── multi_agent/       # Multi-Agent Specialist pipeline (LangGraph)
│   │       ├── graph.py       # LangGraph DAG definition
│   │       ├── nodes.py       # Specialist node handlers
│   │       └── state.py       # Graph state definitions
│   ├── core/                  # Deterministic data profiling & EDA
│   │   ├── eda.py             # Statistical EDA engine
│   │   ├── profiling.py       # Schema & column profiling
│   │   └── quality.py         # Data quality scoring
│   ├── evaluation/            # Controlled experiment & evaluation engine
│   │   ├── evaluator.py       # Single vs Multi-agent runner
│   │   ├── metrics.py         # Output completeness & accuracy scorers
│   │   └── rubric.py          # Ground-truth evaluation rubric
│   └── main.py                # FastAPI endpoints
├── datasets/                  # Sample benchmarking CSV datasets
│   ├── adult_income.csv
│   ├── california_housing.csv
│   ├── iris.csv
│   ├── titanic.csv
│   └── wine.csv
├── frontend/                  # React + TypeScript + Vite UI
│   ├── src/
│   │   ├── components/        # Reusable charts, dropzones & layout
│   │   ├── pages/             # Dashboard, Quality, Exploration, Evaluation
│   │   └── services/          # API client services
│   └── package.json
├── pyproject.toml             # Python dependencies and build config
└── README.md
```