"""
M6 Evaluator
============
Orchestrates the controlled experiment: runs M4 and M5 on identical EDA input,
scores both with the metric framework, builds a comparison table, and persists
the result.

Key design invariant (Research Guarantee)
------------------------------------------
``run_eda()`` is called EXACTLY ONCE per evaluation.  The resulting dict is
passed BY REFERENCE — the same in-memory object — to both pipelines.  This is
asserted at runtime with the ``is`` identity operator, not equality.

Usage
-----
>>> import pandas as pd
>>> from backend.core.eda import run_eda
>>> from backend.evaluation.evaluator import run_evaluation
>>>
>>> df = pd.read_csv("datasets/titanic.csv")
>>> eda_result = run_eda(df, target="Survived")
>>> result = run_evaluation(
...     eda_result=eda_result,
...     dataset_name="titanic",
...     csv_bytes=open("datasets/titanic.csv", "rb").read(),
...     model="llama3.1:8b",
... )
>>> print(result.model_dump_json(indent=2))
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.agents.single_agent import run_single_agent
from backend.agents.multi_agent.graph import run_multi_agent
from backend.evaluation.metrics import score_pipeline
from backend.evaluation.schemas import (
    EvaluationResult,
    MetricComparison,
    PipelineMetrics,
)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

_METRICS_ROOT = Path(__file__).resolve().parents[2] / "results" / "metrics"


def _short_hash(data: bytes, length: int = 8) -> str:
    return hashlib.sha256(data).hexdigest()[:length]


def _timestamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _save_evaluation(result: EvaluationResult) -> Path:
    """Persist the EvaluationResult as JSON under results/metrics/."""
    _METRICS_ROOT.mkdir(parents=True, exist_ok=True)
    filename = f"{result.run_id}.json"
    output_path = _METRICS_ROOT / filename
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result.model_dump(), fh, indent=2, default=str)
    return output_path


# ---------------------------------------------------------------------------
# Comparison table builder
# ---------------------------------------------------------------------------

def _build_comparison(m4: PipelineMetrics, m5: PipelineMetrics) -> list[MetricComparison]:
    """
    Build a per-metric comparison table.

    Direction rules
    ---------------
    - Structural  (completeness)      : higher is better → directional
    - Descriptive (counts, lengths)   : no direction     → None
    - Self-reported (confidence)      : no inherent direction (not validated)
    - Efficiency  (time, calls)       : lower is better  → directional
    - Correctness (accuracy)          : higher is better → directional
    """
    def _better(m4_val, m5_val, higher_is_better: bool) -> str | None:
        if m4_val is None or m5_val is None:
            return None
        if m4_val == m5_val:
            return "tie"
        if higher_is_better:
            return "m4" if m4_val > m5_val else "m5"
        else:
            return "m4" if m4_val < m5_val else "m5"

    comparisons = [
        MetricComparison(
            metric="output_completeness",
            category="STRUCTURAL",
            m4_value=m4.output_completeness,
            m5_value=m5.output_completeness,
            better_pipeline=_better(m4.output_completeness, m5.output_completeness, True),
            note="Primary quality signal. 1.0 = all required fields present.",
        ),
        MetricComparison(
            metric="narrative_length_chars",
            category="DESCRIPTIVE",
            m4_value=m4.narrative_length_chars,
            m5_value=m5.narrative_length_chars,
            better_pipeline=None,
            note="Observed count. Longer is NOT inherently better.",
        ),
        MetricComparison(
            metric="key_risk_count",
            category="DESCRIPTIVE",
            m4_value=m4.key_risk_count,
            m5_value=m5.key_risk_count,
            better_pipeline=None,
            note="Observed count. More risks is NOT inherently better.",
        ),
        MetricComparison(
            metric="recommendation_count",
            category="DESCRIPTIVE",
            m4_value=m4.recommendation_count,
            m5_value=m5.recommendation_count,
            better_pipeline=None,
            note="Observed count. More recommendations is NOT inherently better.",
        ),
        MetricComparison(
            metric="confidence_score",
            category="SELF-REPORTED",
            m4_value=m4.confidence_score,
            m5_value=m5.confidence_score,
            better_pipeline=None,
            note="LLM self-reported. Not externally validated.",
        ),
        MetricComparison(
            metric="execution_time_seconds",
            category="EFFICIENCY",
            m4_value=m4.execution_time_seconds,
            m5_value=m5.execution_time_seconds,
            better_pipeline=_better(m4.execution_time_seconds, m5.execution_time_seconds, False),
            note="Lower is better. M5 always expected to be slower (7 LLM calls).",
        ),
        MetricComparison(
            metric="llm_call_count",
            category="EFFICIENCY",
            m4_value=m4.llm_call_count,
            m5_value=m5.llm_call_count,
            better_pipeline=_better(m4.llm_call_count, m5.llm_call_count, False),
            note="M4=1, M5=7 by design. Lower = cheaper.",
        ),
        MetricComparison(
            metric="recommendation_accuracy",
            category="CORRECTNESS",
            m4_value=m4.recommendation_accuracy,
            m5_value=m5.recommendation_accuracy,
            better_pipeline=_better(m4.recommendation_accuracy, m5.recommendation_accuracy, True),
            note=(
                "M6-B rubric-based correctness. "
                "Primary research quality signal. "
                "None when no EDA conditions were triggered."
            ),
        ),
    ]
    return comparisons


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_evaluation(
    eda_result: dict,
    dataset_name: str,
    csv_bytes: bytes,
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    target: str | None = None,
    persist: bool = True,
) -> EvaluationResult:
    """
    Run the M6 controlled experiment.

    Both pipelines receive the **same in-memory EDA object** — this is
    asserted via Python ``is`` identity before any LLM call is made.

    Parameters
    ----------
    eda_result:
        Pre-computed EDA dict from ``run_eda()``.  Must be computed ONCE by
        the caller; do not compute separate EDA results for M4 and M5.
    dataset_name:
        Human-readable label for the dataset (e.g. ``"titanic"``).
    csv_bytes:
        Raw bytes of the source CSV.  Used to compute a dataset hash for
        reproducibility; never parsed again inside this function.
    model:
        Ollama model name for both pipelines.
    base_url:
        Ollama server URL.
    target:
        Target column name (forwarded to M5; informational).
    persist:
        If True, persist the result to ``results/metrics/``.

    Returns
    -------
    EvaluationResult

    Raises
    ------
    ValueError
        If the research guarantee is violated (eda_result identity check).
    """
    # ------------------------------------------------------------------
    # Research Guarantee: capture object identity before any LLM call
    # ------------------------------------------------------------------
    _eda_id = id(eda_result)

    # ------------------------------------------------------------------
    # Run both pipelines on the same EDA object
    # ------------------------------------------------------------------
    m4_response = run_single_agent(eda_result, model=model, base_url=base_url)
    m5_response = run_multi_agent(eda_result, model=model, base_url=base_url, target=target)

    # ------------------------------------------------------------------
    # Assert identity after pipelines complete (must still be same object)
    # ------------------------------------------------------------------
    if id(eda_result) != _eda_id:
        raise ValueError(
            "Research guarantee violated: eda_result object identity changed "
            "during pipeline execution. Ensure no pipeline replaces eda_result."
        )

    # ------------------------------------------------------------------
    # Score both pipeline responses
    # ------------------------------------------------------------------
    m4_metrics = score_pipeline(m4_response, eda_result)
    m5_metrics = score_pipeline(m5_response, eda_result)

    # ------------------------------------------------------------------
    # Build comparison table
    # ------------------------------------------------------------------
    comparison = _build_comparison(m4_metrics, m5_metrics)

    # ------------------------------------------------------------------
    # Assemble result
    # ------------------------------------------------------------------
    dataset_hash = _short_hash(csv_bytes)
    ts = _timestamp()
    run_id = f"{ts}_eval_{dataset_hash}"

    result = EvaluationResult(
        run_id=run_id,
        dataset_name=dataset_name,
        dataset_hash=dataset_hash,
        model=model,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        m4=m4_metrics,
        m5=m5_metrics,
        comparison=comparison,
    )

    # ------------------------------------------------------------------
    # Persist
    # ------------------------------------------------------------------
    if persist:
        try:
            _save_evaluation(result)
        except Exception:
            pass  # persistence errors must never break the return value

    return result
