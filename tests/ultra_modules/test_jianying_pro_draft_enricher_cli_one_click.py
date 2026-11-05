import unittest
import json
import os
import tempfile
from unittest.mock import patch
import sys

from ultra_modules.jianying_pro_draft_enricher_cli_one_click import JianyingProDraftEnricherCliOneClick, cli_main

class TestJianyingProDraftEnricherCliOneClick(unittest.TestCase):

    def setUp(self):
        self.enricher = JianyingProDraftEnricherCliOneClick()

    def test_normal_complete_draft_enrichment(self):
        """Test #1: Normal complete draft enrichment."""
        mock_draft = {
            "materials": {
                "audios": [{"id": "bgm_1", "type": "bgm", "name": "custom.mp3"}],
                "texts": [{"id": "text_1", "effect_id": "custom_effect"}],
                "transitions": [{"id": "trans_1", "name": "shake"}]
            },
            "video_track": [
                {
                    "clips": [
                        {"id": "clip_1", "animations": [{"type": "kenburns"}]}
                    ]
                }
            ]
        }

        enriched = self.enricher.process_draft(mock_draft)

        # Ensure custom materials are preserved and not duplicated if they already meet the condition
        self.assertEqual(len(enriched['materials']['audios']), 1)
        self.assertEqual(enriched['materials']['audios'][0]['name'], "custom.mp3")

        self.assertEqual(len(enriched['materials']['texts']), 1)
        self.assertEqual(enriched['materials']['texts'][0]['effect_id'], "custom_effect")

        self.assertEqual(len(enriched['materials']['transitions']), 1)

        self.assertEqual(len(enriched['video_track'][0]['clips'][0]['animations']), 1)
        self.assertEqual(enriched['video_track'][0]['clips'][0]['animations'][0]['type'], "kenburns")

    def test_missing_parameters_empty_draft(self):
        """Test #2: Missing parameters / empty draft (self-healing, default fallback)."""
        mock_draft = {}
        enriched = self.enricher.process_draft(mock_draft)

        self.assertIn('materials', enriched)
        self.assertIn('video_track', enriched)

        # Check BGM injected
        self.assertEqual(len(enriched['materials']['audios']), 1)
        self.assertEqual(enriched['materials']['audios'][0]['type'], "bgm")

        # Check default transitions
        self.assertEqual(len(enriched['materials']['transitions']), 1)
        self.assertEqual(enriched['materials']['transitions'][0]['name'], "shake")

    def test_dirty_data_cleaning(self):
        """Test #3: Dirty data (invalid structure, missing keys) (silent cleaning)."""
        mock_draft = {
            "materials": {
                "texts": ["not_a_dict"],
                "audios": "not_a_list",
                "transitions": None
            },
            "video_track": [
                {
                    "clips": ["invalid_clip", {"animations": "invalid"}]
                },
                "invalid_track"
            ]
        }
        enriched = self.enricher.process_draft(mock_draft)

        # BGM should self-heal and inject default
        self.assertEqual(len(enriched['materials']['audios']), 1)
        self.assertEqual(enriched['materials']['audios'][0]['type'], "bgm")

        # Invalid texts ignored, empty lists handled
        self.assertEqual(len(enriched['materials']['texts']), 1)

        # Invalid transitions self-healed
        self.assertEqual(len(enriched['materials']['transitions']), 1)
        self.assertEqual(enriched['materials']['transitions'][0]['name'], "shake")

        # Video tracks self-healed
        clips = enriched['video_track'][0]['clips']
        self.assertEqual(len(clips), 2)
        self.assertEqual(clips[0], "invalid_clip") # preserves other data types untouched if not dict
        self.assertTrue(isinstance(clips[1]['animations'], list))
        self.assertEqual(len(clips[1]['animations']), 1)
        self.assertEqual(clips[1]['animations'][0]['type'], "kenburns")

    def test_extreme_edge_cases(self):
        """Test #4: Extreme edge cases (totally invalid input like string instead of dict)."""
        mock_draft = "totally_invalid_json_string"
        enriched = self.enricher.process_draft(mock_draft)

        # Should initialize to empty dict and then enrich with defaults
        self.assertIsInstance(enriched, dict)
        self.assertIn('materials', enriched)
        self.assertEqual(len(enriched['materials']['audios']), 1)
        self.assertEqual(len(enriched['materials']['transitions']), 1)

    @patch('sys.argv', ['jianying_pro_draft_enricher_cli_one_click.py'])
    def test_cli_execution_zero_parameters(self):
        """Test #5: CLI execution zero parameters."""
        # Create a temporary file to act as the missing 'draft_content.json'
        # The script defaults to 'draft_content.json' in current dir, let's mock the run_file
        # or change dir to temp

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            try:
                # File doesn't exist, CLI should self-heal and create it
                cli_main()

                # Check if it created and enriched the file
                self.assertTrue(os.path.exists("draft_content.json"))
                with open("draft_content.json", "r") as f:
                    data = json.load(f)

                self.assertIn("materials", data)
                self.assertEqual(len(data['materials']['audios']), 1)

            finally:
                os.chdir(original_cwd)

    def test_file_io_with_dirty_json(self):
        """Test #6: File reading with bad json data."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("{invalid json")
            temp_path = f.name

        try:
            self.enricher.run_file(file_path=temp_path, output_path=temp_path)

            with open(temp_path, "r") as f:
                data = json.load(f)

            self.assertIn("materials", data)
            self.assertEqual(len(data['materials']['audios']), 1)
        finally:
            os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()
