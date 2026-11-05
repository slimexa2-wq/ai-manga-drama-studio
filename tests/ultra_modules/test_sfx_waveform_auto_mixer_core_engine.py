import unittest
from ultra_modules.sfx_waveform_auto_mixer_core_engine import SFXWaveformAutoMixer

class TestSFXWaveformAutoMixer(unittest.TestCase):
    def setUp(self):
        self.mixer = SFXWaveformAutoMixer()

    def test_normal_track_mixing(self):
        """测试正常音轨混合，包括多轨与基本参数"""
        tracks = [
            {"file_path": "bgm.wav", "start_time": 0.0, "volume": 0.8, "type": "bgm"},
            {"file_path": "impact.wav", "start_time": 2.5, "volume": 1.5, "type": "impact"},
            {"file_path": "voice.wav", "start_time": 1.0, "volume": 1.0, "type": "voice"}
        ]

        cmd = self.mixer.generate_ffmpeg_mix_command(tracks, "out.wav")
        self.assertIn("ffmpeg", cmd)
        self.assertIn("-i \"bgm.wav\"", cmd)
        self.assertIn("-i \"impact.wav\"", cmd)
        self.assertIn("-i \"voice.wav\"", cmd)
        self.assertIn("amix=inputs=3:duration=longest:dropout_transition=2[out]", cmd)
        self.assertIn("adelay=2500|2500", cmd)
        self.assertIn("volume=0.8", cmd)
        self.assertIn("-y \"out.wav\"", cmd)

    def test_dirty_data_auto_healing(self):
        """测试脏数据自愈：负时间、负音量、错误类型、字符串时间等"""
        tracks = [
            {"file_path": "sword.wav", "start_time": -1.5, "volume": -2.0, "type": "invalid_type"},
            {"file_path": "boom.wav", "start_time": "invalid_time", "volume": "high", "type": "impact"},
            "invalid_track_format",
            {"file_path": "wind.wav", "start_time": 1.5, "volume": 15.0, "type": "transition"}
        ]

        cmd = self.mixer.generate_ffmpeg_mix_command(tracks, "healed.wav")

        # negative start_time healed to 0
        # volume -2.0 healed to 1.0
        # invalid type healed to sfx, but it doesn't affect ffmpeg cmd directly
        self.assertIn("-i \"sword.wav\"", cmd)
        self.assertIn("volume=10.0", cmd) # 15.0 capped to 10.0
        self.assertIn("-i \"boom.wav\"", cmd)
        self.assertIn("-i \"wind.wav\"", cmd)
        self.assertIn("amix=inputs=3:duration=longest", cmd)

        # verify waveform synthesis healing
        waveform = self.mixer.synthesize_waveform_data(tracks, duration=5.0)
        self.assertEqual(len(waveform["events"]), 3)
        self.assertEqual(waveform["events"][0]["time"], 0.0) # start time healed
        self.assertEqual(waveform["events"][0]["intensity"], 1.0) # negative volume healed
        self.assertEqual(waveform["events"][0]["type"], "sfx") # invalid type healed

        self.assertEqual(waveform["events"][1]["time"], 0.0) # invalid time healed to 0

        self.assertEqual(waveform["events"][2]["intensity"], 10.0) # 15 capped to 10

    def test_missing_params_default_fallback(self):
        """测试缺参赋默认值兜底"""
        tracks = [
            {"file_path": "only_path.wav"}
        ]

        cmd = self.mixer.generate_ffmpeg_mix_command(tracks, "default.wav")

        # 只有一个文件，只复制或者没有任何特殊滤镜，这里没有音量或延迟，所以应该是复制
        self.assertIn("-i \"only_path.wav\"", cmd)
        self.assertIn("-c:a copy", cmd)

        waveform = self.mixer.synthesize_waveform_data(tracks, duration=2.0)
        self.assertEqual(len(waveform["events"]), 1)
        self.assertEqual(waveform["events"][0]["time"], 0.0)
        self.assertEqual(waveform["events"][0]["intensity"], 1.0)
        self.assertEqual(waveform["events"][0]["type"], "sfx")

    def test_extreme_boundaries(self):
        """测试极端边界条件（空输入、无file_path的输入等）"""
        # Empty input list
        cmd_empty = self.mixer.generate_ffmpeg_mix_command([], "empty.wav")
        self.assertIn("anullsrc=r=44100:cl=stereo -t 0.1", cmd_empty)

        # Input with no file_path
        tracks_no_path = [{"start_time": 1.0, "volume": 1.0}]
        cmd_no_path = self.mixer.generate_ffmpeg_mix_command(tracks_no_path, "no_path.wav")
        self.assertIn("anullsrc", cmd_no_path)

        waveform_empty = self.mixer.synthesize_waveform_data([], duration=0)
        self.assertEqual(waveform_empty["duration"], 0.1) # 0 healed to 0.1
        self.assertEqual(len(waveform_empty["events"]), 0)
        self.assertEqual(len(waveform_empty["peaks"]), 0)

    def test_waveform_synthesis_fallback(self):
        """测试波形合成兜底逻辑"""
        tracks = [
            {"file_path": "impact1.wav", "start_time": 0.5, "type": "impact"},
            {"file_path": "transition.wav", "start_time": 1.0, "type": "transition"},
            {"file_path": "out_of_bounds.wav", "start_time": 10.0, "type": "sfx"}
        ]

        waveform = self.mixer.synthesize_waveform_data(tracks, duration=2.0)

        # out_of_bounds track should be ignored since start_time >= duration
        self.assertEqual(len(waveform["events"]), 2)

        # impact should have higher intensity
        impact_event = next(e for e in waveform["events"] if e["type"] == "impact")
        self.assertEqual(impact_event["intensity"], 1.5) # default 1.0 * 1.5

        # check peaks generation
        self.assertEqual(len(waveform["peaks"]), 20) # duration 2.0 * 10
        self.assertTrue(all(0.0 <= p <= 1.0 for p in waveform["peaks"]))

if __name__ == '__main__':
    unittest.main()
