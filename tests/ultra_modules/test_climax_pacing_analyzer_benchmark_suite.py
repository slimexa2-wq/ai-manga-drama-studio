import unittest
import math
from ultra_modules.climax_pacing_analyzer_benchmark_suite import generate_synthetic_fixtures, run_benchmark_suite
from ultra_modules.climax_pacing_analyzer_core_engine import analyze_pacing_curve

class TestClimaxPacingAnalyzerBenchmarkSuite(unittest.TestCase):

    def test_normal_operations(self):
        """Test with valid normal data."""
        data = [
            {'emotion_score': 30, 'text': 'Intro'},
            {'emotion_score': 60, 'text': 'Build up'},
            {'emotion_score': 90, 'text': 'Climax'},
            {'emotion_score': 20, 'text': 'Suspense'}
        ]
        result = analyze_pacing_curve(data)

        analyzed = result['analyzed_script']
        self.assertEqual(len(analyzed), 4)

        # Intro: rep or charge based on logic, but score 30 < 40 -> repression
        self.assertEqual(analyzed[0]['rhythm_stage'], 'repression')

        # Build up: diff 30 -> charge
        self.assertEqual(analyzed[1]['rhythm_stage'], 'charge')

        # Climax: 90 > 80 -> climax
        self.assertEqual(analyzed[2]['rhythm_stage'], 'climax')

        # Suspense: drop from 90 to 20 -> diff -70 and prev > 70 -> suspense
        self.assertEqual(analyzed[3]['rhythm_stage'], 'suspense')

    def test_dirty_data_auto_healing(self):
        """Test with dirty data like NaN or strings."""
        data = [
            {'emotion_score': float('nan'), 'text': 'Intro'},
            {'emotion_score': "invalid_string", 'text': 'Build up'},
            {'emotion_score': None, 'text': 'Climax'}
        ]
        result = analyze_pacing_curve(data)
        analyzed = result['analyzed_script']

        self.assertEqual(len(analyzed), 3)
        # Should default to 50.0 and heal
        for item in analyzed:
            self.assertFalse(math.isnan(item['encrypted_score']))
            self.assertTrue(isinstance(item['encrypted_score'], float) or isinstance(item['encrypted_score'], int))
            self.assertGreaterEqual(item['encrypted_score'], 0)
            self.assertLessEqual(item['encrypted_score'], 100)

    def test_missing_parameters_fallback(self):
        """Test behavior when entire dicts, lists, or params are None."""
        # 1. None data
        result = analyze_pacing_curve(None)
        self.assertEqual(len(result['analyzed_script']), 0)

        # 2. None Config
        result2 = analyze_pacing_curve([{'emotion_score': 50}], None)
        self.assertEqual(len(result2['analyzed_script']), 1)

        # 3. None items in list
        result3 = analyze_pacing_curve([None, {'emotion_score': 50}, None])
        # Core engine skips non-dicts
        self.assertEqual(len(result3['analyzed_script']), 1)

        # 4. Empty dict
        result4 = analyze_pacing_curve([{}])
        self.assertEqual(result4['analyzed_script'][0]['emotion_score'], 50.0)

    def test_extreme_boundary_edge_cases(self):
        """Test with extreme boundaries like out-of-bounds scores and cross year dates."""
        data = [
            {'emotion_score': 99999, 'timestamp': '2023-12-31T23:59:59Z'},
            {'emotion_score': -99999, 'timestamp': '2024-01-01T00:00:00Z'}
        ]

        config = {
            'min_score': 0.0,
            'max_score': 100.0
        }

        result = analyze_pacing_curve(data, config)
        analyzed = result['analyzed_script']

        # Scores should be clamped
        self.assertEqual(analyzed[0]['emotion_score'], 100.0)
        self.assertEqual(analyzed[1]['emotion_score'], 0.0)
        self.assertLessEqual(analyzed[0]['encrypted_score'], 100.0)
        self.assertGreaterEqual(analyzed[1]['encrypted_score'], 0.0)

    def test_stress_test_concurrency_pipeline(self):
        """Test the run_benchmark_suite for no crashes under load."""
        result = run_benchmark_suite(data_size=1000, concurrency=10, timeout=10.0, edge_case_ratio=0.2)

        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['processed_chunks'], 0)
        self.assertGreaterEqual(result['total_time_ms'], 0)
        self.assertGreaterEqual(result['average_chunk_time_ms'], 0)

if __name__ == '__main__':
    unittest.main()
