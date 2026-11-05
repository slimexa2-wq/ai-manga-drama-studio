import unittest
import time
from ultra_modules.ego_dual_cloud_dispatcher_batch_pipeline import EgoDualCloudDispatcherBatchPipeline

class TestEgoDualCloudDispatcherBatchPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = EgoDualCloudDispatcherBatchPipeline(max_workers=5)

    def tearDown(self):
        # Shutdown the executor to prevent thread leakage across tests, but wait for tasks to finish
        self.pipeline._executor.shutdown(wait=True)

    def test_01_normal_processing(self):
        """测试正常数据单次批量处理10条记录"""
        records = [{"task_id": f"t_{i}", "prompt": f"test prompt {i}", "model": "imagen-4"} for i in range(10)]
        batch_id = self.pipeline.submit_batch(records)

        # 等待后台执行完成
        time.sleep(0.5)

        snapshot = self.pipeline.get_progress_snapshot(batch_id)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["status"], "completed")
        self.assertEqual(snapshot["total"], 10)
        self.assertEqual(snapshot["completed"], 10)
        self.assertEqual(snapshot["failed"], 0)
        self.assertEqual(len(snapshot["results"]), 10)

    def test_02_dirty_data_self_healing(self):
        """测试脏数据自愈（过滤非字典或异常格式数据）"""
        records = [
            {"task_id": "valid_1", "prompt": "good"},
            None,
            "invalid_string_record",
            ["list_record"],
            {"task_id": "valid_2", "prompt": "good2"}
        ]

        batch_id = self.pipeline.submit_batch(records)

        # 等待后台执行完成
        time.sleep(0.2)

        snapshot = self.pipeline.get_progress_snapshot(batch_id)
        self.assertEqual(snapshot["total"], 2) # 只剩下2条有效数据
        self.assertEqual(snapshot["completed"], 2)

    def test_03_missing_parameter_fallbacks(self):
        """测试缺参默认兜底机制"""
        records = [
            {}, # 完全空参数
            {"prompt": ""}, # prompt为空字符串
            {"model": 123}, # model类型错误
            {"task_id": "t_no_params"}
        ]

        batch_id = self.pipeline.submit_batch(records)
        time.sleep(0.3)

        snapshot = self.pipeline.get_progress_snapshot(batch_id)
        self.assertEqual(snapshot["total"], 4)

        for res in snapshot["results"]:
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["prompt"], "Auto-generated default scene")
            self.assertEqual(res["model"], "gpt-4o")
            self.assertTrue("task_id" in res)
            self.assertTrue("result_url" in res)

    def test_04_extreme_boundary_handling(self):
        """测试极端边界：超过1000条数据应被静默截断"""
        records = [{"prompt": f"test {i}"} for i in range(1050)]
        batch_id = self.pipeline.submit_batch(records)

        # 为了不阻塞测试太久，稍微等待一下
        time.sleep(0.1)
        snapshot = self.pipeline.get_progress_snapshot(batch_id)
        # 立即查看应被截断
        self.assertEqual(snapshot["total"], 1000)

    def test_05_error_resilience(self):
        """测试单条任务出错不阻塞整体进度"""
        records = [
            {"prompt": "good"},
            {"prompt": "raise_error"}, # 这条会触发内部异常
            {"prompt": "good"}
        ]
        batch_id = self.pipeline.submit_batch(records)

        time.sleep(0.2)
        snapshot = self.pipeline.get_progress_snapshot(batch_id)
        self.assertEqual(snapshot["status"], "completed")
        self.assertEqual(snapshot["total"], 3)
        self.assertEqual(snapshot["completed"], 2)
        self.assertEqual(snapshot["failed"], 1)

if __name__ == '__main__':
    unittest.main()
