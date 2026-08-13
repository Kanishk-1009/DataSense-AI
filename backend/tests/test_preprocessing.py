import pandas as pd

from backend.core.eda.preprocessing import (
    generate_preprocessing_recommendations
)


def test_missing_values_recommend_imputation():
    df = pd.DataFrame({
        "Age": [20, None, 30, 35],
        "Salary": [30000, 40000, None, 60000]
    })

    eda = {
        "ml_task": {
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric",
                    "missing_count": 1
                },
                "Salary": {
                    "column_type": "numeric",
                    "missing_count": 1
                }
            }
        },
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = generate_preprocessing_recommendations(
        df,
        eda
    )

    recommendations = result["recommendations"]

    assert result["status"] == "available"
    assert result["recommendation_count"] == 2

    assert any(
        item["column"] == "Age"
        and item["action"] == "imputation"
        for item in recommendations
    )

    assert any(
        item["column"] == "Salary"
        and item["action"] == "imputation"
        for item in recommendations
    )


def test_categorical_feature_requires_encoding():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "State": ["Delhi", "UP", "Delhi", "UP"],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "ml_task": {
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric",
                    "missing_count": 0
                },
                "State": {
                    "column_type": "categorical",
                    "missing_count": 0
                },
                "Salary": {
                    "column_type": "numeric",
                    "missing_count": 0
                }
            }
        },
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = generate_preprocessing_recommendations(
        df,
        eda
    )

    recommendations = result["recommendations"]

    assert any(
        item["column"] == "State"
        and item["type"] == "categorical_encoding"
        and item["action"] == "encoding"
        for item in recommendations
    )


def test_target_outlier_requires_investigation():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, 40000, 50000, 100000]
    })

    eda = {
        "ml_task": {
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric",
                    "missing_count": 0
                },
                "Salary": {
                    "column_type": "numeric",
                    "missing_count": 0
                }
            }
        },
        "outliers": {
            "Salary": {
                "count": 1,
                "percentage": 25.0
            }
        },
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = generate_preprocessing_recommendations(
        df,
        eda
    )

    recommendations = result["recommendations"]

    target_outlier = next(
        item
        for item in recommendations
        if item["type"] == "target_outliers"
    )

    assert target_outlier["column"] == "Salary"
    assert target_outlier["action"] == "investigate"
    assert "remov" not in target_outlier["message"].lower()


def test_feature_outlier_can_be_investigated_or_transformed():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 100],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "ml_task": {
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric",
                    "missing_count": 0
                },
                "Salary": {
                    "column_type": "numeric",
                    "missing_count": 0
                }
            }
        },
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

    result = generate_preprocessing_recommendations(
        df,
        eda
    )

    recommendations = result["recommendations"]

    feature_outlier = next(
        item
        for item in recommendations
        if item["type"] == "feature_outliers"
    )

    assert feature_outlier["column"] == "Age"
    assert feature_outlier["action"] == "investigate_or_transform"


def test_constant_feature_should_be_removed():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Country": ["India", "India", "India", "India"],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "ml_task": {
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric",
                    "missing_count": 0,
                    "is_constant": False
                },
                "Country": {
                    "column_type": "categorical",
                    "missing_count": 0,
                    "is_constant": True
                },
                "Salary": {
                    "column_type": "numeric",
                    "missing_count": 0,
                    "is_constant": False
                }
            }
        },
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = generate_preprocessing_recommendations(
        df,
        eda
    )

    recommendations = result["recommendations"]

    constant_feature = next(
        item
        for item in recommendations
        if item["type"] == "constant_feature"
    )

    assert constant_feature["column"] == "Country"
    assert constant_feature["action"] == "remove"


def test_target_correlation_recommends_investigation():
    df = pd.DataFrame({
        "Experience": [1, 2, 3, 4],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "ml_task": {
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Experience": {
                    "column_type": "numeric",
                    "missing_count": 0
                },
                "Salary": {
                    "column_type": "numeric",
                    "missing_count": 0
                }
            }
        },
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": [
                {
                    "column_a": "Experience",
                    "column_b": "Salary",
                    "correlation": 0.95
                }
            ]
        }
    }

    result = generate_preprocessing_recommendations(
        df,
        eda
    )

    recommendations = result["recommendations"]

    correlation_recommendation = next(
        item
        for item in recommendations
        if item["type"] == "target_correlation"
    )

    assert correlation_recommendation["action"] == "investigate"
    assert correlation_recommendation["columns"] == [
        "Experience",
        "Salary"
    ]
    assert correlation_recommendation["correlation"] == 0.95


def test_feature_multicollinearity_recommendation():
    df = pd.DataFrame({
        "Feature_A": [1, 2, 3, 4],
        "Feature_B": [2, 4, 6, 8],
        "Target": [10, 20, 30, 40]
    })

    eda = {
        "ml_task": {
            "target": "Target"
        },
        "feature_summary": {
            "features": {
                "Feature_A": {
                    "column_type": "numeric",
                    "missing_count": 0
                },
                "Feature_B": {
                    "column_type": "numeric",
                    "missing_count": 0
                },
                "Target": {
                    "column_type": "numeric",
                    "missing_count": 0
                }
            }
        },
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": [
                {
                    "column_a": "Feature_A",
                    "column_b": "Feature_B",
                    "correlation": 0.98
                }
            ]
        }
    }

    result = generate_preprocessing_recommendations(
        df,
        eda
    )

    recommendations = result["recommendations"]

    multicollinearity = next(
        item
        for item in recommendations
        if item["type"] == "multicollinearity"
    )

    assert multicollinearity["action"] == (
        "investigate_feature_redundancy"
    )
    assert multicollinearity["columns"] == [
        "Feature_A",
        "Feature_B"
    ]


def test_clean_dataset_returns_no_recommendations():
    df = pd.DataFrame({
        "Age": [20, 25, 30, 35],
        "Salary": [30000, 40000, 50000, 60000]
    })

    eda = {
        "ml_task": {
            "target": "Salary"
        },
        "feature_summary": {
            "features": {
                "Age": {
                    "column_type": "numeric",
                    "missing_count": 0,
                    "is_constant": False
                },
                "Salary": {
                    "column_type": "numeric",
                    "missing_count": 0,
                    "is_constant": False
                }
            }
        },
        "outliers": {},
        "correlation_analysis": {
            "highly_correlated_pairs": []
        }
    }

    result = generate_preprocessing_recommendations(
        df,
        eda
    )

    assert result["status"] == "available"
    assert result["recommendation_count"] == 0
    assert result["recommendations"] == []
    assert (
        result["dataset_status"]
        == "No missing values require imputation."
    )
    