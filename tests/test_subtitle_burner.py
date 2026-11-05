import unittest
import os
from src.subtitle_burner import split_sentences, generate_ass, generate_srt, burn_subtitles, HIGHLIGHT_KEYWORDS

class TestSubtitleBurner(unittest.TestCase):
    def test_split_sentences(self):
        text = "震惊！系统觉醒，魔帝重生，他要无敌打脸。逆天反转！"
        expected = ["震惊！", "系统觉醒，", "魔帝重生，", "他要无敌打脸。", "逆天反转！"]
        self.assertEqual(split_sentences(text), expected)

        text2 = "Hello world! This is a test. Wait, what?"
        expected2 = ["Hello world!", "This is a test.", "Wait,", "what?"]
        self.assertEqual(split_sentences(text2), expected2)

    def test_generate_ass(self):
        text = "震惊！魔帝重生！"
        duration = 2.0
        ass_content = generate_ass(text, duration)

        self.assertIn("Script Info", ass_content)
        self.assertIn("0:00:00.00", ass_content)
        self.assertIn("0:00:01.00", ass_content)
        self.assertIn("0:00:02.00", ass_content)

        # Check if highlighting keywords is correct
        self.assertIn("{\\c&H0000FF&\\fscx120\\fscy120}震惊{\\r}", ass_content)
        self.assertIn("{\\c&H0000FF&\\fscx120\\fscy120}魔帝{\\r}", ass_content)
        self.assertIn("{\\c&H0000FF&\\fscx120\\fscy120}重生{\\r}", ass_content)

    def test_generate_srt(self):
        text = "震惊！魔帝重生！"
        duration = 2.0
        srt_content = generate_srt(text, duration)

        self.assertIn("1\n00:00:00,000 --> 00:00:01,000", srt_content)
        self.assertIn("2\n00:00:01,000 --> 00:00:02,000", srt_content)

        self.assertIn("<font color=\"#FF0000\"><b>震惊</b></font>", srt_content)
        self.assertIn("<font color=\"#FF0000\"><b>魔帝</b></font>", srt_content)
        self.assertIn("<font color=\"#FF0000\"><b>重生</b></font>", srt_content)

    def test_burn_subtitles_ass(self):
        text = "系统觉醒！"
        duration = 2.0
        output_path = "test_sub.ass"
        try:
            burn_subtitles(text, duration, output_path, fmt='ass')
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("Script Info", content)
                self.assertIn("{\\c&H0000FF&\\fscx120\\fscy120}系统{\\r}", content)
                self.assertIn("{\\c&H0000FF&\\fscx120\\fscy120}觉醒{\\r}", content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_burn_subtitles_srt(self):
        text = "系统觉醒！"
        duration = 2.0
        output_path = "test_sub.srt"
        try:
            burn_subtitles(text, duration, output_path, fmt='srt')
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("00:00:00,000 -->", content)
                self.assertIn("<font color=\"#FF0000\"><b>系统</b></font>", content)
                self.assertIn("<font color=\"#FF0000\"><b>觉醒</b></font>", content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

if __name__ == '__main__':
    unittest.main()
