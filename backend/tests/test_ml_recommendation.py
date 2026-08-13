import pandas as pd

from backend.core.eda.ml_recommendation import generate_ml_recommendation


def test_regression_recommendation():
    df = pd.DataFrame({
        "Experience": [1, 2, 3, 4, 5],
        "Salary": [30000, 40000, 50000, 60000, 70000]
    })

    eda = {
        "ml_task": {
            "task": "regression",
            "task_type": "regression",
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Experience": {
                    "column_type": "numeric"
                }
            }
        },
        "quality_score": {
            "score": 100.0,
            "grade": "Excellent"
        },
        "outliers": {}
    }

    result = generate_ml_recommendation(df, eda)

    assert result["status"] == "available"
    assert result["task"] == "regression"
    assert result["task_type"] == "regression"
    assert result["target"] == "Salary"

    models = [
        model["model"]
        for model in result["recommended_models"]
    ]

    assert "Linear Regression" in models
    assert "Random Forest Regressor" in models
    assert "Gradient Boosting Regressor" in models


def test_binary_classification_recommendation():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Churn": ["Yes", "No", "Yes", "No"]
    })

    eda = {
        "ml_task": {
            "task": "classification",
            "task_type": "binary_classification",
            "target": "Churn"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric"
                }
            }
        },
        "quality_score": {
            "score": 100.0,
            "grade": "Excellent"
        },
        "outliers": {}
    }

    result = generate_ml_recommendation(df, eda)

    assert result["status"] == "available"
    assert result["task_type"] == "binary_classification"

    models = [
        model["model"]
        for model in result["recommended_models"]
    ]

    assert "Logistic Regression" in models
    assert "Random Forest Classifier" in models
    assert "Gradient Boosting Classifier" in models


def test_multiclass_classification_recommendation():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35, 40],
        "Segment": [
            "Basic",
            "Premium",
            "Enterprise",
            "Basic",
            "Premium"
        ]
    })

    eda = {
        "ml_task": {
            "task": "classification",
            "task_type": "multiclass_classification",
            "target": "Segment"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric"
                }
            }
        },
        "quality_score": {
            "score": 95.0,
            "grade": "Excellent"
        },
        "outliers": {}
    }

    result = generate_ml_recommendation(df, eda)

    assert result["status"] == "available"
    assert result["task_type"] == "multiclass_classification"

    models = [
        model["model"]
        for model in result["recommended_models"]
    ]

    assert "Logistic Regression" in models
    assert "Random Forest Classifier" in models
    assert "Gradient Boosting Classifier" in models


def test_categorical_features_require_encoding():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "State": ["Delhi", "UP", "Delhi", "UP"],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "ml_task": {
            "task": "regression",
            "task_type": "regression",
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric"
                },
                "State": {
                    "column_type": "categorical"
                }
            }
        },
        "quality_score": {
            "score": 100.0,
            "grade": "Excellent"
        },
        "outliers": {}
    }

    result = generate_ml_recommendation(df, eda)

    assert any(
        "Categorical features should be encoded"
        in item
        for item in result["preprocessing"]
    )


def test_outliers_generate_preprocessing_advice():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 100],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "ml_task": {
            "task": "regression",
            "task_type": "regression",
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric"
                }
            }
        },
        "quality_score": {
            "score": 85.0,
            "grade": "Good"
        },
        "outliers": {
            "Age": {
                "count": 1,
                "percentage": 25.0
            }
        }
    }

    result = generate_ml_recommendation(df, eda)

    assert any(
        "outliers" in item.lower()
        for item in result["preprocessing"]
    )

    assert any(
        "Age" in item
        for item in result["reasoning"]
    )


def test_missing_ml_task():
    df = pd.DataFrame({
        "Age": [20, 25, 30],
        "Salary": [30000, 40000, 50000]
    })

    eda = {
        "ml_task": {},
        "feature_summary": {
            "features": {}
        },
        "quality_score": {
            "score": 100.0,
            "grade": "Excellent"
        },
        "outliers": {}
    }

    result = generate_ml_recommendation(df, eda)

    assert result["status"] == "unavailable"
    assert result["task"] is None
    assert result["recommended_models"] == []


def test_unsupported_task_type():
    df = pd.DataFrame({
        "Feature": [1, 2, 3],
        "Target": [1, 2, 3]
    })

    eda = {
        "ml_task": {
            "task": "unknown",
            "task_type": "unsupported_task",
            "target": "Target"
        },
        "feature_summary": {
            "features": {
                "Feature": {
                    "column_type": "numeric"
                }
            }
        },
        "quality_score": {
            "score": 100.0,
            "grade": "Excellent"
        },
        "outliers": {}
    }

    result = generate_ml_recommendation(df, eda)

    assert result["status"] == "unsupported"
    assert result["recommended_models"] == []