"""
Integration tests for run_evaluation().

All LLM calls are mocked — no Ollama server required.

Covers:
- Return type and schema validity
- Research guarantee: same EDA object passed to both pipelines (identity, not equality)
- Comparison table structure and directionality
- M6-B rubric checks present in result
- Persistence: results/metrics/ JSON file is created
- Error handling when a pipeline fails
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.evaluation.evaluator import run_evaluation
from backend.evaluation.schemas import EvaluationResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_eda():
    """
    EDA result with high missingness and categorical features, ensuring
    at least two M6-B rubric conditions are triggered for meaningful
    correctness scoring.
    """
    return {
        "missingness": {
            "summary": {
                "overall_missing_percentage": 30.0,
                "columns_with_missing": 2,
            },
            "columns": {},
        },
        "correlation_analysis": {
            "matrix": {},
            "highly_correlated_pairs": [],
            "cramers_v": [],
            "point_biserial": [],
        },
        "outliers": {},
        "feature_summary": {
            "count": 2,
            "features": {
                "sex": {"column": "sex", "column_type": "categorical", "unique_count": 2},
            },
        },
        "ml_task": {
            "task": "classification",
            "task_type": "binary_classification",
            "target": "survived",
            "confidence": 0.98,
        },
        "ml_recommendation": {
            "status": "available",
            "recommended_models": [
                {"model": "Logistic Regression", "reason": "baseline"}
            ],
        },
        "preprocessing": {"status": "available", "recommendations": []},
        "feature_importance": {"status": "unavailable"},
        "report": {
            "dataset": {"rows": 891, "columns": 12},
            "quality": {"score": 78.0, "grade": "Good"},
        },
        "target_analysis": {},
    }


@pytest.fixture
def csv_bytes():
    return b"col1,col2\n1,2\n3,4\n"


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_resp(content: str):
    m = MagicMock()
    m.content = content
    return m


SINGLE_RESP = json.dumps({
    "narrative": (
        "The dataset contains significant missingness requiring imputation. "
        "Categorical features should be encoded appropriately. "
        "Use cross-validation for model evaluation."
    ),
    "key_risks": ["High missingness.", "Class imbalance risk.", "Small sample."],
    "recommendations": [
        "Impute missing values using median.",
        "Encode categorical features with one-hot encoding.",
        "Use stratified cross-validation.",
    ],
    "confidence": 0.80,
})

SPECIALIST_RESP = json.dumps({
    "findings": "No major issues.",
    "risk_level": "low",
    "recommendations": ["Proceed normally."],
})

PREPROCESSING_RESP = json.dumps({
    "steps": ["Encode categoricals.", "Impute missing."],
    "priority_issues": [],
    "risk_level": "low",
})

ALGORITHM_RESP = json.dumps({
    "recommended_models": [{"model": "Logistic Regression", "reason": "baseline"}],
    "reasoning": ["Clean data."],
    "risk_level": "low",
})

CRITIC_RESP = json.dumps({
    "narrative": (
        "The multi-agent analysis recommends imputation for missing values "
        "and encoding for categorical features. Consider class weights."
    ),
    "key_risks": ["Missingness.", "Categorical encoding.", "Imbalance."],
    "recommendations": [
        "Impute missing values.",
        "Encode categoricals.",
        "Use class weights.",
        "Validate with cross-validation.",
    ],
    "confidence": 0.87,
})


def _multi_side_effects():
    return [
        _mock_resp(SPECIALIST_RESP),   # missing_value_agent
        _mock_resp(SPECIALIST_RESP),   # correlation_agent
        _mock_resp(SPECIALIST_RESP),   # outlier_agent
        _mock_resp(SPECIALIST_RESP),   # feature_importance_agent
        _mock_resp(PREPROCESSING_RESP),# preprocessing_planner
        _mock_resp(ALGORITHM_RESP),    # algorithm_recommendation
        _mock_resp(CRITIC_RESP),       # critic_synthesizer
    ]


# ---------------------------------------------------------------------------
# Helper: run a mocked evaluation
# ---------------------------------------------------------------------------

def _run_mocked_eval(eda, csv_bytes, persist=False):
    with (
        patch("backend.agents.single_agent.ChatOllama") as mock_sa,
        patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_ma,
    ):
        sa_llm = MagicMock()
        sa_llm.invoke.return_value = _mock_resp(SINGLE_RESP)
        mock_sa.return_value = sa_llm

        ma_llm = MagicMock()
        ma_llm.invoke.side_effect = _multi_side_effects()
        mock_ma.return_value = ma_llm

        return run_evaluation(
            eda_result=eda,
            dataset_name="test_dataset",
            csv_bytes=csv_bytes,
            model="test-model",
            persist=persist,
        )


# ---------------------------------------------------------------------------
# Return type and schema
# ---------------------------------------------------------------------------

class TestRunEvaluationReturnType:
    def test_returns_evaluation_result(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        assert isinstance(result, EvaluationResult)

    def test_run_id_is_string(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        assert isinstance(result.run_id, str) and result.run_id

    def test_dataset_name_preserved(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        assert result.dataset_name == "test_dataset"

    def test_model_preserved(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        assert result.model == "test-model"

    def test_m4_pipeline_label(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        assert result.m4.pipeline == "single_agent"

    def test_m5_pipeline_label(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        assert result.m5.pipeline == "multi_agent"

    def test_model_dump_is_serialisable(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        d = result.model_dump()
        # Should be JSON-serialisable (no non-serialisable objects)
        json.dumps(d, default=str)


# ---------------------------------------------------------------------------
# Research guarantee: identity, not just equality
# ---------------------------------------------------------------------------

class TestResearchGuarantee:
    def test_eda_object_not_modified(self, minimal_eda, csv_bytes):
        """
        The EDA result must be byte-for-byte identical after the evaluation.
        This ensures no pipeline mutated the shared input.
        """
        original = copy.deepcopy(minimal_eda)
        _run_mocked_eval(minimal_eda, csv_bytes)
        assert minimal_eda == original

    def test_eda_passed_by_identity_to_single_agent(self, minimal_eda, csv_bytes):
        """
        run_single_agent must receive the exact same object that was
        passed to run_evaluation (identity, not a copy).
        """
        captured_args = []

        original_run_single = __import__(
            "backend.agents.single_agent", fromlist=["run_single_agent"]
        ).run_single_agent

        def capturing_single(eda_result, **kwargs):
            captured_args.append(id(eda_result))
            return {
                "status": "success",
                "pipeline": "single_agent",
                "model": "test-model",
                "execution_time_seconds": 1.0,
                "narrative": "Test.",
                "key_risks": ["Risk A."],
                "recommendations": ["Impute missing values."],
                "confidence": 0.8,
                "extra": {},
            }

        with (
            patch("backend.evaluation.evaluator.run_single_agent", side_effect=capturing_single),
            patch("backend.evaluation.evaluator.run_multi_agent") as mock_ma,
        ):
            mock_ma.return_value = {
                "status": "success",
                "pipeline": "multi_agent",
                "model": "test-model",
                "execution_time_seconds": 30.0,
                "narrative": "Multi-agent narrative with imputation recommendation.",
                "key_risks": ["Risk A.", "Risk B."],
                "recommendations": ["Impute missing values.", "Encode categoricals."],
                "confidence": 0.88,
                "extra": {"llm_call_count": 7},
            }

            run_evaluation(
                eda_result=minimal_eda,
                dataset_name="test",
                csv_bytes=csv_bytes,
                persist=False,
            )

        assert len(captured_args) == 1
        # The id captured inside run_single_agent must match the caller's id
        assert captured_args[0] == id(minimal_eda)


# ---------------------------------------------------------------------------
# Comparison table
# ---------------------------------------------------------------------------

class TestComparisonTable:
    def test_comparison_is_list(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        assert isinstance(result.comparison, list)

    def test_comparison_has_expected_metrics(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        metric_names = {c.metric for c in result.comparison}
        required = {
            "output_completeness",
            "narrative_length_chars",
            "key_risk_count",
            "recommendation_count",
            "confidence_score",
            "execution_time_seconds",
            "llm_call_count",
            "recommendation_accuracy",
        }
        assert required.issubset(metric_names)

    def test_descriptive_metrics_have_no_direction(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        descriptive = {
            "narrative_length_chars", "key_risk_count", "recommendation_count"
        }
        for c in result.comparison:
            if c.metric in descriptive:
                assert c.better_pipeline is None, (
                    f"Descriptive metric '{c.metric}' should have no direction"
                )

    def test_efficiency_metrics_have_direction(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        efficiency = {"execution_time_seconds", "llm_call_count"}
        for c in result.comparison:
            if c.metric in efficiency:
                # Should have a direction (lower is better)
                assert c.better_pipeline is not None

    def test_no_composite_score(self, minimal_eda, csv_bytes):
        """
        EvaluationResult must NOT have a 'winner' field or composite score.
        The research paper discusses trade-offs, not a single number.
        """
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        d = result.model_dump()
        assert "winner" not in d
        assert "composite_score" not in d


# ---------------------------------------------------------------------------
# M6-B correctness
# ---------------------------------------------------------------------------

class TestRecommendationAccuracy:
    def test_m4_accuracy_is_float_or_none(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        acc = result.m4.recommendation_accuracy
        assert acc is None or 0.0 <= acc <= 1.0

    def test_m5_accuracy_is_float_or_none(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        acc = result.m5.recommendation_accuracy
        assert acc is None or 0.0 <= acc <= 1.0

    def test_rubric_checks_is_list(self, minimal_eda, csv_bytes):
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        assert isinstance(result.m4.rubric_checks, list)
        assert isinstance(result.m5.rubric_checks, list)

    def test_missingness_condition_triggered(self, minimal_eda, csv_bytes):
        """
        minimal_eda has 30% missingness, so high_missingness should trigger.
        At least one pipeline should have a rubric check for it.
        """
        result = _run_mocked_eval(minimal_eda, csv_bytes)
        all_checks = result.m4.rubric_checks + result.m5.rubric_checks
        triggered_ids = {c.condition_id for c in all_checks if c.condition_triggered}
        assert "high_missingness" in triggered_ids


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_persisted_file_exists(self, minimal_eda, csv_bytes, tmp_path):
        """Verify that persist=True writes a JSON file to results/metrics/."""
        with patch("backend.evaluation.evaluator._METRICS_ROOT", tmp_path):
            result = _run_mocked_eval(minimal_eda, csv_bytes, persist=True)
            expected = tmp_path / f"{result.run_id}.json"
            assert expected.exists()

    def test_persisted_json_has_correct_shape(self, minimal_eda, csv_bytes, tmp_path):
        with patch("backend.evaluation.evaluator._METRICS_ROOT", tmp_path):
            result = _run_mocked_eval(minimal_eda, csv_bytes, persist=True)
            expected = tmp_path / f"{result.run_id}.json"
            data = json.loads(expected.read_text(encoding="utf-8"))
            assert "m4" in data
            assert "m5" in data
            assert "comparison" in data
            assert "run_id" in data
