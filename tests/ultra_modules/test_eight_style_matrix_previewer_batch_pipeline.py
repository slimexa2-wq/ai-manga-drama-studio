import unittest
from ultra_modules.eight_style_matrix_previewer_batch_pipeline import (
    EightStyleMatrixPreviewerBatchPipeline,
    run_matrix_preview_pipeline
)

class TestEightStyleMatrixPreviewerBatchPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = EightStyleMatrixPreviewerBatchPipeline()

    def test_normal_data_processing(self):
        records = ["Hero starts his journey", "The villain strikes back"]
        progress = run_matrix_preview_pipeline(records=records)
        self.assertEqual(progress["total"], 2)
        self.assertEqual(progress["completed"], 2)
        self.assertEqual(progress["failed"], 0)

        # Verify exactly 8 styles are applied to each record
        for result in progress["results"]:
            self.assertEqual(result["status"], "success")
            self.assertEqual(len(result["previews"]), 8)
            # Default styles should be present
            self.assertIn("修仙", result["previews"])

    def test_dirty_data_self_healing(self):
        records = [None, "", 123, {"not_content": "value"}, {"content": ""}]
        progress = run_matrix_preview_pipeline(records=records)

        self.assertEqual(progress["total"], 5)
        self.assertEqual(progress["completed"], 5)

        # Verify self-healing behavior
        results = progress["results"]
        for result in results:
            self.assertEqual(result["status"], "success")
            self.assertEqual(len(result["previews"]), 8)

    def test_missing_parameter_default_fallback(self):
        # Calling with absolutely no arguments
        progress = run_matrix_preview_pipeline()

        # Should default to a single dummy record
        self.assertEqual(progress["total"], 1)
        self.assertEqual(progress["completed"], 1)
        self.assertEqual(progress["failed"], 0)

        result = progress["results"][0]
        self.assertIn("Preview for 修仙: default_re", result["previews"]["修仙"])

    def test_extreme_edge_cases_high_throughput(self):
        # 1000 items processed concurrently
        records = [f"Record {i}" for i in range(1000)]
        progress = run_matrix_preview_pipeline(records=records)

        self.assertEqual(progress["total"], 1000)
        self.assertEqual(progress["completed"], 1000)
        self.assertEqual(progress["failed"], 0)
        self.assertEqual(len(progress["results"]), 1000)

    def test_custom_styles_self_healing(self):
        records = ["Record 1"]

        # Test with fewer than 8 styles
        short_styles = ["自定义风格1", "自定义风格2"]
        progress_short = run_matrix_preview_pipeline(records=records, styles=short_styles)
        previews_short = progress_short["results"][0]["previews"]
        self.assertEqual(len(previews_short), 8)
        self.assertIn("自定义风格1", previews_short)
        self.assertIn("修仙", previews_short) # Padded from default

        # Test with more than 8 styles
        long_styles = [f"自定义风格{i}" for i in range(10)]
        progress_long = run_matrix_preview_pipeline(records=records, styles=long_styles)
        previews_long = progress_long["results"][0]["previews"]
        self.assertEqual(len(previews_long), 8)
        self.assertIn("自定义风格0", previews_long)
        self.assertIn("自定义风格7", previews_long)
        self.assertNotIn("自定义风格8", previews_long)

if __name__ == '__main__':
    unittest.main()
