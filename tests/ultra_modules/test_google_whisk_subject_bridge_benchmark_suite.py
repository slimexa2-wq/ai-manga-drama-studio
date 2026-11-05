import unittest
from ultra_modules.google_whisk_subject_bridge_benchmark_suite import WhiskPayloadBuilder, BenchmarkSuite

class TestGoogleWhiskSubjectBridge(unittest.TestCase):

    def setUp(self):
        self.builder = WhiskPayloadBuilder()
        self.benchmark = BenchmarkSuite()

    def test_normal_operation(self):
        """Test normal payload generation."""
        payload = self.builder.build_payload(subject="Alice", style="cyberpunk", scene="neon city")
        self.assertEqual(payload["slots"]["subject"], "Alice")
        self.assertEqual(payload["slots"]["style"], "cyberpunk")
        self.assertEqual(payload["slots"]["scene"], "neon city")
        self.assertTrue(payload["parameters"]["face_lock"])
        self.assertIn("request_id", payload)
        self.assertLess(payload["metadata"]["processing_time_ms"], 50)

    def test_missing_parameter_fallback(self):
        """Test fallback with missing or None parameters."""
        payload = self.builder.build_payload(subject=None, style="", scene="  ")
        self.assertEqual(payload["slots"]["subject"], "default_subject")
        self.assertEqual(payload["slots"]["style"], "realistic")
        self.assertEqual(payload["slots"]["scene"], "studio")

    def test_dirty_data_self_healing(self):
        """Test self healing with incorrect types and garbled data."""
        payload = self.builder.build_payload(subject=12345, style={"not": "string"}, scene=["list"])
        self.assertEqual(payload["slots"]["subject"], "12345")
        self.assertEqual(payload["slots"]["style"], "{'not': 'string'}")
        self.assertEqual(payload["slots"]["scene"], "['list']")

    def test_extreme_boundary_date(self):
        """Test handling of invalid and boundary date formats."""
        payload_invalid = self.builder.build_payload(timestamp="not-a-date")
        self.assertTrue(isinstance(payload_invalid["metadata"]["timestamp"], str))
        self.assertNotEqual(payload_invalid["metadata"]["timestamp"], "not-a-date")

        payload_leap = self.builder.build_payload(timestamp="2024-02-29T23:59:59")
        self.assertEqual(payload_leap["metadata"]["timestamp"], "2024-02-29T23:59:59")

        payload_year_end = self.builder.build_payload(timestamp="2023-12-31T23:59:59")
        self.assertEqual(payload_year_end["metadata"]["timestamp"], "2023-12-31T23:59:59")

    def test_benchmark_concurrency(self):
        """Test running high concurrency synthetic fixtures and zero crashes."""
        result = self.benchmark.run_benchmark(iterations=100)
        self.assertEqual(result["total_iterations"], 100)
        self.assertEqual(result["error_count"], 0)
        self.assertEqual(result["success_count"], 100)
        self.assertLess(result["avg_payload_generation_time_ms"], 50)

    def test_benchmark_with_errors(self):
        """Test running benchmark with simulated error cases."""
        result = self.benchmark.run_benchmark(iterations=10, include_error_cases=True)
        self.assertEqual(result["total_iterations"], 10)
        self.assertGreater(result["error_count"], 0)
        self.assertLess(result["avg_payload_generation_time_ms"], 50)

if __name__ == '__main__':
    unittest.main()
