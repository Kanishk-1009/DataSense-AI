"""
M6 Evaluation Schemas
=====================
Pydantic models for the M6 controlled experiment results.

Design notes
------------
- ``PipelineMetrics`` captures ALL observed metrics for one pipeline run.
  Metrics are deliberately categorised so consumers know what each one means:
  some are structural quality signals, others are purely descriptive counts,
  others are efficiency or self-reported values.

- ``EvaluationResult`` pairs M4 and M5 metrics alongside metadata.
  There is intentionally NO composite "winner" score — the research paper
  discusses trade-offs; this schema only records observations.

- ``RecommendationAccuracyDetail`` records the M6-B rubric check result
  per EDA condition so the evaluation is fully auditable.
"""

from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# M6-B: per-condition correctness detail
# ---------------------------------------------------------------------------

class RubricCheckResult(BaseModel):
    """
    Result of checking one ground-truth rubric condition against an
    agent's recommendations.
    """
    condition_id: str = Field(
        description="Short identifier for the EDA condition, e.g. 'high_missingness'.",
    )
    condition_description: str = Field(
        description="Human-readable description of the triggered condition.",
    )
    condition_triggered: bool = Field(
        description="True when the EDA data actually exhibits this condition.",
    )
    expected_keywords: list[str] = Field(
        description="Keywords that signal a correct recommendation for this condition.",
    )
    recommendation_matched: bool = Field(
        default=False,
        description=(
            "True when at least one agent recommendation contains a keyword "
            "matching the expected treatment for this condition."
        ),
    )


# ---------------------------------------------------------------------------
# Per-pipeline metrics
# ---------------------------------------------------------------------------

class PipelineMetrics(BaseModel):
    """
    All observed metrics for a single agent pipeline run (M4 or M5).

    Metric taxonomy
    ---------------
    Structural  — did the pipeline produce correct output?
    Descriptive — how much output was produced? (not inherently good or bad)
    Efficiency  — how expensive was the run?
    Self-reported — what did the agent say about its own confidence?
    Correctness — how accurate are the recommendations against EDA evidence?
    """

    pipeline: str = Field(
        description="'single_agent' (M4) or 'multi_agent' (M5).",
    )

    # ---- Structural ---------------------------------------------------------
    output_completeness: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Fraction of required output fields that are non-null and non-empty. "
            "Fields checked: narrative, key_risks (non-empty list), "
            "recommendations (non-empty list), confidence. "
            "1.0 = all present; 0.0 = nothing produced. "
            "Category: STRUCTURAL quality signal."
        ),
    )

    # ---- Descriptive (observed counts — NOT quality signals) ----------------
    narrative_length_chars: int = Field(
        ge=0,
        description=(
            "Character length of the narrative field. "
            "Longer is not inherently better. "
            "Category: DESCRIPTIVE."
        ),
    )
    key_risk_count: int = Field(
        ge=0,
        description=(
            "Number of key risks returned. "
            "More is not inherently better. "
            "Category: DESCRIPTIVE."
        ),
    )
    recommendation_count: int = Field(
        ge=0,
        description=(
            "Number of recommendations returned. "
            "More is not inherently better. "
            "Category: DESCRIPTIVE."
        ),
    )

    # ---- Self-reported ------------------------------------------------------
    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "LLM self-reported confidence (0.0–1.0). "
            "Informational only — not externally validated. "
            "None if the LLM did not return a value. "
            "Category: SELF-REPORTED."
        ),
    )

    # ---- Efficiency ---------------------------------------------------------
    execution_time_seconds: float = Field(
        ge=0.0,
        description=(
            "Total wall-clock time of the agent pipeline. "
            "Category: EFFICIENCY — lower is better."
        ),
    )
    llm_call_count: int = Field(
        ge=0,
        description=(
            "Total LLM invocations during the run. "
            "M4 = 1; M5 = 7. "
            "Category: EFFICIENCY."
        ),
    )

    # ---- Correctness (M6-B) -------------------------------------------------
    recommendation_accuracy: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Fraction of triggered EDA conditions for which the pipeline "
            "produced at least one correctly-targeted recommendation. "
            "Computed against the ground-truth rubric in rubric.py. "
            "None when no EDA conditions were triggered. "
            "Category: CORRECTNESS — the primary research quality signal."
        ),
    )
    rubric_checks: list[RubricCheckResult] = Field(
        default_factory=list,
        description=(
            "Per-condition audit trail for the M6-B correctness evaluation. "
            "Only populated for triggered conditions."
        ),
    )

    # ---- Status passthrough -------------------------------------------------
    status: str = Field(
        description="'success' | 'error' from the underlying AgentResponse.",
    )
    error: str | None = Field(
        default=None,
        description="Error message if the pipeline failed.",
    )


# ---------------------------------------------------------------------------
# Paired evaluation result
# ---------------------------------------------------------------------------

class MetricComparison(BaseModel):
    """
    Per-metric comparison between M4 and M5.
    Records the raw values and which pipeline performed better (if applicable).
    """
    metric: str
    category: str = Field(
        description="STRUCTURAL | DESCRIPTIVE | EFFICIENCY | SELF-REPORTED | CORRECTNESS",
    )
    m4_value: Any
    m5_value: Any
    better_pipeline: str | None = Field(
        default=None,
        description=(
            "Which pipeline is better on this metric, or None if the metric "
            "is purely descriptive (no inherent direction)."
        ),
    )
    note: str | None = Field(
        default=None,
        description="Optional research note about this metric.",
    )


class EvaluationResult(BaseModel):
    """
    Full M6 evaluation result: M4 metrics, M5 metrics, and a per-metric
    comparison table.

    There is deliberately no single composite 'winner' score.
    The comparison table enables a nuanced trade-off discussion in the
    research paper.
    """

    # ---- Identity -----------------------------------------------------------
    run_id: str = Field(
        description="Unique identifier for this evaluation run (timestamp + hash).",
    )
    dataset_name: str = Field(
        description="Human-readable dataset label (e.g. 'titanic').",
    )
    dataset_hash: str = Field(
        description="Short SHA-256 of the source CSV bytes for reproducibility.",
    )
    model: str = Field(
        description="Ollama model used for both pipelines.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp of the evaluation run.",
    )

    # ---- Pipeline results ---------------------------------------------------
    m4: PipelineMetrics = Field(
        description="Metrics for the single-agent (M4) pipeline.",
    )
    m5: PipelineMetrics = Field(
        description="Metrics for the multi-agent (M5) pipeline.",
    )

    # ---- Comparison table ---------------------------------------------------
    comparison: list[MetricComparison] = Field(
        default_factory=list,
        description=(
            "Per-metric comparison of M4 vs M5. "
            "Each entry records the raw values and, for directional metrics, "
            "which pipeline performed better. "
            "Purely descriptive metrics have better_pipeline=None."
        ),
    )

    # ---- Research note ------------------------------------------------------
    research_note: str = Field(
        default=(
            "No composite winner score is computed. "
            "See 'comparison' for a metric-by-metric breakdown. "
            "Discuss trade-offs (quality vs. latency vs. cost) in the paper."
        ),
        description="Standing note for consumers of this result.",
    )
