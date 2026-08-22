"""
End-to-end tests for run_multi_agent().

The compiled LangGraph graph is invoked with a mocked LLM so that:
- No Ollama server is required.
- The full graph topology (fan-out → fan-in → sequential → critic) executes.
- The AgentResponse schema is validated.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.agents.multi_agent.graph import run_multi_agent


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_eda():
    return {
        "missingness": {
            "summary": {
                "total_missing_cells": 0,
                "total_cells": 500,
                "overall_missing_percentage": 0.0,
                "columns_with_missing": 0,
                "likely_mar_columns": [],
                "likely_mcar_columns": [],
                "complete_columns": 10,
                "heuristic_note": "heuristic only",
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
        "feature_importance": {"status": "unavailable"},
        "feature_summary": {"count": 0, "features": {}},
        "preprocessing": {"status": "available", "recommendations": []},
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
        "report": {
            "dataset": {"rows": 891, "columns": 12},
            "quality": {"score": 78.0, "grade": "Good"},
        },
    }


def _mock_response(content: str):
    mock = MagicMock()
    mock.content = content
    return mock


SPECIALIST_RESP = json.dumps({
    "findings": "No issues found.",
    "risk_level": "low",
    "recommendations": ["Proceed normally."],
})

PREPROCESSING_RESP = json.dumps({
    "steps": ["Encode categoricals."],
    "priority_issues": [],
    "risk_level": "low",
})

ALGORITHM_RESP = json.dumps({
    "recommended_models": [{"model": "Logistic Regression", "reason": "good baseline"}],
    "reasoning": ["Clean data."],
    "risk_level": "low",
})

CRITIC_RESP = json.dumps({
    "narrative": "The dataset is clean and suitable for classification.",
    "key_risks": ["Possible label noise."],
    "recommendations": ["Use cross-validation.", "Check class balance."],
    "confidence": 0.88,
})


# Rotate through responses: 6 specialist calls then critic
def _side_effects():
    responses = (
        [SPECIALIST_RESP] * 3      # parallel: missing, correlation, outlier
        + [SPECIALIST_RESP]        # feature importance
        + [PREPROCESSING_RESP]     # preprocessing
        + [ALGORITHM_RESP]         # algorithm
        + [CRITIC_RESP]            # critic
    )
    return [_mock_response(r) for r in responses]


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------

class TestRunMultiAgentReturnStructure:
    def test_returns_dict(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        assert isinstance(result, dict)

    def test_status_success(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        assert result["status"] == "success"

    def test_pipeline_is_multi_agent(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        assert result["pipeline"] == "multi_agent"

    def test_narrative_present(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        assert result["narrative"] is not None

    def test_key_risks_is_list(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        assert isinstance(result["key_risks"], list)

    def test_recommendations_is_list(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        assert isinstance(result["recommendations"], list)

    def test_execution_time_non_negative(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        assert result["execution_time_seconds"] >= 0.0

    def test_model_name_preserved(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda, model="llama3.1:8b")
        assert result["model"] == "llama3.1:8b"


class TestRunMultiAgentExtraMetadata:
    def test_extra_has_llm_call_count(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        assert "llm_call_count" in result["extra"]
        assert result["extra"]["llm_call_count"] == 7

    def test_extra_has_per_node_time(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        per_node = result["extra"]["per_node_time"]
        assert isinstance(per_node, dict)
        assert len(per_node) == 7

    def test_extra_has_specialist_outputs(self, minimal_eda):
        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            result = run_multi_agent(minimal_eda)
        sp = result["extra"]["specialist_outputs"]
        assert isinstance(sp, dict)
        expected_nodes = {
            "missing_value_agent", "correlation_agent", "outlier_agent",
            "feature_importance_agent", "preprocessing_planner_agent",
            "algorithm_recommendation_agent", "critic_synthesizer",
        }
        assert expected_nodes.issubset(sp.keys())


class TestRunMultiAgentErrors:
    def test_error_when_langgraph_unavailable(self, minimal_eda):
        with patch("backend.agents.multi_agent.graph.LANGGRAPH_AVAILABLE", False), \
             patch("backend.agents.multi_agent.graph._COMPILED_GRAPH", None):
            result = run_multi_agent(minimal_eda)
        assert result["status"] == "error"
        assert "langgraph" in result["error"].lower()

    def test_error_on_graph_exception(self, minimal_eda):
        with patch("backend.agents.multi_agent.graph._COMPILED_GRAPH") as mock_graph:
            mock_graph.invoke.side_effect = RuntimeError("graph crashed")
            result = run_multi_agent(minimal_eda)
        assert result["status"] == "error"
        assert "graph crashed" in result["error"]

    def test_error_response_has_pipeline_field(self, minimal_eda):
        with patch("backend.agents.multi_agent.graph.LANGGRAPH_AVAILABLE", False), \
             patch("backend.agents.multi_agent.graph._COMPILED_GRAPH", None):
            result = run_multi_agent(minimal_eda)
        assert result["pipeline"] == "multi_agent"


class TestResearchGuarantee:
    def test_eda_not_modified_by_run(self, minimal_eda):
        """
        The EDA result passed to run_multi_agent must be byte-for-byte
        identical after the run.  This ensures M4 and M5 receive identical input.
        """
        import copy
        original = copy.deepcopy(minimal_eda)

        with patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = _side_effects()
            mock_cls.return_value = mock_llm
            run_multi_agent(minimal_eda)

        assert minimal_eda == original
