import unittest
from ultra_modules.google_whisk_subject_bridge_integration_bridge import WhiskPayloadBuilder

class TestWhiskPayloadBuilderIntegrationBridge(unittest.TestCase):
    def test_normal_v2_schema(self):
        """Validating payload generation with all correct parameters (subject, style, scene)."""
        payload = WhiskPayloadBuilder.build(subject="boy", style="3D render", scene="city")
        self.assertEqual(payload["subject"], "boy")
        self.assertEqual(payload["style"], "3D render")
        self.assertEqual(payload["scene"], "city")
        self.assertIn("timestamp", payload)
        self.assertEqual(payload["status"], "built")

    def test_legacy_schema_mapping(self):
        """Testing backwards compatibility by passing older schema formats."""
        payload = WhiskPayloadBuilder.build(character_prompt="superman", art_style="comic", background="space")
        self.assertEqual(payload["subject"], "superman")
        self.assertEqual(payload["style"], "comic")
        self.assertEqual(payload["scene"], "space")

        # Mixed schema mapping
        payload_mixed = WhiskPayloadBuilder.build(subject="cat", medium="oil painting", setting="garden")
        self.assertEqual(payload_mixed["subject"], "cat")
        self.assertEqual(payload_mixed["style"], "oil painting")
        self.assertEqual(payload_mixed["scene"], "garden")

    def test_missing_parameters_fallback(self):
        """Ensuring missing params trigger reasonable defaults silently."""
        payload = WhiskPayloadBuilder.build()
        self.assertEqual(payload["subject"], "default subject")
        self.assertEqual(payload["style"], "default style")
        self.assertEqual(payload["scene"], "default scene")

        payload_partial = WhiskPayloadBuilder.build(subject="girl")
        self.assertEqual(payload_partial["subject"], "girl")
        self.assertEqual(payload_partial["style"], "default style")
        self.assertEqual(payload_partial["scene"], "default scene")

    def test_dirty_data_healing(self):
        """Checking handling of None, empty strings, and non-string inputs."""
        payload = WhiskPayloadBuilder.build(subject=None, style="   ", scene=12345)
        self.assertEqual(WhiskPayloadBuilder._sanitize(None, "default subject"), "default subject")
        self.assertEqual(payload["style"], "default style")
        self.assertEqual(payload["scene"], "12345")

        payload_empty = WhiskPayloadBuilder.build(subject="", style="\t\n", scene=[])
        self.assertEqual(payload_empty["subject"], "default subject")
        self.assertEqual(payload_empty["style"], "default style")
        self.assertEqual(payload_empty["scene"], "[]")

        # Test class _sanitize explicitly to ensure coverage of exception block
        # Need a type that raises an exception on str() if possible, or at least test a weird object.
        class Unstringable:
            def __str__(self):
                raise Exception("Cannot convert to string")

        payload_weird = WhiskPayloadBuilder.build(subject=Unstringable())
        self.assertEqual(payload_weird["subject"], "default subject")

    def test_extreme_boundary_edge_cases(self):
        """Testing extremely long strings or unexpected structures."""
        long_str = "a" * 10000
        payload = WhiskPayloadBuilder.build(subject=long_str, style=long_str, scene=long_str)
        self.assertEqual(payload["subject"], long_str)
        self.assertEqual(payload["style"], long_str)
        self.assertEqual(payload["scene"], long_str)

        # Pass unexpected kwargs, they should be ignored
        payload_extra = WhiskPayloadBuilder.build(subject="dog", random_key="value")
        self.assertEqual(payload_extra["subject"], "dog")
        self.assertNotIn("random_key", payload_extra)

if __name__ == "__main__":
    # pragma: no cover
    unittest.main()
