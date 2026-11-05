import unittest
from ultra_modules.vertical_keyframe_compositor_integration_bridge import VerticalKeyframeCompositorIntegrationBridge

class TestVerticalKeyframeCompositorIntegrationBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = VerticalKeyframeCompositorIntegrationBridge()

    def test_normal_expected_data(self):
        """Test with correctly formatted data adhering to the new schema."""
        input_data = {
            "width": 1080,
            "height": 1920,
            "light_effect": "glow",
            "speed_lines": True,
            "double_layer_stroke": True,
            "subtitle": "Hello World"
        }
        normalized = self.bridge.bridge_and_normalize(input_data)
        self.assertEqual(normalized["width"], 1080)
        self.assertEqual(normalized["height"], 1920)
        self.assertEqual(normalized["light_effect"], "glow")
        self.assertEqual(normalized["speed_lines"], True)
        self.assertEqual(normalized["double_layer_stroke"], True)
        self.assertEqual(normalized["subtitle"], "Hello World")

    def test_dirty_data_self_healing(self):
        """Test handling of None or entirely invalid types gracefully falling back to defaults."""
        normalized_none = self.bridge.bridge_and_normalize(None)
        self.assertEqual(normalized_none["width"], 1080)
        self.assertEqual(normalized_none["height"], 1920)
        self.assertEqual(normalized_none["light_effect"], "none")
        self.assertEqual(normalized_none["speed_lines"], False)
        self.assertEqual(normalized_none["double_layer_stroke"], False)
        self.assertEqual(normalized_none["subtitle"], "")

        normalized_string = self.bridge.bridge_and_normalize("invalid_string_data")
        self.assertEqual(normalized_string["width"], 1080)
        self.assertEqual(normalized_string["height"], 1920)

    def test_missing_parameter_fallbacks(self):
        """Test handling of empty dictionaries where all parameters are missing."""
        input_data = {}
        normalized = self.bridge.bridge_and_normalize(input_data)
        self.assertEqual(normalized["width"], 1080)
        self.assertEqual(normalized["height"], 1920)
        self.assertEqual(normalized["light_effect"], "none")
        self.assertEqual(normalized["speed_lines"], False)
        self.assertEqual(normalized["double_layer_stroke"], False)
        self.assertEqual(normalized["subtitle"], "")

    def test_extreme_edge_cases(self):
        """Test negative dimensions and incorrect data types falling back to defaults."""
        input_data = {
            "width": -100,  # invalid negative
            "height": 0,    # invalid zero
            "w": -50,
            "h": -100,
            "resolution_w": -500,
            "resolution_h": 0,
            "light_effect": 123, # invalid type for light effect
            "effect_light": 456,
            "speed_lines": "maybe", # strings are truthy but will cast to True which is acceptable fallback logic, let's pass a boolean here to see what happens, wait, bool("maybe") is True.
            # let's test subtitle casting
            "subtitle": 42,
            "sub": None,
            "text_subtitle": None
        }
        normalized = self.bridge.bridge_and_normalize(input_data)
        # Negative dimensions should be ignored and default applied
        self.assertEqual(normalized["width"], 1080)
        self.assertEqual(normalized["height"], 1920)
        # Non-string light effect should be ignored
        self.assertEqual(normalized["light_effect"], "none")
        # Subtitle should be casted to string "42"
        self.assertEqual(normalized["subtitle"], "42")
        self.assertEqual(normalized["speed_lines"], True) # bool("maybe") is True

        input_data2 = {
            "speed_lines": "", # bool("") is False
            "subtitle": None,
            "sub": 12.34
        }
        normalized2 = self.bridge.bridge_and_normalize(input_data2)
        self.assertEqual(normalized2["speed_lines"], False)
        self.assertEqual(normalized2["subtitle"], "12.34")

    def test_schema_mapping(self):
        """Test the forward compatibility mapping of multiple old version field names."""
        input_data = {
            "w": 500,
            "h": 500,
            "effect_light": "sparkle",
            "lines_speed": True,
            "stroke_double_layer": True,
            "sub": "Old Subtitle"
        }
        normalized = self.bridge.bridge_and_normalize(input_data)
        self.assertEqual(normalized["width"], 500)
        self.assertEqual(normalized["height"], 500)
        self.assertEqual(normalized["light_effect"], "sparkle")
        self.assertEqual(normalized["speed_lines"], True)
        self.assertEqual(normalized["double_layer_stroke"], True)
        self.assertEqual(normalized["subtitle"], "Old Subtitle")

        # Test alternative old fields
        input_data2 = {
            "resolution_w": 800,
            "resolution_h": 600,
            "has_speed_lines": True,
            "has_double_stroke": True,
            "text_subtitle": "Alternative Old"
        }
        normalized2 = self.bridge.bridge_and_normalize(input_data2)
        self.assertEqual(normalized2["width"], 800)
        self.assertEqual(normalized2["height"], 600)
        self.assertEqual(normalized2["speed_lines"], True)
        self.assertEqual(normalized2["double_layer_stroke"], True)
        self.assertEqual(normalized2["subtitle"], "Alternative Old")

if __name__ == '__main__':
    unittest.main()
