import unittest
from ultra_modules.eight_style_matrix_previewer_audit_trace import EightStyleMatrixPreviewer, STYLES

class TestEightStyleMatrixPreviewer(unittest.TestCase):
    def test_normal_data(self):
        """测试正常数据输入，能够生成8种画风结果并包含审计追踪。"""
        input_data = {"base_prompt": "一个勇敢的少年", "resolution": "1920x1080"}
        result = EightStyleMatrixPreviewer.generate(input_data)

        self.assertIn("frontend_result", result)
        self.assertIn("_audit_trace", result)

        matrix = result["frontend_result"]["matrix"]
        self.assertEqual(len(matrix), 8)

        for idx, style in enumerate(STYLES):
            self.assertEqual(matrix[idx]["style"], style)
            self.assertIn(f"[{style}风格]", matrix[idx]["prompt"])
            self.assertEqual(matrix[idx]["resolution"], "1920x1080")

    def test_missing_parameters_fallback(self):
        """测试缺参默认兜底（零配置容错）。"""
        input_data = {}
        result = EightStyleMatrixPreviewer.generate(input_data)

        matrix = result["frontend_result"]["matrix"]
        base_data = result["frontend_result"]["base_data"]
        audit_trace = result["_audit_trace"]

        # 默认兜底：base_prompt 和 resolution
        self.assertEqual(base_data["base_prompt"], "默认主角")
        self.assertEqual(base_data["resolution"], "1024x1024")

        # 验证审计日志中包含缺参兜底记录
        fallback_logs = [log for log in audit_trace if log["step"] == "fallback_default"]
        self.assertGreaterEqual(len(fallback_logs), 2)

    def test_dirty_data_self_healing(self):
        """测试脏数据自愈（自动修复并静默记录去重/修复依据）。"""
        input_data = {"base_prompt": "   太多     空格的 句子   \t", "resolution": "512x512"}
        result = EightStyleMatrixPreviewer.generate(input_data)

        base_data = result["frontend_result"]["base_data"]
        audit_trace = result["_audit_trace"]

        self.assertEqual(base_data["base_prompt"], "太多 空格的 句子")

        dedup_logs = [log for log in audit_trace if log["step"] == "deduplication"]
        self.assertEqual(len(dedup_logs), 1)
        self.assertEqual(dedup_logs[0]["details"]["action"], "removed extra whitespaces")

    def test_extreme_boundaries(self):
        """测试极端边界输入，如非字典类型（字符串、None等）。"""
        # 测试传入 None
        result_none = EightStyleMatrixPreviewer.generate(None)
        self.assertEqual(result_none["frontend_result"]["base_data"]["base_prompt"], "默认主角")
        type_fix_logs = [log for log in result_none["_audit_trace"] if log["step"] == "type_fix"]
        self.assertEqual(len(type_fix_logs), 1)

        # 测试传入字符串
        result_str = EightStyleMatrixPreviewer.generate("一个奇怪的字符串")
        self.assertEqual(result_str["frontend_result"]["base_data"]["base_prompt"], "一个奇怪的字符串")
        self.assertEqual(result_str["frontend_result"]["base_data"]["resolution"], "1024x1024")

    def test_audit_trace_verification(self):
        """测试后台全链路可追溯审计日志，确保每一步的折算/修复依据都被记录。"""
        input_data = {"base_prompt": "测试用例"}
        result = EightStyleMatrixPreviewer.generate(input_data)

        audit_trace = result["_audit_trace"]

        # 应该至少包含1条缺参兜底(resolution) 和 8条画风折算日志
        fallback_logs = [log for log in audit_trace if log["step"] == "fallback_default"]
        style_transform_logs = [log for log in audit_trace if log["step"] == "style_transformation"]

        self.assertGreaterEqual(len(fallback_logs), 1)
        self.assertEqual(len(style_transform_logs), 8)

        # 验证每个折算日志的高亮对比
        for log in style_transform_logs:
            self.assertIn("diff_highlights", log["details"])
            self.assertIn("added", log["details"]["diff_highlights"])
            added = log["details"]["diff_highlights"]["added"][0]
            style = log["details"]["target_style"]
            self.assertEqual(added, f"[{style}风格] ")

if __name__ == '__main__':
    unittest.main()
