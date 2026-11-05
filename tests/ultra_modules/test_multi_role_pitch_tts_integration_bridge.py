import unittest
from ultra_modules.multi_role_pitch_tts_integration_bridge import bridge_and_modulate


class TestMultiRolePitchTTSIntegrationBridge(unittest.TestCase):
    def test_normal_operation_standard_fields(self):
        # Test Case 1: Normal operation with standard fields
        payload = {
            "text": "Hello, world!",
            "role": "female_lead",
            "pitch_shift": 0.1,
            "speed_multiplier": 1.2,
            "target_duration_ms": 2000.0
        }
        result = bridge_and_modulate(payload)
        self.assertEqual(result["text"], "Hello, world!")
        self.assertEqual(result["role"], "female_lead")
        self.assertIn("pitch", result)
        self.assertIn("speed", result)
        self.assertIn("duration_ms", result)

    def test_dirty_data_auto_healing(self):
        # Test Case 2: Dirty data auto-healing
        payload = {
            "msg_content": None,
            "character": {"invalid": "dict"},
            "pitch_modifier": "not_a_float",
            "play_speed": -5.0,
            "target_time": float('nan')
        }
        result = bridge_and_modulate(payload)
        self.assertEqual(result["text"], "...")  # Fallback text
        self.assertEqual(result["role"], "narrator")  # Fallback role
        self.assertEqual(result["pitch"], 1.0)
        self.assertEqual(result["speed"], 1.0)

    def test_missing_parameter_fallbacks(self):
        # Test Case 3: Missing parameter fallbacks (None and empty dict)
        result1 = bridge_and_modulate(None)
        self.assertEqual(result1["text"], "...")
        self.assertEqual(result1["role"], "narrator")

        result2 = bridge_and_modulate({})
        self.assertEqual(result2["text"], "...")
        self.assertEqual(result2["role"], "narrator")

        result3 = bridge_and_modulate("invalid_payload_type")
        self.assertEqual(result3["text"], "...")
        self.assertEqual(result3["role"], "narrator")

    def test_extreme_boundary_edge_cases(self):
        # Test Case 4: Extreme boundary and edge cases
        long_text = "A" * 10000
        payload = {
            "content": long_text,
            "actor_role": "villain",
            "pitch_offset": 100.0,  # Extremely high pitch
            "speed_rate": 0.0001,   # Extremely low speed
            "duration_target": -100.0 # Negative target duration
        }
        result = bridge_and_modulate(payload)
        self.assertEqual(result["text"], long_text)
        self.assertEqual(result["role"], "villain")
        self.assertEqual(result["pitch"], 3.0)  # Should be clamped to max 3.0
        self.assertEqual(result["speed"], 0.1)  # Should be clamped to min 0.1 (0.9 * 0.1 ?) Wait, clamp is on final, min 0.1

    def test_schema_forward_compatibility(self):
        # Test Case 5: Schema forward compatibility (legacy fields)
        payload = {
            "msg_content": "Legacy text",
            "actor_role": "male_lead",
            "pitch_modifier": -0.2,
            "play_speed": 1.5,
            "target_time": 3000.0
        }
        result = bridge_and_modulate(payload)
        self.assertEqual(result["text"], "Legacy text")
        self.assertEqual(result["role"], "male_lead")
        self.assertAlmostEqual(result["pitch"], 0.6)  # base_pitch 0.8 - 0.2 = 0.6
        self.assertAlmostEqual(result["duration_ms"], 3000.0) # Meets target duration

    def test_schema_forward_compatibility_alternative_fields(self):
        # Additional test for other legacy fields
        payload = {
            "content": "Alt text",
            "character": "narrator",
            "pitch_offset": 0.5,
            "speed_rate": 2.0,
            "duration_target": 1000.0
        }
        result = bridge_and_modulate(payload)
        self.assertEqual(result["text"], "Alt text")
        self.assertEqual(result["role"], "narrator")
        self.assertAlmostEqual(result["pitch"], 1.5)
        self.assertAlmostEqual(result["duration_ms"], 1000.0)

if __name__ == '__main__':
    unittest.main()
