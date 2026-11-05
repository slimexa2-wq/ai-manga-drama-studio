import unittest
import asyncio
from typing import Dict, Any

from ultra_modules.ego_dual_cloud_dispatcher_audit_trace import EgoDualCloudDispatcherAuditTrace

class TestEgoDualCloudDispatcherAuditTrace(unittest.TestCase):
    def setUp(self):
        self.dispatcher = EgoDualCloudDispatcherAuditTrace()

    def test_normal_execution(self):
        """Test normal execution with standard parameters."""
        prompt = "Create a summary of AI advances in 2024."
        result = self.dispatcher.dispatch(prompt, "chatgpt_plus")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "chatgpt_plus")
        self.assertTrue(result["result"].startswith("Result from chatgpt_plus"))

        # Verify audit log recorded events dynamically
        audit_log = self.dispatcher.get_audit_log()
        self.assertTrue(len(audit_log) >= 3)  # INIT, DISPATCH_START, DISPATCH_COMPLETE

        # Verify timestamp property dynamically
        for entry in audit_log:
            self.assertIn("timestamp", entry)
            self.assertIsInstance(entry["timestamp"], float)

    def test_missing_parameter_fallback(self):
        """Test fallback when parameters are missing."""
        # Dispatch with missing model (None)
        result = self.dispatcher.dispatch("A short prompt")

        # Should fallback to default_model "google_ultra"
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "google_ultra")

    def test_dirty_data_self_healing(self):
        """Test self-healing mechanisms for dirty data."""
        # Dirty prompt and model
        dirty_prompt = None
        dirty_model = "  ChAtgPt_PLuS  "

        result = self.dispatcher.dispatch(dirty_prompt, dirty_model)

        # Should heal model to "chatgpt_plus" and prompt to empty string/default
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model"], "chatgpt_plus")

        # Test completely invalid model type
        invalid_model_result = self.dispatcher.dispatch("prompt", 12345)
        self.assertEqual(invalid_model_result["model"], "google_ultra")

    def test_deduplication(self):
        """Test that identical requests are deduplicated."""
        prompt = "Duplicate prompt test"
        model = "google_ultra"

        # First call
        res1 = self.dispatcher.dispatch(prompt, model)

        # Second call - should hit cache
        res2 = self.dispatcher.dispatch(prompt, model)

        self.assertEqual(res1, res2)

        audit_log = self.dispatcher.get_audit_log()
        dedup_hits = [entry for entry in audit_log if entry["action"] == "DEDUPLICATION_HIT"]
        self.assertEqual(len(dedup_hits), 1)

    def test_extreme_boundaries(self):
        """Test extreme boundary cases like huge inputs."""
        huge_prompt = "A" * 1000000  # 1MB prompt
        result = self.dispatcher.dispatch(huge_prompt)

        self.assertEqual(result["status"], "success")
        self.assertTrue("Result from google_ultra" in result["result"])

    def test_diff_highlight_comparator(self):
        """Test the diff highlight comparator."""
        orig = "Original text"
        new_text = "New text"

        diff = self.dispatcher.diff_highlight_comparator(orig, new_text)

        self.assertFalse(diff["is_identical"])
        self.assertEqual(diff["original_length"], len(orig))
        self.assertEqual(diff["new_length"], len(new_text))

        audit_log = self.dispatcher.get_audit_log()
        diff_entries = [entry for entry in audit_log if entry["action"] == "DIFF_COMPARISON"]
        self.assertEqual(len(diff_entries), 1)

    def test_async_dispatch_in_existing_loop(self):
        """Test calling dispatch when an event loop is already running."""
        async def run_test():
            result = self.dispatcher.dispatch("Test async")
            self.assertEqual(result["status"], "success")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
