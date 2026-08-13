from __future__ import annotations

import pandas as pd


def generate_dataset_insights(
    df: pd.DataFrame,
    eda: dict
) -> dict:
    """
    Generate deterministic, human-readable insights from
    existing EDA results.

    No LLM or probabilistic model is used.
    """

    insights = []

    rows, columns = df.shape

    insights.append(
        f"Dataset contains {rows} rows and {columns} columns."
    )

    missing_by_column = df.isna().sum()
    missing_columns = missing_by_column[
        missing_by_column > 0
    ]

    if missing_columns.empty:
        insights.append(
            "No missing values were detected."
        )
    else:
        total_missing = int(missing_columns.sum())

        insights.append(
            f"{len(missing_columns)} column(s) contain "
            f"missing values ({total_missing} cells affected)."
        )

    duplicate_count = int(df.duplicated().sum())

    if duplicate_count == 0:
        insights.append(
            "No duplicate rows were detected."
        )
    else:
        insights.append(
            f"{duplicate_count} duplicate row(s) were detected."
        )

    correlation_analysis = eda.get(
        "correlation_analysis",
        {}
    )

    correlated_pairs = correlation_analysis.get(
        "highly_correlated_pairs",
        []
    )

    if correlated_pairs:
        for pair in correlated_pairs:
            column_a = pair["column_a"]
            column_b = pair["column_b"]
            correlation = pair["correlation"]

            direction = (
                "positive"
                if correlation > 0
                else "negative"
            )

            insights.append(
                f"{column_a} and {column_b} have a very strong "
                f"{direction} correlation ({correlation:.4f})."
            )
    else:
        insights.append(
            "No highly correlated feature pairs were detected."
        )

    outliers = eda.get("outliers", {})

    outlier_columns = []

    for column, information in outliers.items():
        count = int(information.get("count", 0))

        if count > 0:
            outlier_columns.append(
                (column, count)
            )

    if not outlier_columns:
        insights.append(
            "No statistical outliers were detected."
        )
    else:
        total_outliers = sum(
            count
            for _, count in outlier_columns
        )

        for column, count in outlier_columns:
            insights.append(
                f"{count} statistical outlier(s) were detected "
                f"in {column}."
            )

        if len(outlier_columns) > 1:
            insights.append(
                f"A total of {total_outliers} statistical "
                "outlier(s) were detected across the dataset."
            )

    quality_score = eda.get(
        "quality_score"
    )

    if quality_score:
        score = quality_score.get("score")
        grade = quality_score.get("grade")

        if score is not None and grade:
            insights.append(
                f"Dataset quality score is {score}/100 "
                f"({grade})."
            )

    return {
        "count": len(insights),
        "insights": insights
    }