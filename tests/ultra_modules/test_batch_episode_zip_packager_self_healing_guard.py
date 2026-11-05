import unittest
import os
import shutil
import time
import zipfile
from ultra_modules.batch_episode_zip_packager_self_healing_guard import BatchEpisodeZipPackagerSelfHealingGuard

class TestBatchEpisodeZipPackagerSelfHealingGuard(unittest.TestCase):
    def setUp(self):
        self.output_dir = "test_output_zips"
        self.packager = BatchEpisodeZipPackagerSelfHealingGuard(output_dir=self.output_dir)

        # Create dummy files for normal test
        self.dummy_mp4 = "test_dummy.mp4"
        self.dummy_srt = "test_dummy.srt"
        with open(self.dummy_mp4, "w") as f: f.write("dummy video data")
        with open(self.dummy_srt, "w") as f: f.write("dummy srt data")

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        if os.path.exists(self.dummy_mp4):
            os.remove(self.dummy_mp4)
        if os.path.exists(self.dummy_srt):
            os.remove(self.dummy_srt)

    def test_normal_packaging(self):
        """Test normal packaging with complete data."""
        episodes_data = [
            {
                'episode_number': 1,
                'mp4_path': self.dummy_mp4,
                'srt_path': self.dummy_srt,
                'draft_content': '{"draft": "test1"}',
                'prompts': 'prompt1'
            }
        ]

        zip_path, snapshot_id = self.packager.package_episodes(episodes_data, "test_normal.zip")
        self.assertTrue(os.path.exists(zip_path))
        self.assertIsNotNone(snapshot_id)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            self.assertIn('episode_1/video.mp4', files)
            self.assertIn('episode_1/subtitles.srt', files)
            self.assertIn('episode_1/jianying_draft.json', files)
            self.assertIn('episode_1/prompts.txt', files)

    def test_missing_parameters_defaults(self):
        """Test if missing parameters are correctly filled with defaults."""
        episodes_data = [{}] # Empty dictionary representing missing parameters

        zip_path, _ = self.packager.package_episodes(episodes_data, "test_missing.zip")
        self.assertTrue(os.path.exists(zip_path))

        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            self.assertIn('episode_1/video.mp4', files)
            self.assertIn('episode_1/subtitles.srt', files)

            # Check default contents were used since no files were provided
            self.assertEqual(zf.read('episode_1/jianying_draft.json').decode(), '{"default": "draft"}')
            self.assertEqual(zf.read('episode_1/prompts.txt').decode(), 'default dual-eco prompts')

    def test_dirty_data_self_healing(self):
        """Test dirty data (None, invalid types) is silently healed."""
        episodes_data = [
            None,  # Not a dict
            {
                'episode_number': 'not_an_int',  # Invalid type
                'mp4_path': None,  # None type
                'draft_content': 12345  # Invalid type
            }
        ]

        zip_path, _ = self.packager.package_episodes(episodes_data, "test_dirty.zip")
        self.assertTrue(os.path.exists(zip_path))

        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            # First item (None) should default to episode 1
            self.assertIn('episode_1/video.mp4', files)
            # Second item should default to episode 2 (healed from 'not_an_int')
            self.assertIn('episode_2/video.mp4', files)
            # Check string casting for draft content
            self.assertEqual(zf.read('episode_2/jianying_draft.json').decode(), '12345')

    def test_snapshot_undo(self):
        """Test the 5-second one-click undo mechanism."""
        # 1. Create a zip
        episodes_data = [{'episode_number': 1}]
        zip_path, snapshot_id = self.packager.package_episodes(episodes_data, "test_undo.zip")
        self.assertTrue(os.path.exists(zip_path))

        # 2. Undo it immediately (within 5 seconds)
        success = self.packager.undo(snapshot_id)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(zip_path)) # The newly created zip should be deleted

        # 3. Test timeout (simulate time passing)
        zip_path2, snapshot_id2 = self.packager.package_episodes(episodes_data, "test_undo2.zip")
        self.packager.snapshots[snapshot_id2]['timestamp'] -= 6.0 # Move timestamp back 6 seconds

        success2 = self.packager.undo(snapshot_id2)
        self.assertFalse(success2) # Should fail due to timeout
        self.assertTrue(os.path.exists(zip_path2)) # File should still exist

    def test_extreme_edge_cases(self):
        """Test extreme edge cases like empty input or completely missing data."""
        # Test 1: Empty list
        zip_path1, _ = self.packager.package_episodes([], "test_empty_list.zip")
        self.assertTrue(os.path.exists(zip_path1))
        with zipfile.ZipFile(zip_path1, 'r') as zf:
            self.assertEqual(len(zf.namelist()), 0) # Should be an empty zip

        # Test 2: Invalid episodes format (string instead of list)
        zip_path2, _ = self.packager.package_episodes("invalid_string", "test_invalid_list.zip")
        self.assertTrue(os.path.exists(zip_path2))
        with zipfile.ZipFile(zip_path2, 'r') as zf:
            self.assertIn('episode_1/video.mp4', zf.namelist()) # Should be treated as list of 1 string, healed to ep 1

        # Test 3: None filename
        zip_path3, _ = self.packager.package_episodes([{}], None)
        self.assertTrue(os.path.exists(zip_path3))
        self.assertTrue(zip_path3.endswith('.zip'))

if __name__ == '__main__':
    unittest.main()
