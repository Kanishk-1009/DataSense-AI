"""
Tests for M6 metric scorer functions.

All tests use synthetic AgentResponse dicts and synthetic EDA dicts —
no LLM calls, no Ollama required.

Covers:
- score_output_completeness       (STRUCTURAL)
- score_narrative_length          (DESCRIPTIVE)
- score_key_risk_count            (DESCRIPTIVE)
- score_recommendation_count      (DESCRIPTIVE)
- score_confidence                (SELF-REPORTED)
- score_execution_time            (EFFICIENCY)
- score_llm_call_count            (EFFICIENCY)
- score_recommendation_accuracy   (CORRECTNESS, M6-B)
- score_pipeline (integration)
"""

from __future__ import annotations

import pytest

from backend.evaluation.metrics import (
    score_output_completeness,
    score_narrative_length,
    score_key_risk_count,
    score_recommendation_count,
    score_confidence,
    score_execution_time,
    score_llm_call_count,
    score_recommendation_accuracy,
    score_pipeline,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_agent_response():
    """A well-formed AgentResponse dict (single-agent)."""
    return {
        "status": "success",
        "pipeline": "single_agent",
        "model": "test-model",
        "execution_time_seconds": 8.5,
        "narrative": "The dataset is clean with strong predictive signal. " * 5,
        "key_risks": ["Class imbalance.", "Low sample size.", "Missing values."],
        "recommendations": [
            "Impute missing values using median.",
            "Encode categorical features.",
            "Use cross-validation.",
        ],
        "confidence": 0.82,
        "extra": {},
    }


@pytest.fixture
def empty_agent_response():
    """A minimal (failed/empty) AgentResponse dict."""
    return {
        "status": "error",
        "pipeline": "single_agent",
        "model": "test-model",
        "execution_time_seconds": 0.5,
        "narrative": None,
        "key_risks": [],
        "recommendations": [],
        "confidence": None,
        "extra": {},
    }


@pytest.fixture
def multi_agent_response():
    """AgentResponse from the multi-agent pipeline."""
    return {
        "status": "success",
        "pipeline": "multi_agent",
        "model": "test-model",
        "execution_time_seconds": 45.2,
        "narrative": "Multi-agent narrative with detailed analysis. " * 8,
        "key_risks": ["Risk A.", "Risk B.", "Risk C.", "Risk D."],
        "recommendations": [
            "Impute missing values.",
            "Encode categoricals.",
            "Cap outliers.",
            "Use cross-validation.",
            "Consider class weights.",
        ],
        "confidence": 0.88,
        "extra": {"llm_call_count": 7},
    }


@pytest.fixture
def eda_with_missingness():
    """EDA result that triggers the high_missingness rubric condition."""
    return {
        "missingness": {
            "summary": {
                "overall_missing_percentage": 35.0,
                "columns_with_missing": 3,
            },
            "columns": {},
        },
        "correlation_analysis": {"matrix": {}, "highly_correlated_pairs": []},
        "outliers": {},
        "feature_summary": {"count": 0, "features": {}},
        "ml_task": {"task": "classification"},
        "ml_recommendation": {},
    }


@pytest.fixture
def eda_clean():
    """EDA result that triggers no rubric conditions."""
    return {
        "missingness": {
            "summary": {
                "overall_missing_percentage": 0.0,
                "columns_with_missing": 0,
            },
            "columns": {},
        },
        "correlation_analysis": {"matrix": {}, "highly_correlated_pairs": []},
        "outliers": {},
        "feature_summary": {"count": 0, "features": {}},
        "ml_task": {"task": "classification"},
        "ml_recommendation": {},
    }


# ---------------------------------------------------------------------------
# score_output_completeness
# ---------------------------------------------------------------------------

class TestScoreOutputCompleteness:
    def test_full_response_is_1(self, full_agent_response):
        assert score_output_completeness(full_agent_response) == 1.0

    def test_empty_response_is_0(self, empty_agent_response):
        assert score_output_completeness(empty_agent_response) == 0.0

    def test_partial_two_fields(self):
        resp = {
            "narrative": "Something.",
            "key_risks": ["Risk A."],
            "recommendations": [],
            "confidence": None,
        }
        assert score_output_completeness(resp) == 0.5  # 2/4

    def test_whitespace_narrative_not_counted(self):
        resp = {
            "narrative": "   ",
            "key_risks": ["Risk A."],
            "recommendations": ["Do X."],
            "confidence": 0.8,
        }
        assert score_output_completeness(resp) == 0.75  # 3/4

    def test_result_in_range(self, full_agent_response):
        score = score_output_completeness(full_agent_response)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# score_narrative_length  (DESCRIPTIVE — just count chars)
# ---------------------------------------------------------------------------

class TestScoreNarrativeLength:
    def test_known_length(self):
        resp = {"narrative": "Hello world"}
        assert score_narrative_length(resp) == 11

    def test_none_narrative_is_zero(self):
        assert score_narrative_length({"narrative": None}) == 0

    def test_absent_narrative_is_zero(self):
        assert score_narrative_length({}) == 0


# ---------------------------------------------------------------------------
# score_key_risk_count  (DESCRIPTIVE)
# ---------------------------------------------------------------------------

class TestScoreKeyRiskCount:
    def test_count_correct(self, full_agent_response):
        assert score_key_risk_count(full_agent_response) == 3

    def test_empty_list_is_zero(self, empty_agent_response):
        assert score_key_risk_count(empty_agent_response) == 0

    def test_absent_field_is_zero(self):
        assert score_key_risk_count({}) == 0


# ---------------------------------------------------------------------------
# score_recommendation_count  (DESCRIPTIVE)
# ---------------------------------------------------------------------------

class TestScoreRecommendationCount:
    def test_count_correct(self, full_agent_response):
        assert score_recommendation_count(full_agent_response) == 3

    def test_empty_is_zero(self, empty_agent_response):
        assert score_recommendation_count(empty_agent_response) == 0


# ---------------------------------------------------------------------------
# score_confidence  (SELF-REPORTED)
# ---------------------------------------------------------------------------

class TestScoreConfidence:
    def test_valid_confidence(self, full_agent_response):
        assert score_confidence(full_agent_response) == pytest.approx(0.82)

    def test_none_returns_none(self, empty_agent_response):
        assert score_confidence(empty_agent_response) is None

    def test_clamped_to_1(self):
        assert score_confidence({"confidence": 1.5}) == pytest.approx(1.0)

    def test_clamped_to_0(self):
        assert score_confidence({"confidence": -0.5}) == pytest.approx(0.0)

    def test_invalid_type_returns_none(self):
        assert score_confidence({"confidence": "high"}) is None


# ---------------------------------------------------------------------------
# score_execution_time  (EFFICIENCY)
# ---------------------------------------------------------------------------

class TestScoreExecutionTime:
    def test_returns_float(self, full_agent_response):
        t = score_execution_time(full_agent_response)
        assert isinstance(t, float)
        assert t == pytest.approx(8.5)

    def test_missing_field_returns_zero(self):
        assert score_execution_time({}) == pytest.approx(0.0)

    def test_multi_agent_slower(self, full_agent_response, multi_agent_response):
        t4 = score_execution_time(full_agent_response)
        t5 = score_execution_time(multi_agent_response)
        assert t5 > t4


# ---------------------------------------------------------------------------
# score_llm_call_count  (EFFICIENCY)
# ---------------------------------------------------------------------------

class TestScoreLlmCallCount:
    def test_single_agent_default_1(self, full_agent_response):
        # No llm_call_count in extra — falls back to 1 for single_agent
        assert score_llm_call_count(full_agent_response) == 1

    def test_multi_agent_reads_extra(self, multi_agent_response):
        assert score_llm_call_count(multi_agent_response) == 7

    def test_explicit_extra_overrides_fallback(self):
        resp = {"pipeline": "single_agent", "extra": {"llm_call_count": 3}}
        assert score_llm_call_count(resp) == 3


# ---------------------------------------------------------------------------
# score_recommendation_accuracy  (CORRECTNESS, M6-B)
# ---------------------------------------------------------------------------

class TestScoreRecommendationAccuracy:
    def test_returns_none_when_no_conditions_triggered(
        self, full_agent_response, eda_clean
    ):
        accuracy, checks = score_recommendation_accuracy(full_agent_response, eda_clean)
        assert accuracy is None
        assert checks == []

    def test_returns_float_when_conditions_triggered(
        self, full_agent_response, eda_with_missingness
    ):
        accuracy, checks = score_recommendation_accuracy(
            full_agent_response, eda_with_missingness
        )
        assert accuracy is not None
        assert 0.0 <= accuracy <= 1.0

    def test_impute_keyword_matches_missingness_condition(self, eda_with_missingness):
        # "Impute missing values." should match high_missingness condition
        resp = {
            "recommendations": ["Impute missing values using median."],
            "narrative": "",
        }
        accuracy, checks = score_recommendation_accuracy(resp, eda_with_missingness)
        missingness_check = next(
            (c for c in checks if c.condition_id == "high_missingness"), None
        )
        assert missingness_check is not None
        assert missingness_check.recommendation_matched is True

    def test_irrelevant_recommendations_do_not_match(self, eda_with_missingness):
        resp = {
            "recommendations": ["Use gradient boosting.", "Scale features."],
            "narrative": "",
        }
        accuracy, checks = score_recommendation_accuracy(resp, eda_with_missingness)
        missingness_check = next(
            (c for c in checks if c.condition_id == "high_missingness"), None
        )
        if missingness_check is not None:
            assert missingness_check.recommendation_matched is False

    def test_narrative_also_searched(self, eda_with_missingness):
        # Keyword in narrative should count even if not in recommendations
        resp = {
            "recommendations": ["Scale features."],
            "narrative": "The dataset has significant missingness that requires imputation.",
        }
        accuracy, checks = score_recommendation_accuracy(resp, eda_with_missingness)
        missingness_check = next(
            (c for c in checks if c.condition_id == "high_missingness"), None
        )
        if missingness_check is not None:
            assert missingness_check.recommendation_matched is True

    def test_accuracy_in_range(self, full_agent_response, eda_with_missingness):
        accuracy, _ = score_recommendation_accuracy(
            full_agent_response, eda_with_missingness
        )
        if accuracy is not None:
            assert 0.0 <= accuracy <= 1.0


# ---------------------------------------------------------------------------
# score_pipeline (integration)
# ---------------------------------------------------------------------------

class TestScorePipeline:
    def test_returns_pipeline_metrics(self, full_agent_response, eda_clean):
        from backend.evaluation.schemas import PipelineMetrics
        m = score_pipeline(full_agent_response, eda_clean)
        assert isinstance(m, PipelineMetrics)

    def test_pipeline_field_matches(self, full_agent_response, eda_clean):
        m = score_pipeline(full_agent_response, eda_clean)
        assert m.pipeline == "single_agent"

    def test_all_fields_populated(self, full_agent_response, eda_clean):
        m = score_pipeline(full_agent_response, eda_clean)
        assert m.output_completeness == 1.0
        assert m.narrative_length_chars > 0
        assert m.llm_call_count == 1
        assert m.execution_time_seconds > 0

    def test_multi_agent_llm_count_7(self, multi_agent_response, eda_clean):
        m = score_pipeline(multi_agent_response, eda_clean)
        assert m.llm_call_count == 7

    def test_error_response_completeness_0(self, empty_agent_response, eda_clean):
        m = score_pipeline(empty_agent_response, eda_clean)
        assert m.output_completeness == 0.0
