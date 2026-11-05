import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class VerticalKeyframeCompositorCoreEngine:
    """
    Core engine for rendering 1080x1920 vertical keyframe light effects,
    speed lines, and double-stroke subtitles.
    Implements pure functions and zero-config automatic fault tolerance.
    """

    @staticmethod
    def _clean_image_input(image, default_size=(1080, 1920)):
        """Silent cleaning for image input."""
        if image is None or not isinstance(image, Image.Image):
            # Fallback to a blank image
            return Image.new("RGBA", default_size, (0, 0, 0, 255))
        if image.size != default_size:
            # Force resize
            return image.resize(default_size, Image.Resampling.LANCZOS)
        if image.mode != "RGBA":
            return image.convert("RGBA")
        return image

    @staticmethod
    def _clean_text(text):
        """Silent cleaning for text."""
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        text = text.strip()
        return text if text else "默认字幕"

    @staticmethod
    def _clean_color(color, default=(255, 255, 255, 255)):
        """Silent cleaning for color."""
        if isinstance(color, tuple) and len(color) in (3, 4):
            try:
                cleaned = tuple(max(0, min(255, int(c))) for c in color)
                if len(cleaned) == 3:
                    return cleaned + (255,)
                return cleaned
            except (ValueError, TypeError):
                pass
        elif isinstance(color, str):
            # basic hex support, fallback if invalid
            if color.startswith("#"):
                color = color.lstrip("#")
                try:
                    if len(color) == 6:
                        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4)) + (255,)
                    elif len(color) == 8:
                        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4, 6))
                except ValueError:
                    pass
        return default

    @staticmethod
    def _clean_float(value, default, min_val, max_val):
        """Silent cleaning for float parameters."""
        try:
            val = float(value)
            if math.isnan(val) or math.isinf(val):
                return default
            return max(min_val, min(max_val, val))
        except (ValueError, TypeError):
            return default

    @classmethod
    def apply_light_effect(cls, image, intensity=1.0, color=(255, 255, 255, 100)):
        """
        Apply a light effect to the image.
        """
        image = cls._clean_image_input(image)
        intensity = cls._clean_float(intensity, 1.0, 0.0, 5.0)
        color = cls._clean_color(color, (255, 255, 255, 100))

        width, height = image.size
        center_x, center_y = width // 2, height // 2

        # Create overlay
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        radius = int(min(width, height) * 0.8 * intensity)
        if radius > 0:
            box = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
            draw.ellipse(box, fill=color)
            overlay = overlay.filter(ImageFilter.GaussianBlur(radius=radius * 0.5))

        return Image.alpha_composite(image, overlay)

    @classmethod
    def apply_speed_lines(cls, image, density=0.5, color=(255, 255, 255, 200)):
        """
        Apply manga speed lines radiating from the center.
        """
        image = cls._clean_image_input(image)
        density = cls._clean_float(density, 0.5, 0.0, 1.0)
        color = cls._clean_color(color, (255, 255, 255, 200))

        width, height = image.size
        center_x, center_y = width // 2, height // 2

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        if density > 0:
            num_lines = int(100 * density)
            max_radius = math.hypot(center_x, center_y)

            rng = np.random.default_rng(42) # fixed local seed for reproducibility

            for _ in range(num_lines):
                angle = rng.uniform(0, 2 * math.pi)
                start_radius = rng.uniform(min(width, height) * 0.2, min(width, height) * 0.5)
                end_radius = max_radius

                line_width = rng.integers(1, max(2, int(5 * density)))

                start_x = center_x + start_radius * math.cos(angle)
                start_y = center_y + start_radius * math.sin(angle)
                end_x = center_x + end_radius * math.cos(angle)
                end_y = center_y + end_radius * math.sin(angle)

                draw.line([(start_x, start_y), (end_x, end_y)], fill=color, width=line_width)

        return Image.alpha_composite(image, overlay)

    @classmethod
    def apply_double_stroke_subtitle(cls, image, text="默认字幕", font_size=80,
                                     inner_color=(255, 255, 255, 255),
                                     stroke1_color=(0, 0, 0, 255), stroke1_width=4,
                                     stroke2_color=(255, 0, 0, 255), stroke2_width=8):
        """
        Apply double-stroke subtitles at the bottom of the image.
        """
        image = cls._clean_image_input(image)
        text = cls._clean_text(text)
        font_size = int(cls._clean_float(font_size, 80, 10, 500))

        inner_color = cls._clean_color(inner_color, (255, 255, 255, 255))
        stroke1_color = cls._clean_color(stroke1_color, (0, 0, 0, 255))
        stroke2_color = cls._clean_color(stroke2_color, (255, 0, 0, 255))

        stroke1_width = int(cls._clean_float(stroke1_width, 4, 0, 50))
        stroke2_width = int(cls._clean_float(stroke2_width, 8, 0, 100))

        width, height = image.size
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        # Using textbbox to support newer PIL versions
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # Fallback for very old PIL
            text_width, text_height = draw.textsize(text, font=font)

        x = (width - text_width) // 2
        y = height - text_height - int(height * 0.1)

        # Draw outer stroke (stroke2)
        if stroke2_width > 0:
            for dx in [-stroke2_width, 0, stroke2_width]:
                for dy in [-stroke2_width, 0, stroke2_width]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=stroke2_color)

        # Draw inner stroke (stroke1)
        if stroke1_width > 0:
            for dx in [-stroke1_width, 0, stroke1_width]:
                for dy in [-stroke1_width, 0, stroke1_width]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=stroke1_color)

        # Draw main text
        draw.text((x, y), text, font=font, fill=inner_color)

        return Image.alpha_composite(image, overlay)

    @classmethod
    def compose(cls, image=None, light_params=None, speed_lines_params=None, subtitle_params=None):
        """
        Main pure function entry point.
        """
        image = cls._clean_image_input(image)

        # Apply Light Effect
        light_params = light_params or {}
        image = cls.apply_light_effect(image, **light_params)

        # Apply Speed Lines
        speed_lines_params = speed_lines_params or {}
        image = cls.apply_speed_lines(image, **speed_lines_params)

        # Apply Subtitles
        subtitle_params = subtitle_params or {}
        image = cls.apply_double_stroke_subtitle(image, **subtitle_params)

        return image
