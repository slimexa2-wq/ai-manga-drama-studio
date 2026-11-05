import unittest
import time
from unittest.mock import patch

from ultra_modules.sfx_waveform_auto_mixer_self_healing_guard import SFXWaveformAutoMixerSelfHealingGuard

class TestSFXWaveformAutoMixerSelfHealingGuard(unittest.TestCase):
    def setUp(self):
        self.guard = SFXWaveformAutoMixerSelfHealingGuard(undo_window_seconds=1.0)

    def test_normal_execution_and_snapshot(self):
        """测试正常执行与快照检索"""
        tracks = [{"file_path": "bgm.wav", "volume": 0.8}]
        self.guard.set_tracks(tracks)

        current = self.guard.get_tracks()
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["file_path"], "bgm.wav")
        self.assertEqual(current[0]["volume"], 0.8)

        # Add another track, should trigger snapshot
        self.guard.add_track({"file_path": "impact.wav"})

        current2 = self.guard.get_tracks()
        self.assertEqual(len(current2), 2)

        # Undo addition
        success = self.guard.undo()
        self.assertTrue(success)

        reverted = self.guard.get_tracks()
        self.assertEqual(len(reverted), 1)
        self.assertEqual(reverted[0]["file_path"], "bgm.wav")

    def test_dirty_data_self_healing(self):
        """测试脏数据自愈逻辑"""
        # 测试异常参数初始化
        bad_guard = SFXWaveformAutoMixerSelfHealingGuard(undo_window_seconds="invalid")
        self.assertEqual(bad_guard._undo_window_seconds, 5.0)

        # 混合各种脏数据
        dirty_tracks = [
            {"file_path": "a.wav", "volume": -5.0}, # 负音量自愈
            "b.wav", # 纯字符串自愈
            {"file_path": "c.wav", "start_time": "invalid_time"}, # 错误时间类型自愈
            None, # 无效类型
            {"invalid_key": "val"} # 缺file_path直接忽略
        ]

        self.guard.set_tracks(dirty_tracks)
        clean = self.guard.get_tracks()

        self.assertEqual(len(clean), 3)
        self.assertEqual(clean[0]["volume"], 1.0) # 自愈为默认
        self.assertEqual(clean[1]["file_path"], "b.wav")
        self.assertEqual(clean[2]["start_time"], 0.0)

        # 测试极度宽容的输入规范化: string
        self.guard.set_tracks("  single.wav  ")
        self.assertEqual(len(self.guard.get_tracks()), 1)
        self.assertEqual(self.guard.get_tracks()[0]["file_path"], "single.wav")

        # None
        self.guard.set_tracks(None)
        self.assertEqual(len(self.guard.get_tracks()), 0)

        # int (unsupported) -> silenty ignore
        self.guard.set_tracks(123)
        self.assertEqual(len(self.guard.get_tracks()), 0)

        # string without dict in add_track
        self.guard.add_track("hello.wav")
        self.assertEqual(len(self.guard.get_tracks()), 1)

    def test_missing_parameter_fallbacks_and_safe_calls(self):
        """测试缺参后备逻辑与方法的异常安全执行"""
        self.guard.set_tracks([{"file_path": "test.wav"}])

        # 测试安全命令生成
        cmd1 = self.guard.generate_ffmpeg_mix_command()
        self.assertIn("ffmpeg", cmd1)
        self.assertIn("test.wav", cmd1)

        cmd2 = self.guard.generate_ffmpeg_mix_command(None)
        self.assertIn("output.wav", cmd2)

        # 测试波形安全合成
        wave1 = self.guard.synthesize_waveform_data()
        self.assertEqual(wave1["duration"], 1.0)

        wave2 = self.guard.synthesize_waveform_data("invalid_dur")
        self.assertEqual(wave2["duration"], 1.0)

        wave3 = self.guard.synthesize_waveform_data(-5.0)
        self.assertEqual(wave3["duration"], 1.0)

        # 强制制造异常模拟内部抛出，确保捕获不中断
        with patch.object(self.guard._mixer, 'generate_ffmpeg_mix_command', side_effect=Exception("mocked error")):
            cmd3 = self.guard.generate_ffmpeg_mix_command("safe.wav")
            self.assertIn("anullsrc", cmd3)
            self.assertIn("safe.wav", cmd3)

        with patch.object(self.guard._mixer, 'synthesize_waveform_data', side_effect=Exception("mocked error")):
            wave4 = self.guard.synthesize_waveform_data(2.0)
            self.assertEqual(wave4["duration"], 1.0)

    def test_extreme_boundary_conditions(self):
        """测试极端边界：快照过期，空快照栈操作"""
        self.assertFalse(self.guard.undo()) # Empty

        self.guard.set_tracks("test1.wav")
        self.assertEqual(len(self.guard.get_tracks()), 1)

        # 睡超过 window_seconds (1.0s)
        time.sleep(1.1)

        # 快照应该过期，撤销失败
        self.assertFalse(self.guard.undo())
        self.assertEqual(len(self.guard.get_tracks()), 1) # 仍然是test1

        self.guard.clear_tracks()
        self.assertEqual(len(self.guard.get_tracks()), 0)

        self.assertTrue(self.guard.undo())
        self.assertEqual(len(self.guard.get_tracks()), 1) # 撤销清除

    def test_full_snapshot_workflow(self):
        """完整的快照流工作链"""
        self.guard.set_tracks("1.wav")
        self.guard.add_track("2.wav")
        self.guard.add_track("3.wav")

        self.assertEqual(len(self.guard.get_tracks()), 3)

        # 第一次undo
        self.assertTrue(self.guard.undo())
        self.assertEqual(len(self.guard.get_tracks()), 2)

        # 第二次undo
        self.assertTrue(self.guard.undo())
        self.assertEqual(len(self.guard.get_tracks()), 1)

        # 第三次undo
        self.assertTrue(self.guard.undo())
        self.assertEqual(len(self.guard.get_tracks()), 0)

        # 第四次undo (空)
        self.assertFalse(self.guard.undo())

    def test_exception_swallowing_in_core_methods(self):
        """测试核心方法的异常静默吞噬机制"""
        # 测试 cleanup 异常
        with patch('time.time', side_effect=Exception("time error")):
            # set_tracks 里面会触发 save_snapshot 触发 _cleanup_old_snapshots
            self.guard.set_tracks("1.wav")
            # 异常被吞噬，不会报错，但添加成功
            self.assertEqual(len(self.guard.get_tracks()), 1)

        # 测试 set_tracks 整体异常
        with patch.object(self.guard, '_safe_normalize_input', side_effect=Exception("norm error")):
            self.guard.set_tracks("2.wav")
            # 吞噬了异常，所以还是 1.wav
            self.assertEqual(len(self.guard.get_tracks()), 1)

        # 测试 add_track 整体异常
        with patch.object(self.guard, '_safe_normalize_input', side_effect=Exception("norm error2")):
            self.guard.add_track("2.wav")
            # 吞噬了异常，所以还是 1.wav
            self.assertEqual(len(self.guard.get_tracks()), 1)

if __name__ == '__main__':
    unittest.main()
