import unittest
from ultra_modules.eight_style_matrix_previewer_integration_bridge import bridge_schema

class TestEightStyleMatrixPreviewerIntegrationBridge(unittest.TestCase):
    def test_normal_valid_input(self):
        """Test with modern schema normal input."""
        input_data = {
            "prompt": "主角在森林中探险",
            "styles": ["修仙", "废土生存"],
            "config": {
                "resolution": "1920x1080",
                "aspect_ratio": "16:9"
            }
        }
        result = bridge_schema(input_data)
        self.assertEqual(result["prompt"], "主角在森林中探险")
        self.assertEqual(result["styles"], ["修仙", "废土生存"])
        self.assertEqual(result["config"]["resolution"], "1920x1080")
        self.assertEqual(result["config"]["aspect_ratio"], "16:9")

    def test_legacy_dirty_fields(self):
        """Test with legacy fields and flat structures."""
        input_data = {
            "text": " 一只小猫 ", # legacy prompt, with spaces
            "tags": "赛博朋克, 黑暗奇幻, 赛博朋克", # legacy styles, comma separated, with duplicate
            "width": 800,
            "height": 600,
            "ratio": "4:3"
        }
        result = bridge_schema(input_data)
        self.assertEqual(result["prompt"], "一只小猫")
        self.assertEqual(result["styles"], ["赛博朋克", "黑暗奇幻"]) # duplicate removed, order preserved
        self.assertEqual(result["config"]["resolution"], "800x600")
        self.assertEqual(result["config"]["aspect_ratio"], "4:3")

    def test_dirty_data_self_healing(self):
        """Test with non-dictionary input and invalid list items."""
        # Non-dictionary input should self-heal to defaults
        result_str = bridge_schema("this is completely invalid")
        self.assertEqual(result_str["prompt"], "默认场景：主角站在城市废墟中，眼神坚定")
        self.assertEqual(len(result_str["styles"]), 8)
        self.assertEqual(result_str["config"]["resolution"], "1024x1024")
        self.assertEqual(result_str["config"]["aspect_ratio"], "1:1")

        # Invalid items in list
        input_data = {
            "prompt": "Test",
            "style_list": ["修仙", None, 123, "", "  ", "热血少年"]
        }
        result_list = bridge_schema(input_data)
        self.assertEqual(result_list["styles"], ["修仙", "123", "热血少年"]) # non-strings converted to string, empty ignored

    def test_missing_parameters_default_fallback(self):
        """Test empty input falls back to all defaults."""
        result = bridge_schema({})
        self.assertEqual(result["prompt"], "默认场景：主角站在城市废墟中，眼神坚定")
        self.assertEqual(result["styles"], [
            "修仙", "都市逆袭", "韩漫财阀", "热血少年",
            "中式规则怪谈", "赛博朋克", "废土生存", "黑暗奇幻"
        ])
        self.assertEqual(result["config"]["resolution"], "1024x1024")
        self.assertEqual(result["config"]["aspect_ratio"], "1:1")

    def test_extreme_boundary_conditions(self):
        """Test style lists exceeding 8 items and completely malformed config."""
        input_data = {
            "content": " Boundary check ",
            "styles": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10"],
            "config": "this is not a dictionary",
            "resolution": ["invalid type for resolution"],
            "aspect_ratio": {"invalid": "type"}
        }
        result = bridge_schema(input_data)
        self.assertEqual(result["prompt"], "Boundary check")
        self.assertEqual(result["styles"], ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]) # capped at 8
        self.assertEqual(result["config"]["resolution"], "1024x1024") # invalid flat fell back to default
        self.assertEqual(result["config"]["aspect_ratio"], "1:1") # invalid flat fell back to default

if __name__ == '__main__':
    unittest.main()
