import pandas as pd

from backend.core.eda.ml_task_detection import detect_ml_task


def test_numeric_target_detected_as_regression():
    df = pd.DataFrame({
        "Experience": [1, 2, 3, 4, 5],
        "Salary": [30000, 40000, 50000, 60000, 70000]
    })

    result = detect_ml_task(df, "Salary")

    assert result["target"] == "Salary"
    assert result["target_type"] == "numeric"
    assert result["task"] == "regression"
    assert result["task_type"] == "regression"
    assert result["confidence"] == 0.95
    assert result["status"] == "detected"


def test_binary_categorical_target():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Churn": ["Yes", "No", "Yes", "No"]
    })

    result = detect_ml_task(df, "Churn")

    assert result["target"] == "Churn"
    assert result["target_type"] == "binary"
    assert result["task"] == "classification"
    assert result["task_type"] == "binary_classification"
    assert result["confidence"] == 0.98


def test_multiclass_categorical_target():
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

    result = detect_ml_task(df, "Segment")

    assert result["target"] == "Segment"
    assert result["target_type"] == "categorical"
    assert result["task"] == "classification"
    assert result["task_type"] == "multiclass_classification"
    assert result["unique_classes"] == 3
    assert result["confidence"] == 0.95


def test_numeric_class_labels():
    df = pd.DataFrame({
        "Feature": [10, 20, 30, 40, 50],
        "Label": [0, 1, 0, 1, 0]
    })

    result = detect_ml_task(df, "Label")

    assert result["target"] == "Label"
    assert result["target_type"] == "binary"
    assert result["task"] == "classification"
    assert result["task_type"] == "binary_classification"
    assert result["confidence"] == 0.98
    assert result["unique_classes"] == 2


def test_no_target_provided():
    df = pd.DataFrame({
        "Age": [20, 25, 30],
        "Salary": [30000, 40000, 50000]
    })

    result = detect_ml_task(df)

    assert result["target"] is None
    assert result["task"] is None
    assert result["task_type"] is None
    assert result["confidence"] == 0.0
    assert result["status"] == "target_required"


def test_empty_target_name():
    df = pd.DataFrame({
        "Age": [20, 25, 30],
        "Salary": [30000, 40000, 50000]
    })

    result = detect_ml_task(df, "")

    assert result["target"] is None
    assert result["task"] is None
    assert result["status"] == "target_required"


def test_invalid_target():
    df = pd.DataFrame({
        "Age": [20, 25, 30],
        "Salary": [30000, 40000, 50000]
    })

    result = detect_ml_task(df, "Profit")

    assert result["target"] == "Profit"
    assert result["task"] is None
    assert result["task_type"] is None
    assert result["confidence"] == 0.0
    assert result["status"] == "invalid_target"


def test_target_with_all_missing_values():
    df = pd.DataFrame({
        "Age": [20, 25, 30],
        "Target": [None, None, None]
    })

    result = detect_ml_task(df, "Target")

    assert result["target"] == "Target"
    assert result["task"] is None
    assert result["task_type"] is None
    assert result["confidence"] == 0.0
    assert result["status"] == "invalid_target"


def test_missing_target_values_are_reported():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, None, 50000, 60000]
    })

    result = detect_ml_task(df, "Salary")

    assert result["task"] == "regression"
    assert result["missing_count"] == 1
    assert result["missing_percentage"] == 25.0


def test_numeric_target_with_few_unique_values():
    df = pd.DataFrame({
        "Feature": list(range(20)),
        "Rating": [1, 2, 3, 4, 5] * 4
    })

    result = detect_ml_task(df, "Rating")

    assert result["target"] == "Rating"
    assert result["target_type"] == "numeric"
    assert result["task"] == "classification"
    assert result["task_type"] == "multiclass_classification"
    assert result["unique_classes"] == 5
    assert result["confidence"] == 0.75