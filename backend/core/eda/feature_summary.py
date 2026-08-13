from __future__ import annotations

import pandas as pd

from backend.core.profiler import detect_column_type


def generate_feature_summary(
    df: pd.DataFrame,
    eda: dict,
    target: str | None = None
) -> dict:
    summaries = {}

    numeric_statistics = eda.get(
        "numeric_statistics",
        {}
    )

    correlation_analysis = eda.get(
        "correlation_analysis",
        {}
    )

    correlation_matrix = correlation_analysis.get(
        "matrix",
        {}
    )

    outliers = eda.get(
        "outliers",
        {}
    )

    for column in df.columns:
        series = df[column]

        column_type = detect_column_type(series)

        missing_count = int(series.isna().sum())
        missing_percentage = round(
            missing_count / len(df) * 100,
            2
        ) if len(df) > 0 else 0.0

        unique_count = int(
            series.nunique(dropna=True)
        )

        summary = {
            "column": column,
            "column_type": column_type,
            "missing_count": missing_count,
            "missing_percentage": missing_percentage,
            "unique_count": unique_count,
            "is_constant": unique_count <= 1,
        }

        if column in numeric_statistics:
            stats = numeric_statistics[column]

            summary.update({
                "mean": stats.get("mean"),
                "median": stats.get("median"),
                "std": stats.get("std"),
                "min": stats.get("min"),
                "max": stats.get("max"),
                "q1": stats.get("q1"),
                "q3": stats.get("q3"),
                "skewness": stats.get("skewness"),
                "kurtosis": stats.get("kurtosis"),
            })

        if column in outliers:
            summary["outlier_count"] = int(
                outliers[column].get("count", 0)
            )
            summary["outlier_percentage"] = float(
                outliers[column].get("percentage", 0.0)
            )
        else:
            summary["outlier_count"] = 0
            summary["outlier_percentage"] = 0.0

        if target and column != target:
            target_correlations = correlation_matrix.get(
                column,
                {}
            )

            target_correlation = target_correlations.get(
                target
            )

            summary["target_correlation"] = (
                target_correlation
            )

        elif target and column == target:
            summary["target_correlation"] = 1.0

        else:
            summary["target_correlation"] = None

        summaries[column] = summary

    return {
        "count": len(summaries),
        "features": summaries
    }