import unittest
from ultra_modules.google_whisk_subject_bridge_core_engine import build_whisk_payload

class TestGoogleWhiskSubjectBridgeCoreEngine(unittest.TestCase):

    def test_normal_payload(self):
        """Test payload building with normal, expected inputs."""
        payload = build_whisk_payload(
            subject="A brave knight",
            style="Oil painting style",
            scene="In a dark forest"
        )
        self.assertEqual(payload["slots"]["subject"], "A brave knight")
        self.assertEqual(payload["slots"]["style"], "Oil painting style")
        self.assertEqual(payload["slots"]["scene"], "In a dark forest")

    def test_missing_parameters_fallback(self):
        """Test default fallback when parameters are missing or None."""
        payload = build_whisk_payload()
        self.assertEqual(payload["slots"]["subject"], "1girl, protagonist")
        self.assertEqual(payload["slots"]["style"], "anime, manga, high quality, masterpiece")
        self.assertEqual(payload["slots"]["scene"], "simple background, plain background")

        payload_none = build_whisk_payload(subject=None, style=None, scene=None)
        self.assertEqual(payload_none["slots"]["subject"], "1girl, protagonist")
        self.assertEqual(payload_none["slots"]["style"], "anime, manga, high quality, masterpiece")
        self.assertEqual(payload_none["slots"]["scene"], "simple background, plain background")

    def test_dirty_data_cleaning(self):
        """Test dirty data self-healing, such as excessive spaces or empty strings."""
        payload = build_whisk_payload(
            subject="   A    messy   subject  ",
            style="\n\n Messy \t style \n",
            scene="      "
        )
        self.assertEqual(payload["slots"]["subject"], "A messy subject")
        self.assertEqual(payload["slots"]["style"], "Messy style")
        self.assertEqual(payload["slots"]["scene"], "simple background, plain background") # Blank spaces cleaned to empty, then fallback

    def test_extreme_boundaries_truncation(self):
        """Test truncation for inputs exceeding max length."""
        long_subject = "A" * 2000
        payload = build_whisk_payload(subject=long_subject)

        self.assertEqual(len(payload["slots"]["subject"]), 1000)
        self.assertEqual(payload["slots"]["subject"], "A" * 1000)

    def test_invalid_types_conversion(self):
        """Test invalid types handling by casting to string or applying defaults."""
        payload = build_whisk_payload(
            subject=12345,
            style=["array", "of", "styles"],
            scene={"complex": "object"}
        )

        # Numbers should be stringified
        self.assertEqual(payload["slots"]["subject"], "12345")

        # String representations of lists/dicts (depending on how Python str() behaves)
        # Assuming our sanitize_input just calls str() on it
        self.assertEqual(payload["slots"]["style"], "['array', 'of', 'styles']")
        self.assertEqual(payload["slots"]["scene"], "{'complex': 'object'}")

if __name__ == '__main__':
    unittest.main()
