import unittest
import math
from ultra_modules.climax_pacing_analyzer_anomaly_radar import PacingAnomalyRadar

class TestPacingAnomalyRadar(unittest.TestCase):
    def setUp(self):
        self.radar = PacingAnomalyRadar()

    def test_normal_distribution(self):
        # 正常数据分布，100个点，3个极大异常值
        data = [50.0] * 97 + [100.0, 105.0, 110.0]
        result = self.radar.analyze_pacing(data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 100)

        red_count = sum(1 for r in result["results"] if r["marker"] == "Red")
        green_count = sum(1 for r in result["results"] if r["marker"] == "Green")

        # Top 3% of 100 = 3 anomalies
        self.assertEqual(red_count, 3)
        self.assertEqual(green_count, 97)

        # Check explanations
        for r in result["results"]:
            if r["marker"] == "Red":
                self.assertIn("峰值过高", r["explanation"])
            elif r["marker"] == "Green":
                self.assertIn("静默放行", r["explanation"])

    def test_dirty_data_healing(self):
        # 脏数据自愈
        data = [10.0, "20.0", None, "invalid", math.nan, math.inf, 30.0]
        # Valid data will be: 10.0 (idx 0), 20.0 (idx 1), 30.0 (idx 6)
        result = self.radar.analyze_pacing(data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 3)
        self.assertEqual(result["results"][0]["index"], 0)
        self.assertEqual(result["results"][1]["index"], 1)
        self.assertEqual(result["results"][2]["index"], 6)

    def test_default_fallback_empty_list(self):
        # 缺参默认兜底
        result1 = self.radar.analyze_pacing(None)
        self.assertEqual(result1["status"], "success")
        self.assertEqual(len(result1["results"]), 0)
        self.assertIn("Empty", result1["message"])

        result2 = self.radar.analyze_pacing([])
        self.assertEqual(result2["status"], "success")
        self.assertEqual(len(result2["results"]), 0)

    def test_zero_variance(self):
        # 所有值一样，标准差为0
        data = [10.0, 10.0, 10.0, 10.0, 10.0]
        result = self.radar.analyze_pacing(data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 5)
        # z-scores 均为 0，无异常
        for r in result["results"]:
            self.assertEqual(r["z_score"], 0.0)
            self.assertEqual(r["marker"], "Green")

    def test_statistics_error(self):
        # 触发 statistics.stdev 的 StatisticsError，比如只有两个相同的数
        # 当使用 population standard deviation or generic issues, stdev 抛出 StatisticsError
        # Actually 2 elements is enough for sample stddev unless there's some custom exception.
        # But maybe we can simulate it with a mock or simply passing identical items doesn't raise exception in standard python (it returns 0).
        # We can bypass it using mock to reach 100% coverage, or we can just mock statistics.stdev.
        import statistics
        from unittest.mock import patch

        data = [1.0, 2.0, 3.0]
        with patch('statistics.stdev', side_effect=statistics.StatisticsError("Mock error")):
            result = self.radar.analyze_pacing(data)
            self.assertEqual(result["status"], "success")
            for r in result["results"]:
                self.assertEqual(r["z_score"], 0.0)

    def test_insufficient_data(self):
        # 数据不足2个，无法计算标准差
        data = [5.0]
        result = self.radar.analyze_pacing(data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["marker"], "Green")
        self.assertEqual(result["results"][0]["z_score"], 0.0)
        self.assertIn("不足", result["results"][0]["explanation"])

    def test_extreme_concurrency_or_large_data(self):
        # 极大数量及低谷测试
        data = [50.0] * 970 + [0.0] * 15 + [100.0] * 15 # 15个极低值，15个极高值，Top 3% of 1000 = 30
        result = self.radar.analyze_pacing(data)
        yellow_count = sum(1 for r in result["results"] if r["marker"] == "Yellow")
        red_count = sum(1 for r in result["results"] if r["marker"] == "Red")
        green_count = sum(1 for r in result["results"] if r["marker"] == "Green")

        # Top 3% of 1000 is 30. The 15 low and 15 high should be captured.
        self.assertEqual(yellow_count, 15)
        self.assertEqual(red_count, 15)
        self.assertEqual(green_count, 970)

        for r in result["results"]:
            if r["marker"] == "Yellow":
                self.assertIn("谷值过低", r["explanation"])
            elif r["marker"] == "Red":
                self.assertIn("峰值过高", r["explanation"])

if __name__ == '__main__':
    unittest.main()
