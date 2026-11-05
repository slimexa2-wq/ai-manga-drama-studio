import math
import unittest
import time

from ultra_modules.dialogue_lip_sync_timer_benchmark_suite import DialogueLipSyncTimer, BenchmarkSuite

class TestDialogueLipSyncTimer(unittest.TestCase):
    def test_normal_operation(self):
        """Test normal text processing with default or specific parameters."""
        # Simple English
        duration = DialogueLipSyncTimer.calculate_duration("Hello world!", wpm=60)
        self.assertGreater(duration, 0)

        # CJK text with punctuation
        duration2 = DialogueLipSyncTimer.calculate_duration("测试一句话，测试第二句话。", wpm=120, pause_duration=0.5)
        self.assertGreater(duration2, 0)

        # Batch calculation
        texts = ["Hello", "World!"]
        results = DialogueLipSyncTimer.batch_calculate(texts)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r > 0 for r in results))

    def test_dirty_data_auto_healing(self):
        """Test handling of dirty data: None, empty strings, invalid types (dicts, lists)."""
        dirty_cases = [None, "", "   ", {"key": "value"}, ["list", "item"]]

        for case in dirty_cases:
            duration = DialogueLipSyncTimer.calculate_duration(case)
            self.assertIsInstance(duration, float)
            self.assertFalse(math.isnan(duration))
            self.assertFalse(math.isinf(duration))

        # Batch calculation with mixed data
        mixed_batch = ["Valid", None, "Also valid", {"bad": "type"}]
        results = DialogueLipSyncTimer.batch_calculate(mixed_batch)
        self.assertEqual(len(results), 4)
        self.assertGreater(results[0], 0)
        self.assertEqual(results[1], 0)
        self.assertGreater(results[2], 0)
        self.assertIsInstance(results[3], float)

    def test_missing_parameters_fallback(self):
        """Test that missing or invalid WPM and pause durations fall back to defaults."""
        text = "Hello world! This is a test."

        # Valid parameters
        base_dur = DialogueLipSyncTimer.calculate_duration(text, wpm=100, pause_duration=0.5)

        # Invalid parameters - should fallback
        dur_invalid_wpm = DialogueLipSyncTimer.calculate_duration(text, wpm="invalid", pause_duration=0.5)
        self.assertGreater(dur_invalid_wpm, 0)

        dur_nan_wpm = DialogueLipSyncTimer.calculate_duration(text, wpm=math.nan)
        self.assertGreater(dur_nan_wpm, 0)

        dur_neg_wpm = DialogueLipSyncTimer.calculate_duration(text, wpm=-10)
        self.assertGreater(dur_neg_wpm, 0)

        dur_nan_pause = DialogueLipSyncTimer.calculate_duration(text, pause_duration=math.nan)
        self.assertGreater(dur_nan_pause, 0)

        dur_inf_pause = DialogueLipSyncTimer.calculate_duration(text, pause_duration=float('inf'))
        self.assertGreater(dur_inf_pause, 0)

    def test_extreme_bounds_and_nan_inf(self):
        """Test extreme bounds, massive strings, NaN and Inf inputs."""
        # NaN and Inf as text input
        self.assertEqual(DialogueLipSyncTimer.calculate_duration(math.nan), 0.0)
        self.assertEqual(DialogueLipSyncTimer.calculate_duration(float('inf')), 0.0)
        self.assertEqual(DialogueLipSyncTimer.calculate_duration(-float('inf')), 0.0)

        # Massive strings
        massive_text = "A" * 100000
        start_time = time.time()
        duration = DialogueLipSyncTimer.calculate_duration(massive_text)
        elapsed = time.time() - start_time

        self.assertGreater(duration, 0)
        self.assertLessEqual(duration, 24 * 3600)  # Max capped duration
        # Execution time should be small even for large texts
        self.assertLess(elapsed, 1.0)

    def test_benchmark_suite(self):
        """Test that the benchmark suite runs successfully without crashing."""
        results = BenchmarkSuite.run_benchmark()

        self.assertIn("normal", results)
        self.assertIn("dirty", results)
        self.assertIn("massive", results)
        self.assertIn("edge", results)

        for category, stats in results.items():
            self.assertIn("count", stats)
            self.assertIn("elapsed_ms", stats)
            self.assertIn("avg_ms_per_item", stats)

if __name__ == '__main__':
    unittest.main()
