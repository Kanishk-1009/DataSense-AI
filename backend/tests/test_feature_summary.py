import pandas as pd

from backend.core.eda.feature_summary import generate_feature_summary


def test_numeric_feature_summary():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "numeric_statistics": {
            "Age": {
                "mean": 27.5,
                "median": 27.5,
                "std": 6.455,
                "min": 20,
                "max": 35,
                "q1": 23.75,
                "q3": 31.25,
                "skewness": 0.0,
                "kurtosis": -1.2
            }
        },
        "correlation_analysis": {
            "matrix": {}
        },
        "outliers": {}
    }

    result = generate_feature_summary(df, eda)

    assert result["count"] == 2
    assert "Age" in result["features"]

    age = result["features"]["Age"]

    assert age["column"] == "Age"
    assert age["missing_count"] == 0
    assert age["missing_percentage"] == 0.0
    assert age["unique_count"] == 4
    assert age["is_constant"] is False
    assert age["mean"] == 27.5
    assert age["median"] == 27.5


def test_missing_values_are_detected():
    df = pd.DataFrame({
        "Age": [20, None, 30, 35],
        "Salary": [30000, 40000, None, 60000]
    })

    eda = {
        "numeric_statistics": {},
        "correlation_analysis": {
            "matrix": {}
        },
        "outliers": {}
    }

    result = generate_feature_summary(df, eda)

    age = result["features"]["Age"]
    salary = result["features"]["Salary"]

    assert age["missing_count"] == 1
    assert age["missing_percentage"] == 25.0

    assert salary["missing_count"] == 1
    assert salary["missing_percentage"] == 25.0


def test_constant_column_detection():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Country": ["India", "India", "India", "India"]
    })

    eda = {
        "numeric_statistics": {},
        "correlation_analysis": {
            "matrix": {}
        },
        "outliers": {}
    }

    result = generate_feature_summary(df, eda)

    country = result["features"]["Country"]

    assert country["unique_count"] == 1
    assert country["is_constant"] is True


def test_outlier_information_is_included():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 100]
    })

    eda = {
        "numeric_statistics": {},
        "correlation_analysis": {
            "matrix": {}
        },
        "outliers": {
            "Age": {
                "count": 1,
                "percentage": 25.0
            }
        }
    }

    result = generate_feature_summary(df, eda)

    age = result["features"]["Age"]

    assert age["outlier_count"] == 1
    assert age["outlier_percentage"] == 25.0


def test_target_correlation_is_included():
    df = pd.DataFrame({
        "Experience": [1, 2, 3, 4],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "numeric_statistics": {},
        "correlation_analysis": {
            "matrix": {
                "Experience": {
                    "Experience": 1.0,
                    "Salary": 0.95
                },
                "Salary": {
                    "Experience": 0.95,
                    "Salary": 1.0
                }
            }
        },
        "outliers": {}
    }

    result = generate_feature_summary(
        df,
        eda,
        target="Salary"
    )

    experience = result["features"]["Experience"]
    salary = result["features"]["Salary"]

    assert experience["target_correlation"] == 0.95
    assert salary["target_correlation"] == 1.0


def test_no_target_returns_none_correlation():
    df = pd.DataFrame({
        "Age": [20, 25, 30],
        "Salary": [30000, 40000, 50000]
    })

    eda = {
        "numeric_statistics": {},
        "correlation_analysis": {
            "matrix": {}
        },
        "outliers": {}
    }

    result = generate_feature_summary(df, eda)

    for feature in result["features"].values():
        assert feature["target_correlation"] is None


def test_feature_count_matches_columns():
    df = pd.DataFrame({
        "A": [1, 2, 3],
        "B": ["x", "y", "z"],
        "C": [True, False, True]
    })

    eda = {
        "numeric_statistics": {},
        "correlation_analysis": {
            "matrix": {}
        },
        "outliers": {}
    }

    result = generate_feature_summary(df, eda)

    assert result["count"] == len(df.columns)
    assert set(result["features"].keys()) == {
        "A",
        "B",
        "C"
    }