import pandas as pd

from backend.core.profiler import profile_dataset


def test_dataset_shape():
    df = pd.DataFrame({
        "Age": [20, 30, 40],
        "Salary": [30000, 40000, 50000]
    })

    result = profile_dataset(df)

    assert result["dataset_info"]["rows"] == 3
    assert result["dataset_info"]["columns"] == 2


def test_missing_values():
    df = pd.DataFrame({
        "Age": [20, None, 40]
    })

    result = profile_dataset(df)

    assert result["missing_values"]["Age"]["count"] == 1
    assert result["missing_values"]["Age"]["percentage"] == 33.33


def test_numeric_dataset():
    df = pd.DataFrame({
        "Age": [20, 30, 40],
        "Salary": [30000, 40000, 50000]
    })

    result = profile_dataset(df)

    assert result["columns"]["Age"]["column_type"] == "numeric"
    assert result["columns"]["Salary"]["column_type"] == "numeric"


def test_categorical_statistics():
    df = pd.DataFrame({
        "City": ["Delhi", "Delhi", "Noida", "Delhi"]
    })

    result = profile_dataset(df)

    assert result["columns"]["City"]["column_type"] == "categorical"
    assert result["columns"]["City"]["unique_values"] == 2
    assert result["categorical_statistics"]["City"]["most_frequent"] == "Delhi"
    assert result["categorical_statistics"]["City"]["frequency"] == 3


def test_duplicate_rows():
    df = pd.DataFrame({
        "Age": [20, 20],
        "Salary": [30000, 30000]
    })

    result = profile_dataset(df)

    assert result["dataset_info"]["duplicate_rows"] == 1


def test_empty_dataframe():
    df = pd.DataFrame()

    result = profile_dataset(df)

    assert result["dataset_info"]["rows"] == 0
    assert result["dataset_info"]["columns"] == 0


def test_all_missing_column():
    df = pd.DataFrame({
        "Age": [None, None, None]
    })

    result = profile_dataset(df)

    assert result["missing_values"]["Age"]["count"] == 3
    assert result["missing_values"]["Age"]["percentage"] == 100.0


def test_binary_column():
    df = pd.DataFrame({
        "Purchased": [0, 1, 1, 0]
    })

    result = profile_dataset(df)

    assert result["columns"]["Purchased"]["column_type"] == "binary"


def test_constant_column_warning():
    df = pd.DataFrame({
        "Country": ["India", "India", "India"]
    })

    result = profile_dataset(df)

    assert any(
        "constant" in warning.lower()
        for warning in result["warnings"]
    )


def test_identifier_warning():
    df = pd.DataFrame({
        "UserID": ["A1", "A2", "A3", "A4", "A5"]
    })

    result = profile_dataset(df)

    assert any(
        "identifier" in warning.lower()
        for warning in result["warnings"]
    )


def test_high_cardinality_warning():
    df = pd.DataFrame({
        "Email": [
            "a@test.com",
            "b@test.com",
            "c@test.com",
            "d@test.com",
            "e@test.com"
        ]
    })

    result = profile_dataset(df)

    assert any(
        "cardinality" in warning.lower()
        for warning in result["warnings"]
    )