"""
Tests for analyze_missingness().

The MCAR/MAR labels are heuristic indicators, not formal statistical
classifications.  Tests reflect this by checking for 'likely_mcar' and
'likely_mar' and by verifying that the raw Spearman correlation is
exposed so callers can judge signal strength themselves.
"""

import pytest
import pandas as pd
import numpy as np

from backend.core.eda.missingness import analyze_missingness


# ---- Fixtures -------------------------------------------------------------

@pytest.fixture
def complete_df():
    return pd.DataFrame({
        "a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "b": [10.0, 20.0, 30.0, 40.0, 50.0],
    })


@pytest.fixture
def random_missing_df():
    """Missing values inserted at random positions — likely MCAR-like."""
    rng = np.random.default_rng(42)
    n = 100
    a = rng.normal(0, 1, n).tolist()
    b = rng.normal(5, 2, n).tolist()
    for i in rng.choice(n, 15, replace=False):
        a[i] = None
    return pd.DataFrame({"a": a, "b": b})


@pytest.fixture
def correlated_missing_df():
    """
    Missing values in 'a' correlate strongly with values of 'b'.
    This is a constructed MAR-like scenario.
    """
    n = 100
    b = list(range(n))
    a = [float(i) for i in range(n)]
    for i in range(71, 100):   # null 'a' where 'b' > 70
        a[i] = None
    return pd.DataFrame({"a": a, "b": b})


# ---- Return structure -----------------------------------------------------

class TestReturnStructure:
    def test_returns_dict(self, complete_df):
        result = analyze_missingness(complete_df)
        assert isinstance(result, dict)

    def test_has_summary_and_columns_keys(self, complete_df):
        result = analyze_missingness(complete_df)
        assert "summary" in result
        assert "columns" in result

    def test_summary_has_expected_keys(self, complete_df):
        summary = analyze_missingness(complete_df)["summary"]
        assert "total_missing_cells" in summary
        assert "total_cells" in summary
        assert "overall_missing_percentage" in summary
        assert "columns_with_missing" in summary
        assert "likely_mar_columns" in summary
        assert "likely_mcar_columns" in summary
        assert "heuristic_note" in summary

    def test_columns_covers_all_columns(self, random_missing_df):
        result = analyze_missingness(random_missing_df)
        for col in random_missing_df.columns:
            assert col in result["columns"]

    def test_each_column_has_expected_keys(self, random_missing_df):
        result = analyze_missingness(random_missing_df)
        for col_info in result["columns"].values():
            assert "missing_count" in col_info
            assert "missing_percentage" in col_info
            assert "indicator" in col_info
            assert "max_spearman_correlation" in col_info
            assert "note" in col_info

    def test_indicator_values_are_valid(self, random_missing_df):
        valid_indicators = {"complete", "likely_mcar", "likely_mar", "unknown"}
        result = analyze_missingness(random_missing_df)
        for col_info in result["columns"].values():
            assert col_info["indicator"] in valid_indicators


# ---- Complete dataset -----------------------------------------------------

class TestCompleteDf:
    def test_zero_missing_cells(self, complete_df):
        result = analyze_missingness(complete_df)
        assert result["summary"]["total_missing_cells"] == 0

    def test_no_columns_with_missing(self, complete_df):
        result = analyze_missingness(complete_df)
        assert result["summary"]["columns_with_missing"] == 0

    def test_all_columns_complete_indicator(self, complete_df):
        result = analyze_missingness(complete_df)
        for col_info in result["columns"].values():
            assert col_info["indicator"] == "complete"

    def test_complete_columns_have_no_spearman(self, complete_df):
        result = analyze_missingness(complete_df)
        for col_info in result["columns"].values():
            assert col_info["max_spearman_correlation"] is None


# ---- Random missing (MCAR-like) ------------------------------------------

class TestRandomMissingDf:
    def test_missing_count_correct(self, random_missing_df):
        result = analyze_missingness(random_missing_df)
        expected = int(random_missing_df["a"].isna().sum())
        assert result["columns"]["a"]["missing_count"] == expected

    def test_missing_percentage_correct(self, random_missing_df):
        result = analyze_missingness(random_missing_df)
        expected = round(random_missing_df["a"].isna().mean() * 100, 2)
        assert result["columns"]["a"]["missing_percentage"] == expected

    def test_indicator_is_heuristic_label(self, random_missing_df):
        # Must be one of the valid heuristic labels — not a hard assertion
        # on MCAR/MAR since this is a heuristic, not a statistical test.
        valid = {"likely_mcar", "likely_mar", "unknown"}
        result = analyze_missingness(random_missing_df)
        assert result["columns"]["a"]["indicator"] in valid

    def test_spearman_correlation_exposed(self, random_missing_df):
        result = analyze_missingness(random_missing_df)
        col_info = result["columns"]["a"]
        # Spearman should be a float when computable
        if col_info["indicator"] != "unknown":
            assert isinstance(col_info["max_spearman_correlation"], float)


# ---- Correlated missing (MAR-like) ----------------------------------------

class TestCorrelatedMissingDf:
    def test_a_has_missing(self, correlated_missing_df):
        result = analyze_missingness(correlated_missing_df)
        assert result["columns"]["a"]["missing_count"] > 0

    def test_likely_mar_indicator_detected(self, correlated_missing_df):
        """
        With strongly patterned missingness (null where b > 70), the
        heuristic should flag 'a' as likely_mar.
        """
        result = analyze_missingness(correlated_missing_df)
        assert result["columns"]["a"]["indicator"] == "likely_mar"

    def test_likely_mar_has_warning(self, correlated_missing_df):
        result = analyze_missingness(correlated_missing_df)
        assert "warning" in result["columns"]["a"]

    def test_likely_mar_listed_in_summary(self, correlated_missing_df):
        result = analyze_missingness(correlated_missing_df)
        assert "a" in result["summary"]["likely_mar_columns"]

    def test_spearman_above_threshold(self, correlated_missing_df):
        result = analyze_missingness(correlated_missing_df)
        corr = result["columns"]["a"]["max_spearman_correlation"]
        assert corr is not None
        assert corr >= 0.2  # default threshold

    def test_note_mentions_heuristic(self, correlated_missing_df):
        result = analyze_missingness(correlated_missing_df)
        note = result["columns"]["a"]["note"].lower()
        assert "heuristic" in note


# ---- Summary accuracy ----------------------------------------------------

class TestSummaryAccuracy:
    def test_total_cells_correct(self, random_missing_df):
        result = analyze_missingness(random_missing_df)
        expected = random_missing_df.shape[0] * random_missing_df.shape[1]
        assert result["summary"]["total_cells"] == expected

    def test_overall_percentage_correct(self, random_missing_df):
        result = analyze_missingness(random_missing_df)
        total_cells = random_missing_df.shape[0] * random_missing_df.shape[1]
        total_missing = int(random_missing_df.isna().sum().sum())
        expected = round(total_missing / total_cells * 100, 2)
        assert result["summary"]["overall_missing_percentage"] == expected

    def test_heuristic_note_present(self, complete_df):
        result = analyze_missingness(complete_df)
        assert isinstance(result["summary"]["heuristic_note"], str)
        assert len(result["summary"]["heuristic_note"]) > 0
