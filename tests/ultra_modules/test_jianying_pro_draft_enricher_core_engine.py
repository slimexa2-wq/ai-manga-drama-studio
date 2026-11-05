import json
import unittest
from ultra_modules.jianying_pro_draft_enricher_core_engine import enrich_draft_content

class TestJianyingProDraftEnricherCoreEngine(unittest.TestCase):

    def setUp(self):
        self.sample_draft = {
            "materials": {
                "texts": [
                    {"id": "T1", "content": json.dumps({"text": "什么？！"})},
                    {"id": "T2", "content": json.dumps({"text": "正常文本"})}
                ]
            },
            "tracks": [
                {
                    "type": "video",
                    "segments": [
                        {"id": "S1", "target_timerange": {"start": 0, "duration": 3000000}},
                        {"id": "S2", "target_timerange": {"start": 3000000, "duration": 3000000}}
                    ]
                }
            ]
        }
        self.sample_storyboard = {
            "style": {"default_bgm_mood": "calm_bgm"},
            "shots": [
                {
                    "start_ms": 0,
                    "duration_ms": 3000,
                    "emotion": "shock",
                    "camera_motion": "zoom",
                },
                {
                    "start_ms": 3000,
                    "duration_ms": 3000,
                    "emotion": "calm",
                    "camera_motion": "pan",
                }
            ]
        }

    # 1. Normal usage with fully specified parameters
    def test_normal_usage(self):
        res = enrich_draft_content(self.sample_draft, self.sample_storyboard, options={})

        # Test text effects
        texts = res["materials"]["texts"]
        self.assertTrue("text_effects" in texts[0])
        self.assertEqual(texts[0]["text_effects"][0]["name"], "高亮花字")
        self.assertFalse("text_effects" in texts[1])

        # Test Ken Burns & Transitions
        video_track = next(t for t in res["tracks"] if t["type"] == "video")
        s1, s2 = video_track["segments"]

        self.assertIn("animations", s1)
        self.assertEqual(res["materials"]["animations"][0]["type"], "zoom_in")

        # Transition: added if index > 0 and high tension
        # Let's modify shot 2 to high tension to trigger transition
        storyboard2 = dict(self.sample_storyboard)
        storyboard2["shots"][1]["emotion"] = "shock"
        res2 = enrich_draft_content(self.sample_draft, storyboard2, options={})
        s2_modified = next(t for t in res2["tracks"] if t["type"] == "video")["segments"][1]
        self.assertIn("transition_id", s2_modified)
        self.assertEqual(res2["materials"]["transitions"][0]["name"], "震屏转场")

        # Test BGM
        bgm_track = next(t for t in res["tracks"] if t.get("flag") == "bgm")
        self.assertEqual(len(bgm_track["segments"]), 2)
        audios = res["materials"]["audios"]
        self.assertTrue(any("epic_tension_bgm" in a["name"] for a in audios))
        self.assertTrue(any("calm_bgm" in a["name"] for a in audios))

    # 2. Dirty data self-healing handling
    def test_dirty_data_self_healing(self):
        # Pass lists instead of dicts, strings instead of lists, etc.
        dirty_draft = {
            "materials": "this should be a dict",
            "tracks": "this should be a list"
        }
        dirty_storyboard = {
            "shots": "not a list",
            "style": "not a dict"
        }
        res = enrich_draft_content(dirty_draft, dirty_storyboard)
        self.assertIsInstance(res["materials"], dict)
        self.assertIsInstance(res["tracks"], list)
        self.assertIsInstance(res["materials"]["texts"], list)
        # It should have created a default video track
        self.assertEqual(res["tracks"][0]["type"], "video")

    # 3. Missing parameters default fallback
    def test_missing_parameters_fallback(self):
        # Calling with None
        res = enrich_draft_content()
        self.assertIsInstance(res, dict)
        self.assertIsInstance(res.get("materials"), dict)
        self.assertIsInstance(res.get("tracks"), list)
        self.assertEqual(len(res["tracks"]), 1)
        self.assertEqual(res["tracks"][0]["type"], "video")

    # 4. Extreme boundaries
    def test_extreme_boundaries(self):
        boundary_storyboard = {
            "shots": [
                {
                    "start_ms": -500, # negative
                    "duration_ms": -1000, # negative
                    "emotion": 123, # integer instead of string
                    "camera_motion": None, # None instead of string
                }
            ]
        }
        boundary_draft = {
            "materials": {
                "texts": [
                    {"content": 12345}, # number instead of JSON string
                    {"content": '{"text": null}'} # null text value
                ]
            }
        }
        res = enrich_draft_content(boundary_draft, boundary_storyboard)

        # Check text effects didn't crash
        self.assertNotIn("text_effects", res["materials"]["texts"][0])
        self.assertNotIn("text_effects", res["materials"]["texts"][1])

        # Check BGM clamped values
        bgm_track = next((t for t in res["tracks"] if t.get("flag") == "bgm"), None)
        self.assertIsNotNone(bgm_track)
        seg = bgm_track["segments"][0]
        # fallback to 0 start and 3000ms duration
        self.assertEqual(seg["target_timerange"]["start"], 0)
        self.assertEqual(seg["target_timerange"]["duration"], 3000000)

    # 5. Feature flags disabled
    def test_feature_flags_disabled(self):
        options = {
            "enable_text_effects": False,
            "enable_transitions": False,
            "enable_ken_burns": False,
            "enable_bgm": False
        }
        res = enrich_draft_content(self.sample_draft, self.sample_storyboard, options)

        # Verify text effects are disabled
        self.assertNotIn("text_effects", res["materials"]["texts"][0])

        # Verify transitions & ken burns are disabled
        self.assertEqual(len(res["materials"]["transitions"]), 0)
        self.assertEqual(len(res["materials"]["animations"]), 0)

        video_track = next(t for t in res["tracks"] if t["type"] == "video")
        self.assertNotIn("animations", video_track["segments"][0])

        # Verify BGM is disabled
        self.assertEqual(len(res["materials"]["audios"]), 0)
        bgm_tracks = [t for t in res["tracks"] if t.get("flag") == "bgm"]
        self.assertEqual(len(bgm_tracks), 0)

if __name__ == "__main__":
    unittest.main()
