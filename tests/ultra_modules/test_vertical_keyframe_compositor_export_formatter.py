import unittest
import math
from ultra_modules.vertical_keyframe_compositor_export_formatter import format_export_data, clean_numeric

class TestVerticalKeyframeCompositorExportFormatter(unittest.TestCase):

    def test_normal_execution(self):
        """Test with normal, expected data."""
        data = {
            'speedline_intensity': 0.7,
            'light_effect_opacity': 0.9,
            'subtitle': {
                'text': '你好，世界',
                'inner_stroke_width': 3.0,
                'outer_stroke_width': 5.0,
                'font_size': 80.0
            }
        }
        export_data, report = format_export_data(data)

        self.assertEqual(export_data['resolution']['width'], 1080)
        self.assertEqual(export_data['resolution']['height'], 1920)
        self.assertEqual(export_data['comments'], 0)
        self.assertAlmostEqual(export_data['speedline_intensity'], 0.7)
        self.assertAlmostEqual(export_data['light_effect_opacity'], 0.9)
        self.assertEqual(export_data['subtitle']['text'], '你好，世界')
        self.assertAlmostEqual(export_data['subtitle']['inner_stroke_width'], 3.0)
        self.assertAlmostEqual(export_data['subtitle']['outer_stroke_width'], 5.0)
        self.assertAlmostEqual(export_data['subtitle']['font_size'], 80.0)
        self.assertEqual(export_data['export_status'], "SUCCESS")

        report_lines = report.split('\n')
        self.assertEqual(len(report_lines), 3)
        self.assertIn("1080x1920", report_lines[0])
        self.assertIn("0.70", report_lines[1])
        self.assertIn("0.90", report_lines[1])
        self.assertIn("你好，世界", report_lines[2])

    def test_missing_parameter_fallbacks(self):
        """Test with empty data to ensure defaults are applied properly."""
        data = {}
        export_data, report = format_export_data(data)

        self.assertEqual(export_data['resolution']['width'], 1080)
        self.assertEqual(export_data['resolution']['height'], 1920)
        self.assertEqual(export_data['comments'], 0)
        self.assertAlmostEqual(export_data['speedline_intensity'], 0.5)
        self.assertAlmostEqual(export_data['light_effect_opacity'], 0.8)
        self.assertEqual(export_data['subtitle']['text'], '默认字幕')
        self.assertAlmostEqual(export_data['subtitle']['inner_stroke_width'], 2.0)
        self.assertAlmostEqual(export_data['subtitle']['outer_stroke_width'], 4.0)
        self.assertAlmostEqual(export_data['subtitle']['font_size'], 72.0)

    def test_dirty_data_self_healing(self):
        """Test with unparseable data, NaN, None, and lists to ensure self-healing."""
        data = {
            'speedline_intensity': None,
            'light_effect_opacity': 'invalid_string',
            'subtitle': {
                'text': '',
                'inner_stroke_width': float('nan'),
                'outer_stroke_width': float('inf'),
                'font_size': [1, 2, 3]
            }
        }
        export_data, report = format_export_data(data)

        self.assertEqual(export_data['comments'], 0)
        self.assertAlmostEqual(export_data['speedline_intensity'], 0.5)
        self.assertAlmostEqual(export_data['light_effect_opacity'], 0.8)
        self.assertEqual(export_data['subtitle']['text'], '默认字幕')
        self.assertAlmostEqual(export_data['subtitle']['inner_stroke_width'], 2.0)
        self.assertAlmostEqual(export_data['subtitle']['outer_stroke_width'], 4.0)
        self.assertAlmostEqual(export_data['subtitle']['font_size'], 72.0)

    def test_extreme_boundary_conditions(self):
        """Test with extreme numeric values that are technically valid."""
        data = {
            'speedline_intensity': 1e9,
            'light_effect_opacity': -1e9,
            'subtitle': {
                'text': 'A' * 1000,  # very long string
                'inner_stroke_width': 0.0,
                'outer_stroke_width': -10.5,
                'font_size': 0.0001
            }
        }
        export_data, report = format_export_data(data)

        self.assertAlmostEqual(export_data['speedline_intensity'], 1e9)
        self.assertAlmostEqual(export_data['light_effect_opacity'], -1e9)
        self.assertEqual(export_data['subtitle']['text'], 'A' * 1000)
        self.assertAlmostEqual(export_data['subtitle']['inner_stroke_width'], 0.0)
        self.assertAlmostEqual(export_data['subtitle']['outer_stroke_width'], -10.5)
        self.assertAlmostEqual(export_data['subtitle']['font_size'], 0.0001)

    def test_invalid_input_type(self):
        """Test with non-dictionary input ensuring graceful fallback."""
        export_data, report = format_export_data(None) # type: ignore
        self.assertEqual(export_data['resolution']['width'], 1080)
        self.assertEqual(export_data['resolution']['height'], 1920)
        self.assertEqual(export_data['comments'], 0)

        export_data, report = format_export_data([]) # type: ignore
        self.assertEqual(export_data['resolution']['width'], 1080)
        self.assertEqual(export_data['resolution']['height'], 1920)
        self.assertEqual(export_data['comments'], 0)

    def test_clean_numeric_helper(self):
        """Test the clean_numeric helper function directly for specific branches."""
        self.assertEqual(clean_numeric(1.5, 0.0), 1.5)
        self.assertEqual(clean_numeric("2.5", 0.0), 2.5)
        self.assertEqual(clean_numeric(float('nan'), 0.0), 0.0)
        self.assertEqual(clean_numeric(float('inf'), 0.0), 0.0)
        self.assertEqual(clean_numeric(None, 0.0), 0.0)
        self.assertEqual(clean_numeric("invalid", 0.0), 0.0)
        self.assertEqual(clean_numeric("nan", 0.0), 0.0)
        self.assertEqual(clean_numeric("inf", 0.0), 0.0)

if __name__ == '__main__':
    unittest.main()
