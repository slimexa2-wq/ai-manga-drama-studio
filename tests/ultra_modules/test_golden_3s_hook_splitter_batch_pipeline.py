import unittest
import time
from ultra_modules.golden_3s_hook_splitter_batch_pipeline import Golden3sHookSplitterBatchPipeline

class TestGolden3sHookSplitterBatchPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = Golden3sHookSplitterBatchPipeline(max_workers=5)

    def test_normal_processing(self):
        """测试正常处理流程：提取黄金前3秒与集末悬念"""
        record = {
            "id": "doc_001",
            "text": "开局获得百亿补贴。这不是做梦吧？他在城市里疯狂购物。最后遇到了一位神秘的老人，老人微笑着对他说...",
            "metadata": {"author": "佚名"}
        }

        result = self.pipeline.process_batch([record])
        self.assertEqual(result["snapshot"]["total"], 1)
        self.assertEqual(result["snapshot"]["successful"], 1)
        self.assertEqual(result["snapshot"]["status"], "completed")

        results = result["results"]
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["success"])
        self.assertEqual(results[0]["id"], "doc_001")

        data = results[0]["data"]
        self.assertEqual(data["status"], "success")
        self.assertTrue(len(data["episodes"]) > 0)

        # 检查第一集的钩子和悬念
        ep0 = data["episodes"][0]
        self.assertIn("golden_3s_hook", ep0)
        self.assertIn("cliffhanger", ep0)
        self.assertTrue(ep0["golden_3s_hook"].startswith("开局获得"))

    def test_dirty_data_self_healing(self):
        """测试脏数据自愈：非字典、数值类型"""
        dirty_records = [
            123456,  # 整数
            3.1415,  # 浮点数
            "这是一段直接传入的文本字符串，不是字典。",
            ["列表不被直接支持，将被强制转换"],
            {"wrong_key_for_text": "no text key"} # 缺失text键
        ]

        result = self.pipeline.process_batch(dirty_records)
        self.assertEqual(result["snapshot"]["total"], 5)
        self.assertEqual(result["snapshot"]["successful"], 5)

        results = result["results"]
        self.assertEqual(len(results), 5)
        for res in results:
            self.assertTrue(res["success"])
            self.assertIsNotNone(res["id"])
            # Some dirty records will successfully heal but end up with empty text, which yields "empty_input"
            self.assertIn(res["data"]["status"], ["success", "empty_input"])

    def test_missing_parameters_fallback(self):
        """测试缺参默认兜底"""
        result_none = self.pipeline.process_batch(None)
        self.assertEqual(result_none["snapshot"]["total"], 0)
        self.assertEqual(result_none["snapshot"]["status"], "completed")
        self.assertEqual(len(result_none["results"]), 0)

        result_empty_dict = self.pipeline.process_batch([{}])
        self.assertEqual(result_empty_dict["snapshot"]["total"], 1)
        res = result_empty_dict["results"][0]
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["status"], "empty_input")
        self.assertEqual(len(res["data"]["episodes"]), 0)

    def test_extreme_edge_cases(self):
        """测试极端边界：非常长的文本和极短的文本"""
        long_text = "极长文本测试" * 10000  # 6万字
        short_text = "啊"

        records = [
            {"id": "long_01", "text": long_text},
            {"id": "short_01", "text": short_text}
        ]

        result = self.pipeline.process_batch(records)
        self.assertEqual(result["snapshot"]["successful"], 2)

        results = {r["id"]: r for r in result["results"]}

        # 长文本检查
        long_res = results["long_01"]
        self.assertTrue(long_res["success"])
        self.assertTrue(long_res["data"]["total_episodes"] >= 5)

        # 短文本检查
        short_res = results["short_01"]
        self.assertTrue(short_res["success"])
        self.assertEqual(short_res["data"]["total_episodes"], 1)
        self.assertEqual(short_res["data"]["episodes"][0]["golden_3s_hook"], "啊")

    def test_high_throughput_batching(self):
        """测试高吞吐批量：100条记录"""
        records = [
            {"id": f"batch_{i}", "text": f"这是第{i}个高并发测试文档，需要提取前三秒钩子和悬念。"}
            for i in range(100)
        ]

        start_time = time.time()
        result = self.pipeline.process_batch(records)
        end_time = time.time()

        self.assertEqual(result["snapshot"]["total"], 100)
        self.assertEqual(result["snapshot"]["successful"], 100)
        self.assertEqual(len(result["results"]), 100)
        self.assertTrue(end_time - start_time < 5.0) # 应该非常快

        # 获取进度快照检查
        batch_id = result["batch_id"]
        snapshot = self.pipeline.get_progress_snapshot(batch_id)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["progress_percentage"], 100.0)

if __name__ == '__main__':
    unittest.main()
