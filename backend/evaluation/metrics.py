"""
M6 Metric Scorers
=================
Pure functions that compute each metric from an ``AgentResponse`` dict.

All scorers are deterministic — given the same inputs they return the same
output, with no LLM calls, no side effects, and no external dependencies.

Metric taxonomy (see schemas.py for full docstrings)
-----------------------------------------------------
STRUCTURAL   : output_completeness
DESCRIPTIVE  : narrative_length_chars, key_risk_count, recommendation_count
SELF-REPORTED: confidence_score
EFFICIENCY   : execution_time_seconds, llm_call_count
CORRECTNESS  : recommendation_accuracy  (M6-B, rubric-based)

Design rule
-----------
Do NOT combine DESCRIPTIVE metrics (counts, lengths) into any quality score.
A higher count is not inherently better.  These metrics are recorded as
observations so the research paper can discuss them in context.

Public API
----------
>>> from backend.evaluation.metrics import score_pipeline
>>> metrics = score_pipeline(agent_response, eda_result)
"""

from __future__ import annotations

import re

from backend.evaluation.schemas import PipelineMetrics, RubricCheckResult
from backend.evaluation.rubric import (
    GROUND_TRUTH_RUBRIC,
    extract_triggered_conditions,
    get_effective_targets,
)


# ---------------------------------------------------------------------------
# Individual scorer functions
# ---------------------------------------------------------------------------

def score_output_completeness(agent_response: dict) -> float:
    """
    STRUCTURAL metric.

    Fraction of required AgentResponse fields that are present and non-empty:
      - narrative      : must be a non-empty string
      - key_risks      : must be a non-empty list
      - recommendations: must be a non-empty list
      - confidence     : must be a non-None float

    Returns
    -------
    float in [0.0, 1.0]
        1.0 = all four fields present; 0.25 = only one present.
    """
    required = 4
    present = 0

    narrative = agent_response.get("narrative")
    if isinstance(narrative, str) and narrative.strip():
        present += 1

    risks = agent_response.get("key_risks", [])
    if isinstance(risks, list) and len(risks) > 0:
        present += 1

    recs = agent_response.get("recommendations", [])
    if isinstance(recs, list) and len(recs) > 0:
        present += 1

    conf = agent_response.get("confidence")
    if isinstance(conf, (int, float)) and conf is not None:
        present += 1

    return round(present / required, 4)


def score_narrative_length(agent_response: dict) -> int:
    """
    DESCRIPTIVE metric.

    Raw character count of the narrative.  Not a quality signal.
    """
    narrative = agent_response.get("narrative") or ""
    return len(str(narrative))


def score_key_risk_count(agent_response: dict) -> int:
    """
    DESCRIPTIVE metric.

    Number of key risks returned.  Not a quality signal.
    """
    risks = agent_response.get("key_risks", [])
    return len(risks) if isinstance(risks, list) else 0


def score_recommendation_count(agent_response: dict) -> int:
    """
    DESCRIPTIVE metric.

    Number of recommendations returned.  Not a quality signal.
    """
    recs = agent_response.get("recommendations", [])
    return len(recs) if isinstance(recs, list) else 0


def score_confidence(agent_response: dict) -> float | None:
    """
    SELF-REPORTED metric.

    LLM-reported confidence.  Informational only — not externally validated.
    Returns None if absent.
    """
    conf = agent_response.get("confidence")
    if conf is None:
        return None
    try:
        value = float(conf)
        return round(max(0.0, min(1.0, value)), 4)
    except (TypeError, ValueError):
        return None


def score_execution_time(agent_response: dict) -> float:
    """
    EFFICIENCY metric.

    Wall-clock time of the agent pipeline in seconds.  Lower is better.
    """
    t = agent_response.get("execution_time_seconds", 0.0)
    try:
        return round(float(t), 3)
    except (TypeError, ValueError):
        return 0.0


def score_llm_call_count(agent_response: dict) -> int:
    """
    EFFICIENCY metric.

    Total LLM invocations.  For M4 = 1; for M5 = 7.
    Read from ``extra.llm_call_count`` (populated by both pipelines).
    Falls back to 1 for the single-agent pipeline which does not write
    this field into ``extra``.
    """
    extra = agent_response.get("extra", {})
    count = extra.get("llm_call_count")
    if count is not None:
        try:
            return int(count)
        except (TypeError, ValueError):
            pass
    # Single-agent pipeline always makes exactly 1 call
    pipeline = agent_response.get("pipeline", "")
    return 1 if pipeline == "single_agent" else 0


# ---------------------------------------------------------------------------
# M6-B: recommendation correctness
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# M6-B: Action-Object Dependency Grammar & Negation Guards
# ---------------------------------------------------------------------------

NEGATION_TOKENS: set[str] = {
    "not", "no", "never", "avoid", "don't", "dont", "shouldn't", "shouldnt",
    "cannot", "cant", "can't", "without", "neither", "nor", "stop", "refrain",
    "prevent", "won't", "wont", "hardly", "scarcely", "rarely",
}


def _split_into_sentences(text: str) -> list[str]:
    """
    Split a block of text into distinct sentences and list items.
    Preserves list item boundaries (newlines, bullet points) and punctuation (.!?).
    """
    if not text or not isinstance(text, str):
        return []
    lines = re.split(r"[\n\r]+", text)
    sentences: list[str] = []
    for line in lines:
        line = line.strip()
        line = re.sub(r"^[\s*\->•\d\.\)]+\s*", "", line).strip()
        if not line:
            continue
        parts = re.split(r"(?<=[.!?])\s+", line)
        for part in parts:
            p = part.strip()
            if p:
                sentences.append(p)
    return sentences


def _tokenize_sentence(sentence: str) -> list[str]:
    """
    Extract alphanumeric tokens, preserving apostrophes for contractions (e.g. don't).
    """
    return re.findall(r"[a-z0-9_]+(?:'[a-z]+)?", sentence.lower())


def _evaluate_action_object_grammar(
    sentence: str,
    actions: list[str],
    targets: list[str],
    negation_window: int = 4,
) -> tuple[bool, str | None]:
    """
    Evaluate whether a sentence contains an affirmative (non-negated) Action
    paired with an expected Target in the same clause/sentence.

    Returns
    -------
    (matched: bool, explanation: str | None)
    """
    tokens = _tokenize_sentence(sentence)
    if not tokens:
        return False, None

    sentence_lower = sentence.lower()

    # 1. Identify Target in the sentence
    has_target = False
    matched_target = None
    for tgt in targets:
        t_clean = tgt.lower().strip()
        if not t_clean:
            continue
        if " " in t_clean or "-" in t_clean:
            if t_clean in sentence_lower:
                has_target = True
                matched_target = t_clean
                break
        else:
            for tok in tokens:
                if (
                    tok == t_clean
                    or tok.startswith(t_clean)
                    or t_clean.startswith(tok)
                    or (len(t_clean) >= 4 and t_clean in tok)
                ):
                    has_target = True
                    matched_target = tok
                    break
        if has_target:
            break

    if not has_target:
        return False, None

    # 2. Identify candidate Action tokens in the sentence
    action_matches: list[tuple[int, str]] = []
    for idx, tok in enumerate(tokens):
        for act in actions:
            a_clean = act.lower().strip()
            if not a_clean:
                continue
            if (
                tok == a_clean
                or tok.startswith(a_clean)
                or (len(a_clean) >= 4 and a_clean in tok)
            ):
                action_matches.append((idx, tok))
                break

    # Also check multi-word actions
    for act in actions:
        a_clean = act.lower().strip()
        if (" " in a_clean or "-" in a_clean) and a_clean in sentence_lower:
            neg_pattern = (
                r"\b("
                + "|".join(re.escape(n) for n in NEGATION_TOKENS)
                + r")\b.{1,25}"
                + re.escape(a_clean)
            )
            if not re.search(neg_pattern, sentence_lower):
                return True, f"Affirmative multi-word action '{a_clean}' paired with target '{matched_target}'"

    if not action_matches:
        return False, None

    # 3. Negation Guard: check preceding tokens for each candidate action
    for idx, act_tok in action_matches:
        start_idx = max(0, idx - negation_window)
        preceding = tokens[start_idx:idx]
        is_negated = any(neg in NEGATION_TOKENS for neg in preceding)
        if not is_negated:
            return True, f"Affirmative action '{act_tok}' paired with target '{matched_target}'"

    return False, "Target present but all candidate actions were negated"


def score_recommendation_accuracy(
    agent_response: dict,
    eda_result: dict,
) -> tuple[float | None, list[RubricCheckResult]]:
    """
    CORRECTNESS metric (M6-B).

    Compares the agent's recommendations against the ground-truth rubric
    using Action-Object Dependency Grammar with Negation Guards.

    Guarantees:
    - Verifies affirmative action (kriya) on valid target (karam/column).
    - Rejects negative instructions (e.g. 'do not drop', 'avoid removing').
    - Injects dataset-specific column names dynamically from EDA results.
    - Operates sentence-by-sentence to eliminate accidental distant keyword hits.
    """
    triggered = extract_triggered_conditions(eda_result)
    if not triggered:
        return None, []

    # Gather all candidate sentences from recommendations and narrative
    all_sentences: list[str] = []
    recs = agent_response.get("recommendations", [])
    if isinstance(recs, list):
        for r in recs:
            all_sentences.extend(_split_into_sentences(str(r)))

    narrative = str(agent_response.get("narrative") or "")
    if narrative.strip():
        all_sentences.extend(_split_into_sentences(narrative))

    checks: list[RubricCheckResult] = []
    matched = 0

    for entry in triggered:
        effective_targets = get_effective_targets(entry, eda_result)
        actions = entry.expected_actions

        hit = False
        # Fallback to expected_keywords if entry doesn't have actions/targets configured
        if not actions or not effective_targets:
            combined_text = " ".join(all_sentences).lower()
            hit = any(kw.lower() in combined_text for kw in entry.expected_keywords)
        else:
            for sentence in all_sentences:
                is_match, _ = _evaluate_action_object_grammar(
                    sentence=sentence,
                    actions=actions,
                    targets=effective_targets,
                )
                if is_match:
                    hit = True
                    break

        checks.append(
            RubricCheckResult(
                condition_id=entry.condition_id,
                condition_description=entry.description,
                condition_triggered=True,
                expected_keywords=list(entry.expected_keywords),
                recommendation_matched=hit,
            )
        )
        if hit:
            matched += 1

    accuracy = round(matched / len(triggered), 4)
    return accuracy, checks


# ---------------------------------------------------------------------------
# Aggregate scorer — produces a full PipelineMetrics object
# ---------------------------------------------------------------------------

def score_pipeline(
    agent_response: dict,
    eda_result: dict,
) -> PipelineMetrics:
    """
    Score a single pipeline run and return a ``PipelineMetrics`` object.

    Parameters
    ----------
    agent_response:
        The dict returned by ``run_single_agent()`` or ``run_multi_agent()``.
    eda_result:
        The EDA dict that was passed to the agent.  Required for M6-B
        correctness scoring.

    Returns
    -------
    PipelineMetrics
    """
    accuracy, rubric_checks = score_recommendation_accuracy(
        agent_response, eda_result
    )

    return PipelineMetrics(
        pipeline=agent_response.get("pipeline", "unknown"),
        status=agent_response.get("status", "unknown"),
        error=agent_response.get("error"),
        # Structural
        output_completeness=score_output_completeness(agent_response),
        # Descriptive
        narrative_length_chars=score_narrative_length(agent_response),
        key_risk_count=score_key_risk_count(agent_response),
        recommendation_count=score_recommendation_count(agent_response),
        # Self-reported
        confidence_score=score_confidence(agent_response),
        # Efficiency
        execution_time_seconds=score_execution_time(agent_response),
        llm_call_count=score_llm_call_count(agent_response),
        # Correctness (M6-B)
        recommendation_accuracy=accuracy,
        rubric_checks=rubric_checks,
    )
