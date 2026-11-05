import unittest
from ultra_modules.veo3_camera_motion_prompter_audit_trace import Veo3CameraMotionPrompter

class TestVeo3CameraMotionPrompter(unittest.TestCase):

    def setUp(self):
        self.prompter = Veo3CameraMotionPrompter()

    def test_01_normal_case(self):
        # Normal inputs with standard parameters
        raw_input = [
            {"motion": "dolly in", "speed": "fast"},
            {"motion": "pan left", "speed": "slow"}
        ]
        result = self.prompter.compile(raw_input)

        self.assertTrue(result["success"])
        self.assertIn("fast dolly in, slow pan left", result["final_prompt"])
        self.assertEqual(len(result["audit_trail"]), 4)

        # Check audit trail structure
        norm_log = result["audit_trail"][0]
        self.assertEqual(norm_log["step"], "normalize_input")
        self.assertEqual(norm_log["before"], raw_input)
        self.assertEqual(len(norm_log["after"]), 2)

    def test_02_dirty_data_self_healing(self):
        # Dirty data: typos, string input, invalid dictionary keys, unrecognized types
        raw_input = [
            "push",                   # synonym
            {"motion": "  SurRound ", "speed": " "}, # dirty caps and space, missing speed
            {"action": "zoom"},       # missing motion key entirely
            12345                     # complete invalid type inside list
        ]
        result = self.prompter.compile(raw_input)

        self.assertTrue(result["success"])
        # 'push' -> 'dolly in'
        # 'SurRound' -> 'orbit'
        # missing motion key -> 'static' -> resolved/ignored based on conflicts/logic
        self.assertIn("slow dolly in", result["final_prompt"])
        self.assertIn("slow orbit", result["final_prompt"])

        # Ensure the final prompt is built correctly
        self.assertTrue("cinematic shot, highly detailed" in result["final_prompt"])

    def test_03_missing_param_defaults(self):
        # Missing or completely None input
        result_none = self.prompter.compile(None)
        self.assertTrue(result_none["success"])
        self.assertEqual(result_none["final_prompt"], "static camera, cinematic shot, highly detailed")

        # String input without speed
        result_str = self.prompter.compile("tilt up")
        self.assertTrue(result_str["success"])
        self.assertIn("slow tilt up", result_str["final_prompt"])

    def test_04_conflict_resolution(self):
        # Conflicting motions on same axis (pan left and pan right)
        raw_input = [
            {"motion": "pan left", "speed": "fast"},
            {"motion": "pan right", "speed": "slow"}
        ]
        result = self.prompter.compile(raw_input)

        self.assertTrue(result["success"])
        # Should keep the first one (pan left) and drop the second
        self.assertIn("fast pan left", result["final_prompt"])
        self.assertNotIn("pan right", result["final_prompt"])

    def test_05_extreme_boundary_cases(self):
        # Completely invalid root input (e.g. an integer)
        result_invalid_root = self.prompter.compile(999)
        self.assertTrue(result_invalid_root["success"])
        self.assertEqual(result_invalid_root["final_prompt"], "static camera, cinematic shot, highly detailed")

        # Empty list
        result_empty_list = self.prompter.compile([])
        self.assertTrue(result_empty_list["success"])
        self.assertEqual(result_empty_list["final_prompt"], "static camera, cinematic shot, highly detailed")

        # Fuzzy match test (e.g. string that contains the valid motion but has extra garbage)
        result_fuzzy = self.prompter.compile("please do a pan left now")
        self.assertTrue(result_fuzzy["success"])
        self.assertIn("slow pan left", result_fuzzy["final_prompt"])

        # Test default static fallback via empty string or None string
        result_none_str = self.prompter.compile("none")
        self.assertTrue(result_none_str["success"])
        self.assertEqual(result_none_str["final_prompt"], "static camera, cinematic shot, highly detailed")

    def test_06_coverage_missing_lines(self):
        # Line 77: test with raw_input as a dict
        result_dict = self.prompter.compile({"motion": "pan left"})
        self.assertTrue(result_dict["success"])
        self.assertIn("slow pan left", result_dict["final_prompt"])

        # Line 124: entirely unrecognized substring where fuzzy match fails
        result_unrecognized = self.prompter.compile("xyz123abc")
        self.assertTrue(result_unrecognized["success"])
        self.assertEqual(result_unrecognized["final_prompt"], "static camera, cinematic shot, highly detailed")

if __name__ == '__main__':
    unittest.main()
