import unittest
from ultra_modules.climax_pacing_analyzer_plain_explainer import (
    ClimaxPacingAnalyzerPlainExplainer,
    generate_plain_explanation
)

class TestClimaxPacingAnalyzerPlainExplainer(unittest.TestCase):
    def setUp(self):
        self.explainer = ClimaxPacingAnalyzerPlainExplainer()

    def test_normal_ideal_curve(self):
        """Test with an ideal pacing curve data structure."""
        ideal_data = {
            "analysis": {
                "has_curve": True,
                "overall_rating": "Excellent",
                "scores": {
                    "suppression": 3,
                    "buildup": 2,
                    "payoff": 4,
                    "suspense": 1
                }
            }
        }
        result = generate_plain_explanation(ideal_data)

        # Check basic output structure
        self.assertIn("markdown", result)
        self.assertIn("html", result)
        self.assertIn("json", result)

        markdown = result["markdown"]
        self.assertIn("整体节奏很好", markdown)
        self.assertIn("前期有 3 处压抑情节", markdown)
        self.assertIn("中间有 2 处蓄力情节", markdown)
        self.assertIn("高潮有 4 处爆发打脸", markdown)
        self.assertIn("结尾留了 1 处悬念", markdown)

        self.assertTrue(result["json"]["is_good"])
        self.assertEqual(result["json"]["rating"], "Excellent")

    def test_normal_poor_curve(self):
        """Test with a poor pacing curve."""
        poor_data = {
            "has_curve": False,
            "overall_rating": "Needs Improvement",
            "scores": {
                "suppression": 0,
                "buildup": 0,
                "payoff": 0,
                "suspense": 0
            }
        }
        # Testing when the 'analysis' key is missing but the structure is passed directly
        result = generate_plain_explanation(poor_data)

        markdown = result["markdown"]
        self.assertIn("节奏有些平缓", markdown)
        self.assertIn("前期缺乏压抑", markdown)
        self.assertNotIn("蓄力情节", markdown) # Buildup only shows if > 0
        self.assertIn("缺少爆发打脸情节", markdown)
        self.assertIn("结尾没有明显悬念", markdown)

        self.assertFalse(result["json"]["is_good"])

    def test_dirty_data_self_healing(self):
        """Test with completely broken or dirty data (int, string, None)."""
        dirty_inputs = [None, "some string", 12345, []]

        for dirty in dirty_inputs:
            result = generate_plain_explanation(dirty)
            self.assertIn("markdown", result)
            self.assertIn("html", result)
            self.assertFalse(result["json"]["is_good"])
            self.assertEqual(result["json"]["rating"], "Unknown")
            self.assertIn("节奏有些平缓", result["markdown"])

    def test_missing_params_defaults(self):
        """Test with missing keys inside the analysis dictionary."""
        missing_data = {
            "analysis": {
                "scores": {
                    "suppression": 5
                    # Missing buildup, payoff, suspense
                }
                # Missing has_curve, overall_rating
            }
        }
        result = generate_plain_explanation(missing_data)
        self.assertFalse(result["json"]["is_good"]) # Defaults to False
        self.assertEqual(result["json"]["rating"], "Needs Improvement") # Default rating
        self.assertIn("前期有 5 处压抑情节", result["markdown"])
        self.assertIn("缺少爆发打脸情节", result["markdown"])

    def test_extreme_boundary_cases(self):
        """Test with weird data types within the nested dictionary."""
        extreme_data = {
            "analysis": {
                "has_curve": "Not a bool, but truthy",
                "overall_rating": None,
                "scores": {
                    "suppression": "invalid_int", # Should fall back to 0
                    "buildup": None,              # Should fall back to 0
                    "payoff": 3.14,               # Should be cast to int 3
                    "suspense": [1, 2, 3]         # Invalid type for int casting, fallback to 0
                }
            }
        }
        result = generate_plain_explanation(extreme_data)

        # 'has_curve' should be cast to True
        self.assertTrue(result["json"]["is_good"])

        markdown = result["markdown"]
        # suppression fell back to 0
        self.assertIn("前期缺乏压抑", markdown)

        # payoff cast to int 3
        self.assertIn("高潮有 3 处爆发打脸", markdown)

        # suspense fell back to 0
        self.assertIn("结尾没有明显悬念", markdown)

if __name__ == '__main__':
    unittest.main()
