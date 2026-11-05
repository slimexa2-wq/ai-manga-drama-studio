import unittest
from PIL import Image
import numpy as np
from ultra_modules.vertical_keyframe_compositor_core_engine import VerticalKeyframeCompositorCoreEngine

class TestVerticalKeyframeCompositorCoreEngine(unittest.TestCase):

    def setUp(self):
        self.engine = VerticalKeyframeCompositorCoreEngine()
        self.default_size = (1080, 1920)
        self.test_image = Image.new("RGBA", self.default_size, (10, 20, 30, 255))

    def test_01_normal_operation(self):
        """Test the engine with normal parameters to ensure it runs without errors."""
        light_params = {"intensity": 1.0, "color": (255, 255, 255, 100)}
        speed_lines_params = {"density": 0.5, "color": (200, 200, 200, 150)}
        subtitle_params = {
            "text": "测试正常字幕",
            "font_size": 100,
            "inner_color": (255, 255, 255, 255),
            "stroke1_color": (0, 0, 0, 255),
            "stroke2_color": (255, 0, 0, 255)
        }

        result = self.engine.compose(
            self.test_image,
            light_params=light_params,
            speed_lines_params=speed_lines_params,
            subtitle_params=subtitle_params
        )

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, self.default_size)
        self.assertEqual(result.mode, "RGBA")

    def test_02_dirty_data_self_healing(self):
        """Test the engine's ability to handle wrong types and out of bound values silently."""
        # Intentionally wrong types or invalid data
        light_params = {"intensity": "invalid_string", "color": [255, "bad", 100]}
        speed_lines_params = {"density": float('inf'), "color": "#123"}
        subtitle_params = {
            "text": 12345, # Not a string
            "font_size": -10, # Out of bounds
            "inner_color": "not_a_color",
            "stroke1_color": (0, 0), # Not enough elements
            "stroke2_width": "large" # Wrong type
        }

        # Pass a wrong type for image (e.g. integer instead of Image object)
        result = self.engine.compose(
            999,
            light_params=light_params,
            speed_lines_params=speed_lines_params,
            subtitle_params=subtitle_params
        )

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, self.default_size)
        self.assertEqual(result.mode, "RGBA")

    def test_03_missing_parameter_fallbacks(self):
        """Test the engine when entirely no parameters are provided (None)."""
        result = self.engine.compose(
            None,
            light_params=None,
            speed_lines_params=None,
            subtitle_params=None
        )

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, self.default_size)
        self.assertEqual(result.mode, "RGBA")

    def test_04_extreme_boundary_conditions(self):
        """Test the engine with very large, very small, NaN, and Infinity values."""
        light_params = {"intensity": float('nan'), "color": (1000, -500, 255, 255)}
        speed_lines_params = {"density": -50.5, "color": "#FFFFFFFF"}
        subtitle_params = {
            "text": "", # Empty string
            "font_size": 9999, # Large font size
            "stroke1_width": -10, # Negative width
            "stroke2_width": float('inf') # Infinity width
        }

        # Small wrong size image
        small_image = Image.new("RGB", (100, 100), (0, 0, 0))

        result = self.engine.compose(
            small_image,
            light_params=light_params,
            speed_lines_params=speed_lines_params,
            subtitle_params=subtitle_params
        )

        self.assertIsInstance(result, Image.Image)
        # Verify automatic resize
        self.assertEqual(result.size, self.default_size)
        # Verify automatic conversion to RGBA
        self.assertEqual(result.mode, "RGBA")

    def test_05_color_hex_cleaning(self):
        """Specifically test the color hex string cleaning logic."""
        result_6 = self.engine._clean_color("#FF0000")
        self.assertEqual(result_6, (255, 0, 0, 255))

        result_8 = self.engine._clean_color("#00FF0080")
        self.assertEqual(result_8, (0, 255, 0, 128))

        # Invalid hex
        result_invalid = self.engine._clean_color("#GGGGGG", default=(1, 2, 3, 4))
        self.assertEqual(result_invalid, (1, 2, 3, 4))

if __name__ == "__main__":
    unittest.main()
