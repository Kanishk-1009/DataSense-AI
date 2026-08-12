import pandas as pd

from backend.core.profiler import detect_column_type


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
            "skewness": round(float(clean.skew()), 4)
            if len(clean) > 2 else 0.0
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
            analysis["warning"] = (
                "Target variable shows moderate class imbalance."
            )

    else:
        analysis["error"] = (
            f"Target column type '{column_type}' is not supported "
            "for target analysis."
        )

    return analysis