import unittest
import time
from ultra_modules.golden_3s_hook_splitter_benchmark_suite import Golden3SHookSplitter, SplitterBenchmarkSuite

class TestGolden3SHookSplitter(unittest.TestCase):

    def setUp(self):
        self.splitter = Golden3SHookSplitter()

    def test_normal_behavior(self):
        """Test normal text splitting functionality."""
        text = "This is paragraph one.\n" * 50 + "This is paragraph two.\n" * 50
        results = self.splitter.split(text, words_per_episode=200)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["episode_number"], 1)
        self.assertIn("content", results[0])

    def test_dirty_data_healing(self):
        """Test that the splitter silently heals dirty data (null bytes, weird objects)."""
        dirty_text = "Hello\x00World\x0c!"
        results = self.splitter.split(dirty_text)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "HelloWorld!")

        # Test dictionary conversion
        dict_text = {"key": "value"}
        results2 = self.splitter.split(dict_text)
        self.assertTrue(len(results2) > 0)

        # Test integer conversion
        int_text = 12345
        results3 = self.splitter.split(int_text)
        self.assertEqual(results3[0]["content"], "12345")

        # Test None
        self.assertEqual(self.splitter.split(None), [])

    def test_defaults_for_missing_parameters(self):
        """Test reasonable defaults when parameters are missing or invalid."""
        text = "word \n" * 1500
        # No words_per_episode provided, should use default (1000)
        results = self.splitter.split(text)
        self.assertEqual(len(results), 2)

        # Invalid words_per_episode provided, should fall back to default
        results2 = self.splitter.split(text, words_per_episode=-50)
        self.assertEqual(len(results2), 2)

        # Invalid initialization
        bad_splitter = Golden3SHookSplitter(default_words_per_episode=-100)
        results3 = bad_splitter.split(text)
        self.assertEqual(len(results3), 2)

    def test_extreme_edge_conditions(self):
        """Test extreme boundary/edge cases like empty strings, whitespace only."""
        self.assertEqual(self.splitter.split(""), [])
        self.assertEqual(self.splitter.split("   \n  \t  "), [])

        # Extremely large single word (no spaces)
        long_word = "A" * 10000
        results = self.splitter.split(long_word, words_per_episode=100)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], long_word)

    def test_performance_benchmark_fixture(self):
        """Test that the benchmark suite can run and split a large synthetic dataset efficiently."""
        start = time.time()
        time_taken = SplitterBenchmarkSuite.run_benchmark()
        total_test_time = time.time() - start

        # The benchmark should complete relatively fast, check it didn't take excessively long
        # (e.g. < 5 seconds for 10MB on decent hardware)
        self.assertTrue(time_taken < 10.0, f"Benchmark took too long: {time_taken} seconds")

if __name__ == "__main__":
    unittest.main()
