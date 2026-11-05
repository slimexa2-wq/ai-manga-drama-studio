import unittest
import json
from ultra_modules.ego_dual_cloud_dispatcher_plain_explainer import EgoDualCloudDispatcherPlainExplainer

class TestEgoDualCloudDispatcherPlainExplainer(unittest.TestCase):

    def setUp(self):
        self.explainer = EgoDualCloudDispatcherPlainExplainer()

    def test_normal_execution_paths(self):
        """1. 正常执行流: Verify it can correctly process a valid payload."""
        data = {
            "status": "success",
            "task": "生成仙侠剧本第一集",
            "duration_sec": 45.5,
            "models": [
                {"name": "Gemini 1.5 Pro", "status": "success"},
                {"name": "GPT-4o", "status": "success"}
            ]
        }

        md_res = self.explainer.explain(data, "markdown")
        self.assertIn("✅ 成功", md_res)
        self.assertIn("生成仙侠剧本第一集", md_res)
        self.assertIn("45.5 秒", md_res)
        self.assertIn("Gemini 1.5 Pro: 成功", md_res)
        self.assertIn("GPT-4o: 成功", md_res)

        html_res = self.explainer.explain(data, "html")
        self.assertIn("<li> - Gemini 1.5 Pro: 成功</li>", html_res)
        self.assertIn("<div class='summary-card'>", html_res)

        json_res = self.explainer.explain(data, "json")
        json_data = json.loads(json_res)
        self.assertEqual(json_data["overall_status"], "✅ 成功")

    def test_missing_parameter_fallback(self):
        """2. 缺参默认兜底: Verify it gracefully handles empty or partially missing data."""
        data = {}
        res = self.explainer.explain(data, "markdown")
        self.assertIn("❓ 未知状态", res)
        self.assertIn("未指定任务", res)
        self.assertIn("0.0 秒", res)
        self.assertIn("未调用任何模型", res)

        # Test fallback title logic
        custom_explainer = EgoDualCloudDispatcherPlainExplainer(fallback_title=None)
        self.assertEqual(custom_explainer.fallback_title, "任务执行摘要")

    def test_dirty_data_self_healing(self):
        """3. 脏数据自愈: Silently fixing incorrect types, None values, completely invalid payloads."""
        # Intentionally malformed payload
        data = "This is just a string, not a dict"
        res = self.explainer.explain(data, "markdown")
        self.assertIn("❓ 未知状态", res)
        self.assertIn("未指定任务", res)

        # Partially malformed dict
        data_dict = {
            "status": 123, # should be string
            "task": None,
            "duration_sec": "five seconds", # should be float
            "models": "Just one model" # should be list
        }
        res_dict = self.explainer.explain(data_dict, "markdown")
        self.assertIn("❓ 未知状态", res_dict)
        self.assertIn("未指定任务", res_dict)
        self.assertIn("0.0 秒", res_dict)
        self.assertIn("未调用任何模型", res_dict)

    def test_extreme_boundary_cases(self):
        """4. 极端边界: Huge volume of models and extremely long task description."""
        models = [{"name": f"Model-{i}", "status": "success" if i % 2 == 0 else "failed"} for i in range(1000)]
        long_task = "A" * 10000

        data = {
            "status": "PARTIAL",
            "task": long_task,
            "duration_sec": 999999.9,
            "models": models
        }

        res = self.explainer.explain(data, "html")
        self.assertIn("⚠️ 部分成功", res)
        self.assertIn(long_task, res)
        self.assertIn("999999.9 秒", res)
        self.assertIn("Model-0: 成功", res)
        self.assertIn("Model-1: 失败", res)
        self.assertIn("Model-999: 失败", res)
        self.assertEqual(res.count("<li>"), 1000)

    def test_output_format_behavior(self):
        """5. 输出格式退化: Fallback behavior on unsupported output formats."""
        data = {"status": "success", "task": "test", "duration_sec": 1.0, "models": []}

        # Invalid format string
        res = self.explainer.explain(data, "xml")
        self.assertTrue(res.startswith("# 任务执行摘要")) # Defaults to markdown

        # None as format string
        res2 = self.explainer.explain(data, None)
        self.assertTrue(res2.startswith("# 任务执行摘要")) # Defaults to markdown

        # Wrong type as format string
        res3 = self.explainer.explain(data, 123)
        self.assertTrue(res3.startswith("# 任务执行摘要")) # Defaults to markdown

if __name__ == '__main__':
    unittest.main()
