import unittest
from ultra_modules.climax_pacing_analyzer_core_engine import analyze_pacing_curve

class TestClimaxPacingAnalyzerCoreEngine(unittest.TestCase):

    def test_normal_pacing(self):
        # Ideal rhythm flow: repression -> charge -> climax -> suspense
        script_data = [
            {'emotion_score': 30.0}, # repression
            {'emotion_score': 50.0}, # charge
            {'emotion_score': 85.0}, # climax
            {'emotion_score': 60.0}  # suspense
        ]

        result = analyze_pacing_curve(script_data)
        analyzed = result['analyzed_script']

        self.assertEqual(len(analyzed), 4)

        # Check stages
        self.assertEqual(analyzed[0]['rhythm_stage'], 'repression')
        self.assertEqual(analyzed[1]['rhythm_stage'], 'charge')
        self.assertEqual(analyzed[2]['rhythm_stage'], 'climax')
        self.assertEqual(analyzed[3]['rhythm_stage'], 'suspense')

        # Check boosting (default climax boost 1.5, max 100.0)
        # climax original is 85.0 * 1.5 = 127.5 -> clamped to 100.0
        self.assertEqual(analyzed[2]['encrypted_score'], 100.0)

        # Check suspense drop (default drop 0.8)
        # 60.0 * 0.8 = 48.0
        self.assertEqual(analyzed[3]['encrypted_score'], 48.0)

    def test_dirty_data_repair(self):
        # Handling invalid inputs, strings, wrong types inside script_data
        script_data = [
            'invalid_string', # should be ignored
            {'emotion_score': 'not_a_number'}, # should default to 50.0
            {'emotion_score': '95.5'}, # string but parseable
            {'no_score_key': 'value'}, # should default to 50.0
            123 # should be ignored
        ]

        result = analyze_pacing_curve(script_data)
        analyzed = result['analyzed_script']

        self.assertEqual(len(analyzed), 3) # only 3 valid dicts

        self.assertEqual(analyzed[0]['emotion_score'], 50.0) # unparseable
        self.assertEqual(analyzed[1]['emotion_score'], 95.5) # parseable
        self.assertEqual(analyzed[2]['emotion_score'], 50.0) # missing key

    def test_missing_params(self):
        # `None` arguments fallback behavior
        result_none = analyze_pacing_curve(None, None)
        self.assertEqual(result_none['analyzed_script'], [])
        self.assertEqual(result_none['diagnostics']['total_scenes'], 0)
        self.assertEqual(result_none['diagnostics']['climax_count'], 0)

        # Passing wrong type entirely
        result_wrong_type = analyze_pacing_curve("some_random_string", 42)
        self.assertEqual(result_wrong_type['analyzed_script'], [])

    def test_dict_instead_of_list(self):
        # Passing a single dict instead of a list
        script_data = {'emotion_score': 85.0}
        result = analyze_pacing_curve(script_data)

        analyzed = result['analyzed_script']
        self.assertEqual(len(analyzed), 1)
        self.assertEqual(analyzed[0]['rhythm_stage'], 'climax')
        self.assertEqual(result['diagnostics']['climax_count'], 1)

    def test_extreme_boundaries(self):
        # Handling values far beyond min/max thresholds and invalid configs
        script_data = [
            {'emotion_score': -1000.0},
            {'emotion_score': 5000.0}
        ]

        # Messed up config
        config = {
            'min_score': -50.0,
            'max_score': 200.0,
            'climax_boost': 'invalid_boost', # Should default to 1.5
            'suspense_drop': None # Should default to 0.8
        }

        result = analyze_pacing_curve(script_data, config)
        analyzed = result['analyzed_script']

        self.assertEqual(len(analyzed), 2)

        # Clamped to provided valid config boundaries
        self.assertEqual(analyzed[0]['emotion_score'], -50.0)
        self.assertEqual(analyzed[1]['emotion_score'], 200.0)

        # climax calculation with default fallback climax_boost
        # 200.0 * 1.5 = 300.0, clamped back to max_score 200.0
        self.assertEqual(analyzed[1]['encrypted_score'], 200.0)

if __name__ == '__main__':
    unittest.main()
