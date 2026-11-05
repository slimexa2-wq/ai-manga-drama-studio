import re

def build_whisk_payload(subject=None, style=None, scene=None, **kwargs):
    """
    Constructs a 3-slot (Subject, Style, Scene) request payload for Google Whisk.
    Implements automatic fallback, missing parameter handling, and data sanitization.
    """
    def sanitize_input(value, default_value, max_length=1000):
        if value is None:
            return default_value

        # Convert non-strings to strings
        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception:
                value = default_value

        # Trim leading/trailing whitespace
        value = value.strip()

        # Replace multiple spaces with a single space (dirty data self-healing)
        value = re.sub(r'\s+', ' ', value)

        # Fallback if empty after stripping
        if not value:
            return default_value

        # Truncate to max_length for extreme boundaries
        if len(value) > max_length:
            value = value[:max_length].strip()

        return value

    default_subject = "1girl, protagonist"
    default_style = "anime, manga, high quality, masterpiece"
    default_scene = "simple background, plain background"

    clean_subject = sanitize_input(subject, default_subject)
    clean_style = sanitize_input(style, default_style)
    clean_scene = sanitize_input(scene, default_scene)

    payload = {
        "slots": {
            "subject": clean_subject,
            "style": clean_style,
            "scene": clean_scene
        }
    }

    # Optionally merge in any extra kwargs safely
    for k, v in kwargs.items():
        if k not in ["slots"]:
            payload[k] = v

    return payload
