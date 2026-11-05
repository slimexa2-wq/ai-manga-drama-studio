import unittest
import time
from unittest.mock import patch
from ultra_modules.multi_role_pitch_tts_self_healing_guard import MultiRolePitchTTSGuard, modulate_tts_params, align_duration_ms

class TestMultiRolePitchTTSGuard(unittest.TestCase):
    def setUp(self):
        self.guard = MultiRolePitchTTSGuard(undo_window_seconds=5.0)

    def test_normal_data(self):
        """Test with normal input data."""
        state = self.guard.process_tts_request(
            role="heroine",
            emotion="happy",
            target_duration_ms=2000,
            base_duration_ms=1000
        )
        self.assertEqual(state["role"], "heroine")
        self.assertEqual(state["emotion"], "happy")
        # heroine base (1.2, 1.05), happy mod (1.1, 1.1)
        # expected pitch: 1.2 * 1.1 = 1.32
        self.assertAlmostEqual(state["pitch"], 1.32, places=2)
        # target=2000, current=1000 -> required speed = 1000/2000 = 0.5
        self.assertAlmostEqual(state["speed"], 0.5, places=2)
        self.assertEqual(state["target_duration_ms"], 2000.0)

    def test_dirty_data_self_healing(self):
        """Test self-healing with dirty data like invalid strings or zero."""
        state = self.guard.process_tts_request(
            role=123,  # Invalid type, should convert to str and fallback if not matched
            emotion=None,  # Missing
            target_duration_ms="invalid_string",
            base_duration_ms=0
        )
        self.assertEqual(state["role"], "123")  # converts to str
        self.assertEqual(state["emotion"], "calm")
        # '123' role fallback to narrator (0.9, 1.0) or default fallback (1.0, 1.0)
        # Let's see: roles.get("123", (1.0, 1.0)) -> (1.0, 1.0)
        # emotion "calm" -> (1.0, 1.0)
        # expected pitch: 1.0
        self.assertEqual(state["pitch"], 1.0)

        # invalid target duration defaults to 1000.0
        # invalid (zero) base duration defaults to 1000.0
        # speed = 1000.0 / 1000.0 = 1.0
        self.assertEqual(state["speed"], 1.0)
        self.assertEqual(state["target_duration_ms"], 1000.0)

    def test_missing_parameter_fallback(self):
        """Test default fallbacks when parameters are missing."""
        state = self.guard.process_tts_request()
        self.assertEqual(state["role"], "narrator")
        self.assertEqual(state["emotion"], "calm")
        self.assertEqual(state["pitch"], 0.9)
        self.assertEqual(state["speed"], 1.0)
        self.assertIsNone(state["target_duration_ms"])

    def test_extreme_edge_cases(self):
        """Test with extreme boundary values."""
        state = self.guard.process_tts_request(
            role="villain",
            emotion="angry",
            target_duration_ms=-500, # negative should fallback
            base_duration_ms=float('inf') # infinity could be a problem, checking handled
        )
        self.assertEqual(state["role"], "villain")
        self.assertEqual(state["emotion"], "angry")
        # villain (0.8, 0.95), angry (1.2, 1.2) -> pitch 0.96
        self.assertAlmostEqual(state["pitch"], 0.96, places=2)
        # Negative target falls back to 1000.0
        self.assertEqual(state["target_duration_ms"], 1000.0)

    def test_undo_mechanism_success(self):
        """Test successful 5-second one-click undo mechanism."""
        state1 = self.guard.process_tts_request(role="hero", emotion="calm")
        state2 = self.guard.process_tts_request(role="villain", emotion="angry")

        self.assertEqual(self.guard.get_current_state()["role"], "villain")

        # Undo to previous state
        success = self.guard.undo()
        self.assertTrue(success)
        self.assertEqual(self.guard.get_current_state()["role"], "hero")

        # Undo again to empty initial state
        success2 = self.guard.undo()
        self.assertTrue(success2)
        self.assertEqual(self.guard.get_current_state(), {})

    def test_undo_mechanism_expiration(self):
        """Test that snapshots older than 5 seconds are ignored."""
        with patch('time.time') as mock_time:
            # Start at t=0
            mock_time.return_value = 0.0
            self.guard.process_tts_request(role="narrator")

            # Move to t=6.0 (past the 5-second window)
            mock_time.return_value = 6.0

            # Undo should fail because snapshot is expired
            success = self.guard.undo()
            self.assertFalse(success)
            # Current state remains unchanged
            self.assertEqual(self.guard.get_current_state()["role"], "narrator")

    def test_empty_undo(self):
        """Test undo when no snapshots are available."""
        success = self.guard.undo()
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
