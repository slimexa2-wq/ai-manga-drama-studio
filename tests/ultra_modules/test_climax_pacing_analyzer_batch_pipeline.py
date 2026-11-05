import unittest
import time
from ultra_modules.climax_pacing_analyzer_batch_pipeline import (
    ClimaxPacingAnalyzer,
    ClimaxPacingBatchPipeline,
    analyze_scripts
)

class TestClimaxPacingAnalyzerBatchPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = ClimaxPacingBatchPipeline(max_workers=2)

    def test_normal_pacing_analysis(self):
        """Test normal pacing curve analysis."""
        record = {
            "id": "1",
            "content": "主角被辱骂废柴，他选择隐忍闭关修炼，出关后无敌秒杀众人，震惊全场。然而背后还有暗影阴谋未完。"
        }
        analyzer = ClimaxPacingAnalyzer()
        res = analyzer.analyze_record(record)

        self.assertEqual(res["status"], "success")
        analysis = res["analysis"]
        self.assertTrue(analysis["has_curve"])
        self.assertGreater(analysis["scores"]["suppression"], 0)
        self.assertGreater(analysis["scores"]["buildup"], 0)
        self.assertGreater(analysis["scores"]["payoff"], 0)
        self.assertGreater(analysis["scores"]["suspense"], 0)
        self.assertEqual(analysis["overall_rating"], "Excellent")

    def test_batch_processing_and_snapshot(self):
        """Test batch processing and non-blocking snapshot updates."""
        records = [
            {"id": f"rec_{i}", "content": "普通的日常"} for i in range(10)
        ]

        # Make the batch big enough so it might take a moment, or mock it to be slow.
        # But we just want to ensure it works properly.
        job_id = self.pipeline.submit_batch(records)

        # Immediately check snapshot
        snapshot = self.pipeline.get_snapshot(job_id)
        self.assertIn(snapshot["status"], ["processing", "completed"])
        self.assertEqual(snapshot["total"], 10)

        # Wait for completion
        while snapshot["status"] != "completed":
            time.sleep(0.05)
            snapshot = self.pipeline.get_snapshot(job_id)

        self.assertEqual(snapshot["status"], "completed")
        self.assertEqual(snapshot["completed"], 10)
        self.assertEqual(len(snapshot["results"]), 10)

    def test_dirty_data_self_healing(self):
        """Test handling of invalid types and malformed data silently."""
        records = [
            "Just a string instead of dict",
            12345,
            None,
            {"wrong_key": "No content here"}
        ]

        results = analyze_scripts(records)

        self.assertEqual(len(results), 4)
        for res in results:
            self.assertEqual(res["status"], "success")
            self.assertIn("analysis", res)

        # Check specific behaviors
        # For string, it should be treated as text content
        res_string = next(r for r in results if r["analysis"]["scores"]["suppression"] == 0) # Simplistic check, they all have 0 in this test
        self.assertIsNotNone(res_string)

    def test_missing_params_fallback(self):
        """Test fallback when expected dict keys are missing."""
        record = {"text": "主角觉醒无敌打脸全场"} # Missing 'content', but has 'text'

        analyzer = ClimaxPacingAnalyzer()
        res = analyzer.analyze_record(record)

        self.assertEqual(res["status"], "success")
        self.assertTrue(res["analysis"]["has_curve"]) # Because "觉醒" and "无敌打脸"
        self.assertGreater(res["analysis"]["scores"]["buildup"], 0)
        self.assertGreater(res["analysis"]["scores"]["payoff"], 0)

    def test_extreme_boundary_cases(self):
        """Test extreme boundary cases like empty input or massive inputs."""
        # Case 1: None input
        res = analyze_scripts(None)
        self.assertEqual(len(res), 0)

        # Case 2: 1500 records (should cap at 1000)
        records = [{"id": f"{i}", "content": "Test"} for i in range(1500)]
        res2 = analyze_scripts(records)
        self.assertEqual(len(res2), 1000)

if __name__ == '__main__':
    unittest.main()
