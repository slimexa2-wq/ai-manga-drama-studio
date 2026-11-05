import unittest
from ultra_modules.jianying_pro_draft_enricher_benchmark_suite import (
    JianyingDraftEnricher,
    SyntheticFixtureGenerator,
    BenchmarkSuite
)

class TestJianyingDraftEnricher(unittest.TestCase):
    def setUp(self):
        self.enricher = JianyingDraftEnricher()

    def test_normal_operation(self):
        """Test normal draft enrichment operations."""
        draft = SyntheticFixtureGenerator.generate_normal_draft()
        result = self.enricher.enrich_draft(draft)

        # Verify text effects added
        self.assertIn("text_effects", result["materials"]["texts"][0])
        # Verify transition added
        self.assertEqual(len(result["materials"]["transitions"]), 1)
        self.assertEqual(result["materials"]["transitions"][0]["type"], "shake")
        # Verify KenBurns added to canvas
        self.assertIn("camera_movement", result["materials"]["canvases"][0])
        # Verify default BGM added
        self.assertEqual(len(result["materials"]["audios"]), 1)
        self.assertEqual(result["materials"]["audios"][0]["type"], "bgm")

    def test_dirty_data_auto_healing(self):
        """Test auto-healing mechanisms for dirty data."""
        draft = SyntheticFixtureGenerator.generate_dirty_draft()
        result = self.enricher.enrich_draft(draft)

        # Ensure it didn't crash and text was healed
        texts = result["materials"]["texts"]
        # Only valid dict items are kept/processed properly by _apply_text_effects in this logic,
        # but the non-dict item is ignored. The null content should be replaced with default.
        self.assertEqual(texts[0]["content"], "Default Text")
        self.assertIn("text_effects", texts[0])

        # Transitions auto-healed from string to list containing default transition
        self.assertIsInstance(result["materials"]["transitions"], list)
        self.assertEqual(len(result["materials"]["transitions"]), 1)

        # Audios auto-created
        self.assertIsInstance(result["materials"]["audios"], list)
        self.assertEqual(len(result["materials"]["audios"]), 1)

        # Canvases auto-created empty
        self.assertIsInstance(result["materials"]["canvases"], list)

    def test_missing_parameter_fallback(self):
        """Test fallback when the entire draft content is None."""
        result = self.enricher.enrich_draft(None)

        self.assertIsNotNone(result)
        self.assertIn("id", result)
        self.assertIn("materials", result)
        self.assertIn("texts", result["materials"])

        # It should have injected default transitions and BGM even to an empty draft
        self.assertEqual(len(result["materials"]["transitions"]), 1)
        self.assertEqual(len(result["materials"]["audios"]), 1)

    def test_extreme_boundary_gibberish(self):
        """Test processing of gibberish strings and edge case encodings."""
        draft = SyntheticFixtureGenerator.generate_gibberish_draft()
        result = self.enricher.enrich_draft(draft)

        # Verify it didn't crash and effects applied correctly despite weird strings
        self.assertIn("text_effects", result["materials"]["texts"][0])
        self.assertEqual(result["materials"]["texts"][0]["content"], "锟斤拷\x00\x01\x02" * 10)

    def test_cross_year_boundary(self):
        """Test processing of draft with cross-year/month boundaries (e.g., metadata)."""
        draft = SyntheticFixtureGenerator.generate_cross_boundary_draft()
        result = self.enricher.enrich_draft(draft)

        # Verify metadata remains intact and processing didn't crash
        self.assertIn("metadata", result)
        self.assertEqual(result["metadata"]["created_at"], "2023-12-31T23:59:59Z")
        self.assertEqual(result["metadata"]["updated_at"], "2024-01-01T00:00:01Z")

    def test_performance_benchmark(self):
        """Test that enrichment of a massive draft completes within acceptable time (e.g. < 500ms)."""
        # Testing with 10,000 items
        execution_time_ms = BenchmarkSuite.run_benchmark(self.enricher, items_count=10000)

        # Verify execution time is reasonably fast (millisecond level)
        # Note: 500ms is a generous limit for 10k simple dict iterations in Python
        self.assertLess(execution_time_ms, 500.0, f"Benchmark took too long: {execution_time_ms} ms")

if __name__ == '__main__':
    unittest.main()
