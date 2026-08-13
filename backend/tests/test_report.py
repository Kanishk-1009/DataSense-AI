import pandas as pd

from backend.core.eda.report import generate_dataset_report


def test_generate_dataset_report():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "State": ["Delhi", "UP", "Delhi", "UP"],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "quality_score": {
            "score": 94.5,
            "grade": "Excellent",
            "status": "🟢 Excellent Quality"
        },
        "ml_task": {
            "target": "Salary",
            "task": "regression",
            "task_type": "regression",
            "confidence": 0.95
        },
        "ml_recommendation": {
            "recommended_models": [
                {
                    "model": "Linear Regression",
                    "reason": "Baseline model."
                },
                {
                    "model": "Random Forest Regressor",
                    "reason": "Nonlinear model."
                }
            ]
        },
        "preprocessing": {
            "recommendations": [
                {
                    "column": "State",
                    "message": (
                        "State should be encoded before "
                        "model training."
                    )
                }
            ]
        },
        "insights": {
            "insights": [
                "No missing values were detected.",
                "No duplicate rows were detected."
            ]
        }
    }

    result = generate_dataset_report(df, eda)

    assert result["dataset"]["rows"] == 4
    assert result["dataset"]["columns"] == 3

    assert result["quality"]["score"] == 94.5
    assert result["quality"]["grade"] == "Excellent"

    assert result["ml_task"]["target"] == "Salary"
    assert result["ml_task"]["task"] == "regression"
    assert result["ml_task"]["confidence"] == 0.95

    assert result["key_findings"] == [
        "No missing values were detected.",
        "No duplicate rows were detected."
    ]

    assert result["recommended_models"] == [
        "Linear Regression",
        "Random Forest Regressor"
    ]

    assert result["preprocessing"] == [
        "State should be encoded before model training."
    ]


def test_report_handles_missing_optional_sections():
    df = pd.DataFrame({
        "Age": [20, 25, 30]
    })

    eda = {}

    result = generate_dataset_report(df, eda)

    assert result["dataset"]["rows"] == 3
    assert result["dataset"]["columns"] == 1

    assert result["quality"]["score"] is None
    assert result["quality"]["grade"] is None

    assert result["ml_task"]["target"] is None
    assert result["ml_task"]["task"] is None

    assert result["key_findings"] == []
    assert result["recommended_models"] == []
    assert result["preprocessing"] == []