import unittest
import os
from ultra_modules.karaoke_ass_subtitle_burner_core_engine import (
    format_timestamp_ass,
    clean_text,
    generate_karaoke_ass_content,
    get_ffmpeg_burn_command
)

class TestKaraokeAssSubtitleBurnerCoreEngine(unittest.TestCase):

    def test_format_timestamp_ass(self):
        # Normal
        self.assertEqual(format_timestamp_ass(3661.123), "1:01:01.12")
        self.assertEqual(format_timestamp_ass(0), "0:00:00.00")

        # Edge cases & dirty data
        self.assertEqual(format_timestamp_ass(-5.5), "0:00:00.00")
        self.assertEqual(format_timestamp_ass("invalid"), "0:00:00.00")
        self.assertEqual(format_timestamp_ass(None), "0:00:00.00")

    def test_clean_text(self):
        self.assertEqual(clean_text("  hello  "), "hello")
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text(123), "123")

    def test_generate_karaoke_ass_content_normal(self):
        text = "震惊！魔帝重生了，这也太逆天了吧！"
        duration = 5.0
        content = generate_karaoke_ass_content(text, duration)

        self.assertIn("[Script Info]", content)
        self.assertIn("[Events]", content)
        self.assertIn("Dialogue:", content)

        # Keyword highlighting should be applied
        self.assertIn("震", content)
        self.assertIn("惊", content)
        self.assertIn("魔", content)
        self.assertIn("帝", content)
        self.assertIn("逆", content)
        self.assertIn("天", content)
        self.assertIn("{\\c&H0000FF&\\fscx150\\fscy150\\t(0,200,\\fscx120\\fscy120)}", content)

        # Karaoke tags
        self.assertIn("{\\k", content)

    def test_generate_karaoke_ass_content_missing_params_and_dirty_data(self):
        # Missing/dirty parameters
        content = generate_karaoke_ass_content(text=None, duration_sec="abc", highlight_keywords=123)
        self.assertIn("默", content)
        self.assertIn("认", content)
        self.assertIn("字", content)
        self.assertIn("幕", content)

        content2 = generate_karaoke_ass_content(text="", duration_sec=-10, highlight_keywords=[None, "", "关键字"])
        self.assertIn("默", content2)
        self.assertIn("幕", content2)

        # Empty sentence fallback
        content3 = generate_karaoke_ass_content(text="...", duration_sec=3.0)
        self.assertIn("Dialogue:", content3)

    def test_get_ffmpeg_burn_command(self):
        # Normal
        cmd = get_ffmpeg_burn_command("in.mp4", "sub.ass", "out.mp4")
        self.assertEqual(cmd, ["ffmpeg", "-y", "-i", "in.mp4", "-vf", "ass='sub.ass'", "-c:a", "copy", "out.mp4"])

        # Appending to existing filter
        cmd2 = get_ffmpeg_burn_command("in.mp4", "sub.ass", "out.mp4", "scale=1920:1080")
        self.assertIn("-vf", cmd2)
        idx = cmd2.index("-vf")
        self.assertEqual(cmd2[idx + 1], "scale=1920:1080,ass='sub.ass'")

        # Missing parameters fallback
        cmd3 = get_ffmpeg_burn_command(None, None, None, None)
        self.assertEqual(cmd3, ["ffmpeg", "-y", "-i", "input.mp4", "-vf", "ass='subtitles.ass'", "-c:a", "copy", "output.mp4"])

        # Escaping
        cmd4 = get_ffmpeg_burn_command("in.mp4", "folder\\sub's.ass", "out.mp4")
        idx = cmd4.index("-vf")
        self.assertEqual(cmd4[idx + 1], "ass='folder/sub\\'s.ass'")

if __name__ == '__main__':
    unittest.main()
