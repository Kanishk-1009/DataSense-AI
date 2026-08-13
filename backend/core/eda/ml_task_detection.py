from __future__ import annotations

import pandas as pd

from backend.core.profiler import detect_column_type


def detect_ml_task(
    df: pd.DataFrame,
    target: str | None = None
) -> dict:
    if target is None or target.strip() == "":
        return {
            "task": None,
            "task_type": None,
            "confidence": 0.0,
            "target": None,
            "reason": "No target column was provided.",
            "status": "target_required"
        }

    if target not in df.columns:
        return {
            "task": None,
            "task_type": None,
            "confidence": 0.0,
            "target": target,
            "reason": f"Target column '{target}' was not found in the dataset.",
            "status": "invalid_target"
        }

    series = df[target]

    total_rows = len(series)
    missing_count = int(series.isna().sum())
    non_missing = series.dropna()

    if non_missing.empty:
        return {
            "task": None,
            "task_type": None,
            "confidence": 0.0,
            "target": target,
            "reason": "Target column contains no non-missing values.",
            "status": "invalid_target"
        }

    detected_type = detect_column_type(series)

    unique_count = int(non_missing.nunique())
    unique_ratio = unique_count / len(non_missing)

    result = {
        "target": target,
        "target_type": detected_type,
        "unique_classes": unique_count,
        "missing_count": missing_count,
        "missing_percentage": round(
            missing_count / total_rows * 100,
            2
        ) if total_rows > 0 else 0.0,
        "task": None,
        "task_type": None,
        "confidence": 0.0,
        "reason": "",
        "status": "detected"
    }

    if unique_count == 2:
        result["target_type"] = "binary"
        result["task"] = "classification"
        result["task_type"] = "binary_classification"
        result["confidence"] = 0.98
        result["reason"] = (
            "The target contains two distinct classes, "
            "indicating a binary classification problem."
        )

        return result

    if detected_type == "categorical":
        result["target_type"] = "categorical"
        result["task"] = "classification"
        result["task_type"] = "multiclass_classification"
        result["confidence"] = 0.95
        result["reason"] = (
            f"The categorical target contains {unique_count} "
            "classes, indicating multiclass classification."
        )

        return result

    if detected_type == "binary":
        result["target_type"] = "binary"
        result["task"] = "classification"
        result["task_type"] = "binary_classification"
        result["confidence"] = 0.98
        result["reason"] = (
            "The target contains two distinct classes, "
            "indicating a binary classification problem."
        )

        return result

    if detected_type == "numeric":
        if unique_count <= 10 and unique_ratio <= 0.5:
            result["task"] = "classification"
            result["task_type"] = "multiclass_classification"
            result["confidence"] = 0.75
            result["reason"] = (
                "The numeric target contains a small number of "
                "distinct values relative to the dataset size and "
                "may represent class labels."
            )
        else:
            result["task"] = "regression"
            result["task_type"] = "regression"
            result["confidence"] = 0.95
            result["reason"] = (
                "The target is numeric with sufficient continuous "
                "variation, indicating a regression problem."
            )

        return result

    result["status"] = "unsupported"
    result["confidence"] = 0.0
    result["reason"] = (
        f"Target type '{detected_type}' is not supported "
        "for automatic ML task detection."
    )

    return result