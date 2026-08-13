import pandas as pd

from backend.core.eda.numeric_statistics import compute_numeric_statistics
from backend.core.eda.correlation import compute_correlation_analysis
from backend.core.eda.outliers import detect_outliers
from backend.core.eda.target_analysis import analyze_target_variable
from backend.core.eda.quality_score import compute_data_quality_score
from backend.core.eda.insights import generate_dataset_insights
from backend.core.eda.feature_summary import generate_feature_summary


def run_eda(df: pd.DataFrame, target: str = None) -> dict:
    numeric_statistics = compute_numeric_statistics(df)
    correlation_analysis = compute_correlation_analysis(df)
    outliers = detect_outliers(df)

    eda_result = {
        "numeric_statistics": numeric_statistics,
        "correlation_analysis": correlation_analysis,
        "outliers": outliers,
        "target_analysis": None
    }

    if target:
        eda_result["target_analysis"] = analyze_target_variable(
            df,
            target
        )

    quality_score = compute_data_quality_score(
        df,
        eda_result
    )

    eda_result["quality_score"] = quality_score

    dataset_insights = generate_dataset_insights(
        df,
        eda_result
    )

    eda_result["insights"] = dataset_insights

    feature_summary = generate_feature_summary(
        df,
        eda_result,
        target
    )

    eda_result["feature_summary"] = feature_summary

    return eda_result