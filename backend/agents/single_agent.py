"""
Single-Agent LangChain Pipeline
================================
Passes the full deterministic EDA result to a locally-running LLM (via
Ollama) and returns a structured narrative interpretation.

The agent uses a single prompt containing the EDA JSON. It is intentionally
simple — a single LLM call with a carefully engineered system prompt —
serving as the baseline architecture against which the multi-agent
LangGraph system (Phase 3) will be compared.

Usage
-----
>>> from backend.agents.single_agent import run_single_agent
>>> result = run_single_agent(eda_result, model="llama3.1:8b")
>>> print(result["narrative"])
"""

from __future__ import annotations

import json
import time
from typing import Any

try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    ChatOllama = None  # type: ignore[assignment]
    LANGCHAIN_AVAILABLE = False

from backend.agents.schemas import AgentResponse


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert data scientist specialising in dataset analysis and \
machine learning. You will be given the results of a deterministic \
exploratory data analysis (EDA) in JSON format.

Your task is to produce a structured, human-readable interpretation of \
the dataset. Respond ONLY with a valid JSON object that has exactly these \
keys:

{
  "narrative": "<2-4 paragraph plain-English summary of the dataset>",
  "key_risks": [
    "<concise risk statement>",
    ...
  ],
  "recommendations": [
    "<actionable recommendation>",
    ...
  ],
  "confidence": <float 0.0-1.0 reflecting your certainty given the data>
}

Rules:
- Base ALL statements strictly on the data provided. Do not invent facts.
- "key_risks" should list the top 3-5 risks (e.g. data quality issues, \
  class imbalance, missing values, multicollinearity).
- "recommendations" should list 3-6 concrete, prioritised actions.
- Keep technical jargon minimal; assume a non-expert reader.
- Return only the JSON object — no extra text, no markdown fences.
"""


def _build_user_message(eda_result: dict) -> str:
    """Serialise the EDA result into a compact JSON string for the prompt."""
    # Trim very large fields to stay within context limits
    trimmed = {}

    for key, value in eda_result.items():
        if key == "correlation_analysis":
            # Keep only highly correlated pairs and first 5 rows of matrix
            ca = value if isinstance(value, dict) else {}
            matrix = ca.get("matrix", {})
            trimmed_matrix = dict(list(matrix.items())[:5])
            trimmed[key] = {
                "matrix_preview": trimmed_matrix,
                "highly_correlated_pairs": ca.get("highly_correlated_pairs", []),
                "cramers_v": ca.get("cramers_v", [])[:10],
                "point_biserial": ca.get("point_biserial", [])[:10],
            }
        elif key == "feature_importance":
            fi = value if isinstance(value, dict) else {}
            trimmed[key] = {
                "status": fi.get("status"),
                "task_type": fi.get("task_type"),
                "random_forest": fi.get("random_forest", [])[:10],
                "mutual_information": fi.get("mutual_information", [])[:10],
            }
        elif key == "feature_summary":
            fs = value if isinstance(value, dict) else {}
            features = fs.get("features", {})
            trimmed[key] = {
                "count": fs.get("count"),
                "features": dict(list(features.items())[:15]),
            }
        else:
            trimmed[key] = value

    return (
        "Here is the deterministic EDA result for the uploaded dataset:\n\n"
        + json.dumps(trimmed, indent=2, default=str)
    )


def _parse_llm_response(raw: str) -> dict:
    """
    Attempt to parse the LLM response as JSON.
    Falls back to a structured error dict if parsing fails.
    """
    text = raw.strip()

    # Strip accidental markdown fences
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    try:
        parsed = json.loads(text)
        return parsed
    except json.JSONDecodeError:
        return {
            "narrative": text,
            "key_risks": [],
            "recommendations": [],
            "confidence": None,
            "_parse_error": "LLM response was not valid JSON; raw text returned as narrative.",
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_single_agent(
    eda_result: dict,
    model: str = "llama3.1:8b",
    temperature: float = 0.2,
    base_url: str = "http://localhost:11434",
) -> dict:
    """
    Run the single-agent LangChain pipeline on a completed EDA result.

    Parameters
    ----------
    eda_result:
        The dict returned by ``run_eda()``.
    model:
        Ollama model name (must be pulled locally, e.g. ``llama3.1:8b``).
    temperature:
        Sampling temperature. Lower values produce more deterministic output.
    base_url:
        Ollama server URL.

    Returns
    -------
    dict
        Contains keys: ``narrative``, ``key_risks``, ``recommendations``,
        ``confidence``, ``model``, ``execution_time_seconds``, and
        optionally ``error``.
    """
    if not LANGCHAIN_AVAILABLE:
        return AgentResponse(
            status="error",
            model=model,
            pipeline="single_agent",
            execution_time_seconds=0.0,
            error=(
                "LangChain / langchain-ollama is not installed. "
                "Run: pip install langchain langchain-ollama langchain-core"
            ),
        ).model_dump()

    start = time.perf_counter()

    try:
        llm = ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url,
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_user_message(eda_result)),
        ]

        response = llm.invoke(messages)
        raw_content = response.content
        elapsed = round(time.perf_counter() - start, 3)

        parsed = _parse_llm_response(raw_content)

        # Separate known schema fields from any extra LLM fields
        known = {"narrative", "key_risks", "recommendations", "confidence"}
        extra_fields = {k: v for k, v in parsed.items() if k not in known}

        return AgentResponse(
            status="success",
            model=model,
            pipeline="single_agent",
            execution_time_seconds=elapsed,
            narrative=parsed.get("narrative"),
            key_risks=parsed.get("key_risks", []),
            recommendations=parsed.get("recommendations", []),
            confidence=parsed.get("confidence"),
            extra=extra_fields,
        ).model_dump()

    except Exception as exc:
        elapsed = round(time.perf_counter() - start, 3)
        return AgentResponse(
            status="error",
            model=model,
            pipeline="single_agent",
            execution_time_seconds=elapsed,
            error=str(exc),
        ).model_dump()
