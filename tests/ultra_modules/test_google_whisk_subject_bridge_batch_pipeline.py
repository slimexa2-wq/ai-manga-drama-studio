import unittest
import time
from ultra_modules.google_whisk_subject_bridge_batch_pipeline import WhiskPayloadBuilder, WhiskBatchPipeline

class TestGoogleWhiskSubjectBridgeBatchPipeline(unittest.TestCase):

    def test_normal_batch_processing(self):
        """测试正常数据批量处理"""
        pipeline = WhiskBatchPipeline()
        items = [
            {"subject": "hero", "style": "anime", "scene": "city"},
            {"subject": "villain", "style": "dark", "scene": "castle"},
        ]

        batch_id = pipeline.submit_batch(items)
        self.assertIsNotNone(batch_id)

        # Wait for processing to complete
        pipeline.shutdown()

        snapshot = pipeline.get_progress_snapshot()
        self.assertEqual(snapshot["total"], 2)
        self.assertEqual(snapshot["completed"], 2)
        self.assertEqual(snapshot["failed"], 0)
        self.assertTrue(snapshot["is_done"])

        results = pipeline.get_results()
        self.assertEqual(len(results), 2)

        subjects = [res["subject"] for res in results]
        self.assertIn("hero", subjects)
        self.assertIn("villain", subjects)

    def test_dirty_data_auto_healing(self):
        """测试脏数据自愈（非字典、非字符串）"""
        pipeline = WhiskBatchPipeline()
        # 脏数据: 整数, None字典，空字典
        items = [
            123,  # 不是字典
            {"subject": 456, "style": None, "scene": []}, # 错误类型
            {} # 空字典
        ]

        pipeline.submit_batch(items)
        pipeline.shutdown()

        results = pipeline.get_results()
        self.assertEqual(len(results), 3)

        # 检查是否正常补全了默认值
        for res in results:
            self.assertEqual(res["style"], "default style")
            self.assertEqual(res["scene"], "default scene")
            self.assertTrue(isinstance(res["subject"], str))

    def test_missing_param_fallbacks(self):
        """测试缺参默认兜底（空字符串，None，缺失键）"""
        payload1 = WhiskPayloadBuilder.build(subject="", style=" ", scene=None)
        self.assertEqual(payload1["subject"], "default subject")
        self.assertEqual(payload1["style"], "default style")
        self.assertEqual(payload1["scene"], "default scene")

        payload2 = WhiskPayloadBuilder.build()
        self.assertEqual(payload2["subject"], "default subject")
        self.assertEqual(payload2["style"], "default style")
        self.assertEqual(payload2["scene"], "default scene")

    def test_extreme_boundary_1000_records(self):
        """测试极端边界：一次性处理 1000 条记录"""
        pipeline = WhiskBatchPipeline(max_workers=50) # 使用更多worker加速测试
        items = [{"subject": f"subject_{i}"} for i in range(1000)]

        pipeline.submit_batch(items)
        pipeline.shutdown()

        snapshot = pipeline.get_progress_snapshot()
        self.assertEqual(snapshot["total"], 1000)
        self.assertEqual(snapshot["completed"], 1000)
        self.assertEqual(snapshot["failed"], 0)
        self.assertTrue(snapshot["is_done"])

        results = pipeline.get_results()
        self.assertEqual(len(results), 1000)

    def test_async_non_blocking_progress(self):
        """测试异步非阻塞和进度快照"""
        pipeline = WhiskBatchPipeline(max_workers=2)
        # 提交大量任务，因为是异步的，提交应立即返回
        items = [{"subject": f"subject_{i}"} for i in range(100)]

        start_time = time.time()
        pipeline.submit_batch(items)
        submit_time = time.time() - start_time

        # 提交时间应该非常短
        self.assertTrue(submit_time < 0.1)

        # 可以在处理过程中获取快照
        snapshot = pipeline.get_progress_snapshot()
        self.assertEqual(snapshot["total"], 100)
        # 此时可能还未完成，也可能完成了一部分
        self.assertFalse(snapshot["is_done"] and snapshot["completed"] == 0)

        pipeline.shutdown()
        final_snapshot = pipeline.get_progress_snapshot()
        self.assertTrue(final_snapshot["is_done"])
        self.assertEqual(final_snapshot["completed"], 100)

if __name__ == '__main__':
    unittest.main()
