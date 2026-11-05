import unittest
import json
from ultra_modules.vertical_keyframe_compositor_plain_explainer import (
    VerticalKeyframeCompositorPlainExplainer,
    run_explainer_pipeline
)

class TestVerticalKeyframeCompositorPlainExplainer(unittest.TestCase):

    def setUp(self):
        self.explainer = VerticalKeyframeCompositorPlainExplainer()

    def test_normal_data_processing(self):
        params = {
            "lighting_effect": "赛博朋克霓虹光",
            "speed_line": "放射状高速线",
            "subtitle_style": "黄黑双层描边"
        }
        result = run_explainer_pipeline(params)

        self.assertIn("赛博朋克霓虹光", result["plain_text"])
        self.assertIn("放射状高速线", result["markdown"])
        self.assertIn("黄黑双层描边", result["html"])

        json_data = json.loads(result["json"])
        self.assertEqual(json_data["lighting_effect"], "赛博朋克霓虹光")
        self.assertEqual(json_data["speed_line"], "放射状高速线")
        self.assertEqual(json_data["subtitle_style"], "黄黑双层描边")

    def test_missing_parameter_default_fallback(self):
        # Testing with missing parameters entirely
        result = run_explainer_pipeline()

        self.assertIn("柔和自然光", result["plain_text"])
        self.assertIn("无", result["markdown"])
        self.assertIn("默认双层描边", result["html"])

        # Testing with empty dict
        result2 = run_explainer_pipeline({})
        self.assertIn("柔和自然光", result2["plain_text"])

    def test_dirty_data_self_healing(self):
        # Test with incorrect type and None values inside dict
        params = {
            "lighting_effect": None,
            "speed_line": "",
            "subtitle_style": "   "
        }
        result = run_explainer_pipeline(params)

        json_data = json.loads(result["json"])
        self.assertEqual(json_data["lighting_effect"], "柔和自然光")
        self.assertEqual(json_data["speed_line"], "无")
        self.assertEqual(json_data["subtitle_style"], "默认双层描边")

        # Test with completely wrong input type (e.g., list or string)
        result2 = run_explainer_pipeline(["not", "a", "dict"])
        self.assertIn("柔和自然光", result2["plain_text"])

    def test_extreme_boundary_conditions(self):
        # Test with extremely long strings and unexpected types
        long_string = "A" * 10000
        params = {
            "lighting_effect": long_string,
            "speed_line": 12345,  # int instead of string
            "subtitle_style": ["a", "b", "c"] # list instead of string
        }
        result = run_explainer_pipeline(params)

        json_data = json.loads(result["json"])
        self.assertEqual(json_data["lighting_effect"], long_string)
        self.assertEqual(json_data["speed_line"], "12345")
        self.assertEqual(json_data["subtitle_style"], "['a', 'b', 'c']")

    def test_string_none_healing(self):
        # Testing specific branch where string is "None"
        params = {
            "lighting_effect": "None",
            "speed_line": "None",
            "subtitle_style": "None"
        }
        result = run_explainer_pipeline(params)

        json_data = json.loads(result["json"])
        self.assertEqual(json_data["lighting_effect"], "柔和自然光")
        self.assertEqual(json_data["speed_line"], "无")
        self.assertEqual(json_data["subtitle_style"], "默认双层描边")

if __name__ == '__main__':
    unittest.main()
