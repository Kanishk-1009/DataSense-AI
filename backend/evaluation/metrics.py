"""
M6 Metric Scorers
=================
Pure functions that compute each metric from an ``AgentResponse`` dict.

All scorers are deterministic — given the same inputs they return the same
output, with no LLM calls, no side effects, and no external dependencies.

Metric taxonomy (see schemas.py for full docstrings)
-----------------------------------------------------
STRUCTURAL   : output_completeness
DESCRIPTIVE  : narrative_length_chars, key_risk_count, recommendation_count
SELF-REPORTED: confidence_score
EFFICIENCY   : execution_time_seconds, llm_call_count
CORRECTNESS  : recommendation_accuracy  (M6-B, rubric-based)

Design rule
-----------
Do NOT combine DESCRIPTIVE metrics (counts, lengths) into any quality score.
A higher count is not inherently better.  These metrics are recorded as
observations so the research paper can discuss them in context.

Public API
----------
>>> from backend.evaluation.metrics import score_pipeline
>>> metrics = score_pipeline(agent_response, eda_result)
"""

from __future__ import annotations

from backend.evaluation.schemas import PipelineMetrics, RubricCheckResult
from backend.evaluation.rubric import (
    GROUND_TRUTH_RUBRIC,
    extract_triggered_conditions,
)


# ---------------------------------------------------------------------------
# Individual scorer functions
# ---------------------------------------------------------------------------

def score_output_completeness(agent_response: dict) -> float:
    """
    STRUCTURAL metric.

    Fraction of required AgentResponse fields that are present and non-empty:
      - narrative      : must be a non-empty string
      - key_risks      : must be a non-empty list
      - recommendations: must be a non-empty list
      - confidence     : must be a non-None float

    Returns
    -------
    float in [0.0, 1.0]
        1.0 = all four fields present; 0.25 = only one present.
    """
    required = 4
    present = 0

    narrative = agent_response.get("narrative")
    if isinstance(narrative, str) and narrative.strip():
        present += 1

    risks = agent_response.get("key_risks", [])
    if isinstance(risks, list) and len(risks) > 0:
        present += 1

    recs = agent_response.get("recommendations", [])
    if isinstance(recs, list) and len(recs) > 0:
        present += 1

    conf = agent_response.get("confidence")
    if isinstance(conf, (int, float)) and conf is not None:
        present += 1

    return round(present / required, 4)


def score_narrative_length(agent_response: dict) -> int:
    """
    DESCRIPTIVE metric.

    Raw character count of the narrative.  Not a quality signal.
    """
    narrative = agent_response.get("narrative") or ""
    return len(str(narrative))


def score_key_risk_count(agent_response: dict) -> int:
    """
    DESCRIPTIVE metric.

    Number of key risks returned.  Not a quality signal.
    """
    risks = agent_response.get("key_risks", [])
    return len(risks) if isinstance(risks, list) else 0


def score_recommendation_count(agent_response: dict) -> int:
    """
    DESCRIPTIVE metric.

    Number of recommendations returned.  Not a quality signal.
    """
    recs = agent_response.get("recommendations", [])
    return len(recs) if isinstance(recs, list) else 0


def score_confidence(agent_response: dict) -> float | None:
    """
    SELF-REPORTED metric.

    LLM-reported confidence.  Informational only — not externally validated.
    Returns None if absent.
    """
    conf = agent_response.get("confidence")
    if conf is None:
        return None
    try:
        value = float(conf)
        return round(max(0.0, min(1.0, value)), 4)
    except (TypeError, ValueError):
        return None


def score_execution_time(agent_response: dict) -> float:
    """
    EFFICIENCY metric.

    Wall-clock time of the agent pipeline in seconds.  Lower is better.
    """
    t = agent_response.get("execution_time_seconds", 0.0)
    try:
        return round(float(t), 3)
    except (TypeError, ValueError):
        return 0.0


def score_llm_call_count(agent_response: dict) -> int:
    """
    EFFICIENCY metric.

    Total LLM invocations.  For M4 = 1; for M5 = 7.
    Read from ``extra.llm_call_count`` (populated by both pipelines).
    Falls back to 1 for the single-agent pipeline which does not write
    this field into ``extra``.
    """
    extra = agent_response.get("extra", {})
    count = extra.get("llm_call_count")
    if count is not None:
        try:
            return int(count)
        except (TypeError, ValueError):
            pass
    # Single-agent pipeline always makes exactly 1 call
    pipeline = agent_response.get("pipeline", "")
    return 1 if pipeline == "single_agent" else 0


# ---------------------------------------------------------------------------
# M6-B: recommendation correctness
# ---------------------------------------------------------------------------

def score_recommendation_accuracy(
    agent_response: dict,
    eda_result: dict,
) -> tuple[float | None, list[RubricCheckResult]]:
    """
    CORRECTNESS metric (M6-B).

    Compares the agent's recommendations against the ground-truth rubric
    to assess whether the agent addressed the issues actually present in
    the dataset.

    Algorithm
    ---------
    1. Identify which rubric conditions are triggered by ``eda_result``.
    2. For each triggered condition, check whether any recommendation in
       ``agent_response['recommendations']`` contains at least one of the
       expected keywords (case-insensitive substring match).
    3. Return the ratio of conditions correctly addressed.

    Parameters
    ----------
    agent_response:
        The dict returned by ``run_single_agent()`` or ``run_multi_agent()``.
    eda_result:
        The same EDA dict passed to the agent.

    Returns
    -------
    (accuracy, rubric_checks)
        accuracy       : float in [0, 1] or None (when no conditions triggered)
        rubric_checks  : list of RubricCheckResult for audit trail
    """
    triggered = extract_triggered_conditions(eda_result)

    # Build a single string of all recommendations for fast keyword search
    recs = agent_response.get("recommendations", [])
    rec_text = " ".join(str(r) for r in recs).lower() if recs else ""

    # Also check narrative for keyword coverage
    narrative = str(agent_response.get("narrative") or "").lower()
    combined_text = rec_text + " " + narrative

    checks: list[RubricCheckResult] = []
    matched = 0

    for entry in triggered:
        hit = any(kw.lower() in combined_text for kw in entry.expected_keywords)
        checks.append(
            RubricCheckResult(
                condition_id=entry.condition_id,
                condition_description=entry.description,
                condition_triggered=True,
                expected_keywords=list(entry.expected_keywords),
                recommendation_matched=hit,
            )
        )
        if hit:
            matched += 1

    if not triggered:
        return None, []

    accuracy = round(matched / len(triggered), 4)
    return accuracy, checks


# ---------------------------------------------------------------------------
# Aggregate scorer — produces a full PipelineMetrics object
# ---------------------------------------------------------------------------

def score_pipeline(
    agent_response: dict,
    eda_result: dict,
) -> PipelineMetrics:
    """
    Score a single pipeline run and return a ``PipelineMetrics`` object.

    Parameters
    ----------
    agent_response:
        The dict returned by ``run_single_agent()`` or ``run_multi_agent()``.
    eda_result:
        The EDA dict that was passed to the agent.  Required for M6-B
        correctness scoring.

    Returns
    -------
    PipelineMetrics
    """
    accuracy, rubric_checks = score_recommendation_accuracy(
        agent_response, eda_result
    )

    return PipelineMetrics(
        pipeline=agent_response.get("pipeline", "unknown"),
        status=agent_response.get("status", "unknown"),
        error=agent_response.get("error"),
        # Structural
        output_completeness=score_output_completeness(agent_response),
        # Descriptive
        narrative_length_chars=score_narrative_length(agent_response),
        key_risk_count=score_key_risk_count(agent_response),
        recommendation_count=score_recommendation_count(agent_response),
        # Self-reported
        confidence_score=score_confidence(agent_response),
        # Efficiency
        execution_time_seconds=score_execution_time(agent_response),
        llm_call_count=score_llm_call_count(agent_response),
        # Correctness (M6-B)
        recommendation_accuracy=accuracy,
        rubric_checks=rubric_checks,
    )
