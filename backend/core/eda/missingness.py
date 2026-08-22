from __future__ import annotations

import pandas as pd
from scipy.stats import spearmanr


def _missingness_indicator(
    column: str,
    missing_mask: pd.Series,
    df: pd.DataFrame,
    correlation_threshold: float = 0.2,
) -> dict:
    """
    Compute a heuristic missingness indicator using Spearman correlation.

    This is NOT a formal statistical test (e.g. Little's MCAR test).
    It is a lightweight heuristic: the binary missing-value indicator for
    a column is correlated against every other numeric column.  A high
    Spearman |r| suggests the missingness may be related to observed data
    (MAR-like); a low |r| suggests it may be random (MCAR-like).

    The returned labels ('likely_mcar', 'likely_mar', 'unknown') are
    exploratory indicators to guide further investigation, not definitive
    statistical conclusions.

    Parameters
    ----------
    column:
        Name of the column being analysed.
    missing_mask:
        Boolean Series — True where the column value is missing.
    df:
        Full dataset (used to look up other columns).
    correlation_threshold:
        Spearman |r| above which the pattern is labelled 'likely_mar'.

    Returns
    -------
    dict
        Keys: 'indicator', 'max_spearman_correlation', 'note'
    """
    if missing_mask.sum() == 0:
        return {
            "indicator": "complete",
            "max_spearman_correlation": None,
            "note": "No missing values in this column.",
        }

    other_numeric = df.drop(columns=[column]).select_dtypes(include="number")

    if other_numeric.empty or len(missing_mask) < 10:
        return {
            "indicator": "unknown",
            "max_spearman_correlation": None,
            "note": (
                "Insufficient data or no numeric columns available "
                "to compute a missingness indicator."
            ),
        }

    binary_indicator = missing_mask.astype(int)
    max_corr = 0.0

    for other_col in other_numeric.columns:
        other_series = other_numeric[other_col]
        valid = other_series.notna()
        if valid.sum() < 10:
            continue
        try:
            corr, _ = spearmanr(
                binary_indicator[valid],
                other_series[valid],
            )
            if pd.notna(corr):
                max_corr = max(max_corr, abs(float(corr)))
        except Exception:
            continue

    if max_corr >= correlation_threshold:
        return {
            "indicator": "likely_mar",
            "max_spearman_correlation": round(max_corr, 4),
            "note": (
                f"The missing-value indicator for '{column}' shows a "
                f"Spearman |r| of {max_corr:.4f} with at least one other "
                "numeric column, suggesting the missingness may not be "
                "fully random (MAR-like). This is a heuristic signal — "
                "verify with domain knowledge before choosing an imputation "
                "strategy."
            ),
        }

    return {
        "indicator": "likely_mcar",
        "max_spearman_correlation": round(max_corr, 4),
        "note": (
            f"The missing-value indicator for '{column}' shows a low "
            f"Spearman |r| of {max_corr:.4f} with other numeric columns, "
            "suggesting the missingness may be approximately random "
            "(MCAR-like). This is a heuristic signal, not a formal test."
        ),
    }


def analyze_missingness(
    df: pd.DataFrame,
    correlation_threshold: float = 0.2,
) -> dict:
    """
    Analyse the missingness patterns of a dataset using a lightweight
    Spearman-correlation heuristic.

    For each column:
    - Reports the missing count and percentage.
    - Provides a heuristic indicator ('likely_mcar', 'likely_mar',
      'unknown', or 'complete') based on whether missingness correlates
      with other observed columns.
    - Exposes the maximum Spearman |r| so consumers can judge the
      strength of the signal themselves.

    .. note::
        The 'likely_mcar' / 'likely_mar' labels are **exploratory
        heuristics**, not the results of a formal statistical test such as
        Little's MCAR test.  They should be treated as signals for further
        investigation, not definitive classifications.

    Parameters
    ----------
    df:
        Input dataset.
    correlation_threshold:
        Spearman |r| threshold above which missingness is labelled
        'likely_mar'.  Default 0.2 is intentionally conservative.

    Returns
    -------
    dict
        'summary': dataset-level counts and indicator lists.
        'columns': per-column missing counts, percentages, indicators,
                   Spearman correlations, and notes.
    """
    total_cells = df.shape[0] * df.shape[1]
    total_missing = int(df.isna().sum().sum())

    column_analysis: dict[str, dict] = {}
    likely_mar_columns: list[str] = []
    likely_mcar_columns: list[str] = []
    complete_columns: list[str] = []

    for column in df.columns:
        missing_mask = df[column].isna()
        missing_count = int(missing_mask.sum())
        missing_pct = (
            round(missing_count / len(df) * 100, 2) if len(df) > 0 else 0.0
        )

        indicator_result = _missingness_indicator(
            column, missing_mask, df, correlation_threshold
        )

        indicator = indicator_result["indicator"]

        entry: dict = {
            "missing_count": missing_count,
            "missing_percentage": missing_pct,
            "indicator": indicator,
            "max_spearman_correlation": indicator_result[
                "max_spearman_correlation"
            ],
            "note": indicator_result["note"],
        }

        if indicator == "likely_mar":
            likely_mar_columns.append(column)
            entry["warning"] = (
                f"'{column}' shows a MAR-like pattern (heuristic). "
                "Consider whether missingness is related to other observed "
                "variables before choosing an imputation strategy."
            )
        elif indicator == "likely_mcar":
            likely_mcar_columns.append(column)
        elif indicator == "complete":
            complete_columns.append(column)

        column_analysis[column] = entry

    missing_columns = [
        col for col in df.columns if df[col].isna().any()
    ]

    summary: dict = {
        "total_missing_cells": total_missing,
        "total_cells": total_cells,
        "overall_missing_percentage": (
            round(total_missing / total_cells * 100, 2)
            if total_cells > 0
            else 0.0
        ),
        "columns_with_missing": len(missing_columns),
        "likely_mar_columns": likely_mar_columns,
        "likely_mcar_columns": likely_mcar_columns,
        "complete_columns": len(complete_columns),
        "heuristic_note": (
            "Missingness indicators are based on Spearman correlation and "
            "are exploratory heuristics, not formal statistical tests."
        ),
    }

    return {
        "summary": summary,
        "columns": column_analysis,
    }
