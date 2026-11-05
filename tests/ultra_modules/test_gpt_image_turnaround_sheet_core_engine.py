import unittest
from ultra_modules.gpt_image_turnaround_sheet_core_engine import build_gpt_image_turnaround_prompt

class TestGPTImageTurnaroundSheetCoreEngine(unittest.TestCase):

    def test_normal_generation(self):
        """Test with all valid standard inputs."""
        res = build_gpt_image_turnaround_prompt(
            character_desc="A warrior princess with a glowing sword.",
            style="cyberpunk, neon lighting",
            include_expressions=False,
            aspect_ratio="1:1"
        )
        conf = res["config"]
        self.assertEqual(conf["character_desc"], "A warrior princess with a glowing sword.")
        self.assertEqual(conf["style"], "cyberpunk, neon lighting")
        self.assertFalse(conf["include_expressions"])
        self.assertEqual(conf["aspect_ratio"], "1:1")

        prompt = res["prompt"]
        self.assertIn("A warrior princess with a glowing sword.", prompt)
        self.assertIn("cyberpunk, neon lighting", prompt)
        self.assertIn("--ar 1:1", prompt)
        self.assertNotIn("facial expressions", prompt)

    def test_missing_parameters_fallback(self):
        """Test that missing kwargs default to sensible values."""
        res = build_gpt_image_turnaround_prompt()
        conf = res["config"]

        self.assertTrue(conf["character_desc"])
        self.assertTrue(conf["style"])
        self.assertTrue(conf["include_expressions"])
        self.assertEqual(conf["aspect_ratio"], "16:9")

        prompt = res["prompt"]
        self.assertIn(conf["character_desc"], prompt)
        self.assertIn("facial expressions", prompt)

    def test_dirty_data_cleaning(self):
        """Test with incorrect types like dicts and integers."""
        res = build_gpt_image_turnaround_prompt(
            character_desc={"name": "Alice", "role": "mage"},
            style=12345,
            include_expressions=1,
            aspect_ratio=None
        )
        conf = res["config"]
        self.assertEqual(conf["character_desc"], '{"name": "Alice", "role": "mage"}')
        self.assertEqual(conf["style"], "12345")
        self.assertTrue(conf["include_expressions"])
        self.assertEqual(conf["aspect_ratio"], "16:9")

    def test_extreme_boundaries(self):
        """Test with empty strings, whitespace, and malformed aspect ratios."""
        res = build_gpt_image_turnaround_prompt(
            character_desc="   ",
            style="",
            include_expressions="",
            aspect_ratio=" 16 x 9 "
        )
        conf = res["config"]
        # Empty space should trigger default character and style
        self.assertTrue(len(conf["character_desc"]) > 5)
        self.assertNotEqual(conf["character_desc"], "   ")
        self.assertTrue(len(conf["style"]) > 5)

        # Empty string expression flag should mean False based on our rules
        self.assertFalse(conf["include_expressions"])

        # 16 x 9 should be cleaned to 16:9
        self.assertEqual(conf["aspect_ratio"], "16:9")

        # Another invalid AR test
        res2 = build_gpt_image_turnaround_prompt(aspect_ratio="invalid_ar")
        self.assertEqual(res2["config"]["aspect_ratio"], "16:9")

    def test_expressions_toggle(self):
        """Test various string inputs for the boolean expressions toggle."""
        self.assertFalse(build_gpt_image_turnaround_prompt(include_expressions="false")["config"]["include_expressions"])
        self.assertFalse(build_gpt_image_turnaround_prompt(include_expressions=" 0 ")["config"]["include_expressions"])
        self.assertFalse(build_gpt_image_turnaround_prompt(include_expressions="No")["config"]["include_expressions"])
        self.assertFalse(build_gpt_image_turnaround_prompt(include_expressions="F")["config"]["include_expressions"])
        self.assertFalse(build_gpt_image_turnaround_prompt(include_expressions="n")["config"]["include_expressions"])

        self.assertTrue(build_gpt_image_turnaround_prompt(include_expressions="true")["config"]["include_expressions"])
        self.assertTrue(build_gpt_image_turnaround_prompt(include_expressions="yes")["config"]["include_expressions"])
        self.assertTrue(build_gpt_image_turnaround_prompt(include_expressions="1")["config"]["include_expressions"])

if __name__ == '__main__':
    unittest.main()
