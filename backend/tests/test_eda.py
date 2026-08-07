import pandas as pd

from backend.core.eda import (
    analyze_target_variable,
    compute_correlation_analysis,
    compute_numeric_statistics,
    detect_outliers,
    run_eda
)


def test_numeric_statistics_basic():
    df = pd.DataFrame({
        "Age": [20, 30, 40, 50],
        "Salary": [30000, 40000, 50000, 60000]
    })

    result = compute_numeric_statistics(df)

    assert result["Age"]["mean"] == 35.0
    assert result["Age"]["min"] == 20.0
    assert result["Age"]["max"] == 50.0
    assert "Salary" in result


def test_numeric_statistics_excludes_categorical():
    df = pd.DataFrame({
        "Age": [20, 30, 40],
        "City": ["Delhi", "Noida", "Delhi"]
    })

    result = compute_numeric_statistics(df)

    assert "Age" in result
    assert "City" not in result


def test_numeric_statistics_ignores_missing_values():
    df = pd.DataFrame({
        "Age": [20, None, 40]
    })

    result = compute_numeric_statistics(df)

    assert result["Age"]["mean"] == 30.0


def test_correlation_analysis_detects_pair():
    df = pd.DataFrame({
        "A": [1, 2, 3, 4, 5],
        "B": [2, 4, 6, 8, 10]
    })

    result = compute_correlation_analysis(df)

    assert result["matrix"]["A"]["B"] == 1.0
    assert len(result["highly_correlated_pairs"]) == 1
    assert result["highly_correlated_pairs"][0]["column_a"] == "A"
    assert result["highly_correlated_pairs"][0]["column_b"] == "B"


def test_correlation_analysis_insufficient_columns():
    df = pd.DataFrame({
        "Age": [20, 30, 40]
    })

    result = compute_correlation_analysis(df)

    assert result["matrix"] == {}
    assert result["highly_correlated_pairs"] == []


def test_outlier_detection_finds_outlier():
    df = pd.DataFrame({
        "Age": [20, 21, 22, 23, 24, 200]
    })

    result = detect_outliers(df)

    assert result["Age"]["count"] == 1
    assert result["Age"]["percentage"] > 0


def test_outlier_detection_no_outliers():
    df = pd.DataFrame({
        "Age": [20, 21, 22, 23, 24, 25]
    })

    result = detect_outliers(df)

    assert result["Age"]["count"] == 0


def test_outlier_detection_skips_short_series():
    df = pd.DataFrame({
        "Age": [20, 30, 40]
    })

    result = detect_outliers(df)

    assert "Age" not in result


def test_target_analysis_numeric():
    df = pd.DataFrame({
        "Salary": [30000, 40000, 50000, 60000]
    })

    result = analyze_target_variable(df, "Salary")

    assert result["column_type"] == "numeric"
    assert result["mean"] == 45000.0


def test_target_analysis_categorical_balanced():
    df = pd.DataFrame({
        "Purchased": ["Yes", "No", "Yes", "No"]
    })

    result = analyze_target_variable(df, "Purchased")

    assert result["column_type"] == "categorical"
    assert result["num_classes"] == 2
    assert "warning" not in result


def test_target_analysis_categorical_imbalance():
    df = pd.DataFrame({
        "Purchased": ["No"] * 19 + ["Yes"]
    })

    result = analyze_target_variable(df, "Purchased")

    assert "warning" in result
    assert "imbalanced" in result["warning"].lower()


def test_target_analysis_missing_column():
    df = pd.DataFrame({
        "Age": [20, 30, 40]
    })

    result = analyze_target_variable(df, "DoesNotExist")

    assert "error" in result


def test_run_eda_without_target():
    df = pd.DataFrame({
        "Age": [20, 30, 40],
        "Salary": [30000, 40000, 50000]
    })

    result = run_eda(df)

    assert "numeric_statistics" in result
    assert "correlation_analysis" in result
    assert "outliers" in result
    assert result["target_analysis"] is None


def test_run_eda_with_target():
    df = pd.DataFrame({
        "Age": [20, 30, 40],
        "Purchased": ["Yes", "No", "Yes"]
    })

    result = run_eda(df, target="Purchased")

    assert result["target_analysis"]["column"] == "Purchased"
    assert result["target_analysis"]["column_type"] == "categorical"
