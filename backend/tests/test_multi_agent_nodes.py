"""
Tests for each of the 7 multi-agent node functions.

All LLM calls are mocked — Ollama is not required.
Each node is tested in isolation: correct EDA slice extracted,
partial state returned with the right keys, timing and call count recorded.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.agents.multi_agent.nodes import (
    missing_value_node,
    correlation_node,
    outlier_node,
    feature_importance_node,
    preprocessing_node,
    algorithm_recommendation_node,
    critic_synthesizer_node,
)
from backend.agents.multi_agent.state import initial_state


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_eda():
    return {
        "missingness": {
            "summary": {"total_missing_cells": 5, "columns_with_missing": 2},
            "columns": {"age": {"missing_count": 3, "indicator": "likely_mcar"}},
        },
        "correlation_analysis": {
            "matrix": {"a": {"a": 1.0, "b": 0.9}},
            "highly_correlated_pairs": [{"column_a": "a", "column_b": "b", "correlation": 0.9, "method": "pearson"}],
            "cramers_v": [],
            "point_biserial": [],
        },
        "outliers": {
            "age": {
                "count": 2, "percentage": 2.0,
                "iqr": {"count": 2}, "zscore": {"count": 1},
                "isolation_forest": {"count": 3},
                "consensus_count": 2,
                "lower_bound": 0.0, "upper_bound": 100.0,
            }
        },
        "feature_importance": {
            "status": "available",
            "task_type": "classification",
            "target": "survived",
            "random_forest": [{"feature": "age", "importance": 0.4, "rank": 1}],
            "mutual_information": [{"feature": "age", "score": 0.3, "rank": 1}],
        },
        "feature_summary": {
            "count": 2,
            "features": {
                "age": {"column_type": "numeric", "missing_count": 3}
            },
        },
        "preprocessing": {
            "status": "available",
            "recommendations": [
                {"column": "age", "type": "missing_values", "priority": "high",
                 "action": "imputation", "message": "age has missing values."}
            ],
        },
        "ml_task": {
            "task": "classification",
            "task_type": "binary_classification",
            "target": "survived",
            "confidence": 0.98,
        },
        "ml_recommendation": {
            "status": "available",
            "recommended_models": [{"model": "Logistic Regression", "reason": "baseline"}],
        },
        "report": {
            "dataset": {"rows": 891, "columns": 12},
            "quality": {"score": 78.0, "grade": "Good"},
        },
    }


@pytest.fixture
def base_state(full_eda):
    return initial_state(eda=full_eda, model="test-model")


def _make_llm_response(content: str):
    mock = MagicMock()
    mock.content = content
    return mock


VALID_SPECIALIST_JSON = json.dumps({
    "findings": "Some findings.",
    "risk_level": "medium",
    "recommendations": ["Do X.", "Do Y."],
})

VALID_PREPROCESSING_JSON = json.dumps({
    "steps": ["Step 1", "Step 2"],
    "priority_issues": ["Issue A"],
    "risk_level": "high",
})

VALID_ALGORITHM_JSON = json.dumps({
    "recommended_models": [{"model": "Random Forest", "reason": "robust"}],
    "reasoning": ["Data has outliers."],
    "risk_level": "medium",
})

VALID_CRITIC_JSON = json.dumps({
    "narrative": "Overall the dataset is reasonable.",
    "key_risks": ["Missing values in age.", "Class imbalance."],
    "recommendations": ["Impute age.", "Use SMOTE."],
    "confidence": 0.82,
})


# ---------------------------------------------------------------------------
# Shared partial-state assertions
# ---------------------------------------------------------------------------

def _assert_partial_state(result: dict, node_name: str):
    assert "specialist_outputs" in result
    assert node_name in result["specialist_outputs"]
    assert "per_node_time" in result
    assert node_name in result["per_node_time"]
    assert "llm_call_count" in result
    assert result["llm_call_count"] == 1
    assert result["per_node_time"][node_name] >= 0.0


# ---------------------------------------------------------------------------
# missing_value_node
# ---------------------------------------------------------------------------

class TestMissingValueNode:
    def test_returns_partial_state(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_SPECIALIST_JSON)
            result = missing_value_node(base_state)
        _assert_partial_state(result, "missing_value_agent")

    def test_output_has_findings(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_SPECIALIST_JSON)
            result = missing_value_node(base_state)
        out = result["specialist_outputs"]["missing_value_agent"]
        assert "findings" in out

    def test_handles_llm_error(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.side_effect = ConnectionError("Ollama down")
            result = missing_value_node(base_state)
        assert "error" in result["specialist_outputs"]["missing_value_agent"]
        assert result["llm_call_count"] == 1

    def test_unavailable_when_no_langchain(self, base_state):
        with patch("backend.agents.multi_agent.nodes.LANGCHAIN_AVAILABLE", False):
            result = missing_value_node(base_state)
        assert result["llm_call_count"] == 0


# ---------------------------------------------------------------------------
# correlation_node
# ---------------------------------------------------------------------------

class TestCorrelationNode:
    def test_returns_partial_state(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_SPECIALIST_JSON)
            result = correlation_node(base_state)
        _assert_partial_state(result, "correlation_agent")

    def test_handles_llm_error(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.side_effect = RuntimeError("fail")
            result = correlation_node(base_state)
        assert "error" in result["specialist_outputs"]["correlation_agent"]


# ---------------------------------------------------------------------------
# outlier_node
# ---------------------------------------------------------------------------

class TestOutlierNode:
    def test_returns_partial_state(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_SPECIALIST_JSON)
            result = outlier_node(base_state)
        _assert_partial_state(result, "outlier_agent")

    def test_handles_llm_error(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.side_effect = RuntimeError("fail")
            result = outlier_node(base_state)
        assert "error" in result["specialist_outputs"]["outlier_agent"]


# ---------------------------------------------------------------------------
# feature_importance_node
# ---------------------------------------------------------------------------

class TestFeatureImportanceNode:
    def test_returns_partial_state(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_SPECIALIST_JSON)
            result = feature_importance_node(base_state)
        _assert_partial_state(result, "feature_importance_agent")


# ---------------------------------------------------------------------------
# preprocessing_node
# ---------------------------------------------------------------------------

class TestPreprocessingNode:
    def test_returns_partial_state(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_PREPROCESSING_JSON)
            result = preprocessing_node(base_state)
        _assert_partial_state(result, "preprocessing_planner_agent")

    def test_includes_specialist_context(self, base_state):
        # Populate some earlier specialist outputs in state
        base_state["specialist_outputs"]["missing_value_agent"] = {
            "findings": "missing data"
        }
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_PREPROCESSING_JSON)
            result = preprocessing_node(base_state)
        assert result["llm_call_count"] == 1


# ---------------------------------------------------------------------------
# algorithm_recommendation_node
# ---------------------------------------------------------------------------

class TestAlgorithmRecommendationNode:
    def test_returns_partial_state(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_ALGORITHM_JSON)
            result = algorithm_recommendation_node(base_state)
        _assert_partial_state(result, "algorithm_recommendation_agent")


# ---------------------------------------------------------------------------
# critic_synthesizer_node
# ---------------------------------------------------------------------------

class TestCriticSynthesizerNode:
    def test_returns_final_response(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_CRITIC_JSON)
            result = critic_synthesizer_node(base_state)
        assert "final_response" in result
        assert result["final_response"] is not None

    def test_final_response_has_narrative(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_CRITIC_JSON)
            result = critic_synthesizer_node(base_state)
        fr = result["final_response"]
        assert fr.get("narrative") is not None

    def test_final_response_pipeline_is_multi_agent(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.return_value = _make_llm_response(VALID_CRITIC_JSON)
            result = critic_synthesizer_node(base_state)
        assert result["final_response"]["pipeline"] == "multi_agent"

    def test_unavailable_returns_error_final_response(self, base_state):
        with patch("backend.agents.multi_agent.nodes.LANGCHAIN_AVAILABLE", False):
            result = critic_synthesizer_node(base_state)
        assert result["final_response"]["status"] == "error"
        assert result["llm_call_count"] == 0

    def test_handles_llm_error(self, base_state):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_cls.return_value.invoke.side_effect = ConnectionError("down")
            result = critic_synthesizer_node(base_state)
        fr = result["final_response"]
        assert "error" in fr
