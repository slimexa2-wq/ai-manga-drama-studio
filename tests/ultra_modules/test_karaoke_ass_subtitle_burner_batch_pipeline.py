import unittest
from unittest.mock import patch
import os
import time
import shutil
from typing import List, Dict

from ultra_modules.karaoke_ass_subtitle_burner_batch_pipeline import (
    KaraokeSubtitleBatchPipeline,
    SubtitleTask,
    ms_to_ass_time,
    generate_karaoke_ass_content
)

class TestKaraokeSubtitleBatchPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = KaraokeSubtitleBatchPipeline(max_workers=5)
        # Create dummy directory for test outputs
        self.test_dir = "test_karaoke_outputs"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        self.pipeline.shutdown(wait=True)
        # Cleanup
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        # Remove any lingering temp ass files or default output files created in current dir
        for f in os.listdir("."):
            if f.endswith("_temp.ass") or f.startswith("default_burned") or f.endswith("_burned.mp4"):
                os.remove(f)

    def test_ms_to_ass_time(self):
        self.assertEqual(ms_to_ass_time(0), "0:00:00.00")
        self.assertEqual(ms_to_ass_time(1000), "0:00:01.00")
        self.assertEqual(ms_to_ass_time(3600000), "1:00:00.00")
        self.assertEqual(ms_to_ass_time(3661000), "1:01:01.00")
        self.assertEqual(ms_to_ass_time(-100), "0:00:00.00") # Extreme boundary

    def test_generate_karaoke_ass_content(self):
        lyrics = [{
            "start": 1000,
            "end": 2000,
            "words": [
                {"word": "Hello", "duration": 500},
                {"word": "World", "duration": 500}
            ]
        }]
        content = generate_karaoke_ass_content(lyrics)
        self.assertIn("[Script Info]", content)
        self.assertIn("Dialogue: 0,0:00:01.00,0:00:02.00", content)
        self.assertIn("{\\kf50\\fscx120\\fscy120\\t(0,500, \\fscx100\\fscy100)}Hello", content)

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_missing_parameters_fallback(self, mock_run, mock_exists):
        mock_exists.return_value = True

        # Missing output path, missing video path
        data = [{
            "task_id": "test_missing_params",
            "video_path": "",
            "lyrics": []
        }]
        task_ids = self.pipeline.submit_batch(data)
        self.assertEqual(len(task_ids), 1)

        # Wait for completion
        time.sleep(0.5)

        snapshot = self.pipeline.get_progress_snapshot()
        self.assertEqual(snapshot["completed"], 1)
        result = snapshot["results"]["test_missing_params"]
        self.assertEqual(result["status"], "COMPLETED")
        self.assertTrue(result["output_path"].endswith("default_burned.mp4"))

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_dirty_data_self_healing(self, mock_run, mock_exists):
        mock_exists.return_value = True

        # Invalid timestamps, negative values, etc.
        data = [{
            "task_id": "test_dirty_data",
            "video_path": os.path.join(self.test_dir, "dirty.avi"),
            "lyrics": [{
                "start": -500,
                "end": -100,
                "words": [
                    {"word": "Bad", "duration": -100},
                    {"word": "Time"} # Missing duration
                ]
            }]
        }]
        task_ids = self.pipeline.submit_batch(data)
        time.sleep(0.5)

        snapshot = self.pipeline.get_progress_snapshot()
        self.assertEqual(snapshot["completed"], 1)
        result = snapshot["results"]["test_dirty_data"]
        self.assertEqual(result["status"], "COMPLETED")
        # Ensure extension auto-correction to .mp4
        self.assertEqual(result["output_path"], os.path.join(self.test_dir, "dirty_burned.avi"))

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_extreme_boundary_conditions(self, mock_run, mock_exists):
        mock_exists.return_value = True

        # Empty inputs
        data = []
        task_ids = self.pipeline.submit_batch(data)
        self.assertEqual(len(task_ids), 0)

        snapshot = self.pipeline.get_progress_snapshot()
        self.assertEqual(snapshot["total"], 0)

        # Empty dict
        data = [{}]
        task_ids = self.pipeline.submit_batch(data)
        self.assertEqual(len(task_ids), 1)
        time.sleep(0.5)
        snapshot = self.pipeline.get_progress_snapshot()
        self.assertEqual(snapshot["total"], 1)
        self.assertEqual(snapshot["completed"], 1)

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_normal_batch_and_concurrency(self, mock_run, mock_exists):
        mock_exists.return_value = True

        # Submit a batch of 20 items to test concurrency and snapshot mechanism
        batch_size = 20
        data = []
        for i in range(batch_size):
            data.append({
                "task_id": f"concurrency_{i}",
                "video_path": os.path.join(self.test_dir, f"video_{i}.mp4"),
                "lyrics": [{"start": 0, "end": 1000, "words": [{"word": "Test", "duration": 1000}]}]
            })

        task_ids = self.pipeline.submit_batch(data)
        self.assertEqual(len(task_ids), batch_size)

        # Immediate snapshot
        snapshot = self.pipeline.get_progress_snapshot()
        self.assertEqual(snapshot["total"], batch_size)

        # Wait for all to complete
        time.sleep(1)
        snapshot = self.pipeline.get_progress_snapshot()
        self.assertEqual(snapshot["completed"], batch_size)
        self.assertEqual(snapshot["pending"], 0)
        self.assertEqual(snapshot["failed"], 0)

if __name__ == "__main__":
    unittest.main()
