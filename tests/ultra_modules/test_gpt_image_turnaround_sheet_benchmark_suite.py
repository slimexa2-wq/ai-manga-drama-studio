import unittest
import time
import datetime
from ultra_modules.gpt_image_turnaround_sheet_benchmark_suite import (
    GPTImageTurnaroundGenerator,
    TurnaroundBenchmarkSuite
)

class TestGPTImageTurnaroundSheetBenchmarkSuite(unittest.TestCase):
    def setUp(self):
        self.generator = GPTImageTurnaroundGenerator()
        self.suite = TurnaroundBenchmarkSuite(concurrency=200)

    def test_normal_case(self):
        """Test with standard, valid parameters."""
        res = self.generator.generate_instruction(
            character_desc="a fierce knight with silver armor",
            style="cyberpunk",
            views=["front", "side", "three-quarter"],
            expressions=["determined", "smirking"],
            date_context="2024-05-15"
        )
        self.assertIn("fierce knight", res["prompt"])
        self.assertIn("cyberpunk", res["prompt"])
        self.assertIn("three-quarter", res["prompt"])
        self.assertIn("smirking", res["prompt"])
        self.assertIn("2024-05-15", res["prompt"])
        self.assertEqual(res["model"], "gpt-image-2")

    def test_missing_parameter_fallback(self):
        """Test that missing parameters default correctly (zero-configuration)."""
        res = self.generator.generate_instruction()
        self.assertIn("young adventurer", res["prompt"])
        self.assertIn("Japanese anime style", res["prompt"])
        self.assertIn("front", res["prompt"])
        self.assertIn("neutral", res["prompt"])

        # Test missing but some provided
        res2 = self.generator.generate_instruction(style="watercolor")
        self.assertIn("young adventurer", res2["prompt"])
        self.assertIn("watercolor", res2["prompt"])

    def test_dirty_data_self_healing(self):
        """Test robustness against None, integers, dicts, whitespace, and dirty chars."""
        # 1. Invalid types
        res = self.generator.generate_instruction(
            character_desc=12345,
            style={"invalid": "dict"},
            views="not a list",
            expressions=[None, 123, "   "],
            date_context="not-a-date"
        )
        self.assertIn("12345", res["prompt"])
        self.assertIn("dict", res["prompt"]) # stringified dict
        self.assertIn("front", res["prompt"]) # views fallback
        self.assertIn("neutral", res["prompt"]) # default exprs due to invalid
        # self.assertIn(datetime.datetime.now().strftime("%Y-%m-%d"), res["prompt"]) # Date falls back

        # 2. Extremely dirty string
        dirty_str = "   \x00\x01\x02 \n valid \t \r  \x08"
        res2 = self.generator.generate_instruction(character_desc=dirty_str)
        self.assertIn("valid", res2["parameters"]["character_desc"])

    def test_extreme_boundaries(self):
        """Test extreme boundaries like leap year crossover, end of year."""
        # Leap year valid
        res_leap = self.generator.generate_instruction(date_context="2024-02-29")
        self.assertEqual(res_leap["parameters"]["date_context"], "2024-02-29")

        # Leap year invalid (should fallback)
        res_invalid_leap = self.generator.generate_instruction(date_context="2023-02-29")
        self.assertNotEqual(res_invalid_leap["parameters"]["date_context"], "2023-02-29")

        # Super large string
        huge_string = "a" * 10000
        res_huge = self.generator.generate_instruction(character_desc=huge_string)
        self.assertTrue(res_huge["parameters"]["character_desc"].startswith("aaaa"))
        self.assertEqual(len(res_huge["parameters"]["character_desc"]), 10000)

    def test_super_high_concurrency_benchmark(self):
        """Test high concurrency benchmark to ensure zero crashes and fast response."""
        payload = {
            "character_desc": "test user",
            "style": "test style",
            "views": ["front"],
            "expressions": ["happy"],
            "date_context": "2025-01-01"
        }

        # Simulate 1000 concurrent requests
        stats = self.suite.run_benchmark(payload, count=1000)

        self.assertEqual(stats["total_requests"], 1000)
        self.assertEqual(stats["failures"], 0)
        self.assertEqual(stats["successes"], 1000)
        self.assertEqual(stats["success_rate"], 100.0)
        # It should be extremely fast (millisecond level per request on average)
        self.assertTrue(stats["avg_latency_ms"] < 50, f"Average latency too high: {stats['avg_latency_ms']} ms")
        self.assertGreater(stats["total_time_ms"], 0)

if __name__ == '__main__':
    unittest.main()
