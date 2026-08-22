from __future__ import annotations

# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, pointbiserialr

from backend.core.eda.numeric_statistics import _numeric_columns
from backend.core.profiler import detect_column_type


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cramers_v(series_a: pd.Series, series_b: pd.Series) -> float | None:
    """
    Compute Cramér's V association between two categorical series.
    Returns None if the contingency table is degenerate.
    """
    try:
        contingency = pd.crosstab(series_a, series_b)
        chi2, _, _, _ = chi2_contingency(contingency, correction=False)
        n = int(contingency.values.sum())
        k = min(contingency.shape) - 1
        if n == 0 or k == 0:
            return None
        return round(float(np.sqrt(chi2 / (n * k))), 4)
    except Exception:
        return None


def _point_biserial(
    binary_series: pd.Series,
    numeric_series: pd.Series,
) -> float | None:
    """
    Compute Point-Biserial correlation between a binary and a numeric column.
    Returns None on failure.
    """
    try:
        combined = pd.concat(
            [binary_series, numeric_series], axis=1
        ).dropna()
        if len(combined) < 4:
            return None
        b_col = combined.iloc[:, 0]
        n_col = combined.iloc[:, 1]
        unique_vals = b_col.unique()
        if len(unique_vals) != 2:
            return None
        corr, _ = pointbiserialr(b_col.astype(float), n_col.astype(float))
        return round(float(corr), 4)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def compute_correlation_analysis(
    df: pd.DataFrame,
    threshold: float = 0.8,
) -> dict:
    """
    Compute a unified association analysis:
    - Pearson correlation matrix for numeric columns
    - Cramér's V for categorical–categorical pairs
    - Point-Biserial for binary–numeric pairs

    All highly associated pairs (|value| >= threshold) are flagged.

    Parameters
    ----------
    df:
        Input dataset.
    threshold:
        Association strength threshold for flagging pairs.

    Returns
    -------
    dict
        Pearson matrix, Cramér's V table, Point-Biserial table, and
        a unified list of highly associated pairs.
    """
    numeric_cols = _numeric_columns(df)

    # ---- 1. Pearson -------------------------------------------------------
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr(method="pearson")
        matrix = {
            row: {
                col: (
                    round(float(value), 4)
                    if pd.notna(value)
                    else None
                )
                for col, value in corr_matrix.loc[row].items()
            }
            for row in corr_matrix.index
        }
        highly_correlated_pairs: list[dict] = []
        cols = list(corr_matrix.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                col_a, col_b = cols[i], cols[j]
                value = corr_matrix.loc[col_a, col_b]
                if pd.notna(value) and abs(value) >= threshold:
                    highly_correlated_pairs.append({
                        "column_a": col_a,
                        "column_b": col_b,
                        "correlation": round(float(value), 4),
                        "method": "pearson",
                    })
    else:
        matrix = {}
        highly_correlated_pairs = []

    # ---- 2. Cramér's V (categorical–categorical) --------------------------
    categorical_cols = [
        col for col in df.columns
        if detect_column_type(df[col]) == "categorical"
    ]
    cramers_v_table: list[dict] = []
    for i in range(len(categorical_cols)):
        for j in range(i + 1, len(categorical_cols)):
            col_a = categorical_cols[i]
            col_b = categorical_cols[j]
            v = _cramers_v(df[col_a], df[col_b])
            if v is not None:
                entry = {
                    "column_a": col_a,
                    "column_b": col_b,
                    "cramers_v": v,
                }
                cramers_v_table.append(entry)
                if v >= threshold:
                    highly_correlated_pairs.append({
                        "column_a": col_a,
                        "column_b": col_b,
                        "correlation": v,
                        "method": "cramers_v",
                    })

    # ---- 3. Point-Biserial (binary–numeric) ------------------------------
    binary_cols = [
        col for col in df.columns
        if detect_column_type(df[col]) == "binary"
    ]
    point_biserial_table: list[dict] = []
    for bin_col in binary_cols:
        for num_col in numeric_cols:
            if bin_col == num_col:
                continue
            pb = _point_biserial(df[bin_col], df[num_col])
            if pb is not None:
                entry = {
                    "binary_column": bin_col,
                    "numeric_column": num_col,
                    "point_biserial": pb,
                }
                point_biserial_table.append(entry)
                if abs(pb) >= threshold:
                    highly_correlated_pairs.append({
                        "column_a": bin_col,
                        "column_b": num_col,
                        "correlation": pb,
                        "method": "point_biserial",
                    })

    return {
        "matrix": matrix,
        "highly_correlated_pairs": highly_correlated_pairs,
        "cramers_v": cramers_v_table,
        "point_biserial": point_biserial_table,
    }