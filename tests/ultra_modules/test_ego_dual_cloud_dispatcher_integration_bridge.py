import unittest
import asyncio
from ultra_modules.ego_dual_cloud_dispatcher_integration_bridge import (
    SchemaForwardCompatibilityConverter,
    EgoDualCloudDispatcher
)

class TestEgoDualCloudDispatcherIntegrationBridge(unittest.TestCase):

    def setUp(self):
        self.dispatcher = EgoDualCloudDispatcher(max_workers=2)

    def tearDown(self):
        self.dispatcher.shutdown()

    # 1. Normal Mapping Tests
    def test_normal_mapping_and_routing_chatgpt(self):
        payload = {
            "prompt": "Create a manga panel",
            "model": "gpt-4o",
            "provider": "openai",
            "params": {"temperature": 0.7}
        }

        # Test schema converter
        mapped = SchemaForwardCompatibilityConverter.map_payload(payload)
        self.assertEqual(mapped["prompt"], "Create a manga panel")
        self.assertEqual(mapped["model"], "gpt-4o")
        self.assertEqual(mapped["provider"], "chatgpt_plus")
        self.assertEqual(mapped["params"], {"temperature": 0.7})

        # Test dispatcher (sync internal)
        result = self.dispatcher._sync_dispatch_task(payload)
        self.assertEqual(result["status"], "success")
        self.assertIn("ChatGPT Plus", result["result"])

    def test_normal_mapping_and_routing_google(self):
        payload = {
            "text_prompt": "Create another panel",
            "model_name": "gemini-3.1-pro",
            "cloud": "google",
            "config": {"top_p": 0.9}
        }

        mapped = SchemaForwardCompatibilityConverter.map_payload(payload)
        self.assertEqual(mapped["prompt"], "Create another panel")
        self.assertEqual(mapped["model"], "gemini-3.1-pro")
        self.assertEqual(mapped["provider"], "google_ultra")
        self.assertEqual(mapped["params"], {"top_p": 0.9})

        result = self.dispatcher._sync_dispatch_task(payload)
        self.assertEqual(result["status"], "success")
        self.assertIn("Google Ultra", result["result"])

    # 2. Dirty Data Self-Healing
    def test_dirty_data_self_healing(self):
        # Payload is a string instead of dict
        payload = "this is just a string, totally wrong"
        mapped = SchemaForwardCompatibilityConverter.map_payload(payload)
        self.assertEqual(mapped["prompt"], "generate a default creative media")
        self.assertEqual(mapped["model"], "auto-default-model")
        self.assertEqual(mapped["provider"], "auto")
        self.assertEqual(mapped["params"], {})

        # Payload has wrong types for fields
        payload2 = {
            "prompt": 12345,
            "model": ["not", "a", "string"],
            "provider": {"wrong": "type"},
            "params": "not a dict"
        }
        mapped2 = SchemaForwardCompatibilityConverter.map_payload(payload2)
        self.assertEqual(mapped2["prompt"], "generate a default creative media")
        self.assertEqual(mapped2["model"], "auto-default-model")
        self.assertEqual(mapped2["provider"], "auto")
        self.assertEqual(mapped2["params"], {})

    # 3. Missing Defaults Fallbacks
    def test_missing_defaults(self):
        # Completely empty payload
        payload = {}
        mapped = SchemaForwardCompatibilityConverter.map_payload(payload)
        self.assertEqual(mapped["prompt"], "generate a default creative media")
        self.assertEqual(mapped["model"], "auto-default-model")
        self.assertEqual(mapped["provider"], "auto")
        self.assertEqual(mapped["params"], {})

        # Test dispatcher handles auto-routing when provider is missing/auto
        result = self.dispatcher._sync_dispatch_task(payload)
        self.assertEqual(result["status"], "success")
        self.assertIn("Auto-Routed", result["result"])

    # 4. Extreme Boundary Cases (Empty strings, spaces, concurrency with many tasks)
    def test_extreme_boundaries_and_spaces(self):
        payload = {
            "prompt": "   ",
            "model": " \t ",
            "provider": "\n",
            "params": {}
        }
        mapped = SchemaForwardCompatibilityConverter.map_payload(payload)
        # Should fallback to defaults if strings are empty after strip
        self.assertEqual(mapped["prompt"], "generate a default creative media")
        self.assertEqual(mapped["model"], "auto-default-model")
        self.assertEqual(mapped["provider"], "auto")

    def test_async_orchestrate_concurrent_tasks_extreme(self):
        async def run_async():
            # Test with invalid payloads parameter (string instead of list)
            invalid_payloads = "not a list"
            results = []
            async for res in self.dispatcher.async_orchestrate_concurrent_tasks(invalid_payloads):
                results.append(res)

            # The invalid string gets wrapped into a list ['not a list'],
            # which then goes to _sync_dispatch_task where map_payload handles the string as dirty data
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["status"], "success")

            # Test with a large batch of empty payloads
            large_batch = [{}] * 50
            results = []
            async for res in self.dispatcher.async_orchestrate_concurrent_tasks(large_batch):
                results.append(res)

            self.assertEqual(len(results), 50)
            for res in results:
                self.assertEqual(res["status"], "success")

        asyncio.run(run_async())

    # 5. Exception handling boundary
    def test_dispatch_exception_tolerance(self):
        # Monkey patch map_payload to raise an exception to test dispatcher's tolerance
        original_map = SchemaForwardCompatibilityConverter.map_payload

        def mock_error_map(payload):
            raise ValueError("Intentional crash")

        SchemaForwardCompatibilityConverter.map_payload = staticmethod(mock_error_map)

        try:
            result = self.dispatcher._sync_dispatch_task({"prompt": "test"})
            self.assertEqual(result["status"], "error")
            self.assertIn("Intentional crash", result["error"])
        finally:
            # Restore
            SchemaForwardCompatibilityConverter.map_payload = staticmethod(original_map)

    def test_async_orchestrate_exception_tolerance(self):
        # Test exception catching in async_orchestrate_concurrent_tasks when the future itself fails

        # We'll submit a mock task that raises an exception before it can even run,
        # or we mock loop.run_in_executor to return a future that fails.
        async def run_async():
            loop = asyncio.get_running_loop()
            original_run = loop.run_in_executor

            def mock_run_in_executor(executor, func, *args):
                future = asyncio.Future()
                future.set_exception(RuntimeError("Future failed"))
                return future

            loop.run_in_executor = mock_run_in_executor

            try:
                results = []
                async for res in self.dispatcher.async_orchestrate_concurrent_tasks([{"prompt": "test"}]):
                    results.append(res)

                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]["status"], "error")
                self.assertIn("Future failed", results[0]["error"])
            finally:
                loop.run_in_executor = original_run

        asyncio.run(run_async())

    def test_provider_auto(self):
        payload = {
            "provider": "unknown_provider"
        }
        mapped = SchemaForwardCompatibilityConverter.map_payload(payload)
        self.assertEqual(mapped["provider"], "auto")

if __name__ == '__main__':
    unittest.main()
