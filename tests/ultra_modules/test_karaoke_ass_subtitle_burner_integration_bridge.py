import unittest
from ultra_modules.karaoke_ass_subtitle_burner_integration_bridge import bridge_integration_payload, _safe_get

class TestKaraokeAssSubtitleBurnerIntegrationBridge(unittest.TestCase):

    def test_normal_v1_schema(self):
        """Test with straightforward flat v1 schema."""
        payload = {
            "text": "正常的第一版文本",
            "duration_sec": 5.5,
            "highlight_keywords": ["正常", "文本"],
            "input_video": "v1_in.mp4",
            "output_video": "v1_out.mp4",
            "ass_file_path": "v1_sub.ass"
        }
        result = bridge_integration_payload(payload)

        self.assertEqual(result["text"], "正常的第一版文本")
        self.assertEqual(result["duration_sec"], 5.5)
        self.assertEqual(result["highlight_keywords"], ["正常", "文本"])
        self.assertEqual(result["input_video"], "v1_in.mp4")
        self.assertEqual(result["output_video"], "v1_out.mp4")
        self.assertEqual(result["ass_file_path"], "v1_sub.ass")

    def test_v2_schema_auto_mapping(self):
        """Test auto-mapping for nested v2 and v3 schemas."""
        payload = {
            "subtitle": {
                "text": "嵌套的字幕文本",
                "duration": "4.2"
            },
            "effects": {
                "highlights": ["嵌套", "字幕"]
            },
            "media": {
                "source_video": "nested_in.mp4",
                "target_video": "nested_out.mp4"
            },
            "files": {
                "ass_path": "nested.ass"
            }
        }
        result = bridge_integration_payload(payload)

        self.assertEqual(result["text"], "嵌套的字幕文本")
        self.assertEqual(result["duration_sec"], 4.2)
        self.assertEqual(result["highlight_keywords"], ["嵌套", "字幕"])
        self.assertEqual(result["input_video"], "nested_in.mp4")
        self.assertEqual(result["output_video"], "nested_out.mp4")
        self.assertEqual(result["ass_file_path"], "nested.ass")

    def test_missing_params_fallback(self):
        """Test fallback behavior when payload is empty or None."""
        # Test empty dict
        result1 = bridge_integration_payload({})
        self.assertEqual(result1["text"], "默认字幕")
        self.assertEqual(result1["duration_sec"], 3.0)
        self.assertIn("震惊", result1["highlight_keywords"])
        self.assertEqual(result1["input_video"], "input.mp4")

        # Test None payload
        result2 = bridge_integration_payload(None)
        self.assertEqual(result2["text"], "默认字幕")
        self.assertEqual(result2["duration_sec"], 3.0)
        self.assertEqual(result2["output_video"], "output.mp4")
        self.assertEqual(result2["ass_file_path"], "subtitles.ass")

    def test_dirty_data_self_healing(self):
        """Test self-healing with incorrect types and dirty data."""
        payload = {
            "text": 12345,  # Number instead of string
            "duration_sec": "invalid_duration",  # String instead of number
            "highlight_keywords": [None, "", "  有效词  ", 456],  # Dirty list
            "input_video": None,  # Explicit None
        }
        result = bridge_integration_payload(payload)

        self.assertEqual(result["text"], "12345")
        self.assertEqual(result["duration_sec"], 3.0)  # Fallback
        self.assertEqual(result["highlight_keywords"], ["有效词", "456"])
        self.assertEqual(result["input_video"], "input.mp4")  # Fallback

    def test_extreme_boundaries(self):
        """Test extreme boundaries such as negative duration or excessively nested payload."""
        payload = {
            "duration_sec": -10.0,
            "highlight_keywords": [], # Empty list
            "v2_schema": {
                "dialogue": "   ", # Whitespace string
                "emphasis_words": []
            }
        }
        result = bridge_integration_payload(payload)

        self.assertEqual(result["text"], "默认字幕") # Whitespace should be ignored or mapped to fallback
        self.assertEqual(result["duration_sec"], 3.0) # Negative should fallback to 3.0
        self.assertIn("逆天", result["highlight_keywords"]) # Should fallback to default keywords if empty list

    def test_safe_get_helper(self):
        """Test the _safe_get utility function directly."""
        data = {"a": {"b": {"c": 10}}}
        self.assertEqual(_safe_get(data, ["a", "b", "c"]), 10)
        self.assertEqual(_safe_get(data, ["a", "x", "c"], "default"), "default")
        self.assertEqual(_safe_get(None, ["a"], "def"), "def")
        self.assertEqual(_safe_get({"a": 1}, ["a", "b"]), None)

if __name__ == '__main__':
    unittest.main()
