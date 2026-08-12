import pandas as pd

from backend.core.profiler import detect_column_type


def _numeric_columns(df: pd.DataFrame) -> list:
    return [
        column
        for column in df.columns
        if detect_column_type(df[column]) == "numeric"
    ]


def compute_numeric_statistics(df: pd.DataFrame) -> dict:
    statistics = {}

    for column in _numeric_columns(df):
        series = df[column].dropna()

        if series.empty:
            continue

        statistics[column] = {
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "std": round(float(series.std()), 4) if len(series) > 1 else 0.0,
            "min": round(float(series.min()), 4),
            "max": round(float(series.max()), 4),
            "q1": round(float(series.quantile(0.25)), 4),
            "q3": round(float(series.quantile(0.75)), 4),
            "skewness": round(float(series.skew()), 4) if len(series) > 2 else 0.0,
            "kurtosis": round(float(series.kurt()), 4) if len(series) > 3 else 0.0,
        }

    return statistics