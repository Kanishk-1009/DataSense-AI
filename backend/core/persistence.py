"""
Result persistence utilities.

Saves EDA and agent outputs as JSON files under results/raw/ so that
every experiment run is frozen and reproducible — a hard requirement for
the M6 Single-Agent vs Multi-Agent evaluation.

File naming convention:
    results/raw/<timestamp>_<pipeline>_<hash>.json

where <hash> is a short SHA-256 of the source CSV bytes, making it easy
to group runs on the same dataset.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_RESULTS_ROOT = Path(__file__).resolve().parents[2] / "results" / "raw"


def _short_hash(data: bytes, length: int = 8) -> str:
    return hashlib.sha256(data).hexdigest()[:length]


def _timestamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def save_result(
    pipeline: str,
    csv_bytes: bytes,
    eda_result: dict[str, Any],
    agent_result: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """
    Persist an experiment result to results/raw/.

    Parameters
    ----------
    pipeline:
        Short label for the pipeline ('eda_only', 'single_agent',
        'multi_agent').
    csv_bytes:
        Raw bytes of the uploaded CSV.  Used to compute a dataset hash
        so runs on the same file can be grouped.
    eda_result:
        Deterministic EDA output from ``run_eda()``.
    agent_result:
        Agent output (optional; None for EDA-only runs).
    metadata:
        Any extra key-value pairs to store alongside the result
        (e.g. model name, target column, timestamp).

    Returns
    -------
    Path
        Absolute path of the saved JSON file.
    """
    _RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

    dataset_hash = _short_hash(csv_bytes)
    ts = _timestamp()
    filename = f"{ts}_{pipeline}_{dataset_hash}.json"
    output_path = _RESULTS_ROOT / filename

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "timestamp": ts,
        "pipeline": pipeline,
        "dataset_hash": dataset_hash,
        "metadata": metadata or {},
        "eda": eda_result,
        "agent": agent_result,
    }

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)

    return output_path
