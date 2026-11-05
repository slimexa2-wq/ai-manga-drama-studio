import unittest
import uuid
import time
from ultra_modules.gpt_image_turnaround_sheet_batch_pipeline import (
    GPTImageTurnaroundSheetPipeline,
    generate_turnaround_sheets
)

class TestGPTImageTurnaroundSheetBatchPipeline(unittest.TestCase):

    def test_normal_operation_with_strings(self):
        """Test normal operation with a list of strings as input."""
        records = ["Hero character, red cape", "Villain character, dark armor"]
        results = generate_turnaround_sheets(records)

        self.assertEqual(len(results), 2)
        for res in results:
            self.assertEqual(res["status"], "success")
            self.assertTrue("GPT-Image-2 prompt: A highly detailed character design model sheet of" in res["turnaround_prompt"])
            self.assertTrue("GPT-Image-2 prompt: A character expression sheet of" in res["expression_prompt"])
            self.assertEqual(res["style"], "anime") # default style
            self.assertIsNotNone(res["id"])

    def test_normal_operation_with_dicts(self):
        """Test normal operation with a list of dictionaries (ID, description, style)."""
        records = [
            {"id": "123", "description": "Ninja in black", "style": "cyberpunk"},
            {"id": "456", "description": "Samurai in red", "style": "watercolor"}
        ]
        results = generate_turnaround_sheets(records)

        self.assertEqual(len(results), 2)

        # Sort by ID to ensure correct assertions as batch processing is unordered
        results_by_id = {res["id"]: res for res in results}

        self.assertIn("123", results_by_id)
        self.assertEqual(results_by_id["123"]["original_description"], "Ninja in black")
        self.assertEqual(results_by_id["123"]["style"], "cyberpunk")

        self.assertIn("456", results_by_id)
        self.assertEqual(results_by_id["456"]["original_description"], "Samurai in red")
        self.assertEqual(results_by_id["456"]["style"], "watercolor")

    def test_dirty_data_self_healing(self):
        """Test dirty data self-healing (mixed types, None, empty inputs)."""
        records = [
            None,
            "",
            "   ",
            {"description": ""},
            {"id": "test_id"}, # missing description
            123, # invalid type, should be handled by default fallback
            {"id": "valid_id", "description": "Valid desc", "style": None}
        ]

        results = generate_turnaround_sheets(records)
        self.assertEqual(len(results), 7)

        for res in results:
            self.assertEqual(res["status"], "success")
            self.assertTrue(len(res["turnaround_prompt"]) > 0)
            self.assertTrue(len(res["expression_prompt"]) > 0)
            self.assertIsNotNone(res["id"])
            self.assertIsNotNone(res["original_description"])

    def test_extreme_boundary_case_throughput(self):
        """Extreme boundary case: High throughput testing (e.g., 1000 records)."""
        # Create 1000 records
        records = [{"id": str(i), "description": f"Character {i}"} for i in range(1000)]

        start_time = time.time()
        results = generate_turnaround_sheets(records)
        end_time = time.time()

        self.assertEqual(len(results), 1000)
        # Should be relatively fast due to concurrency
        self.assertTrue((end_time - start_time) < 10.0, "Batch processing of 1000 records took too long.")

    def test_progress_callback(self):
        """Test progress callback updates without blocking."""
        records = ["Char A", "Char B", "Char C", "Char D", "Char E"]

        callback_history = []

        def mock_progress(processed, total, current_results):
            callback_history.append((processed, total, len(current_results)))

        results = generate_turnaround_sheets(records, progress_callback=mock_progress)

        self.assertEqual(len(results), 5)
        # Check if callback was called the correct number of times
        self.assertEqual(len(callback_history), 5)

        # Verify the final callback state
        last_call = callback_history[-1]
        self.assertEqual(last_call[0], 5) # processed
        self.assertEqual(last_call[1], 5) # total
        self.assertEqual(last_call[2], 5) # len(results)

if __name__ == '__main__':
    unittest.main()
