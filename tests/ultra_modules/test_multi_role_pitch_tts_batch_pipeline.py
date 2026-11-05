import unittest
from ultra_modules.multi_role_pitch_tts_batch_pipeline import (
    DynamicTTSModulator,
    DurationAlignmentEngine,
    run_batch_tts_pipeline
)

class TestMultiRolePitchTTSBatchPipeline(unittest.TestCase):

    def test_normal_batch_processing(self):
        """Test 1: Normal batch processing with multiple roles."""
        records = [
            {"id": "1", "role": "narrator", "text": "Once upon a time in a faraway land."},
            {"id": "2", "role": "male_lead", "text": "I will protect you with my life."},
            {"id": "3", "role": "female_lead", "text": "Thank you, I believe in you."},
            {"id": "4", "role": "villain", "text": "You will both perish!"}
        ]

        result = run_batch_tts_pipeline(records)

        self.assertEqual(result["total"], 4)
        self.assertEqual(result["processed"], 4)

        results = result["results"]
        # Extract IDs to verify all were processed
        processed_ids = [r["id"] for r in results]
        self.assertCountEqual(processed_ids, ["1", "2", "3", "4"])

        for r in results:
            self.assertEqual(r["status"], "success")
            self.assertIn("tts_params", r)
            self.assertIn("duration_ms", r)

    def test_dirty_data_self_healing(self):
        """Test 2: Dirty data self-healing (missing role, out-of-bounds parameters, None values)."""
        records = [
            {"id": "1", "role": None, "text": "Default to narrator."},
            {"id": "2", "role": "unknown_role", "text": "Should also default to narrator."},
            {"id": "3", "role": "male_lead", "text": "Testing pitch.", "pitch": 5.0}, # Out of bounds high
            {"id": "4", "role": "female_lead", "text": "Testing speed.", "speed": 0.1}, # Out of bounds low
        ]

        result = run_batch_tts_pipeline(records)
        results = {r["id"]: r for r in result["results"]}

        # Test missing/unknown role
        self.assertEqual(results["1"]["tts_params"]["role_id"], "narrator")
        self.assertEqual(results["2"]["tts_params"]["role_id"], "narrator")

        # Test out of bounds parameters
        self.assertEqual(results["3"]["tts_params"]["pitch"], 2.0) # Max pitch
        self.assertEqual(results["4"]["tts_params"]["speed"], 0.5) # Min speed

    def test_duration_alignment_logic(self):
        """Test 3: Duration alignment logic (verifying millisecond computation)."""
        text = "Hello" # 5 characters
        # Base ms per char is 250, so 5 * 250 = 1250ms at 1.0 speed

        # Speed 1.0
        duration = DurationAlignmentEngine.compute_duration(text, 1.0)
        self.assertEqual(duration, 1250)

        # Speed 2.0 (half time)
        duration = DurationAlignmentEngine.compute_duration(text, 2.0)
        self.assertEqual(duration, 625)

        # Speed 0.5 (double time)
        duration = DurationAlignmentEngine.compute_duration(text, 0.5)
        self.assertEqual(duration, 2500)

    def test_concurrency_and_high_throughput(self):
        """Test 4: Concurrency and high throughput (processing a simulated batch of 100+ records)."""
        records = [{"id": str(i), "role": "narrator", "text": f"Line {i} of the script."} for i in range(150)]

        import time
        start_time = time.time()
        result = run_batch_tts_pipeline(records, max_workers=20)
        end_time = time.time()

        self.assertEqual(result["total"], 150)
        self.assertEqual(result["processed"], 150)

        # Given each processing sleeps for 0.001s, sequential would take 0.15s.
        # However, threaded is extremely fast anyway, we just ensure it completes properly.
        self.assertTrue(end_time - start_time < 2.0) # Ensure it's somewhat fast

    def test_edge_cases(self):
        """Test 5: Edge cases (empty text, extremely long text)."""
        records = [
            {"id": "1", "role": "narrator", "text": ""},
            {"id": "2", "role": "narrator", "text": None},
            {"id": "3", "role": "narrator", "text": "A" * 10000},
        ]

        result = run_batch_tts_pipeline(records)
        results = {r["id"]: r for r in result["results"]}

        # Empty text
        self.assertEqual(results["1"]["status"], "empty_text")
        self.assertEqual(results["1"]["duration_ms"], 0)

        # None text
        self.assertEqual(results["2"]["status"], "empty_text")
        self.assertEqual(results["2"]["duration_ms"], 0)

        # Long text
        self.assertEqual(results["3"]["status"], "success")
        self.assertTrue(results["3"]["duration_ms"] > 0)

    def test_text_heuristics(self):
        """Test heuristics adjustments like punctuation."""
        # Check text heuristics directly
        params_exclaim = DynamicTTSModulator.modulate("narrator", "Watch out!")
        self.assertEqual(params_exclaim["emotion"], "excited")

        params_question = DynamicTTSModulator.modulate("narrator", "Who goes there?")
        self.assertEqual(params_question["emotion"], "curious")

if __name__ == '__main__':
    unittest.main()
