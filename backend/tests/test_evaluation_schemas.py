"""
Tests for M6 Pydantic schemas.

Validates:
- PipelineMetrics construction (valid and invalid inputs)
- RubricCheckResult construction
- EvaluationResult construction and comparison table
- Field constraints (ge/le bounds)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.evaluation.schemas import (
    EvaluationResult,
    MetricComparison,
    PipelineMetrics,
    RubricCheckResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_pipeline_metrics(pipeline: str = "single_agent", **overrides) -> dict:
    base = {
        "pipeline": pipeline,
        "status": "success",
        "output_completeness": 1.0,
        "narrative_length_chars": 400,
        "key_risk_count": 3,
        "recommendation_count": 5,
        "confidence_score": 0.85,
        "execution_time_seconds": 7.2,
        "llm_call_count": 1,
        "recommendation_accuracy": 0.75,
        "rubric_checks": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# RubricCheckResult
# ---------------------------------------------------------------------------

class TestRubricCheckResult:
    def test_valid_construction(self):
        r = RubricCheckResult(
            condition_id="high_missingness",
            condition_description="Dataset has > 20% missing values.",
            condition_triggered=True,
            expected_keywords=["impute", "fill"],
            recommendation_matched=True,
        )
        assert r.condition_id == "high_missingness"
        assert r.recommendation_matched is True

    def test_defaults(self):
        r = RubricCheckResult(
            condition_id="x",
            condition_description="desc",
            condition_triggered=False,
            expected_keywords=[],
        )
        assert r.recommendation_matched is False


# ---------------------------------------------------------------------------
# PipelineMetrics
# ---------------------------------------------------------------------------

class TestPipelineMetrics:
    def test_valid_single_agent(self):
        m = PipelineMetrics(**_make_pipeline_metrics("single_agent"))
        assert m.pipeline == "single_agent"
        assert m.llm_call_count == 1

    def test_valid_multi_agent(self):
        m = PipelineMetrics(**_make_pipeline_metrics("multi_agent", llm_call_count=7))
        assert m.llm_call_count == 7

    def test_completeness_bounds(self):
        with pytest.raises(ValidationError):
            PipelineMetrics(**_make_pipeline_metrics(output_completeness=1.5))
        with pytest.raises(ValidationError):
            PipelineMetrics(**_make_pipeline_metrics(output_completeness=-0.1))

    def test_confidence_none_allowed(self):
        m = PipelineMetrics(**_make_pipeline_metrics(confidence_score=None))
        assert m.confidence_score is None

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            PipelineMetrics(**_make_pipeline_metrics(confidence_score=1.1))
        with pytest.raises(ValidationError):
            PipelineMetrics(**_make_pipeline_metrics(confidence_score=-0.01))

    def test_recommendation_accuracy_none_allowed(self):
        m = PipelineMetrics(**_make_pipeline_metrics(recommendation_accuracy=None))
        assert m.recommendation_accuracy is None

    def test_recommendation_accuracy_bounds(self):
        with pytest.raises(ValidationError):
            PipelineMetrics(**_make_pipeline_metrics(recommendation_accuracy=1.1))

    def test_narrative_length_non_negative(self):
        with pytest.raises(ValidationError):
            PipelineMetrics(**_make_pipeline_metrics(narrative_length_chars=-1))

    def test_error_field_optional(self):
        m = PipelineMetrics(**_make_pipeline_metrics(status="error", error="Ollama down"))
        assert m.error == "Ollama down"

    def test_rubric_checks_default_empty(self):
        data = _make_pipeline_metrics()
        data.pop("rubric_checks")
        m = PipelineMetrics(**data)
        assert m.rubric_checks == []


# ---------------------------------------------------------------------------
# MetricComparison
# ---------------------------------------------------------------------------

class TestMetricComparison:
    def test_directional_metric(self):
        c = MetricComparison(
            metric="output_completeness",
            category="STRUCTURAL",
            m4_value=1.0,
            m5_value=0.75,
            better_pipeline="m4",
        )
        assert c.better_pipeline == "m4"

    def test_descriptive_metric_no_direction(self):
        c = MetricComparison(
            metric="key_risk_count",
            category="DESCRIPTIVE",
            m4_value=4,
            m5_value=7,
            better_pipeline=None,
        )
        assert c.better_pipeline is None

    def test_none_values_allowed(self):
        c = MetricComparison(
            metric="recommendation_accuracy",
            category="CORRECTNESS",
            m4_value=None,
            m5_value=None,
        )
        assert c.m4_value is None


# ---------------------------------------------------------------------------
# EvaluationResult
# ---------------------------------------------------------------------------

class TestEvaluationResult:
    def _make_result(self) -> EvaluationResult:
        m4 = PipelineMetrics(**_make_pipeline_metrics("single_agent"))
        m5 = PipelineMetrics(**_make_pipeline_metrics("multi_agent", llm_call_count=7))
        return EvaluationResult(
            run_id="20260101T000000Z_eval_abcd1234",
            dataset_name="titanic",
            dataset_hash="abcd1234",
            model="llama3.1:8b",
            m4=m4,
            m5=m5,
        )

    def test_valid_construction(self):
        r = self._make_result()
        assert r.dataset_name == "titanic"
        assert r.m4.pipeline == "single_agent"
        assert r.m5.pipeline == "multi_agent"

    def test_comparison_defaults_empty(self):
        r = self._make_result()
        assert isinstance(r.comparison, list)

    def test_research_note_present(self):
        r = self._make_result()
        assert "composite" in r.research_note.lower() or "winner" in r.research_note.lower()

    def test_model_dump_is_dict(self):
        r = self._make_result()
        d = r.model_dump()
        assert isinstance(d, dict)
        assert "m4" in d
        assert "m5" in d
        assert "comparison" in d
