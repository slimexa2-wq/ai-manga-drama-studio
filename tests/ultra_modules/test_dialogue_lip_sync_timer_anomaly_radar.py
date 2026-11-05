import unittest
from ultra_modules.dialogue_lip_sync_timer_anomaly_radar import calculate_expected_duration, scan_anomalies

class TestDialogueLipSyncTimerAnomalyRadar(unittest.TestCase):
    def test_calculate_expected_duration(self):
        self.assertEqual(calculate_expected_duration("你好"), 0.5) # 2 * 0.25
        self.assertEqual(calculate_expected_duration("你好，世界。"), 1.0 + 0.2 + 0.4) # 4*0.25 + 0.2 + 0.4
        self.assertEqual(calculate_expected_duration(None), 0.0)
        self.assertEqual(calculate_expected_duration(123), 0.75) # "123" -> 3 * 0.25

    def test_scan_anomalies_normal(self):
        dialogues = [
            {"text": "你好", "actual_duration": 0.5},
            {"text": "大家好", "actual_duration": 0.75}
        ]
        results = scan_anomalies(dialogues)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "GREEN")
        self.assertEqual(results[1]["status"], "GREEN")

    def test_scan_anomalies_dirty_data_healing(self):
        # 测试缺参、None、类型错误等
        dialogues = [
            "not a dict",
            {"text": None, "actual_duration": "not a number"},
            {"text": 123},
        ]
        results = scan_anomalies(dialogues)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["expected_duration"], 0.0)
        self.assertEqual(results[0]["actual_duration"], 0.0) # 缺参兜底
        self.assertEqual(results[0]["status"], "GREEN")

        self.assertEqual(results[1]["expected_duration"], 0.0)
        self.assertEqual(results[1]["actual_duration"], 0.0) # 兜底到expected
        self.assertEqual(results[1]["status"], "GREEN")

        self.assertEqual(results[2]["expected_duration"], 0.75)
        self.assertEqual(results[2]["actual_duration"], 0.75)
        self.assertEqual(results[2]["status"], "GREEN")

        # Test scan_anomalies non list
        self.assertEqual(scan_anomalies(None), [])

        # Test scan_anomalies convertible string
        res = scan_anomalies([{"text": "你好", "actual_duration": "0.6"}])
        self.assertEqual(res[0]["actual_duration"], 0.6)

    def test_scan_anomalies_outliers(self):
        # 模拟100个数据，其中3个有巨大的diff，应该是RED，另外7个较大的diff是YELLOW
        dialogues = []
        for i in range(100):
            if i < 90:
                dialogues.append({"text": "测试", "actual_duration": 0.5}) # 正常 expected 0.5
            elif i < 97:
                dialogues.append({"text": "测试", "actual_duration": 1.2}) # 差值 0.7，YELLOW (>= 0.5)
            else:
                dialogues.append({"text": "测试", "actual_duration": 3.0}) # 差值 2.5，RED (Top 3%且>=1.0)

        results = scan_anomalies(dialogues)

        red_count = sum(1 for r in results if r["status"] == "RED")
        yellow_count = sum(1 for r in results if r["status"] == "YELLOW")
        green_count = sum(1 for r in results if r["status"] == "GREEN")

        self.assertEqual(red_count, 3)
        self.assertEqual(yellow_count, 7)
        self.assertEqual(green_count, 90)

        for r in results:
            if r["status"] == "RED":
                self.assertIn("长太多了", r["reason"])

    def test_scan_anomalies_short_outlier(self):
        # 模拟极端短的情况
        dialogues = []
        for i in range(100):
            if i < 99:
                dialogues.append({"text": "这是一个很长很长很长的句子，应该需要很多时间来读完。", "actual_duration": 7.0}) # expected 26*0.25+0.2+0.4 = 7.1
            else:
                dialogues.append({"text": "这是一个很长很长很长的句子，应该需要很多时间来读完。", "actual_duration": 1.0}) # 极短

        results = scan_anomalies(dialogues)
        red_item = [r for r in results if r["status"] == "RED"][0]
        self.assertIn("短太多了", red_item["reason"])

    def test_scan_anomalies_small_sample(self):
         dialogues = [
            {"text": "测试", "actual_duration": 0.5},
            {"text": "测试", "actual_duration": 0.5},
            {"text": "测试", "actual_duration": 0.5},
            {"text": "测试", "actual_duration": 2.5}, # > 1.0 + mean+2std
         ]
         results = scan_anomalies(dialogues)
         self.assertEqual(results[3]["status"], "RED")

         # 没有足够大的差距
         dialogues2 = [
            {"text": "测试", "actual_duration": 0.5},
            {"text": "测试", "actual_duration": 0.6},
         ]
         results2 = scan_anomalies(dialogues2)
         self.assertEqual(results2[1]["status"], "GREEN")

if __name__ == '__main__': # pragma: no cover
    unittest.main()
