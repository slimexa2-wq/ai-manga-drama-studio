import unittest
from ultra_modules.character_dna_seed_locker_export_formatter import CharacterDNALockerExportFormatter

class TestCharacterDNALockerExportFormatter(unittest.TestCase):

    def test_normal_execution(self):
        """Test with clean, valid data."""
        locked_dna_list = [
            {
                "character_id": "hero_01",
                "episode_id": "ep_01",
                "hair_color": "black",
                "eye_color": "red",
                "locked_seed": 123456
            },
            {
                "character_id": "hero_01",
                "episode_id": "ep_02",
                "hair_color": "black",
                "eye_color": "red",
                "locked_seed": 789012
            }
        ]

        cleaned_export, report = CharacterDNALockerExportFormatter.format_export(locked_dna_list)

        self.assertEqual(len(cleaned_export), 2)
        self.assertEqual(cleaned_export[0]["character_id"], "hero_01")
        self.assertIn("共锁定 2 组数据", report)
        self.assertIn("涉及 1 个角色", report)
        self.assertIn("2 集", report)
        self.assertEqual(len(report.split('\n')), 3)

    def test_missing_parameter_defaults(self):
        """Test fallback behavior for missing input."""
        # When None is passed
        cleaned_export, report = CharacterDNALockerExportFormatter.format_export(None)

        self.assertEqual(cleaned_export, [])
        self.assertIn("共锁定 0 组数据", report)

        # When invalid type is passed
        cleaned_export, report = CharacterDNALockerExportFormatter.format_export("invalid_string_input")
        self.assertEqual(cleaned_export, [])

    def test_dirty_data_self_healing(self):
        """Test with dirty data like None, NaN strings, non-dict list items, etc."""
        float_nan = float('nan')
        dirty_dna_list = [
            "this_is_not_a_dict_and_should_be_skipped",
            {
                "character_id": "villain_01",
                "episode_id": "ep_03",
                "hair_color": None,  # Should become ""
                "eye_color": " NaN ",  # Should become ""
                "locked_seed": float_nan,  # Should become 0.0
                "nested_data": [None, " nan "], # Should be cleaned recursively
                "nested_dict": {"key": None} # Should be cleaned recursively
            }
        ]

        cleaned_export, report = CharacterDNALockerExportFormatter.format_export(dirty_dna_list)

        self.assertEqual(len(cleaned_export), 1)
        record = cleaned_export[0]
        self.assertEqual(record["hair_color"], "")
        self.assertEqual(record["eye_color"], "")
        self.assertEqual(record["locked_seed"], 0.0)
        self.assertEqual(record["nested_data"], ["", ""])
        self.assertEqual(record["nested_dict"], {"key": ""})

        self.assertIn("共锁定 1 组数据", report)
        self.assertIn("涉及 1 个角色", report)

    def test_extreme_boundary_cases(self):
        """Test extreme boundary cases like empty lists or very large lists."""
        # Empty list
        cleaned_export, report = CharacterDNALockerExportFormatter.format_export([])
        self.assertEqual(cleaned_export, [])

        # Large list
        large_list = [
            {"character_id": f"char_{i}", "episode_id": "ep_01", "val": i}
            for i in range(100)
        ]
        cleaned_export, report = CharacterDNALockerExportFormatter.format_export(large_list)
        self.assertEqual(len(cleaned_export), 100)
        self.assertIn("共锁定 100 组数据", report)
        self.assertIn("涉及 100 个角色", report)
        self.assertIn("1 集", report)

    def test_clean_value_recursive_coverage(self):
        """Specifically ensure 100% branch coverage on _clean_value static method."""
        # Testing list with dict, float nan, none, strings
        val = CharacterDNALockerExportFormatter._clean_value([
            {"key": None},
            float('nan'),
            " NaN ",
            "normal string "
        ])

        self.assertEqual(val, [
            {"key": ""},
            0.0,
            "",
            "normal string"
        ])

        # Testing float that is not NaN
        val2 = CharacterDNALockerExportFormatter._clean_value(3.14)
        self.assertEqual(val2, 3.14)

        # Testing random unsupported type (int)
        val3 = CharacterDNALockerExportFormatter._clean_value(42)
        self.assertEqual(val3, 42)

if __name__ == '__main__':
    unittest.main()
