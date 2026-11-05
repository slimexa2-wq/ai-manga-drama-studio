import unittest
from ultra_modules.climax_pacing_analyzer_integration_bridge import ClimaxPacingAnalyzerIntegrationBridge, process_integration_payload

class TestClimaxPacingAnalyzerIntegrationBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = ClimaxPacingAnalyzerIntegrationBridge()

    def test_normal_data_bridge(self):
        """Test bridging of normal v2 data schema."""
        raw_data = {
            "has_curve": True,
            "overall_rating": "Excellent",
            "scores": {
                "suppression": 3,
                "buildup": 2,
                "payoff": 4,
                "suspense": 1
            }
        }

        result = self.bridge.bridge_data(raw_data)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["version"], "v2")
        self.assertTrue(result["analysis"]["has_curve"])
        self.assertEqual(result["analysis"]["overall_rating"], "Excellent")

        scores = result["analysis"]["scores"]
        self.assertEqual(scores["suppression"], 3)
        self.assertEqual(scores["buildup"], 2)
        self.assertEqual(scores["payoff"], 4)
        self.assertEqual(scores["suspense"], 1)

    def test_dirty_data_self_healing(self):
        """Test self-healing with completely corrupted input (e.g., list, string, integer)."""
        # Testing list input
        result1 = process_integration_payload(["corrupted", "list"])
        self.assertEqual(result1["analysis"]["has_curve"], False)
        self.assertEqual(result1["analysis"]["overall_rating"], "Unknown")
        self.assertEqual(result1["analysis"]["scores"]["suppression"], 0)

        # Testing string input
        result2 = process_integration_payload("dirty string")
        self.assertEqual(result2["analysis"]["has_curve"], False)
        self.assertEqual(result2["analysis"]["overall_rating"], "Unknown")

        # Check audit log in self instance
        audit_history = self.bridge.get_audit_history()
        self.bridge.bridge_data(123)
        new_audit = self.bridge.get_audit_history()
        self.assertTrue(any("Dirty data detected" in log for log in new_audit))

    def test_missing_params_fallback(self):
        """Test missing keys, empty dicts, or partially populated payload fallbacks."""
        # Empty dict
        result1 = self.bridge.bridge_data({})
        self.assertEqual(result1["analysis"]["has_curve"], False)
        self.assertEqual(result1["analysis"]["overall_rating"], "Unknown")

        # Partial dict
        result2 = self.bridge.bridge_data({"has_curve": True, "scores": {"buildup": 5}})
        self.assertTrue(result2["analysis"]["has_curve"])
        self.assertEqual(result2["analysis"]["overall_rating"], "Unknown")
        self.assertEqual(result2["analysis"]["scores"]["buildup"], 5)
        self.assertEqual(result2["analysis"]["scores"]["suppression"], 0)
        self.assertEqual(result2["analysis"]["scores"]["payoff"], 0)

    def test_cross_version_schema_mapping(self):
        """Test automatic mapping of old v1 schema fields to v2 fields."""
        old_schema_data = {
            "curve_detected": True,
            "overall_grade": "Good",
            "score_breakdown": {
                "repression_count": 2,
                "charge_count": 3,
                "climax_count": "5",  # Dirty data type coercion test
                "suspense_count": 1
            }
        }

        result = self.bridge.bridge_data(old_schema_data)

        self.assertTrue(result["analysis"]["has_curve"])
        self.assertEqual(result["analysis"]["overall_rating"], "Good")

        scores = result["analysis"]["scores"]
        self.assertEqual(scores["suppression"], 2)
        self.assertEqual(scores["buildup"], 3)
        self.assertEqual(scores["payoff"], 5)  # Auto converted string to int
        self.assertEqual(scores["suspense"], 1)

        logs = self.bridge.get_audit_history()
        self.assertTrue(any("Mapped 'curve_detected' to 'has_curve'" in log for log in logs))
        self.assertTrue(any("Mapped 'overall_grade' to 'overall_rating'" in log for log in logs))

    def test_logger_setup_branch(self):
        """Test the logger handlers branch."""
        import logging
        import importlib
        import ultra_modules.climax_pacing_analyzer_integration_bridge
        logger = logging.getLogger("climax_pacing_bridge_audit")
        logger.addHandler(logging.NullHandler())
        importlib.reload(ultra_modules.climax_pacing_analyzer_integration_bridge)

    def test_extreme_boundary_cases(self):
        """Test with huge datasets, nested dicts with non-ASCII or mixed types."""
        # Extreme boundary case for score types
        mixed_types_data = {
            "has_curve": 1, # will be boolean True
            "overall_rating": None, # Will be casted to "None" string
            "scores": {
                "suppression": None, # Should be ignored (handled by try-except) and fallback to 0
                "buildup": [1,2,3], # Type error, fallback to 0
                "payoff": 2.9, # Valid float but cast to int -> 2
                "suspense_count": "invalid" # Should fallback to 0
            },
            "extra_huge_payload": "a" * 10000 # Ignored by schema conversion
        }

        result = self.bridge.bridge_data(mixed_types_data)
        self.assertTrue(result["analysis"]["has_curve"])
        self.assertEqual(result["analysis"]["overall_rating"], "None")

        scores = result["analysis"]["scores"]
        self.assertEqual(scores["suppression"], 0)
        self.assertEqual(scores["buildup"], 0)
        self.assertEqual(scores["payoff"], 2)
        self.assertEqual(scores["suspense"], 0)

if __name__ == '__main__':
    unittest.main()
