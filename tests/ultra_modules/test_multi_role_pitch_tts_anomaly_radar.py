import unittest
from ultra_modules.multi_role_pitch_tts_anomaly_radar import MultiRolePitchTTSAnomalyRadar

class TestMultiRolePitchTTSAnomalyRadar(unittest.TestCase):

    def test_normal_dataset(self):
        """1. Normal dataset (all Green)."""
        items = [{'role': 'hero', 'pitch': 1.0, 'speed': 1.0, 'duration_ms': 1000.0} for _ in range(50)]
        result = MultiRolePitchTTSAnomalyRadar.scan_and_modulate(items)
        for res in result:
            self.assertEqual(res['anomaly_status'], 'GREEN')
            self.assertEqual(res['anomaly_reason'], '正常')

    def test_top_3_percent_anomalies(self):
        """2. Top 3% anomalies (properly marked Red)."""
        items = [{'role': 'villain', 'pitch': 1.0, 'speed': 1.0, 'duration_ms': 1000.0} for _ in range(97)]
        # Add 3 extreme outliers
        items.append({'role': 'villain', 'pitch': 100.0, 'speed': 1.0, 'duration_ms': 1000.0})
        items.append({'role': 'villain', 'pitch': 1.0, 'speed': 0.1, 'duration_ms': 1000.0})
        items.append({'role': 'villain', 'pitch': 1.0, 'speed': 1.0, 'duration_ms': 10000.0})

        result = MultiRolePitchTTSAnomalyRadar.scan_and_modulate(items)

        red_count = sum(1 for res in result if res['anomaly_status'] == 'RED')
        self.assertEqual(red_count, 3, "Exactly 3 RED items expected for Top 3% of 100 items.")

        # Verify reason texts
        self.assertEqual(result[-3]['anomaly_reason'], '音高偏高异常明显')
        self.assertEqual(result[-2]['anomaly_reason'], '语速偏慢异常明显')
        self.assertEqual(result[-1]['anomaly_reason'], '时长偏长异常明显')

    def test_marginal_anomalies(self):
        """3. Marginal anomalies (marked Yellow)."""
        # Create a dataset where 5 items are outliers, but we only mark the top 3 (3%) as RED, leaving 2 as YELLOW
        items = [{'role': 'narrator', 'pitch': 1.0, 'speed': 1.0, 'duration_ms': 1000.0} for _ in range(95)]

        # Outliers that exceed Z-score 1.5 but not all will be in the top 3%
        # The top 3% will be the 3 with the highest Z-scores.
        items.append({'role': 'narrator', 'pitch': 100.0, 'speed': 1.0, 'duration_ms': 1000.0})  # Highest deviation
        items.append({'role': 'narrator', 'pitch': 90.0, 'speed': 1.0, 'duration_ms': 1000.0})   # High deviation
        items.append({'role': 'narrator', 'pitch': 80.0, 'speed': 1.0, 'duration_ms': 1000.0})   # High deviation
        items.append({'role': 'narrator', 'pitch': 30.0, 'speed': 1.0, 'duration_ms': 1000.0})   # Marginal (Yellow) (z=1.64 > 1.5)
        items.append({'role': 'narrator', 'pitch': 28.0, 'speed': 1.0, 'duration_ms': 1000.0})   # Marginal (Yellow) (z=1.51 > 1.5)

        result = MultiRolePitchTTSAnomalyRadar.scan_and_modulate(items)

        red_count = sum(1 for res in result if res['anomaly_status'] == 'RED')
        yellow_count = sum(1 for res in result if res['anomaly_status'] == 'YELLOW')

        self.assertEqual(red_count, 3, "Exactly 3 RED items expected for Top 3%.")
        self.assertEqual(yellow_count, 2, "Exactly 2 YELLOW items expected.")

        for res in result:
            if res['anomaly_status'] == 'YELLOW':
                self.assertIn('轻微偏差静默放行', res['anomaly_reason'])

    def test_dirty_data_self_healing(self):
        """4. Dirty data self-healing (strings, NaNs, missing keys)."""
        import math
        items = [
            {'role': 'hero', 'pitch': 'invalid', 'speed': math.nan, 'duration_ms': None},
            {'role': 'hero'}, # Missing keys
            {'pitch': 5.0} # Missing role
        ]
        result = MultiRolePitchTTSAnomalyRadar.scan_and_modulate(items)

        # Self-healing defaults: role='unknown_role', pitch=0.0, speed=1.0, duration=1000.0
        self.assertEqual(result[0]['pitch'], 0.0)
        self.assertEqual(result[0]['speed'], 1.0)
        self.assertEqual(result[0]['duration_ms'], 1000.0)

        self.assertEqual(result[1]['pitch'], 0.0)
        self.assertEqual(result[1]['speed'], 1.0)

        self.assertEqual(result[2]['role'], 'unknown_role')
        self.assertEqual(result[2]['pitch'], 5.0)

    def test_extreme_boundary_conditions(self):
        """5. Extreme boundary conditions (empty list, single element list, division by zero cases)."""
        # Empty list
        self.assertEqual(MultiRolePitchTTSAnomalyRadar.scan_and_modulate([]), [])

        # Single element
        result_single = MultiRolePitchTTSAnomalyRadar.scan_and_modulate([{'role': 'hero'}])
        self.assertEqual(len(result_single), 1)
        self.assertEqual(result_single[0]['anomaly_status'], 'GREEN')

        # All same values (standard deviation = 0)
        items = [{'role': 'hero', 'pitch': 5.0, 'speed': 2.0} for _ in range(10)]
        result_same = MultiRolePitchTTSAnomalyRadar.scan_and_modulate(items)
        for res in result_same:
            self.assertEqual(res['anomaly_status'], 'GREEN')

if __name__ == '__main__':
    unittest.main()
