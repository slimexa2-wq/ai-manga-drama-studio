import unittest
import time
from ultra_modules.vertical_keyframe_compositor_batch_pipeline import (
    RenderConfig,
    RenderTask,
    VerticalKeyframeCompositorBatchPipeline
)

class TestVerticalKeyframeCompositorBatchPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = VerticalKeyframeCompositorBatchPipeline(max_workers=20)

    def tearDown(self):
        self.pipeline.shutdown()

    def test_normal_batch_processing(self):
        """Test normal operation with valid inputs (10 records)."""
        tasks = [RenderTask(task_id=f"t_{i}", image_data=f"img_{i}", subtitle="hello", subtitle_color="#FF0000") for i in range(10)]
        config = RenderConfig(width=1080, height=1920, enable_light_effects=True, enable_speed_lines=False)

        batch_id = self.pipeline.submit_batch(tasks, config)
        self.assertIsNotNone(batch_id)

        results = self.pipeline.wait_for_completion(batch_id)
        self.assertEqual(len(results), 10)

        snapshot = self.pipeline.get_progress_snapshot(batch_id)
        self.assertTrue(snapshot.is_done)
        self.assertEqual(snapshot.successful, 10)
        self.assertEqual(snapshot.failed, 0)

        # Verify output formatting
        res0 = [r for r in results if r.task_id == "t_0"][0]
        self.assertTrue(res0.success)
        self.assertIn("Rendered(1080x1920): img_0", res0.output_data)
        self.assertIn("LightEffects", res0.output_data)
        self.assertNotIn("SpeedLines", res0.output_data)
        self.assertIn("DoubleStrokeSubtitle('hello', color=#FF0000)", res0.output_data)

    def test_dirty_data_self_healing(self):
        """Test how the pipeline handles invalid/dirty data by self-healing or falling back."""
        # Mix of valid and invalid objects
        tasks = [
            RenderTask(task_id="t1", image_data="valid"),
            "string_instead_of_task_object", # Dirty: Not a RenderTask
            None, # Dirty: None object
            RenderTask(task_id="t2", image_data="simulated_fatal_error") # Dirty: causes internal exception
        ]

        batch_id = self.pipeline.submit_batch(tasks) # Uses default config
        results = self.pipeline.wait_for_completion(batch_id)

        self.assertEqual(len(results), 4)

        # Verify specific handling
        success_count = sum(1 for r in results if r.success)
        fail_count = sum(1 for r in results if not r.success)

        self.assertEqual(success_count, 3)
        self.assertEqual(fail_count, 1) # The "simulated_fatal_error" should be caught

        snapshot = self.pipeline.get_progress_snapshot(batch_id)
        self.assertEqual(snapshot.successful, 3)
        self.assertEqual(snapshot.failed, 1)
        self.assertTrue(snapshot.is_done)

    def test_missing_params_default_fallback(self):
        """Test default parameters kick in when initialized with missing/invalid params."""
        # 1. Invalid config params
        config = RenderConfig(width=-500, height="not_an_int", enable_light_effects=None)
        self.assertEqual(config.width, 1080)
        self.assertEqual(config.height, 1920)
        self.assertFalse(config.enable_light_effects)

        # 2. Invalid task params
        task = RenderTask(task_id="", image_data=None, subtitle_color="red") # color must start with #
        self.assertNotEqual(task.task_id, "") # UUID generated
        self.assertEqual(task.image_data, "default_blank_image")
        self.assertEqual(task.subtitle_color, "#FFFFFF") # Fallback to #FFFFFF

        batch_id = self.pipeline.submit_batch([task], config)
        results = self.pipeline.wait_for_completion(batch_id)
        self.assertTrue(results[0].success)

    def test_extreme_boundaries_empty_and_large(self):
        """Test empty batch and very large batch (1000 items)."""
        # Empty batch
        batch_id_empty = self.pipeline.submit_batch([])
        snapshot = self.pipeline.get_progress_snapshot(batch_id_empty)
        self.assertTrue(snapshot.is_done)
        self.assertEqual(snapshot.total, 0)

        results_empty = self.pipeline.wait_for_completion(batch_id_empty)
        self.assertEqual(len(results_empty), 0)

        # Large batch
        tasks = [RenderTask(task_id=f"big_{i}", image_data=f"x") for i in range(1000)]
        batch_id_large = self.pipeline.submit_batch(tasks)

        # Immediate check (might be 0 or small number done)
        snapshot = self.pipeline.get_progress_snapshot(batch_id_large)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.total, 1000)

        results_large = self.pipeline.wait_for_completion(batch_id_large)
        self.assertEqual(len(results_large), 1000)

        snapshot_done = self.pipeline.get_progress_snapshot(batch_id_large)
        self.assertTrue(snapshot_done.is_done)
        self.assertEqual(snapshot_done.completed, 1000)

    def test_concurrent_processing_performance_and_correctness(self):
        """Test concurrency allows high throughput and non-blocking status updates."""
        tasks = [RenderTask(task_id=f"c_{i}") for i in range(50)]

        start_time = time.time()
        batch_id = self.pipeline.submit_batch(tasks)
        submit_time = time.time() - start_time

        # Submit should be very fast (non-blocking)
        self.assertLess(submit_time, 0.1)

        # We can poll progress while it runs
        snapshot = self.pipeline.get_progress_snapshot(batch_id)
        self.assertIsNotNone(snapshot)

        # Wait for all
        results = self.pipeline.wait_for_completion(batch_id)
        self.assertEqual(len(results), 50)

        # Ensure all tasks are correctly processed without mixed up data
        task_ids_in_results = set(r.task_id for r in results)
        expected_ids = set(f"c_{i}" for i in range(50))
        self.assertEqual(task_ids_in_results, expected_ids)

if __name__ == '__main__':
    unittest.main()
