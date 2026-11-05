import unittest
import time
from ultra_modules.character_dna_seed_locker_audit_trace import CharacterDNALocker

class TestCharacterDNALocker(unittest.TestCase):
    def setUp(self):
        self.locker = CharacterDNALocker()

    def test_normal_execution(self):
        # Locking standard valid DNA
        dna = self.locker.lock_dna(
            "char_01",
            hair="blonde long hair",
            eyes="blue eyes",
            clothing="knight armor",
            style_suffix="fantasy, 8k resolution",
            seed=12345
        )
        self.assertEqual(dna["hair"], "blonde long hair")
        self.assertEqual(dna["seed"], 12345)

        # Test prompt generation
        prompt = self.locker.generate_prompt_snippet("char_01")
        self.assertEqual(prompt, "blonde long hair, blue eyes, knight armor, fantasy, 8k resolution")

    def test_missing_parameter_fallbacks(self):
        # Empty kwargs
        dna1 = self.locker.lock_dna("char_02")
        self.assertEqual(dna1["hair"], "black short hair")
        self.assertEqual(dna1["seed"], 42)

        # Only some kwargs
        dna2 = self.locker.lock_dna("char_03", hair="red hair", eyes=None, clothing=" ")
        self.assertEqual(dna2["hair"], "red hair")
        self.assertEqual(dna2["eyes"], "dark eyes") # Fallback since None
        self.assertEqual(dna2["clothing"], "casual modern clothing") # Fallback since only spaces

        # get_dna on unknown char
        dna_fallback = self.locker.get_dna("unknown_char")
        self.assertEqual(dna_fallback["hair"], "black short hair")

        # Checking prompt for missing parameter fallback
        prompt = self.locker.generate_prompt_snippet("unknown_char")
        self.assertEqual(prompt, "black short hair, dark eyes, casual modern clothing, masterpiece, best quality")

        # Verify audit log for auto-fallback
        logs = self.locker.get_audit_trace("unknown_char")
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]["operation"], "AUTO_FALLBACK")
        self.assertEqual(logs[1]["operation"], "AUTO_FALLBACK")

    def test_dirty_data_self_healing(self):
        # Invalid types for string fields and seed
        dna = self.locker.lock_dna(
            "char_04",
            hair=123,
            eyes=["blue"],
            clothing={"type": "armor"},
            style_suffix=None,
            seed="not_an_int"
        )
        self.assertEqual(dna["hair"], "123")
        self.assertEqual(dna["eyes"], "['blue']")
        self.assertEqual(dna["clothing"], "{'type': 'armor'}")
        self.assertEqual(dna["style_suffix"], "masterpiece, best quality")
        self.assertEqual(dna["seed"], 42)

        # Seed out of bounds
        dna_bounds1 = self.locker.lock_dna("char_05", seed=-1)
        self.assertEqual(dna_bounds1["seed"], 42)

        dna_bounds2 = self.locker.lock_dna("char_06", seed=5000000000) # > 32-bit max
        self.assertEqual(dna_bounds2["seed"], 42)

        # _clean_and_heal direct test for non-dict
        cleaned = self.locker._clean_and_heal(None)
        self.assertEqual(cleaned["seed"], 42)

    def test_extreme_boundary_cases(self):
        # char_id is None
        dna = self.locker.lock_dna(None, hair="none_hair")
        self.assertEqual(dna["hair"], "none_hair")
        self.assertEqual(self.locker.get_dna(None)["hair"], "none_hair")
        self.assertEqual(self.locker.get_dna("UNKNOWN_CHAR")["hair"], "none_hair")

        # char_id is not a string
        dna_int = self.locker.lock_dna(1234, hair="int_hair")
        self.assertEqual(self.locker.get_dna("1234")["hair"], "int_hair")

        # char_id is empty string
        dna_empty = self.locker.lock_dna("   ", hair="empty_hair")
        self.assertEqual(self.locker.get_dna("UNKNOWN_CHAR")["hair"], "empty_hair") # Since it strips and falls back

        self.assertTrue(len(self.locker.get_audit_trace(None)) > 0)

        # Audit trace with invalid char_id types
        self.assertEqual(len(self.locker.get_audit_trace(1234)), 1)
        self.assertEqual(self.locker.get_audit_trace("   ")[-1]["state"]["hair"], "empty_hair")

    def test_audit_trace_and_deduplication(self):
        # Initial lock
        self.locker.lock_dna("char_07", hair="blue hair")
        logs = self.locker.get_audit_trace("char_07")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["operation"], "INIT")
        self.assertTrue("timestamp" in logs[0])
        self.assertTrue(isinstance(logs[0]["timestamp"], float))

        # Duplicate lock (no change)
        self.locker.lock_dna("char_07", hair="blue hair")
        logs = self.locker.get_audit_trace("char_07")
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[1]["operation"], "DEDUPLICATE")
        self.assertEqual(logs[1]["diff"], {})

        # Update lock (change)
        self.locker.lock_dna("char_07", hair="red hair", seed=100)
        logs = self.locker.get_audit_trace("char_07")
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[2]["operation"], "UPDATE")
        self.assertEqual(logs[2]["diff"]["hair"]["from"], "blue hair")
        self.assertEqual(logs[2]["diff"]["hair"]["to"], "red hair")
        self.assertEqual(logs[2]["diff"]["seed"]["from"], 42)
        self.assertEqual(logs[2]["diff"]["seed"]["to"], 100)

        # Verify timestamp validity (should be around current time)
        current_time = time.time()
        for log in logs:
            self.assertTrue(abs(current_time - log["timestamp"]) < 5.0)

if __name__ == '__main__':
    unittest.main()
