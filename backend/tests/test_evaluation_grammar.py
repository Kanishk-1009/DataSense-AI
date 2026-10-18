"""
Unit tests for Action-Object Dependency Grammar with Negation Guards (M6-B).
Uses standard library unittest so it runs in any environment without external dependencies.
"""

import unittest
from backend.evaluation.metrics import (
    _split_into_sentences,
    _tokenize_sentence,
    _evaluate_action_object_grammar,
    score_recommendation_accuracy,
)
from backend.evaluation.rubric import (
    GROUND_TRUTH_RUBRIC,
    extract_triggered_conditions,
    get_effective_targets,
)


class TestSentenceSplitting(unittest.TestCase):
    def test_markdown_bullets_and_newlines(self):
        text = (
            "- Impute missing Age values.\n"
            "* Clip extreme Fare outliers.\n"
            "1. Encode categorical Sex column. Also check Embarked."
        )
        sentences = _split_into_sentences(text)
        self.assertEqual(len(sentences), 4)
        self.assertEqual(sentences[0], "Impute missing Age values.")
        self.assertEqual(sentences[1], "Clip extreme Fare outliers.")
        self.assertEqual(sentences[2], "Encode categorical Sex column.")
        self.assertEqual(sentences[3], "Also check Embarked.")

    def test_empty_text(self):
        self.assertEqual(_split_into_sentences(""), [])
        self.assertEqual(_split_into_sentences(None), [])


class TestActionObjectGrammar(unittest.TestCase):
    def setUp(self):
        self.missing_actions = ["imput", "fill", "replac", "drop", "remov", "estimat", "handl"]
        self.missing_targets = ["miss", "null", "nan", "empt", "age", "cabin"]
        self.outlier_actions = ["cap", "clip", "transform", "winsoriz", "scale", "remov", "drop"]
        self.outlier_targets = ["outlier", "extreme", "skew", "fare"]

    def test_affirmative_positive_match(self):
        sentence = "We recommend imputing the missing values in the Age column using median."
        is_match, reason = _evaluate_action_object_grammar(
            sentence, self.missing_actions, self.missing_targets
        )
        self.assertTrue(is_match)
        self.assertIn("imput", str(reason))

    def test_negation_guard_rejects_negative_instruction(self):
        # Even though "drop" and "missing" are in the sentence, "not" precedes "drop"
        sentence = "Do not drop missing rows, as it causes 20% data loss."
        is_match, reason = _evaluate_action_object_grammar(
            sentence, self.missing_actions, self.missing_targets
        )
        self.assertFalse(is_match)
        self.assertIn("all candidate actions were negated", str(reason))

    def test_avoid_negation_guard(self):
        sentence = "Avoid removing outliers from the dataset."
        is_match, reason = _evaluate_action_object_grammar(
            sentence, self.outlier_actions, self.outlier_targets
        )
        self.assertFalse(is_match)

    def test_conjunction_with_affirmative_alternative(self):
        # "drop" is negated, but "impute" is affirmative in the same sentence
        sentence = "Do not drop missing rows, instead impute them using median."
        is_match, reason = _evaluate_action_object_grammar(
            sentence, self.missing_actions, self.missing_targets
        )
        self.assertTrue(is_match)
        self.assertIn("impute", str(reason))

    def test_dynamic_column_binding(self):
        # "Fare" is the column name; "outlier" is not explicitly mentioned
        sentence = "Clip extreme values in the Fare column."
        is_match, reason = _evaluate_action_object_grammar(
            sentence, self.outlier_actions, self.outlier_targets
        )
        self.assertTrue(is_match)

    def test_accidental_keyword_rejection_across_contexts(self):
        # Action exists without target
        sentence1 = "We handle models with extreme care."
        is_match1, _ = _evaluate_action_object_grammar(
            sentence1, self.missing_actions, self.missing_targets
        )
        self.assertFalse(is_match1)

        # Target exists without action
        sentence2 = "The dataset has many missing values."
        is_match2, _ = _evaluate_action_object_grammar(
            sentence2, self.missing_actions, self.missing_targets
        )
        self.assertFalse(is_match2)


class TestDynamicTargetExtraction(unittest.TestCase):
    def test_titanic_eda_dynamic_injection(self):
        eda = {
            "missingness": {
                "summary": {"overall_missing_percentage": 25.0, "likely_mar_columns": ["Age"]},
                "columns": {
                    "Age": {"missing_count": 177, "missing_percentage": 19.8},
                    "Cabin": {"missing_count": 687, "missing_percentage": 77.1},
                },
            },
            "outliers": {
                "Fare": {"iqr_outliers": 116},
            },
            "feature_summary": {
                "features": {
                    "Sex": {"column_type": "categorical"},
                    "Embarked": {"column_type": "categorical"},
                }
            },
            "correlation_analysis": {
                "highly_correlated_pairs": [
                    {"feature_1": "SibSp", "feature_2": "Parch"}
                ]
            },
            "ml_task": {"task": "classification", "target": "Survived"},
            "ml_recommendation": {},
            "target_analysis": {},
        }

        # Check missingness entry
        missing_entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "high_missingness")
        effective_missing_targets = get_effective_targets(missing_entry, eda)
        self.assertIn("age", effective_missing_targets)
        self.assertIn("cabin", effective_missing_targets)

        # Check outliers entry
        outlier_entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "outliers_present")
        effective_outlier_targets = get_effective_targets(outlier_entry, eda)
        self.assertIn("fare", effective_outlier_targets)

        # Check categorical entry
        cat_entry = next(e for e in GROUND_TRUTH_RUBRIC if e.condition_id == "categorical_features")
        effective_cat_targets = get_effective_targets(cat_entry, eda)
        self.assertIn("sex", effective_cat_targets)
        self.assertIn("embarked", effective_cat_targets)


class TestRecommendationAccuracyIntegration(unittest.TestCase):
    def setUp(self):
        self.eda = {
            "missingness": {
                "summary": {"overall_missing_percentage": 30.0},
                "columns": {"Age": {"missing_count": 100}},
            },
            "outliers": {"Fare": {"count": 20}},
            "feature_summary": {
                "features": {"Sex": {"column_type": "categorical"}}
            },
            "correlation_analysis": {"highly_correlated_pairs": []},
            "ml_task": {"task": "classification", "target": "Survived"},
            "ml_recommendation": {},
            "target_analysis": {},
        }

    def test_affirmative_recommendations_score_full(self):
        response = {
            "recommendations": [
                "Impute the missing values in Age using median.",
                "Apply Winsorization to clip extreme Fare values.",
                "One-hot encode the categorical Sex feature.",
            ],
            "narrative": "Clean dataset ready for modeling.",
        }
        accuracy, checks = score_recommendation_accuracy(response, self.eda)
        self.assertIsNotNone(accuracy)
        self.assertEqual(accuracy, 1.0)
        for check in checks:
            self.assertTrue(check.recommendation_matched, f"{check.condition_id} should be matched")

    def test_negated_recommendations_fail(self):
        response = {
            "recommendations": [
                "Do not impute missing values, leave them empty.",
                "Never clip outliers in Fare.",
                "Avoid encoding Sex.",
            ],
            "narrative": "",
        }
        accuracy, checks = score_recommendation_accuracy(response, self.eda)
        self.assertIsNotNone(accuracy)
        self.assertEqual(accuracy, 0.0)
        for check in checks:
            self.assertFalse(check.recommendation_matched, f"{check.condition_id} should NOT be matched")


if __name__ == "__main__":
    unittest.main()
