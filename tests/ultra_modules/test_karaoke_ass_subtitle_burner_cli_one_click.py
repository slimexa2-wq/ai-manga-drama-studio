import unittest
import os
import tempfile
import json
from unittest.mock import patch
from ultra_modules.karaoke_ass_subtitle_burner_cli_one_click import (
    parse_input_data,
    format_ass_time,
    generate_karaoke_ass,
    run_one_click,
    ensure_dummy_video,
    burn_subtitles_to_video
)

class TestKaraokeAssSubtitleBurner(unittest.TestCase):

    def test_parse_input_data_normal_json(self):
        """Test parsing valid JSON string."""
        json_data = '[{"text": "系统觉醒", "start": 1.0, "end": 2.5}]'
        parsed = parse_input_data(json_data)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["text"], "系统觉醒")
        self.assertEqual(parsed[0]["start"], 1.0)
        self.assertEqual(parsed[0]["end"], 2.5)

    def test_parse_input_data_dirty_healing(self):
        """Test healing dirty data (missing start/end, wrong types, missing text)."""
        dirty_data = [
            {"text": "第一句"}, # Missing start/end
            {"text": "", "start": "invalid", "end": "wrong"}, # Empty text, string times
            {"text": "第三句", "start": 5.0, "end": 2.0} # End before start
        ]
        parsed = parse_input_data(dirty_data)
        self.assertEqual(len(parsed), 3)
        # First item defaults based on current_time=0.0
        self.assertEqual(parsed[0]["start"], 0.0)
        self.assertEqual(parsed[0]["end"], 2.0)
        # Second item, text is empty so fallback to "...", times fallback and build on previous
        self.assertEqual(parsed[1]["text"], "...")
        self.assertEqual(parsed[1]["start"], 2.0)
        self.assertEqual(parsed[1]["end"], 4.0)
        # Third item, end < start, heals to start + 2.0
        self.assertEqual(parsed[2]["start"], 5.0)
        self.assertEqual(parsed[2]["end"], 7.0)

    def test_parse_input_data_extreme_boundary(self):
        """Test with None and empty list, should fallback to default."""
        parsed_none = parse_input_data(None)
        self.assertEqual(len(parsed_none), 1)
        self.assertEqual(parsed_none[0]["text"], "默认动态字幕")

        parsed_empty = parse_input_data([])
        self.assertEqual(len(parsed_empty), 1)
        self.assertEqual(parsed_empty[0]["text"], "默认动态字幕")

    def test_generate_karaoke_ass_formatting(self):
        """Test ASS generation and karaoke effect formatting."""
        data = [{"text": "震惊！无敌的魔帝重生了", "start": 0.0, "end": 2.0}]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ass") as tmp:
            ass_path = tmp.name

        try:
            generate_karaoke_ass(data, ass_path)
            with open(ass_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertIn("Script Info", content)
            self.assertIn("Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,", content)
            # Check for keyword highlight formatting
            self.assertIn("{\\c&H0000FF&\\fscx150\\fscy150}", content) # Highlighting for keywords
            self.assertIn("{\\k", content) # Karaoke effect

        finally:
            if os.path.exists(ass_path):
                os.remove(ass_path)

    @patch('subprocess.run')
    def test_run_one_click_defaults(self, mock_run):
        """Test the one-click CLI entry point with defaults (no parameters)."""
        # Mock subprocess.run to just return a successful result to avoid actual ffmpeg calls during unit tests
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""

        video_out = "test_out.mp4"
        try:
            out = run_one_click(video_out=video_out)
            self.assertEqual(out, video_out)
            # Check that subprocess.run was called for dummy video and subtitle burning
            self.assertTrue(mock_run.called)
        finally:
            if os.path.exists(video_out):
                os.remove(video_out)

if __name__ == '__main__':
    unittest.main()
