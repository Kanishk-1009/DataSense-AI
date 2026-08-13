from __future__ import annotations

import pandas as pd


def generate_ml_recommendation(
    df: pd.DataFrame,
    eda: dict
) -> dict:
    ml_task = eda.get("ml_task", {})

    task = ml_task.get("task")
    task_type = ml_task.get("task_type")

    if not task or not task_type:
        return {
            "status": "unavailable",
            "task": None,
            "recommended_models": [],
            "preprocessing": [],
            "reasoning": [
                "A valid machine-learning task could not be determined."
            ]
        }

    feature_summary = eda.get(
        "feature_summary",
        {}
    )

    features = feature_summary.get(
        "features",
        {}
    )

    target = ml_task.get("target")

    feature_columns = [
        column
        for column in df.columns
        if column != target
    ]

    numeric_features = []
    categorical_features = []

    for column in feature_columns:
        summary = features.get(column, {})
        column_type = summary.get("column_type")

        if column_type == "numeric":
            numeric_features.append(column)

        elif column_type in ("categorical", "binary"):
            categorical_features.append(column)

    preprocessing = []

    if numeric_features:
        preprocessing.append(
            "Numeric features can be used directly by tree-based models."
        )

    if categorical_features:
        preprocessing.append(
            "Categorical features should be encoded before model training."
        )

    if task_type == "regression":
        recommended_models = [
            {
                "model": "Linear Regression",
                "reason": (
                    "Provides a simple and interpretable baseline "
                    "for continuous target prediction."
                )
            },
            {
                "model": "Random Forest Regressor",
                "reason": (
                    "Handles nonlinear relationships and mixed feature "
                    "patterns with limited preprocessing."
                )
            },
            {
                "model": "Gradient Boosting Regressor",
                "reason": (
                    "Can model complex nonlinear relationships and "
                    "interactions between features."
                )
            }
        ]

    elif task_type == "binary_classification":
        recommended_models = [
            {
                "model": "Logistic Regression",
                "reason": (
                    "Provides a strong and interpretable baseline "
                    "for binary classification."
                )
            },
            {
                "model": "Random Forest Classifier",
                "reason": (
                    "Handles nonlinear relationships and feature "
                    "interactions effectively."
                )
            },
            {
                "model": "Gradient Boosting Classifier",
                "reason": (
                    "Often performs well on structured tabular "
                    "classification datasets."
                )
            }
        ]

    elif task_type == "multiclass_classification":
        recommended_models = [
            {
                "model": "Logistic Regression",
                "reason": (
                    "Provides a simple baseline for multiclass "
                    "classification."
                )
            },
            {
                "model": "Random Forest Classifier",
                "reason": (
                    "Handles nonlinear relationships and multiple "
                    "feature interactions."
                )
            },
            {
                "model": "Gradient Boosting Classifier",
                "reason": (
                    "Can capture complex relationships in structured "
                    "classification data."
                )
            }
        ]

    else:
        return {
            "status": "unsupported",
            "task": task,
            "recommended_models": [],
            "preprocessing": [],
            "reasoning": [
                f"ML task type '{task_type}' is not currently supported."
            ]
        }

    reasoning = [
        f"Detected ML task: {task_type}.",
        f"Dataset contains {len(df)} rows and {len(feature_columns)} input features.",
        f"{len(numeric_features)} numeric feature(s) detected.",
        f"{len(categorical_features)} categorical feature(s) detected."
    ]

    quality_score = eda.get("quality_score", {})

    if quality_score.get("score") is not None:
        reasoning.append(
            f"Data quality score is "
            f"{quality_score['score']}/100 "
            f"({quality_score.get('grade', 'Unknown')})."
        )

    outliers = eda.get("outliers", {})

    outlier_columns = [
        column
        for column, information in outliers.items()
        if information.get("count", 0) > 0
    ]

    if outlier_columns:
        reasoning.append(
            "Outliers were detected in: "
            + ", ".join(outlier_columns)
            + "."
        )

        preprocessing.append(
            "Review detected outliers before model training."
        )

    return {
        "status": "available",
        "task": task,
        "task_type": task_type,
        "target": target,
        "recommended_models": recommended_models,
        "preprocessing": preprocessing,
        "reasoning": reasoning
    }