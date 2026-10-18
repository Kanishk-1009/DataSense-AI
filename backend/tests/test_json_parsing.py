"""
Unit tests for robust JSON parsing in single_agent and multi_agent nodes.
Uses standard library unittest so it runs in any environment without external test runners.
"""

import unittest
from backend.agents.single_agent import _parse_llm_response


class TestRobustJSONParsing(unittest.TestCase):
    def test_clean_json(self):
        raw = '{"narrative": "Clean narrative", "key_risks": ["Risk 1"], "recommendations": ["Rec 1"], "confidence": 0.9}'
        res = _parse_llm_response(raw)
        self.assertEqual(res["narrative"], "Clean narrative")
        self.assertEqual(res["key_risks"], ["Risk 1"])
        self.assertEqual(res["recommendations"], ["Rec 1"])
        self.assertEqual(res["confidence"], 0.9)
        self.assertNotIn("_parse_error", res)

    def test_markdown_fence_without_tag(self):
        raw = '```\n{"narrative": "Fenced narrative", "key_risks": [], "recommendations": [], "confidence": 0.8}\n```'
        res = _parse_llm_response(raw)
        self.assertEqual(res["narrative"], "Fenced narrative")
        self.assertNotIn("_parse_error", res)

    def test_markdown_fence_with_json_tag(self):
        raw = '```json\n{"narrative": "JSON tagged", "key_risks": ["R"], "recommendations": ["Rec"], "confidence": 0.85}\n```'
        res = _parse_llm_response(raw)
        self.assertEqual(res["narrative"], "JSON tagged")
        self.assertNotIn("_parse_error", res)

    def test_conversational_prefix_and_fence(self):
        raw = (
            'Here is the complete analysis of your dataset:\n\n'
            '```json\n'
            '{\n'
            '  "narrative": "Preamble test",\n'
            '  "key_risks": ["Missing values in age"],\n'
            '  "recommendations": ["Impute with median"],\n'
            '  "confidence": 0.75\n'
            '}\n'
            '```\n\n'
            'I hope this helps your ML modeling!'
        )
        res = _parse_llm_response(raw)
        self.assertEqual(res["narrative"], "Preamble test")
        self.assertEqual(res["recommendations"], ["Impute with median"])
        self.assertNotIn("_parse_error", res)

    def test_embedded_json_without_fences(self):
        raw = 'Analysis output is {"narrative": "Embedded", "key_risks": [], "recommendations": ["Action"], "confidence": 0.5} thanks.'
        res = _parse_llm_response(raw)
        self.assertEqual(res["narrative"], "Embedded")
        self.assertEqual(res["recommendations"], ["Action"])
        self.assertNotIn("_parse_error", res)

    def test_trailing_comma_cleanup(self):
        raw = '{"narrative": "Trailing comma test", "key_risks": ["Risk A",], "recommendations": ["Rec A",], "confidence": 0.7,}'
        res = _parse_llm_response(raw)
        self.assertEqual(res["narrative"], "Trailing comma test")
        self.assertEqual(res["key_risks"], ["Risk A"])
        self.assertEqual(res["recommendations"], ["Rec A"])
        self.assertNotIn("_parse_error", res)

    def test_empty_string(self):
        res = _parse_llm_response("")
        self.assertIn("_parse_error", res)

    def test_invalid_text_fallback(self):
        raw = "This is purely text without any json structure at all."
        res = _parse_llm_response(raw)
        self.assertEqual(res["narrative"], raw)
        self.assertEqual(res["recommendations"], [])
        self.assertIn("_parse_error", res)

    def test_normalize_alternate_keys(self):
        from backend.agents.single_agent import _normalize_keys
        raw_dict = {
            "summary": "This is a summary",
            "risks": ["Risk 1", "Risk 2"],
            "actions": ["Action 1", "Action 2"],
            "confidence_score": 0.88,
        }
        res = _normalize_keys(raw_dict)
        self.assertEqual(res["narrative"], "This is a summary")
        self.assertEqual(res["key_risks"], ["Risk 1", "Risk 2"])
        self.assertEqual(res["recommendations"], ["Action 1", "Action 2"])
        self.assertEqual(res["confidence"], 0.88)

    def test_normalize_nested_root_dict(self):
        from backend.agents.single_agent import _normalize_keys
        raw_dict = {
            "analysis": {
                "narrative": "Nested narrative",
                "key_risks": ["R1"],
                "recommendations": ["Rec1"],
                "confidence": 0.75,
            }
        }
        res = _normalize_keys(raw_dict)
        self.assertEqual(res["narrative"], "Nested narrative")
        self.assertEqual(res["key_risks"], ["R1"])
        self.assertEqual(res["recommendations"], ["Rec1"])
        self.assertEqual(res["confidence"], 0.75)


    def test_compact_user_message(self):
        from backend.agents.single_agent import _build_user_message
        mock_eda = {
            "report": {"dataset": {"rows": 891, "columns": 12, "duplicate_rows": 0}},
            "quality_score": {"score": 85, "grade": "B"},
            "ml_task": {"task": "binary_classification", "target": "Survived", "confidence": 0.9},
            "missingness": {
                "columns": {
                    "Age": {"missing_count": 177, "missing_percentage": 19.87},
                    "Fare": {"missing_count": 0, "missing_percentage": 0.0},
                },
                "summary": {"overall_missing_percentage": 3.2},
            },
            "outliers": {
                "Fare": {"count": 116, "percentage": 13.0},
                "Age": {"count": 0, "percentage": 0.0},
            },
            "preprocessing": {"dummy_large": "x" * 5000},  # should be excluded
            "report_large": {"dummy_large": "y" * 5000},   # should be excluded
        }
        msg = _build_user_message(mock_eda)
        self.assertIn("Age", msg)
        self.assertIn("Survived", msg)
        # Verify that excluded/redundant fields are not in the message
        self.assertNotIn("dummy_large", msg)
        # Verify message is reasonably compact
        self.assertLess(len(msg), 3000)

    def test_fallback_response(self):
        from backend.agents.single_agent import _generate_fallback_response
        mock_eda = {
            "report": {"dataset": {"rows": 891, "columns": 12}},
            "quality_score": {"score": 80, "grade": "B"},
            "ml_task": {"task": "classification", "target": "Survived"},
            "missingness": {"columns": {"Age": {"missing_count": 177, "missing_percentage": 19.87}}},
            "outliers": {"Fare": {"count": 116}},
            "correlation_analysis": {"highly_correlated_pairs": [{"col1": "A", "col2": "B"}]},
        }
        fallback = _generate_fallback_response(mock_eda)
        self.assertTrue(len(fallback["narrative"]) > 50)
        self.assertTrue(len(fallback["key_risks"]) > 0)
        self.assertTrue(len(fallback["recommendations"]) > 0)
        self.assertEqual(fallback["confidence"], 0.8)
        self.assertTrue(fallback["_fallback_used"])


if __name__ == "__main__":
    unittest.main()


