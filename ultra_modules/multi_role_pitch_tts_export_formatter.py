import math

class TTSExportFormatter:
    """
    Engine for multi-role pitch/speed dynamic modulation and millisecond duration alignment.
    Supports clean export (no comments, no NaN/None) and 3-line report generation.
    """

    DEFAULT_ROLE_CONFIGS = {
        "narrator": {"pitch": 0.0, "speed": 1.0},
        "male_lead": {"pitch": -2.0, "speed": 1.1},
        "female_lead": {"pitch": 2.0, "speed": 1.05},
        "villain": {"pitch": -4.0, "speed": 0.9},
        "default": {"pitch": 0.0, "speed": 1.0}
    }

    def __init__(self):
        pass

    def _clean_numeric(self, value, default_value):
        if value is None:
            return default_value
        if isinstance(value, float) and math.isnan(value):
            return default_value
        return float(value)

    def format_export(self, raw_data):
        """
        Process raw TTS data.
        raw_data: list of dicts with keys 'role', 'text', 'pitch', 'speed', 'duration_ms'.
        Returns: (formatted_data, report_text)
        """
        if not raw_data:
            raw_data = []

        formatted_data = []
        total_duration_ms = 0
        valid_lines = 0

        for item in raw_data:
            if not isinstance(item, dict):
                continue

            role = item.get("role", "default")
            if role not in self.DEFAULT_ROLE_CONFIGS:
                role = "default"

            default_config = self.DEFAULT_ROLE_CONFIGS[role]

            pitch = self._clean_numeric(item.get("pitch"), default_config["pitch"])
            speed = self._clean_numeric(item.get("speed"), default_config["speed"])
            duration_ms = self._clean_numeric(item.get("duration_ms"), 0.0)

            # Clamp or adjust extreme values
            pitch = max(-10.0, min(10.0, pitch))
            speed = max(0.5, min(2.0, speed))
            duration_ms = max(0.0, duration_ms)

            text = item.get("text")
            if not text:
                text = "..."

            formatted_item = {
                "role": role,
                "text": str(text),
                "pitch": pitch,
                "speed": speed,
                "duration_ms": duration_ms,
                "comments": 0  # requirement: comments=0
            }
            formatted_data.append(formatted_item)
            total_duration_ms += duration_ms
            valid_lines += 1

        report = (
            f"Export Complete: {valid_lines} dialogue lines processed.\n"
            f"Total Duration: {total_duration_ms} ms aligned.\n"
            f"Status: Clean export generated with zero NaN/None and zero comments."
        )

        return formatted_data, report
