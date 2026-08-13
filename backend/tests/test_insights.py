import pandas as pd

from backend.core.eda.insights import generate_dataset_insights


def test_dataset_structure_insight():
    df = pd.DataFrame({
        "Age": [20, 25, 30],
        "Salary": [30000, 40000, 50000]
    })

    result = generate_dataset_insights(
        df,
        {
            "correlation_analysis": {
                "highly_correlated_pairs": []
            },
            "outliers": {},
            "quality_score": {
                "score": 100.0,
                "grade": "Excellent"
            }
        }
    )

    assert "Dataset contains 3 rows and 2 columns." in result["insights"]


def test_missing_values_insight():
    df = pd.DataFrame({
        "Age": [20, None, 30],
        "Salary": [30000, 40000, None]
    })

    result = generate_dataset_insights(
        df,
        {
            "correlation_analysis": {
                "highly_correlated_pairs": []
            },
            "outliers": {}
        }
    )

    assert any(
        "missing values" in insight.lower()
        for insight in result["insights"]
    )


def test_duplicate_rows_insight():
    df = pd.DataFrame({
        "Age": [20, 20, 30],
        "Salary": [30000, 30000, 50000]
    })

    result = generate_dataset_insights(
        df,
        {
            "correlation_analysis": {
                "highly_correlated_pairs": []
            },
            "outliers": {}
        }
    )

    assert any(
        "duplicate" in insight.lower()
        for insight in result["insights"]
    )


def test_correlation_insight():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, 40000, 50000, 60000]
    })

    result = generate_dataset_insights(
        df,
        {
            "correlation_analysis": {
                "highly_correlated_pairs": [
                    {
                        "column_a": "Age",
                        "column_b": "Salary",
                        "correlation": 0.95
                    }
                ]
            },
            "outliers": {}
        }
    )

    assert any(
        "Age and Salary" in insight
        for insight in result["insights"]
    )

    assert any(
        "0.9500" in insight
        for insight in result["insights"]
    )


def test_outlier_insight():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, 40000, 50000, 60000]
    })

    result = generate_dataset_insights(
        df,
        {
            "correlation_analysis": {
                "highly_correlated_pairs": []
            },
            "outliers": {
                "Salary": {
                    "count": 1,
                    "percentage": 25.0
                }
            }
        }
    )

    assert any(
        "1 statistical outlier(s) were detected in Salary."
        in insight
        for insight in result["insights"]
    )


def test_quality_score_insight():
    df = pd.DataFrame({
        "Age": [20, 25, 30],
        "Salary": [30000, 40000, 50000]
    })

    result = generate_dataset_insights(
        df,
        {
            "correlation_analysis": {
                "highly_correlated_pairs": []
            },
            "outliers": {},
            "quality_score": {
                "score": 94.5,
                "grade": "Excellent"
            }
        }
    )

    assert any(
        "Dataset quality score is 94.5/100 (Excellent)."
        in insight
        for insight in result["insights"]
    )


def test_clean_dataset_insights():
    df = pd.DataFrame({
        "Age": [20, 25, 30],
        "Salary": [30000, 40000, 50000]
    })

    result = generate_dataset_insights(
        df,
        {
            "correlation_analysis": {
                "highly_correlated_pairs": []
            },
            "outliers": {},
            "quality_score": {
                "score": 100.0,
                "grade": "Excellent"
            }
        }
    )

    assert any(
        "No missing values were detected."
        in insight
        for insight in result["insights"]
    )

    assert any(
        "No duplicate rows were detected."
        in insight
        for insight in result["insights"]
    )

    assert any(
        "No statistical outliers were detected."
        in insight
        for insight in result["insights"]
    )

    assert result["count"] == len(result["insights"])