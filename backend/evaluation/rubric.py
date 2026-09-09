"""
M6-B Ground-Truth Rubric
========================
A manually curated mapping from EDA conditions to expected recommendation
categories.

Design rationale
----------------
The rubric answers the research question: "Are the agent recommendations
*correct given what the EDA found*?"

Each ``RubricEntry`` defines:
- A unique ``condition_id``
- A human-readable ``description``
- An ``eda_extractor``: a pure function ``(eda_result: dict) -> bool``
  that detects whether the condition is present in the data
- A list of ``expected_keywords``: strings (lower-cased) that constitute
  a correct recommendation response to this condition

Keyword matching is intentionally lenient (substring, case-insensitive):
the goal is to detect whether the *concept* was addressed, not whether
the agent used the exact phrase.

Extending the rubric
--------------------
Add a new ``RubricEntry`` to ``GROUND_TRUTH_RUBRIC``.  No other code
needs to change — ``extract_triggered_conditions`` and
``score_recommendation_accuracy`` (in metrics.py) iterate this list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RubricEntry:
    condition_id: str
    description: str
    eda_extractor: Callable[[dict], bool]
    expected_keywords: list[str]


# ---------------------------------------------------------------------------
# EDA extractor helpers
# ---------------------------------------------------------------------------

def _missingness_high(eda: dict) -> bool:
    """True when any column has > 20 % missing values."""
    summary = eda.get("missingness", {}).get("summary", {})
    pct = summary.get("overall_missing_percentage", 0.0)
    if pct is None:
        return False
    return float(pct) > 20.0


def _has_high_correlation(eda: dict) -> bool:
    """True when the EDA detected at least one highly correlated numeric pair."""
    pairs = eda.get("correlation_analysis", {}).get("highly_correlated_pairs", [])
    return len(pairs) > 0


def _has_outliers(eda: dict) -> bool:
    """True when outlier detection flagged at least one column."""
    outliers = eda.get("outliers", {})
    return bool(outliers)


def _has_categorical_features(eda: dict) -> bool:
    """True when the feature summary contains at least one categorical feature."""
    features = eda.get("feature_summary", {}).get("features", {})
    for info in features.values():
        # Real EDA output stores the type under ``column_type``.  The legacy
        # ``dtype`` key (used by older test fixtures) is kept as a fallback.
        col_type = str(info.get("column_type", "")).lower()
        dtype = str(info.get("dtype", "")).lower()
        if col_type in ("categorical", "binary", "datetime"):
            return True
        if "object" in dtype or "categor" in dtype or "bool" in dtype:
            return True
    return False


def _has_class_imbalance(eda: dict) -> bool:
    """
    True when the target is a classification task AND the ml_recommendation
    flags class imbalance or the target analysis shows imbalance.
    """
    ml_task = eda.get("ml_task", {})
    task = ml_task.get("task", "")
    if "classif" not in str(task).lower():
        return False
    # Check ml_recommendation notes for imbalance keywords
    recs = eda.get("ml_recommendation", {})
    notes = str(recs).lower()
    target_analysis = str(eda.get("target_analysis", {})).lower()
    return "imbalance" in notes or "imbalance" in target_analysis or "imbalanced" in target_analysis


def _is_regression_task(eda: dict) -> bool:
    """True when the detected task is regression."""
    ml_task = eda.get("ml_task", {})
    task = str(ml_task.get("task", "")).lower()
    return "regression" in task


# ---------------------------------------------------------------------------
# Ground-truth rubric
# ---------------------------------------------------------------------------

GROUND_TRUTH_RUBRIC: list[RubricEntry] = [
    RubricEntry(
        condition_id="high_missingness",
        description="Dataset has > 20 % overall missing values.",
        eda_extractor=_missingness_high,
        expected_keywords=[
            "impute", "imputation", "missing", "drop", "remove", "fill",
            "median", "mean", "mode", "knn", "interpolat",
        ],
    ),
    RubricEntry(
        condition_id="high_correlation",
        description="At least one highly correlated numeric feature pair detected.",
        eda_extractor=_has_high_correlation,
        expected_keywords=[
            "correlat", "multicollinear", "vif", "redundan", "collinear",
            "feature select", "dimensionality", "pca", "drop feature",
        ],
    ),
    RubricEntry(
        condition_id="outliers_present",
        description="Outlier detection flagged at least one feature.",
        eda_extractor=_has_outliers,
        expected_keywords=[
            "outlier", "anomal", "cap", "clip", "transform", "log",
            "winsoriz", "robust", "iqr", "z-score",
        ],
    ),
    RubricEntry(
        condition_id="categorical_features",
        description="Dataset contains categorical or object-dtype features.",
        eda_extractor=_has_categorical_features,
        expected_keywords=[
            "encod", "one-hot", "label encod", "ordinal", "categor",
            "dummy", "target encod", "embed",
        ],
    ),
    RubricEntry(
        condition_id="class_imbalance",
        description="Classification target with suspected class imbalance.",
        eda_extractor=_has_class_imbalance,
        expected_keywords=[
            "imbalance", "imbalanced", "resample", "oversample", "undersample",
            "smote", "class weight", "stratif", "weighted",
        ],
    ),
    RubricEntry(
        condition_id="regression_task",
        description="Detected ML task is regression.",
        eda_extractor=_is_regression_task,
        expected_keywords=[
            "regression", "linear regression", "ridge", "lasso", "xgboost",
            "gradient boost", "random forest regress", "svr",
            "continuous target", "numeric target",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Public helper: extract which conditions are triggered
# ---------------------------------------------------------------------------

def extract_triggered_conditions(eda_result: dict) -> list[RubricEntry]:
    """
    Return only the rubric entries whose ``eda_extractor`` returns True
    for the given EDA result.

    Parameters
    ----------
    eda_result:
        The dict returned by ``run_eda()``.

    Returns
    -------
    list[RubricEntry]
        Subset of ``GROUND_TRUTH_RUBRIC`` that applies to this dataset.
    """
    return [entry for entry in GROUND_TRUTH_RUBRIC if entry.eda_extractor(eda_result)]
