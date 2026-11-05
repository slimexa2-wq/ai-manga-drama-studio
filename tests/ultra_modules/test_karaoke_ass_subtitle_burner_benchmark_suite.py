import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import subprocess
from ultra_modules.karaoke_ass_subtitle_burner_benchmark_suite import (
    generate_karaoke_ass,
    burn_subtitles,
    SyntheticBenchmarkSuite
)

class TestKaraokeAssSubtitleBurnerBenchmarkSuite(unittest.TestCase):

    def test_normal_operation(self):
        subtitles = [{
            "start": 0,
            "end": 1000,
            "words": [
                {"word": "Hello", "start": 0, "end": 500},
                {"word": "World", "start": 500, "end": 1000}
            ]
        }]
        result = generate_karaoke_ass(subtitles)
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:01.00", result)
        self.assertIn("{\\k50}{\\t(0,200,\\fscx120\\fscy120)}Hello", result)
        self.assertIn("{\\k50}{\\t(0,200,\\fscx120\\fscy120)}World", result)

    def test_dirty_data_self_healing(self):
        subtitles = [
            None,
            "Invalid",
            {
                "start": "abc", # Invalid type
                "end": None,    # Null
                "words": "not_a_list"
            },
            {
                "start": 0,
                "end": 1000,
                "words": [
                    None,
                    {"word": ""}, # Missing word entirely or empty
                    {"word": "Healed", "start": "x", "end": "y"}
                ]
            }
        ]
        result = generate_karaoke_ass(subtitles)
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:01.00", result)
        self.assertIn("Healed", result)

    def test_missing_parameter_fallbacks(self):
        subtitles = [{"text": "Just text", "start": 1000, "end": 2000}]
        # No words provided, falls back to raw text
        result = generate_karaoke_ass(subtitles, options={"font_name": "CustomFont", "font_size": 72})
        self.assertIn("Style: KaraokeDefault,CustomFont,72", result)
        self.assertIn("Just text", result)

    def test_extreme_boundaries(self):
        suite = SyntheticBenchmarkSuite()
        cross_year_ds = suite.generate_cross_year_dataset()
        result = generate_karaoke_ass(cross_year_ds)
        # Year timestamp 31536000000ms is approx 8760 hours
        self.assertIn("8760:00:00.00", result)

        # Negative timestamp should be clamped to 0
        self.assertIn("0:00:00.00,0:00:01.00", result)

        # Inverted timestamps should be self-corrected (end = start + 1000)
        self.assertIn("0:00:05.00,0:00:06.00", result)

        # Benchmark massive concurrent dataset to ensure no crash and fast response
        massive_ds = suite.generate_massive_concurrent_dataset(size=1000)
        avg_time = suite.run_benchmark(massive_ds, iterations=1)
        self.assertGreater(avg_time, 0)
        # Assuming it completes under 500ms for 1000 records
        self.assertLess(avg_time, 500)

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_burn_subtitles_ffmpeg(self, mock_exists, mock_run):
        mock_exists.return_value = True

        # Test Success
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(burn_subtitles("dummy.mp4", "dummy.ass", "out.mp4"))

        # Test subprocess exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg")
        self.assertFalse(burn_subtitles("dummy.mp4", "dummy.ass", "out.mp4"))

        # Test Timeout
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 60)
        self.assertFalse(burn_subtitles("dummy.mp4", "dummy.ass", "out.mp4"))

        # Test missing files
        mock_exists.return_value = False
        self.assertFalse(burn_subtitles("dummy.mp4", "dummy.ass", "out.mp4"))

if __name__ == '__main__':
    unittest.main()
