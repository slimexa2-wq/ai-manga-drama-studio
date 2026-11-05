import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from ultra_modules.karaoke_ass_subtitle_burner_audit_trace import KaraokeSubtitleBurner, SubtitleAuditTracer

class TestKaraokeSubtitleBurner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ass_path = os.path.join(self.temp_dir.name, "output.ass")
        self.output_path = os.path.join(self.temp_dir.name, "output.mp4")
        self.burner = KaraokeSubtitleBurner()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normal_execution(self):
        """Test with clean, well-formed subtitle data."""
        subtitles = [
            {
                "text": "Hello world",
                "start": 0.0,
                "end": 1.0,
                "words": [
                    {"word": "Hello", "start": 0.0, "end": 0.5},
                    {"word": "world", "start": 0.5, "end": 1.0}
                ]
            }
        ]

        result = self.burner.process(subtitles, ass_path=self.ass_path, output_path=self.output_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["result_path"], self.ass_path)
        self.assertTrue(os.path.exists(self.ass_path))

        with open(self.ass_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("{\\k50}Hello {\\k50}world", content)

    def test_dirty_data_healing_string(self):
        """Test healing when subtitles is just a string."""
        subtitles = "Just a simple string"
        result = self.burner.process(subtitles, ass_path=self.ass_path)
        self.assertTrue(result["success"])

        with open(self.ass_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Dialogue: 0,0:00:00.00,0:00:02.00", content)
            self.assertIn("{\\k50}Just {\\k50}a {\\k50}simple {\\k50}string", content)

    def test_dirty_data_healing_dict(self):
        """Test healing when subtitles is a single dict instead of list."""
        subtitles = {"text": "A dict"}
        result = self.burner.process(subtitles, ass_path=self.ass_path)
        self.assertTrue(result["success"])

        with open(self.ass_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("{\\k100}A {\\k100}dict", content)

    def test_dirty_data_healing_invalid_types_and_missing_values(self):
        """Test healing with missing timestamps, overlapping timestamps, invalid types."""
        subtitles = [
            "invalid_not_dict", # should be skipped
            {"text": "", "start": 0, "end": 1}, # Empty text, should skip
            {"text": None, "start": 0, "end": 1}, # None text, should be skipped
            {"text": 123, "start": 0, "end": 1}, # int text, should be converted
            {"text": "First", "start": "invalid", "end": "invalid"}, # Fallback to 1.0-3.0
            {"text": "Second", "start": 1.0, "end": 0.5}, # End < Start, heal to 3.0-5.0
            {"text": "Third", "start": 0.5, "end": 4.0}, # Start < Last End (5.0), heal to 5.0-7.0
            {"text": "Fourth", "start": 7.0, "end": 8.0, "words": [
                {"word": "A"},
                {"word": "", "start": 7.1, "end": 7.2},
                {"word": 1, "start": "invalid", "end": "invalid"},
                {"word": "B", "start": 7.3, "end": 7.2}, # w_end < w_start
                {"word": "C", "start": 7.2, "end": 7.4}, # w_start < last end
                "not_a_dict"
            ]},
            {"text": "   ", "start": 8.0, "end": 9.0}, # empty after strip
            {"text": "Fifth", "start": 9.0, "end": 10.0, "words": [{"word": "  "}]}, # empty word after strip, heals to default words
            {"text": "Sixth", "start": 10.0, "end": 11.0, "words": [{"word": "Sixth", "start": 10.0, "end": 12.0}]}, # word end > end, heals actual_end
            {"text": "   ", "start": 11.0, "end": 12.0}, # heals split_text empty
            {"text": "   ", "start": 12.0, "end": 13.0, "words": []} # split_text will be fallback empty list, then to [text]
        ]
        result = self.burner.process(subtitles, ass_path=self.ass_path)
        self.assertTrue(result["success"])

        with open(self.ass_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{\\k100}123", content)
            self.assertIn("Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k200}First", content)
            self.assertIn("Dialogue: 0,0:00:03.00,0:00:05.00,Default,,0,0,0,,{\\k200}Second", content)
            self.assertIn("Dialogue: 0,0:00:05.00,0:00:07.00,Default,,0,0,0,,{\\k200}Third", content)
            self.assertIn("Dialogue: 0,0:00:07.00,0:00:08.00,Default,,0,0,0,,{\\k9}A {\\k9}1 {\\k9}B {\\k0}C", content)

    def test_empty_or_invalid_input(self):
        """Test extreme boundary where input is completely invalid or results in empty subtitles."""
        result = self.burner.process(None, ass_path=self.ass_path)
        self.assertTrue(result["success"])
        self.assertIsNone(result["result_path"])
        self.assertEqual(result["message"], "No valid subtitles found")

    @patch("builtins.open")
    def test_ass_write_failure(self, mock_open):
        """Test handling of ASS file write failure."""
        mock_open.side_effect = PermissionError("Access denied")
        subtitles = [{"text": "Test"}]
        result = self.burner.process(subtitles, ass_path=self.ass_path)
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Failed to write ASS file")

    @patch("subprocess.run")
    def test_ffmpeg_success(self, mock_run):
        """Test ffmpeg burning success."""
        mock_run.return_value = MagicMock(returncode=0)
        subtitles = [{"text": "Test"}]

        # Create a dummy video file
        video_path = os.path.join(self.temp_dir.name, "input.mp4")
        with open(video_path, "w") as f:
            f.write("dummy video")

        result = self.burner.process(subtitles, video_path=video_path, ass_path=self.ass_path, output_path=self.output_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["result_path"], self.output_path)

    @patch("subprocess.run")
    def test_ffmpeg_failure_fallback(self, mock_run):
        """Test ffmpeg failure falling back silently to ASS path."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")
        subtitles = [{"text": "Test"}]

        video_path = os.path.join(self.temp_dir.name, "input.mp4")
        with open(video_path, "w") as f:
            f.write("dummy video")

        result = self.burner.process(subtitles, video_path=video_path, ass_path=self.ass_path, output_path=self.output_path)
        self.assertTrue(result["success"])
        # Falls back to ASS path
        self.assertEqual(result["result_path"], self.ass_path)

    @patch("subprocess.run")
    def test_ffmpeg_exception_fallback(self, mock_run):
        """Test ffmpeg exception falling back silently to ASS path."""
        mock_run.side_effect = FileNotFoundError("ffmpeg not found")
        subtitles = [{"text": "Test"}]

        video_path = os.path.join(self.temp_dir.name, "input.mp4")
        with open(video_path, "w") as f:
            f.write("dummy video")

        result = self.burner.process(subtitles, video_path=video_path, ass_path=self.ass_path, output_path=self.output_path)
        self.assertTrue(result["success"])
        # Falls back to ASS path
        self.assertEqual(result["result_path"], self.ass_path)

    @patch("subprocess.run")
    def test_ffmpeg_other_exception_fallback(self, mock_run):
        """Test ffmpeg other exception falling back silently to ASS path."""
        mock_run.side_effect = Exception("Unknown error")
        subtitles = [{"text": "Test"}]

        video_path = os.path.join(self.temp_dir.name, "input.mp4")
        with open(video_path, "w") as f:
            f.write("dummy video")

        result = self.burner.process(subtitles, video_path=video_path, ass_path=self.ass_path, output_path=self.output_path)
        self.assertTrue(result["success"])
        # Falls back to ASS path
        self.assertEqual(result["result_path"], self.ass_path)

    def test_video_not_found(self):
        """Test missing video file falls back to ASS."""
        subtitles = [{"text": "Test"}]
        result = self.burner.process(subtitles, video_path="nonexistent.mp4", ass_path=self.ass_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["result_path"], self.ass_path)

if __name__ == '__main__':
    unittest.main()
