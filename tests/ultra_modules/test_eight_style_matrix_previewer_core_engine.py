import unittest
from ultra_modules.eight_style_matrix_previewer_core_engine import generate_style_matrix

class TestEightStyleMatrixPreviewerCoreEngine(unittest.TestCase):

    def test_normal_case(self):
        """Test with valid normal inputs."""
        prompt = "主角发现了一个秘密基地"
        styles = ["修仙", "赛博朋克"]
        config = {"resolution": "1920x1080", "aspect_ratio": "16:9"}

        result = generate_style_matrix(prompt, styles, config)

        self.assertEqual(result["base_prompt"], prompt)
        self.assertEqual(result["config"]["resolution"], "1920x1080")
        self.assertEqual(result["config"]["aspect_ratio"], "16:9")
        self.assertEqual(len(result["previews"]), 2)
        self.assertEqual(result["previews"][0]["style"], "修仙")
        self.assertEqual(result["previews"][0]["combined_prompt"], f"[修仙风格] {prompt}")

    def test_missing_params(self):
        """Test with missing or None parameters to ensure default fallbacks work."""
        result = generate_style_matrix()

        self.assertEqual(result["base_prompt"], "默认场景：主角站在城市废墟中，眼神坚定")
        self.assertEqual(result["config"]["resolution"], "1024x1024")
        self.assertEqual(result["config"]["aspect_ratio"], "1:1")

        self.assertEqual(len(result["previews"]), 8)
        self.assertEqual(result["previews"][0]["style"], "修仙")
        self.assertEqual(result["previews"][1]["style"], "都市逆袭")

    def test_dirty_data_cleaning(self):
        """Test with unexpected types or empty values."""
        # Non-string prompt, invalid list items in styles, malformed config
        result = generate_style_matrix(
            prompt=12345,
            styles=[123, "", None, "废土生存"],
            config="invalid_config"
        )

        self.assertEqual(result["base_prompt"], "默认场景：主角站在城市废墟中，眼神坚定")
        self.assertEqual(result["config"]["resolution"], "1024x1024")
        self.assertEqual(len(result["previews"]), 1)
        self.assertEqual(result["previews"][0]["style"], "废土生存")

        # Test empty string resolution and aspect ratio
        result2 = generate_style_matrix(
            config={"resolution": "   ", "aspect_ratio": None}
        )
        self.assertEqual(result2["config"]["resolution"], "1024x1024")
        self.assertEqual(result2["config"]["aspect_ratio"], "1:1")

    def test_extreme_boundaries(self):
        """Test with very large or unexpected input values (boundary conditions)."""
        very_long_prompt = "A" * 10000
        very_long_styles = [f"style_{i}" for i in range(100)]

        result = generate_style_matrix(
            prompt=very_long_prompt,
            styles=very_long_styles
        )

        self.assertEqual(result["base_prompt"], very_long_prompt)
        # Ensure it caps at 8 styles
        self.assertEqual(len(result["previews"]), 8)
        self.assertEqual(result["previews"][0]["style"], "style_0")
        self.assertEqual(result["previews"][7]["style"], "style_7")

    def test_custom_config_override(self):
        """Test partial configurations."""
        result = generate_style_matrix(
            config={"resolution": "800x600"} # aspect_ratio missing
        )

        self.assertEqual(result["config"]["resolution"], "800x600")
        self.assertEqual(result["config"]["aspect_ratio"], "1:1")

if __name__ == "__main__":
    unittest.main()
