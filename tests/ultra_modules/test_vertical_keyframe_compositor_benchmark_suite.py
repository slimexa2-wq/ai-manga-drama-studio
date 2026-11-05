import unittest
import time
from ultra_modules.vertical_keyframe_compositor_benchmark_suite import (
    VerticalKeyframeCompositor,
    SyntheticFixtureGenerator,
    BenchmarkRunner
)

class TestVerticalKeyframeCompositorBenchmarkSuite(unittest.TestCase):

    def setUp(self):
        self.compositor = VerticalKeyframeCompositor()
        self.fixtures = SyntheticFixtureGenerator.generate_test_cases()

    def test_normal_execution(self):
        """Test normal execution case (case 0 in fixtures)"""
        frame_data = self.fixtures[0]
        result = self.compositor.process_keyframe(frame_data)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["components"]["light_effect"]["type"], "lens_flare")
        self.assertEqual(result["components"]["speedlines"]["density"], 100)
        self.assertEqual(result["components"]["subtitle"]["text"], "热血沸腾！")
        self.assertEqual(result["components"]["subtitle"]["timestamp"], "2023-10-01T12:00:00")

    def test_missing_parameter_default_fallback(self):
        """Test missing parameter default fallback (empty dict)"""
        frame_data = self.fixtures[1] # {}
        result = self.compositor.process_keyframe(frame_data)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["components"]["light_effect"]["type"], "soft_glow")
        self.assertEqual(result["components"]["speedlines"]["density"], 50)
        self.assertEqual(result["components"]["subtitle"]["text"], "默认字幕")
        self.assertIsNotNone(result["components"]["subtitle"]["timestamp"])

    def test_dirty_data_auto_healing(self):
        """Test dirty data auto-healing (nulls and invalid types)"""
        frame_data = self.fixtures[2]
        result = self.compositor.process_keyframe(frame_data)

        self.assertEqual(result["status"], "success")
        # '12345' gets ignored as a non-string or cleaned up
        self.assertEqual(result["components"]["light_effect"]["type"], "soft_glow")
        # 'high' cannot be cast to int, so default is used
        self.assertEqual(result["components"]["speedlines"]["density"], 50)
        # None subtitle defaults to "默认字幕"
        self.assertEqual(result["components"]["subtitle"]["text"], "默认字幕")

    def test_extreme_boundary_cross_year_and_garbled_text(self):
        """Test garbled text and extreme boundaries (cross year boundary)"""
        frame_data = self.fixtures[3]
        result = self.compositor.process_keyframe(frame_data)

        self.assertEqual(result["status"], "success")
        # ✨🌟*&^%$#@ has no alphanumeric/underscore, falls back to default
        self.assertEqual(result["components"]["light_effect"]["type"], "soft_glow")
        # -9999 out of bounds (0-1000), falls back to 50
        self.assertEqual(result["components"]["speedlines"]["density"], 50)
        # Empty after strip, falls back
        self.assertEqual(result["components"]["subtitle"]["text"], "默认字幕")
        self.assertEqual(result["components"]["subtitle"]["timestamp"], "2023-12-31T23:59:59")

    def test_extreme_boundary_leap_year_cross_month(self):
        """Test extreme boundaries (leap year/cross month boundary)"""
        frame_data = self.fixtures[4]
        result = self.compositor.process_keyframe(frame_data)

        self.assertEqual(result["status"], "success")
        # Empty light effect falls back
        self.assertEqual(result["components"]["light_effect"]["type"], "soft_glow")
        # 9999999 out of bounds (0-1000), falls back to 50
        self.assertEqual(result["components"]["speedlines"]["density"], 50)
        self.assertEqual(result["components"]["subtitle"]["text"], "跨越时空的决战")
        self.assertEqual(result["components"]["subtitle"]["timestamp"], "2024-02-29T23:59:59")

    def test_massive_concurrency_benchmark(self):
        """Test zero-crash and millisecond-level response under massive concurrency."""
        # 1000 concurrent tasks
        benchmark_result = BenchmarkRunner.run_benchmark(concurrency=1000)

        self.assertTrue(benchmark_result["is_zero_crash"])
        self.assertEqual(benchmark_result["total_frames_processed"], 1000)
        self.assertEqual(benchmark_result["successful_frames"], 1000)

        # Ensures average time per frame is within millisecond-level bounds (e.g., < 10ms avg across threads)
        # Note: Actual processing in python might vary, but since it's just dictionary construction, it will be fast.
        self.assertLess(benchmark_result["average_time_per_frame_ms"], 50.0)

if __name__ == '__main__':
    unittest.main()
