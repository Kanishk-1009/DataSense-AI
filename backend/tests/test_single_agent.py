"""
Tests for the single-agent pipeline.

All LLM calls are mocked so that these tests run without Ollama installed.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.agents.single_agent import (
    _build_user_message,
    _parse_llm_response,
    run_single_agent,
)


# ---- Fixtures -------------------------------------------------------------

@pytest.fixture
def minimal_eda():
    return {
        "numeric_statistics": {"age": {"mean": 35.0, "median": 33.0, "std": 10.0}},
        "correlation_analysis": {
            "matrix": {},
            "highly_correlated_pairs": [],
            "cramers_v": [],
            "point_biserial": [],
        },
        "outliers": {},
        "missingness": {
            "summary": {
                "total_missing_cells": 0,
                "total_cells": 500,
                "overall_missing_percentage": 0.0,
                "columns_with_missing": 0,
                "mar_columns": [],
                "mcar_columns": [],
                "complete_columns": 10,
            },
            "columns": {},
        },
        "quality_score": {
            "score": 92.0,
            "grade": "Excellent",
            "status": "🟢 Excellent Quality",
        },
        "insights": {"count": 2, "insights": ["No missing values.", "No duplicates."]},
        "feature_summary": {"count": 2, "features": {}},
        "ml_task": {
            "task": "classification",
            "task_type": "binary_classification",
            "target": "survived",
            "confidence": 0.98,
        },
        "ml_recommendation": {"status": "available", "recommended_models": []},
        "preprocessing": {"status": "available", "recommendations": []},
        "feature_importance": {"status": "unavailable"},
        "report": {
            "dataset": {"rows": 100, "columns": 5},
            "quality": {"score": 92.0, "grade": "Excellent"},
        },
    }


@pytest.fixture
def valid_llm_json():
    return json.dumps({
        "narrative": "This is a clean dataset with strong predictive signal.",
        "key_risks": ["Slight class imbalance.", "Low sample size."],
        "recommendations": ["Collect more data.", "Use cross-validation."],
        "confidence": 0.85,
    })


# ---- _build_user_message --------------------------------------------------

class TestBuildUserMessage:
    def test_returns_string(self, minimal_eda):
        msg = _build_user_message(minimal_eda)
        assert isinstance(msg, str)

    def test_contains_eda_keys(self, minimal_eda):
        msg = _build_user_message(minimal_eda)
        assert "numeric_statistics" in msg
        assert "quality_score" in msg

    def test_is_valid_json_embedded(self, minimal_eda):
        msg = _build_user_message(minimal_eda)
        # Strip the preamble line and parse the JSON block
        json_start = msg.index("{")
        json.loads(msg[json_start:])  # Should not raise


# ---- _parse_llm_response --------------------------------------------------

class TestParseLlmResponse:
    def test_parses_valid_json(self, valid_llm_json):
        result = _parse_llm_response(valid_llm_json)
        assert result["narrative"] == "This is a clean dataset with strong predictive signal."
        assert len(result["key_risks"]) == 2
        assert result["confidence"] == 0.85

    def test_strips_markdown_fences(self):
        raw = "```json\n{\"narrative\": \"hello\", \"key_risks\": [], \"recommendations\": [], \"confidence\": 0.5}\n```"
        result = _parse_llm_response(raw)
        assert result.get("narrative") == "hello"

    def test_fallback_on_invalid_json(self):
        result = _parse_llm_response("This is plain text, not JSON.")
        assert result["narrative"] == "This is plain text, not JSON."
        assert "_parse_error" in result

    def test_empty_string_fallback(self):
        result = _parse_llm_response("")
        assert "_parse_error" in result


# ---- run_single_agent (mocked LLM) ----------------------------------------

class TestRunSingleAgent:
    def _make_mock_response(self, content: str):
        mock_response = MagicMock()
        mock_response.content = content
        return mock_response

    def test_returns_dict_on_success(self, minimal_eda, valid_llm_json):
        with patch(
            "backend.agents.single_agent.ChatOllama"
        ) as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = self._make_mock_response(valid_llm_json)
            mock_cls.return_value = mock_llm

            result = run_single_agent(minimal_eda, model="test-model")

        assert isinstance(result, dict)

    def test_success_status(self, minimal_eda, valid_llm_json):
        with patch("backend.agents.single_agent.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = self._make_mock_response(valid_llm_json)
            mock_cls.return_value = mock_llm

            result = run_single_agent(minimal_eda, model="test-model")

        assert result["status"] == "success"

    def test_narrative_present(self, minimal_eda, valid_llm_json):
        with patch("backend.agents.single_agent.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = self._make_mock_response(valid_llm_json)
            mock_cls.return_value = mock_llm

            result = run_single_agent(minimal_eda)

        assert result["narrative"] is not None

    def test_key_risks_is_list(self, minimal_eda, valid_llm_json):
        with patch("backend.agents.single_agent.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = self._make_mock_response(valid_llm_json)
            mock_cls.return_value = mock_llm

            result = run_single_agent(minimal_eda)

        assert isinstance(result["key_risks"], list)

    def test_recommendations_is_list(self, minimal_eda, valid_llm_json):
        with patch("backend.agents.single_agent.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = self._make_mock_response(valid_llm_json)
            mock_cls.return_value = mock_llm

            result = run_single_agent(minimal_eda)

        assert isinstance(result["recommendations"], list)

    def test_execution_time_present(self, minimal_eda, valid_llm_json):
        with patch("backend.agents.single_agent.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = self._make_mock_response(valid_llm_json)
            mock_cls.return_value = mock_llm

            result = run_single_agent(minimal_eda)

        assert "execution_time_seconds" in result
        assert result["execution_time_seconds"] >= 0.0

    def test_error_on_llm_exception(self, minimal_eda):
        with patch("backend.agents.single_agent.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = ConnectionError("Ollama not running")
            mock_cls.return_value = mock_llm

            result = run_single_agent(minimal_eda)

        assert result["status"] == "error"
        assert "Ollama not running" in result["error"]
        assert result["narrative"] is None

    def test_model_name_in_response(self, minimal_eda, valid_llm_json):
        with patch("backend.agents.single_agent.ChatOllama") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = self._make_mock_response(valid_llm_json)
            mock_cls.return_value = mock_llm

            result = run_single_agent(minimal_eda, model="llama3.1:8b")

        assert result["model"] == "llama3.1:8b"

    def test_langchain_unavailable_returns_error(self, minimal_eda):
        with patch(
            "backend.agents.single_agent.LANGCHAIN_AVAILABLE", False
        ):
            result = run_single_agent(minimal_eda)

        assert result["status"] == "error"
        assert "langchain" in result["error"].lower()
