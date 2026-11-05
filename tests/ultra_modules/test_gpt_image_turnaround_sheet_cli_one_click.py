import unittest
import os
import json
import csv
from unittest.mock import patch
from ultra_modules.gpt_image_turnaround_sheet_cli_one_click import (
    get_default_config,
    sanitize_input,
    generate_prompts,
    run_pipeline,
    main
)

class TestGptImageTurnaroundSheet(unittest.TestCase):

    def setUp(self):
        self.prefix = "test_turnaround_output"
        self.json_file = f"{self.prefix}.json"
        self.csv_file = f"{self.prefix}.csv"

    def tearDown(self):
        for file in [self.json_file, self.csv_file]:
            if os.path.exists(file):
                os.remove(file)

    def test_sanitize_input_normal(self):
        """Test normal operation with valid data"""
        input_data = {
            "character_desc": "a wise old wizard",
            "style": "watercolor, fantasy",
            "views": ["front", "side"],
            "expressions": ["laughing"]
        }
        cleaned = sanitize_input(input_data)
        self.assertEqual(cleaned["character_desc"], "a wise old wizard")
        self.assertEqual(cleaned["style"], "watercolor, fantasy")
        self.assertEqual(cleaned["views"], ["front", "side"])
        self.assertEqual(cleaned["expressions"], ["laughing"])

    def test_sanitize_input_missing_parameters_fallback(self):
        """Test missing parameter fallback to defaults"""
        # Empty dictionary
        cleaned = sanitize_input({})
        defaults = get_default_config()
        self.assertEqual(cleaned, defaults)

        # Missing some parameters
        input_data = {
            "character_desc": "a knight"
        }
        cleaned = sanitize_input(input_data)
        self.assertEqual(cleaned["character_desc"], "a knight")
        self.assertEqual(cleaned["style"], defaults["style"])

    def test_sanitize_input_dirty_data_auto_healing(self):
        """Test dirty data auto-healing (e.g. malformed inputs, wrong types)"""
        defaults = get_default_config()

        # Entirely invalid type (integer instead of dict)
        cleaned = sanitize_input(12345)
        self.assertEqual(cleaned, defaults)

        # None input
        cleaned = sanitize_input(None)
        self.assertEqual(cleaned, defaults)

        # Wrong types for individual fields
        input_data = {
            "character_desc": 100,  # Int instead of string
            "style": True,          # Bool instead of string
            "views": "front",       # String instead of list
            "expressions": [1, 2]   # List of ints instead of strings
        }
        cleaned = sanitize_input(input_data)
        self.assertEqual(cleaned["character_desc"], defaults["character_desc"])
        self.assertEqual(cleaned["style"], defaults["style"])
        self.assertEqual(cleaned["views"], defaults["views"])
        self.assertEqual(cleaned["expressions"], defaults["expressions"])

        # List containing a mix of valid and invalid items
        input_data = {
            "views": ["front", 123, "", "back", None]
        }
        cleaned = sanitize_input(input_data)
        self.assertEqual(cleaned["views"], ["front", "back"])

    def test_run_pipeline_execution(self):
        """Test the run pipeline functionality creates files"""
        input_data = {
            "character_desc": "test char",
            "style": "test style",
            "views": ["v1"],
            "expressions": ["e1"]
        }

        output_files = run_pipeline(input_data, output_format='both', output_prefix=self.prefix)

        self.assertIn('json', output_files)
        self.assertIn('csv', output_files)

        self.assertTrue(os.path.exists(self.json_file))
        self.assertTrue(os.path.exists(self.csv_file))

        # Verify JSON
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 2) # 1 turnaround + 1 expression
            self.assertEqual(data[0]["type"], "turnaround_sheet")
            self.assertEqual(data[1]["type"], "expression")

        # Verify CSV
        with open(self.csv_file, 'r', encoding='utf-8-sig') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 2)
            self.assertEqual(reader[0]["type"], "turnaround_sheet")

    def test_run_pipeline_empty_data(self):
        """Test run_pipeline with empty data outputting empty csv"""
        # Hack to test empty data logic for csv
        output_files = run_pipeline(None, output_format='csv', output_prefix=self.prefix)
        self.assertIn('csv', output_files)
        self.assertTrue(os.path.exists(self.csv_file))

        # To test export_to_csv with empty list, let's call it directly
        from ultra_modules.gpt_image_turnaround_sheet_cli_one_click import export_to_csv
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)
        export_to_csv([], self.csv_file)
        self.assertFalse(os.path.exists(self.csv_file))

    @patch('sys.argv', ['script.py', '--format', 'json', '--prefix', 'test_turnaround_output'])
    def test_main_cli_zero_parameter(self):
        """Test CLI with only format and prefix args"""
        main()
        self.assertTrue(os.path.exists(self.json_file))
        # Ensure it generated with default values
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn("a young anime boy", data[0]["prompt"])

    @patch('sys.argv', ['script.py', '--character', 'a dog', '--style', 'realistic', '--views', 'top, bottom', '--expressions', 'barking, sleeping', '--format', 'both', '--prefix', 'test_turnaround_output'])
    def test_main_cli_all_parameters(self):
        """Test CLI with all parameters specified"""
        main()
        self.assertTrue(os.path.exists(self.json_file))
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 3) # 1 turnaround + 2 expressions

            # Check custom turnaround prompt
            self.assertIn("top, bottom", data[0]["prompt"])
            self.assertIn("a dog", data[0]["prompt"])
            self.assertIn("realistic", data[0]["prompt"])

            # Check expression prompt
            self.assertEqual(data[1]["target"], "barking")
            self.assertEqual(data[2]["target"], "sleeping")

    @patch('sys.argv', ['script.py', '--format', 'csv', '--prefix', 'test_turnaround_output'])
    @patch('ultra_modules.gpt_image_turnaround_sheet_cli_one_click.run_pipeline', side_effect=Exception("Test Error"))
    @patch('sys.exit')
    def test_main_cli_exception(self, mock_exit, mock_run_pipeline):
        """Test exception handling in main"""
        main()
        mock_run_pipeline.assert_called_once()
        mock_exit.assert_called_once_with(1)

    def test_extreme_boundary_cases(self):
        """Test boundary cases like empty strings and spaces"""
        input_data = {
            "character_desc": "   ",
            "style": "\t\n",
            "views": [" ", "\t", "valid_view"],
            "expressions": []
        }
        cleaned = sanitize_input(input_data)
        defaults = get_default_config()
        self.assertEqual(cleaned["character_desc"], defaults["character_desc"])
        self.assertEqual(cleaned["style"], defaults["style"])
        self.assertEqual(cleaned["views"], ["valid_view"])
        self.assertEqual(cleaned["expressions"], defaults["expressions"])

if __name__ == '__main__':
    unittest.main()
