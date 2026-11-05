import unittest
import time
import os
import tempfile
from PIL import Image

from ultra_modules.vertical_keyframe_compositor_self_healing_guard import VerticalKeyframeCompositorSelfHealingGuard

class TestVerticalKeyframeCompositorSelfHealingGuard(unittest.TestCase):
    def setUp(self):
        self.compositor = VerticalKeyframeCompositorSelfHealingGuard()
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create a valid test image
        self.valid_image_path = os.path.join(self.temp_dir.name, 'valid.png')
        img = Image.new('RGB', (1080, 1920), color='blue')
        img.save(self.valid_image_path)

        # Create an image with wrong size
        self.wrong_size_path = os.path.join(self.temp_dir.name, 'wrong_size.png')
        img_wrong = Image.new('RGB', (500, 500), color='green')
        img_wrong.save(self.wrong_size_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normal_render(self):
        """Test normal operation with all features enabled (light, speed lines, subtitle)."""
        options = {
            'light_intensity': 0.8,
            'speed_lines_intensity': 0.5,
            'subtitle_text': 'This is a test subtitle'
        }

        result_img = self.compositor.render_keyframe(self.valid_image_path, options)

        self.assertIsNotNone(result_img)
        self.assertEqual(result_img.size, (1080, 1920))
        self.assertEqual(result_img.mode, 'RGBA')

        # Check that history was updated
        self.assertEqual(len(self.compositor._history), 1)

    def test_dirty_data_self_healing(self):
        """Dirty data self-healing: invalid types, out-of-range parameters, invalid image path."""
        # 1. Invalid image path
        result_img_bad_path = self.compositor.render_keyframe("invalid/path/that/does/not/exist.png", {})
        self.assertIsNotNone(result_img_bad_path)
        self.assertEqual(result_img_bad_path.size, (1080, 1920))

        # 2. Image with wrong size (should be automatically resized)
        result_img_wrong_size = self.compositor.render_keyframe(self.wrong_size_path, {})
        self.assertEqual(result_img_wrong_size.size, (1080, 1920))

        # 3. Invalid types and out-of-range parameters
        options = {
            'light_intensity': "not_a_number", # Should self-heal or fallback
            'speed_lines_intensity': 9999.9, # Should be clamped to 1.0
            'subtitle_text': 12345 # Invalid type for text, should self-heal
        }
        result_img_dirty = self.compositor.render_keyframe(self.valid_image_path, options)
        self.assertIsNotNone(result_img_dirty)
        self.assertEqual(result_img_dirty.size, (1080, 1920))

    def test_branch_coverage_edges(self):
        """Test specific edge cases to ensure 100% branch coverage for exceptions and early returns."""
        # Force Exception in undo
        self.compositor._history = None # Will cause TypeError when undoing
        self.assertIsNone(self.compositor.undo())
        self.compositor._history = [] # Reset

        # Force Exception in _render_light_effect
        class BadImage:
            @property
            def size(self):
                raise ValueError("Bad size")
            def convert(self, mode):
                return Image.new('RGBA', (10, 10))

        bad_img = BadImage()
        res_light = self.compositor._render_light_effect(bad_img, 0.5)
        self.assertEqual(res_light.size, (10, 10))

        # Test speed lines with <=0 intensity (early return)
        res_speed = self.compositor._render_speed_lines(bad_img, 0)
        self.assertEqual(res_speed, bad_img)

        # Force Exception in _render_speed_lines
        res_speed = self.compositor._render_speed_lines(bad_img, 0.5)
        self.assertEqual(res_speed.size, (10, 10))

        # Force Exception in _render_dual_stroke_subtitle
        res_subtitle = self.compositor._render_dual_stroke_subtitle(bad_img, "Test")
        self.assertEqual(res_subtitle.size, (10, 10))

        # Force Exception in render_keyframe itself (Absolute self-healing fallback)
        # Mock _save_snapshot to raise exception
        original_save = self.compositor._save_snapshot
        def bad_save(state):
            raise RuntimeError("Boom")
        self.compositor._save_snapshot = bad_save

        # It should trigger the absolute fallback which returns fallback, but wait fallback also gets saved causing exception in save which triggers inner try-except
        res_fallback = self.compositor.render_keyframe(self.valid_image_path, {})
        self.assertIsNone(res_fallback)

        # Force Exception in the absolute fallback itself
        self.compositor.width = -1
        self.compositor.height = -1
        res_double_fallback = self.compositor.render_keyframe(self.valid_image_path, {})
        self.assertIsNone(res_double_fallback)

        self.compositor._save_snapshot = original_save
        self.compositor.width = 1080
        self.compositor.height = 1920

        # Try to trigger the success case of the fallback block
        # We need to monkey patch something that runs after snapshot saving to raise Exception.
        original_render_light = self.compositor._render_light_effect
        def bad_render_light(base_image, intensity):
            raise RuntimeError("Force fallback success")
        self.compositor._render_light_effect = bad_render_light

        res_absolute = self.compositor.render_keyframe(self.valid_image_path, {})
        self.assertEqual(res_absolute.size, (1080, 1920))

        self.compositor._render_light_effect = original_render_light

    def test_missing_params_fallback(self):
        """Missing parameters fallback: empty options/None."""
        # Options is None
        result_img_none = self.compositor.render_keyframe(self.valid_image_path, None)
        self.assertIsNotNone(result_img_none)

        # Options is empty dict
        result_img_empty = self.compositor.render_keyframe(self.valid_image_path, {})
        self.assertIsNotNone(result_img_empty)

    def test_undo_snapshot_success(self):
        """Undo snapshot functionality within the 5-second window."""
        self.compositor.render_keyframe(self.valid_image_path, {})
        self.assertEqual(len(self.compositor._history), 1)

        # Perform undo
        undone_state = self.compositor.undo()
        self.assertIsNotNone(undone_state)
        self.assertEqual(undone_state.size, (1080, 1920))

        # History should be empty after undoing the only item
        self.assertEqual(len(self.compositor._history), 0)

    def test_undo_snapshot_expired_and_empty(self):
        """Undo attempt when the snapshot has expired (>5 seconds) or when there is no history."""
        # 1. Empty history
        self.assertIsNone(self.compositor.undo())

        # 2. Expired snapshot
        self.compositor._undo_window_seconds = 0.1 # short window
        self.compositor.render_keyframe(self.valid_image_path, {})

        # Wait for expiration
        time.sleep(0.2)
        self.assertIsNone(self.compositor.undo())
