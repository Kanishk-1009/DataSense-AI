import pytest
import pandas as pd
import numpy as np

from backend.core.eda.outliers import (
    detect_outliers,
    _detect_iqr,
    _detect_zscore,
    _detect_isolation_forest,
)


# ---- Fixtures -------------------------------------------------------------

@pytest.fixture
def clean_df():
    """Dataset with no outliers."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({"value": rng.normal(50, 5, 200)})


@pytest.fixture
def outlier_df():
    """Dataset with clear outliers."""
    data = list(range(1, 101)) + [1000, -1000]
    return pd.DataFrame({"value": data})


@pytest.fixture
def multi_col_df():
    """Multi-column dataset."""
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "a": list(rng.normal(0, 1, 100)) + [50.0],
        "b": list(rng.normal(10, 2, 100)) + [10.5],
    })


# ---- _detect_iqr ----------------------------------------------------------

class TestDetectIQR:
    def test_returns_expected_keys(self, outlier_df):
        result = _detect_iqr(outlier_df["value"])
        assert "count" in result
        assert "percentage" in result
        assert "lower_bound" in result
        assert "upper_bound" in result

    def test_detects_clear_outliers(self, outlier_df):
        result = _detect_iqr(outlier_df["value"])
        assert result["count"] >= 2

    def test_clean_series_low_outliers(self, clean_df):
        # A 200-sample normal draw may have a small number of IQR outliers
        # by chance — assert it's statistically low (≤ 3), not necessarily 0.
        result = _detect_iqr(clean_df["value"])
        assert result["count"] <= 3

    def test_percentage_in_range(self, outlier_df):
        result = _detect_iqr(outlier_df["value"])
        assert 0.0 <= result["percentage"] <= 100.0


# ---- _detect_zscore -------------------------------------------------------

class TestDetectZScore:
    def test_returns_expected_keys(self, outlier_df):
        result = _detect_zscore(outlier_df["value"])
        assert "count" in result
        assert "percentage" in result
        assert "threshold" in result

    def test_detects_extreme_outliers(self, outlier_df):
        result = _detect_zscore(outlier_df["value"])
        assert result["count"] >= 2

    def test_constant_series_zero_outliers(self):
        s = pd.Series([5.0] * 50)
        result = _detect_zscore(s)
        assert result["count"] == 0

    def test_custom_threshold(self, outlier_df):
        strict = _detect_zscore(outlier_df["value"], threshold=1.0)
        loose = _detect_zscore(outlier_df["value"], threshold=5.0)
        assert strict["count"] >= loose["count"]


# ---- _detect_isolation_forest ---------------------------------------------

class TestDetectIsolationForest:
    def test_returns_expected_keys(self, outlier_df):
        result = _detect_isolation_forest(outlier_df["value"])
        assert "count" in result
        assert "percentage" in result

    def test_detects_anomalies(self, outlier_df):
        result = _detect_isolation_forest(outlier_df["value"])
        assert result["count"] >= 1

    def test_percentage_in_range(self, outlier_df):
        result = _detect_isolation_forest(outlier_df["value"])
        assert 0.0 <= result["percentage"] <= 100.0


# ---- detect_outliers (main function) ------------------------------------

class TestDetectOutliers:
    def test_returns_dict(self, multi_col_df):
        result = detect_outliers(multi_col_df)
        assert isinstance(result, dict)

    def test_numeric_columns_present(self, multi_col_df):
        result = detect_outliers(multi_col_df)
        assert "a" in result
        assert "b" in result

    def test_backward_compat_keys(self, multi_col_df):
        result = detect_outliers(multi_col_df)
        for col_info in result.values():
            assert "count" in col_info
            assert "percentage" in col_info
            assert "lower_bound" in col_info
            assert "upper_bound" in col_info

    def test_all_methods_present(self, multi_col_df):
        result = detect_outliers(multi_col_df)
        for col_info in result.values():
            assert "iqr" in col_info
            assert "zscore" in col_info
            assert "isolation_forest" in col_info

    def test_consensus_count_present(self, multi_col_df):
        result = detect_outliers(multi_col_df)
        for col_info in result.values():
            assert "consensus_count" in col_info

    def test_skips_small_series(self):
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = detect_outliers(df)
        assert result == {}

    def test_ignores_categorical_columns(self):
        df = pd.DataFrame({
            "num": [1, 2, 3, 4, 5, 1000],
            "cat": ["a", "b", "c", "a", "b", "c"],
        })
        result = detect_outliers(df)
        assert "cat" not in result
        assert "num" in result

    def test_handles_missing_values(self):
        data = list(range(1, 51)) + [None, None, 1000]
        df = pd.DataFrame({"x": data})
        result = detect_outliers(df)
        assert "x" in result
