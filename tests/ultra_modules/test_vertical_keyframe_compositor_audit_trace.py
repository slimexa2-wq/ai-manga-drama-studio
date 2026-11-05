import unittest
from PIL import Image
from ultra_modules.vertical_keyframe_compositor_audit_trace import KeyframeCompositor, AuditLogger

class TestVerticalKeyframeCompositorAuditTrace(unittest.TestCase):
    def test_normal_operation(self):
        config = {
            "width": 1080,
            "height": 1920,
            "speed_lines": 50,
            "text": "Hello World",
            "light_effect": True
        }
        compositor = KeyframeCompositor(config)

        # Test with a valid base image
        base_image = Image.new("RGBA", (1080, 1920), (100, 100, 100, 255))
        result_img = compositor.render(base_image)

        self.assertEqual(result_img.size, (1080, 1920))

        logs = compositor.get_audit_trail()
        actions = [log["action"] for log in logs]

        self.assertIn("effect", actions)

        # We expect light effect, speed lines, and subtitle
        effect_logs = [log["details"] for log in logs if log["action"] == "effect"]
        self.assertIn("Applied light effect", effect_logs)
        self.assertIn("Applied 50 speed lines", effect_logs)
        self.assertIn("Applied double-stroke subtitle", effect_logs)

    def test_missing_config_defaults(self):
        compositor = KeyframeCompositor({})
        result_img = compositor.render(None)

        self.assertEqual(result_img.size, (1080, 1920)) # Defaults

        logs = compositor.get_audit_trail()

        # Check defaults were used for missing keys
        fallback_logs = [log["details"] for log in logs if log["action"] == "fallback"]
        self.assertTrue(any("Missing width" in l for l in fallback_logs))
        self.assertTrue(any("Missing height" in l for l in fallback_logs))
        self.assertTrue(any("No base image provided" in l for l in fallback_logs))

    def test_dirty_data_self_healing(self):
        config = {
            "width": "not_an_int",
            "height": "1920px", # Also not parseable by int() directly
            "speed_lines": "some string",
            "text": "AAAABBBBBBBBBBBCCCCC",
            "light_effect": "True" # string instead of bool
        }
        compositor = KeyframeCompositor(config)

        # Test with invalid base image type
        result_img = compositor.render("invalid_image_type")

        self.assertEqual(result_img.size, (1080, 1920)) # Should fallback to 1080x1920
        self.assertEqual(compositor.config["text"], "AAAABBBBBCCCCC") # Deduplicated text > 5

        logs = compositor.get_audit_trail()
        sanitization_logs = [log["details"] for log in logs if log["action"] == "sanitization"]
        fallback_logs = [log["details"] for log in logs if log["action"] == "fallback"]

        self.assertTrue(any("Invalid width type or value" in l for l in sanitization_logs))
        self.assertTrue(any("Invalid height type or value" in l for l in sanitization_logs))
        self.assertTrue(any("Invalid speed_lines type or value" in l for l in sanitization_logs))
        self.assertTrue(any("Deduplicated excessively repeated characters" in l for l in sanitization_logs))
        self.assertTrue(any("light_effect is not a boolean" in l for l in sanitization_logs))
        self.assertTrue(any("Invalid base image type" in l for l in fallback_logs))

    def test_extreme_boundary_cases(self):
        config = {
            "width": -100,
            "height": 0,
            "speed_lines": 99999,
            "text": None
        }
        compositor = KeyframeCompositor(config)

        # Test resizing base image that is smaller/larger
        base_image = Image.new("RGBA", (500, 500), (0, 0, 0, 255))
        result_img = compositor.render(base_image)

        self.assertEqual(result_img.size, (1080, 1920)) # Width, height should be sanitized to default 1080, 1920
        self.assertEqual(compositor.config["speed_lines"], 500) # Capped at 500
        self.assertEqual(compositor.config["text"], "") # Coerced to string

        logs = compositor.get_audit_trail()
        sanitization_logs = [log["details"] for log in logs if log["action"] == "sanitization"]

        self.assertTrue(any("Negative or zero width" in l for l in sanitization_logs))
        self.assertTrue(any("Negative or zero height" in l for l in sanitization_logs))
        self.assertTrue(any("Excessive speed_lines" in l for l in sanitization_logs))
        self.assertTrue(any("Text is not a string" in l for l in sanitization_logs))
        self.assertTrue(any("Resizing base image" in l for l in sanitization_logs))

        # Test negative speed_lines
        compositor2 = KeyframeCompositor({"speed_lines": -50})
        self.assertEqual(compositor2.config["speed_lines"], 0)

    def test_type_mismatch_self_healing(self):
        # Pass completely invalid type for config (e.g., int or string)
        compositor = KeyframeCompositor("completely_invalid_config")
        result_img = compositor.render()

        self.assertEqual(result_img.size, (1080, 1920))

        logs = compositor.get_audit_trail()
        fallback_logs = [log["details"] for log in logs if log["action"] == "fallback"]

        self.assertTrue(any("Config is not a dict" in l for l in fallback_logs))

        # Try with a list
        compositor2 = KeyframeCompositor([1, 2, 3])
        self.assertEqual(compositor2.config["width"], 1080)

if __name__ == '__main__':
    unittest.main()
