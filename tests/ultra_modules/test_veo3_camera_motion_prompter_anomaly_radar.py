import unittest
from ultra_modules.veo3_camera_motion_prompter_anomaly_radar import Veo3CameraMotionPrompterAnomalyRadar

class TestVeo3CameraMotionPrompterAnomalyRadar(unittest.TestCase):

    def test_normal_data_silent_pass(self):
        """Test normal execution where valid parameters are passed silently."""
        data = [
            {"subject": "a peaceful lake", "motion": "pan", "speed": 1.0},
            {"subject": "a dark forest", "motion": "tilt", "speed": 1.2},
            {"subject": "a busy city street", "motion": "tracking", "speed": 1.5},
            {"subject": "an empty desert", "motion": "static", "speed": 1.0},
            {"subject": "a mountain peak", "motion": "crane", "speed": 0.8},
        ]
        results = Veo3CameraMotionPrompterAnomalyRadar.compile_and_scan(data)
        self.assertEqual(len(results), 5)
        # Verify the normal item is passed silently with green marker
        for res in results:
            self.assertIn("[Veo 3 / Sora 2 Optimized]", res["compiled_prompt"])
            self.assertFalse(res["requires_attention"])
            self.assertIn(res["marker"], ["🟢", "🟡"])

    def test_missing_parameter_fallback(self):
        """Test zero-configuration auto-fallback for missing parameters or None input."""
        results_none = Veo3CameraMotionPrompterAnomalyRadar.compile_and_scan(None)
        self.assertEqual(len(results_none), 1)
        self.assertIn("A Highly Detailed Cinematic Shot", results_none[0]["compiled_prompt"])
        self.assertIn("Cinematic Pan", results_none[0]["compiled_prompt"])

        results_empty_dict = Veo3CameraMotionPrompterAnomalyRadar.compile_and_scan([{}])
        self.assertEqual(len(results_empty_dict), 1)
        self.assertIn("A Highly Detailed Cinematic Shot", results_empty_dict[0]["compiled_prompt"])

    def test_dirty_data_self_healing(self):
        """Test self-healing mechanisms for dirty or incorrectly typed data."""
        data = [
            "Just a string subject",
            {"subject": 12345, "speed": "fast", "motion": None},
            {"subject": "valid subject", "speed": float("nan"), "motion": ["invalid", "list"]}
        ]
        results = Veo3CameraMotionPrompterAnomalyRadar.compile_and_scan(data)
        self.assertEqual(len(results), 3)

        # Checking first item
        self.assertIn("Just A String Subject", results[0]["compiled_prompt"])

        # Checking second item (subject coerced to string, speed fallback to 1.0, motion fallback)
        self.assertIn("12345", results[1]["compiled_prompt"])
        self.assertIn("1.0x speed", results[1]["compiled_prompt"])
        self.assertIn("Cinematic Pan", results[1]["compiled_prompt"])

        # Checking third item (NaN speed fallback to 1.0, invalid motion fallback)
        self.assertIn("Valid Subject", results[2]["compiled_prompt"])
        self.assertIn("1.0x speed", results[2]["compiled_prompt"])

    def test_extreme_boundary_cases_anomalies(self):
        """Test extreme boundary cases that trigger anomaly detection (top 3% highlighting)."""
        # Generate 100 normal prompts
        data = [{"subject": f"normal subject {i}", "speed": 1.0, "motion": "pan"} for i in range(100)]

        # Inject one extreme anomaly that should trigger the top 3% Z-Score/IQR outlier detection
        data.append({
            "subject": "extreme " * 100,
            "speed": 50.0,
            "motion": "extreme zoom dolly"
        })

        results = Veo3CameraMotionPrompterAnomalyRadar.compile_and_scan(data)
        self.assertEqual(len(results), 101)

        # Find the anomaly
        anomaly = results[-1]
        self.assertTrue(anomaly["requires_attention"])
        self.assertEqual(anomaly["marker"], "🔴")
        self.assertIn("人工重点核查", anomaly["reason"])

    def test_empty_list_input(self):
        """Test passing an empty list."""
        results = Veo3CameraMotionPrompterAnomalyRadar.compile_and_scan([])
        self.assertEqual(len(results), 1)
        self.assertIn("A Highly Detailed Cinematic Shot", results[0]["compiled_prompt"])

if __name__ == '__main__':
    unittest.main()
