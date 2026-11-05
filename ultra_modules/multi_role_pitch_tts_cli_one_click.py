import json
import csv
import io

class MultiRolePitchTTSEngine:
    def __init__(self):
        # Default config per role for fallback
        self.role_defaults = {
            "narrator": {"pitch": 1.0, "speed": 1.0, "emotion": "neutral"},
            "male_lead": {"pitch": 0.8, "speed": 1.1, "emotion": "confident"},
            "female_lead": {"pitch": 1.2, "speed": 1.05, "emotion": "gentle"},
            "villain": {"pitch": 0.6, "speed": 0.9, "emotion": "sinister"},
            "unknown": {"pitch": 1.0, "speed": 1.0, "emotion": "neutral"}
        }
        self.base_ms_per_char = 200  # Base duration 200ms per character

    def heal_dirty_data(self, item):
        """Auto-heal dirty data with default fallbacks"""
        if not isinstance(item, dict):
            item = {"text": str(item) if item else ""}

        # Sanitize role
        role = item.get("role", "narrator")
        if not isinstance(role, str) or not str(role).strip():
            role = "unknown"
        elif not role.strip():
            role = "narrator"
        role = str(role).strip().lower()
        if role not in self.role_defaults:
            role = "unknown"

        # Sanitize text
        text = item.get("text", "")
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        text = text.strip()
        if not text:
            text = "..." # Default fallback text

        defaults = self.role_defaults.get(role, self.role_defaults["unknown"])

        # Sanitize pitch, speed, emotion
        try:
            pitch = float(item.get("pitch", defaults["pitch"]))
        except (ValueError, TypeError):
            pitch = defaults["pitch"]

        try:
            speed = float(item.get("speed", defaults["speed"]))
            if speed <= 0:
                speed = defaults["speed"]
        except (ValueError, TypeError):
            speed = defaults["speed"]

        emotion = item.get("emotion", defaults["emotion"])
        if not isinstance(emotion, str) or not emotion.strip():
            emotion = defaults["emotion"]

        return {
            "role": role,
            "text": text,
            "pitch": pitch,
            "speed": speed,
            "emotion": emotion
        }

    def process_and_align(self, script_data):
        """Process scripts and return aligned segments with millisecond precision"""
        if not isinstance(script_data, list):
            # Try to auto-heal single object to list
            if script_data:
                script_data = [script_data]
            else:
                script_data = [{"role": "narrator", "text": "Default story begins..."}]

        if not script_data:
            script_data = [{"role": "narrator", "text": "Default story begins..."}]

        results = []
        current_time_ms = 0

        for item in script_data:
            healed = self.heal_dirty_data(item)

            # Calculate duration: base * char_count / speed
            char_count = len(healed["text"])
            duration_ms = int((char_count * self.base_ms_per_char) / healed["speed"])

            # Ensure minimum duration
            if duration_ms < 500:
                duration_ms = 500

            start_ms = current_time_ms
            end_ms = current_time_ms + duration_ms

            result_item = {
                "role": healed["role"],
                "text": healed["text"],
                "pitch": healed["pitch"],
                "speed": healed["speed"],
                "emotion": healed["emotion"],
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": duration_ms
            }
            results.append(result_item)
            current_time_ms = end_ms

        return results

    def format_output(self, results, output_format="json"):
        """Export to JSON or CSV (Excel) seamlessly"""
        output_format = output_format.strip().lower() if isinstance(output_format, str) else "json"
        if output_format not in ["json", "excel", "csv"]:
            output_format = "json"

        if output_format == "json":
            return json.dumps(results, ensure_ascii=False, indent=2)
        else:
            # Excel/CSV adapter
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Role", "Text", "Pitch", "Speed", "Emotion", "Start(ms)", "End(ms)", "Duration(ms)"])
            for r in results:
                writer.writerow([r["role"], r["text"], r["pitch"], r["speed"], r["emotion"], r["start_ms"], r["end_ms"], r["duration_ms"]])
            return output.getvalue()

def run_cli_one_click(input_data=None, output_format="json"):
    """
    Zero-parameter one-click CLI entry point.
    If no input is provided, uses reasonable defaults.
    """
    engine = MultiRolePitchTTSEngine()

    # Sensible defaults for zero-param invocation
    if input_data is None:
        input_data = [
            {"role": "narrator", "text": "In a world of magic..."},
            {"role": "male_lead", "text": "I will conquer the heavens!", "speed": "fast"}, # dirty data: string speed
            {"role": "villain", "text": "", "pitch": None}, # dirty data: empty text and none pitch
            {"role": "unknown_role", "text": "Who am I?"} # fallback role
        ]

    results = engine.process_and_align(input_data)
    formatted = engine.format_output(results, output_format)
    return formatted

if __name__ == "__main__":
    # If run as a script, default to zero-param execution and print JSON
    print("Running in JSON mode (Default):")
    print(run_cli_one_click())
    print("\\nRunning in Excel/CSV mode:")
    print(run_cli_one_click(output_format="excel"))
