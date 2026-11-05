import unittest
import math
from ultra_modules.multi_role_pitch_tts_audit_trace import MultiRoleTTSModulator

class TestMultiRoleTTSModulator(unittest.TestCase):
    def setUp(self):
        self.modulator = MultiRoleTTSModulator()

    def test_normal_case_multiple_roles_emotions(self):
        """Test normal cases with valid roles and emotions."""
        result = self.modulator.modulate(role="male_lead", emotion="angry", text="Hello world")
        self.assertEqual(result["role"], "male_lead")
        self.assertEqual(result["emotion"], "angry")
        self.assertEqual(result["text"], "Hello world")
        self.assertEqual(result["pitch"], -3.0)  # -2.0 base - 1.0 emotion
        self.assertEqual(result["speed"], 1.32)  # 1.1 base * 1.2 emotion

        self.modulator.clear_audit_trail()
        result = self.modulator.modulate(role="female_lead", emotion="happy", text="Hi there")
        self.assertEqual(result["role"], "female_lead")
        self.assertEqual(result["emotion"], "happy")
        self.assertEqual(result["text"], "Hi there")
        self.assertEqual(result["pitch"], 3.5)  # 2.0 base + 1.5 emotion
        self.assertEqual(result["speed"], 1.21) # 1.05 base * 1.15 emotion

    def test_dirty_data_healing_and_fallback(self):
        """Test how dirty data is silently healed."""
        # None inputs
        result = self.modulator.modulate(role=None, emotion=None, text=None, target_duration_ms=None)
        self.assertEqual(result["role"], "narrator")
        self.assertEqual(result["emotion"], "neutral")
        self.assertEqual(result["text"], "")
        self.assertEqual(result["pitch"], 0.0)
        self.assertEqual(result["speed"], 1.0)

        # Non-string fallback for text
        self.modulator.clear_audit_trail()
        result = self.modulator.modulate(role="narrator", emotion="neutral", text=123)
        self.assertEqual(result["text"], "123")

        # Invalid role and emotion
        self.modulator.clear_audit_trail()
        result = self.modulator.modulate(role="unknown_role", emotion="unknown_emotion", text="  Too   many   spaces  ")
        self.assertEqual(result["role"], "narrator")
        self.assertEqual(result["emotion"], "neutral")
        self.assertEqual(result["text"], "Too many spaces")

        logs = self.modulator.get_audit_trail()
        actions = [log["action"] for log in logs]
        self.assertIn("sanitize_string_space_dedup", actions)
        self.assertIn("unknown_role_fallback", actions)
        self.assertIn("unknown_emotion_fallback", actions)

    def test_millisecond_duration_alignment(self):
        """Test dynamic speed adjustment based on target duration."""
        text = "12345" # 5 chars * 250ms = 1250ms estimated base

        # Exact fit
        result = self.modulator.modulate(role="narrator", text=text, target_duration_ms=1250)
        self.assertEqual(result["speed"], 1.0)

        # Needs to be twice as fast
        result = self.modulator.modulate(role="narrator", text=text, target_duration_ms=625)
        self.assertEqual(result["speed"], 2.0)

        # Needs to be twice as slow
        result = self.modulator.modulate(role="narrator", text=text, target_duration_ms=2500)
        self.assertEqual(result["speed"], 0.5)

    def test_extreme_boundary_clamping(self):
        """Test boundaries for pitch and speed."""
        text = "12345" # 1250ms

        # Extremely fast (should clamp to max 2.0)
        result = self.modulator.modulate(role="narrator", text=text, target_duration_ms=10) # 1250 / 10 = 125.0 -> clamped 2.0
        self.assertEqual(result["speed"], 2.0)

        # Extremely slow (should clamp to min 0.5)
        result = self.modulator.modulate(role="narrator", text=text, target_duration_ms=100000) # 1250 / 100000 = 0.0125 -> clamped 0.5
        self.assertEqual(result["speed"], 0.5)

        # Extreme pitch by role + emotion
        result = self.modulator.modulate(role="villain", emotion="sad", text="test")
        self.assertEqual(result["pitch"], -5.5) # -4.0 - 1.5

        result = self.modulator.modulate(role="female_lead", emotion="excited", text="test")
        self.assertEqual(result["pitch"], 4.0) # 2.0 + 2.0

        # Invalid float for target_duration_ms
        self.modulator.clear_audit_trail()
        result = self.modulator.modulate(role="narrator", text="test", target_duration_ms="invalid")
        logs = self.modulator.get_audit_trail()
        actions = [log["action"] for log in logs]
        self.assertIn("sanitize_float_invalid", actions)

        self.modulator.clear_audit_trail()
        result = self.modulator.modulate(role="narrator", text="test", target_duration_ms=float('inf'))
        logs = self.modulator.get_audit_trail()
        actions = [log["action"] for log in logs]
        self.assertIn("sanitize_float_invalid", actions)

        self.modulator.clear_audit_trail()
        result = self.modulator.modulate(role="narrator", text="test", target_duration_ms=float('nan'))
        logs = self.modulator.get_audit_trail()
        actions = [log["action"] for log in logs]
        self.assertIn("sanitize_float_invalid", actions)

    def test_audit_trail_logging(self):
        """Test that the audit trail captures operations silently."""
        self.modulator.modulate(role="unknown_role", emotion="unknown_emotion", text="   a    b   ", target_duration_ms=-100)
        logs = self.modulator.get_audit_trail()

        # Verify specific logs exist
        actions = [log["action"] for log in logs]
        self.assertIn("sanitize_string_space_dedup", actions)
        self.assertIn("unknown_role_fallback", actions)
        self.assertIn("unknown_emotion_fallback", actions)
        self.assertIn("sanitize_float_clamp_min", actions)
        self.assertIn("modulate_success", actions)
        self.assertTrue(len(logs) > 0)

    def test_none_target_duration(self):
        self.modulator.modulate(role="narrator", emotion="neutral", text="test", target_duration_ms=None)
        logs = self.modulator.get_audit_trail()
        actions = [log["action"] for log in logs]
        self.assertIn("sanitize_float_default", actions)

if __name__ == '__main__':
    unittest.main()
