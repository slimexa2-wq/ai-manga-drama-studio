import unittest
import math
from ultra_modules.sfx_waveform_auto_mixer_anomaly_radar import (
    generate_sfx_waveform_path,
    generate_ffmpeg_mix_command,
    scan_anomalies_radar
)

class TestSFXWaveformAutoMixerAnomalyRadar(unittest.TestCase):

    def test_waveform_path_normal_and_dirty_data(self):
        # Normal
        self.assertEqual(generate_sfx_waveform_path("sword_clash", 2.5), "/auto_mixer/sfx/sword_clash_int2.50.wav")
        # Dirty data self-healing: invalid type
        self.assertEqual(generate_sfx_waveform_path(123, "not_float"), "/auto_mixer/sfx/heavy_bass_int1.00.wav")
        # Default missing parameter
        self.assertEqual(generate_sfx_waveform_path(), "/auto_mixer/sfx/heavy_bass_int1.00.wav")
        # Negative intensity self-healing
        self.assertEqual(generate_sfx_waveform_path("transition_whoosh", -5.0), "/auto_mixer/sfx/transition_whoosh_int1.00.wav")
        # Invalid effect type
        self.assertEqual(generate_sfx_waveform_path("magic_spell", 1.5), "/auto_mixer/sfx/heavy_bass_int1.50.wav")

    def test_ffmpeg_mix_command_generation(self):
        # Normal
        paths = ["track1.wav", "track2.wav", "track3.wav"]
        cmd = generate_ffmpeg_mix_command(paths, "output.wav")
        self.assertIn("-i 'track1.wav' -i 'track2.wav' -i 'track3.wav'", cmd)
        self.assertIn("[0:a][1:a][2:a]amix=inputs=3:duration=longest[a]", cmd)
        self.assertIn("-map '[a]' 'output.wav'", cmd)

        # Missing parameters fallback
        self.assertEqual(generate_ffmpeg_mix_command(), "")
        self.assertEqual(generate_ffmpeg_mix_command([]), "")

        # Dirty data self-healing: empty paths or non-string paths
        paths_dirty = ["track1.wav", "", None, 123, "  track2.wav  "]
        cmd_dirty = generate_ffmpeg_mix_command(paths_dirty, 123)
        self.assertIn("-i 'track1.wav' -i 'track2.wav'", cmd_dirty)
        self.assertIn("-map '[a]' 'final_mix.wav'", cmd_dirty) # Default output fallback

    def test_anomaly_radar_normal_scan(self):
        # Create 100 values: 97 normal (around 10), 3 anomalies (Red/Yellow)
        # To get 3% Top anomalies, we need n=100.
        values = [10.0] * 97 + [100.0, 50.0, 0.0]
        results = scan_anomalies_radar(values)
        self.assertEqual(len(results), 100)

        red_count = 0
        yellow_count = 0
        green_count = 0
        for r in results:
            if r["status"] == "Red":
                red_count += 1
                self.assertEqual(r["reason"], "极度偏离正常水平，存在严重风险，务必人工确认！")
            elif r["status"] == "Yellow":
                yellow_count += 1
                self.assertEqual(r["reason"], "数值出现异常偏离，建议抽查确认。")
            elif r["status"] == "Green":
                green_count += 1
                self.assertEqual(r["reason"], "正常，静默放行。")

        # Top 3% of 100 is 3 items. They should be red or yellow.
        self.assertEqual(red_count + yellow_count, 3)
        self.assertEqual(green_count, 97)

    def test_anomaly_radar_dirty_data_self_healing(self):
        # Dirty data should be treated as 0.0
        values = [10.0, None, "invalid", 20.0, [1,2,3], 15.0]
        results = scan_anomalies_radar(values)
        self.assertEqual(len(results), 6)
        clean_values_mapped = [r["value"] for r in results]
        self.assertEqual(clean_values_mapped, [10.0, 0.0, 0.0, 20.0, 0.0, 15.0])

        # Missing parameter fallback
        self.assertEqual(scan_anomalies_radar(), [])

    def test_anomaly_radar_extreme_boundaries(self):
        # Empty list
        self.assertEqual(scan_anomalies_radar([]), [])

        # Single element list
        res_single = scan_anomalies_radar([5.0])
        self.assertEqual(len(res_single), 1)
        self.assertEqual(res_single[0]["z_score"], 0.0)
        self.assertEqual(res_single[0]["status"], "Red" if res_single[0]["status"] == "Red" else "Yellow") # ceiling(1*0.03)=1 -> top 1

        # Two element list, identical values (std_dev = 0)
        res_zero_std = scan_anomalies_radar([10.0, 10.0, 10.0])
        self.assertEqual(len(res_zero_std), 3)
        for r in res_zero_std:
            self.assertEqual(r["z_score"], 0.0)

    def test_iqr_branch_coverage(self):
        # Test IQR path explicitly with a small sample
        # Even number
        results_even = scan_anomalies_radar([1.0, 2.0, 3.0, 100.0])
        self.assertEqual(len(results_even), 4)

        # Odd number
        results_odd = scan_anomalies_radar([1.0, 2.0, 3.0, 4.0, 100.0])
        self.assertEqual(len(results_odd), 5)

if __name__ == '__main__':
    unittest.main()
