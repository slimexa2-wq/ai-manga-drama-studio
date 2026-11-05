import unittest
from datetime import datetime, timezone, timedelta
import concurrent.futures
from ultra_modules.google_whisk_subject_bridge_audit_trace import WhiskSubjectBridge, AuditLogger

class TestWhiskSubjectBridge(unittest.TestCase):

    def setUp(self):
        self.bridge = WhiskSubjectBridge()

    def test_normal_case(self):
        """Test case for normal, valid inputs."""
        result = self.bridge.build_payload(
            subject="Hero",
            style="Cyberpunk",
            scene=["City", "Night"]
        )
        payload = result["payload"]
        self.assertEqual(payload["subject"], "Hero")
        self.assertEqual(payload["style"], "Cyberpunk")
        self.assertEqual(payload["scene"], ["City", "Night"])
        self.assertEqual(len(result["audit_trace"]), 0) # No fixes applied

    def test_dirty_data_self_healing(self):
        """Test self-healing logic for dirty data (removing invalid types, stripping whitespace, deduplicating)."""
        result = self.bridge.build_payload(
            subject="  Hero  ", # Needs stripping
            style=12345, # Needs type cast
            scene=["City", "  Night  ", 123, "City", "", None], # Needs stripping, deduplication, type cast, drop empty
            extra_param="dropped" # Unsupported kwarg
        )

        payload = result["payload"]
        self.assertEqual(payload["subject"], "Hero")
        self.assertEqual(payload["style"], "12345")
        self.assertEqual(payload["scene"], ["City", "Night", "123", "None"])
        self.assertNotIn("extra_param", payload)

        trace = result["audit_trace"]
        self.assertGreater(len(trace), 0)
        steps = [log["step"] for log in trace]
        self.assertIn("clean_subject", steps)
        self.assertIn("clean_style", steps)
        self.assertIn("clean_scene", steps)
        self.assertIn("drop_unsupported_kwargs", steps)

    def test_missing_parameter_fallback(self):
        """Test default values for missing parameters."""
        result = self.bridge.build_payload()
        payload = result["payload"]
        self.assertEqual(payload["subject"], "default_subject")
        self.assertEqual(payload["style"], "default_style")
        self.assertEqual(payload["scene"], ["default_scene"])

        trace = result["audit_trace"]
        steps = [log["step"] for log in trace]
        self.assertIn("clean_subject", steps)
        self.assertIn("clean_style", steps)
        self.assertIn("clean_scene", steps)

    def test_cross_year_boundaries_and_scene_types(self):
        """Test edge cases with strings, parsing comma separated scenes."""
        result = self.bridge.build_payload(
            subject=None,
            style="",
            scene="City,  Night , Future  , 2023 ,2024" # Comma separated string scene
        )

        payload = result["payload"]
        self.assertEqual(payload["subject"], "default_subject")
        self.assertEqual(payload["style"], "default_style")
        self.assertEqual(payload["scene"], ["City", "Night", "Future", "2023", "2024"])

        # Test empty string conversion
        res_empty_str = self.bridge.build_payload(scene="  , ,  ")
        self.assertEqual(res_empty_str["payload"]["scene"], ["default_scene"])

        res_none_str = self.bridge.build_payload(scene=[])
        self.assertEqual(res_none_str["payload"]["scene"], ["default_scene"])

        res_single_word = self.bridge.build_payload(scene="singleword")
        self.assertEqual(res_single_word["payload"]["scene"], ["singleword"])

        res_int_scene = self.bridge.build_payload(scene=12345)
        self.assertEqual(res_int_scene["payload"]["scene"], ["12345"])

    def test_extreme_concurrent_execution(self):
        """Test boundary cases using concurrency to ensure thread safety of the core pure function."""
        def run_task(i):
            return self.bridge.build_payload(
                subject=f"Subj_{i}",
                style=f"Style_{i}",
                scene=[f"Scene_{i}", f"Scene_{i}"] # Will be deduplicated
            )

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_task, i) for i in range(100)]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        self.assertEqual(len(results), 100)
        for res in results:
            payload = res["payload"]
            self.assertTrue(payload["subject"].startswith("Subj_"))
            self.assertTrue(payload["style"].startswith("Style_"))
            self.assertEqual(len(payload["scene"]), 1) # Deduplicated
            self.assertTrue(payload["scene"][0].startswith("Scene_"))

            trace = res["audit_trace"]
            steps = [log["step"] for log in trace]
            self.assertIn("clean_scene", steps)

    def test_audit_logger_diff_generation(self):
        """Test that AuditLogger diff generation does not crash on strange inputs."""
        logger = AuditLogger()
        logger.log_step("test_step", {"a": 1}, {"a": 2}, "Reason")
        logs = logger.get_logs()
        self.assertEqual(len(logs), 1)
        self.assertIn("Diff: [{'a': 1}] -> [{'a': 2}]", logs[0]["diff_highlight"])

if __name__ == '__main__':
    unittest.main()
