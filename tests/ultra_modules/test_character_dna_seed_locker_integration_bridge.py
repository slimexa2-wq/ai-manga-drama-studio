import unittest
from ultra_modules.character_dna_seed_locker_integration_bridge import CharacterDnaSeedLockerIntegrationBridge

class TestCharacterDnaSeedLockerIntegrationBridge(unittest.TestCase):

    def setUp(self):
        self.bridge = CharacterDnaSeedLockerIntegrationBridge()

    def test_normal_execution_forward_compatibility(self):
        # Maps legacy schema v1 directly to new schema (in payload and inner level)
        payload = {
            "hair": "silver",
            "eye": "red",
            "outfit": "mage robe",
            "character_dna": {
                "seed": 999
            }
        }
        result = self.bridge.bridge_dna_schema(payload)

        self.assertIn("character_dna", result)
        dna = result["character_dna"]

        # Mapped from payload
        self.assertEqual(dna["hair_color"], "silver")
        self.assertEqual(dna["eye_color"], "red")
        self.assertEqual(dna["clothing"], "mage robe")

        # Mapped from inner dict
        self.assertEqual(dna["fixed_seed"], 999)

        # Fallback
        self.assertEqual(dna["style_suffix"], "anime style, masterpiece, best quality")

        # Old payload keys should be cleaned up
        self.assertNotIn("hair", result)
        self.assertNotIn("eye", result)
        self.assertNotIn("outfit", result)
        self.assertNotIn("seed", dna)

    def test_missing_parameter_fallback(self):
        # A payload missing almost all DNA info
        payload = {
            "character_name": "Hero",
            "character_dna": {
                "hair_color": "blonde"
            }
        }
        result = self.bridge.bridge_dna_schema(payload)

        dna = result["character_dna"]
        self.assertEqual(dna["hair_color"], "blonde") # Preserved

        # Fallbacks applied
        self.assertEqual(dna["eye_color"], "black")
        self.assertEqual(dna["clothing"], "casual wear")
        self.assertEqual(dna["style_suffix"], "anime style, masterpiece, best quality")
        self.assertEqual(dna["fixed_seed"], 42)

        # Original keys untouched
        self.assertEqual(result["character_name"], "Hero")

    def test_dirty_data_self_healing(self):
        # Contains completely broken data types and empty strings
        payload = {
            "character_dna": {
                "hair_color": "",               # Empty string
                "eye_color": None,              # None
                "clothing": 123,                # Number instead of string
                "style_suffix": "   ",          # Blank string
                "fixed_seed": "not_a_number"    # Invalid int
            }
        }

        result = self.bridge.bridge_dna_schema(payload)
        dna = result["character_dna"]

        # All of the above should be healed to defaults
        self.assertEqual(dna["hair_color"], "black")
        self.assertEqual(dna["eye_color"], "black")
        self.assertEqual(dna["clothing"], "casual wear")
        self.assertEqual(dna["style_suffix"], "anime style, masterpiece, best quality")
        self.assertEqual(dna["fixed_seed"], 42)

    def test_extreme_boundary_empty_dict(self):
        # Empty payload
        payload = {}
        result = self.bridge.bridge_dna_schema(payload)

        self.assertIn("character_dna", result)
        dna = result["character_dna"]
        self.assertEqual(dna["hair_color"], "black")
        self.assertEqual(dna["eye_color"], "black")
        self.assertEqual(dna["clothing"], "casual wear")
        self.assertEqual(dna["style_suffix"], "anime style, masterpiece, best quality")
        self.assertEqual(dna["fixed_seed"], 42)

    def test_extreme_boundary_invalid_type(self):
        # Completely invalid payload type (e.g., None or a string/list)
        for invalid_payload in [None, "invalid_string", ["a", "list"], 12345]:
            with self.subTest(invalid_payload=invalid_payload):
                result = self.bridge.bridge_dna_schema(invalid_payload)
                self.assertIsInstance(result, dict)
                self.assertIn("character_dna", result)
                dna = result["character_dna"]
                self.assertEqual(dna["fixed_seed"], 42)

    def test_dirty_data_seed_float_to_int(self):
        # Testing if seed handles floats or float-strings properly
        payload = {
            "character_dna": {
                "fixed_seed": 42.9
            }
        }
        result = self.bridge.bridge_dna_schema(payload)
        self.assertEqual(result["character_dna"]["fixed_seed"], 42)

        payload2 = {
            "character_dna": {
                "fixed_seed": "100.5"
            }
        }
        result2 = self.bridge.bridge_dna_schema(payload2)
        self.assertEqual(result2["character_dna"]["fixed_seed"], 100)

    def test_dirty_data_corrupted_character_dna_node(self):
        # When 'character_dna' node exists but is not a dict
        payload = {
            "character_dna": "should_be_a_dict"
        }
        result = self.bridge.bridge_dna_schema(payload)
        self.assertIsInstance(result["character_dna"], dict)
        self.assertEqual(result["character_dna"]["hair_color"], "black")

if __name__ == '__main__':
    unittest.main()
