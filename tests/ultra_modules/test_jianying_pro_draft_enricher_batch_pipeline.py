import unittest
from ultra_modules.jianying_pro_draft_enricher_batch_pipeline import enrich_drafts, JianyingDraftEnricherBatchPipeline

class TestJianyingDraftEnricherBatchPipeline(unittest.TestCase):

    def test_normal_processing(self):
        """Test Case 1: Normal processing with well-formed, basic data."""
        drafts = [{
            "materials": {
                "texts": [{"id": "txt1", "content": "Hello World"}]
            },
            "video_track": [
                {"clips": [{"id": "clip1"}]}
            ]
        }]

        result = enrich_drafts(drafts)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["errors"], 0)

        enriched = result["results"][0]

        # Check BGM injection
        self.assertIn("audios", enriched["materials"])
        self.assertEqual(enriched["materials"]["audios"][0]["type"], "bgm")

        # Check text effects (花字特效)
        self.assertEqual(enriched["materials"]["texts"][0]["effect_id"], "default_text_effect_01")

        # Check transitions (震屏转场)
        self.assertIn("transitions", enriched["materials"])
        self.assertEqual(enriched["materials"]["transitions"][0]["name"], "shake")

        # Check KenBurns (运镜)
        clip = enriched["video_track"][0]["clips"][0]
        self.assertEqual(clip["animations"][0]["type"], "kenburns")

    def test_dirty_data_self_healing(self):
        """Test Case 2: Dirty data self-healing (invalid types passed)."""
        # Pass an integer instead of a dict, and pass a completely invalid list
        drafts = [12345, "invalid_string", None]

        result = enrich_drafts(drafts)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["processed"], 3)
        # Should gracefully self-heal all to empty valid templates instead of crashing

        for enriched in result["results"]:
            self.assertIsInstance(enriched, dict)
            self.assertIn("materials", enriched)
            self.assertIn("audios", enriched["materials"])
            self.assertEqual(enriched["materials"]["audios"][0]["type"], "bgm")

    def test_missing_parameters_fallback(self):
        """Test Case 3: Default fallback when parameters are entirely missing."""
        # Empty dict should be fully populated with default templates
        drafts = [{}]

        result = enrich_drafts(drafts)
        self.assertEqual(result["status"], "success")

        enriched = result["results"][0]
        self.assertIn("materials", enriched)
        self.assertIn("audios", enriched["materials"])
        self.assertIn("transitions", enriched["materials"])

    def test_boundary_conditions_empty_or_single_input(self):
        """Test Case 4: Extreme boundary conditions (empty list, single non-list item)."""
        # Empty list
        result_empty = enrich_drafts([])
        self.assertEqual(result_empty["processed"], 0)
        self.assertEqual(result_empty["results"], [])

        # Passed a dict directly instead of a list
        single_dict = {"materials": {}}
        result_single = enrich_drafts(single_dict) # type: ignore
        self.assertEqual(result_single["processed"], 1)
        self.assertEqual(len(result_single["results"]), 1)
        self.assertIn("audios", result_single["results"][0]["materials"])

    def test_large_batch_concurrency(self):
        """Test Case 5: Large batch processing behavior and throughput."""
        # Simulate dragging in 100 records
        drafts = [{"id": f"draft_{i}"} for i in range(100)]

        pipeline = JianyingDraftEnricherBatchPipeline(max_workers=20)
        result = pipeline.process_batch(drafts)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["processed"], 100)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(len(result["results"]), 100)

        # Verify ordering is preserved
        for i in range(100):
            self.assertEqual(result["results"][i]["id"], f"draft_{i}")
            self.assertIn("materials", result["results"][i])

if __name__ == '__main__':
    unittest.main()
