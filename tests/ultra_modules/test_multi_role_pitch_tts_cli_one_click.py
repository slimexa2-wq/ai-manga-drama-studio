import unittest
import json
import csv
import io
from ultra_modules.multi_role_pitch_tts_cli_one_click import MultiRolePitchTTSEngine, run_cli_one_click

class TestMultiRolePitchTTS(unittest.TestCase):
    def setUp(self):
        self.engine = MultiRolePitchTTSEngine()

    def test_normal_operation(self):
        # Normal inputs
        data = [
            {"role": "narrator", "text": "Once upon a time."},
            {"role": "male_lead", "text": "I will protect you.", "pitch": 0.9, "speed": 1.0, "emotion": "determined"}
        ]
        results = self.engine.process_and_align(data)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["role"], "narrator")
        self.assertEqual(results[1]["role"], "male_lead")
        self.assertEqual(results[1]["emotion"], "determined")

        self.assertTrue(results[0]["end_ms"] > results[0]["start_ms"])
        self.assertEqual(results[1]["start_ms"], results[0]["end_ms"])
        self.assertEqual(results[1]["end_ms"], results[1]["start_ms"] + results[1]["duration_ms"])

    def test_dirty_data_auto_healing(self):
        # Dirty data with invalid pitch, speed, missing role, etc.
        data = [
            {"text": "Just some text without role."}, # no role
            {"role": 123, "text": "Invalid role type"}, # invalid role
            {"role": "female_lead", "text": "invalid pitch and speed", "pitch": "high", "speed": -1.5},
            "Just a string instead of dict", # not a dict
            None # none object
        ]
        results = self.engine.process_and_align(data)
        self.assertEqual(len(results), 5)

        # item 0
        self.assertEqual(results[0]["role"], "narrator")

        # item 1
        self.assertEqual(results[1]["role"], "unknown")

        # item 2
        self.assertEqual(results[2]["role"], "female_lead")
        self.assertEqual(results[2]["pitch"], self.engine.role_defaults["female_lead"]["pitch"])
        self.assertEqual(results[2]["speed"], self.engine.role_defaults["female_lead"]["speed"])

        # item 3
        self.assertEqual(results[3]["role"], "narrator")
        self.assertEqual(results[3]["text"], "Just a string instead of dict")

        # item 4 (None converted to empty string text which defaults to "...")
        self.assertEqual(results[4]["role"], "narrator")
        self.assertEqual(results[4]["text"], "...")

    def test_missing_parameter_fallbacks(self):
        # Using run_cli_one_click without parameters
        output = run_cli_one_click()
        data = json.loads(output)

        self.assertEqual(len(data), 4)

        self.assertEqual(data[0]["role"], "narrator")
        self.assertEqual(data[1]["role"], "male_lead")
        # Ensure fast speed string healed to default
        self.assertEqual(data[1]["speed"], self.engine.role_defaults["male_lead"]["speed"])

        self.assertEqual(data[2]["role"], "villain")
        self.assertEqual(data[2]["text"], "...")
        self.assertEqual(data[2]["pitch"], self.engine.role_defaults["villain"]["pitch"])

        self.assertEqual(data[3]["role"], "unknown")
        self.assertEqual(data[3]["text"], "Who am I?")

    def test_extreme_boundary_edge_cases(self):
        # Empty list, None input, single dict input
        res1 = self.engine.process_and_align([])
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]["text"], "Default story begins...")

        res2 = self.engine.process_and_align(None)
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0]["text"], "Default story begins...")

        res3 = self.engine.process_and_align({"role": "narrator", "text": "Single object."})
        self.assertEqual(len(res3), 1)
        self.assertEqual(res3[0]["text"], "Single object.")

    def test_excel_csv_adapter_mode(self):
        # Test formatting output to CSV
        output = run_cli_one_click(output_format="csv")
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Header + 4 data rows from default run_cli_one_click
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0], ["Role", "Text", "Pitch", "Speed", "Emotion", "Start(ms)", "End(ms)", "Duration(ms)"])
        self.assertEqual(rows[1][0], "narrator")
        self.assertEqual(rows[2][0], "male_lead")

    def test_format_output_fallbacks(self):
        results = self.engine.process_and_align([])
        out_json1 = self.engine.format_output(results, output_format="invalid_format")
        out_json2 = self.engine.format_output(results, output_format=123)
        out_json3 = self.engine.format_output(results, output_format=None)

        self.assertTrue(out_json1.startswith("["))
        self.assertTrue(out_json2.startswith("["))
        self.assertTrue(out_json3.startswith("["))

if __name__ == "__main__":
    unittest.main()
