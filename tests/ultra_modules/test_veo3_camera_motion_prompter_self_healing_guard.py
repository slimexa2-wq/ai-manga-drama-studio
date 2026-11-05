import unittest
import time
from ultra_modules.veo3_camera_motion_prompter_self_healing_guard import (
    Veo3CameraMotionPrompter,
    heal_motion_params,
    build_veo3_sora2_prompt
)

class TestVeo3CameraMotionPrompter(unittest.TestCase):
    def setUp(self):
        self.prompter = Veo3CameraMotionPrompter()

    def test_normal_input(self):
        """Test with valid and complete input."""
        raw_input = {
            "action": "push",
            "speed": "cinematic",
            "direction": "",
            "strength": 8.5,
            "target": "the hero"
        }
        result = self.prompter.compile(raw_input)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["healed_params"]["action"], "push")
        self.assertEqual(result["healed_params"]["speed"], "cinematic")
        self.assertEqual(result["healed_params"]["strength"], 8.5)
        self.assertEqual(result["healed_params"]["target"], "the hero")
        self.assertIn("pushing in towards the hero", result["prompt"])
        self.assertIn("intensity 8.5/10.0", result["prompt"])

    def test_dirty_data_self_healing(self):
        """Test self-healing mechanism for dirty data types."""
        raw_input = {
            "action": ["not", "a", "string"],  # should fallback to "static"
            "speed": 123,                      # should fallback to "medium"
            "strength": "invalid_float",       # should fallback to 5.0
            "target": None                     # should fallback to "center subject"
        }
        result = self.prompter.compile(raw_input)

        self.assertEqual(result["healed_params"]["action"], "static")
        self.assertEqual(result["healed_params"]["speed"], "medium")
        self.assertEqual(result["healed_params"]["strength"], 5.0)
        self.assertEqual(result["healed_params"]["target"], "center subject")

        self.assertIn("static shot focusing on center subject", result["prompt"])
        self.assertIn("medium camera motion", result["prompt"])

    def test_missing_params_fallback(self):
        """Test fallback when passing empty or missing parameters."""
        raw_input = None # Not a dict
        result = self.prompter.compile(raw_input)

        self.assertEqual(result["healed_params"]["action"], "static")
        self.assertEqual(result["healed_params"]["speed"], "medium")
        self.assertEqual(result["healed_params"]["strength"], 5.0)

        # Action dependent defaults
        raw_input_pan = {"action": "pan"}
        res_pan = self.prompter.compile(raw_input_pan)
        self.assertEqual(res_pan["healed_params"]["direction"], "right")

        raw_input_orbit = {"action": "orbit"}
        res_orbit = self.prompter.compile(raw_input_orbit)
        self.assertEqual(res_orbit["healed_params"]["direction"], "clockwise")

    def test_extreme_boundaries(self):
        """Test boundary conditions for values like strength limits and string sanitization."""
        raw_input = {
            "action": " PULL ",            # Spaced and uppercase
            "strength": -999.0,            # Should clip to 1.0
            "target": "evil@#$%villain!!!" # Should sanitize special characters
        }
        result = self.prompter.compile(raw_input)

        self.assertEqual(result["healed_params"]["action"], "pull")
        self.assertEqual(result["healed_params"]["strength"], 1.0)
        # Assuming our sanitization allows \w \s \- , .
        self.assertEqual(result["healed_params"]["target"], "evilvillain")
        self.assertIn("intensity 1.0/10.0", result["prompt"])

        raw_input_high_strength = {"strength": 9999.0}
        res2 = self.prompter.compile(raw_input_high_strength)
        self.assertEqual(res2["healed_params"]["strength"], 10.0)

    def test_snapshot_undo_mechanism(self):
        """Test the 5-second 1-click snapshot undo functionality."""
        base_time = time.time()

        raw_input_1 = {"action": "pan", "target": "apple"}
        self.prompter.compile(raw_input_1, current_time=base_time)

        # Valid undo within 5 seconds
        undo_res = self.prompter.undo(current_time=base_time + 2.0)
        self.assertEqual(undo_res, raw_input_1)

        # Re-compile
        self.prompter.compile(raw_input_1, current_time=base_time)

        # Invalid undo past 5 seconds
        undo_res_late = self.prompter.undo(current_time=base_time + 6.0)
        self.assertIsNone(undo_res_late)

        # Empty snapshot check
        self.prompter._snapshots = []
        self.assertIsNone(self.prompter.undo(current_time=base_time))

if __name__ == '__main__':
    unittest.main()
