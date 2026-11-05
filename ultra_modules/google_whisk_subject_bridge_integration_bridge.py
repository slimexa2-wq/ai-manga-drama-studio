import time

class WhiskPayloadBuilder:
    """
    Google Labs Whisk Subject/Style/Scene Payload Builder.
    Implements automatic fallback, missing parameter handling, data sanitization,
    and backwards compatibility with legacy schema fields.
    """

    @staticmethod
    def _sanitize(value, default_value):
        if value is None:
            return default_value
        try:
            str_val = str(value).strip()
            if not str_val:
                return default_value
            return str_val
        except Exception:
            return default_value

    @classmethod
    def build(cls, **kwargs):
        """
        Builds payload with self-healing for missing, invalid, or dirty data.
        Maps old/legacy schema fields to the new Whisk fields.
        Never raises exceptions. Uses reasonable defaults.
        """
        # Legacy mapping dictionaries
        subject_keys = ["subject", "character_prompt", "protagonist", "actor"]
        style_keys = ["style", "art_style", "visual_style", "medium"]
        scene_keys = ["scene", "background", "setting", "environment"]

        def find_value(keys, default_val):
            for k in keys:
                if k in kwargs and kwargs[k] is not None:
                    # found a candidate, let's sanitize it and see if it's usable
                    val = cls._sanitize(kwargs[k], "")
                    if val:
                        return val
            return default_val

        # Defaults
        default_subject = "default subject"
        default_style = "default style"
        default_scene = "default scene"

        # Self-healing logic and mapping
        safe_subject = find_value(subject_keys, default_subject)
        safe_style = find_value(style_keys, default_style)
        safe_scene = find_value(scene_keys, default_scene)

        payload = {
            "subject": safe_subject,
            "style": safe_style,
            "scene": safe_scene,
            "timestamp": time.time(),
            "status": "built"
        }

        return payload
