import unittest
import json
import csv
import io
import sys
from unittest.mock import patch
from ultra_modules.google_whisk_subject_bridge_cli_one_click import WhiskPayloadBuilder, cli_main

class TestWhiskPayloadBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = WhiskPayloadBuilder()

    def test_normal_execution(self):
        # 1. 正常执行
        payload = self.builder.build_payload(
            subject="Hero",
            style="Anime",
            scene="City ruins"
        )
        data = payload["whisk_payload"]
        self.assertEqual(data["subject_slot"], "Hero")
        self.assertEqual(data["style_slot"], "Anime")
        self.assertEqual(data["scene_slot"], "City ruins")

        # Test output formats
        json_out = self.builder.export_json(payload)
        self.assertIn('"Hero"', json_out)
        self.assertIn('"Anime"', json_out)

        csv_out = self.builder.export_csv(payload)
        self.assertIn("Hero,Anime,City ruins", csv_out)

    def test_missing_parameter_fallback(self):
        # 2. 缺参默认兜底
        payload = self.builder.build_payload()
        data = payload["whisk_payload"]
        self.assertEqual(data["subject_slot"], "Default Character")
        self.assertEqual(data["style_slot"], "Cinematic, detailed")
        self.assertEqual(data["scene_slot"], "Default Studio Background")

    def test_dirty_data_self_healing(self):
        # 3. 脏数据自愈
        payload = self.builder.build_payload(
            subject="  Messy string  \n",
            style=123,
            scene=None
        )
        data = payload["whisk_payload"]
        self.assertEqual(data["subject_slot"], "Messy string")
        self.assertEqual(data["style_slot"], "123")
        self.assertEqual(data["scene_slot"], "Default Studio Background")

    def test_extreme_boundary_cases(self):
        # 4. 极端边界
        # 传入全空格和极长字符串
        payload = self.builder.build_payload(
            subject="   ",
            style="a" * 10000,
            scene=""
        )
        data = payload["whisk_payload"]
        self.assertEqual(data["subject_slot"], "Default Character") # 空白字符串视为无输入
        self.assertEqual(data["style_slot"], "a" * 10000)
        self.assertEqual(data["scene_slot"], "Default Studio Background")

    @patch('sys.argv', ['cli_main'])
    def test_cli_zero_parameter_invocation(self):
        # 5. CLI零参数一键调用（不报错并返回JSON默认值）
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = cli_main()

            # Verify the result returned
            result_dict = json.loads(result)
            self.assertEqual(result_dict["whisk_payload"]["subject_slot"], "Default Character")

            # Verify the stdout
            stdout_val = mock_stdout.getvalue()
            self.assertIn("Default Character", stdout_val)

    @patch('sys.argv', ['cli_main', '--subject', 'Villain', '--format', 'csv'])
    def test_cli_csv_invocation(self):
        # 额外：CLI调用输出CSV格式
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = cli_main()

            self.assertIn("Villain", result)
            self.assertIn("Cinematic, detailed", result)

            stdout_val = mock_stdout.getvalue()
            self.assertIn("Villain", stdout_val)

if __name__ == "__main__":
    unittest.main()
