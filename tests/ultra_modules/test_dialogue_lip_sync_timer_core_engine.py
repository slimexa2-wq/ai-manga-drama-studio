import unittest
import math
from ultra_modules.dialogue_lip_sync_timer_core_engine import calculate_scene_duration

class TestDialogueLipSyncTimerCoreEngine(unittest.TestCase):
    def test_basic_text_only(self):
        """测试只有文字的计算"""
        # 10 chars, wpm 250 (4.16 chars/sec) -> 2.4s + 0.5 padding = 2.9s
        res = calculate_scene_duration(text="一二三四五六七八九十", wpm=250, padding=0.5)
        self.assertAlmostEqual(res, 2.9, places=2)

    def test_text_with_punctuation(self):
        """测试文字带标点"""
        # 10 chars, 2 puncts (0.5s each), wpm=300 (5 chars/sec)
        # text_dur = (10 / 5) + 2 * 0.5 = 3.0s
        # final = 3.0s + 0.5s padding = 3.5s
        res = calculate_scene_duration(text="一二三四五，六七八九十。", wpm=300, padding=0.5)
        self.assertAlmostEqual(res, 3.5, places=2)

    def test_audio_duration_priority(self):
        """测试音频时长优先级最高"""
        res = calculate_scene_duration(text="短文字", audio_duration=10.0, padding=1.0)
        self.assertEqual(res, 11.0)

    def test_dirty_data_fallback(self):
        """测试脏数据自愈"""
        res = calculate_scene_duration(
            text=None,
            audio_duration="invalid",
            waveform_peaks=[1.2, "dirty", -5, math.nan, 3.5],
            wpm=0,
            punctuation_pause=-1,
            min_duration=None,
            padding="bad"
        )
        # 此时 fallback：
        # text = ""
        # audio_duration = 0.0
        # clean_peaks = [1.2, 3.5]
        # wpm = 250
        # punctuation_pause = 0.5
        # min_duration = 1.0
        # padding = 0.5
        # peak_duration = 3.5
        # text_duration = 0
        # base_duration = 3.5
        # final = 3.5 + 0.5 = 4.0
        self.assertEqual(res, 4.0)

    def test_min_duration_clamp(self):
        """测试最短时长限制"""
        res = calculate_scene_duration(text="", padding=0, min_duration=5.0)
        self.assertEqual(res, 5.0)

if __name__ == '__main__':
    unittest.main()
