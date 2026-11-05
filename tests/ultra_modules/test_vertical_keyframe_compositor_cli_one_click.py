import json
import os
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

from ultra_modules.vertical_keyframe_compositor_cli_one_click import (
    CompositorConfig,
    process_keyframe,
    run_cli,
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT
)

class TestVerticalKeyframeCompositor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_img_path = os.path.join(self.temp_dir.name, "output.png")
        self.input_img_path = os.path.join(self.temp_dir.name, "input.png")

        # Create a dummy input image
        img = Image.new("RGB", (800, 600), color="blue")
        img.save(self.input_img_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normal_execution_with_minimum_defaults(self):
        """Test Case 1: Normal execution with minimal configuration."""
        config = CompositorConfig.from_dict({
            'output_image_path': self.output_img_path
        })

        # Missing input image -> should self-heal and generate placeholder
        result = process_keyframe(config, seed=42)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.output_img_path))

        # Verify output size
        with Image.open(self.output_img_path) as out_img:
            self.assertEqual(out_img.size, (DEFAULT_WIDTH, DEFAULT_HEIGHT))

    def test_dirty_data_self_healing(self):
        """Test Case 2: Dirty data self-healing (negative/non-numeric light intensity, invalid speed lines)."""
        dirty_data = {
            'light_intensity': -5.0, # Negative
            'speed_lines_count': "many", # Non-numeric
            'output_image_path': self.output_img_path
        }

        config = CompositorConfig.from_dict(dirty_data)

        # It should clamp intensity to 0.0 (from -5.0), and speed lines to default 50
        self.assertEqual(config.light_intensity, 0.0)
        self.assertEqual(config.speed_lines_count, 50)

        result = process_keyframe(config, seed=42)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.output_img_path))

    def test_missing_parameter_fallback(self):
        """Test Case 3: Missing parameter default fallback (empty string text)."""
        data = {
            'text': "   ", # Empty/whitespace string
            'output_image_path': self.output_img_path
        }

        config = CompositorConfig.from_dict(data)
        self.assertEqual(config.text, "默认字幕")

        # Run process
        result = process_keyframe(config, seed=42)
        self.assertTrue(result)

    def test_extreme_boundary_conditions(self):
        """Test Case 4: Extreme boundary conditions (broken input path, extreme config values)."""
        data = {
            'input_image_path': "/this/path/does/not/exist.png",
            'output_image_path': self.output_img_path,
            'light_intensity': 1000.0, # Exceeds clamp limit
            'speed_lines_count': 9999 # Exceeds clamp limit
        }

        config = CompositorConfig.from_dict(data)
        self.assertEqual(config.light_intensity, 5.0) # Clamped
        self.assertEqual(config.speed_lines_count, 500) # Clamped

        result = process_keyframe(config, seed=42)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.output_img_path))

    @patch('argparse.ArgumentParser.parse_args')
    def test_cli_execution_with_config_file(self, mock_parse_args):
        """Test Case 5: CLI execution path with broken config file and CLI overrides."""
        config_path = os.path.join(self.temp_dir.name, "config.json")

        # Write broken JSON
        with open(config_path, "w") as f:
            f.write("{ broken json ")

        mock_parse_args.return_value = type('Args', (), {
            'config': config_path,
            'input': self.input_img_path,
            'output': self.output_img_path,
            'text': 'CLI Subtitle'
        })()

        # Should gracefully handle broken JSON, use CLI args, and process
        run_cli()

        self.assertTrue(os.path.exists(self.output_img_path))

    @patch('argparse.ArgumentParser.parse_args')
    def test_cli_execution_with_excel_file(self, mock_parse_args):
        """Test Case 6: CLI execution path with an excel config file."""
        import pandas as pd
        config_path = os.path.join(self.temp_dir.name, "config.xlsx")

        # Write valid Excel
        df = pd.DataFrame([{
            'text': 'Excel Subtitle',
            'light_intensity': 2.5
        }])
        df.to_excel(config_path, index=False)

        mock_parse_args.return_value = type('Args', (), {
            'config': config_path,
            'input': self.input_img_path,
            'output': self.output_img_path,
            'text': None
        })()

        run_cli()

        self.assertTrue(os.path.exists(self.output_img_path))

if __name__ == '__main__':
    unittest.main()
