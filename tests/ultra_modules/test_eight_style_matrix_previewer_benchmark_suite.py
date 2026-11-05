import unittest
import time
from datetime import datetime
from ultra_modules.eight_style_matrix_previewer_benchmark_suite import EightStyleMatrixPreviewerBenchmarkSuite

class TestEightStyleMatrixPreviewerBenchmarkSuite(unittest.TestCase):
    def setUp(self):
        self.suite = EightStyleMatrixPreviewerBenchmarkSuite(concurrency_limit=50)

    def test_normal_case_success(self):
        """Test normal data generation and millisecond response time."""
        payload = {
            "text": "The hero awakens his hidden power.",
            "timestamp": "2023-10-15T12:00:00+00:00",
            "resolution": "1920x1080"
        }
        result = self.suite.generate_matrix_preview(payload)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["original_text"], payload["text"])
        self.assertEqual(result["resolution"], "1920x1080")
        self.assertEqual(len(result["matrix"]), 8)
        self.assertTrue(result["processing_time_ms"] < 100) # Response within 100ms

    def test_dirty_data_self_healing(self):
        """Test zero-configuration fault tolerance with dirty/malformed data."""
        payload = {
            "text": "   \n\t  ", # Whitespace only
            "timestamp": "invalid-time",
            "resolution": "bad_res"
        }
        result = self.suite.generate_matrix_preview(payload)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["original_text"], self.suite.DEFAULT_TEXT)
        self.assertEqual(result["resolution"], self.suite.DEFAULT_RESOLUTION)
        # Check if timestamp is auto-healed to a valid ISO format
        try:
            datetime.fromisoformat(result["timestamp"])
        except ValueError:
            self.fail("Timestamp was not healed to valid ISO format")

        # Test non-dict payload
        non_dict_result = self.suite.generate_matrix_preview(["I am a list"])
        self.assertEqual(non_dict_result["status"], "success")
        self.assertEqual(non_dict_result["original_text"], self.suite.DEFAULT_TEXT)

    def test_missing_parameter_fallback(self):
        """Test missing parameters get reasonable default values."""
        payload = {}
        result = self.suite.generate_matrix_preview(payload)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["original_text"], self.suite.DEFAULT_TEXT)
        self.assertEqual(result["resolution"], self.suite.DEFAULT_RESOLUTION)
        self.assertTrue(result["timestamp"])

    def test_extreme_boundary_cases(self):
        """Test cross-year boundary timestamps and non-printable characters."""
        payload = {
            "text": "Test\x00\x01\x02\x03Boundary",
            "timestamp": "2023-12-31T23:59:59.999",
            "resolution": "  3840 x 2160  "
        }
        result = self.suite.generate_matrix_preview(payload)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["original_text"], "TestBoundary") # Non-printable cleaned
        self.assertEqual(result["resolution"], "3840x2160") # Spaces cleaned

    def test_high_concurrency_benchmark(self):
        """Test zero crashes under high concurrency with synthetic fixtures."""
        # 1000 items is a good test, but we can do a smaller subset for unit test speed if needed,
        # 200 items is sufficient to test threading limits and zero-crash without taking too long.
        benchmark_results = self.suite.benchmark_performance(count=200)
        self.assertEqual(benchmark_results["total_requests"], 200)
        self.assertEqual(benchmark_results["successful_requests"], 200)
        self.assertTrue(benchmark_results["avg_processing_time_ms"] >= 0)

if __name__ == '__main__':
    unittest.main()
