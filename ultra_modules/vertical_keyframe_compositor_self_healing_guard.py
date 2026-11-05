import time
import copy
from typing import Dict, Any, Optional
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    pass # Will be installed later

class VerticalKeyframeCompositorSelfHealingGuard:
    """
    1080x1920 vertical screen manga keyframe light effect rendering,
    speed line synthesis, and dual-stroke large subtitle compositor.
    Features abnormal input silent self-healing and 5-second one-click undo snapshot mechanism.
    """

    def __init__(self):
        self.width = 1080
        self.height = 1920
        self._history = []
        self._undo_window_seconds = 5.0

    def _save_snapshot(self, state_data: Any):
        """Save a snapshot with timestamp."""
        # Deep copy the state data if it's a dictionary or list,
        # but in Pillow context it might be an Image object.
        # We will handle the specific data type in the render method.
        # For now, we store timestamp and data.
        self._history.append({
            'timestamp': time.time(),
            'data': state_data
        })

    def undo(self) -> Optional[Any]:
        """
        One-click undo: returns the previous state if within 5 seconds,
        otherwise silently returns None and does not throw errors.
        """
        try:
            if not self._history:
                return None

            last_snapshot = self._history[-1]
            current_time = time.time()

            if current_time - last_snapshot['timestamp'] <= self._undo_window_seconds:
                self._history.pop() # Remove the undone snapshot
                return last_snapshot['data']
            else:
                # Snapshot expired, silently fail
                return None
        except Exception:
            # Self-healing: catch everything and return None
            return None

    def _render_light_effect(self, base_image, light_intensity: float):
        """Render a subtle light effect gradient or glow."""
        try:
            intensity = float(light_intensity) if light_intensity is not None else 0.5
            intensity = max(0.0, min(1.0, intensity)) # clamp 0-1

            # Create a simple radial gradient or overlay for light effect
            overlay = Image.new('RGBA', base_image.size, (255, 255, 255, int(50 * intensity)))

            # Simple blending
            return Image.alpha_composite(base_image.convert('RGBA'), overlay)
        except Exception:
            return base_image.convert('RGBA')

    def _render_dual_stroke_subtitle(self, base_image, text: str):
        """Render a dual-stroke large subtitle at the bottom."""
        try:
            if not text or not isinstance(text, str):
                return base_image

            overlay = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # For self-healing and testing without external font files, use default font
            font = ImageFont.load_default()

            # In a real app we'd measure text, here we do a simple fallback
            # PIL 10+ handles textbbox, for old versions fallback to textsize
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
            except AttributeError:
                # Fallback for old Pillow
                text_w, text_h = draw.textsize(text, font=font)

            x = (self.width - text_w) // 2
            y = self.height - 200 - text_h

            # Draw dual stroke: outer stroke (black), inner stroke (dark gray), main text (white)
            stroke_width_outer = 4
            stroke_width_inner = 2

            # Outer stroke
            for dx in range(-stroke_width_outer, stroke_width_outer + 1):
                for dy in range(-stroke_width_outer, stroke_width_outer + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))

            # Inner stroke
            for dx in range(-stroke_width_inner, stroke_width_inner + 1):
                for dy in range(-stroke_width_inner, stroke_width_inner + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=(100, 100, 100, 255))

            # Main text
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

            return Image.alpha_composite(base_image.convert('RGBA'), overlay)
        except Exception:
            # Self-healing
            return base_image.convert('RGBA')

    def render_keyframe(self, image_path: str, options: Dict[str, Any] = None) -> Any:
        """
        Main rendering entrypoint.
        Silent self-healing on bad inputs, returns a Pillow Image.
        Saves a snapshot for undo.
        """
        try:
            options = options or {}

            # Try to load image
            try:
                base_image = Image.open(image_path).convert('RGBA')
            except Exception:
                # Self-healing: bad path, create blank canvas
                base_image = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))

            # Resize if needed (naive resize for safety)
            if base_image.size != (self.width, self.height):
                base_image = base_image.resize((self.width, self.height))

            # Save snapshot of the current state BEFORE applying new effects
            # We copy the image so further modifications don't alter the snapshot
            self._save_snapshot(base_image.copy())

            # Apply effects sequentially
            light_intensity = options.get('light_intensity', 0.5)
            speed_lines_intensity = options.get('speed_lines_intensity', 0.3)
            subtitle_text = options.get('subtitle_text', '')

            img = self._render_light_effect(base_image, light_intensity)
            img = self._render_speed_lines(img, speed_lines_intensity)
            img = self._render_dual_stroke_subtitle(img, subtitle_text)

            return img
        except Exception:
            # Absolute self-healing fallback
            try:
                fallback = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))
                self._save_snapshot(fallback.copy())
                return fallback
            except Exception:
                return None

    def _render_speed_lines(self, base_image, intensity: float):
        """Render simple vertical speed lines."""
        try:
            line_intensity = float(intensity) if intensity is not None else 0.3
            line_intensity = max(0.0, min(1.0, line_intensity))

            if line_intensity <= 0:
                return base_image

            overlay = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Draw random vertical lines based on intensity
            import random
            num_lines = int(100 * line_intensity)
            for _ in range(num_lines):
                x = random.randint(0, self.width)
                y_start = random.randint(0, self.height)
                y_end = y_start + random.randint(100, 800)
                width = random.randint(1, 4)
                alpha = random.randint(50, 150)
                draw.line([(x, y_start), (x, y_end)], fill=(255, 255, 255, alpha), width=width)

            return Image.alpha_composite(base_image.convert('RGBA'), overlay)
        except Exception:
            return base_image.convert('RGBA')
