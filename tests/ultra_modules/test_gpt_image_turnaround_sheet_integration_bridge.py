import unittest
import json
import time
from ultra_modules.gpt_image_turnaround_sheet_integration_bridge import GPTImageTurnaroundSheetIntegrationBridge, integrate_bridge

class TestGPTImageTurnaroundSheetIntegrationBridge(unittest.TestCase):

    def setUp(self):
        self.bridge = GPTImageTurnaroundSheetIntegrationBridge()

    def test_normal_v1_to_v2_forward_compatibility(self):
        # Test case 1: Normal execution (forward compatibility from v1 to v2)
        v1_payload = {
            "character_id": "char-12345",
            "char_desc": "a handsome hero",
            "art_style": "cyberpunk",
            "created_at": 1600000000 # old timestamp in seconds
        }

        result = integrate_bridge(v1_payload)

        self.assertEqual(result["id"], "char-12345")
        self.assertEqual(result["description"], "a handsome hero")
        self.assertEqual(result["style"], "cyberpunk")
        self.assertEqual(result["metadata"]["version"], "v2")
        self.assertTrue(result["metadata"]["schema_bridge_applied"])
        # Dynamic comparison against the test data payload for timestamp logic
        self.assertEqual(result["metadata"]["timestamp"], 1600000000000)

    def test_dirty_data_self_healing_json_string(self):
        # Test case 2: Dirty data self-healing (JSON string)
        dirty_json = '{"uuid": "dirty-456", "prompt": "a villian with a scar", "preset": "oil painting", "time": 1700000000000}'

        result = integrate_bridge(dirty_json)

        self.assertEqual(result["id"], "dirty-456")
        self.assertEqual(result["description"], "a villian with a scar")
        self.assertEqual(result["style"], "oil painting")
        self.assertEqual(result["metadata"]["version"], "v2")
        self.assertEqual(result["metadata"]["timestamp"], 1700000000000)

    def test_missing_parameter_defaults(self):
        # Test case 3: Missing parameter defaults (falling back to sensible defaults)
        partial_payload = {
            "char_desc": "a cute mascot"
            # Missing id, style, timestamp
        }

        result = integrate_bridge(partial_payload)

        self.assertTrue(isinstance(result["id"], str) and len(result["id"]) > 10) # default id generated
        self.assertEqual(result["description"], "a cute mascot")
        self.assertEqual(result["style"], "anime") # default style
        self.assertTrue(isinstance(result["metadata"]["timestamp"], int))
        self.assertTrue(result["metadata"]["timestamp"] > 0)

    def test_extreme_boundary_cases_empty_or_null(self):
        # Test case 4: Extreme boundary cases (e.g., empty objects, nulls)
        for boundary_val in [None, {}, "", 123, []]:
            result = integrate_bridge(boundary_val)
            self.assertTrue(isinstance(result["id"], str) and len(result["id"]) > 10)
            self.assertEqual(result["description"], "default character")
            self.assertEqual(result["style"], "anime")
            self.assertEqual(result["metadata"]["version"], "v2")
            self.assertTrue(result["metadata"]["timestamp"] > 0)

    def test_dirty_data_self_healing_raw_string(self):
        # Test case 5: Dirty data self-healing (plain string instead of dict/json)
        raw_string = "   just a random string description   "

        result = integrate_bridge(raw_string)

        self.assertTrue(isinstance(result["id"], str) and len(result["id"]) > 10)
        self.assertEqual(result["description"], "just a random string description")
        self.assertEqual(result["style"], "anime")
        self.assertEqual(result["metadata"]["version"], "v2")
        self.assertTrue(result["metadata"]["timestamp"] > 0)

if __name__ == '__main__':
    unittest.main()
