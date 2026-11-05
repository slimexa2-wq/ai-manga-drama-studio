import unittest
import time
from ultra_modules.character_dna_seed_locker_batch_pipeline import CharacterDnaSeedLockerBatchPipeline

class TestCharacterDnaSeedLockerBatchPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = CharacterDnaSeedLockerBatchPipeline(max_workers=50)

    def test_01_normal_case_sync(self):
        """Test 1: Normal standard input arguments (sync batch)."""
        records = [
            {
                "char_id": "hero_01",
                "hair_color": "silver hair",
                "eye_color": "red eyes",
                "clothing": "cyberpunk jacket",
                "style_suffix": "3d render, octane render",
                "seed": 9999
            },
            {
                "char_id": "villain_01",
                "hair_color": "blonde hair",
                "eye_color": "blue eyes",
                "clothing": "formal suit",
                "style_suffix": "dark fantasy, intricate",
                "seed": 8888
            }
        ]
        results = self.pipeline.process_batch_sync(records)
        self.assertEqual(len(results), 2)

        # Check hero
        self.assertEqual(results[0]["char_id"], "hero_01")
        self.assertEqual(results[0]["hair_color"], "silver hair")
        self.assertEqual(results[0]["seed"], 9999)
        self.assertTrue("silver hair, red eyes, cyberpunk jacket" in results[0]["locked_prompt"])

        # Check villain
        self.assertEqual(results[1]["char_id"], "villain_01")
        self.assertEqual(results[1]["seed"], 8888)

    def test_02_dirty_data_self_healing(self):
        """Test 2: Validates self-healing of completely corrupt/malformed records."""
        # Mix of non-dict, missing char_id, invalid seeds, None values
        records = [
            "This is a string, not a dict",
            None,
            {
                "char_id": "",
                "hair_color": 12345, # Invalid type
                "eye_color": None,
                "seed": "not_an_int"
            }
        ]
        results = self.pipeline.process_batch_sync(records)
        self.assertEqual(len(results), 3)

        for res in results:
            self.assertTrue(res["char_id"].startswith("char_"))
            self.assertEqual(res["hair_color"], CharacterDnaSeedLockerBatchPipeline.DEFAULT_HAIR)
            self.assertEqual(res["eye_color"], CharacterDnaSeedLockerBatchPipeline.DEFAULT_EYE)
            self.assertEqual(res["clothing"], CharacterDnaSeedLockerBatchPipeline.DEFAULT_CLOTHING)
            self.assertEqual(res["style_suffix"], CharacterDnaSeedLockerBatchPipeline.DEFAULT_STYLE)
            self.assertEqual(res["seed"], CharacterDnaSeedLockerBatchPipeline.DEFAULT_SEED)

    def test_03_missing_params_fallback(self):
        """Test 3: Asserts fallback to default visual DNA values and standard styles."""
        records = [
            {"char_id": "missing_params_char"}
        ]
        results = self.pipeline.process_batch_sync(records)
        self.assertEqual(len(results), 1)
        res = results[0]

        self.assertEqual(res["char_id"], "missing_params_char")
        self.assertEqual(res["hair_color"], CharacterDnaSeedLockerBatchPipeline.DEFAULT_HAIR)
        self.assertEqual(res["eye_color"], CharacterDnaSeedLockerBatchPipeline.DEFAULT_EYE)
        self.assertEqual(res["seed"], CharacterDnaSeedLockerBatchPipeline.DEFAULT_SEED)

    def test_04_extreme_edge_cases(self):
        """Test 4: Executes empty batches and massive batches concurrently."""
        # Empty batch
        empty_results = self.pipeline.process_batch_sync([])
        self.assertEqual(empty_results, [])

        # Massive batch (1000 items)
        massive_records = [{"char_id": f"char_{i}", "seed": i} for i in range(1000)]
        massive_results = self.pipeline.process_batch_sync(massive_records)
        self.assertEqual(len(massive_results), 1000)

        # Verify ordering is preserved
        self.assertEqual(massive_results[0]["char_id"], "char_0")
        self.assertEqual(massive_results[0]["seed"], 0)
        self.assertEqual(massive_results[999]["char_id"], "char_999")
        self.assertEqual(massive_results[999]["seed"], 999)

    def test_05_async_snapshot_and_stream(self):
        """Test 5: Exercises non-blocking execution yielding progress snapshots and streaming."""
        # 1. Async Snapshot Test
        records = [{"char_id": f"async_char_{i}"} for i in range(100)]
        job_id = self.pipeline.submit_batch_async(records)
        self.assertTrue(job_id.startswith("job_"))

        snapshot = self.pipeline.get_job_snapshot(job_id)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["total"], 100)
        self.assertTrue(0 <= snapshot["completed"] <= 100)

        # Wait for job to finish
        timeout = 5
        start_time = time.time()
        while time.time() - start_time < timeout:
            snapshot = self.pipeline.get_job_snapshot(job_id)
            if snapshot["status"] == "completed":
                break
            time.sleep(0.1)

        self.assertEqual(snapshot["status"], "completed")
        self.assertEqual(snapshot["completed"], 100)
        self.assertEqual(snapshot["progress_pct"], 100.0)
        self.assertEqual(len(snapshot["results"]), 100)

        # Verify results don't contain None (all finished)
        for res in snapshot["results"]:
            self.assertIsNotNone(res)
            self.assertTrue(res["char_id"].startswith("async_char_"))

        # 2. Streaming Test
        stream_records = [{"char_id": f"stream_char_{i}"} for i in range(10)]
        stream_results = []
        for res in self.pipeline.process_stream(stream_records):
            stream_results.append(res)

        self.assertEqual(len(stream_results), 10)
        # Verify all came through (order not guaranteed, so check sets)
        stream_ids = {r["char_id"] for r in stream_results}
        expected_ids = {f"stream_char_{i}" for i in range(10)}
        self.assertEqual(stream_ids, expected_ids)

if __name__ == '__main__':
    unittest.main()
