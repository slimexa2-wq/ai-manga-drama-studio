import unittest
import json
import csv
import io
import os
import tempfile
from unittest.mock import patch
from ultra_modules.golden_3s_hook_splitter_cli_one_click import (
    process_novel_one_click,
    DEFAULT_NOVEL_TEXT,
    main
)

class TestGolden3sHookSplitterCLI(unittest.TestCase):
    def setUp(self):
        self.test_text = "第1章 开始。这本来是一个和平的世界，直到那天，魔王降临了。所有人都在恐慌，只有他站了出来。'我要打十个！'他喊道。"

    def test_01_normal_run_json(self):
        """Test 1: Normal run with explicit parameters (text and JSON format)."""
        result = process_novel_one_click(text=self.test_text, output_format="json")
        data = json.loads(result)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["episode"], 1)
        self.assertTrue("魔王" in data[0]["content"])

    def test_02_missing_parameter_fallback(self):
        """Test 2: Missing parameter fallback (no text provided, defaults to internal text)."""
        # None passed
        result1 = process_novel_one_click(text=None, output_format="json")
        data1 = json.loads(result1)
        self.assertTrue(data1[0]["content"] in DEFAULT_NOVEL_TEXT or DEFAULT_NOVEL_TEXT in data1[0]["content"])

        # Empty string passed
        result2 = process_novel_one_click(text="   \n   ", output_format="json")
        data2 = json.loads(result2)
        self.assertTrue(data2[0]["content"] in DEFAULT_NOVEL_TEXT or DEFAULT_NOVEL_TEXT in data2[0]["content"])

    def test_03_dirty_data_self_healing(self):
        """Test 3: Dirty data self-healing (passing weird spaces, zero-width characters, and edge-case datatypes)."""
        # Weird spaces and zero-width characters
        dirty_text = "这\u200b是\u200c一\u200d段\uFEFF脏  数据\n\n\n测试。"
        result = process_novel_one_click(text=dirty_text, output_format="json")
        data = json.loads(result)
        self.assertEqual(data[0]["content"], "这是一段脏 数据 测试。")

        # Edge-case datatype (integer)
        result_int = process_novel_one_click(text=12345, output_format="json")
        data_int = json.loads(result_int)
        self.assertEqual(data_int[0]["content"], "12345")

        # Unknown format falls back to json
        result_format = process_novel_one_click(text=self.test_text, output_format="unknown_format")
        self.assertTrue(result_format.strip().startswith("["))

    def test_04_excel_csv_dual_mode(self):
        """Test 4: Excel/CSV dual-mode format check (ensure the CSV header and rows match the episodes)."""
        result = process_novel_one_click(text=self.test_text, output_format="csv")
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        self.assertGreater(len(rows), 1)
        self.assertEqual(rows[0], ["集数", "黄金前3秒钩子", "集末悬念", "大白话摘要", "正文内容"])
        self.assertEqual(rows[1][0], "1")

    def test_05_extreme_boundary_and_file_write(self):
        """Test 5: Extreme boundary (CLI output writing fallback and valid file writing)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid file write (JSON)
            json_path = os.path.join(temp_dir, "out.json")
            result = process_novel_one_click(text=self.test_text, output_format="json", output_path=json_path)
            self.assertTrue(os.path.exists(json_path))
            with open(json_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data[0]["episode"], 1)

            # Valid directory write (auto appends filename)
            process_novel_one_click(text=self.test_text, output_format="csv", output_path=temp_dir)
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "auto_export.csv")))

            # Invalid path (simulating failure by pointing to a restricted directory or invalid path format)
            # Will not crash, just silently ignores the failure and returns the string
            invalid_path = "/root/restricted_area/should_fail.json"
            result_invalid = process_novel_one_click(text=self.test_text, output_format="json", output_path=invalid_path)
            self.assertTrue(result_invalid.startswith("["))

    @patch('sys.argv', ['golden_3s_hook_splitter_cli_one_click', '--text', 'CLI测试内容', '--format', 'csv'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_cli(self, mock_stdout):
        """Test CLI main function execution."""
        main()
        output = mock_stdout.getvalue()
        self.assertIn("集数,黄金前3秒钩子", output)
        self.assertIn("CLI测试内容", output)

if __name__ == '__main__':
    unittest.main()
