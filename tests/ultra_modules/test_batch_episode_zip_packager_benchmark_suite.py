import unittest
import zipfile
import io
import datetime
from ultra_modules.batch_episode_zip_packager_benchmark_suite import BatchEpisodeZipPackager, BenchmarkSuite

class TestBatchEpisodeZipPackager(unittest.TestCase):
    def setUp(self):
        self.packager = BatchEpisodeZipPackager()

    def test_normal_execution(self):
        """Test normal execution with valid parameters."""
        episodes = self.packager.generate_synthetic_fixtures(num_episodes=5)
        self.assertEqual(len(episodes), 5)

        zip_bytes = self.packager.package_episodes(episodes=episodes, concurrency=2)
        self.assertTrue(len(zip_bytes) > 0)

        # Verify ZIP contents
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            namelist = zf.namelist()
            # 5 episodes * 4 files each
            self.assertEqual(len(namelist), 20)

            # Check if one of the expected files exists
            has_mp4 = any(name.endswith(".mp4") for name in namelist)
            self.assertTrue(has_mp4)

    def test_missing_parameter_fallback(self):
        """Test that missing or invalid parameters fallback to reasonable defaults."""
        # Test generate_synthetic_fixtures defaults
        episodes = self.packager.generate_synthetic_fixtures(num_episodes=None)
        self.assertEqual(len(episodes), 10)

        episodes = self.packager.generate_synthetic_fixtures(num_episodes=-5)
        self.assertEqual(len(episodes), 10)

        episodes = self.packager.generate_synthetic_fixtures(num_episodes="not an int")
        self.assertEqual(len(episodes), 10)

        # Test package_episodes defaults
        zip_bytes = self.packager.package_episodes(episodes=None, concurrency=None)
        self.assertTrue(len(zip_bytes) > 0)

        zip_bytes = self.packager.package_episodes(episodes="not a list", concurrency="invalid")
        self.assertTrue(len(zip_bytes) > 0)

    def test_dirty_data_self_healing(self):
        """Test zero crash tolerance with dirty or malformed data."""
        # Malformed list of episodes (none, not dicts)
        episodes = [
            None,
            "not a dict",
            {"title": None, "timestamp": "not a datetime"},
            {"title": "Episode_\x00\x01\x02\n\t", "mp4_content": "not bytes"}
        ]

        zip_bytes = self.packager.package_episodes(episodes=episodes, concurrency=1)
        self.assertTrue(len(zip_bytes) > 0)

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            namelist = zf.namelist()
            self.assertTrue(len(namelist) > 0)
            # Ensure no unprintable characters in paths
            for name in namelist:
                self.assertTrue(all(c.isprintable() for c in name))

    def test_extreme_boundary_cases(self):
        """Test extreme boundaries like cross-year/month and massive concurrency."""
        episodes = self.packager.generate_synthetic_fixtures(
            num_episodes=50,
            cross_year_month=True,
            dirty_data=True
        )

        # Check cross year boundary exists
        has_2023 = False
        has_2024 = False
        for ep in episodes:
            if ep["timestamp"].year == 2023:
                has_2023 = True
            elif ep["timestamp"].year == 2024:
                has_2024 = True
        self.assertTrue(has_2023 and has_2024)

        # Package with massive concurrency
        zip_bytes = self.packager.package_episodes(episodes=episodes, concurrency=1000)
        self.assertTrue(len(zip_bytes) > 0)

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            namelist = zf.namelist()
            self.assertEqual(len(namelist), 50 * 4)

    def test_benchmark_suite(self):
        """Test the benchmark suite to ensure it returns expected metrics."""
        suite = BenchmarkSuite()
        metrics = suite.run_benchmark()

        self.assertIn("episodes_processed", metrics)
        self.assertIn("zip_size_bytes", metrics)
        self.assertIn("duration_ms", metrics)

        self.assertEqual(metrics["episodes_processed"], 1000)
        self.assertTrue(metrics["zip_size_bytes"] > 0)
        self.assertTrue(metrics["duration_ms"] > 0)

if __name__ == '__main__':
    unittest.main()
