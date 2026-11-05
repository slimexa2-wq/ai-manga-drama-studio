import unittest
import os
import shutil
import tempfile
from ultra_modules.karaoke_ass_subtitle_burner_self_healing_guard import KaraokeSubtitleBurnerSelfHealingGuard

class TestKaraokeSubtitleBurnerSelfHealingGuard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.guard = KaraokeSubtitleBurnerSelfHealingGuard(snapshot_dir=os.path.join(self.temp_dir, "snapshots"))
        self.dummy_video = os.path.join(self.temp_dir, "dummy_video.mp4")

        # Create a dummy video file
        with open(self.dummy_video, 'w') as f:
            f.write("dummy video content")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_normal_burning(self):
        # 1. Normal data
        words_data = [
            {'word': 'Hello', 'start': 0.0, 'end': 1.0},
            {'word': 'World', 'start': 1.0, 'end': 2.0}
        ]

        output_path = os.path.join(self.temp_dir, "output.mp4")
        result_path = self.guard.burn_subtitles(self.dummy_video, words_data, output_path)

        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(result_path))

        # Checking generated ASS
        ass_content = KaraokeSubtitleBurnerSelfHealingGuard.generate_ass(words_data)
        self.assertIn("{\\K100}Hello", ass_content)
        self.assertIn("{\\K100}World", ass_content)

    def test_dirty_data_healing(self):
        # 2. Dirty data (bad types, missing timestamps, string lists, reversed timestamps)
        dirty_data = [
            {'word': 'A', 'start': 'invalid', 'end': None}, # should fallback to start=0.0, end=0.5
            'B', # string should fallback to start=last_end, end=last_end+0.5
            {'word': 'C', 'start': 2.0, 'end': 1.0}, # reversed timestamps, should be swapped
            123 # invalid type, should be ignored
        ]

        healed_data = KaraokeSubtitleBurnerSelfHealingGuard._heal_words_data(dirty_data)

        self.assertEqual(len(healed_data), 3)
        self.assertEqual(healed_data[0]['word'], 'A')
        self.assertEqual(healed_data[0]['start'], 0.0)
        self.assertEqual(healed_data[0]['end'], 0.5)

        self.assertEqual(healed_data[1]['word'], 'B')
        self.assertEqual(healed_data[1]['start'], 0.5)
        self.assertEqual(healed_data[1]['end'], 1.0)

        self.assertEqual(healed_data[2]['word'], 'C')
        self.assertEqual(healed_data[2]['start'], 1.0)
        self.assertEqual(healed_data[2]['end'], 2.0)

        # Test completely broken input
        healed_broken = KaraokeSubtitleBurnerSelfHealingGuard._heal_words_data("Just a string")
        self.assertEqual(len(healed_broken), 1)
        self.assertEqual(healed_broken[0]['word'], "Just a string")

    def test_missing_parameters_fallback(self):
        # 3. Missing output_path
        words_data = [{'word': 'Test', 'start': 0.0, 'end': 1.0}]

        # Shouldn't raise error, should fallback to default path
        result_path = self.guard.burn_subtitles(self.dummy_video, words_data)

        expected_path = os.path.join(self.temp_dir, "dummy_video_karaoke.mp4")
        self.assertEqual(result_path, expected_path)
        self.assertTrue(os.path.exists(expected_path))

    def test_snapshot_undo(self):
        # 4. Snapshot undo mechanism
        output_path = os.path.join(self.temp_dir, "undo_test.mp4")

        # Create an initial file
        with open(output_path, 'w') as f:
            f.write("original content")

        words_data = [{'word': 'Test', 'start': 0.0, 'end': 1.0}]

        # Burn, which will overwrite (or fallback to overwrite)
        self.guard.burn_subtitles(self.dummy_video, words_data, output_path)

        # Check that content was overwritten by dummy video content (fallback behavior)
        with open(output_path, 'r') as f:
            content = f.read()
            self.assertEqual(content, "dummy video content")

        # Perform undo
        success = self.guard.undo_burn()
        self.assertTrue(success)

        # Verify original content is restored
        with open(output_path, 'r') as f:
            content = f.read()
            self.assertEqual(content, "original content")

    def test_extreme_boundary_conditions(self):
        # 5. Extreme boundary conditions

        # Undo before doing anything
        new_guard = KaraokeSubtitleBurnerSelfHealingGuard()
        self.assertFalse(new_guard.undo_burn())

        # Burn to a path that doesn't exist initially, then undo
        output_path = os.path.join(self.temp_dir, "nonexistent.mp4")
        words_data = [] # Empty data

        self.guard.burn_subtitles(self.dummy_video, words_data, output_path)
        self.assertTrue(os.path.exists(output_path))

        # Undo should remove the newly created file because it didn't exist before
        success = self.guard.undo_burn()
        self.assertTrue(success)
        self.assertFalse(os.path.exists(output_path))

        # Test generation with completely empty list
        ass_content = KaraokeSubtitleBurnerSelfHealingGuard.generate_ass([])
        self.assertNotIn("Dialogue:", ass_content)
        self.assertIn("[Script Info]", ass_content)

if __name__ == '__main__':
    unittest.main()
