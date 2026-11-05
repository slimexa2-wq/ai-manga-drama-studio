import unittest
import json
from ultra_modules.eight_style_matrix_previewer_plain_explainer import explain_backend_result_to_plain_language

class TestEightStyleMatrixPreviewerPlainExplainer(unittest.TestCase):

    def test_normal_case_success_all_formats(self):
        backend_result = {
            "total": 1,
            "completed": 1,
            "failed": 0,
            "results": [
                {
                    "status": "success",
                    "previews": {
                        "修仙": "预览内容A",
                        "都市逆袭": "预览内容B"
                    }
                }
            ]
        }

        # JSON format
        res_json = explain_backend_result_to_plain_language(backend_result, "json")
        parsed_json = json.loads(res_json)
        self.assertEqual(parsed_json["title"], "8大画风对比一键摘要")
        self.assertIn("成功为您生成了 1 条内容的画风对比", parsed_json["summary"])
        self.assertEqual(len(parsed_json["styles"]), 2)
        self.assertIn("【修仙】: 预览内容A", parsed_json["styles"])

        # Markdown format
        res_md = explain_backend_result_to_plain_language(backend_result, "markdown")
        self.assertIn("# 8大画风对比一键摘要", res_md)
        self.assertIn("**摘要**：成功为您生成了 1 条内容", res_md)
        self.assertIn("- 【修仙】: 预览内容A", res_md)

        # HTML format
        res_html = explain_backend_result_to_plain_language(backend_result, "html")
        self.assertIn("<h1>8大画风对比一键摘要</h1>", res_html)
        self.assertIn("<strong>摘要</strong>：成功为您生成了 1 条内容", res_html)
        self.assertIn("<li>【修仙】: 预览内容A</li>", res_html)

    def test_dirty_data_and_missing_params(self):
        # Missing params (None)
        res1 = json.loads(explain_backend_result_to_plain_language(None))
        self.assertEqual(res1["title"], "结果为空")
        self.assertEqual(res1["summary"], "系统处理中或遇到未知数据，建议重新提交一次。")

        # Dirty data (String instead of dict)
        res2 = json.loads(explain_backend_result_to_plain_language("dirty_string_data"))
        self.assertEqual(res2["title"], "结果为空")

        # Missing total, completed, failed
        res3 = json.loads(explain_backend_result_to_plain_language({"results": []}))
        self.assertEqual(res3["title"], "暂无处理任务")

        # Format fallback (invalid format type)
        res4 = explain_backend_result_to_plain_language(None, 123)
        # 123 is invalid, falls back to JSON
        parsed_res4 = json.loads(res4)
        self.assertEqual(parsed_res4["title"], "结果为空")

    def test_partial_failure_case(self):
        backend_result = {
            "total": 3,
            "completed": 2,
            "failed": 1,
            "results": [
                {
                    "status": "success",
                    "previews": {"修仙": "预览A"}
                },
                {
                    "status": "failed",
                    "error": "Timeout"
                },
                {
                    "status": "success",
                    "previews": {"末日生存": "预览B"}
                }
            ]
        }
        res = json.loads(explain_backend_result_to_plain_language(backend_result))
        self.assertIn("成功为您生成了 2 条", res["summary"])
        self.assertIn("其中有 1 条处理失败", res["summary"])
        self.assertEqual(len(res["styles"]), 2)
        self.assertIn("【末日生存】: 预览B", res["styles"])

    def test_all_failed_case(self):
        backend_result = {
            "total": 2,
            "completed": 0,
            "failed": 2,
            "results": [
                {"status": "failed", "error": "Error1"},
                {"status": "failed", "error": "Error2"}
            ]
        }
        res = json.loads(explain_backend_result_to_plain_language(backend_result))
        self.assertEqual(res["title"], "任务处理失败")
        self.assertIn("抱歉，提交的 2 个任务未能成功生成对比", res["summary"])
        self.assertEqual(len(res["styles"]), 0)

    def test_extreme_edge_cases(self):
        # Empty results array but completed is > 0
        backend_result1 = {
            "total": 1,
            "completed": 1,
            "failed": 0,
            "results": []
        }
        res1 = json.loads(explain_backend_result_to_plain_language(backend_result1))
        self.assertEqual(len(res1["styles"]), 0)
        self.assertIn("一秒钟浏览如下", res1["summary"])

        # Results is not a list
        backend_result2 = {
            "total": 1,
            "completed": 1,
            "failed": 0,
            "results": "not_a_list"
        }
        res2 = json.loads(explain_backend_result_to_plain_language(backend_result2))
        self.assertEqual(len(res2["styles"]), 0)

        # Previews is not a dict
        backend_result3 = {
            "total": 1,
            "completed": 1,
            "failed": 0,
            "results": [{"status": "success", "previews": "not_a_dict"}]
        }
        res3 = json.loads(explain_backend_result_to_plain_language(backend_result3))
        self.assertEqual(len(res3["styles"]), 0)

if __name__ == '__main__':
    unittest.main()
