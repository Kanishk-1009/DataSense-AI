"""
Tests for the M6-B ground-truth rubric.

Validates:
- Each eda_extractor correctly identifies its condition
- extract_triggered_conditions returns the right subset
- Rubric entries are unique by condition_id
- All expected_keywords lists are non-empty
"""

from __future__ import annotations

import pytest

from backend.evaluation.rubric import (
    GROUND_TRUTH_RUBRIC,
    RubricEntry,
    extract_triggered_conditions,
)


# ---------------------------------------------------------------------------
# Fixtures — synthetic EDA dicts
# ---------------------------------------------------------------------------

@pytest.fixture
def eda_high_missingness():
    return {
        "missingness": {
            "summary": {
                "overall_missing_percentage": 35.0,
                "columns_with_missing": 3,
            }
        },
        "correlation_analysis": {"highly_correlated_pairs": []},
        "outliers": {},
        "feature_summary": {"features": {}},
        "ml_task": {"task": "classification"},
        "ml_recommendation": {},
        "target_analysis": {},
    }


@pytest.fixture
def eda_low_missingness():
    return {
        "missingness": {
            "summary": {
                "overall_missing_percentage": 5.0,
                "columns_with_missing": 1,
            }
        },
        "correlation_analysis": {"highly_correlated_pairs": []},
        "outliers": {},
        "feature_summary": {"features": {}},
        "ml_task": {"task": "classification"},
        "ml_recommendation": {},
        "target_analysis": {},
    }


@pytest.fixture
def eda_with_correlation():
    return {
        "missingness": {"summary": {"overall_missing_percentage": 0.0}},
        "correlation_analysis": {
            "highly_correlated_pairs": [
                {"feature_1": "age", "feature_2": "fare", "correlation": 0.92}
            ]
        },
        "outliers": {},
        "feature_summary": {"features": {}},
        "ml_task": {"task": "classification"},
        "ml_recommendation": {},
        "target_analysis": {},
    }


@pytest.fixture
def eda_with_outliers():
    return {
        "missingness": {"summary": {"overall_missing_percentage": 0.0}},
        "correlation_analysis": {"highly_correlated_pairs": []},
        "outliers": {"age": {"iqr_outliers": 5, "zscore_outliers": 3}},
        "feature_summary": {"features": {}},
        "ml_task": {"task": "classification"},
        "ml_recommendation": {},
        "target_analysis": {},
    }


@pytest.fixture
def eda_with_categorical():
    return {
        "missingness": {"summary": {"overall_missing_percentage": 0.0}},
        "correlation_analysis": {"highly_correlated_pairs": []},
        "outliers": {},
        "feature_summary": {
            "features": {
                "sex": {"dtype": "object", "unique_count": 2},
                "embarked": {"dtype": "object", "unique_count": 3},
            }
        },
        "ml_task": {"task": "classification"},
        "ml_recommendation": {},
        "target_analysis": {},
    }


@pytest.fixture
def eda_classification_with_imbalance():
    return {
        "missingness": {"summary": {"overall_missing_percentage": 0.0}},
        "correlation_analysis": {"highly_correlated_pairs": []},
        "outliers": {},
        "feature_summary": {"features": {}},
        "ml_task": {"task": "binary_classification"},
        "ml_recommendation": {"status": "available", "notes": "Class imbalance detected."},
        "target_analysis": {"class_balance": "imbalanced"},
    }


@pytest.fixture
def eda_regression():
    return {
        "missingness": {"summary": {"overall_missing_percentage": 0.0}},
        "correlation_analysis": {"highly_correlated_pairs": []},
        "outliers": {},
        "feature_summary": {"features": {}},
        "ml_task": {"task": "regression"},
        "ml_recommendation": {},
        "target_analysis": {},
    }


@pytest.fixture
def eda_clean():
    return {
        "missingness": {"summary": {"overall_missing_percentage": 0.0}},
        "correlation_analysis": {"highly_correlated_pairs": []},
        "outliers": {},
        "feature_summary": {"features": {}},
        "ml_task": {"task": "classification"},
        "ml_recommendation": {},
        "target_analysis": {},
    }


# ---------------------------------------------------------------------------
# Rubric structure tests
# ---------------------------------------------------------------------------

class TestRubricStructure:
    def test_rubric_is_non_empty(self):
        assert len(GROUND_TRUTH_RUBRIC) >= 4

    def test_all_entries_are_rubric_entry(self):
        for entry in GROUND_TRUTH_RUBRIC:
            assert isinstance(entry, RubricEntry)

    def test_condition_ids_are_unique(self):
        ids = [e.condition_id for e in GROUND_TRUTH_RUBRIC]
        assert len(ids) == len(set(ids)), "Duplicate condition_ids found"

    def test_all_have_expected_keywords(self):
        for entry in GROUND_TRUTH_RUBRIC:
            assert len(entry.expected_keywords) > 0, (
                f"condition '{entry.condition_id}' has no expected_keywords"
            )

    def test_all_have_descriptions(self):
        for entry in GROUND_TRUTH_RUBRIC:
            assert isinstance(entry.description, str) and entry.description.strip()

    def test_all_have_callable_extractor(self):
        for entry in GROUND_TRUTH_RUBRIC:
            assert callable(entry.eda_extractor)


# ---------------------------------------------------------------------------
# Individual eda_extractor tests
# ---------------------------------------------------------------------------

class TestEdaExtractors:
    def test_high_missingness_detected(self, eda_high_missingness):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "high_missingness")
        assert entry.eda_extractor(eda_high_missingness) is True

    def test_high_missingness_not_detected_low(self, eda_low_missingness):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "high_missingness")
        assert entry.eda_extractor(eda_low_missingness) is False

    def test_high_correlation_detected(self, eda_with_correlation):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "high_correlation")
        assert entry.eda_extractor(eda_with_correlation) is True

    def test_high_correlation_not_detected_empty(self, eda_clean):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "high_correlation")
        assert entry.eda_extractor(eda_clean) is False

    def test_outliers_detected(self, eda_with_outliers):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "outliers_present")
        assert entry.eda_extractor(eda_with_outliers) is True

    def test_outliers_not_detected_empty(self, eda_clean):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "outliers_present")
        assert entry.eda_extractor(eda_clean) is False

    def test_categorical_features_detected(self, eda_with_categorical):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "categorical_features")
        assert entry.eda_extractor(eda_with_categorical) is True

    def test_categorical_features_not_detected_empty(self, eda_clean):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "categorical_features")
        assert entry.eda_extractor(eda_clean) is False

    def test_regression_detected(self, eda_regression):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "regression_task")
        assert entry.eda_extractor(eda_regression) is True

    def test_regression_not_detected_classification(self, eda_clean):
        entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "regression_task")
        assert entry.eda_extractor(eda_clean) is False


# ---------------------------------------------------------------------------
# extract_triggered_conditions
# ---------------------------------------------------------------------------

class TestExtractTriggeredConditions:
    def test_clean_dataset_no_conditions(self, eda_clean):
        triggered = extract_triggered_conditions(eda_clean)
        assert triggered == []

    def test_high_missingness_included(self, eda_high_missingness):
        triggered = extract_triggered_conditions(eda_high_missingness)
        ids = [e.condition_id for e in triggered]
        assert "high_missingness" in ids

    def test_only_triggered_conditions_returned(self, eda_with_outliers):
        triggered = extract_triggered_conditions(eda_with_outliers)
        ids = [e.condition_id for e in triggered]
        assert "outliers_present" in ids
        assert "high_missingness" not in ids   # missingness is 0%
        assert "high_correlation" not in ids   # no correlated pairs

    def test_regression_triggers_regression_condition(self, eda_regression):
        triggered = extract_triggered_conditions(eda_regression)
        ids = [e.condition_id for e in triggered]
        assert "regression_task" in ids

    def test_multi_condition_dataset(self, eda_with_outliers, eda_with_categorical):
        # Combine two partial EDA dicts
        combined = {**eda_with_outliers}
        combined["feature_summary"] = eda_with_categorical["feature_summary"]
        triggered = extract_triggered_conditions(combined)
        ids = [e.condition_id for e in triggered]
        assert "outliers_present" in ids
        assert "categorical_features" in ids

    def test_returns_list_of_rubric_entries(self, eda_high_missingness):
        triggered = extract_triggered_conditions(eda_high_missingness)
        for entry in triggered:
            assert isinstance(entry, RubricEntry)

    def test_empty_eda_does_not_crash(self):
        triggered = extract_triggered_conditions({})
        assert isinstance(triggered, list)
