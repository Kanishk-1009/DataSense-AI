from __future__ import annotations

import pandas as pd


def generate_dataset_report(
    df: pd.DataFrame,
    eda: dict
) -> dict:
    quality = eda.get("quality_score", {})
    ml_task = eda.get("ml_task", {})
    ml_recommendation = eda.get(
        "ml_recommendation",
        {}
    )
    preprocessing = eda.get(
        "preprocessing",
        {}
    )
    insights = eda.get(
        "insights",
        {}
    )

    recommended_models = [
        item.get("model")
        for item in ml_recommendation.get(
            "recommended_models",
            []
        )
        if item.get("model")
    ]

    preprocessing_recommendations = [
        item.get("message")
        for item in preprocessing.get(
            "recommendations",
            []
        )
        if item.get("message")
    ]

    key_findings = insights.get(
        "insights",
        []
    )

    return {
        "dataset": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1])
        },
        "quality": {
            "score": quality.get("score"),
            "grade": quality.get("grade"),
            "status": quality.get("status")
        },
        "ml_task": {
            "target": ml_task.get("target"),
            "task": ml_task.get("task"),
            "task_type": ml_task.get("task_type"),
            "confidence": ml_task.get("confidence")
        },
        "key_findings": key_findings,
        "recommended_models": recommended_models,
        "preprocessing": preprocessing_recommendations
    }