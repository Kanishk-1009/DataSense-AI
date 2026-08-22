from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.core.eda.numeric_statistics import _numeric_columns


def _detect_iqr(series: pd.Series) -> dict:
    """IQR-based outlier detection (Tukey fences)."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    mask = (series < lower_bound) | (series > upper_bound)
    count = int(mask.sum())
    return {
        "count": count,
        "percentage": round(count / len(series) * 100, 2),
        "lower_bound": round(float(lower_bound), 4),
        "upper_bound": round(float(upper_bound), 4),
    }


def _detect_zscore(series: pd.Series, threshold: float = 3.0) -> dict:
    """Z-Score outlier detection (|z| > threshold)."""
    mean = series.mean()
    std = series.std()

    if std == 0 or pd.isna(std):
        return {
            "count": 0,
            "percentage": 0.0,
            "threshold": threshold,
        }

    z_scores = (series - mean).abs() / std
    mask = z_scores > threshold
    count = int(mask.sum())
    return {
        "count": count,
        "percentage": round(count / len(series) * 100, 2),
        "threshold": threshold,
    }


def _detect_isolation_forest(series: pd.Series) -> dict:
    """Isolation Forest outlier detection."""
    values = series.values.reshape(-1, 1)

    clf = IsolationForest(contamination="auto", random_state=42)
    labels = clf.fit_predict(values)

    # IsolationForest returns -1 for outliers, 1 for inliers
    count = int((labels == -1).sum())
    return {
        "count": count,
        "percentage": round(count / len(series) * 100, 2),
    }


def detect_outliers(df: pd.DataFrame) -> dict:
    """
    Detect outliers in numeric columns using three complementary methods:
    - IQR (Tukey fences)
    - Z-Score (|z| > 3)
    - Isolation Forest

    Parameters
    ----------
    df:
        Input dataset.

    Returns
    -------
    dict
        Per-column outlier information from all three methods.
    """
    outliers = {}

    for column in _numeric_columns(df):
        series = df[column].dropna()

        if len(series) < 4:
            continue

        iqr_result = _detect_iqr(series)
        zscore_result = _detect_zscore(series)
        iforest_result = _detect_isolation_forest(series)

        # Consensus count: reported by at least 2 of 3 methods
        counts = [
            iqr_result["count"],
            zscore_result["count"],
            iforest_result["count"],
        ]
        consensus_count = sorted(counts)[1]  # median of three

        outliers[column] = {
            "iqr": iqr_result,
            "zscore": zscore_result,
            "isolation_forest": iforest_result,
            # Backward-compatible summary (uses IQR as primary)
            "count": iqr_result["count"],
            "percentage": iqr_result["percentage"],
            "lower_bound": iqr_result["lower_bound"],
            "upper_bound": iqr_result["upper_bound"],
            "consensus_count": consensus_count,
        }

    return outliers