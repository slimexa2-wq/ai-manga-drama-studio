import unittest
import json
import csv
import io
from ultra_modules.eight_style_matrix_previewer_cli_one_click import EightStyleMatrixPreviewer

class TestEightStyleMatrixPreviewer(unittest.TestCase):
    def setUp(self):
        self.previewer_json = EightStyleMatrixPreviewer(output_format="json")
        self.previewer_csv = EightStyleMatrixPreviewer(output_format="csv")

    def test_normal_execution_json(self):
        """Test normal execution with standard text input returning JSON."""
        script_text = "男主重生归来，眼神冷冽。"
        result = self.previewer_json.process_one_click(script_text)

        # Verify JSON structure
        data = json.loads(result)
        self.assertEqual(len(data), 8)
        self.assertEqual(data[0]["style"], "修仙 (Xianxia)")
        self.assertIn("男主重生归来", data[0]["prompt"])

    def test_normal_execution_csv(self):
        """Test normal execution returning CSV (acting as Excel adapter)."""
        script_text = "家族破产，唯我独尊。"
        result = self.previewer_csv.process_one_click(script_text)

        # Verify CSV structure
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[1]["style"], "都市逆袭 (Urban Rebirth)")
        self.assertIn("唯我独尊", rows[1]["prompt"])

    def test_dirty_data_self_healing(self):
        """Test that dirty data (extra whitespace, newlines) is self-healed."""
        script_text = "   \n 诡异的规则 \t\n  "
        result = self.previewer_json.process_one_click(script_text)

        data = json.loads(result)
        # Should strip to "诡异的规则"
        self.assertIn("诡异的规则", data[4]["prompt"])
        self.assertNotIn("\n", data[4]["prompt"])

    def test_missing_parameter_fallback(self):
        """Test that missing parameter triggers zero-config fallback to default."""
        result = self.previewer_json.process_one_click(None)

        data = json.loads(result)
        self.assertEqual(len(data), 8)
        self.assertIn("默认极简片段", data[0]["prompt"])

        result2 = self.previewer_json.process_one_click("")
        data2 = json.loads(result2)
        self.assertIn("默认极简片段", data2[0]["prompt"])

    def test_extreme_boundary_cases(self):
        """Test extreme boundary cases like very long strings and unsupported types."""
        # Extremely long string
        long_string = "龙王赘婿" * 1000
        result = self.previewer_json.process_one_click(long_string)
        data = json.loads(result)
        self.assertEqual(len(data), 8)
        self.assertIn("龙王赘婿", data[0]["prompt"])

        # Unsupported type (e.g. integer) handled gracefully due to self-healing/fallback
        previewer = EightStyleMatrixPreviewer()
        result_type = previewer.process_one_click(12345)
        data_type = json.loads(result_type)
        self.assertIn("默认极简片段", data_type[0]["prompt"])

if __name__ == '__main__':
    unittest.main()
