import unittest
import json
from ultra_modules.karaoke_ass_subtitle_burner_plain_explainer import KaraokeSubtitleExplainer

class TestKaraokeSubtitleExplainer(unittest.TestCase):

    def test_normal_execution(self):
        """Test with valid and expected inputs."""
        payload = {
            "status": "success",
            "total_subtitles": 45,
            "processed_duration": 12.5,
            "success_rate": 1.0,
            "video_url": "https://example.com/video.mp4"
        }
        result = KaraokeSubtitleExplainer.generate_summary_card(payload)

        self.assertIn("字幕烧录成功。共处理了 45 句逐词高亮字幕", result["plain_text"])
        self.assertIn("总耗时 12.5 秒", result["plain_text"])
        self.assertIn("成功率 100.0%", result["plain_text"])

        self.assertEqual(result["json"]["metrics"]["status"], "成功")
        self.assertEqual(result["json"]["metrics"]["total_subtitles"], 45)
        self.assertEqual(result["json"]["metrics"]["processed_duration"], 12.5)
        self.assertEqual(result["json"]["actions"]["view_video"], "https://example.com/video.mp4")

        self.assertIn("https://example.com/video.mp4", result["html"])
        self.assertIn("https://example.com/video.mp4", result["markdown"])

    def test_missing_parameter_fallback(self):
        """Test with an empty dict to ensure defaults are applied gracefully."""
        payload = {}
        result = KaraokeSubtitleExplainer.generate_summary_card(payload)

        self.assertEqual(result["json"]["metrics"]["status"], "成功")
        self.assertEqual(result["json"]["metrics"]["total_subtitles"], 0)
        self.assertEqual(result["json"]["metrics"]["processed_duration"], 0.0)
        self.assertEqual(result["json"]["metrics"]["success_rate_percentage"], 100.0)
        self.assertEqual(result["json"]["actions"]["view_video"], "#")

    def test_dirty_data_self_healing(self):
        """Test with invalid types and unparseable strings."""
        # Invalid payload type (e.g. integer)
        result1 = KaraokeSubtitleExplainer.generate_summary_card(12345)
        self.assertEqual(result1["json"]["metrics"]["status"], "成功")
        self.assertEqual(result1["json"]["metrics"]["total_subtitles"], 0)

        # Unparseable JSON string
        result2 = KaraokeSubtitleExplainer.generate_summary_card("{this_is_not_json:")
        self.assertEqual(result2["json"]["metrics"]["total_subtitles"], 0)

        # Wrong types inside the dictionary
        payload3 = {
            "status": ["invalid"],
            "total_subtitles": "not_an_int",
            "processed_duration": None,
            "success_rate": "invalid_float",
            "video_url": None
        }
        result3 = KaraokeSubtitleExplainer.generate_summary_card(payload3)
        self.assertEqual(result3["json"]["metrics"]["status"], "成功")
        self.assertEqual(result3["json"]["metrics"]["total_subtitles"], 0)
        self.assertEqual(result3["json"]["metrics"]["processed_duration"], 0.0)
        self.assertEqual(result3["json"]["metrics"]["success_rate_percentage"], 100.0)
        self.assertEqual(result3["json"]["actions"]["view_video"], "#")

    def test_extreme_boundary_cases(self):
        """Test with negative values and extreme cases."""
        payload = {
            "status": "partial",
            "total_subtitles": -10,  # Should become 0
            "processed_duration": -5.5,  # Should become 0.0
            "success_rate": 1.5,  # Should become 1.0
        }
        result = KaraokeSubtitleExplainer.generate_summary_card(payload)

        self.assertEqual(result["json"]["metrics"]["status"], "部分成功")
        self.assertEqual(result["json"]["metrics"]["total_subtitles"], 0)
        self.assertEqual(result["json"]["metrics"]["processed_duration"], 0.0)
        self.assertEqual(result["json"]["metrics"]["success_rate_percentage"], 100.0)

    def test_valid_json_string(self):
        """Test passing a valid JSON string instead of a dict."""
        payload = json.dumps({
            "status": "failed",
            "total_subtitles": 20,
            "processed_duration": 5.0,
            "success_rate": 0.5,
            "video_url": "https://example.com/fail.mp4"
        })
        result = KaraokeSubtitleExplainer.generate_summary_card(payload)

        self.assertEqual(result["json"]["metrics"]["status"], "失败")
        self.assertEqual(result["json"]["metrics"]["total_subtitles"], 20)
        self.assertEqual(result["json"]["metrics"]["processed_duration"], 5.0)
        self.assertEqual(result["json"]["metrics"]["success_rate_percentage"], 50.0)
        self.assertEqual(result["json"]["actions"]["view_video"], "https://example.com/fail.mp4")

if __name__ == "__main__":
    unittest.main()
