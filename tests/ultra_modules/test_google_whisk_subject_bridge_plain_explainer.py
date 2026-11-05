import unittest
import json
from ultra_modules.google_whisk_subject_bridge_plain_explainer import GoogleWhiskSubjectBridgePlainExplainer

class TestGoogleWhiskSubjectBridgePlainExplainer(unittest.TestCase):

    def test_normal_valid_inputs(self):
        """Test with completely valid, well-formed input data."""
        payload = {
            "subject": {"name": "A cute cat", "confidence": 0.95},
            "style": {"name": "Cyberpunk", "intensity": 0.8},
            "scene": {"name": "Night City", "lighting": "Neon"}
        }

        md = GoogleWhiskSubjectBridgePlainExplainer.generate_markdown_card(payload)
        self.assertIn("A cute cat", md)
        self.assertIn("0.95", md)
        self.assertIn("Cyberpunk", md)
        self.assertIn("0.80", md)
        self.assertIn("Night City", md)
        self.assertIn("Neon", md)

        html = GoogleWhiskSubjectBridgePlainExplainer.generate_html_card(payload)
        self.assertIn("<b>Subject</b>: A cute cat", html)

        j_str = GoogleWhiskSubjectBridgePlainExplainer.generate_json_card(payload)
        j_data = json.loads(j_str)
        self.assertEqual(j_data["summary"]["subject_name"], "A cute cat")

    def test_missing_data_fallback(self):
        """Test handling of missing keys, providing safe default values."""
        payload = {
            # Empty payload
        }

        md = GoogleWhiskSubjectBridgePlainExplainer.generate_markdown_card(payload)
        self.assertIn("Unknown Subject", md)
        self.assertIn("0.00", md)
        self.assertIn("Standard Style", md)
        self.assertIn("Default Scene", md)
        self.assertIn("Standard Lighting", md)

    def test_dirty_data_self_healing(self):
        """Test robust handling of dirty data formats (e.g. percentages as strings, nulls)."""
        payload = {
            "subject": {"name": None, "confidence": "95%"},
            "style": {"name": " Watercolor  ", "intensity": "invalid_float"},
            "scene": {"name": 12345, "lighting": None}
        }

        md = GoogleWhiskSubjectBridgePlainExplainer.generate_markdown_card(payload)
        self.assertIn("Unknown Subject", md)
        self.assertIn("0.95", md)  # 95% converted to 0.95
        self.assertIn("Watercolor", md)  # Stripped
        self.assertIn("0.00", md)  # Invalid float converted to default 0.0
        self.assertIn("12345", md)  # Int converted to str
        self.assertIn("Standard Lighting", md) # None converted to default

    def test_extreme_boundary_values(self):
        """Test extreme/boundary values for numbers and deeply nested empty dicts."""
        payload = {
            "subject": {"name": "", "confidence": -99999.99},
            "style": {"name": "A" * 1000, "intensity": 1e9},
            "scene": {"name": "", "lighting": ""}
        }

        md = GoogleWhiskSubjectBridgePlainExplainer.generate_markdown_card(payload)
        self.assertIn("Unknown Subject", md)  # Empty string defaults back
        self.assertIn("-99999.99", md)
        self.assertIn("A" * 1000, md)
        self.assertIn("1000000000.00", md)
        self.assertIn("Default Scene", md)

    def test_invalid_top_level_payload(self):
        """Test when the entire payload is garbage (None, string, int, list)."""
        bad_payloads = [
            None,
            "just a string",
            123,
            ["a", "list"],
            '{"subject": "this is a string, not a dict"}' # Valid JSON, but bad types inside
        ]

        for bad_p in bad_payloads:
            md = GoogleWhiskSubjectBridgePlainExplainer.generate_markdown_card(bad_p)
            self.assertIn("Unknown Subject", md)
            self.assertIn("Standard Style", md)
            self.assertIn("Default Scene", md)

            j_str = GoogleWhiskSubjectBridgePlainExplainer.generate_json_card(bad_p)
            j_data = json.loads(j_str)
            self.assertEqual(j_data["summary"]["subject_name"], "Unknown Subject")

if __name__ == '__main__':
    unittest.main()
