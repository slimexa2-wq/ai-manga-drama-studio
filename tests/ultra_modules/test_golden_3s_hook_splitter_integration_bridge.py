import unittest
import json
from ultra_modules.golden_3s_hook_splitter_integration_bridge import Golden3sHookSplitterIntegrationBridge

class TestGolden3sHookSplitterIntegrationBridge(unittest.TestCase):

    def setUp(self):
        self.bridge = Golden3sHookSplitterIntegrationBridge()

        # A simple novel text with multiple paragraphs to test splitting.
        self.sample_novel_text = (
            "第一章 魔帝归来。他冷笑一声，眼中满是杀机。\n\n"
            "周围的人都在瑟瑟发抖。没有人敢直视他的眼睛。\n\n"
            "就在这时，天空中突然降下一道惊雷！\n\n"
            "到底是谁，敢在此时挑战魔帝的威严？"
        )

        # A massive text (extreme boundary condition)
        self.massive_text = "这是一段非常长的有换行的文字。\n" * 1000

    def test_normal_case_expected_schema(self):
        """Test with expected standard schema (text and target_duration_sec)."""
        payload = {
            "text": self.sample_novel_text,
            "target_duration_sec": 75
        }
        result = self.bridge.process_payload(payload)

        self.assertTrue(result["success"])
        self.assertGreater(len(result["episodes"]), 0)
        self.assertEqual(result["original_duration_target"], 75)

        # Verify the episode structure
        episode = result["episodes"][0]
        self.assertIn("text", episode)
        self.assertIn("golden_3s_hook", episode)
        self.assertIn("cliffhanger", episode)
        self.assertIn("satisfying_beats", episode)

    def test_normal_case_alternative_schema(self):
        """Test with an alternative schema that should be dynamically mapped."""
        payload = {
            "novel_text": self.sample_novel_text,
            "episode_length": 60
        }
        result = self.bridge.process_payload(payload)

        self.assertTrue(result["success"])
        self.assertGreater(len(result["episodes"]), 0)
        self.assertEqual(result["original_duration_target"], 60)

    def test_dirty_data_self_healing_json_string(self):
        """Test handling of a JSON string payload instead of a dictionary."""
        payload_dict = {
            "content": self.sample_novel_text,
            "duration": 50
        }
        payload_str = json.dumps(payload_dict)

        result = self.bridge.process_payload(payload_str)
        self.assertTrue(result["success"])
        self.assertEqual(result["original_duration_target"], 50)

    def test_dirty_data_self_healing_primitives(self):
        """Test handling of extreme primitive inputs (integer)."""
        # Sending just a number as payload should convert it to text.
        result = self.bridge.process_payload(12345)

        self.assertTrue(result["success"])
        # A short text will likely be put into a single episode.
        self.assertEqual(result["episodes"][0]["text"], "12345")

    def test_missing_parameter_fallback(self):
        """Test missing duration parameter or completely empty dictionaries/None."""
        # 1. Missing duration, only text
        payload_no_duration = {"manuscript": self.sample_novel_text}
        result1 = self.bridge.process_payload(payload_no_duration)
        self.assertTrue(result1["success"])
        self.assertEqual(result1["original_duration_target"], 75) # Default

        # 2. Empty dict
        result2 = self.bridge.process_payload({})
        self.assertFalse(result2["success"])
        self.assertEqual(result2["error"], "No valid text content found in payload.")

        # 3. None
        result3 = self.bridge.process_payload(None)
        self.assertFalse(result3["success"])
        self.assertEqual(result3["error"], "No valid text content found in payload.")

    def test_extreme_boundary_conditions(self):
        """Test massive string without spaces/newlines and whitespace-only text."""
        # 1. Massive string
        payload_massive = {"story": self.massive_text, "target_duration_sec": 30}
        result1 = self.bridge.process_payload(payload_massive)
        self.assertTrue(result1["success"])
        # Should be split into multiple episodes because it exceeds 30 sec targeting
        self.assertGreater(len(result1["episodes"]), 1)

        # 2. Whitespace-only string
        payload_empty = {"text": "   \n\t   "}
        result2 = self.bridge.process_payload(payload_empty)
        self.assertFalse(result2["success"])
        self.assertEqual(result2["error"], "Empty text content after stripping.")

if __name__ == '__main__':
    unittest.main()
