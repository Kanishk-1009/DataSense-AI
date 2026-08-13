from __future__ import annotations

import pandas as pd


def generate_preprocessing_recommendations(
    df: pd.DataFrame,
    eda: dict
) -> dict:
    recommendations = []
    target = eda.get("ml_task", {}).get("target")

    feature_summary = eda.get(
        "feature_summary",
        {}
    ).get("features", {})

    outliers = eda.get("outliers", {})

    correlation_analysis = eda.get(
        "correlation_analysis",
        {}
    )

    highly_correlated_pairs = correlation_analysis.get(
        "highly_correlated_pairs",
        []
    )

    for column in df.columns:
        summary = feature_summary.get(column, {})

        missing_count = int(
            summary.get("missing_count", 0)
        )

        if missing_count > 0:
            recommendations.append({
                "column": column,
                "type": "missing_values",
                "priority": "high",
                "action": "imputation",
                "message": (
                    f"{column} contains {missing_count} missing "
                    "value(s). Consider an appropriate imputation "
                    "strategy before model training."
                )
            })

        column_type = summary.get("column_type")

        if column != target and column_type in (
            "categorical",
            "binary"
        ):
            recommendations.append({
                "column": column,
                "type": "categorical_encoding",
                "priority": "medium",
                "action": "encoding",
                "message": (
                    f"{column} is a categorical feature and should "
                    "be encoded before model training."
                )
            })

        outlier_info = outliers.get(column, {})
        outlier_count = int(
            outlier_info.get("count", 0)
        )

        if outlier_count > 0:
            if column == target:
                recommendations.append({
                    "column": column,
                    "type": "target_outliers",
                    "priority": "medium",
                    "action": "investigate",
                    "message": (
                        f"{column} contains {outlier_count} statistical "
                        "outlier(s). Investigate these observations "
                        "before deciding whether any treatment is appropriate."
                    )
                })
            else:
                recommendations.append({
                    "column": column,
                    "type": "feature_outliers",
                    "priority": "medium",
                    "action": "investigate_or_transform",
                    "message": (
                        f"{column} contains {outlier_count} statistical "
                        "outlier(s). Investigate whether they should be "
                        "retained, transformed, or handled."
                    )
                })

        if summary.get("is_constant", False):
            recommendations.append({
                "column": column,
                "type": "constant_feature",
                "priority": "high",
                "action": "remove",
                "message": (
                    f"{column} contains a constant value and provides "
                    "no useful variation for machine learning."
                )
            })

    for pair in highly_correlated_pairs:
        column_a = pair.get("column_a")
        column_b = pair.get("column_b")
        correlation = pair.get("correlation")

        if column_a == target or column_b == target:
            recommendation_type = "target_correlation"
            action = "investigate"
            message = (
                f"{column_a} and {column_b} have a very strong "
                f"correlation ({correlation}). Review this relationship "
                "for potential target leakage or redundancy."
            )
        else:
            recommendation_type = "multicollinearity"
            action = "investigate_feature_redundancy"
            message = (
                f"{column_a} and {column_b} have a very strong "
                f"correlation ({correlation}). Consider reviewing "
                "them for multicollinearity or redundant information."
            )

        recommendations.append({
            "column": None,
            "type": recommendation_type,
            "priority": "medium",
            "action": action,
            "message": message,
            "columns": [
                column_a,
                column_b
            ],
            "correlation": correlation
        })

    missing_count = int(df.isna().sum().sum())

    if missing_count == 0:
        dataset_status = "No missing values require imputation."

    else:
        dataset_status = (
            f"{missing_count} missing value(s) require investigation "
            "and appropriate imputation."
        )

    return {
        "status": "available",
        "recommendation_count": len(recommendations),
        "dataset_status": dataset_status,
        "recommendations": recommendations
    }