"""
M6 CLI Runner
=============
Entry point for running the M6 controlled experiment from the command line.

Usage
-----
Development verification (mocked — needs no Ollama)::

    python -m backend.evaluation.runner \\
        --csv datasets/titanic.csv \\
        --target Survived \\
        --model llama3.1:8b \\
        --dry-run

Actual research experiment (requires running Ollama)::

    python -m backend.evaluation.runner \\
        --csv datasets/titanic.csv \\
        --target Survived \\
        --model llama3.1:8b

Output
------
Prints a formatted metric-by-metric comparison table to stdout and saves a
JSON result file under ``results/metrics/``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt(value) -> str:
    """Format a metric value for the comparison table."""
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _print_comparison_table(result) -> None:
    """Print a human-readable metric comparison table to stdout."""
    width_metric = 28
    width_cat = 14
    width_val = 12

    separator = "─" * (width_metric + width_cat + width_val * 2 + width_val + 6)

    print()
    print("═" * len(separator))
    print(f"  M6 Evaluation: {result.dataset_name!r}  |  model: {result.model}")
    print(f"  Run ID: {result.run_id}")
    print("═" * len(separator))
    print(
        f"  {'Metric':<{width_metric}} {'Category':<{width_cat}} "
        f"{'M4':>{width_val}} {'M5':>{width_val}} {'Better':<{width_val}}"
    )
    print(separator)

    for c in result.comparison:
        better = c.better_pipeline or "—"
        print(
            f"  {c.metric:<{width_metric}} {c.category:<{width_cat}} "
            f"{_fmt(c.m4_value):>{width_val}} {_fmt(c.m5_value):>{width_val}} "
            f"{better:<{width_val}}"
        )
        if c.note:
            print(f"  {'':>{width_metric}}   ↳ {c.note}")

    print(separator)
    print()

    # M6-B rubric detail
    print("  M6-B Recommendation Accuracy (rubric detail)")
    print(f"  {'Condition':<30} {'M4':>8} {'M5':>8}")
    print("  " + "─" * 48)

    m4_checks = {c.condition_id: c for c in result.m4.rubric_checks}
    m5_checks = {c.condition_id: c for c in result.m5.rubric_checks}
    all_ids = sorted(set(list(m4_checks) + list(m5_checks)))

    if not all_ids:
        print("  (no rubric conditions triggered for this dataset)")
    else:
        for cid in all_ids:
            m4_hit = m4_checks[cid].recommendation_matched if cid in m4_checks else None
            m5_hit = m5_checks[cid].recommendation_matched if cid in m5_checks else None
            m4_str = "✓" if m4_hit else ("✗" if m4_hit is False else "—")
            m5_str = "✓" if m5_hit else ("✗" if m5_hit is False else "—")
            print(f"  {cid:<30} {m4_str:>8} {m5_str:>8}")

    print()
    print(f"  {result.research_note}")
    print("═" * len(separator))
    print()


# ---------------------------------------------------------------------------
# Dry-run stub (for structural verification without Ollama)
# ---------------------------------------------------------------------------

def _dry_run(csv_path: Path, target: str | None, model: str) -> None:
    """
    Validate the full pipeline structure without making real LLM calls.
    Uses the same mocking strategy as the test suite.
    """
    import json
    from unittest.mock import MagicMock, patch
    import pandas as pd
    from backend.core.eda import run_eda

    print(f"[dry-run] Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    csv_bytes = csv_path.read_bytes()
    print(f"[dry-run] Dataset shape: {df.shape}")

    print("[dry-run] Running EDA (deterministic) ...")
    eda_result = run_eda(df, target=target)
    print("[dry-run] EDA complete.")

    mock_single = json.dumps({
        "narrative": "Dry-run single-agent narrative.",
        "key_risks": ["Risk A", "Risk B"],
        "recommendations": ["Impute missing values.", "Encode categoricals."],
        "confidence": 0.80,
    })
    mock_critic = json.dumps({
        "narrative": "Dry-run multi-agent narrative.",
        "key_risks": ["Risk A", "Risk B", "Risk C"],
        "recommendations": [
            "Impute missing values.", "Encode categoricals.", "Check outliers.",
        ],
        "confidence": 0.85,
    })
    mock_spec = json.dumps({
        "findings": "Dry-run findings.",
        "risk_level": "low",
        "recommendations": ["Proceed."],
    })
    mock_prep = json.dumps({
        "steps": ["Encode categoricals."],
        "priority_issues": [],
        "risk_level": "low",
    })
    mock_algo = json.dumps({
        "recommended_models": [{"model": "LogReg", "reason": "baseline"}],
        "reasoning": ["Clean data."],
        "risk_level": "low",
    })

    def _mock_response(content: str):
        m = MagicMock()
        m.content = content
        return m

    side_effects = (
        [_mock_response(mock_spec)] * 3
        + [_mock_response(mock_spec)]
        + [_mock_response(mock_prep)]
        + [_mock_response(mock_algo)]
        + [_mock_response(mock_critic)]
    )

    from backend.evaluation.evaluator import run_evaluation

    print("[dry-run] Running M4 and M5 with mocked LLM ...")
    with (
        patch("backend.agents.single_agent.ChatOllama") as mock_sa,
        patch("backend.agents.multi_agent.nodes.ChatOllama") as mock_ma,
    ):
        mock_sa_llm = MagicMock()
        mock_sa_llm.invoke.return_value = _mock_response(mock_single)
        mock_sa.return_value = mock_sa_llm

        mock_ma_llm = MagicMock()
        mock_ma_llm.invoke.side_effect = side_effects
        mock_ma.return_value = mock_ma_llm

        result = run_evaluation(
            eda_result=eda_result,
            dataset_name=csv_path.stem,
            csv_bytes=csv_bytes,
            model=model,
            target=target,
            persist=True,
        )

    _print_comparison_table(result)
    print("[dry-run] Structural verification complete. No real LLM calls were made.")


# ---------------------------------------------------------------------------
# Real experiment
# ---------------------------------------------------------------------------

def _real_run(
    csv_path: Path,
    target: str | None,
    model: str,
    ollama_url: str,
) -> None:
    """Run the actual experiment against a live Ollama server."""
    import pandas as pd
    from backend.core.eda import run_eda
    from backend.evaluation.evaluator import run_evaluation

    print(f"Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    csv_bytes = csv_path.read_bytes()
    print(f"Dataset shape: {df.shape}")

    print("Running EDA (deterministic, no LLM) ...")
    eda_result = run_eda(df, target=target)
    print("EDA complete.")

    print(f"Running M4 (single-agent) and M5 (multi-agent) with model '{model}' ...")
    result = run_evaluation(
        eda_result=eda_result,
        dataset_name=csv_path.stem,
        csv_bytes=csv_bytes,
        model=model,
        base_url=ollama_url,
        target=target,
        persist=True,
    )

    _print_comparison_table(result)
    print(f"Result saved to: results/metrics/{result.run_id}.json")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m backend.evaluation.runner",
        description=(
            "M6 Controlled Experiment: compare M4 (single-agent) vs "
            "M5 (multi-agent) on the same EDA result."
        ),
    )
    parser.add_argument(
        "--csv",
        required=True,
        type=Path,
        metavar="PATH",
        help="Path to the CSV dataset to analyse.",
    )
    parser.add_argument(
        "--target",
        default=None,
        metavar="COLUMN",
        help="Target column name for supervised analysis (optional).",
    )
    parser.add_argument(
        "--model",
        default="llama3.1:8b",
        metavar="MODEL",
        help="Ollama model name (default: llama3.1:8b).",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        metavar="URL",
        help="Ollama server URL (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Run with mocked LLM responses to validate the pipeline structure "
            "without a live Ollama server."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if not args.csv.exists():
        print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        _dry_run(args.csv, args.target, args.model)
    else:
        _real_run(args.csv, args.target, args.model, args.ollama_url)


if __name__ == "__main__":
    main()
