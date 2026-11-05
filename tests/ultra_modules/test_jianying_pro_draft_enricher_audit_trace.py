import unittest
import json
from ultra_modules.jianying_pro_draft_enricher_audit_trace import JianyingProDraftEnricherAuditTrace, enrich_jianying_draft

class TestJianyingProDraftEnricherAuditTrace(unittest.TestCase):

    def setUp(self):
        # A relatively normal, clean subset of draft content
        self.normal_draft_data = {
            "materials": {
                "texts": [{"id": "t1", "content": "{\"text\": \"Hello\"}"}],
                "audios": [],
                "transitions": [],
                "video_effects": [],
                "materials": []
            },
            "tracks": [
                {
                    "id": "trk1",
                    "type": "video",
                    "segments": [
                        {"id": "seg1"},
                        {"id": "seg2"}
                    ]
                }
            ]
        }

    def test_normal_operation(self):
        """Test normal operation with valid, clean dictionary input."""
        enricher = JianyingProDraftEnricherAuditTrace(self.normal_draft_data)

        enricher.apply_text_styles(stroke_color="#FF0000")
        enricher.inject_transition("fade", 300000)
        enricher.inject_ken_burns(1.5)
        enricher.inject_bgm("assets/music.mp3", 0.8)

        data = enricher.draft_data

        # Check text styles
        txt = data["materials"]["texts"][0]
        self.assertTrue(txt["has_stroke"])
        self.assertEqual(txt["stroke_color"], "#FF0000")

        # Check transitions
        transitions = data["materials"]["transitions"]
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]["name"], "fade")

        # Check segment has transition ref
        seg1 = data["tracks"][0]["segments"][0]
        self.assertIn(transitions[0]["id"], seg1["extra_material_refs"])

        # Check Ken Burns
        clip = seg1["clip"]
        self.assertEqual(clip["animation"]["zoom"], 1.5)

        # Check BGM
        audios = data["materials"]["audios"]
        self.assertEqual(len(audios), 1)
        self.assertEqual(audios[0]["path"], "assets/music.mp3")

        # Check Audit log
        log = enricher.get_audit_trail()
        actions = [entry["action"] for entry in log]
        self.assertIn("PARSE_DICT", actions)
        self.assertIn("APPLY_TEXT_STYLES", actions)
        self.assertIn("INJECT_TRANSITION", actions)
        self.assertIn("INJECT_KEN_BURNS", actions)
        self.assertIn("INJECT_BGM", actions)

    def test_dirty_data_healing_and_missing_params(self):
        """Test how the class handles completely empty or malformed input."""
        # Provide just an empty string (simulating empty file)
        enricher = JianyingProDraftEnricherAuditTrace("")

        # It should heal to a minimum viable structure
        data = enricher.draft_data
        self.assertIn("materials", data)
        self.assertIn("tracks", data)
        self.assertIsInstance(data["materials"]["texts"], list)

        # Call operations on the empty healed data
        enricher.apply_text_styles() # missing stroke_color etc. should fallback
        enricher.inject_transition()
        enricher.inject_ken_burns()
        enricher.inject_bgm("") # Should skip safely

        log = enricher.get_audit_trail()
        # Verify that HEAL_DATA actions were logged
        heal_actions = [e for e in log if e["action"] == "HEAL_DATA"]
        self.assertGreater(len(heal_actions), 0)

        # Verify that BGM injection was skipped safely
        skip_actions = [e for e in log if e["action"] == "INJECT_BGM" and e["details"].get("status") == "skipped"]
        self.assertEqual(len(skip_actions), 1)

    def test_undo_functionality(self):
        """Test the one-click undo capability."""
        enricher = JianyingProDraftEnricherAuditTrace(self.normal_draft_data)
        enricher.apply_text_styles(stroke_color="#123456")

        # Ensure it was changed
        self.assertEqual(enricher.draft_data["materials"]["texts"][0]["stroke_color"], "#123456")

        # Undo
        restored_data = enricher.undo()

        # The text style should not be present in the original data structure subset
        self.assertNotIn("stroke_color", restored_data["materials"]["texts"][0])
        self.assertNotIn("stroke_color", enricher.draft_data["materials"]["texts"][0])

        # Test undo without snapshot
        enricher._initial_snapshot = None
        same_data = enricher.undo()
        self.assertEqual(same_data, enricher.draft_data)

    def test_coverage_branches(self):
        """Test specific branches for 100% coverage."""
        # Test valid JSON string
        enricher = JianyingProDraftEnricherAuditTrace('{"materials": {}, "tracks": []}')
        self.assertIsInstance(enricher.draft_data, dict)

        # Test parsed JSON is not dict (e.g. list)
        enricher2 = JianyingProDraftEnricherAuditTrace('[1, 2, 3]')
        self.assertIsInstance(enricher2.draft_data, dict)

        # Test wrapper without bgm
        result = enrich_jianying_draft(
            draft_content=self.normal_draft_data,
            zoom_factor=1.2,
            transition_name="fade_in",
            stroke_color="#00FF00"
        )
        if "audios" in result["materials"]:
            self.assertEqual(len(result["materials"]["audios"]), 0)

    def test_extreme_boundaries(self):
        """Test with deeply nested broken data."""
        broken_data = {
            "materials": {
                "texts": [
                    None,
                    123,
                    {"content": "not_json"}
                ]
            },
            "tracks": [
                {
                    "type": "video",
                    "segments": [
                        None,
                        "string_segment",
                        {"clip": "not_a_dict"}
                    ]
                },
                "not_a_dict_track",
                {
                    "type": "audio",
                    "segments": []
                }
            ]
        }

        enricher = JianyingProDraftEnricherAuditTrace(broken_data)
        enricher.apply_text_styles()
        enricher.inject_ken_burns()
        enricher.inject_transition()

        data = enricher.draft_data
        texts = data["materials"]["texts"]
        self.assertEqual(texts[2]["text_color"], "#FFFFFF") # Style applied to valid dict

        seg = data["tracks"][0]["segments"][2]
        self.assertEqual(seg["clip"]["animation"]["type"], "ken_burns") # Fixed clip type

    def test_frontend_wrapper(self):
        """Test the enrich_jianying_draft one-click zero-friction wrapper."""
        result = enrich_jianying_draft(
            draft_content=self.normal_draft_data,
            bgm_path="epic_music.mp3",
            zoom_factor=1.2,
            transition_name="fade_in",
            stroke_color="#00FF00"
        )

        self.assertEqual(result["materials"]["texts"][0]["stroke_color"], "#00FF00")
        self.assertEqual(result["materials"]["transitions"][0]["name"], "fade_in")
        self.assertEqual(result["tracks"][0]["segments"][0]["clip"]["animation"]["zoom"], 1.2)
        self.assertEqual(result["materials"]["audios"][0]["path"], "epic_music.mp3")

if __name__ == "__main__":
    unittest.main()
