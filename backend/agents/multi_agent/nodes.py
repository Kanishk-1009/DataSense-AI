"""
LangGraph node functions for the multi-agent pipeline.

Node contract
-------------
Every node function:
1. Receives the full ``MultiAgentState``.
2. Extracts only its relevant EDA slice — never modifies ``state["eda"]``.
3. Makes exactly one ``ChatOllama`` call.
4. Returns a **partial state dict** containing only the keys it writes.
   LangGraph merges this with the existing state using the registered reducers.

Return shape for a node that writes specialist output::

    {
        "specialist_outputs": {"<node_name>": {...}},
        "per_node_time": {"<node_name>": <float>},
        "llm_call_count": 1,
    }

Errors are caught and stored under ``specialist_outputs[node_name]["error"]``
so the graph can continue to the Critic even if one specialist fails.
"""

from __future__ import annotations

import json
import re
import time

try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    ChatOllama = None  # type: ignore[assignment]
    LANGCHAIN_AVAILABLE = False

from backend.agents.multi_agent.state import MultiAgentState
from backend.agents.multi_agent.prompts import (
    MISSING_VALUE_PROMPT,
    CORRELATION_PROMPT,
    OUTLIER_PROMPT,
    FEATURE_IMPORTANCE_PROMPT,
    PREPROCESSING_PROMPT,
    ALGORITHM_PROMPT,
    CRITIC_SYNTHESIZER_PROMPT,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_llm(state: MultiAgentState) -> "ChatOllama":
    return ChatOllama(
        model=state["model"],
        temperature=0.2,
        base_url=state["base_url"],
        format="json",
        timeout=120.0,
        num_predict=1000,
    )


def _call_llm(llm: "ChatOllama", system_prompt: str, user_content: str, agent_name: str = "") -> dict:
    """
    Invoke the LLM and parse the JSON response using robust extraction.
    Returns the parsed dict, or a dict with an ``_parse_error`` key on failure.
    """
    if agent_name:
        print(f"🤖 [M5 MULTI-AGENT] Running specialist: {agent_name}...", flush=True)
    start_call = time.perf_counter()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(messages)
    raw = response.content.strip()

    if agent_name:
        elapsed = round(time.perf_counter() - start_call, 2)
        print(f"✅ [M5 MULTI-AGENT] Completed: {agent_name} ({elapsed}s)", flush=True)

    def _try_load(candidate: str) -> dict | None:
        try:
            val = json.loads(candidate)
            if isinstance(val, dict):
                return val
        except json.JSONDecodeError:
            try:
                cleaned = re.sub(r",\s*([\]}])", r"\1", candidate)
                val = json.loads(cleaned)
                if isinstance(val, dict):
                    return val
            except Exception:
                pass
        return None

    # Strategy 1: Direct JSON parse
    parsed = _try_load(raw)
    if parsed is not None:
        return parsed

    # Strategy 2: Code fence blocks
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(fence_pattern, raw)
    for block in matches:
        parsed = _try_load(block.strip())
        if parsed is not None:
            return parsed

    # Strategy 3: First '{' to last '}'
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw[start : end + 1].strip()
        parsed = _try_load(candidate)
        if parsed is not None:
            return parsed

    return {
        "raw_response": raw,
        "_parse_error": "LLM response was not valid JSON.",
    }


def _node_unavailable(node_name: str, reason: str) -> dict:
    """Return a partial state indicating LangChain is unavailable."""
    return {
        "specialist_outputs": {
            node_name: {
                "findings": None,
                "risk_level": "unknown",
                "recommendations": [],
                "error": reason,
            }
        },
        "per_node_time": {node_name: 0.0},
        "llm_call_count": 0,
    }


# ---------------------------------------------------------------------------
# Parallel specialist nodes (fan-out from START)
# ---------------------------------------------------------------------------

def missing_value_node(state: MultiAgentState) -> dict:
    node_name = "missing_value_agent"
    if not LANGCHAIN_AVAILABLE:
        return _node_unavailable(node_name, "LangChain not installed.")

    start = time.perf_counter()
    try:
        llm = _get_llm(state)
        missingness = state["eda"].get("missingness", {})
        user_msg = (
            "Analyse the following missingness data and return your findings:\n\n"
            + json.dumps(missingness, indent=2, default=str)
        )
        result = _call_llm(llm, MISSING_VALUE_PROMPT, user_msg, node_name)
    except Exception as exc:
        result = {"error": str(exc), "findings": None,
                  "risk_level": "unknown", "recommendations": []}

    elapsed = round(time.perf_counter() - start, 3)
    return {
        "specialist_outputs": {node_name: result},
        "per_node_time": {node_name: elapsed},
        "llm_call_count": 1,
    }


def correlation_node(state: MultiAgentState) -> dict:
    node_name = "correlation_agent"
    if not LANGCHAIN_AVAILABLE:
        return _node_unavailable(node_name, "LangChain not installed.")

    start = time.perf_counter()
    try:
        llm = _get_llm(state)
        # Trim the full Pearson matrix to a preview to keep context short
        ca = state["eda"].get("correlation_analysis", {})
        matrix = ca.get("matrix", {})
        trimmed = {
            "matrix_preview": dict(list(matrix.items())[:8]),
            "highly_correlated_pairs": ca.get("highly_correlated_pairs", []),
            "cramers_v": ca.get("cramers_v", [])[:10],
            "point_biserial": ca.get("point_biserial", [])[:10],
        }
        user_msg = (
            "Analyse the following correlation data and return your findings:\n\n"
            + json.dumps(trimmed, indent=2, default=str)
        )
        result = _call_llm(llm, CORRELATION_PROMPT, user_msg, node_name)
    except Exception as exc:
        result = {"error": str(exc), "findings": None,
                  "risk_level": "unknown", "recommendations": []}

    elapsed = round(time.perf_counter() - start, 3)
    return {
        "specialist_outputs": {node_name: result},
        "per_node_time": {node_name: elapsed},
        "llm_call_count": 1,
    }


def outlier_node(state: MultiAgentState) -> dict:
    node_name = "outlier_agent"
    if not LANGCHAIN_AVAILABLE:
        return _node_unavailable(node_name, "LangChain not installed.")

    start = time.perf_counter()
    try:
        llm = _get_llm(state)
        outliers = state["eda"].get("outliers", {})
        user_msg = (
            "Analyse the following outlier detection results and return your "
            "findings:\n\n"
            + json.dumps(outliers, indent=2, default=str)
        )
        result = _call_llm(llm, OUTLIER_PROMPT, user_msg, node_name)
    except Exception as exc:
        result = {"error": str(exc), "findings": None,
                  "risk_level": "unknown", "recommendations": []}

    elapsed = round(time.perf_counter() - start, 3)
    return {
        "specialist_outputs": {node_name: result},
        "per_node_time": {node_name: elapsed},
        "llm_call_count": 1,
    }


# ---------------------------------------------------------------------------
# Sequential nodes (fan-in and beyond)
# ---------------------------------------------------------------------------

def feature_importance_node(state: MultiAgentState) -> dict:
    node_name = "feature_importance_agent"
    if not LANGCHAIN_AVAILABLE:
        return _node_unavailable(node_name, "LangChain not installed.")

    start = time.perf_counter()
    try:
        llm = _get_llm(state)
        fi = state["eda"].get("feature_importance", {})
        # Trim to top 15 features for context efficiency
        fi_trimmed = {
            "status": fi.get("status"),
            "task_type": fi.get("task_type"),
            "target": fi.get("target"),
            "random_forest": fi.get("random_forest", [])[:15],
            "mutual_information": fi.get("mutual_information", [])[:15],
        }
        fs = state["eda"].get("feature_summary", {})
        features = fs.get("features", {})
        fs_trimmed = {
            "count": fs.get("count"),
            "features": dict(list(features.items())[:15]),
        }
        payload = {
            "feature_importance": fi_trimmed,
            "feature_summary": fs_trimmed,
        }
        user_msg = (
            "Analyse the following feature importance and summary data:\n\n"
            + json.dumps(payload, indent=2, default=str)
        )
        result = _call_llm(llm, FEATURE_IMPORTANCE_PROMPT, user_msg, node_name)
    except Exception as exc:
        result = {"error": str(exc), "findings": None,
                  "risk_level": "unknown", "recommendations": []}

    elapsed = round(time.perf_counter() - start, 3)
    return {
        "specialist_outputs": {node_name: result},
        "per_node_time": {node_name: elapsed},
        "llm_call_count": 1,
    }


def preprocessing_node(state: MultiAgentState) -> dict:
    node_name = "preprocessing_planner_agent"
    if not LANGCHAIN_AVAILABLE:
        return _node_unavailable(node_name, "LangChain not installed.")

    start = time.perf_counter()
    try:
        llm = _get_llm(state)
        preprocessing = state["eda"].get("preprocessing", {})
        # Inject earlier specialist outputs for context
        specialist_context = {
            k: v for k, v in state["specialist_outputs"].items()
            if k in ("missing_value_agent", "correlation_agent", "outlier_agent")
        }
        payload = {
            "deterministic_preprocessing": preprocessing,
            "specialist_findings": specialist_context,
        }
        user_msg = (
            "Produce a prioritised preprocessing plan based on the following:\n\n"
            + json.dumps(payload, indent=2, default=str)
        )
        result = _call_llm(llm, PREPROCESSING_PROMPT, user_msg, node_name)
    except Exception as exc:
        result = {"error": str(exc), "steps": [], "priority_issues": [],
                  "risk_level": "unknown"}

    elapsed = round(time.perf_counter() - start, 3)
    return {
        "specialist_outputs": {node_name: result},
        "per_node_time": {node_name: elapsed},
        "llm_call_count": 1,
    }


def algorithm_recommendation_node(state: MultiAgentState) -> dict:
    node_name = "algorithm_recommendation_agent"
    if not LANGCHAIN_AVAILABLE:
        return _node_unavailable(node_name, "LangChain not installed.")

    start = time.perf_counter()
    try:
        llm = _get_llm(state)
        ml_task = state["eda"].get("ml_task", {})
        ml_rec = state["eda"].get("ml_recommendation", {})
        specialist_context = {
            k: v for k, v in state["specialist_outputs"].items()
            if k != "algorithm_recommendation_agent"
        }
        payload = {
            "ml_task": ml_task,
            "ml_recommendation": ml_rec,
            "specialist_findings": specialist_context,
        }
        user_msg = (
            "Validate and refine the model recommendations based on the "
            "following data:\n\n"
            + json.dumps(payload, indent=2, default=str)
        )
        result = _call_llm(llm, ALGORITHM_PROMPT, user_msg, node_name)
    except Exception as exc:
        result = {"error": str(exc), "recommended_models": [],
                  "reasoning": [], "risk_level": "unknown"}

    elapsed = round(time.perf_counter() - start, 3)
    return {
        "specialist_outputs": {node_name: result},
        "per_node_time": {node_name: elapsed},
        "llm_call_count": 1,
    }


def critic_synthesizer_node(state: MultiAgentState) -> dict:
    """
    Final node.  Reads ALL specialist outputs + EDA report section.
    Writes the completed ``final_response`` to state.
    """
    node_name = "critic_synthesizer"
    if not LANGCHAIN_AVAILABLE:
        return {
            "specialist_outputs": {node_name: {"error": "LangChain not installed."}},
            "per_node_time": {node_name: 0.0},
            "llm_call_count": 0,
            "final_response": {
                "status": "error",
                "error": "LangChain not installed.",
                "model": state["model"],
                "pipeline": "multi_agent",
                "execution_time_seconds": 0.0,
                "narrative": None,
                "key_risks": [],
                "recommendations": [],
                "confidence": None,
                "extra": {},
            },
        }

    start = time.perf_counter()
    try:
        llm = _get_llm(state)
        payload = {
            "dataset_report": state["eda"].get("report", {}),
            "specialist_outputs": state["specialist_outputs"],
        }
        user_msg = (
            "Synthesise the specialist findings into a final analysis:\n\n"
            + json.dumps(payload, indent=2, default=str)
        )
        result = _call_llm(llm, CRITIC_SYNTHESIZER_PROMPT, user_msg, node_name)
    except Exception as exc:
        result = {
            "narrative": None,
            "key_risks": [],
            "recommendations": [],
            "confidence": None,
            "error": str(exc),
        }

    elapsed = round(time.perf_counter() - start, 3)

    # Build the final AgentResponse-compatible dict
    known = {"narrative", "key_risks", "recommendations", "confidence"}
    extra_fields = {k: v for k, v in result.items() if k not in known}

    final_response = {
        "status": "success" if "error" not in result else "error",
        "model": state["model"],
        "pipeline": "multi_agent",
        # execution_time_seconds will be set by run_multi_agent()
        "execution_time_seconds": 0.0,
        "narrative": result.get("narrative"),
        "key_risks": result.get("key_risks", []),
        "recommendations": result.get("recommendations", []),
        "confidence": result.get("confidence"),
        "error": result.get("error"),
        "extra": {
            **extra_fields,
            # These are filled in by run_multi_agent() after graph completes
            "llm_call_count": 0,
            "per_node_time": {},
            "specialist_outputs": {},
        },
    }

    return {
        "specialist_outputs": {node_name: result},
        "per_node_time": {node_name: elapsed},
        "llm_call_count": 1,
        "final_response": final_response,
    }
