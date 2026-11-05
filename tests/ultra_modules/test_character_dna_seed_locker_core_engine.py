import unittest
from ultra_modules.character_dna_seed_locker_core_engine import CharacterDNALockerCoreEngine

class TestCharacterDNALockerCoreEngine(unittest.TestCase):

    def test_normal_valid_data(self):
        """Test with normal valid parameters"""
        dna_params = {
            "hair_color": "silver",
            "eye_color": "crimson",
            "clothing": "dark knight armor",
            "style_suffix": "dark fantasy, extremely detailed",
            "base_seed": 1024
        }
        result = CharacterDNALockerCoreEngine.lock_dna("char_001", "ep_01", dna_params)

        self.assertEqual(result["character_id"], "char_001")
        self.assertEqual(result["episode_id"], "ep_01")
        self.assertEqual(result["hair_color"], "silver")
        self.assertEqual(result["eye_color"], "crimson")
        self.assertEqual(result["clothing"], "dark knight armor")
        self.assertEqual(result["style_suffix"], "dark fantasy, extremely detailed")
        self.assertEqual(result["base_seed"], 1024)
        self.assertIsInstance(result["locked_seed"], int)

    def test_missing_parameter_fallbacks(self):
        """Test fallback mechanisms when parameters are omitted"""
        result = CharacterDNALockerCoreEngine.lock_dna("char_002", "ep_02", None)

        self.assertEqual(result["character_id"], "char_002")
        self.assertEqual(result["episode_id"], "ep_02")
        self.assertEqual(result["hair_color"], "black")
        self.assertEqual(result["eye_color"], "brown")
        self.assertEqual(result["clothing"], "casual wear")
        self.assertEqual(result["style_suffix"], "anime style, masterpiece, best quality")
        self.assertEqual(result["base_seed"], 42)
        self.assertIsInstance(result["locked_seed"], int)

        # Test with empty dict
        result2 = CharacterDNALockerCoreEngine.lock_dna("char_003", "ep_03", {})
        self.assertEqual(result2["hair_color"], "black")

    def test_dirty_data_auto_healing(self):
        """Test silent auto-healing of dirty data (wrong types, extra spaces)"""
        dirty_params = {
            "hair_color": "   blonde   ",  # Trailing spaces
            "eye_color": 12345,  # Int instead of string
            "clothing": ["a", "list"],  # List instead of string
            "style_suffix": {"dict": "value"},  # Dict instead of string
            "base_seed": "  999.5  "  # String float instead of int
        }
        # Non-string IDs
        result = CharacterDNALockerCoreEngine.lock_dna(100, 200, dirty_params)

        self.assertEqual(result["character_id"], "100")
        self.assertEqual(result["episode_id"], "200")
        self.assertEqual(result["hair_color"], "blonde")
        self.assertEqual(result["eye_color"], "12345")
        self.assertEqual(result["clothing"], "['a', 'list']")
        self.assertEqual(result["style_suffix"], "{'dict': 'value'}")
        self.assertEqual(result["base_seed"], 999)
        self.assertIsInstance(result["locked_seed"], int)

    def test_extreme_boundaries(self):
        """Test extreme boundaries like None values everywhere and un-stringable objects"""

        class Unstringable:
            def __str__(self):
                raise ValueError("Cannot stringify")

        extreme_params = {
            "hair_color": None,
            "eye_color": Unstringable(),
            "clothing": "",  # Empty string
            "style_suffix": None,
            "base_seed": "not_a_number"
        }

        result = CharacterDNALockerCoreEngine.lock_dna(None, None, extreme_params)

        self.assertEqual(result["character_id"], "unknown_character")
        self.assertEqual(result["episode_id"], "unknown_episode")
        self.assertEqual(result["hair_color"], "black")
        self.assertEqual(result["eye_color"], "brown")  # Fallback due to exception
        self.assertEqual(result["clothing"], "casual wear")  # Fallback due to empty string
        self.assertEqual(result["style_suffix"], "anime style, masterpiece, best quality")
        self.assertEqual(result["base_seed"], 42)  # Fallback due to invalid seed string
        self.assertIsInstance(result["locked_seed"], int)

        # Another test for float seed
        float_params = {"base_seed": 3.14}
        result2 = CharacterDNALockerCoreEngine.lock_dna("c", "e", float_params)
        self.assertEqual(result2["base_seed"], 3)

    def test_seed_derivation_determinism(self):
        """Test that the derived locked_seed is deterministic for the same inputs, but varies across different inputs"""
        params1 = {"base_seed": 100}

        # Same character, same episode -> Same locked seed
        res1 = CharacterDNALockerCoreEngine.lock_dna("hero", "ep1", params1)
        res2 = CharacterDNALockerCoreEngine.lock_dna("hero", "ep1", params1)
        self.assertEqual(res1["locked_seed"], res2["locked_seed"])

        # Same character, different episode -> Different locked seed
        res3 = CharacterDNALockerCoreEngine.lock_dna("hero", "ep2", params1)
        self.assertNotEqual(res1["locked_seed"], res3["locked_seed"])

        # Different character, same episode -> Different locked seed
        res4 = CharacterDNALockerCoreEngine.lock_dna("villain", "ep1", params1)
        self.assertNotEqual(res1["locked_seed"], res4["locked_seed"])

        # Same character, same episode, different base_seed -> Different locked seed
        params2 = {"base_seed": 101}
        res5 = CharacterDNALockerCoreEngine.lock_dna("hero", "ep1", params2)
        self.assertNotEqual(res1["locked_seed"], res5["locked_seed"])

if __name__ == '__main__':
    unittest.main()
