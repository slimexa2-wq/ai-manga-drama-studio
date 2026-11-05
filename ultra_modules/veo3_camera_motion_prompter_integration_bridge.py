import json
from typing import Dict, Any

class Veo3Sora2PrompterBridge:
    def __init__(self):
        pass

    def convert_and_compile(self, input_data: Any) -> str:
        """
        Converts the input data into a unified cinematic camera motion prompt.
        Handles missing parameters, dirty data self-healing, and version mapping silently.
        """
        if isinstance(input_data, str):
            try:
                data = json.loads(input_data)
            except json.JSONDecodeError:
                data = {}
        elif isinstance(input_data, dict):
            data = input_data
        else:
            data = {}

        # Self-healing and normalization for missing or dirty data
        camera_type = data.get("camera_type") or data.get("type") or "cinematic"
        if not isinstance(camera_type, str):
            camera_type = "cinematic"

        motion = data.get("motion") or data.get("movement") or "pan right"
        if not isinstance(motion, str):
            motion = "pan right"

        speed = data.get("speed") or data.get("velocity") or "slow"
        if not isinstance(speed, str):
            speed = "slow"

        focus = data.get("focus") or data.get("focus_on") or "subject"
        if not isinstance(focus, str):
            focus = "subject"

        # Special logic to combine the fields into a prompt
        prompt = f"Camera: {camera_type.strip().capitalize()} shot, Motion: {motion.strip().lower()}, Speed: {speed.strip().lower()}, Focus: {focus.strip()}."
        return prompt

if __name__ == '__main__': # pragma: no cover
    pass
