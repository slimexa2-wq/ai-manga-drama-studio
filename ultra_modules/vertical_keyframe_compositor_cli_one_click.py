import argparse
import json
import logging
import os
import random
from dataclasses import dataclass
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Fallback values for 1080x1920
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920

@dataclass
class CompositorConfig:
    input_image_path: str = ""
    output_image_path: str = "output_keyframe.png"
    text: str = "震撼登场！"
    light_intensity: float = 1.0
    speed_lines_count: int = 50

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompositorConfig':
        config = cls()

        # Self-healing for path
        if 'input_image_path' in data and isinstance(data['input_image_path'], str):
            config.input_image_path = data['input_image_path']
        if 'output_image_path' in data and isinstance(data['output_image_path'], str):
            config.output_image_path = data['output_image_path']

        # Self-healing for text
        if 'text' in data:
            if not isinstance(data['text'], str) or not data['text'].strip():
                config.text = "默认字幕"
            else:
                config.text = data['text']

        # Self-healing for light intensity
        if 'light_intensity' in data:
            try:
                val = float(data['light_intensity'])
                config.light_intensity = max(0.0, min(5.0, val)) # Clamped between 0 and 5
            except (ValueError, TypeError):
                config.light_intensity = 1.0

        # Self-healing for speed lines
        if 'speed_lines_count' in data:
            try:
                val = int(data['speed_lines_count'])
                config.speed_lines_count = max(0, min(500, val))
            except (ValueError, TypeError):
                config.speed_lines_count = 50

        return config

def render_light_effect(img: Image.Image, intensity: float, rng: np.random.Generator) -> Image.Image:
    """Adds a dynamic light effect via screen blending pure functions"""
    if intensity <= 0.0:
        return img

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = img.size

    # Generate some random glowing orbs
    num_orbs = int(10 * intensity)
    for _ in range(num_orbs):
        x = rng.integers(0, width)
        y = rng.integers(0, height)
        radius = rng.integers(50, 300)

        # Colors: warm light (yellow-orange-ish)
        r = rng.integers(200, 255)
        g = rng.integers(100, 200)
        b = rng.integers(50, 100)
        a = rng.integers(20, int(100 * min(1.0, intensity)))

        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(r, g, b, a))

    # Blur the overlay heavily to make it soft
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=50))

    return Image.alpha_composite(img.convert("RGBA"), overlay)

def render_speed_lines(img: Image.Image, count: int, rng: np.random.Generator) -> Image.Image:
    """Renders manga speed lines originating from center-ish out"""
    if count <= 0:
        return img

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = img.size
    center_x, center_y = width // 2, height // 2

    max_radius = np.hypot(width, height)

    for _ in range(count):
        angle = rng.uniform(0, 2 * np.pi)
        inner_radius = rng.uniform(min(width, height) * 0.2, min(width, height) * 0.6)

        x1 = center_x + np.cos(angle) * inner_radius
        y1 = center_y + np.sin(angle) * inner_radius

        x2 = center_x + np.cos(angle) * max_radius
        y2 = center_y + np.sin(angle) * max_radius

        thickness = rng.integers(1, 8)
        # White speed lines with varying opacity
        alpha = rng.integers(50, 200)
        draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, alpha), width=thickness)

    return Image.alpha_composite(img.convert("RGBA"), overlay)

def get_chinese_font(size: int) -> ImageFont.FreeTypeFont:
    """Finds a viable Chinese font, or loads default if none available."""
    # Common font paths in Linux / macOS / Windows
    possible_fonts = [
        "simhei.ttf", "simsun.ttc", "simsun.ttf",
        "msyh.ttc", "msyh.ttf",
        "NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/System/Library/Fonts/PingFang.ttc"
    ]
    for p in possible_fonts:
        try:
            return ImageFont.truetype(p, size)
        except IOError:
            continue
    # If no font found, we will still fallback to default, though it may result in tofu boxes
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def render_double_stroke_text(img: Image.Image, text: str) -> Image.Image:
    """Renders double-stroke text for high visibility"""
    if not text:
        return img

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = img.size

    font = get_chinese_font(80)

    # Attempt to use textbbox if available, fallback for older PILLOW
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = draw.textsize(text, font=font)

    x = (width - text_w) // 2
    # Place text near the bottom
    y = height - text_h - 200

    # Outer stroke (Black, wide)
    stroke_width_outer = 6
    for dx in range(-stroke_width_outer, stroke_width_outer + 1):
        for dy in range(-stroke_width_outer, stroke_width_outer + 1):
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))

    # Inner stroke (White, thinner)
    stroke_width_inner = 2
    for dx in range(-stroke_width_inner, stroke_width_inner + 1):
        for dy in range(-stroke_width_inner, stroke_width_inner + 1):
            draw.text((x + dx, y + dy), text, font=font, fill=(255, 255, 255, 255))

    # Core text (Bright Yellow/Gold)
    draw.text((x, y), text, font=font, fill=(255, 223, 0, 255))

    return Image.alpha_composite(img.convert("RGBA"), overlay)

def process_keyframe(config: CompositorConfig, seed: Optional[int] = None) -> bool:
    """
    Main pipeline for processing the keyframe. Returns True if successful.
    If input_image_path is invalid/missing, auto-generates a placeholder background.
    """
    rng = np.random.default_rng(seed)

    # 1. Load or Generate Base Image
    try:
        if config.input_image_path and os.path.exists(config.input_image_path):
            img = Image.open(config.input_image_path).convert("RGBA")
        else:
            logger.warning("Input image not found or not specified. Generating 1080x1920 placeholder.")
            img = Image.new("RGBA", (DEFAULT_WIDTH, DEFAULT_HEIGHT), (40, 40, 60, 255))
    except Exception as e:
        logger.warning(f"Error loading image {config.input_image_path}: {e}. Generating placeholder.")
        img = Image.new("RGBA", (DEFAULT_WIDTH, DEFAULT_HEIGHT), (40, 40, 60, 255))

    # Resize to vertical 1080x1920 if it isn't
    if img.size != (DEFAULT_WIDTH, DEFAULT_HEIGHT):
        img = img.resize((DEFAULT_WIDTH, DEFAULT_HEIGHT), Image.Resampling.LANCZOS)

    # 2. Add Effects
    img = render_light_effect(img, config.light_intensity, rng)
    img = render_speed_lines(img, config.speed_lines_count, rng)
    img = render_double_stroke_text(img, config.text)

    # 3. Save Output
    try:
        # Save as RGB to support PNG without alpha or JPEG
        out_img = img.convert("RGB")
        out_dir = os.path.dirname(config.output_image_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        out_img.save(config.output_image_path)
        logger.info(f"Successfully saved composited keyframe to {config.output_image_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save output image: {e}")
        return False

def run_cli():
    parser = argparse.ArgumentParser(description="一键国漫竖屏关键帧合成器 (One-Click Vertical Keyframe Compositor)")
    parser.add_argument("--config", "-c", type=str, help="Optional JSON config file path")
    parser.add_argument("--input", "-i", type=str, help="Input image path (optional)")
    parser.add_argument("--output", "-o", type=str, help="Output image path (optional)")
    parser.add_argument("--text", "-t", type=str, help="Subtitle text (optional)")

    args = parser.parse_args()

    # Base params
    params = {}

    # 1. Load from Config File (if exists)
    if args.config:
        if os.path.exists(args.config):
            try:
                if args.config.endswith('.xlsx') or args.config.endswith('.xls'):
                    df = pd.read_excel(args.config)
                    # Use the first row as the config parameters
                    if not df.empty:
                        params = df.iloc[0].to_dict()
                else:
                    with open(args.config, 'r', encoding='utf-8') as f:
                        params = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to parse config file {args.config}, using defaults. Error: {e}")
        else:
            logger.warning(f"Config file {args.config} not found, using defaults.")

    # 2. Overwrite with CLI Args
    if args.input: params['input_image_path'] = args.input
    if args.output: params['output_image_path'] = args.output
    if args.text: params['text'] = args.text

    # 3. Process
    config = CompositorConfig.from_dict(params)
    process_keyframe(config)

if __name__ == "__main__":
    run_cli()
