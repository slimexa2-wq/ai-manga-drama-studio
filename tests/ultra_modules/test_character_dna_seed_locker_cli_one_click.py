import unittest
import os
from unittest.mock import patch
import sys
from ultra_modules.character_dna_seed_locker_cli_one_click import (
    sanitize_dna,
    generate_episodes_dna,
    run_pipeline,
    main,
    get_default_dna
)

class TestCharacterDnaSeedLockerCliOneClick(unittest.TestCase):
    def setUp(self):
        self.default_dna = get_default_dna()
        self.test_prefix = "test_character_dna"
        self.json_file = f"{self.test_prefix}.json"
        self.csv_file = f"{self.test_prefix}.csv"

    def tearDown(self):
        if os.path.exists(self.json_file):
            os.remove(self.json_file)
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)

    def test_normal_execution_valid_inputs(self):
        """Test 1: Normal execution with valid inputs."""
        custom_dna = {
            "hair_color": "silver",
            "eye_color": "red",
            "clothing": "armor",
            "style_suffix": "dark fantasy",
            "fixed_seed": 9999
        }
        sanitized = sanitize_dna(custom_dna)
        self.assertEqual(sanitized["hair_color"], "silver")
        self.assertEqual(sanitized["fixed_seed"], 9999)

        dna_list = generate_episodes_dna(sanitized, episodes=5)
        self.assertEqual(len(dna_list), 5)
        self.assertEqual(dna_list[0]["episode"], 1)
        self.assertEqual(dna_list[4]["episode"], 5)

    def test_dirty_data_self_healing(self):
        """Test 2: Dirty data self-healing (invalid types or values)."""
        dirty_dna = {
            "hair_color": 123,  # Invalid type, should fallback
            "eye_color": "   ", # Empty/whitespace string, should fallback
            "clothing": None,   # None, should fallback
            "style_suffix": "custom style", # Valid
            "fixed_seed": "not an int" # Invalid seed string, should fallback
        }
        sanitized = sanitize_dna(dirty_dna)
        self.assertEqual(sanitized["hair_color"], self.default_dna["hair_color"])
        self.assertEqual(sanitized["eye_color"], self.default_dna["eye_color"])
        self.assertEqual(sanitized["clothing"], self.default_dna["clothing"])
        self.assertEqual(sanitized["style_suffix"], "custom style")
        self.assertEqual(sanitized["fixed_seed"], self.default_dna["fixed_seed"])

        # Test boolean for seed (edge case: bool is subclass of int)
        bool_dna = {"fixed_seed": True}
        sanitized_bool = sanitize_dna(bool_dna)
        self.assertEqual(sanitized_bool["fixed_seed"], self.default_dna["fixed_seed"])

    def test_missing_parameter_default_fallback(self):
        """Test 3: Missing parameter default fallback."""
        # Completely empty dict
        sanitized_empty = sanitize_dna({})
        self.assertEqual(sanitized_empty, self.default_dna)

        # Completely invalid input (e.g., list instead of dict)
        sanitized_list = sanitize_dna(["invalid"])
        self.assertEqual(sanitized_list, self.default_dna)

    def test_extreme_boundaries(self):
        """Test 4: Extreme boundaries."""
        # Extremely long string
        long_string = "a" * 10000
        extreme_dna = {
            "hair_color": long_string,
            "fixed_seed": "-12345" # Negative integer string
        }
        sanitized = sanitize_dna(extreme_dna)
        self.assertEqual(sanitized["hair_color"], long_string)
        self.assertEqual(sanitized["fixed_seed"], -12345)

    @patch('sys.argv', ['character_dna_seed_locker_cli_one_click.py', '--prefix', 'test_character_dna'])
    def test_cli_invocation(self):
        """Test 5: CLI invocation with zero configuration (using default arguments)."""
        # Run main to trigger the pipeline
        main()

        # Check if files were created
        self.assertTrue(os.path.exists(self.json_file))
        self.assertTrue(os.path.exists(self.csv_file))

        # Further verify the pipeline function itself
        result_files = run_pipeline(None, 'both', self.test_prefix)
        self.assertIn('json', result_files)
        self.assertIn('csv', result_files)

if __name__ == '__main__':
    unittest.main()
