import unittest
from ultra_modules.dialogue_lip_sync_timer_batch_pipeline import DialogueLipSyncTimerBatchPipeline

class TestDialogueLipSyncTimerBatchPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = DialogueLipSyncTimerBatchPipeline(max_workers=5)

    def test_normal_flow_mixed_inputs(self):
        """Test 1: Normal case with mixed inputs (text only, text + audio, provided duration)."""
        records = [
            {"text": "你好，世界！"},
            {"text": "这段话比较长，包含一些逗号，和句号。", "audio_url": "http://example.com/audio.mp3"},
            {"text": "我自带了时长。", "duration": 5.5},
            {"text": "包含波形。", "waveform_peaks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]} # 1.5s
        ]

        result = self.pipeline.process_batch(records)
        self.assertEqual(result["total_processed"], 4)
        self.assertEqual(result["success_count"], 4)
        self.assertEqual(len(result["results"]), 4)

        # Check generated durations (exact logic checks)
        res0 = result["results"][0]
        self.assertGreaterEqual(res0["calculated_duration"], 1.0)
        self.assertFalse(res0["has_audio_aligned"])

        res1 = result["results"][1]
        self.assertGreater(res1["calculated_duration"], res0["calculated_duration"])
        self.assertTrue(res1["has_audio_aligned"])

        res2 = result["results"][2]
        self.assertEqual(res2["calculated_duration"], 5.5)

        res3 = result["results"][3]
        self.assertGreaterEqual(res3["calculated_duration"], 1.5)
        self.assertTrue(res3["has_audio_aligned"])

    def test_dirty_data_self_healing(self):
        """Test 2: Dirty data self-healing (missing keys, None values, wrong types)."""
        records = [
            None,
            123,
            {"text": None},
            {"not_text": "hello"},
            {"text": "Error duration", "duration": "invalid_string"},
            {"text": "List as text", "text": ["this", "is", "wrong"]}
        ]

        result = self.pipeline.process_batch(records)
        self.assertEqual(result["total_processed"], 6)
        self.assertEqual(result["success_count"], 6) # Should all heal and succeed

        for r in result["results"]:
            self.assertGreaterEqual(r["calculated_duration"], 1.0)
            self.assertEqual(r["status"], "success")

        self.assertEqual(result["results"][4]["calculated_duration"], self.pipeline._calculate_duration("Error duration"))

    def test_missing_parameter_defaults(self):
        """Test 3: Missing parameter defaults (empty dict, empty string, empty list)."""
        records = [
            {},
            {"text": ""},
            {"text": "   "}
        ]

        result = self.pipeline.process_batch(records)
        self.assertEqual(result["total_processed"], 3)
        self.assertEqual(result["success_count"], 3)

        for r in result["results"]:
            self.assertEqual(r["calculated_duration"], 1.0) # Default min duration

        # Test totally empty input
        result_empty = self.pipeline.process_batch([])
        self.assertEqual(result_empty["total_processed"], 0)
        self.assertEqual(result_empty["success_count"], 0)

    def test_extreme_boundary_cases(self):
        """Test 4: Extreme boundary cases (massive batch size 1000 records)."""
        records = [{"text": f"这是第 {i} 条测试数据。" * 10} for i in range(1000)]

        result = self.pipeline.process_batch(records)
        self.assertEqual(result["total_processed"], 1000)
        self.assertEqual(result["success_count"], 1000)
        self.assertEqual(len(result["results"]), 1000)

        # Verify ordering is preserved
        for i in range(100): # check first 100
            self.assertTrue(str(i) in result["results"][i]["text"])

    def test_concurrent_execution_snapshots(self):
        """Test 5: Concurrent execution verification (streaming)."""
        records = [{"text": f"Streaming {i}"} for i in range(50)]

        snapshots = list(self.pipeline.stream_process_batch(records))
        self.assertTrue(len(snapshots) > 0)

        final_snapshot = snapshots[-1]
        self.assertEqual(final_snapshot["total"], 50)
        self.assertEqual(final_snapshot["completed"], 50)
        self.assertEqual(final_snapshot["progress"], 1.0)
        self.assertTrue(final_snapshot["is_final"])
        self.assertEqual(len(final_snapshot["all_results_so_far"]), 50)

        # Progress should be monotonically increasing or staying same in chunks
        prev_prog = 0
        for s in snapshots:
            self.assertGreaterEqual(s["progress"], prev_prog)
            prev_prog = s["progress"]

if __name__ == '__main__':
    unittest.main()
