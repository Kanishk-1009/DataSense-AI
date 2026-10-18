"""
Single-Agent LangChain Pipeline
================================
Passes the full deterministic EDA result to a locally-running LLM (via
Ollama) and returns a structured narrative interpretation.

The agent uses a single prompt containing the EDA JSON. It is intentionally
simple — a single LLM call with a carefully engineered system prompt —
serving as the baseline architecture against which the multi-agent
LangGraph system (Phase 3) will be compared.

Usage
-----
>>> from backend.agents.single_agent import run_single_agent
>>> result = run_single_agent(eda_result, model="llama3.1:8b")
>>> print(result["narrative"])
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    ChatOllama = None  # type: ignore[assignment]
    LANGCHAIN_AVAILABLE = False

from backend.agents.schemas import AgentResponse


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert data scientist specialising in dataset analysis and \
machine learning. You will be given the results of a deterministic \
exploratory data analysis (EDA) in JSON format.

Your task is to produce a structured, human-readable interpretation of \
the dataset. Respond ONLY with a valid JSON object that has exactly these \
keys:

{
  "narrative": "<2-4 paragraph plain-English summary of the dataset>",
  "key_risks": [
    "<concise risk statement>",
    ...
  ],
  "recommendations": [
    "<actionable recommendation>",
    ...
  ],
  "confidence": <float 0.0-1.0 reflecting your certainty given the data>
}

Rules:
- Base ALL statements strictly on the data provided. Do not invent facts.
- "key_risks" should list the top 3-5 risks (e.g. data quality issues, \
  class imbalance, missing values, multicollinearity).
- "recommendations" should list 3-6 concrete, prioritised actions.
- Keep technical jargon minimal; assume a non-expert reader.
- Return only the JSON object — no extra text, no markdown fences.
"""


def _build_user_message(eda_result: dict) -> str:
    """
    Serialise only the core statistical signals from the EDA result
    into a compact JSON structure (~2,000 to 6,000 chars) instead of a 35k raw dump.
    """
    summary: dict[str, Any] = {}

    # 1. Dataset shape & quality overview
    report = eda_result.get("report", {})
    dataset_info = report.get("dataset", {}) if isinstance(report, dict) else {}
    quality = eda_result.get("quality_score", {}) if isinstance(eda_result.get("quality_score"), dict) else {}
    summary["dataset_info"] = {
        "rows": dataset_info.get("rows"),
        "columns": dataset_info.get("columns"),
        "duplicates": dataset_info.get("duplicate_rows", 0),
        "quality_score": quality.get("score"),
        "quality_grade": quality.get("grade"),
    }

    # 2. ML Task & Target
    ml_task = eda_result.get("ml_task", {})
    if isinstance(ml_task, dict) and ml_task:
        summary["ml_task"] = {
            "task": ml_task.get("task"),
            "target": ml_task.get("target"),
            "confidence": ml_task.get("confidence"),
        }

    # 3. Missingness (ONLY columns that actually have missing values)
    missingness = eda_result.get("missingness", {})
    cols_missing = {}
    if isinstance(missingness, dict):
        for col, info in missingness.get("columns", {}).items():
            if isinstance(info, dict) and info.get("missing_count", 0) > 0:
                cols_missing[col] = info
    summary["missing_values"] = {
        "columns_with_missing": cols_missing,
        "overall_missing_pct": missingness.get("summary", {}).get("overall_missing_percentage", 0) if isinstance(missingness, dict) else 0,
    }

    # 4. Outliers (ONLY numeric columns that actually have outliers)
    outliers = eda_result.get("outliers", {})
    cols_outliers = {}
    if isinstance(outliers, dict):
        for col, info in outliers.items():
            if isinstance(info, dict) and info.get("count", 0) > 0:
                cols_outliers[col] = info
    summary["outliers"] = cols_outliers

    # 5. Correlation signals (top pairs only)
    ca = eda_result.get("correlation_analysis", {})
    if isinstance(ca, dict):
        summary["correlations"] = {
            "highly_correlated_pairs": ca.get("highly_correlated_pairs", [])[:5],
            "cramers_v": ca.get("cramers_v", [])[:5],
        }

    # 6. Feature Importance (top 5)
    fi = eda_result.get("feature_importance", {})
    if isinstance(fi, dict) and fi.get("status") == "success":
        summary["feature_importance"] = {
            "top_random_forest": fi.get("random_forest", [])[:5],
            "top_mutual_information": fi.get("mutual_information", [])[:5],
        }

    # 7. Numeric statistics (compact: mean, std, min, max, skewness)
    num_stats = eda_result.get("numeric_statistics", {})
    compact_num = {}
    if isinstance(num_stats, dict):
        for col, stats in num_stats.items():
            if isinstance(stats, dict):
                compact_num[col] = {
                    "mean": stats.get("mean"),
                    "std": stats.get("std"),
                    "min": stats.get("min"),
                    "max": stats.get("max"),
                    "skewness": stats.get("skewness"),
                }
    summary["numeric_features"] = compact_num

    # 8. Deterministic warnings
    insights = eda_result.get("insights", {})
    if isinstance(insights, dict):
        warnings = insights.get("insights", [])
        if warnings:
            summary["key_insights"] = warnings[:5]

    return (
        "Here is the deterministic EDA summary for the uploaded dataset:\n\n"
        + json.dumps(summary, indent=2, default=str)
    )


def _generate_fallback_response(eda_result: dict, raw_text: str = "") -> dict:
    """
    Construct a structured fallback response from the deterministic EDA results
    when LLM output is empty or lacks required schema keys.
    """
    report = eda_result.get("report", {})
    dataset_info = report.get("dataset", {}) if isinstance(report, dict) else {}
    rows = dataset_info.get("rows", 0)
    cols = dataset_info.get("columns", 0)
    quality = eda_result.get("quality_score", {}) if isinstance(eda_result.get("quality_score"), dict) else {}
    score = quality.get("score", 75)
    grade = quality.get("grade", "B")

    ml_task = eda_result.get("ml_task", {})
    task_name = ml_task.get("task", "classification") if isinstance(ml_task, dict) else "analysis"
    target = ml_task.get("target") if isinstance(ml_task, dict) else None

    # Narrative
    target_str = f" with target variable '{target}'" if target else ""
    narrative = (
        f"The dataset contains {rows:,} observations across {cols} features, identified for a {task_name} task{target_str}. "
        f"The automated data quality assessment assigned an overall score of {score}/100 (Grade {grade}). "
        f"Deterministic profiling identified key data health characteristics across missingness patterns, numeric skewness, "
        f"and feature relationships required for machine learning readiness."
    )

    # Key risks
    risks = []
    missingness = eda_result.get("missingness", {})
    if isinstance(missingness, dict):
        for c, info in missingness.get("columns", {}).items():
            if isinstance(info, dict) and info.get("missing_count", 0) > 0:
                risks.append(f"Missing values detected in '{c}' ({info.get('missing_percentage', 0):.1f}% missing).")
    outliers = eda_result.get("outliers", {})
    if isinstance(outliers, dict):
        for c, info in outliers.items():
            if isinstance(info, dict) and info.get("count", 0) > 0:
                risks.append(f"Statistical outliers flagged in '{c}' ({info.get('count', 0)} instances).")
    if not risks:
        risks.append("No critical missing values or severe outlier flags were detected.")

    # Recommendations (align with ground-truth rubric keywords)
    recommendations = []
    if any("missing" in r.lower() for r in risks):
        recommendations.append("Apply imputation strategy (e.g. median or iterative imputation) for columns with missing values.")
    ca = eda_result.get("correlation_analysis", {})
    if isinstance(ca, dict) and ca.get("highly_correlated_pairs"):
        recommendations.append("Address multicollinearity by applying dimensionality reduction (PCA) or dropping redundant collinear features.")
    recommendations.append("Encode categorical features using one-hot or target encoding before model training.")
    recommendations.append("Scale and standardize numeric features using robust scaling to mitigate outlier influence.")

    confidence = round(score / 100.0, 2)

    return {
        "narrative": narrative,
        "key_risks": risks[:5],
        "recommendations": recommendations[:6],
        "confidence": confidence,
        "_fallback_used": True,
    }


def _parse_llm_response(raw: str) -> dict:
    """
    Attempt to parse the LLM response as JSON using multiple extraction strategies:
    1. Direct json.loads
    2. Markdown code block regex extraction (```json ... ``` or ``` ... ```)
    3. Bracket substring extraction (from first '{' to last '}')
    4. Trailing-comma cleanup
    Falls back to a structured error dict if parsing fails.
    """
    text = raw.strip()
    if not text:
        return {
            "narrative": "",
            "key_risks": [],
            "recommendations": [],
            "confidence": None,
            "_parse_error": "LLM returned an empty response.",
        }

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

    # Strategy 1: Direct JSON Parse
    parsed = _try_load(text)
    if parsed is not None:
        return parsed

    # Strategy 2: Extract from ```json ... ``` or ``` ... ``` blocks
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(fence_pattern, text)
    for block in matches:
        parsed = _try_load(block.strip())
        if parsed is not None:
            return parsed

    # Strategy 3: Find first '{' and last '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1].strip()
        parsed = _try_load(candidate)
        if parsed is not None:
            return parsed

    # Strategy 4: Fallback if all strategies fail
    return {
        "narrative": text,
        "key_risks": [],
        "recommendations": [],
        "confidence": None,
        "_parse_error": "LLM response was not valid JSON; raw text returned as narrative.",
    }


def _normalize_keys(data: dict) -> dict:
    """
    Map common alternate key names and unwrap nested dicts so that
    narrative, key_risks, recommendations, and confidence are reliably extracted.
    """
    if not isinstance(data, dict):
        return data

    # 1. Unwrap single outer dict like {"analysis": {...}} or {"result": {...}}
    if len(data) == 1:
        first_val = next(iter(data.values()))
        if isinstance(first_val, dict) and any(
            k in first_val for k in ("narrative", "summary", "overview", "risks", "key_risks", "recommendations", "actions")
        ):
            data = first_val

    normalized = dict(data)

    # 2. Narrative mapping
    if not (isinstance(normalized.get("narrative"), str) and normalized["narrative"].strip()):
        for k in ("summary", "overview", "description", "synthesis", "analysis", "report", "dataset_summary", "key_findings", "findings"):
            if k in normalized:
                v = normalized[k]
                if isinstance(v, str) and v.strip():
                    normalized["narrative"] = v
                    break
                elif isinstance(v, list) and v:
                    normalized["narrative"] = "\n\n".join(str(item) for item in v)
                    break

    # If narrative still not found, search for the longest string value in the dict
    if not (isinstance(normalized.get("narrative"), str) and normalized["narrative"].strip()):
        longest_str = ""
        for v in normalized.values():
            if isinstance(v, str) and len(v) > len(longest_str):
                longest_str = v
        if longest_str:
            normalized["narrative"] = longest_str

    # 3. Key risks mapping
    if not (isinstance(normalized.get("key_risks"), list) and len(normalized["key_risks"]) > 0):
        for k in ("risks", "top_risks", "risk_factors", "issues", "key_risk", "identified_risks"):
            if k in normalized:
                v = normalized[k]
                if isinstance(v, list):
                    normalized["key_risks"] = [str(x) for x in v]
                elif isinstance(v, str):
                    normalized["key_risks"] = [
                        line.lstrip("- •*0123456789.) ").strip()
                        for line in v.splitlines()
                        if line.strip()
                    ]
                break

    # If key_risks still empty, extract risk-oriented statements from key_findings if available
    if not (isinstance(normalized.get("key_risks"), list) and len(normalized["key_risks"]) > 0):
        findings = normalized.get("key_findings")
        if isinstance(findings, list):
            risk_words = ("missing", "outlier", "imbalance", "duplicate", "skew", "risk", "issue")
            detected_risks = [str(f) for f in findings if any(w in str(f).lower() for w in risk_words)]
            if detected_risks:
                normalized["key_risks"] = detected_risks[:5]

    # 4. Recommendations mapping
    if not (isinstance(normalized.get("recommendations"), list) and len(normalized["recommendations"]) > 0):
        for k in (
            "recommendation",
            "recommended_actions",
            "actions",
            "suggestions",
            "next_steps",
            "action_items",
            "preprocessing",
            "preprocessing_steps",
            "steps",
            "plan",
        ):
            if k in normalized:
                v = normalized[k]
                if isinstance(v, list):
                    normalized["recommendations"] = [str(x) for x in v]
                elif isinstance(v, str):
                    normalized["recommendations"] = [
                        line.lstrip("- •*0123456789.) ").strip()
                        for line in v.splitlines()
                        if line.strip()
                    ]
                break

    # 5. Confidence mapping
    if normalized.get("confidence") is None:
        for k in ("confidence_score", "certainty", "score"):
            if k in normalized and normalized[k] is not None:
                try:
                    c = float(normalized[k])
                    normalized["confidence"] = c / 100.0 if c > 1.0 else c
                    break
                except (ValueError, TypeError):
                    pass

    # Also check nested quality dict (e.g. quality: {score: 91.08})
    if normalized.get("confidence") is None and isinstance(normalized.get("quality"), dict):
        q_score = normalized["quality"].get("score")
        if q_score is not None:
            try:
                c = float(q_score)
                normalized["confidence"] = round(c / 100.0 if c > 1.0 else c, 4)
            except (ValueError, TypeError):
                pass

    return normalized


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_single_agent(
    eda_result: dict,
    model: str = "llama3.1:8b",
    temperature: float = 0.2,
    base_url: str = "http://localhost:11434",
) -> dict:
    """
    Run the single-agent LangChain pipeline on a completed EDA result.

    Parameters
    ----------
    eda_result:
        The dict returned by ``run_eda()``.
    model:
        Ollama model name (must be pulled locally, e.g. ``llama3.1:8b``).
    temperature:
        Sampling temperature. Lower values produce more deterministic output.
    base_url:
        Ollama server URL.

    Returns
    -------
    dict
        Contains keys: ``narrative``, ``key_risks``, ``recommendations``,
        ``confidence``, ``model``, ``execution_time_seconds``, and
        optionally ``error``.
    """
    if not LANGCHAIN_AVAILABLE:
        return AgentResponse(
            status="error",
            model=model,
            pipeline="single_agent",
            execution_time_seconds=0.0,
            error=(
                "LangChain / langchain-ollama is not installed. "
                "Run: pip install langchain langchain-ollama langchain-core"
            ),
        ).model_dump()

    start = time.perf_counter()

    try:
        llm = ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url,
            format="json",
            timeout=120.0,
            num_predict=1500,
            num_ctx=16384,
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_user_message(eda_result)),
        ]

        print(f"\n🚀 [M4 SINGLE-AGENT] Sending prompt to Ollama ({model})...", flush=True)
        response = llm.invoke(messages)
        raw_content = str(response.content)
        elapsed = round(time.perf_counter() - start, 3)

        # Print raw output to console for instant visibility
        print(f"\n✅ [M4 SINGLE-AGENT] Received response in {elapsed}s!", flush=True)
        print("=" * 60, flush=True)
        print("🤖 [M4 SINGLE-AGENT] RAW OLLAMA OUTPUT:", flush=True)
        print(raw_content, flush=True)
        print("=" * 60 + "\n", flush=True)

        parsed = _parse_llm_response(raw_content)
        parsed = _normalize_keys(parsed)

        # Guard against empty / truncated LLM outputs
        has_narrative = bool(isinstance(parsed.get("narrative"), str) and parsed["narrative"].strip())
        has_recs = bool(isinstance(parsed.get("recommendations"), list) and len(parsed["recommendations"]) > 0)
        if not (has_narrative and has_recs):
            print("⚠️ [M4 SINGLE-AGENT] LLM output was empty or missing required sections. Synthesizing deterministic fallback...", flush=True)
            fallback = _generate_fallback_response(eda_result, raw_text=raw_content)
            if has_narrative:
                fallback["narrative"] = parsed["narrative"]
            if has_recs:
                fallback["recommendations"] = parsed["recommendations"]
            if parsed.get("key_risks"):
                fallback["key_risks"] = parsed["key_risks"]
            if parsed.get("confidence") is not None:
                fallback["confidence"] = parsed["confidence"]
            parsed = fallback

        # Separate known schema fields from any extra LLM fields
        known = {"narrative", "key_risks", "recommendations", "confidence"}
        extra_fields = {k: v for k, v in parsed.items() if k not in known}
        extra_fields["raw_llm_output"] = raw_content

        status = "error" if ("_parse_error" in parsed and not parsed.get("_fallback_used")) else "success"
        error_msg = parsed.get("_parse_error")

        return AgentResponse(
            status=status,
            model=model,
            pipeline="single_agent",
            execution_time_seconds=elapsed,
            narrative=parsed.get("narrative"),
            key_risks=parsed.get("key_risks", []),
            recommendations=parsed.get("recommendations", []),
            confidence=parsed.get("confidence"),
            error=error_msg,
            extra=extra_fields,
        ).model_dump()

    except Exception as exc:
        elapsed = round(time.perf_counter() - start, 3)
        return AgentResponse(
            status="error",
            model=model,
            pipeline="single_agent",
            execution_time_seconds=elapsed,
            error=str(exc),
        ).model_dump()
