import unittest
import math
from ultra_modules.karaoke_ass_subtitle_burner_anomaly_radar import KaraokeAssSubtitleBurnerAnomalyRadar

class TestKaraokeAssSubtitleBurnerAnomalyRadar(unittest.TestCase):

    def test_scan_and_mark_normal_cases(self):
        """Test normal data flow and Top 3% tagging logic."""
        subtitles = [
            {"text": f"Subtitle {i}", "duration": 1.0} for i in range(100)
        ]
        # Inject one abnormally fast and one abnormally slow
        subtitles[50] = {"text": "Very long subtitle text that is too fast", "duration": 0.1}
        subtitles[60] = {"text": "Slow", "duration": 10.0}

        results = KaraokeAssSubtitleBurnerAnomalyRadar.scan_and_mark(subtitles)

        self.assertEqual(len(results), 100)

        # At least one should be flagged
        flagged = [r for r in results if r["status"] != "Green"]
        self.assertTrue(len(flagged) > 0)
        self.assertTrue(len(flagged) <= math.ceil(100 * 0.03))  # At most 3% (3 items)

        # Check reasons
        has_fast = any("闪现过快" in r["reason"] for r in flagged)
        has_slow = any("停留过长" in r["reason"] for r in flagged)
        self.assertTrue(has_fast or has_slow)

    def test_dirty_data_self_healing(self):
        """Test dirty data self-healing: None, non-dict, non-string text, NaN/invalid duration."""
        subtitles = [
            None,
            123,
            "just a string",
            {"text": None, "duration": -5},
            {"text": {"dict": "as_text"}, "duration": float('nan')},
            {"text": "missing duration"}
        ]

        results = KaraokeAssSubtitleBurnerAnomalyRadar.scan_and_mark(subtitles)
        self.assertEqual(len(results), len(subtitles))
        for res in results:
            self.assertEqual(res["status"], "Green") # since list is small (<100) and variance might be zero, or it triggers fallback
            self.assertIn("正常放行", res["reason"])
            self.assertIsInstance(res["text"], str)

    def test_ffmpeg_command_generation_fallbacks(self):
        """Test missing parameter default fallbacks for FFmpeg command generation."""
        cmd = KaraokeAssSubtitleBurnerAnomalyRadar.generate_ffmpeg_burn_command()
        self.assertIn("default_in.mp4", cmd)
        self.assertIn("default_sub.ass", cmd)
        self.assertIn("default_out.mp4", cmd)
        self.assertIn("-vf \"ass='default_sub.ass'\"", cmd)

    def test_ffmpeg_command_generation_existing_vf_and_escaping(self):
        """Test FFmpeg command with existing -vf filters and tricky path escaping."""
        existing_vf = "scale=1920:1080, format=yuv420p"
        cmd = KaraokeAssSubtitleBurnerAnomalyRadar.generate_ffmpeg_burn_command(
            input_video="in.mp4",
            ass_file="C:\\path\\with:colon\\and'quote.ass",
            output_video="out.mp4",
            existing_vf=existing_vf
        )

        self.assertIn("-i \"in.mp4\"", cmd)
        self.assertIn("\"out.mp4\"", cmd)

        # Ensure it didn't duplicate -vf but appended
        self.assertIn("-vf \"scale=1920:1080, format=yuv420p, ass=", cmd)

        # Check escaping
        escaped_path = r"C\:\\path\\with\:colon\\and\'quote.ass"
        self.assertIn(escaped_path, cmd)

    def test_extreme_boundary_cases_empty_and_single(self):
        """Test extreme boundary cases like empty lists or single item (concurrency safety proxy)."""
        self.assertEqual(KaraokeAssSubtitleBurnerAnomalyRadar.scan_and_mark([]), [])

        res_single = KaraokeAssSubtitleBurnerAnomalyRadar.scan_and_mark([{"text": "Hello", "duration": 2.0}])
        self.assertEqual(len(res_single), 1)
        self.assertEqual(res_single[0]["status"], "Green")

    def test_iqr_zero_division_fallback(self):
        """Test when IQR is 0 to avoid zero division errors."""
        subtitles = [
            {"text": "Same speed", "duration": 1.0},
            {"text": "Same speed", "duration": 1.0},
            {"text": "Same speed", "duration": 1.0},
            {"text": "Same speed", "duration": 1.0},
        ]
        results = KaraokeAssSubtitleBurnerAnomalyRadar.scan_and_mark(subtitles)
        self.assertEqual(len(results), 4)
        for res in results:
            self.assertEqual(res["status"], "Green")

    def test_red_and_yellow_severity(self):
        """Test logic that splits RED vs YELLOW."""
        subtitles = [
            {"text": f"Normal {i}", "duration": 1.0} for i in range(100)
        ]
        # High deviation (>3.0) -> RED
        subtitles[50] = {"text": "EXTREME", "duration": 0.001}
        # Moderate deviation (>1.0 but <=3.0) -> YELLOW
        subtitles[51] = {"text": "MODERATE fast but not too fast string", "duration": 0.5}

        results = KaraokeAssSubtitleBurnerAnomalyRadar.scan_and_mark(subtitles)

        # We need to find at least one red
        statuses = [r["status"] for r in results]
        self.assertIn("Red", statuses)

if __name__ == "__main__":
    unittest.main()
