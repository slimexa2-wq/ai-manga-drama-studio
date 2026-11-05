import unittest
import time
from ultra_modules.jianying_pro_draft_enricher_self_healing_guard import enrich_draft_content, JianyingProDraftEnricherSelfHealingGuard

class TestJianyingProDraftEnricherSelfHealingGuard(unittest.TestCase):
    def test_normal_operation(self):
        """Test normal operation with valid data."""
        draft = {
            'tracks': [
                {'type': 'video', 'segments': [{'id': 'v1', 'duration': 3000}]},
                {'type': 'text', 'segments': [{'id': 't1', 'text': 'Hello'}]}
            ]
        }
        enriched = enrich_draft_content(draft)

        # BGM should be injected
        audio_track = next((t for t in enriched['tracks'] if t.get('type') == 'audio'), None)
        self.assertIsNotNone(audio_track)
        self.assertEqual(audio_track['segments'][0]['file'], 'default_bgm.mp3')

        # KenBurns and transitions should be injected
        video_track = next(t for t in enriched['tracks'] if t.get('type') == 'video')
        segment = video_track['segments'][0]
        self.assertEqual(segment['animations'][0]['name'], 'KenBurns')
        self.assertEqual(segment['transition']['name'], 'shake')

        # Text effects should be injected
        text_track = next(t for t in enriched['tracks'] if t.get('type') == 'text')
        text_segment = text_track['segments'][0]
        self.assertEqual(text_segment['style']['effect'], 'flower_text')

    def test_dirty_data_self_healing(self):
        """Test self-healing with malformed or dirty data."""
        dirty_draft = "this is a string, not a dict"
        enriched = enrich_draft_content(dirty_draft)

        self.assertIsInstance(enriched, dict)
        self.assertIn('tracks', enriched)
        self.assertIsInstance(enriched['tracks'], list)

        audio_track = next((t for t in enriched['tracks'] if t.get('type') == 'audio'), None)
        self.assertIsNotNone(audio_track)

        dirty_draft2 = {
            'tracks': [
                "not a dict",
                {'type': 'video', 'segments': "not a list"}
            ]
        }
        enriched2 = enrich_draft_content(dirty_draft2)
        # Because we discard non-dict tracks, the video track is at index 0
        video_track = enriched2['tracks'][0]
        self.assertEqual(video_track['segments'], [])

    def test_missing_params_defaults(self):
        """Test missing parameters default correctly (disable effects)."""
        draft = {
            'tracks': [
                {'type': 'video', 'segments': [{'id': 'v1', 'duration': 3000}]},
                {'type': 'text', 'segments': [{'id': 't1', 'text': 'Hello'}]}
            ]
        }
        params = {
            'effects': False,
            'transitions': False,
            'ken_burns': False,
            'bgm': None
        }
        enriched = enrich_draft_content(draft, params)

        # No BGM
        audio_track = next((t for t in enriched['tracks'] if t.get('type') == 'audio'), None)
        self.assertIsNone(audio_track)

        # No KenBurns/transitions
        video_track = next(t for t in enriched['tracks'] if t.get('type') == 'video')
        segment = video_track['segments'][0]
        self.assertNotIn('animations', segment)
        self.assertNotIn('transition', segment)

        # No text effect
        text_track = next(t for t in enriched['tracks'] if t.get('type') == 'text')
        text_segment = text_track['segments'][0]
        self.assertNotIn('style', text_segment)

    def test_extreme_boundaries(self):
        """Test extreme boundary conditions, like empty draft."""
        draft = {}
        enriched = enrich_draft_content(draft)
        self.assertIn('tracks', enriched)
        self.assertEqual(len(enriched['tracks']), 1)
        self.assertEqual(enriched['tracks'][0]['type'], 'audio')

    def test_undo_functionality(self):
        """Test the 5-second snapshot undo functionality."""
        guard = JianyingProDraftEnricherSelfHealingGuard(undo_window_seconds=1)

        initial_draft = {'tracks': [{'type': 'video', 'segments': [{'id': 'initial'}]}]}

        # Apply enrichment
        enriched_draft = guard.apply_enrichment(initial_draft)

        # State changed
        self.assertNotEqual(initial_draft, enriched_draft)
        self.assertEqual(len(guard.snapshots), 1)

        # Undo
        restored_draft = guard.undo()
        self.assertEqual(restored_draft, initial_draft)

        # No more undo available
        self.assertIsNone(guard.undo())

        # Test expiration
        guard.apply_enrichment(initial_draft)
        time.sleep(1.1)
        self.assertIsNone(guard.undo())

if __name__ == '__main__':
    unittest.main()
