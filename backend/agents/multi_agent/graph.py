"""
LangGraph graph assembly and public ``run_multi_agent()`` entry point.

Graph topology
--------------

                       START
                         │
          ┌──────────────┼──────────────┐   (parallel fan-out)
          ▼              ▼              ▼
   missing_value_    correlation_    outlier_
      agent             agent         agent
          │              │              │
          └──────────────┼──────────────┘   (fan-in: all must complete)
                         ▼
              feature_importance_agent
                         ▼
             preprocessing_planner_agent
                         ▼
          algorithm_recommendation_agent
                         ▼
                 critic_synthesizer
                         │
                        END

Research guarantee
------------------
``run_multi_agent()`` accepts the *already-computed* EDA result dict.
It does NOT recompute the EDA.  M4 and M5 therefore receive byte-for-byte
identical input, making the architecture the sole experimental variable.
"""

from __future__ import annotations

import time

try:
    from langgraph.graph import StateGraph, START, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from backend.agents.multi_agent.state import MultiAgentState, initial_state
from backend.agents.multi_agent.nodes import (
    missing_value_node,
    correlation_node,
    outlier_node,
    feature_importance_node,
    preprocessing_node,
    algorithm_recommendation_node,
    critic_synthesizer_node,
)
from backend.agents.schemas import AgentResponse


# ---------------------------------------------------------------------------
# Graph compilation (done once at import time)
# ---------------------------------------------------------------------------

def _build_graph() -> "StateGraph | None":
    if not LANGGRAPH_AVAILABLE:
        return None

    graph = StateGraph(MultiAgentState)

    # Register nodes
    graph.add_node("missing_value_agent", missing_value_node)
    graph.add_node("correlation_agent", correlation_node)
    graph.add_node("outlier_agent", outlier_node)
    graph.add_node("feature_importance_agent", feature_importance_node)
    graph.add_node("preprocessing_planner_agent", preprocessing_node)
    graph.add_node("algorithm_recommendation_agent", algorithm_recommendation_node)
    graph.add_node("critic_synthesizer", critic_synthesizer_node)

    # Parallel fan-out from START
    graph.add_edge(START, "missing_value_agent")
    graph.add_edge(START, "correlation_agent")
    graph.add_edge(START, "outlier_agent")

    # Fan-in: all three parallel nodes must finish before feature importance
    graph.add_edge("missing_value_agent", "feature_importance_agent")
    graph.add_edge("correlation_agent", "feature_importance_agent")
    graph.add_edge("outlier_agent", "feature_importance_agent")

    # Sequential chain after fan-in
    graph.add_edge("feature_importance_agent", "preprocessing_planner_agent")
    graph.add_edge("preprocessing_planner_agent", "algorithm_recommendation_agent")
    graph.add_edge("algorithm_recommendation_agent", "critic_synthesizer")
    graph.add_edge("critic_synthesizer", END)

    return graph.compile()


_COMPILED_GRAPH = _build_graph()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_multi_agent(
    eda_result: dict,
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    target: str | None = None,
) -> dict:
    """
    Run the multi-agent LangGraph pipeline on a completed EDA result.

    Parameters
    ----------
    eda_result:
        The dict returned by ``run_eda()``.  Never modified.
    model:
        Ollama model name (must be pulled locally).
    base_url:
        Ollama server URL.
    target:
        Target column name (informational; forwarded to state).

    Returns
    -------
    dict
        ``AgentResponse.model_dump()`` with ``pipeline == "multi_agent"``.
        Extra fields in ``extra``:
        - ``llm_call_count``     — total LLM calls across all nodes
        - ``per_node_time``      — per-node wall-clock times (seconds)
        - ``specialist_outputs`` — raw outputs from all 7 agents
    """
    if not LANGGRAPH_AVAILABLE or _COMPILED_GRAPH is None:
        return AgentResponse(
            status="error",
            model=model,
            pipeline="multi_agent",
            execution_time_seconds=0.0,
            error=(
                "LangGraph is not installed. "
                "Run: pip install langgraph langchain-ollama"
            ),
        ).model_dump()

    wall_start = time.perf_counter()

    try:
        state = initial_state(
            eda=eda_result,
            model=model,
            base_url=base_url,
            target=target,
        )

        final_state: MultiAgentState = _COMPILED_GRAPH.invoke(state)

        wall_elapsed = round(time.perf_counter() - wall_start, 3)

        # Retrieve the partial final_response built by critic_synthesizer_node
        fr = final_state.get("final_response") or {}

        # Overwrite execution_time_seconds with the true wall-clock total
        fr["execution_time_seconds"] = wall_elapsed

        # Populate the extra fields with full state metadata
        fr.setdefault("extra", {})
        fr["extra"]["llm_call_count"] = final_state.get("llm_call_count", 0)
        fr["extra"]["per_node_time"] = final_state.get("per_node_time", {})
        fr["extra"]["specialist_outputs"] = final_state.get(
            "specialist_outputs", {}
        )

        # Validate through AgentResponse for schema guarantee
        return AgentResponse(**fr).model_dump()

    except Exception as exc:
        wall_elapsed = round(time.perf_counter() - wall_start, 3)
        return AgentResponse(
            status="error",
            model=model,
            pipeline="multi_agent",
            execution_time_seconds=wall_elapsed,
            error=str(exc),
        ).model_dump()
