import pandas as pd

from backend.core.eda.numeric_statistics import compute_numeric_statistics
from backend.core.eda.correlation import compute_correlation_analysis
from backend.core.eda.outliers import detect_outliers
from backend.core.eda.target_analysis import analyze_target_variable


def run_eda(df: pd.DataFrame, target: str = None) -> dict:
    eda_result = {
        "numeric_statistics": compute_numeric_statistics(df),
        "correlation_analysis": compute_correlation_analysis(df),
        "outliers": detect_outliers(df),
        "target_analysis": None
    }

    if target:
        eda_result["target_analysis"] = analyze_target_variable(df, target)

    return eda_result