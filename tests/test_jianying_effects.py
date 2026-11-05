import json
import unittest
from src.jianying_effects_enricher import enrich_draft_content
from src.storyboard_engine import build_storyboard

class TestJianyingEffectsEnricher(unittest.TestCase):
    def setUp(self):
        self.sample_storyboard = {
            "title": "测试",
            "style": {"default_bgm_mood": "default_bgm"},
            "shots": [
                {
                    "shot_id": "SHOT_01",
                    "start_ms": 0,
                    "duration_ms": 3000,
                    "emotion": "shock",
                    "camera_motion": "shake",
                    "subtitle_text": "什么？！"
                },
                {
                    "shot_id": "SHOT_02",
                    "start_ms": 3000,
                    "duration_ms": 3000,
                    "emotion": "calm",
                    "camera_motion": "pan",
                    "subtitle_text": "没关系。"
                }
            ]
        }

        self.sample_draft_content = {
            "materials": {
                "texts": [
                    {"id": "TXT_01", "content": json.dumps({"text": "什么？！"})},
                    {"id": "TXT_02", "content": json.dumps({"text": "没关系。"})},
                ]
            },
            "tracks": [
                {
                    "type": "video",
                    "segments": [
                        {"id": "SEG_01", "target_timerange": {"start": 0, "duration": 3000000}},
                        {"id": "SEG_02", "target_timerange": {"start": 3000000, "duration": 3000000}},
                    ]
                }
            ]
        }

    def test_text_highlight_injection(self):
        result = enrich_draft_content(self.sample_draft_content, self.sample_storyboard)
        texts = result["materials"]["texts"]

        # '什么？！' should have text_effects because it contains '！' and '？'
        self.assertIn("text_effects", texts[0])
        self.assertEqual(texts[0]["text_effects"][0]["name"], "高亮花字")

        # '没关系。' should not have text_effects
        self.assertNotIn("text_effects", texts[1])

    def test_transition_and_effects_injection(self):
        result = enrich_draft_content(self.sample_draft_content, self.sample_storyboard)
        video_effects = result["materials"].get("video_effects", [])

        # Shot 1 has 'shock' emotion and 'shake' camera motion -> high tension -> should have video_effect
        self.assertGreater(len(video_effects), 0)
        self.assertEqual(video_effects[0]["name"], "震屏")

        video_track = next(t for t in result["tracks"] if t["type"] == "video")

        # The first segment is high tension but it's the first one, so no transition before it.
        # But it should have the video effect ID linked.
        self.assertIn("video_effects", video_track["segments"][0])
        self.assertEqual(video_track["segments"][0]["video_effects"][0]["id"], video_effects[0]["id"])

        # Let's test a case where a transition is added (i.e., shot > 0 is high tension)
        self.sample_storyboard["shots"][1]["emotion"] = "angry"
        self.sample_storyboard["shots"][1]["camera_motion"] = "fast pan"
        result2 = enrich_draft_content(self.sample_draft_content, self.sample_storyboard)

        transitions = result2["materials"].get("transitions", [])
        self.assertGreater(len(transitions), 0)
        self.assertEqual(transitions[0]["name"], "闪白转场")

        video_track2 = next(t for t in result2["tracks"] if t["type"] == "video")
        self.assertIn("transition_id", video_track2["segments"][1])
        self.assertEqual(video_track2["segments"][1]["transition_id"], transitions[0]["id"])

    def test_bgm_track_injection(self):
        result = enrich_draft_content(self.sample_draft_content, self.sample_storyboard)
        audios = result["materials"].get("audios", [])

        # Should have BGM materials created
        self.assertGreater(len(audios), 0)
        self.assertTrue(any(a["name"] == "mood_bgm_epic_tension_bgm.mp3" for a in audios)) # from first shot (shock/shake)
        self.assertTrue(any(a["name"] == "mood_bgm_default_bgm.mp3" for a in audios)) # from second shot (calm)

        # Should have a BGM track
        bgm_track = next((t for t in result["tracks"] if t.get("flag") == "bgm"), None)
        self.assertIsNotNone(bgm_track)
        self.assertEqual(bgm_track["type"], "audio")
        self.assertEqual(len(bgm_track["segments"]), 2)


if __name__ == "__main__":
    unittest.main()
