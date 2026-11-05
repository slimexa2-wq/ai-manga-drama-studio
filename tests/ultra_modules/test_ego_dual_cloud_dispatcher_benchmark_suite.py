import unittest
import asyncio
import time
from ultra_modules.ego_dual_cloud_dispatcher_benchmark_suite import (
    EgoDualCloudDispatcher,
    SyntheticFixturesBuilder
)

class TestEgoDualCloudDispatcherBenchmarkSuite(unittest.TestCase):

    def setUp(self):
        self.dispatcher = EgoDualCloudDispatcher()

    def test_normal_execution(self):
        """Test normal execution flow."""
        data = SyntheticFixturesBuilder.generate_normal_data()

        async def run_test():
            result = await self.dispatcher.dispatch_task(data)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["processed_task_id"], data["task_id"])
            self.assertEqual(result["provider"], "google")
            self.assertEqual(result["model"], "gemini-3.1-pro")
            self.assertTrue(result["processed_at"] > 0)

        asyncio.run(run_test())

    def test_missing_parameter_fallback(self):
        """Test missing parameter fallback to defaults."""
        data = SyntheticFixturesBuilder.generate_missing_params_data()

        async def run_test():
            result = await self.dispatcher.dispatch_task(data)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["provider"], "google") # Default provider
            self.assertEqual(result["model"], "gemini-3.1-pro") # Default model
            self.assertIsNotNone(result["processed_task_id"])
            self.assertTrue(len(result["processed_task_id"]) > 0)

        asyncio.run(run_test())

    def test_dirty_data_self_healing(self):
        """Test dirty data self-healing and sanitization."""
        data = SyntheticFixturesBuilder.generate_dirty_data()

        async def run_test():
            result = await self.dispatcher.dispatch_task(data)
            self.assertEqual(result["status"], "success")
            self.assertNotEqual(result["processed_task_id"], "invalid-uuid!@#$") # Should be sanitized
            self.assertTrue(result["processed_task_id"].isalnum() or '-' in result["processed_task_id"])
            self.assertEqual(result["provider"], "google") # Fallback to default
            self.assertEqual(result["model"], "gemini-3.1-pro") # Fallback to default model since provider is default
            self.assertEqual(result["result_length"], len("Create a scene ")) # Stripped control chars

        asyncio.run(run_test())

    def test_cross_year_month_boundaries(self):
        """Test cross-year and cross-month boundaries."""
        data = SyntheticFixturesBuilder.generate_cross_boundary_data()

        async def run_test():
            result = await self.dispatcher.dispatch_task(data)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["provider"], "openai")
            self.assertEqual(result["model"], "gpt-4o")
            # Should have the exact same boundary timestamp preserved and result generated
            self.assertEqual(result["processed_task_id"], data["task_id"])

            # Internal test checks timestamp via self._sanitize_and_fill_defaults
            safe_task = self.dispatcher._sanitize_and_fill_defaults(data)
            self.assertEqual(safe_task["timestamp"], data["timestamp"])

        asyncio.run(run_test())

    def test_extreme_concurrency_benchmark(self):
        """Test zero-crash and millisecond response on massive concurrency."""
        batch_size = 10000
        batch = SyntheticFixturesBuilder.generate_massive_concurrency_batch(batch_size)

        start_time = time.time()

        async def run_test():
            results = await self.dispatcher.dispatch_batch(batch)
            self.assertEqual(len(results), batch_size)
            for res in results:
                self.assertEqual(res["status"], "success")

        asyncio.run(run_test())
        end_time = time.time()

        # Benchmark time per request
        total_time = end_time - start_time
        time_per_request_ms = (total_time / batch_size) * 1000

        # We assert it's somewhat fast, definitely shouldn't crash.
        # Allowing some buffer for slow environments, but typically should be << 1ms.
        self.assertTrue(time_per_request_ms < 10, f"Time per request is too slow: {time_per_request_ms} ms")

if __name__ == "__main__":
    unittest.main()
