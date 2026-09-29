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
Single AI Agent
   ↓
Natural-Language Analysis