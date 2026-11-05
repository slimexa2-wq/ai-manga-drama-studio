import unittest
import os
import tempfile
import json
import csv
import shutil
from ultra_modules.dialogue_lip_sync_timer_cli_one_click import DialogueLipSyncTimerCLIOneClick

class TestDialogueLipSyncTimerCLIOneClick(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for output files
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.test_dir)

    def test_normal_execution(self):
        """测试正常参数执行及输出"""
        text = "你好，世界！这是一段测试文本。"
        result = DialogueLipSyncTimerCLIOneClick.process_and_export(
            text=text,
            output_format="all",
            output_dir=self.test_dir
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["text"], text)
        self.assertIn("duration", result)
        self.assertGreater(result["duration"], 0)
        self.assertIn("json", result["exports"])
        self.assertIn("excel", result["exports"])

        # Verify JSON file
        with open(result["exports"]["json"], "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["text"], text)

        # Verify CSV file
        with open(result["exports"]["excel"], "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0], ["Text", "Duration", "Status"])
            self.assertEqual(rows[1][0], text)
            self.assertEqual(rows[1][2], "success")

    def test_missing_parameter_fallback(self):
        """测试缺参兜底：自动使用合理默认值跑通全流程"""
        result = DialogueLipSyncTimerCLIOneClick.process_and_export(
            text=None,
            output_format="json",
            output_dir=self.test_dir
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["text"], "这是一段默认测试文本，包含了标点符号！用于一键跑通测试。")
        self.assertGreater(result["duration"], 0)
        self.assertIn("json", result["exports"])
        self.assertNotIn("excel", result["exports"])

    def test_dirty_data_self_healing(self):
        """测试脏数据自愈：空字符串或非法类型自动恢复"""
        result = DialogueLipSyncTimerCLIOneClick.process_and_export(
            text="   ", # 只有空格
            output_format="excel",
            output_dir=self.test_dir
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["text"], "这是一段默认测试文本，包含了标点符号！用于一键跑通测试。")
        self.assertGreater(result["duration"], 0)
        self.assertIn("excel", result["exports"])
        self.assertNotIn("json", result["exports"])

        result2 = DialogueLipSyncTimerCLIOneClick.process_and_export(
            text=12345, # 传入了数字而非字符串
            output_format="none",
            output_dir=self.test_dir
        )
        self.assertEqual(result2["status"], "success")
        self.assertEqual(result2["text"], "这是一段默认测试文本，包含了标点符号！用于一键跑通测试。")

    def test_extreme_boundary_cases(self):
        """测试极端边界用例：超长文本和仅含标点的文本"""
        # 超长文本
        long_text = "我" * 10000 + "。"
        result_long = DialogueLipSyncTimerCLIOneClick.process_and_export(
            text=long_text,
            output_format="none",
            output_dir=self.test_dir
        )
        self.assertEqual(result_long["status"], "success")
        self.assertGreater(result_long["duration"], 10)

        # 仅含标点
        punct_text = "。。。。！！！？？？"
        result_punct = DialogueLipSyncTimerCLIOneClick.process_and_export(
            text=punct_text,
            output_format="none",
            output_dir=self.test_dir
        )
        self.assertEqual(result_punct["status"], "success")
        self.assertGreater(result_punct["duration"], 0)

    def test_export_formats_and_directory_creation(self):
        """测试导出格式以及目录自动创建逻辑"""
        new_dir = os.path.join(self.test_dir, "nested_dir")

        result = DialogueLipSyncTimerCLIOneClick.process_and_export(
            text="Test directory creation",
            output_format="all",
            output_dir=new_dir
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.exists(os.path.join(new_dir, "dialogue_timing.json")))
        self.assertTrue(os.path.exists(os.path.join(new_dir, "dialogue_timing.csv")))

if __name__ == '__main__':
    unittest.main()
