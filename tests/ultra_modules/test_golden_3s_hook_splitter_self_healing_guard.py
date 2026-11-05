import unittest
import time
from unittest.mock import patch
from ultra_modules.golden_3s_hook_splitter_self_healing_guard import Golden3sHookSplitterSelfHealingGuard

class TestGolden3sHookSplitterSelfHealingGuard(unittest.TestCase):
    def setUp(self):
        self.guard = Golden3sHookSplitterSelfHealingGuard(max_workers=2, undo_window_seconds=1.0) # short window for testing

    def test_scenario_1_normal_correct_data(self):
        """1. 正常正确数据处理"""
        raw_input = [{"id": "123", "text": "这是一个正常测试字符串。黄金前3秒一定要抓人！之后是悬念..."}]
        result = self.guard.process_with_guard(raw_input)

        self.assertIn("undo_token", result)
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)

        # 验证底层 pipeline 返回成功
        res_data = result["results"][0]
        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["id"], "123")
        self.assertIn("data", res_data)

    def test_scenario_2_dirty_data_self_healing(self):
        """2. 脏数据自愈 (非字符串、奇怪类型)"""
        # 输入数字，布尔，以及格式不对的字典
        raw_input = [12345, True, {"random_key": "value"}]
        result = self.guard.process_with_guard(raw_input)

        self.assertIn("undo_token", result)
        self.assertEqual(len(result["results"]), 3)

        # 12345 应该变成 {"text": "12345", "id": "<uuid>"}
        self.assertTrue(result["results"][0]["success"])
        self.assertTrue(any(len(r["data"].get("episodes", [])) >= 1 for r in result["results"] if r.get("data", {}).get("status") == "success")) # 至少拆出一集

        # Check overall results
        self.assertEqual(sum(1 for r in result["results"] if r["success"]), 3)
        self.assertTrue(any(len(r["data"].get("episodes", [])) == 0 for r in result["results"]))

    def test_scenario_3_missing_parameters_fallback(self):
        """3. 缺参默认兜底 (None 等)"""
        raw_input = None
        result = self.guard.process_with_guard(raw_input)
        self.assertEqual(len(result["results"]), 0) # 空输入不报错

        raw_input_2 = [{"id": None, "text": None}, {}]
        result2 = self.guard.process_with_guard(raw_input_2)
        self.assertEqual(len(result2["results"]), 2)
        for res in result2["results"]:
            self.assertTrue(res["success"])
            self.assertIsNotNone(res["id"]) # 自动生成 UUID

    def test_scenario_4_extreme_boundary_conditions(self):
        """4. 极端边界条件 (极长字符串，完全空字符串)"""
        long_str = "a" * 150000 # 十万字规模
        raw_input = [{"text": long_str}, {"text": ""}]

        result = self.guard.process_with_guard(raw_input)
        self.assertEqual(len(result["results"]), 2)

        # 检查极长字符串是否被成功拆分
        long_res = result["results"][0]
        self.assertTrue(long_res["success"])
        self.assertGreater(len(long_res["data"]["episodes"]), 1)

        # 检查空字符串
        empty_res = result["results"][1]
        self.assertTrue(empty_res["success"])
        self.assertEqual(len(empty_res["data"]["episodes"]), 0)
        self.assertEqual(empty_res["data"]["status"], "empty_input")

    def test_scenario_5_undo_snapshot_functionality(self):
        """5. 5秒一键撤回(Undo)机制快照功能测试"""
        raw_input = [{"id": "999", "text": "即将被撤回的数据"}]

        # 测试正常撤回
        result = self.guard.process_with_guard(raw_input)
        undo_token = result["undo_token"]

        undo_res = self.guard.undo(undo_token)
        self.assertTrue(undo_res["success"])
        self.assertEqual(undo_res["reason"], "restored")
        self.assertEqual(len(undo_res["restored_data"]), 1)
        self.assertEqual(undo_res["restored_data"][0]["text"], "即将被撤回的数据")

        # 重复撤回应该失败（已经清理）
        undo_res_again = self.guard.undo(undo_token)
        self.assertFalse(undo_res_again["success"])
        self.assertEqual(undo_res_again["reason"], "invalid_or_expired_token")

        # 测试超时撤回
        result2 = self.guard.process_with_guard(raw_input)
        undo_token2 = result2["undo_token"]

        # 等待超时 (self.undo_window_seconds 是 1.0)
        time.sleep(1.1)

        undo_res_timeout = self.guard.undo(undo_token2)
        self.assertFalse(undo_res_timeout["success"])
        self.assertEqual(undo_res_timeout["reason"], "invalid_or_expired_token")

    @patch("ultra_modules.golden_3s_hook_splitter_self_healing_guard.Golden3sHookSplitterSelfHealingGuard._extract_hook_and_cliffhanger")
    def test_scenario_6_pipeline_fatal_error(self, mock_process):
        """测试底层提取抛出异常时的静默处理"""
        mock_process.side_effect = Exception("Simulated fatal error")

        raw_input = [{"text": "test"}]
        result = self.guard.process_with_guard(raw_input)

        self.assertIn("undo_token", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertFalse(result["results"][0]["success"])
        self.assertEqual(result["results"][0]["data"]["status"], "error")

    def test_scenario_7_unconvertible_object(self):
        """测试无法转成字典或字符串的奇怪对象"""
        class Unconvertible:
            def __str__(self):
                raise ValueError("cannot cast to string")

        obj = Unconvertible()
        raw_input = [obj]

        # 即使极其奇怪的对象，也要能静默容错（至少不会抛出阻断用户的异常）
        # 这里 str(obj) 会抛错，但在 except Exception 里会有进一步的 fallback 或者它会直接用默认值
        try:
            result = self.guard.process_with_guard(raw_input)
            self.assertTrue(True)
        except Exception:
            self.fail("Should not raise exception on unconvertible objects")

if __name__ == '__main__':
    unittest.main()
