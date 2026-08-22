from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.feature_selection import (
    mutual_info_classif,
    mutual_info_regression,
)
from sklearn.preprocessing import LabelEncoder

from backend.core.profiler import detect_column_type


def _encode_features(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """
    Encode all non-numeric feature columns for sklearn compatibility.
    Categorical and binary columns are label-encoded.
    Missing values are filled with the column median or -1.
    """
    encoded = df[feature_cols].copy()

    for col in feature_cols:
        col_type = detect_column_type(df[col])

        if col_type in ("categorical", "binary"):
            le = LabelEncoder()
            non_null = encoded[col].dropna().astype(str)
            le.fit(non_null)
            encoded[col] = encoded[col].map(
                lambda v, le=le: le.transform([str(v)])[0]
                if pd.notna(v)
                else -1
            )
        else:
            # Numeric: fill NaN with median
            median = encoded[col].median()
            encoded[col] = encoded[col].fillna(
                median if pd.notna(median) else 0
            )

    return encoded


def compute_feature_importance(
    df: pd.DataFrame,
    target: str,
    task_type: str | None = None,
) -> dict:
    """
    Compute feature importance using Random Forest and Mutual Information.

    Parameters
    ----------
    df:
        Input dataset.
    target:
        Name of the target column.
    task_type:
        One of 'classification' or 'regression'.
        If None, inferred from the target column type.

    Returns
    -------
    dict
        Ranked feature importance scores from both Random Forest and
        Mutual Information.
    """
    if target not in df.columns:
        return {
            "status": "error",
            "error": f"Target column '{target}' not found in dataset.",
            "random_forest": [],
            "mutual_information": [],
        }

    feature_cols = [col for col in df.columns if col != target]

    if not feature_cols:
        return {
            "status": "error",
            "error": "No feature columns found.",
            "random_forest": [],
            "mutual_information": [],
        }

    # --- Determine task type from target if not provided ---
    if task_type is None:
        target_type = detect_column_type(df[target])
        if target_type in ("categorical", "binary"):
            task_type = "classification"
        else:
            task_type = "regression"

    # --- Prepare features ---
    X = _encode_features(df, feature_cols)

    # --- Prepare target ---
    target_series = df[target].copy()
    target_type = detect_column_type(target_series)

    if task_type == "classification":
        if target_type in ("categorical", "binary"):
            le = LabelEncoder()
            target_series = target_series.fillna("__missing__").astype(str)
            y = le.fit_transform(target_series)
        else:
            y = target_series.fillna(target_series.median()).astype(int).values
    else:
        y = target_series.fillna(target_series.median()).values

    # --- Drop rows where y is still NaN ---
    valid_mask = ~pd.Series(y).isna()
    X = X[valid_mask.values]
    y = y[valid_mask.values]

    if len(X) < 5:
        return {
            "status": "insufficient_data",
            "error": "Not enough rows to compute feature importance.",
            "random_forest": [],
            "mutual_information": [],
        }

    try:
        # ---- Random Forest ------------------------------------------------
        n_estimators = min(100, max(10, len(X) // 5))

        if task_type == "classification":
            rf = RandomForestClassifier(
                n_estimators=n_estimators,
                random_state=42,
                n_jobs=-1,
            )
            mi_func = mutual_info_classif
        else:
            rf = RandomForestRegressor(
                n_estimators=n_estimators,
                random_state=42,
                n_jobs=-1,
            )
            mi_func = mutual_info_regression

        rf.fit(X, y)
        rf_importances = rf.feature_importances_

        rf_ranked = sorted(
            [
                {
                    "feature": col,
                    "importance": round(float(imp), 6),
                    "rank": 0,
                }
                for col, imp in zip(feature_cols, rf_importances)
            ],
            key=lambda x: x["importance"],
            reverse=True,
        )
        for rank, item in enumerate(rf_ranked, start=1):
            item["rank"] = rank

        # ---- Mutual Information -------------------------------------------
        mi_scores = mi_func(X, y, random_state=42)
        total_mi = float(mi_scores.sum())

        mi_ranked = sorted(
            [
                {
                    "feature": col,
                    "score": round(float(score), 6),
                    "normalized_score": (
                        round(float(score) / total_mi, 6)
                        if total_mi > 0
                        else 0.0
                    ),
                    "rank": 0,
                }
                for col, score in zip(feature_cols, mi_scores)
            ],
            key=lambda x: x["score"],
            reverse=True,
        )
        for rank, item in enumerate(mi_ranked, start=1):
            item["rank"] = rank

        return {
            "status": "available",
            "task_type": task_type,
            "target": target,
            "feature_count": len(feature_cols),
            "random_forest": rf_ranked,
            "mutual_information": mi_ranked,
        }

    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "random_forest": [],
            "mutual_information": [],
        }
