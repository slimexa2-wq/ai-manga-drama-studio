import json
import logging

logger = logging.getLogger(__name__)

class GoogleWhiskSubjectBridgePlainExplainer:
    """
    Translates complex Google Labs Whisk Subject/Style/Scene payloads into
    simple, plain text cards for frontend display.

    Design Principle: Prioritize UI/UX efficiency and simplicity; frontend operations
    must be simple and intuitive, regardless of backend complexity.
    Backend components must implement zero-configuration fault tolerance,
    automatically assigning reasonable default values for missing parameters
    and silently cleaning dirty data to ensure zero crash tolerance.
    """

    DEFAULT_SUBJECT_NAME = "Unknown Subject"
    DEFAULT_STYLE = "Standard Style"
    DEFAULT_SCENE = "Default Scene"
    DEFAULT_CONFIDENCE = 0.0

    @classmethod
    def _safe_float(cls, val, default=0.0):
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            val = val.strip()
            if val.endswith('%'):
                val = val[:-1]
                try:
                    return float(val) / 100.0
                except ValueError:
                    return default
            try:
                return float(val)
            except ValueError:
                return default
        return default

    @classmethod
    def _safe_str(cls, val, default=""):
        if val is None:
            return default
        return str(val).strip() or default

    @classmethod
    def _parse_payload(cls, payload):
        """Safely parse payload, even if dirty."""
        if not isinstance(payload, dict):
            # Attempt to parse if string
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                    if not isinstance(payload, dict):
                        payload = {}
                except Exception:
                    payload = {}
            else:
                payload = {}

        # Extract components with fallbacks
        subject = payload.get("subject", {})
        if not isinstance(subject, dict):
            subject = {}
        style = payload.get("style", {})
        if not isinstance(style, dict):
            style = {}
        scene = payload.get("scene", {})
        if not isinstance(scene, dict):
            scene = {}

        return {
            "subject_name": cls._safe_str(subject.get("name"), cls.DEFAULT_SUBJECT_NAME),
            "subject_confidence": cls._safe_float(subject.get("confidence"), cls.DEFAULT_CONFIDENCE),
            "style_name": cls._safe_str(style.get("name"), cls.DEFAULT_STYLE),
            "style_intensity": cls._safe_float(style.get("intensity"), cls.DEFAULT_CONFIDENCE),
            "scene_name": cls._safe_str(scene.get("name"), cls.DEFAULT_SCENE),
            "scene_lighting": cls._safe_str(scene.get("lighting"), "Standard Lighting"),
        }

    @classmethod
    def generate_markdown_card(cls, payload) -> str:
        """Generates a plain-text markdown card."""
        data = cls._parse_payload(payload)
        return (
            f"**Whisk Generation Settings**\n"
            f"- **Subject**: {data['subject_name']} (Confidence: {data['subject_confidence']:.2f})\n"
            f"- **Style**: {data['style_name']} (Intensity: {data['style_intensity']:.2f})\n"
            f"- **Scene**: {data['scene_name']} (Lighting: {data['scene_lighting']})"
        )

    @classmethod
    def generate_html_card(cls, payload) -> str:
        """Generates a plain-text HTML card."""
        data = cls._parse_payload(payload)
        return (
            f"<div class='whisk-card'>\n"
            f"  <h3>Whisk Generation Settings</h3>\n"
            f"  <ul>\n"
            f"    <li><b>Subject</b>: {data['subject_name']} (Confidence: {data['subject_confidence']:.2f})</li>\n"
            f"    <li><b>Style</b>: {data['style_name']} (Intensity: {data['style_intensity']:.2f})</li>\n"
            f"    <li><b>Scene</b>: {data['scene_name']} (Lighting: {data['scene_lighting']})</li>\n"
            f"  </ul>\n"
            f"</div>"
        )

    @classmethod
    def generate_json_card(cls, payload) -> str:
        """Generates a plain-text JSON string of the simple card data."""
        data = cls._parse_payload(payload)
        return json.dumps({
            "title": "Whisk Generation Settings",
            "summary": data
        }, indent=2)

    @classmethod
    def generate_all(cls, payload) -> dict:
        """Generate all formats."""
        return {
            "markdown": cls.generate_markdown_card(payload),
            "html": cls.generate_html_card(payload),
            "json": cls.generate_json_card(payload)
        }
