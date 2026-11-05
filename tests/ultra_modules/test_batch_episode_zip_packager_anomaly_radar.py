import unittest
import os
import zipfile
import shutil
from ultra_modules.batch_episode_zip_packager_anomaly_radar import package_and_scan_episodes

class TestBatchEpisodeZipPackagerAnomalyRadar(unittest.TestCase):

    def setUp(self):
        self.test_zip_path = "test_output.zip"
        if os.path.exists(self.test_zip_path):
            os.remove(self.test_zip_path)

    def tearDown(self):
        if os.path.exists(self.test_zip_path):
            os.remove(self.test_zip_path)
        if os.path.exists("default_batch_episodes.zip"):
            os.remove("default_batch_episodes.zip")

    def test_normal_execution_distribution(self):
        """Test 1: Normal execution & distribution (~100 episodes). Red(3%), Yellow(7%)."""
        # Create 100 episodes
        episodes = []
        for i in range(100):
            # Normal distribution with some explicit anomalies at the end
            if i == 98:
                size = 500000000.0 # Extremely large
                dur = 180.0
            elif i == 99:
                size = 50000000.0
                dur = 1800.0 # Extremely long
            else:
                size = 50000000.0 + (i * 1000)
                dur = 180.0 + (i * 0.1)

            episodes.append({
                'id': f'ep_{i}',
                'file_size': size,
                'duration': dur
            })

        result = package_and_scan_episodes(episodes, self.test_zip_path)

        red_count = sum(1 for ep in result if ep['marker'] == 'red')
        yellow_count = sum(1 for ep in result if ep['marker'] == 'yellow')
        green_count = sum(1 for ep in result if ep['marker'] == 'green')

        self.assertEqual(len(result), 100)
        self.assertEqual(red_count, 3) # 3% of 100
        self.assertEqual(yellow_count, 7) # 7% of 100
        self.assertEqual(green_count, 90) # remaining 90%

        # Verify the top anomalies were marked red
        red_reasons = [ep['reason'] for ep in result if ep['marker'] == 'red']
        self.assertTrue(any("文件体积异常过大" in r for r in red_reasons))
        self.assertTrue(any("视频时长异常过长" in r for r in red_reasons))

    def test_dirty_data_self_healing(self):
        """Test 2: Dirty Data Self-Healing."""
        episodes = [
            {'id': 'ep_0', 'file_size': '50000000', 'duration': '180'}, # String type
            {'id': 'ep_1', 'file_size': None, 'duration': None}, # None
            {'id': 'ep_2'}, # Missing fields entirely
            {'id': 'ep_3', 'file_size': 'invalid_string', 'duration': 'invalid'} # Invalid string
        ]

        result = package_and_scan_episodes(episodes, self.test_zip_path)

        self.assertEqual(len(result), 4)
        for ep in result:
            self.assertIsNotNone(ep.get('file_size'))
            self.assertIsNotNone(ep.get('duration'))
            self.assertIsInstance(ep['file_size'], float)
            self.assertIsInstance(ep['duration'], float)

        # Since all values are healed to median, stdev should be 0, all should be green
        for ep in result:
            self.assertEqual(ep['marker'], 'green')

    def test_missing_params_auto_defaults(self):
        """Test 3: Missing Params & Auto-Defaults."""
        episodes = [{'id': 'ep_0'}]
        # Call with no output_zip
        result = package_and_scan_episodes(episodes)

        self.assertTrue(os.path.exists("default_batch_episodes.zip"))

        # Validate dummy files inside zip
        with zipfile.ZipFile("default_batch_episodes.zip", 'r') as zf:
            files = zf.namelist()
            self.assertIn("ep_0/ep_0.mp4", files)
            self.assertIn("ep_0/ep_0.srt", files)
            self.assertIn("ep_0/ep_0_draft.json", files)
            self.assertIn("ep_0/ep_0_prompts.txt", files)

        self.assertEqual(len(result), 1)

    def test_extreme_boundary_conditions(self):
        """Test 4: Extreme Boundary Conditions (Empty, Single, Identical)."""
        # Empty
        res_empty = package_and_scan_episodes([], self.test_zip_path)
        self.assertEqual(res_empty, [])
        self.assertFalse(os.path.exists(self.test_zip_path))

        # Single
        res_single = package_and_scan_episodes([{'id': 'ep_0', 'file_size': 100, 'duration': 100}], self.test_zip_path)
        self.assertEqual(len(res_single), 1)
        self.assertEqual(res_single[0]['marker'], 'green') # stdev=0, z=0

        # Identical
        res_identical = package_and_scan_episodes([
            {'id': 'ep_0', 'file_size': 100, 'duration': 100},
            {'id': 'ep_1', 'file_size': 100, 'duration': 100},
            {'id': 'ep_2', 'file_size': 100, 'duration': 100}
        ], self.test_zip_path)

        self.assertEqual(len(res_identical), 3)
        for ep in res_identical:
            self.assertEqual(ep['marker'], 'green')

    def test_zip_packaging_verification(self):
        """Test 5: ZIP Packaging Verification (Real vs Dummy)."""
        # Create a real dummy file
        test_dir = "temp_test_dir"
        os.makedirs(test_dir, exist_ok=True)
        real_mp4 = os.path.join(test_dir, "real.mp4")
        with open(real_mp4, "w") as f:
            f.write("real_mp4_content")

        episodes = [
            {
                'id': 'ep_0',
                'mp4_path': real_mp4,
                # Missing srt, draft, prompt will fallback to dummy
            }
        ]

        result = package_and_scan_episodes(episodes, self.test_zip_path)

        self.assertTrue(os.path.exists(self.test_zip_path))

        with zipfile.ZipFile(self.test_zip_path, 'r') as zf:
            # Check real file
            with zf.open("ep_0/real.mp4") as f:
                content = f.read().decode()
                self.assertEqual(content, "real_mp4_content")

            # Check dummy srt
            with zf.open("ep_0/ep_0.srt") as f:
                content = f.read().decode()
                self.assertIn("Auto Generated Subtitle", content)

        # Cleanup
        shutil.rmtree(test_dir)

if __name__ == '__main__':
    unittest.main()
