import unittest

from ultra_modules.google_whisk_subject_bridge_anomaly_radar import scan_and_build_payloads

class TestGoogleWhiskSubjectBridgeAnomalyRadar(unittest.TestCase):
    def test_normal_execution_all_green(self):
        # Setup data with very little variance
        data = [
            {"subject": "boy", "style": "anime", "scene": "school", "value": 10},
            {"subject": "girl", "style": "anime", "scene": "school", "value": 10},
            {"subject": "man", "style": "anime", "scene": "school", "value": 10},
            {"subject": "woman", "style": "anime", "scene": "school", "value": 10},
        ]
        result = scan_and_build_payloads(data)
        self.assertEqual(len(result), 4)
        for p in result:
            self.assertEqual(p["status"], "GREEN")
            self.assertEqual(p["z_score"], 0.0)

    def test_dirty_data_self_healing(self):
        # Pass non-dict items and missing values
        data = [
            "just a string",
            123,
            None,
            {"subject": "valid", "style": "valid", "scene": "valid"},
        ]
        result = scan_and_build_payloads(data)
        self.assertEqual(len(result), 4)
        # Check first item healed
        self.assertEqual(result[0]["subject"], "default_subject")
        self.assertEqual(result[0]["style"], "default_style")
        self.assertEqual(result[0]["scene"], "default_scene")
        # Ensure it falls back to string length for value since value is missing
        expected_len = len("default_subject") + len("default_style") + len("default_scene")
        self.assertEqual(result[0]["value"], float(expected_len))

    def test_missing_parameters_default_fallbacks(self):
        # Empty dict should get defaults
        data = [{}]
        result = scan_and_build_payloads(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["subject"], "default_subject")
        self.assertEqual(result[0]["style"], "default_style")
        self.assertEqual(result[0]["scene"], "default_scene")
        self.assertEqual(result[0]["status"], "GREEN")

    def test_extreme_boundary_conditions_and_red_status(self):
        # Generate enough normal items and one extreme outlier
        data = [{"subject": f"sub{i}", "style": "anime", "scene": "school", "value": 10} for i in range(100)]
        # Add extreme outlier
        data.append({"subject": "outlier", "style": "anime", "scene": "school", "value": 1000})

        result = scan_and_build_payloads(data)
        self.assertEqual(len(result), 101)

        # Check that top 3% (ceil(101*0.03) = 4) include our outlier and it's marked RED
        # Since only one is an extreme outlier, it will have a very high z-score
        red_items = [p for p in result if p["status"] == "RED"]
        self.assertGreaterEqual(len(red_items), 1)
        self.assertEqual(red_items[0]["value"], 1000)
        self.assertTrue("需人工关注" in red_items[0]["reason"])

    def test_empty_and_null_input(self):
        self.assertEqual(scan_and_build_payloads([]), [])
        self.assertEqual(scan_and_build_payloads(None), [])

    def test_iqr_outlier_yellow_status(self):
        # Set up values where one is a slight outlier (yellow) but not top 3% extreme enough if we force top 3%
        # Actually, any IQR outlier not in top 3% or with Z > 1.0 gets YELLOW
        data = [{"value": 10} for _ in range(50)]
        # Add a few slight outliers
        data.extend([{"value": 100}, {"value": 100}, {"value": 100}, {"value": 100}, {"value": 100}])
        # Add one extreme outlier to take up the RED slots
        data.append({"value": 1000})

        result = scan_and_build_payloads(data)
        yellow_items = [p for p in result if p["status"] == "YELLOW"]
        # The 100 values should be yellow because they are IQR outliers and/or Z > 1 but not top 3% (red)
        self.assertGreater(len(yellow_items), 0)
        for y in yellow_items:
            self.assertTrue("轻微波动" in y["reason"])

if __name__ == '__main__':
    unittest.main()
