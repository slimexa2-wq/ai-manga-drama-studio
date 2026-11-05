import unittest
import time
from unittest.mock import patch
from ultra_modules.gpt_image_turnaround_sheet_self_healing_guard import GPTImageTurnaroundSheetSelfHealingGuard

class TestGPTImageTurnaroundSheetSelfHealingGuard(unittest.TestCase):
    def setUp(self):
        self.guard = GPTImageTurnaroundSheetSelfHealingGuard()

    def test_01_normal_execution(self):
        """Test normal execution with valid string inputs."""
        res = self.guard.generate(
            character_desc="A cute cat girl",
            style="cyberpunk",
            include_expressions=False,
            aspect_ratio="1:1"
        )
        self.assertIn("Character Description: A cute cat girl", res["prompt"])
        self.assertIn("Style: cyberpunk", res["prompt"])
        self.assertNotIn("facial expressions", res["prompt"])
        self.assertIn("--ar 1:1", res["prompt"])
        self.assertEqual(res["config"]["character_desc"], "A cute cat girl")
        self.assertEqual(res["config"]["style"], "cyberpunk")
        self.assertFalse(res["config"]["include_expressions"])
        self.assertEqual(res["config"]["aspect_ratio"], "1:1")

    def test_02_missing_parameter_fallback(self):
        """Test fallback defaults when no arguments are provided."""
        res = self.guard.generate()
        self.assertIn("A handsome anime protagonist", res["prompt"])
        self.assertIn("high quality anime style", res["prompt"])
        self.assertIn("facial expressions", res["prompt"])
        self.assertIn("--ar 16:9", res["prompt"])
        self.assertEqual(res["config"]["character_desc"], "A handsome anime protagonist with a mysterious aura, wearing a dark cloak.")
        self.assertEqual(res["config"]["style"], "high quality anime style, masterpiece, best quality, ultra-detailed")
        self.assertTrue(res["config"]["include_expressions"])
        self.assertEqual(res["config"]["aspect_ratio"], "16:9")

    def test_03_dirty_data_self_healing(self):
        """Test handling of invalid types and malformed data."""
        res = self.guard.generate(
            character_desc={"name": "hero"},
            style=["cool", "dark"],
            include_expressions=" false ",
            aspect_ratio="16x9"
        )
        self.assertIn('{"name": "hero"}', res["config"]["character_desc"])
        self.assertIn("['cool', 'dark']", res["config"]["style"])
        self.assertFalse(res["config"]["include_expressions"])
        self.assertEqual(res["config"]["aspect_ratio"], "16:9")

    def test_04_extreme_boundary_cases(self):
        """Test extreme boundary cases like None, empty strings, and integer texts."""
        res = self.guard.generate(
            character_desc=None,
            style="",
            include_expressions=0,
            aspect_ratio="   "
        )
        self.assertEqual(res["config"]["character_desc"], "A handsome anime protagonist with a mysterious aura, wearing a dark cloak.")
        self.assertEqual(res["config"]["style"], "high quality anime style, masterpiece, best quality, ultra-detailed")
        self.assertFalse(res["config"]["include_expressions"])
        self.assertEqual(res["config"]["aspect_ratio"], "16:9")

        res2 = self.guard.generate(
            character_desc=12345,
            style=987,
            include_expressions="T",
            aspect_ratio="21-9"
        )
        self.assertEqual(res2["config"]["character_desc"], "12345")
        self.assertEqual(res2["config"]["style"], "987")
        self.assertTrue(res2["config"]["include_expressions"])
        self.assertEqual(res2["config"]["aspect_ratio"], "21:9")

    def test_05_undo_snapshot_mechanism(self):
        """Test the 5-second undo snapshot mechanism."""
        # First generation
        res1 = self.guard.generate(character_desc="Gen 1")
        self.assertEqual(res1["config"]["character_desc"], "Gen 1")

        # Second generation
        res2 = self.guard.generate(character_desc="Gen 2")
        self.assertEqual(res2["config"]["character_desc"], "Gen 2")

        # Undo within window (mock time to be immediate)
        with patch('time.time', return_value=time.time()):
            undone_res = self.guard.undo()
            self.assertIsNotNone(undone_res)
            self.assertEqual(undone_res["config"]["character_desc"], "Gen 1")

        # Third generation
        res3 = self.guard.generate(character_desc="Gen 3")
        self.assertEqual(res3["config"]["character_desc"], "Gen 3")

        # Undo outside window (mock time to be 6 seconds later)
        last_timestamp = self.guard._snapshot_history[-1]["timestamp"]
        with patch('time.time', return_value=last_timestamp + 6.0):
            undone_res_expired = self.guard.undo()
            self.assertIsNone(undone_res_expired)
            self.assertEqual(self.guard.get_current_state()["config"]["character_desc"], "Gen 3")

    def test_06_snapshot_limit(self):
        """Test that snapshot history doesn't exceed the limit of 10."""
        for i in range(15):
            self.guard.generate(character_desc=f"Gen {i}")
        self.assertEqual(len(self.guard._snapshot_history), 10)

    def test_07_undo_empty_history(self):
        """Test undo when history is empty."""
        undone_res = self.guard.undo()
        self.assertIsNone(undone_res)

if __name__ == '__main__':
    unittest.main()
