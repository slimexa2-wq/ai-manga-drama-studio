import unittest
import math
from ultra_modules.character_dna_seed_locker_anomaly_radar import scan_dna_anomalies, _safe_float

class TestCharacterDnaSeedLockerAnomalyRadar(unittest.TestCase):

    def test_safe_float(self):
        self.assertEqual(_safe_float(1.5), 1.5)
        self.assertEqual(_safe_float(1), 1.0)
        self.assertEqual(_safe_float("2.5"), 2.5)
        self.assertEqual(_safe_float(None), 0.0)
        self.assertEqual(_safe_float("invalid"), 0.0)
        self.assertEqual(_safe_float(float('nan')), 0.0)
        self.assertEqual(_safe_float(float('inf')), 0.0)
        self.assertEqual(_safe_float(object()), 0.0)

    def test_missing_parameters_fallback(self):
        # Should gracefully handle None or empty list
        res_none = scan_dna_anomalies(None)
        self.assertEqual(res_none["status"], "success")
        self.assertEqual(len(res_none["results"]), 0)

        res_empty = scan_dna_anomalies([])
        self.assertEqual(res_empty["status"], "success")
        self.assertEqual(len(res_empty["results"]), 0)

    def test_dirty_data_auto_healing(self):
        # Should heal invalid/missing deviation scores and weird dict structures
        dirty_data = [
            {"deviation_score": "bad_value"}, # invalid string
            {"deviation_score": None},        # None
            "I am a string, not a dict",      # completely wrong type
            {"id": "ep4", "deviation_score": 5.0} # normal
        ]
        res = scan_dna_anomalies(dirty_data)
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["results"]), 4)

        # Check healed values
        # Top score should be 5.0 (the only valid one)
        self.assertEqual(res["results"][0]["deviation_score"], 5.0)
        self.assertEqual(res["results"][0]["id"], "ep4")

        # Others should be 0.0
        self.assertEqual(res["results"][1]["deviation_score"], 0.0)
        self.assertEqual(res["results"][2]["deviation_score"], 0.0)
        self.assertEqual(res["results"][3]["deviation_score"], 0.0)

    def test_normal_operation_and_markers(self):
        # 100 episodes, normal distribution with a few outliers
        # Top 3% = 3 items (Red)
        # Next 7% = 7 items (Yellow)
        # Rest = 90 items (Green)
        data = []
        for i in range(100):
            score = 1.0 + (i % 5) * 0.1 # Normal variance 1.0 - 1.4
            data.append({"id": f"ep_{i}", "deviation_score": score})

        # Inject outliers
        data[10]["deviation_score"] = 9.9 # Red
        data[20]["deviation_score"] = 9.8 # Red
        data[30]["deviation_score"] = 9.7 # Red

        # Next top scores (Yellow)
        data[40]["deviation_score"] = 5.6
        data[50]["deviation_score"] = 5.5
        data[60]["deviation_score"] = 5.4
        data[70]["deviation_score"] = 5.3
        data[80]["deviation_score"] = 5.2
        data[90]["deviation_score"] = 5.1
        data[15]["deviation_score"] = 5.0

        res = scan_dna_anomalies(data)
        results = res["results"]

        self.assertEqual(len(results), 100)

        # Verify counts
        reds = [r for r in results if r["marker"] == "Red"]
        yellows = [r for r in results if r["marker"] == "Yellow"]
        greens = [r for r in results if r["marker"] == "Green"]

        self.assertEqual(len(reds), 3)
        self.assertEqual(len(yellows), 7)
        self.assertEqual(len(greens), 90)

        # Verify plain English reasons
        self.assertIn("严重偏离标准DNA", reds[0]["reason"])
        self.assertIn("轻微偏离标准DNA", yellows[0]["reason"])
        self.assertIn("正常", greens[0]["reason"])

    def test_extreme_boundary_identical_data(self):
        # All items are identical. Standard deviation is 0.
        # No anomalies should be reported.
        data = [{"id": f"ep_{i}", "deviation_score": 2.0} for i in range(50)]
        res = scan_dna_anomalies(data)

        self.assertEqual(res["metrics"]["std_dev"], 0.0)

        results = res["results"]
        reds = [r for r in results if r["marker"] == "Red"]
        yellows = [r for r in results if r["marker"] == "Yellow"]
        greens = [r for r in results if r["marker"] == "Green"]

        self.assertEqual(len(reds), 0)
        self.assertEqual(len(yellows), 0)
        self.assertEqual(len(greens), 50)

    def test_small_sample_size(self):
        # Small sample size (e.g., 2 items)
        data = [{"id": "1", "deviation_score": 10.0}, {"id": "2", "deviation_score": 1.0}]
        res = scan_dna_anomalies(data)

        results = res["results"]
        self.assertEqual(len(results), 2)
        # Because n < 10, top 3% and top 10% logic:
        # top_3_pct_count = max(1, math.ceil(n * 0.03)) if n >= 34 else (1 if n > 0 else 0) -> 1
        # top_10_pct_count = max(1, math.ceil(n * 0.10)) if n >= 10 else (1 if n > 0 else 0) -> 1
        # So top 1 is Red, the rest Green. There is no Yellow if top_10_pct_count == top_3_pct_count
        self.assertEqual(results[0]["marker"], "Red")
        self.assertEqual(results[1]["marker"], "Green")

if __name__ == '__main__':
    unittest.main()
