import math
import re
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

class AuditLogger:
    def __init__(self) -> None:
        self.logs: List[Dict[str, Any]] = []

    def log(self, action: str, details: str, context: Optional[Dict[str, Any]] = None) -> None:
        self.logs.append({
            "action": action,
            "details": details,
            "context": context or {}
        })

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.logs


class KeyframeCompositor:
    def __init__(self, config: Any) -> None:
        self.audit_logger = AuditLogger()
        self.config = self._sanitize_config(config)

    def _sanitize_config(self, config: Any) -> Dict[str, Any]:
        if not isinstance(config, dict):
            self.audit_logger.log(
                "fallback",
                "Config is not a dict, using empty dict",
                {"input_type": type(config).__name__}
            )
            config_dict: Dict[str, Any] = {}
        else:
            config_dict = dict(config)

        sanitized_config: Dict[str, Any] = {}

        # Sanitize dimensions
        width = config_dict.get("width")
        height = config_dict.get("height")

        def sanitize_dimension(val: Any, default: int, name: str) -> int:
            if val is None:
                self.audit_logger.log("fallback", f"Missing {name}, defaulting to {default}")
                return default
            try:
                val_int = int(val)
                if val_int <= 0:
                    self.audit_logger.log("sanitization", f"Negative or zero {name} ({val_int}), defaulting to {default}")
                    return default
                return val_int
            except (ValueError, TypeError):
                self.audit_logger.log("sanitization", f"Invalid {name} type or value, defaulting to {default}")
                return default

        sanitized_config["width"] = sanitize_dimension(width, 1080, "width")
        sanitized_config["height"] = sanitize_dimension(height, 1920, "height")

        # Sanitize speed lines count
        speed_lines = config_dict.get("speed_lines", 0)
        try:
            speed_lines_int = int(speed_lines)
            if speed_lines_int < 0:
                self.audit_logger.log("sanitization", f"Negative speed_lines ({speed_lines_int}), setting to 0")
                speed_lines_int = 0
            elif speed_lines_int > 500:
                self.audit_logger.log("sanitization", f"Excessive speed_lines ({speed_lines_int}), capping at 500")
                speed_lines_int = 500
            sanitized_config["speed_lines"] = speed_lines_int
        except (ValueError, TypeError):
            self.audit_logger.log("sanitization", "Invalid speed_lines type or value, setting to 0")
            sanitized_config["speed_lines"] = 0

        # Sanitize text
        text = config_dict.get("text", "")
        if not isinstance(text, str):
            self.audit_logger.log("sanitization", "Text is not a string, coercing to string")
            text_str = str(text) if text is not None else ""
        else:
            text_str = text

        # Deduplicate excessively repeated text
        original_text = text_str
        text_str = re.sub(r'(.)\1{5,}', r'\1\1\1\1\1', text_str)
        if text_str != original_text:
            self.audit_logger.log("sanitization", "Deduplicated excessively repeated characters in text")
        sanitized_config["text"] = text_str

        # Sanitize light effect
        light_effect = config_dict.get("light_effect", False)
        if not isinstance(light_effect, bool):
            self.audit_logger.log("sanitization", "light_effect is not a boolean, coercing to bool")
            light_effect = bool(light_effect)
        sanitized_config["light_effect"] = light_effect

        return sanitized_config

    def render(self, base_image: Any = None) -> Image.Image:
        width = self.config["width"]
        height = self.config["height"]

        if base_image is None:
            self.audit_logger.log("fallback", "No base image provided, generating blank canvas")
            img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        elif not isinstance(base_image, Image.Image):
            self.audit_logger.log("fallback", "Invalid base image type, generating blank canvas")
            img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        else:
            if base_image.size != (width, height):
                self.audit_logger.log("sanitization", f"Resizing base image from {base_image.size} to {(width, height)}")
                img = base_image.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")
            else:
                img = base_image.copy().convert("RGBA")

        # Apply light effects
        if self.config["light_effect"]:
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 50))
            img = Image.alpha_composite(img, overlay)
            self.audit_logger.log("effect", "Applied light effect")

        # Apply speed lines
        speed_lines = self.config["speed_lines"]
        if speed_lines > 0:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            center_x, center_y = width // 2, height // 2
            radius = math.hypot(width, height)

            for i in range(speed_lines):
                angle = (2 * math.pi * i) / speed_lines
                end_x = center_x + radius * math.cos(angle)
                end_y = center_y + radius * math.sin(angle)
                if i % 2 == 0:
                    draw.line([(center_x, center_y), (end_x, end_y)], fill=(255, 255, 255, 100), width=2)

            img = Image.alpha_composite(img, overlay)
            self.audit_logger.log("effect", f"Applied {speed_lines} speed lines")

        # Apply text with double stroke
        text = self.config["text"]
        if text:
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (width - text_w) // 2
            y = height - text_h - 100

            # Outer stroke
            for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
                draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))

            # Inner stroke
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]:
                draw.text((x + dx, y + dy), text, font=font, fill=(255, 0, 0, 255))

            # Main text
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
            self.audit_logger.log("effect", "Applied double-stroke subtitle")

        return img

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        return self.audit_logger.get_logs()
