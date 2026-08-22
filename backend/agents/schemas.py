"""
Shared Pydantic schemas for agent responses.

Defining a formal schema here ensures that both the single-agent (Phase 2)
and the future multi-agent (Phase 3) pipelines return identically shaped
output, making them directly comparable in the evaluation phase (M6).
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """
    Standardised response schema for all agent pipelines.

    Both the single-agent (LangChain) and multi-agent (LangGraph)
    implementations must return an object that is serialisable to this
    shape so that evaluation metrics can be applied uniformly.
    """

    # --- Identity -----------------------------------------------------------
    status: str = Field(
        description="'success' | 'error' | 'unavailable'",
    )
    model: str = Field(
        description="Ollama model identifier used for this run.",
    )
    pipeline: str = Field(
        description="Pipeline type: 'single_agent' | 'multi_agent'.",
    )

    # --- Timing -------------------------------------------------------------
    execution_time_seconds: float = Field(
        ge=0.0,
        description="Wall-clock time for the full agent pipeline in seconds.",
    )

    # --- LLM Output ---------------------------------------------------------
    narrative: str | None = Field(
        default=None,
        description=(
            "Plain-English summary of the dataset produced by the LLM. "
            "None when status != 'success'."
        ),
    )
    key_risks: list[str] = Field(
        default_factory=list,
        description="Top risks identified by the LLM (3–5 items).",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Prioritised, actionable recommendations (3–6 items).",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Self-reported LLM confidence (0.0–1.0). "
            "None if the LLM did not return a value."
        ),
    )

    # --- Error details (only populated when status == 'error') --------------
    error: str | None = Field(
        default=None,
        description="Error message when status == 'error'.",
    )

    # --- Optional passthrough fields ----------------------------------------
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Any additional fields returned by the LLM that are not part "
            "of the core schema (e.g. _parse_error)."
        ),
    )

    model_config = {"extra": "allow"}
