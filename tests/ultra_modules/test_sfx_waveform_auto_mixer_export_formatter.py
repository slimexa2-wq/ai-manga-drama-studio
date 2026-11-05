import unittest
import math
from ultra_modules.sfx_waveform_auto_mixer_export_formatter import (
    clean_data,
    generate_waveform,
    format_export_data
)

class TestSFXWaveformAutoMixerExportFormatter(unittest.TestCase):

    def test_clean_data(self):
        """Test cleaning of dirty data including None and NaN."""
        self.assertEqual(clean_data(None, 10), 10)
        self.assertEqual(clean_data(float('nan'), 20), 20)
        self.assertEqual(clean_data(5, 10), 5)
        self.assertEqual(clean_data("test", "default"), "test")

    def test_generate_waveform_normal(self):
        """Test normal execution for different SFX types."""
        # Heavy bass
        waveform = generate_waveform("heavy_bass", duration=1.0, amplitude=1.0, frequency=60.0)
        self.assertTrue(len(waveform) > 0)
        self.assertTrue(all(isinstance(v, float) for v in waveform))
        self.assertFalse(any(math.isnan(v) for v in waveform))

        # Sword clash
        waveform = generate_waveform("sword_clash", duration=0.5, amplitude=0.8, frequency=2000.0)
        self.assertTrue(len(waveform) > 0)

        # Transition whoosh
        waveform = generate_waveform("transition_whoosh", duration=2.0, amplitude=0.5)
        self.assertTrue(len(waveform) > 0)

    def test_generate_waveform_missing_defaults_and_boundaries(self):
        """Test missing parameter defaults and extreme boundary conditions."""
        # Missing/dirty parameters
        waveform = generate_waveform(None, duration=None, amplitude=float('nan'))
        self.assertTrue(len(waveform) > 0)

        # Extreme boundaries
        waveform_short = generate_waveform("heavy_bass", duration=-10.0) # Should max to 0.1
        self.assertTrue(len(waveform_short) > 0)

        waveform_amp = generate_waveform("sword_clash", amplitude=-5.0) # Should max to 0.0
        self.assertTrue(all(v == 0.0 for v in waveform_amp))

    def test_format_export_data_normal(self):
        """Test format export data with normal inputs."""
        tracks = [
            {"sfx_type": "heavy_bass", "duration": 2.0, "amplitude": 1.0},
            {"sfx_type": "sword_clash", "duration": 1.5, "amplitude": 0.8}
        ]

        export_data, report_text = format_export_data(tracks, "Epic_Battle")

        self.assertEqual(export_data["project_name"], "Epic_Battle")
        self.assertEqual(export_data["comments"], 0)
        self.assertEqual(export_data["total_duration"], 3.5)
        self.assertEqual(len(export_data["tracks"]), 2)

        # Verify no NaN/None in export data tracks
        for track in export_data["tracks"]:
            self.assertIsNotNone(track["sfx_type"])
            self.assertIsNotNone(track["duration"])
            self.assertIsNotNone(track["amplitude"])
            self.assertFalse(any(math.isnan(v) for v in track["waveform"]))

        # Verify 3-line report
        lines = report_text.split('\n')
        self.assertEqual(len(lines), 3)
        self.assertIn("Epic_Battle", lines[0])
        self.assertIn("2", lines[1])
        self.assertIn("3.50", lines[1])

    def test_format_export_data_dirty_and_missing(self):
        """Test format export data with dirty data self-healing and defaults."""
        dirty_tracks = [
            None,
            "invalid_track",
            {"sfx_type": None, "duration": float('nan'), "amplitude": None}
        ]

        export_data, report_text = format_export_data(dirty_tracks, None)

        self.assertEqual(export_data["project_name"], "Untitled_Manga_Drama")
        self.assertEqual(export_data["comments"], 0)
        self.assertEqual(len(export_data["tracks"]), 1)

        track = export_data["tracks"][0]
        self.assertEqual(track["sfx_type"], "default")
        self.assertEqual(track["duration"], 1.0)
        self.assertEqual(track["amplitude"], 1.0)

        lines = report_text.split('\n')
        self.assertEqual(len(lines), 3)

if __name__ == '__main__':
    unittest.main()
