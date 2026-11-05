"""
Vertical Keyframe Compositor Integration Bridge
===============================================
A bridge for mapping old schema to new schema with zero-configuration fallbacks
for 1080x1920 vertical manga keyframe compositor.
"""
from typing import Dict, Any

class VerticalKeyframeCompositorIntegrationBridge:
    """
    Bridge class for vertical manga keyframe compositor schema normalization.
    """

    def __init__(self):
        self.default_width = 1080
        self.default_height = 1920
        self.default_light_effect = "none"
        self.default_speed_lines = False
        self.default_double_layer_stroke = False
        self.default_subtitle = ""

    def bridge_and_normalize(self, input_data: Any) -> Dict[str, Any]:
        """
        Normalize input data, map old fields to new ones, and apply safe defaults.
        """
        if not isinstance(input_data, dict):
            input_data = {}

        normalized = {
            "width": self.default_width,
            "height": self.default_height,
            "light_effect": self.default_light_effect,
            "speed_lines": self.default_speed_lines,
            "double_layer_stroke": self.default_double_layer_stroke,
            "subtitle": self.default_subtitle
        }

        # Mapping width
        if "width" in input_data and isinstance(input_data["width"], int) and input_data["width"] > 0:
            normalized["width"] = input_data["width"]
        elif "w" in input_data and isinstance(input_data["w"], int) and input_data["w"] > 0:
            normalized["width"] = input_data["w"]
        elif "resolution_w" in input_data and isinstance(input_data["resolution_w"], int) and input_data["resolution_w"] > 0:
            normalized["width"] = input_data["resolution_w"]

        # Mapping height
        if "height" in input_data and isinstance(input_data["height"], int) and input_data["height"] > 0:
            normalized["height"] = input_data["height"]
        elif "h" in input_data and isinstance(input_data["h"], int) and input_data["h"] > 0:
            normalized["height"] = input_data["h"]
        elif "resolution_h" in input_data and isinstance(input_data["resolution_h"], int) and input_data["resolution_h"] > 0:
            normalized["height"] = input_data["resolution_h"]

        # Mapping light_effect
        if "light_effect" in input_data and isinstance(input_data["light_effect"], str):
            normalized["light_effect"] = input_data["light_effect"]
        elif "effect_light" in input_data and isinstance(input_data["effect_light"], str):
            normalized["light_effect"] = input_data["effect_light"]

        # Mapping speed_lines
        if "speed_lines" in input_data:
            normalized["speed_lines"] = bool(input_data["speed_lines"])
        elif "lines_speed" in input_data:
            normalized["speed_lines"] = bool(input_data["lines_speed"])
        elif "has_speed_lines" in input_data:
            normalized["speed_lines"] = bool(input_data["has_speed_lines"])

        # Mapping double_layer_stroke
        if "double_layer_stroke" in input_data:
            normalized["double_layer_stroke"] = bool(input_data["double_layer_stroke"])
        elif "stroke_double_layer" in input_data:
            normalized["double_layer_stroke"] = bool(input_data["stroke_double_layer"])
        elif "has_double_stroke" in input_data:
            normalized["double_layer_stroke"] = bool(input_data["has_double_stroke"])

        # Mapping subtitle
        if "subtitle" in input_data and isinstance(input_data["subtitle"], str):
            normalized["subtitle"] = input_data["subtitle"]
        elif "sub" in input_data and isinstance(input_data["sub"], str):
            normalized["subtitle"] = input_data["sub"]
        elif "text_subtitle" in input_data and isinstance(input_data["text_subtitle"], str):
            normalized["subtitle"] = input_data["text_subtitle"]
        elif "subtitle" in input_data or "sub" in input_data or "text_subtitle" in input_data:
             val = input_data.get("subtitle") or input_data.get("sub") or input_data.get("text_subtitle")
             if val is not None:
                normalized["subtitle"] = str(val)

        return normalized
