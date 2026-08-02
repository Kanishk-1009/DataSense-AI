import pandas as pd

from backend.core.profiler import detect_column_type


def _numeric_columns(df: pd.DataFrame) -> list:
    return [
        column for column in df.columns
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
            "kurtosis": round(float(series.kurt()), 4) if len(series) > 3 else 0.0
        }

    return statistics


def compute_correlation_analysis(df: pd.DataFrame, threshold: float = 0.8) -> dict:
    numeric_columns = _numeric_columns(df)

    if len(numeric_columns) < 2:
        return {
            "matrix": {},
            "highly_correlated_pairs": []
        }

    corr_matrix = df[numeric_columns].corr(method="pearson")

    matrix = {
        row: {
            col: (round(float(value), 4) if pd.notna(value) else None)
            for col, value in corr_matrix.loc[row].items()
        }
        for row in corr_matrix.index
    }

    highly_correlated_pairs = []
    columns = list(corr_matrix.columns)

    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):

            col_a, col_b = columns[i], columns[j]
            value = corr_matrix.loc[col_a, col_b]

            if pd.notna(value) and abs(value) >= threshold:
                highly_correlated_pairs.append({
                    "column_a": col_a,
                    "column_b": col_b,
                    "correlation": round(float(value), 4)
                })

    return {
        "matrix": matrix,
        "highly_correlated_pairs": highly_correlated_pairs
    }


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


def analyze_target_variable(df: pd.DataFrame, target: str) -> dict:
    if target not in df.columns:
        return {
            "error": f"Target column '{target}' not found in dataset."
        }

    series = df[target]
    column_type = detect_column_type(series)

    analysis = {
        "column": target,
        "column_type": column_type
    }

    if column_type == "numeric":
        clean = series.dropna()

        if clean.empty:
            analysis["error"] = "Target column has no non-missing values."
            return analysis

        analysis.update({
            "mean": round(float(clean.mean()), 4),
            "median": round(float(clean.median()), 4),
            "std": round(float(clean.std()), 4) if len(clean) > 1 else 0.0,
            "min": round(float(clean.min()), 4),
            "max": round(float(clean.max()), 4),
            "skewness": round(float(clean.skew()), 4) if len(clean) > 2 else 0.0
        })

    elif column_type in ("categorical", "binary"):
        counts = series.value_counts(dropna=True)
        total = int(counts.sum())

        if total == 0:
            analysis["error"] = "Target column has no non-missing values."
            return analysis

        analysis["class_distribution"] = {
            str(label): {
                "count": int(count),
                "percentage": round(count / total * 100, 2)
            }
            for label, count in counts.items()
        }
        analysis["num_classes"] = int(len(counts))

        majority_ratio = counts.max() / total

        if majority_ratio > 0.90:
            analysis["warning"] = "Target variable is highly imbalanced."
        elif majority_ratio > 0.75:
            analysis["warning"] = "Target variable shows moderate class imbalance."

    else:
        analysis["error"] = (
            f"Target column type '{column_type}' is not supported "
            "for target analysis."
        )

    return analysis


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
