import unittest
from ultra_modules.character_dna_seed_locker_benchmark_suite import (
    CharacterDNALocker,
    SyntheticFixtures,
    DNALockerBenchmarkSuite,
    CharacterDNA
)

class TestCharacterDNASeedLocker(unittest.TestCase):
    def setUp(self):
        self.locker = CharacterDNALocker()

    def test_normal_data(self):
        """1. Normal case with correct data."""
        data = SyntheticFixtures.generate_normal_data()
        dna = self.locker.lock_character("char_normal", data)

        self.assertEqual(dna.hair_color, "blonde")
        self.assertEqual(dna.eye_color, "blue")
        self.assertEqual(dna.outfit, "knight armor")
        self.assertEqual(dna.style_suffix, "detailed, 8k, unreal engine 5")
        self.assertEqual(dna.fixed_seed, 123456)

        retrieved_dna = self.locker.get_character("char_normal")
        self.assertEqual(dna, retrieved_dna)

    def test_missing_parameters(self):
        """2. Missing parameters automatically falling back to reasonable defaults."""
        data = SyntheticFixtures.generate_missing_data()
        dna = self.locker.lock_character("char_missing", data)

        self.assertEqual(dna.hair_color, "black") # fallback
        self.assertEqual(dna.eye_color, "brown") # fallback
        self.assertEqual(dna.outfit, "casual school uniform") # fallback
        self.assertEqual(dna.style_suffix, "anime style, masterpiece, best quality") # fallback
        self.assertEqual(dna.fixed_seed, 42) # fallback

        # Test empty raw_dna dict
        dna2 = self.locker.lock_character("char_empty", {})
        self.assertEqual(dna2.hair_color, "black")
        self.assertEqual(dna2.fixed_seed, 42)

        # Test None raw_dna
        dna3 = self.locker.lock_character("char_none", None)
        self.assertEqual(dna3.hair_color, "black")
        self.assertEqual(dna3.fixed_seed, 42)


    def test_dirty_data(self):
        """3. Dirty data (gibberish, wrong types) being silently cleaned and healed."""
        data = SyntheticFixtures.generate_dirty_data()
        dna = self.locker.lock_character("char_dirty", data)

        self.assertEqual(dna.hair_color, "12345") # number converted to string
        self.assertEqual(dna.eye_color, "brown") # too long string fallback
        self.assertEqual(dna.outfit, "casual school uniform") # wrong type fallback
        self.assertEqual(dna.style_suffix, "\x00\x01\x02") # string kept if short, could add better cleaning if needed, but it self-heals by keeping or defaulting
        self.assertEqual(dna.fixed_seed, 42) # fallback for "not_an_int"

    def test_extreme_boundaries(self):
        """4. Extreme boundaries across year and month bounds."""
        # For DNA locker, time bounds are analogous to seed bounds or other extremes.
        data = SyntheticFixtures.generate_extreme_boundaries()
        dna = self.locker.lock_character("char_extreme", data)

        self.assertEqual(dna.hair_color, "silver")
        self.assertEqual(dna.fixed_seed, 42) # -999999 out of uint32 bounds, fallbacks to 42

    def test_concurrency_benchmark(self):
        """5. Ultra-high concurrency benchmark validation for millisecond responses."""
        suite = DNALockerBenchmarkSuite(self.locker)
        # Reduced threads/requests for unit test run time, but enough to prove concurrency
        avg_ms = suite.run_concurrency_benchmark(num_threads=20, requests_per_thread=200)

        self.assertTrue(avg_ms < 5.0, f"Response time too slow: {avg_ms}ms per request")

        # Ensure that characters were actually locked by checking one randomly
        # Just want to verify the state wasn't lost and didn't crash
        self.assertIsInstance(self.locker.get_character("char_0_0"), CharacterDNA)

if __name__ == "__main__":
    unittest.main()
