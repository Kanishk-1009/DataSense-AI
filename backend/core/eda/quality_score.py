from __future__ import annotations

import pandas as pd


def _score_missing_values(df: pd.DataFrame) -> tuple[float, str | None]:
    if df.empty:
        return 0.0, "Dataset is empty."

    total_cells = df.shape[0] * df.shape[1]

    if total_cells == 0:
        return 0.0, None

    missing_count = int(df.isna().sum().sum())
    missing_rate = missing_count / total_cells

    penalty = min(missing_rate * 100, 30.0)

    if missing_count > 0:
        issue = (
            f"Missing values detected "
            f"({missing_rate * 100:.2f}% of cells)."
        )
    else:
        issue = None

    return penalty, issue


def _score_duplicates(df: pd.DataFrame) -> tuple[float, str | None]:
    if df.empty:
        return 0.0, None

    duplicate_count = int(df.duplicated().sum())
    duplicate_rate = duplicate_count / len(df)

    penalty = min(duplicate_rate * 100, 15.0)

    if duplicate_count > 0:
        issue = (
            f"Duplicate rows detected "
            f"({duplicate_rate * 100:.2f}% of rows)."
        )
    else:
        issue = None

    return penalty, issue


def _score_outliers(eda: dict) -> tuple[float, str | None]:
    outliers = eda.get("outliers", {})

    if not outliers:
        return 0.0, None

    outlier_rates = [
        float(info.get("percentage", 0.0))
        for info in outliers.values()
    ]

    if not outlier_rates:
        return 0.0, None

    average_outlier_rate = sum(outlier_rates) / len(outlier_rates)

    penalty = min(average_outlier_rate, 15.0)

    if average_outlier_rate > 0:
        issue = (
            "Outliers detected across numeric columns "
            f"(average rate: {average_outlier_rate:.2f}%)."
        )
    else:
        issue = None

    return penalty, issue


def _score_correlations(eda: dict) -> tuple[float, str | None]:
    correlation_analysis = eda.get("correlation_analysis", {})

    highly_correlated_pairs = correlation_analysis.get(
        "highly_correlated_pairs",
        []
    )

    pair_count = len(highly_correlated_pairs)

    if pair_count == 0:
        return 0.0, None

    penalty = min(pair_count * 5.0, 10.0)

    issue = (
        f"{pair_count} highly correlated feature pair(s) detected."
    )

    return penalty, issue


def _score_constant_columns(df: pd.DataFrame) -> tuple[float, str | None]:
    if df.empty:
        return 0.0, None

    constant_columns = [
        column
        for column in df.columns
        if df[column].nunique(dropna=False) <= 1
    ]

    if not constant_columns:
        return 0.0, None

    penalty = 10.0

    issue = (
        f"{len(constant_columns)} constant column(s) detected."
    )

    return penalty, issue


def _get_grade(score: float) -> tuple[str, str]:
    if score >= 90:
        return "Excellent", "🟢 Excellent Quality"

    if score >= 75:
        return "Good", "🟢 Good Quality"

    if score >= 60:
        return "Fair", "🟡 Fair Quality"

    if score >= 40:
        return "Poor", "🟠 Poor Quality"

    return "Critical", "🔴 Critical Quality"


def compute_data_quality_score(
    df: pd.DataFrame,
    eda: dict
) -> dict:
    """
    Compute a deterministic dataset quality score from 0 to 100.

    The score considers:
    - Missing values
    - Duplicate rows
    - Statistical outliers
    - Highly correlated feature pairs
    - Constant columns

    Parameters
    ----------
    df:
        Original dataset.

    eda:
        Existing deterministic EDA result containing outlier
        and correlation information.

    Returns
    -------
    dict
        Quality score, grade, issues, strengths, and recommendations.
    """

    if df.empty:
        return {
            "score": 0.0,
            "grade": "Critical",
            "status": "🔴 Critical Quality",
            "strengths": [],
            "issues": ["Dataset is empty."],
            "recommendations": [
                "Provide a dataset containing rows and columns."
            ]
        }

    # Calculate individual penalties.
    missing_penalty, missing_issue = _score_missing_values(df)
    duplicate_penalty, duplicate_issue = _score_duplicates(df)
    outlier_penalty, outlier_issue = _score_outliers(eda)
    correlation_penalty, correlation_issue = _score_correlations(eda)
    constant_penalty, constant_issue = _score_constant_columns(df)

    penalties = [
        missing_penalty,
        duplicate_penalty,
        outlier_penalty,
        correlation_penalty,
        constant_penalty,
    ]

    issues = [
        issue
        for issue in [
            missing_issue,
            duplicate_issue,
            outlier_issue,
            correlation_issue,
            constant_issue,
        ]
        if issue is not None
    ]

    # Final score.
    score = 100.0 - sum(penalties)
    score = max(0.0, min(100.0, score))
    score = round(score, 2)

    grade, status = _get_grade(score)

    # Determine strengths.
    strengths = []

    if not df.isna().any().any():
        strengths.append("No missing values detected.")

    if not df.duplicated().any():
        strengths.append("No duplicate rows detected.")

    outliers = eda.get("outliers", {})

    if outliers and all(
        float(info.get("percentage", 0.0)) == 0
        for info in outliers.values()
    ):
        strengths.append("No statistical outliers detected.")

    correlation_analysis = eda.get("correlation_analysis", {})

    if not correlation_analysis.get("highly_correlated_pairs", []):
        strengths.append("No highly correlated feature pairs detected.")

    constant_columns = [
        column
        for column in df.columns
        if df[column].nunique(dropna=False) <= 1
    ]

    if not constant_columns:
        strengths.append("No constant columns detected.")

    if not strengths:
        strengths.append("Dataset contains usable structural information.")

    # Generate deterministic recommendations.
    recommendations = []

    if missing_issue is not None:
        recommendations.append(
            "Review missing values and choose an appropriate "
            "imputation strategy."
        )

    if duplicate_issue is not None:
        recommendations.append(
            "Review duplicate rows before model training."
        )

    if outlier_issue is not None:
        recommendations.append(
            "Investigate detected outliers before deciding "
            "whether to remove or transform them."
        )

    if correlation_issue is not None:
        recommendations.append(
            "Review highly correlated features for potential "
            "multicollinearity."
        )

    if constant_issue is not None:
        recommendations.append(
            "Consider removing constant columns because they "
            "provide no predictive variation."
        )

    if not recommendations:
        recommendations.append(
            "Dataset quality is good. Continue with exploratory "
            "analysis and preprocessing as required."
        )

    return {
        "score": score,
        "grade": grade,
        "status": status,
        "strengths": strengths,
        "issues": issues,
        "recommendations": recommendations,
    }