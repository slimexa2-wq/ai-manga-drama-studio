import unittest
from ultra_modules.ego_dual_cloud_dispatcher_core_engine import build_dispatch_schedule

class TestEgoDualCloudDispatcherCoreEngine(unittest.TestCase):

    def test_normal_schedule(self):
        tasks = [
            {"id": "t1", "prompt": "Draw a dragon", "target_cloud": "google_ultra"},
            {"id": "t2", "prompt": "Write a story", "target_cloud": "chatgpt_plus"}
        ]
        result = build_dispatch_schedule(tasks)
        self.assertEqual(len(result["google_ultra"]), 1)
        self.assertEqual(result["google_ultra"][0]["id"], "t1")
        self.assertEqual(result["google_ultra"][0]["prompt"], "Draw a dragon")

        self.assertEqual(len(result["chatgpt_plus"]), 1)
        self.assertEqual(result["chatgpt_plus"][0]["id"], "t2")
        self.assertEqual(result["chatgpt_plus"][0]["prompt"], "Write a story")

    def test_dirty_data_self_healing(self):
        # Pass None, non-list, and mixed types in a list
        result1 = build_dispatch_schedule(None)
        self.assertEqual(result1, {"google_ultra": [], "chatgpt_plus": []})

        result2 = build_dispatch_schedule("invalid string")
        self.assertEqual(result2, {"google_ultra": [], "chatgpt_plus": []})

        # Test mixed types and ignore invalid task elements
        tasks = [
            None,
            "not a dict",
            123,
            {"id": "t1", "prompt": "A prompt", "target_cloud": "google_ultra"}
        ]
        result3 = build_dispatch_schedule(tasks)
        self.assertEqual(len(result3["google_ultra"]), 1)
        self.assertEqual(len(result3["chatgpt_plus"]), 0)

    def test_missing_params_default_fallback(self):
        tasks = [
            # Missing ID and prompt, invalid cloud -> uses defaults and generates auto-ID
            {}
        ]
        result = build_dispatch_schedule(tasks, fallback_cloud="chatgpt_plus", default_prompt="fallback prompt")
        self.assertEqual(len(result["chatgpt_plus"]), 1)
        self.assertTrue(result["chatgpt_plus"][0]["id"].startswith("auto-"))
        self.assertEqual(result["chatgpt_plus"][0]["prompt"], "fallback prompt")
        self.assertEqual(result["chatgpt_plus"][0]["target_cloud"], "chatgpt_plus")

    def test_invalid_fallback_cloud_parameter(self):
        tasks = [
            {"id": "t1", "prompt": "hello", "target_cloud": "invalid_cloud"}
        ]
        # Invalid fallback cloud passed into the function itself -> should hardcode to google_ultra
        result = build_dispatch_schedule(tasks, fallback_cloud="some_nonsense")
        self.assertEqual(len(result["google_ultra"]), 1)
        self.assertEqual(len(result["chatgpt_plus"]), 0)

    def test_extreme_boundary_whitespace(self):
        tasks = [
            {
                "id": "   ", # Invalid ID
                "prompt": "   \n\t  ", # Whitespace prompt -> should use default
                "target_cloud": "  chatgpt_plus \n " # Should be stripped and lowercased
            },
            {
                "id": 456, # Int ID -> converts to str
                "prompt": "   Valid prompt   ", # Strips whitespace
                "target_cloud": "GOOGLE_ULTRA" # Lowercases
            }
        ]
        result = build_dispatch_schedule(tasks, default_prompt="default_img")

        # First task goes to chatgpt_plus
        self.assertEqual(len(result["chatgpt_plus"]), 1)
        self.assertTrue(result["chatgpt_plus"][0]["id"].startswith("auto-"))
        self.assertEqual(result["chatgpt_plus"][0]["prompt"], "default_img")

        # Second task goes to google_ultra
        self.assertEqual(len(result["google_ultra"]), 1)
        self.assertEqual(result["google_ultra"][0]["id"], "456")
        self.assertEqual(result["google_ultra"][0]["prompt"], "Valid prompt")

if __name__ == "__main__":
    unittest.main()
