import pandas as pd

from backend.core.eda.quality_score import compute_data_quality_score


def test_perfect_dataset():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "outliers": {
            "Age": {"percentage": 0},
            "Salary": {"percentage": 0}
        },
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = compute_data_quality_score(df, eda)

    assert result["score"] == 100.0
    assert result["grade"] == "Excellent"
    assert result["status"] == "🟢 Excellent Quality"


def test_missing_values_reduce_score():
    df = pd.DataFrame({
        "Age": [20, None, 30, 35],
        "Salary": [30000, 40000, None, 60000]
    })

    eda = {
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = compute_data_quality_score(df, eda)

    assert result["score"] < 100
    assert result["grade"] in {
        "Excellent",
        "Good",
        "Fair",
        "Poor",
        "Critical"
    }
    assert any(
        "Missing values" in issue
        for issue in result["issues"]
    )


def test_duplicate_rows_reduce_score():
    df = pd.DataFrame({
        "Age": [20, 20, 30, 35],
        "Salary": [30000, 30000, 50000, 60000]
    })

    eda = {
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = compute_data_quality_score(df, eda)

    assert result["score"] < 100
    assert any(
        "Duplicate rows" in issue
        for issue in result["issues"]
    )


def test_outliers_reduce_score():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "outliers": {
            "Age": {
                "count": 1,
                "percentage": 25.0
            }
        },
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = compute_data_quality_score(df, eda)

    assert result["score"] < 100
    assert any(
        "Outliers detected" in issue
        for issue in result["issues"]
    )


def test_high_correlation_reduces_score():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": [
                {
                    "column_a": "Age",
                    "column_b": "Salary",
                    "correlation": 0.95
                }
            ]
        }
    }

    result = compute_data_quality_score(df, eda)

    assert result["score"] == 95.0
    assert any(
        "highly correlated" in issue
        for issue in result["issues"]
    )


def test_constant_column_reduces_score():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Country": ["India", "India", "India", "India"]
    })

    eda = {
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = compute_data_quality_score(df, eda)

    assert result["score"] == 90.0
    assert any(
        "constant column" in issue
        for issue in result["issues"]
    )


def test_empty_dataset():
    df = pd.DataFrame()

    eda = {
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = compute_data_quality_score(df, eda)

    assert result["score"] == 0.0
    assert result["grade"] == "Critical"
    assert result["status"] == "🔴 Critical Quality"
    assert "Dataset is empty." in result["issues"]


def test_score_never_exceeds_100():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = compute_data_quality_score(df, eda)

    assert 0 <= result["score"] <= 100


def test_score_never_below_zero():
    df = pd.DataFrame({
        "A": [1, 1, 1, 1],
        "B": [2, 2, 2, 2]
    })

    eda = {
        "outliers": {
            "A": {"percentage": 100},
            "B": {"percentage": 100}
        },
        "correlation_analysis": {
            "highly_correlated_pairs": [
                {"column_a": "A", "column_b": "B", "correlation": 1.0},
                {"column_a": "B", "column_b": "A", "correlation": 1.0},
                {"column_a": "A", "column_b": "B", "correlation": 1.0}
            ]
        }
    }

    result = compute_data_quality_score(df, eda)

    assert 0 <= result["score"] <= 100