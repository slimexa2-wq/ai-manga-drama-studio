import unittest
import math
from ultra_modules.multi_role_pitch_tts_export_formatter import TTSExportFormatter

class TestTTSExportFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = TTSExportFormatter()

    def test_normal_flow(self):
        raw_data = [
            {"role": "narrator", "text": "Once upon a time...", "pitch": 0.5, "speed": 1.2, "duration_ms": 1500},
            {"role": "male_lead", "text": "I am here.", "pitch": -2.5, "speed": 1.0, "duration_ms": 1000}
        ]
        formatted, report = self.formatter.format_export(raw_data)

        self.assertEqual(len(formatted), 2)
        self.assertEqual(formatted[0]["pitch"], 0.5)
        self.assertEqual(formatted[0]["comments"], 0)
        self.assertEqual(formatted[1]["speed"], 1.0)

        self.assertIn("2 dialogue lines processed.", report)
        self.assertIn("Total Duration: 2500.0 ms", report)

    def test_dirty_data_self_healing(self):
        raw_data = [
            {"role": "narrator", "text": "Dirty data", "pitch": float('nan'), "speed": None, "duration_ms": None}
        ]
        formatted, report = self.formatter.format_export(raw_data)

        self.assertEqual(len(formatted), 1)
        # Should fallback to default config for narrator
        self.assertEqual(formatted[0]["pitch"], 0.0)
        self.assertEqual(formatted[0]["speed"], 1.0)
        self.assertEqual(formatted[0]["duration_ms"], 0.0)
        self.assertEqual(formatted[0]["comments"], 0)

    def test_missing_parameter_fallback(self):
        raw_data = [
            {"role": "female_lead"}  # missing text, pitch, speed, duration_ms
        ]
        formatted, report = self.formatter.format_export(raw_data)

        self.assertEqual(len(formatted), 1)
        self.assertEqual(formatted[0]["text"], "...")
        self.assertEqual(formatted[0]["pitch"], 2.0)
        self.assertEqual(formatted[0]["speed"], 1.05)
        self.assertEqual(formatted[0]["duration_ms"], 0.0)
        self.assertEqual(formatted[0]["comments"], 0)

    def test_extreme_boundaries(self):
        raw_data = [
            {"role": "villain", "text": "Die!", "pitch": -50.0, "speed": 0.1, "duration_ms": -1000},
            {"role": "male_lead", "text": "Never!", "pitch": 100.0, "speed": 10.0, "duration_ms": 999999}
        ]
        formatted, report = self.formatter.format_export(raw_data)

        self.assertEqual(len(formatted), 2)
        # Pitch clamped between -10.0 and 10.0
        self.assertEqual(formatted[0]["pitch"], -10.0)
        self.assertEqual(formatted[1]["pitch"], 10.0)
        # Speed clamped between 0.5 and 2.0
        self.assertEqual(formatted[0]["speed"], 0.5)
        self.assertEqual(formatted[1]["speed"], 2.0)
        # Duration maxed with 0.0
        self.assertEqual(formatted[0]["duration_ms"], 0.0)
        self.assertEqual(formatted[1]["duration_ms"], 999999.0)

    def test_unknown_role_fallback(self):
        raw_data = [
            {"role": "alien", "text": "We come in peace.", "pitch": 3.0, "speed": 1.5, "duration_ms": 2000}
        ]
        formatted, report = self.formatter.format_export(raw_data)

        self.assertEqual(len(formatted), 1)
        self.assertEqual(formatted[0]["role"], "default")
        self.assertEqual(formatted[0]["pitch"], 3.0)
        self.assertEqual(formatted[0]["speed"], 1.5)
        self.assertEqual(formatted[0]["duration_ms"], 2000.0)

    def test_empty_or_invalid_input(self):
        # Empty list
        formatted, report = self.formatter.format_export([])
        self.assertEqual(len(formatted), 0)
        self.assertIn("0 dialogue lines processed.", report)

        # Invalid elements
        formatted, report = self.formatter.format_export([None, "string", 123])
        self.assertEqual(len(formatted), 0)

if __name__ == '__main__':
    unittest.main()
