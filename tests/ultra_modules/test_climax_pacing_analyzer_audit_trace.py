import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from ultra_modules.climax_pacing_analyzer_audit_trace import analyze_and_trace

class TestClimaxPacingAnalyzerAuditTrace(unittest.TestCase):
    def test_normal_sequence(self):
        # Case 1: Sequential segments using pacing keywords
        segments = [
            {"text": "主角遭受无尽的压抑", "timestamp": "2023-01-01T10:00:00Z"},
            {"text": "开始疯狂蓄力", "timestamp": "2023-01-01T10:05:00Z"},
            {"text": "终于爆发了，打脸所有人", "timestamp": "2023-01-01T10:10:00Z"},
            {"text": "留下巨大的悬念", "timestamp": "2023-01-01T10:15:00Z"}
        ]
        result = analyze_and_trace(segments)
        self.assertEqual(len(result["segments"]), 4)
        pacing_curve = [s["pacing"] for s in result["segments"]]
        self.assertEqual(pacing_curve, ["oppression", "gathering", "climax", "suspense"])
        self.assertIn("Analyzed 4 segments.", result["summary"])
        self.assertTrue(len(result["_audit_logs"]) >= 0)

    def test_dirty_data(self):
        # Case 2: Dirty Data - Lists containing integers, dicts missing 'text', duplicates
        segments = [
            12345,
            {"timestamp": "2023-01-01T12:00:00Z"}, # Missing text
            "主角爆发了", # String type
            "主角爆发了", # Duplicate
            {"text": "", "timestamp": "2023-01-01T12:05:00Z"} # Empty text
        ]
        result = analyze_and_trace(segments)
        # We have 5 elements:
        # 12345 -> text: '12345'
        # {'timestamp': '2023-01-01T12:00:00Z'} -> missing text -> '默认剧情'
        # '主角爆发了' -> text: '主角爆发了'
        # '主角爆发了' -> duplicate -> removed
        # {'text': '', 'timestamp': '2023-01-01T12:05:00Z'} -> missing text -> '默认剧情' -> duplicate -> removed
        # So we have 3 unique elements.
        self.assertEqual(len(result["segments"]), 3)
        texts = [s["text"] for s in result["segments"]]
        self.assertIn("12345", texts)
        self.assertIn("默认剧情", texts)
        self.assertIn("主角爆发了", texts)
        self.assertTrue(any("heal_type" == log["step"] for log in result["_audit_logs"]))
        self.assertTrue(any("heal_missing_text" == log["step"] for log in result["_audit_logs"]))

    def test_missing_parameters_and_timestamps(self):
        # Case 3: Missing Param - Pass None and ensure reasonable defaults are set
        result = analyze_and_trace(None)
        self.assertEqual(len(result["segments"]), 0)
        self.assertIn("Analyzed 0 segments", result["summary"])
        self.assertTrue(any(log["step"] == "init" for log in result["_audit_logs"]))

        # Also test timestamp branch coverage
        dt = datetime.now()
        dt_utc = datetime.now(timezone.utc)
        result2 = analyze_and_trace([
            {"text": "t1", "timestamp": dt},
            {"text": "t2", "timestamp": dt_utc},
            {"text": "t3", "timestamp": "2023-01-01T12:00:00"},
            {"text": "t4", "timestamp": "invalid_time_string"},
            {"text": "t5"}, # missing timestamp entirely handled by self-healing
            {"text": "t6", "timestamp": ""}
        ])
        self.assertEqual(len(result2["segments"]), 6)

        # Test converting single object to list
        result3 = analyze_and_trace({"text": "single_obj"})
        self.assertEqual(len(result3["segments"]), 1)
        self.assertTrue(any(log["step"] == "init" for log in result3["_audit_logs"]))

    def test_cross_year_boundary(self):
        # Case 4: Cross-year Boundary - Pass segments spanning years out of order
        now = datetime.now(timezone.utc)
        dt_old = now - timedelta(days=400)
        dt_new = now + timedelta(days=400)

        segments = [
            {"text": "悬念未决", "timestamp": dt_new.isoformat()},
            {"text": "遭受屈辱的开始", "timestamp": dt_old.isoformat()},
            {"text": "中期爆发点", "timestamp": now.isoformat()},
        ]
        result = analyze_and_trace(segments)
        self.assertEqual(len(result["segments"]), 3)
        # Should be sorted chronologically
        texts = [s["text"] for s in result["segments"]]
        self.assertEqual(texts, ["遭受屈辱的开始", "中期爆发点", "悬念未决"])
        self.assertTrue(any("sort" == log["step"] for log in result["_audit_logs"]))

    def test_concurrency(self):
        # Case 5: Concurrency - Use ThreadPoolExecutor to run 100 times concurrently
        segments = [{"text": "蓄力", "timestamp": "2023-05-01T10:00:00Z"}]

        def run_task():
            return analyze_and_trace(segments)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_task) for _ in range(100)]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), 100)
        for res in results:
            self.assertEqual(len(res["segments"]), 1)
            self.assertEqual(res["segments"][0]["pacing"], "gathering")

if __name__ == '__main__':
    unittest.main()
