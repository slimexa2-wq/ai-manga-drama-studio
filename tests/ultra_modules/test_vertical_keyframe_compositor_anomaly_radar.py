import unittest
from ultra_modules.vertical_keyframe_compositor_anomaly_radar import VerticalKeyframeCompositorAnomalyRadar

class TestVerticalKeyframeCompositorAnomalyRadar(unittest.TestCase):
    def setUp(self):
        self.radar = VerticalKeyframeCompositorAnomalyRadar()

    def test_normal_operation(self):
        # 100 normal frames
        data = [{'render_time': 100 + i * 0.1} for i in range(100)]
        results = self.radar.analyze(data)
        self.assertEqual(len(results), 100)

        # Check that top 3% (3 frames) are flagged as red (if there's variance)
        red_count = sum(1 for r in results if r['marker'] == 'red')
        green_count = sum(1 for r in results if r['marker'] == 'green')
        self.assertEqual(red_count, 3)
        self.assertEqual(green_count, 97)

    def test_dirty_data_auto_healing(self):
        # Data containing strings, None, strings that look like numbers, NaNs, Inf
        import math
        data = [
            {'render_time': '105'},
            {'render_time': None},
            {'render_time': 'not_a_number'},
            {'render_time': math.nan},
            {'render_time': math.inf},
            'not_a_dict',
            {'wrong_key': 100}
        ]

        # Add normal data to form a sufficient sample
        data.extend([{'render_time': 100 + i * 0.1} for i in range(100)])

        results = self.radar.analyze(data)
        # Expected to silently heal and skip the bad records, except '105' which converts successfully
        self.assertEqual(len(results), 101) # 100 normal + 1 converted string '105'

        # Ensure it runs without exception
        red_count = sum(1 for r in results if r['marker'] == 'red')
        self.assertEqual(red_count, 4) # top 3% of 101 is ceil(3.03) = 4

    def test_missing_parameter_fallbacks(self):
        # Empty inputs
        results_none = self.radar.analyze(None)
        self.assertEqual(results_none, [])

        results_empty = self.radar.analyze([])
        self.assertEqual(results_empty, [])

        # Missing config handling
        radar_no_config = VerticalKeyframeCompositorAnomalyRadar(config=None)
        self.assertEqual(radar_no_config.anomaly_threshold_percent, 0.03)

    def test_extreme_boundaries(self):
        # Identical values to test division by zero in Z-Score/IQR
        data_identical = [{'render_time': 50} for _ in range(100)]

        # Test default z-score identical values
        results_identical = self.radar.analyze(data_identical)
        self.assertEqual(len(results_identical), 100)

        # Should not flag any anomalies because variance is 0 (all scores are 0)
        red_count = sum(1 for r in results_identical if r['marker'] == 'red')
        self.assertEqual(red_count, 0)

        # Test IQR identical values
        radar_iqr = VerticalKeyframeCompositorAnomalyRadar(config={'method': 'iqr'})
        results_iqr_identical = radar_iqr.analyze(data_identical)
        self.assertEqual(len(results_iqr_identical), 100)
        red_count_iqr = sum(1 for r in results_iqr_identical if r['marker'] == 'red')
        self.assertEqual(red_count_iqr, 0)

        # Edge case: single element
        results_single = self.radar.analyze([{'render_time': 100}])
        self.assertEqual(len(results_single), 1)
        self.assertEqual(results_single[0]['marker'], 'green')

    def test_top_3_percent_identification(self):
        # 200 items, normal are 10-20, outliers are 1000+
        data = [{'render_time': 10 + (i % 10)} for i in range(194)]
        outliers = [
            {'render_time': 1000},
            {'render_time': 1050},
            {'render_time': 1100},
            {'render_time': 1200},
            {'render_time': 1300},
            {'render_time': 1500}
        ]
        data.extend(outliers)

        # total 200, 3% of 200 is 6. So exactly our 6 outliers should be flagged
        results = self.radar.analyze(data)

        red_results = [r for r in results if r['marker'] == 'red']
        green_results = [r for r in results if r['marker'] == 'green']

        self.assertEqual(len(red_results), 6)
        self.assertEqual(len(green_results), 194)

        # Verify the outliers are the correct ones
        for r in red_results:
            self.assertTrue(r['value'] >= 1000)

        # Test IQR method identifying top 3% as well
        radar_iqr = VerticalKeyframeCompositorAnomalyRadar(config={'method': 'iqr'})
        results_iqr = radar_iqr.analyze(data)

        red_results_iqr = [r for r in results_iqr if r['marker'] == 'red']
        self.assertEqual(len(red_results_iqr), 6)
        for r in red_results_iqr:
            self.assertTrue(r['value'] >= 1000)

if __name__ == '__main__':
    unittest.main()
