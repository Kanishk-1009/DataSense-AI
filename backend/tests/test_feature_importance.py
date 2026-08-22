import pytest
import pandas as pd
import numpy as np

from backend.core.eda.feature_importance import compute_feature_importance


# ---- Fixtures -------------------------------------------------------------

@pytest.fixture
def classification_df():
    rng = np.random.default_rng(42)
    n = 100
    a = rng.normal(0, 1, n)
    b = rng.normal(5, 2, n)
    target = (a + b > 5).astype(int)
    return pd.DataFrame({"feature_a": a, "feature_b": b, "label": target})


@pytest.fixture
def regression_df():
    rng = np.random.default_rng(7)
    n = 100
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(3, 1, n)
    y = 2 * x1 + x2 + rng.normal(0, 0.5, n)
    return pd.DataFrame({"x1": x1, "x2": x2, "y": y})


@pytest.fixture
def mixed_df():
    rng = np.random.default_rng(0)
    n = 80
    return pd.DataFrame({
        "num": rng.normal(0, 1, n),
        "cat": rng.choice(["A", "B", "C"], n),
        "target": rng.choice([0, 1], n),
    })


# ---- Status and structure -------------------------------------------------

class TestComputeFeatureImportanceStatus:
    def test_returns_dict(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        assert isinstance(result, dict)

    def test_available_status(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        assert result["status"] == "available"

    def test_error_on_missing_target(self, classification_df):
        result = compute_feature_importance(classification_df, target="nonexistent")
        assert result["status"] == "error"

    def test_error_on_no_features(self):
        df = pd.DataFrame({"only_target": [0, 1, 0, 1, 0, 1]})
        result = compute_feature_importance(df, target="only_target")
        assert result["status"] == "error"

    def test_insufficient_data(self):
        df = pd.DataFrame({"x": [1, 2, 3], "y": [0, 1, 0]})
        result = compute_feature_importance(df, target="y")
        assert result["status"] in ("error", "insufficient_data")


# ---- Random Forest results ------------------------------------------------

class TestRandomForestImportance:
    def test_rf_list_present(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        assert "random_forest" in result
        assert isinstance(result["random_forest"], list)

    def test_rf_contains_all_features(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        feature_names = {item["feature"] for item in result["random_forest"]}
        assert "feature_a" in feature_names
        assert "feature_b" in feature_names
        assert "label" not in feature_names

    def test_rf_ranked_in_order(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        importances = [item["importance"] for item in result["random_forest"]]
        assert importances == sorted(importances, reverse=True)

    def test_rf_ranks_sequential(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        ranks = [item["rank"] for item in result["random_forest"]]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_rf_regression_works(self, regression_df):
        result = compute_feature_importance(regression_df, target="y", task_type="regression")
        assert result["status"] == "available"
        assert len(result["random_forest"]) == 2


# ---- Mutual Information results ------------------------------------------

class TestMutualInformation:
    def test_mi_list_present(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        assert "mutual_information" in result
        assert isinstance(result["mutual_information"], list)

    def test_mi_contains_all_features(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        feature_names = {item["feature"] for item in result["mutual_information"]}
        assert "feature_a" in feature_names
        assert "feature_b" in feature_names

    def test_mi_ranked_in_order(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        scores = [item["score"] for item in result["mutual_information"]]
        assert scores == sorted(scores, reverse=True)

    def test_mi_normalized_score_in_range(self, classification_df):
        result = compute_feature_importance(classification_df, target="label")
        for item in result["mutual_information"]:
            assert 0.0 <= item["normalized_score"] <= 1.0


# ---- Mixed types ----------------------------------------------------------

class TestMixedTypes:
    def test_handles_categorical_features(self, mixed_df):
        result = compute_feature_importance(mixed_df, target="target")
        assert result["status"] == "available"
        feature_names = {item["feature"] for item in result["random_forest"]}
        assert "cat" in feature_names
        assert "num" in feature_names
