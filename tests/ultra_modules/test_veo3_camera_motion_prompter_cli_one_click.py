import unittest
import json
import csv
import io
from ultra_modules.veo3_camera_motion_prompter_cli_one_click import (
    generate_motion_prompt,
    format_output_json,
    format_output_excel,
    cli_entrypoint
)

class TestVeo3CameraMotionPrompter(unittest.TestCase):

    def test_01_normal_data(self):
        """Test normal data input for generate_motion_prompt."""
        movements = ["pan left", "tilt up"]
        subjects = ["a running dog", "a flying bird"]
        env = "a sunny park"

        # Test generation with seed for deterministic output
        result = generate_motion_prompt(camera_movements=movements, subjects=subjects, environment=env, seed=42)

        self.assertIn(result["movement"], movements)
        self.assertIn(result["subject"], subjects)
        self.assertEqual(result["environment"], env)
        self.assertIn("Cinematic", result["prompt"])
        self.assertIn("sunny park", result["prompt"])
        self.assertEqual(result["model_target"], "Veo 3 / Sora 2")

    def test_02_dirty_data_self_healing(self):
        """Test dirty data self-healing, e.g., None elements, empty strings, wrong types."""
        # Intentionally wrong types (not list, but strings)
        movements = "   zoom in   "
        subjects = "   a sad cat   "
        env = "   rainy street   "

        result = generate_motion_prompt(camera_movements=movements, subjects=subjects, environment=env, seed=42)

        self.assertEqual(result["movement"], "zoom in")
        self.assertEqual(result["subject"], "a sad cat")
        self.assertEqual(result["environment"], "rainy street")

        # Test lists with None and empty strings
        movements_list = [None, "", "   ", "crane shot"]
        subjects_list = [None, "", "happy dog"]

        result2 = generate_motion_prompt(camera_movements=movements_list, subjects=subjects_list, environment=None, seed=42)
        self.assertEqual(result2["movement"], "crane shot")
        self.assertEqual(result2["subject"], "happy dog")
        self.assertEqual(result2["environment"], "a foggy futuristic cityscape at dusk") # default env

    def test_03_default_fallback_and_missing_params(self):
        """Test that missing parameters or completely empty valid inputs fallback to reasonable defaults."""
        result = generate_motion_prompt(seed=42)

        default_movements = ["slow push in", "dynamic crane shot", "fast pan right", "orbit around"]
        default_subjects = ["a lone wanderer", "a glowing artifact", "two people conversing"]

        self.assertIn(result["movement"], default_movements)
        self.assertIn(result["subject"], default_subjects)
        self.assertEqual(result["environment"], "a foggy futuristic cityscape at dusk")

        # Empty lists fallback
        result_empty = generate_motion_prompt(camera_movements=[], subjects=[], environment="", seed=42)
        self.assertIn(result_empty["movement"], default_movements)
        self.assertIn(result_empty["subject"], default_subjects)
        self.assertEqual(result_empty["environment"], "a foggy futuristic cityscape at dusk")

    def test_04_extreme_edge_cases(self):
        """Test extreme edge cases like lists of spaces, integers instead of strings."""
        result = generate_motion_prompt(camera_movements=[123, 456], subjects=[True, False], environment=999, seed=1)

        self.assertIn(result["movement"], ["123", "456"])
        self.assertIn(result["subject"], ["True", "False"])
        self.assertEqual(result["environment"], "999")

        result_spaces = generate_motion_prompt(camera_movements=["  ", " \t "], subjects=["\n"], environment="  ")
        # Should fallback to defaults because after strip they are empty
        default_movements = ["slow push in", "dynamic crane shot", "fast pan right", "orbit around"]
        default_subjects = ["a lone wanderer", "a glowing artifact", "two people conversing"]

        self.assertIn(result_spaces["movement"], default_movements)
        self.assertIn(result_spaces["subject"], default_subjects)
        self.assertEqual(result_spaces["environment"], "a foggy futuristic cityscape at dusk")

    def test_05_cli_entrypoint_and_output_formats(self):
        """Test the cli_entrypoint wrapper and the formatting tools."""
        # Test JSON format
        json_output = cli_entrypoint(output_format="json", seed=42)
        parsed_json = json.loads(json_output)
        self.assertEqual(parsed_json["model_target"], "Veo 3 / Sora 2")

        # Test Excel/CSV format
        excel_output = cli_entrypoint(output_format="excel", seed=42)
        reader = csv.DictReader(io.StringIO(excel_output))
        rows = list(reader)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["model_target"], "Veo 3 / Sora 2")

        # Test dirty format inputs (fallback to json)
        bad_format_output = cli_entrypoint(output_format="xml", seed=42)
        parsed_bad = json.loads(bad_format_output)
        self.assertEqual(parsed_bad["model_target"], "Veo 3 / Sora 2")

        bad_format_output_2 = cli_entrypoint(output_format=None, seed=42)
        parsed_bad_2 = json.loads(bad_format_output_2)
        self.assertEqual(parsed_bad_2["model_target"], "Veo 3 / Sora 2")

if __name__ == "__main__":
    unittest.main()
