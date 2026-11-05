import unittest
import os
import json
import csv
import sys
from unittest.mock import patch
from ultra_modules.climax_pacing_analyzer_cli_one_click import analyze_pacing, output_adapter, main

class TestClimaxPacingAnalyzer(unittest.TestCase):

    def setUp(self):
        self.output_files = []

    def tearDown(self):
        for file in self.output_files:
            if os.path.exists(file):
                os.remove(file)

    def test_normal_execution(self):
        """Test normal data execution."""
        data = [
            {"chapter": 1, "text": "废柴少年被退婚，受尽屈辱"},
            {"chapter": 2, "text": "获得秘籍，开始闭关修炼"},
            {"chapter": 3, "text": "家族大比一招爆发，疯狂打脸震惊全场"},
            {"chapter": 4, "text": "神秘人出现，不知前途如何危机四伏"}
        ]
        results = analyze_pacing(data)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]["dominant_emotion"], "suppression")
        self.assertEqual(results[1]["dominant_emotion"], "power_gathering")
        self.assertEqual(results[2]["dominant_emotion"], "climax")
        self.assertEqual(results[3]["dominant_emotion"], "suspense")

    def test_missing_parameter_fallback(self):
        """Test zero-parameter/missing-parameter fallback."""
        results = analyze_pacing()
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]["dominant_emotion"], "suppression")
        self.assertEqual(results[1]["dominant_emotion"], "power_gathering")
        self.assertEqual(results[2]["dominant_emotion"], "climax")
        self.assertEqual(results[3]["dominant_emotion"], "suspense")

        results_empty_list = analyze_pacing([])
        self.assertEqual(len(results_empty_list), 4)

    def test_dirty_data_self_healing(self):
        """Test dirty data self-healing and boundary condition."""
        data = [
            "Just a string without dict format",
            {"chapter": "invalid", "text": None},
            {"chapter": 100, "text": 12345},
            None
        ]
        results = analyze_pacing(data)
        self.assertEqual(len(results), 4)

        self.assertEqual(results[0]["chapter"], 1)
        self.assertEqual(results[0]["text"], "Just a string without dict format")

        self.assertEqual(results[1]["chapter"], 2)
        self.assertEqual(results[1]["text"], "")

        self.assertEqual(results[2]["chapter"], 100)
        self.assertEqual(results[2]["text"], "12345")

        self.assertEqual(results[3]["chapter"], 4)
        self.assertEqual(results[3]["text"], "None")

    def test_extreme_boundary(self):
        """Test extreme boundary (non-list primitive input)."""
        data = "This is completely wrong format, just a plain string with 退婚"
        results = analyze_pacing(data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chapter"], 0)
        self.assertEqual(results[0]["text"], "This is completely wrong format, just a plain string with 退婚")
        self.assertEqual(results[0]["dominant_emotion"], "suppression")

    def test_json_and_excel_adapters(self):
        """Test JSON and Excel/CSV output adapters seamlessly."""
        data = analyze_pacing()

        # Test JSON
        json_path = output_adapter(data, "json", "test_output_json")
        self.output_files.append(json_path)
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        self.assertEqual(len(loaded_data), 4)

        # Test CSV/Excel
        csv_path = output_adapter(data, "csv", "test_output_csv")
        self.output_files.append(csv_path)
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            loaded_csv = list(reader)
        self.assertEqual(len(loaded_csv), 4)
        self.assertEqual(loaded_csv[0]["dominant_emotion"], "suppression")

        # Test empty CSV
        empty_csv_path = output_adapter([], "csv", "test_output_empty")
        self.output_files.append(empty_csv_path)
        self.assertTrue(os.path.exists(empty_csv_path))

    def test_main(self):
        """Test main function for 100% coverage."""
        with patch.object(sys, 'argv', ['climax_pacing_analyzer_cli_one_click.py', '--format', 'json', '--output', 'test_main_output']):
            main()
            self.output_files.append("test_main_output.json")
            self.assertTrue(os.path.exists("test_main_output.json"))

        with patch.object(sys, 'argv', ['climax_pacing_analyzer_cli_one_click.py', '--format', 'excel', '--output', 'test_main_output_excel']):
            main()
            self.output_files.append("test_main_output_excel.csv")
            self.assertTrue(os.path.exists("test_main_output_excel.csv"))

if __name__ == "__main__":
    unittest.main()
