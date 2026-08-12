import pandas as pd

from backend.core.eda.numeric_statistics import _numeric_columns


def detect_outliers(df: pd.DataFrame) -> dict:
    outliers = {}

    for column in _numeric_columns(df):
        series = df[column].dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_count = int(outlier_mask.sum())

        outliers[column] = {
            "count": outlier_count,
            "percentage": round(outlier_count / len(series) * 100, 2),
            "lower_bound": round(float(lower_bound), 4),
            "upper_bound": round(float(upper_bound), 4)
        }

    return outliers