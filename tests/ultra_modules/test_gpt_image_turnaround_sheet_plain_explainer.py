import unittest
import json
from ultra_modules.gpt_image_turnaround_sheet_plain_explainer import generate_plain_explainer

class TestGPTImageTurnaroundSheetPlainExplainer(unittest.TestCase):
    def test_normal_execution(self):
        """Test with normal, expected data."""
        backend_result = {
            "prompt": "Create a character design turnaround sheet...\n--ar 16:9 --niji 6",
            "config": {
                "character_desc": "A cute magical girl with pink hair.",
                "style": "watercolor, studio ghibli",
                "include_expressions": True,
                "aspect_ratio": "16:9"
            }
        }

        md_result = generate_plain_explainer(backend_result, format="markdown")
        self.assertIn("A cute magical girl with pink hair.", md_result)
        self.assertIn("watercolor, studio ghibli", md_result)
        self.assertIn("16:9", md_result)
        self.assertIn("包含3-4种不同表情", md_result)
        self.assertIn("--ar 16:9 --niji 6", md_result)

        html_result = generate_plain_explainer(backend_result, format="html")
        self.assertIn("<div class=\"turnaround-explainer\">", html_result)
        self.assertIn("A cute magical girl with pink hair.", html_result)

        json_result = generate_plain_explainer(backend_result, format="json")
        json_obj = json.loads(json_result)
        self.assertEqual(json_obj["core_settings"]["character_desc"], "A cute magical girl with pink hair.")

    def test_missing_parameters_fallback(self):
        """Test with empty/missing data to trigger fallbacks."""
        backend_result = {}

        md_result = generate_plain_explainer(backend_result, format="markdown")
        self.assertIn("未指定角色设定", md_result)
        self.assertIn("未指定风格", md_result)
        self.assertIn("未指定比例", md_result)
        self.assertIn("包含3-4种不同表情", md_result) # default is True
        self.assertIn("（未生成提示词）", md_result)

    def test_dirty_data_self_healing(self):
        """Test with dirty data like wrong types."""
        backend_result = {
            "prompt": 12345, # Should be string
            "config": {
                "character_desc": {"wrong": "type"}, # Should be string
                "style": ["also wrong"], # Should be string
                "include_expressions": "not a boolean", # Should be bool
                "aspect_ratio": None # Should be string
            }
        }

        md_result = generate_plain_explainer(backend_result, format="markdown")
        self.assertIn("{'wrong': 'type'}", md_result)
        self.assertIn("['also wrong']", md_result)
        self.assertIn("未指定比例", md_result)
        self.assertIn("包含3-4种不同表情", md_result) # Fallbacks to True when not bool
        self.assertIn("12345", md_result)

        # Another case of dirty data: the result itself is not a dict or valid JSON
        bad_result = generate_plain_explainer(True, format="INVALID_FORMAT")
        self.assertIn("未指定角色设定", bad_result)

    def test_boundary_conditions(self):
        """Test boundary conditions like extremely long strings or false boolean."""
        backend_result = {
            "prompt": "A" * 10000,
            "config": {
                "character_desc": "B" * 5000,
                "style": "C" * 1000,
                "include_expressions": False,
                "aspect_ratio": "1:1"
            }
        }

        md_result = generate_plain_explainer(backend_result, format="markdown")
        self.assertIn("B" * 5000, md_result)
        self.assertIn("本次未包含特殊面部表情。", md_result)
        self.assertIn("否", md_result)
        self.assertIn("1:1", md_result)

    def test_json_string_parsing(self):
        """Test passing a JSON string instead of a dict."""
        json_str = json.dumps({
            "prompt": "Generated prompt",
            "config": {
                "character_desc": "JSON parsed character",
                "style": "JSON parsed style",
                "include_expressions": True,
                "aspect_ratio": "9:16"
            }
        })

        md_result = generate_plain_explainer(json_str, format="markdown")
        self.assertIn("JSON parsed character", md_result)
        self.assertIn("9:16", md_result)

        # Test invalid JSON string
        invalid_json_str = "This is not valid JSON { "
        md_result_invalid = generate_plain_explainer(invalid_json_str, format="markdown")
        self.assertIn("未指定角色设定", md_result_invalid)

if __name__ == '__main__':
    unittest.main()
