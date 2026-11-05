import unittest
from unittest.mock import patch
import time

from ultra_modules.google_whisk_subject_bridge_self_healing_guard import WhiskPayloadBuilder

class TestWhiskPayloadBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = WhiskPayloadBuilder()

    def test_normal_payload(self):
        """Test payload generation with valid normal inputs."""
        payload = self.builder.build_payload(subject="Hero", style="Cyberpunk", scene="City")
        self.assertEqual(payload["subject"], "Hero")
        self.assertEqual(payload["style"], "Cyberpunk")
        self.assertEqual(payload["scene"], "City")
        self.assertIn("timestamp", payload)
        self.assertEqual(self.builder.get_snapshot_count(), 1)

    def test_missing_parameters_fallback(self):
        """Test that missing or None parameters fallback to reasonable defaults."""
        payload = self.builder.build_payload()
        self.assertEqual(payload["subject"], "default_subject")
        self.assertEqual(payload["style"], "default_style")
        self.assertEqual(payload["scene"], "default_scene")

        payload_none = self.builder.build_payload(subject=None, style=None, scene=None)
        self.assertEqual(payload_none["subject"], "default_subject")
        self.assertEqual(payload_none["style"], "default_style")
        self.assertEqual(payload_none["scene"], "default_scene")

    def test_dirty_data_self_healing(self):
        """Test self-healing for whitespace, empty strings, and non-string types."""
        # Empty string / whitespace
        payload = self.builder.build_payload(subject="   ", style="", scene="  \n ")
        self.assertEqual(payload["subject"], "default_subject")
        self.assertEqual(payload["style"], "default_style")
        self.assertEqual(payload["scene"], "default_scene")

        # Non-string coercible to string
        payload2 = self.builder.build_payload(subject=123, style=["a", "b"], scene={"key": "val"})
        self.assertEqual(payload2["subject"], "123")
        self.assertEqual(payload2["style"], "['a', 'b']")
        self.assertEqual(payload2["scene"], "{'key': 'val'}")

    @patch('time.time')
    def test_successful_undo(self, mock_time):
        """Test successful one-click undo within 5 seconds."""
        mock_time.return_value = 100.0
        self.builder.build_payload(subject="Test")
        self.assertEqual(self.builder.get_snapshot_count(), 1)

        # Advance time by 3 seconds (within 5 seconds limit)
        mock_time.return_value = 103.0
        result = self.builder.undo()

        self.assertTrue(result)
        self.assertEqual(self.builder.get_snapshot_count(), 0)

    @patch('time.time')
    def test_expired_undo(self, mock_time):
        """Test undo failure after 5 seconds have passed."""
        mock_time.return_value = 100.0
        self.builder.build_payload(subject="Test")
        self.assertEqual(self.builder.get_snapshot_count(), 1)

        # Advance time by 6 seconds (beyond 5 seconds limit)
        mock_time.return_value = 106.0
        result = self.builder.undo()

        self.assertFalse(result)
        self.assertEqual(self.builder.get_snapshot_count(), 1)

    def test_extreme_boundaries(self):
        """Test extreme/boundary cases such as undoing with empty history."""
        result = self.builder.undo()
        self.assertFalse(result)
        self.assertEqual(self.builder.get_snapshot_count(), 0)

    def test_sanitize_exception_handling(self):
        """Test sanitize's exception handling by passing a class that raises exception on __str__"""
        class BadClass:
            def __str__(self):
                raise ValueError("Bad string representation")

        payload = self.builder.build_payload(subject=BadClass())
        self.assertEqual(payload["subject"], "default_subject")

if __name__ == '__main__':
    unittest.main()
