"""
Tests for MultiAgentState initialisation and reducer behaviour.
"""

import operator
import pytest

from backend.agents.multi_agent.state import (
    MultiAgentState,
    _merge_dicts,
    initial_state,
)


class TestMergeDicts:
    def test_merges_disjoint_keys(self):
        a = {"x": 1}
        b = {"y": 2}
        result = _merge_dicts(a, b)
        assert result == {"x": 1, "y": 2}

    def test_b_overwrites_a(self):
        a = {"x": 1}
        b = {"x": 99}
        result = _merge_dicts(a, b)
        assert result["x"] == 99

    def test_does_not_mutate_inputs(self):
        a = {"x": 1}
        b = {"y": 2}
        _merge_dicts(a, b)
        assert a == {"x": 1}
        assert b == {"y": 2}

    def test_empty_a(self):
        result = _merge_dicts({}, {"k": "v"})
        assert result == {"k": "v"}

    def test_empty_b(self):
        result = _merge_dicts({"k": "v"}, {})
        assert result == {"k": "v"}


class TestInitialState:
    def test_returns_dict(self):
        state = initial_state(eda={"foo": "bar"})
        assert isinstance(state, dict)

    def test_eda_set_correctly(self):
        eda = {"numeric_statistics": {}}
        state = initial_state(eda=eda)
        assert state["eda"] is eda

    def test_defaults(self):
        state = initial_state(eda={})
        assert state["model"] == "llama3.1:8b"
        assert state["base_url"] == "http://localhost:11434"
        assert state["target"] is None

    def test_custom_model(self):
        state = initial_state(eda={}, model="mistral:7b")
        assert state["model"] == "mistral:7b"

    def test_specialist_outputs_empty(self):
        state = initial_state(eda={})
        assert state["specialist_outputs"] == {}

    def test_per_node_time_empty(self):
        state = initial_state(eda={})
        assert state["per_node_time"] == {}

    def test_llm_call_count_zero(self):
        state = initial_state(eda={})
        assert state["llm_call_count"] == 0

    def test_final_response_none(self):
        state = initial_state(eda={})
        assert state["final_response"] is None

    def test_fresh_containers_each_call(self):
        s1 = initial_state(eda={})
        s2 = initial_state(eda={})
        s1["specialist_outputs"]["x"] = 1
        assert "x" not in s2["specialist_outputs"]

    def test_all_required_keys_present(self):
        required = {
            "eda", "model", "base_url", "target",
            "specialist_outputs", "per_node_time",
            "llm_call_count", "final_response",
        }
        state = initial_state(eda={})
        assert required.issubset(state.keys())
