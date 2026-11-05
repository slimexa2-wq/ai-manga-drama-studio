import unittest
import math
from ultra_modules.ego_dual_cloud_dispatcher_anomaly_radar import analyze_anomalies

class TestEgoDualCloudDispatcherAnomalyRadar(unittest.TestCase):

    def test_normal_execution_top_3_percent(self):
        # 100 tasks, 3 anomalies (high scores), the rest normal
        tasks = [{"id": i, "duration_ms": 100.0} for i in range(97)]
        tasks.append({"id": 97, "duration_ms": 1000.0})
        tasks.append({"id": 98, "duration_ms": 1100.0})
        tasks.append({"id": 99, "duration_ms": 1200.0})

        result = analyze_anomalies(tasks, metric_key="duration_ms", top_percent=3.0)
        self.assertEqual(len(result), 100)

        reds = [t for t in result if t["_anomaly_color"] == "red"]
        self.assertEqual(len(reds), 3)
        self.assertIn("异常偏高", reds[0]["_anomaly_reason"])

        greens_or_yellows = [t for t in result if t["_anomaly_color"] in ["green", "yellow"]]
        self.assertEqual(len(greens_or_yellows), 97)

    def test_dirty_data_self_healing(self):
        tasks = [
            {"id": 1, "duration_ms": 100.0},
            {"id": 2, "duration_ms": 120.0},
            {"id": 3, "duration_ms": "invalid"},
            {"id": 4, "duration_ms": float('nan')},
            {"id": 5}, # missing key
            {"id": 6, "duration_ms": None}
        ]

        result = analyze_anomalies(tasks, metric_key="duration_ms")
        self.assertEqual(len(result), 6)

        dirty_tasks = [result[2], result[3], result[4], result[5]]
        for t in dirty_tasks:
            self.assertEqual(t["_anomaly_color"], "yellow")
            self.assertIn("数据缺失或格式损坏", t["_anomaly_reason"])

    def test_missing_parameter_defaults(self):
        # Call without metric_key or top_percent
        tasks = [{"id": i, "duration_ms": 100.0} for i in range(100)]
        result = analyze_anomalies(tasks)
        self.assertEqual(len(result), 100)
        self.assertTrue(all(t["_anomaly_color"] == "green" for t in result))

    def test_extreme_boundary_conditions(self):
        # Empty list
        self.assertEqual(analyze_anomalies([]), [])

        # List with exactly 1 element
        result1 = analyze_anomalies([{"duration_ms": 100.0}])
        self.assertEqual(len(result1), 1)
        self.assertEqual(result1[0]["_anomaly_color"], "green")

        # List with all identical values
        tasks = [{"duration_ms": 50.0} for _ in range(10)]
        result2 = analyze_anomalies(tasks)
        self.assertEqual(len(result2), 10)
        self.assertTrue(all(t["_anomaly_color"] == "green" for t in result2))

    def test_small_dataset_fallback(self):
        # 5 tasks, Top 3% of 5 is 0, but one is statistically significant anomaly
        tasks = [
            {"id": 1, "duration_ms": 100.0},
            {"id": 2, "duration_ms": 101.0},
            {"id": 3, "duration_ms": 99.0},
            {"id": 4, "duration_ms": 100.0},
            {"id": 5, "duration_ms": 5000.0}  # Anomaly
        ]

        result = analyze_anomalies(tasks)
        self.assertEqual(len(result), 5)

        reds = [t for t in result if t["_anomaly_color"] == "red"]
        self.assertEqual(len(reds), 1)
        self.assertEqual(reds[0]["id"], 5)
        self.assertIn("需排查", reds[0]["_anomaly_reason"])

if __name__ == '__main__':
    unittest.main()
