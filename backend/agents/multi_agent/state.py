"""
LangGraph shared state for the multi-agent pipeline.

Design rules
------------
- ``eda`` is set once at graph entry and is NEVER modified by any node.
  All nodes read from it; none write to it.  This guarantees M4 and M5
  receive byte-for-byte identical EDA input.

- ``specialist_outputs`` and ``per_node_time`` use merge reducers so that
  parallel nodes can each write their slice without clobbering each other.

- ``llm_call_count`` uses an additive reducer so each node's increment is
  accumulated correctly across concurrent branches.

- ``final_response`` is written only by the Critic/Synthesizer node.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


# ---------------------------------------------------------------------------
# Reducers
# ---------------------------------------------------------------------------

def _merge_dicts(a: dict, b: dict) -> dict:
    """Shallow merge: b's keys overwrite a's keys."""
    result = dict(a)
    result.update(b)
    return result


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class MultiAgentState(TypedDict):
    # ------------------------------------------------------------------
    # Input — set at graph entry, never modified
    # ------------------------------------------------------------------
    eda: dict
    model: str
    base_url: str
    target: str | None

    # ------------------------------------------------------------------
    # Specialist outputs — merged across parallel branches
    # Each node writes:
    #   specialist_outputs[node_name] = {"findings": ..., "risk_level": ...,
    #                                    "recommendations": [...]}
    # ------------------------------------------------------------------
    specialist_outputs: Annotated[dict, _merge_dicts]

    # ------------------------------------------------------------------
    # Timing — merged across parallel branches
    # Each node writes:  per_node_time[node_name] = float (seconds)
    # ------------------------------------------------------------------
    per_node_time: Annotated[dict, _merge_dicts]

    # ------------------------------------------------------------------
    # LLM call counter — accumulated across all nodes
    # ------------------------------------------------------------------
    llm_call_count: Annotated[int, operator.add]

    # ------------------------------------------------------------------
    # Final output — written by the Critic/Synthesizer
    # ------------------------------------------------------------------
    final_response: dict | None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def initial_state(
    eda: dict,
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    target: str | None = None,
) -> MultiAgentState:
    """
    Return a correctly typed initial state dict for ``graph.invoke()``.

    All mutable containers are freshly constructed to avoid shared
    references across runs.
    """
    return MultiAgentState(
        eda=eda,
        model=model,
        base_url=base_url,
        target=target,
        specialist_outputs={},
        per_node_time={},
        llm_call_count=0,
        final_response=None,
    )
