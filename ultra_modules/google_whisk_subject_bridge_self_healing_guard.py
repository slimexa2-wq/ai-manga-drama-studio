import time
import copy

class WhiskPayloadBuilder:
    """
    Google Labs Whisk Subject/Style/Scene Payload Builder.
    Provides silent self-healing for missing/invalid data and a 5-second one-click undo mechanism.
    """
    def __init__(self):
        self._snapshots = []

    def build_payload(self, subject=None, style=None, scene=None):
        """
        Builds payload with self-healing for missing, invalid, or dirty data.
        Never raises exceptions or shows popups. Uses reasonable defaults.
        """
        # Self-healing logic
        safe_subject = self._sanitize(subject, "default_subject")
        safe_style = self._sanitize(style, "default_style")
        safe_scene = self._sanitize(scene, "default_scene")

        payload = {
            "subject": safe_subject,
            "style": safe_style,
            "scene": safe_scene,
            "timestamp": time.time()
        }

        self._snapshots.append(copy.deepcopy(payload))
        return payload

    def _sanitize(self, value, default_value):
        if value is None:
            return default_value
        try:
            str_val = str(value).strip()
            if not str_val:
                return default_value
            return str_val
        except Exception:
            return default_value

    def undo(self):
        """
        One-click undo to revert the last payload generation.
        Only allows undo if within 5 seconds of creation.
        Returns True if successful, False otherwise.
        """
        if not self._snapshots:
            return False

        latest_snapshot = self._snapshots[-1]
        current_time = time.time()

        if current_time - latest_snapshot["timestamp"] <= 5.0:
            self._snapshots.pop()
            return True

        return False

    def get_snapshot_count(self):
        return len(self._snapshots)
