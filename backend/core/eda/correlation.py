import pandas as pd

from backend.core.eda.numeric_statistics import _numeric_columns


def compute_correlation_analysis(
    df: pd.DataFrame,
    threshold: float = 0.8
) -> dict:
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