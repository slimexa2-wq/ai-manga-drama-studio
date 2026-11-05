import unittest
import time
from typing import Dict, Any

from ultra_modules.veo3_camera_motion_prompter_batch_pipeline import (
    PromptCompiler,
    Veo3CameraMotionPrompterBatchPipeline
)

class TestVeo3CameraMotionPrompterBatchPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = Veo3CameraMotionPrompterBatchPipeline(max_workers=20)

    def tearDown(self):
        self.pipeline.shutdown()

    def test_1_normal_parameters(self):
        """Test case 1: Normal inputs with full parameters."""
        record = {
            "subject": "A cyber samurai standing in neon rain",
            "lens": "50mm wide lens",
            "camera_motion": "slow push in, pan right",
            "lighting": "cyberpunk neon lighting, high contrast",
            "speed": "slow motion (0.5x)"
        }

        compiled = PromptCompiler.compile_prompt(record)

        self.assertIn("A cyber samurai standing in neon rain", compiled)
        self.assertIn("50mm wide lens", compiled)
        self.assertIn("slow push in, pan right", compiled)
        self.assertIn("cyberpunk neon lighting", compiled)
        self.assertIn("slow motion", compiled)

    def test_2_dirty_data_self_healing(self):
        """Test case 2: Dirty data self-healing (invalid types, None values)."""
        record = {
            "subject": 12345,  # int instead of string
            "lens": None,      # None
            "camera_motion": ["invalid", "list"], # list instead of string
            "lighting": "   valid string with spaces   ",
            "speed": ""        # empty string
        }

        compiled = PromptCompiler.compile_prompt(record)

        # 12345 is not a string, falls back to default
        self.assertIn(PromptCompiler.DEFAULT_SUBJECT, compiled)
        # None falls back to default
        self.assertIn(PromptCompiler.DEFAULT_LENS, compiled)
        # List falls back to default
        self.assertIn(PromptCompiler.DEFAULT_CAMERA_MOTION, compiled)
        # Spaces should be stripped
        self.assertIn("valid string with spaces", compiled)
        self.assertNotIn("   valid string with spaces   ", compiled)
        # Empty string falls back to default
        self.assertIn(PromptCompiler.DEFAULT_SPEED, compiled)

        # Test compiling totally invalid record (not dict)
        compiled_not_dict = PromptCompiler.compile_prompt(["invalid", "type"])
        self.assertIn(PromptCompiler.DEFAULT_SUBJECT, compiled_not_dict)

    def test_3_missing_parameters_fallback(self):
        """Test case 3: Missing parameter fallback (empty parameters, missing keys default to reasonable cinematic fallbacks)."""
        record: Dict[str, Any] = {}
        compiled = PromptCompiler.compile_prompt(record)

        self.assertIn(PromptCompiler.DEFAULT_SUBJECT, compiled)
        self.assertIn(PromptCompiler.DEFAULT_LENS, compiled)
        self.assertIn(PromptCompiler.DEFAULT_CAMERA_MOTION, compiled)
        self.assertIn(PromptCompiler.DEFAULT_LIGHTING, compiled)
        self.assertIn(PromptCompiler.DEFAULT_SPEED, compiled)

    def test_4_non_blocking_and_snapshot(self):
        """Test case 4: Non-blocking batch processing and progress snapshots."""
        records = [
            {"subject": f"Subject {i}"} for i in range(50)
        ]

        job_id = self.pipeline.submit_batch(records)
        self.assertIsNotNone(job_id)

        # Should be able to get a snapshot immediately without blocking
        snapshot = self.pipeline.get_progress_snapshot(job_id)
        self.assertIn(snapshot["status"], ["processing", "completed"])
        self.assertEqual(snapshot["total"], 50)
        self.assertTrue(0 <= snapshot["completed"] <= 50)

        # Wait for completion
        timeout = 5.0
        start = time.time()
        while time.time() - start < timeout:
            snapshot = self.pipeline.get_progress_snapshot(job_id)
            if snapshot["status"] == "completed":
                break
            time.sleep(0.1)

        self.assertEqual(snapshot["status"], "completed")
        self.assertEqual(snapshot["completed"], 50)
        self.assertEqual(snapshot["progress_percentage"], 100)
        self.assertIsNotNone(snapshot["results"])
        self.assertEqual(len(snapshot["results"]), 50)
        self.assertIn("Subject 0", snapshot["results"][0])

    def test_5_extreme_edge_cases(self):
        """Test case 5: Extreme edge cases (empty lists, huge batch of 1000+ items)."""

        # Empty list
        job_id_empty = self.pipeline.submit_batch([])
        snapshot_empty = self.pipeline.get_progress_snapshot(job_id_empty)
        self.assertEqual(snapshot_empty["status"], "completed")
        self.assertEqual(snapshot_empty["total"], 0)
        self.assertEqual(snapshot_empty["completed"], 0)
        self.assertEqual(snapshot_empty["progress_percentage"], 100)

        # Invalid input (not a list)
        job_id_invalid = self.pipeline.submit_batch("not a list") # type: ignore
        snapshot_invalid = self.pipeline.get_progress_snapshot(job_id_invalid)
        self.assertEqual(snapshot_invalid["status"], "completed")
        self.assertEqual(snapshot_invalid["total"], 0)

        # Huge batch (1000 items)
        records = [{"subject": f"Huge {i}"} for i in range(1000)]
        job_id_huge = self.pipeline.submit_batch(records)

        # Non blocking immediate check
        snapshot_huge_start = self.pipeline.get_progress_snapshot(job_id_huge)
        self.assertIn(snapshot_huge_start["status"], ["processing", "completed"])

        # Wait for completion
        timeout = 10.0
        start = time.time()
        while time.time() - start < timeout:
            snapshot = self.pipeline.get_progress_snapshot(job_id_huge)
            if snapshot["status"] == "completed":
                break
            time.sleep(0.5)

        snapshot_huge_end = self.pipeline.get_progress_snapshot(job_id_huge)
        self.assertEqual(snapshot_huge_end["status"], "completed")
        self.assertEqual(snapshot_huge_end["completed"], 1000)
        self.assertEqual(len(snapshot_huge_end["results"]), 1000)

        # Job not found
        snapshot_not_found = self.pipeline.get_progress_snapshot("non-existent-id")
        self.assertEqual(snapshot_not_found["status"], "not_found")

if __name__ == '__main__':
    unittest.main()
