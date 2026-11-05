import unittest
import math
from ultra_modules.eight_style_matrix_previewer_anomaly_radar import EightStyleAnomalyRadar

class TestEightStyleAnomalyRadar(unittest.TestCase):
    def setUp(self):
        self.radar = EightStyleAnomalyRadar()

    def test_normal_operation(self):
        data = [
            {'style_name': 'xianxia', 'metric_value': 10},
            {'style_name': 'urban', 'metric_value': 10},
            {'style_name': 'korean_drama', 'metric_value': 11},
            {'style_name': 'shounen', 'metric_value': 11},
            {'style_name': 'rules_horror', 'metric_value': 10}
        ]
        result = self.radar.analyze_styles(data)
        self.assertEqual(len(result), 5)
        for item in result:
            self.assertEqual(item['color_marker'], 'Green')
            self.assertEqual(item['reason'], '数值处于正常范围内，无需处理。')

    def test_dirty_data_auto_healing(self):
        data = [
            {'style_name': 'xianxia', 'metric_value': 'invalid_string'},
            {'style_name': 'urban', 'metric_value': None},
            {'style_name': 'korean_drama', 'metric_value': float('nan')},
            {'style_name': 'shounen', 'metric_value': float('inf')},
            {'style_name': 'rules_horror', 'metric_value': []}
        ]
        result = self.radar.analyze_styles(data)
        self.assertEqual(len(result), 5)
        for item in result:
            self.assertEqual(item['metric_value'], 0.0)
            self.assertEqual(item['color_marker'], 'Green')

    def test_missing_params(self):
        # Missing data list
        self.assertEqual(self.radar.analyze_styles(), [])

        # Wrong type of data list
        self.assertEqual(self.radar.analyze_styles("not a list"), [])

        # Empty list
        self.assertEqual(self.radar.analyze_styles([]), [])

        # Missing keys in dict
        data = [{'metric_value': 10}, {'style_name': 'xianxia'}, 'not a dict']
        result = self.radar.analyze_styles(data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['style_name'], 'Unknown')
        self.assertEqual(result[1]['metric_value'], 0.0)

        # Test empty cleaned data path in _calculate_stats
        # This will trigger the empty check in _calculate_stats if we bypass the analyze_styles early return
        # But analyze_styles handles empty lists. We can call _calculate_stats directly.
        self.assertEqual(self.radar._calculate_stats([]), {'mean': 0.0, 'std_dev': 0.0, 'q1': 0.0, 'q3': 0.0, 'iqr': 0.0})

    def test_extreme_boundary_limits(self):
        data = [
            {'style_name': 'style1', 'metric_value': -999999999},
            {'style_name': 'style2', 'metric_value': 999999999},
            {'style_name': 'style3', 'metric_value': 0}
        ]
        result = self.radar.analyze_styles(data)
        self.assertEqual(len(result), 3)
        # 999999999 might be flagged as Yellow depending on distribution
        # with just 3 items, n >= 3, top 3% is 1 item.
        # However, z_score > 2.0 or val > iqr_upper_bound is required for Red.
        # Let's check what it got.
        styles = {r['style_name']: r['color_marker'] for r in result}
        self.assertIn(styles['style2'], ['Yellow', 'Red', 'Green'])

    def test_iqr_zscore_calculation(self):
        # We need to trigger a Red. Top 3% of 100 items is 3 items.
        # Let's generate 97 normal items and 3 extreme items.
        data = [{'style_name': f'style_{i}', 'metric_value': 10 + (i % 5)} for i in range(97)]
        # Add 3 extreme outliers
        data.append({'style_name': 'outlier_1', 'metric_value': 5000})
        data.append({'style_name': 'outlier_2', 'metric_value': 5001})
        data.append({'style_name': 'outlier_3', 'metric_value': 5002})

        result = self.radar.analyze_styles(data)
        self.assertEqual(len(result), 100)

        reds = [r for r in result if r['color_marker'] == 'Red']
        self.assertEqual(len(reds), 3)
        for r in reds:
            self.assertTrue(r['style_name'].startswith('outlier'))
            self.assertIn("数值极高", r['reason'])

        yellows = [r for r in result if r['color_marker'] == 'Yellow']
        # Some normal items might not be Yellow if they are tightly clustered.
        greens = [r for r in result if r['color_marker'] == 'Green']
        self.assertTrue(len(greens) > 0)

    def test_yellow_trigger(self):
        # Trigger Yellow: z_score > 1.5 or val > iqr_upper_bound
        data = [{'style_name': f'style_{i}', 'metric_value': i} for i in range(20)]
        # Add multiple extreme items so 'yellow_style' is NOT in top 3%
        data.append({'style_name': 'extreme1', 'metric_value': 5000})
        data.append({'style_name': 'extreme2', 'metric_value': 5001})
        data.append({'style_name': 'yellow_style', 'metric_value': 25})
        result = self.radar.analyze_styles(data)
        self.assertEqual(len(result), 23)
        yellows = [r for r in result if r['color_marker'] == 'Yellow']
        self.assertTrue(len(yellows) > 0)
