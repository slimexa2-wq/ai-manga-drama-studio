import copy
import time
import uuid
import re
from typing import Dict, Any, List, Optional

def heal_motion_params(params: Any) -> Dict[str, Any]:
    """Pure function to silently heal dirty inputs and missing parameters."""
    if not isinstance(params, dict):
        params = {}

    healed = {}

    # 1. Action
    action_raw = params.get("action")
    if not isinstance(action_raw, str):
        action_raw = str(action_raw) if action_raw is not None else "static"
    action = action_raw.strip().lower()

    valid_actions = {"push", "pull", "pan", "tilt", "orbit", "static", "tracking", "crane"}
    if action not in valid_actions:
        action = "static"
    healed["action"] = action

    # 2. Speed
    speed_raw = params.get("speed")
    if not isinstance(speed_raw, str):
        speed_raw = str(speed_raw) if speed_raw is not None else "medium"
    speed = speed_raw.strip().lower()

    if speed not in {"slow", "medium", "fast", "cinematic"}:
        speed = "medium"
    healed["speed"] = speed

    # 3. Direction
    direction_raw = params.get("direction")
    if not isinstance(direction_raw, str):
        direction_raw = str(direction_raw) if direction_raw is not None else ""
    direction = direction_raw.strip().lower()

    if action == "pan":
        if direction not in {"left", "right"}:
            direction = "right"
    elif action == "tilt":
        if direction not in {"up", "down"}:
            direction = "up"
    elif action == "orbit":
        if direction in {"cw", "clockwise"}:
            direction = "clockwise"
        elif direction in {"ccw", "counterclockwise"}:
            direction = "counterclockwise"
        else:
            direction = "clockwise"
    elif action == "crane":
        if direction not in {"up", "down"}:
            direction = "up"
    else:
        direction = ""
    healed["direction"] = direction

    # 4. Strength/Intensity
    strength_raw = params.get("strength", 5.0)
    try:
        strength = float(strength_raw)
        if strength < 1.0:
            strength = 1.0
        elif strength > 10.0:
            strength = 10.0
    except (ValueError, TypeError):
        strength = 5.0
    healed["strength"] = strength

    # 5. Target/Focus
    target_raw = params.get("target")
    if not isinstance(target_raw, str):
        target_raw = str(target_raw) if target_raw is not None else "center subject"
    target = target_raw.strip()
    target = re.sub(r'[^\w\s\-,.]', '', target)
    if not target:
        target = "center subject"
    healed["target"] = target

    return healed

def build_veo3_sora2_prompt(params: Dict[str, Any]) -> str:
    """Pure function to build the structured prompt for Veo 3 / Sora 2."""
    action = params["action"]
    speed = params["speed"]
    direction = params["direction"]
    strength = params["strength"]
    target = params["target"]

    direction_clause = f" {direction}" if direction else ""

    if action == "orbit":
        motion_desc = f"orbiting{direction_clause} around {target}"
    elif action == "push":
        motion_desc = f"pushing in towards {target}"
    elif action == "pull":
        motion_desc = f"pulling out away from {target}"
    elif action == "pan":
        motion_desc = f"panning{direction_clause} across {target}"
    elif action == "tilt":
        motion_desc = f"tilting{direction_clause} along {target}"
    elif action == "tracking":
        motion_desc = f"tracking {target} steadily"
    elif action == "crane":
        motion_desc = f"crane shot moving{direction_clause} revealing {target}"
    else:
        motion_desc = f"static shot focusing on {target}"

    prompt = f"Cinematic {speed} camera motion, {motion_desc}, motion intensity {strength:.1f}/10.0, Veo 3 and Sora 2 optimization, ultra-high definition, 8k resolution, masterful cinematography."

    return prompt

class Veo3CameraMotionPrompter:
    def __init__(self):
        self._snapshots: List[Dict[str, Any]] = []
        self.undo_window_seconds = 5.0

    def _create_snapshot(self, raw_input: Any, current_time: float) -> None:
        """Saves a lightweight snapshot of the state."""
        snapshot = {
            "id": str(uuid.uuid4()),
            "timestamp": current_time,
            "raw_input": copy.deepcopy(raw_input)
        }
        self._snapshots.append(snapshot)
        if len(self._snapshots) > 10:
            self._snapshots.pop(0)

    def compile(self, raw_input: Any, current_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Compiles dirty input into a structured Veo 3 / Sora 2 prompt.
        Saves snapshot for 1-click undo.
        """
        if current_time is None:
            current_time = time.time()

        self._create_snapshot(raw_input, current_time)

        healed_params = heal_motion_params(raw_input)
        prompt = build_veo3_sora2_prompt(healed_params)

        return {
            "status": "success",
            "prompt": prompt,
            "healed_params": healed_params
        }

    def undo(self, current_time: Optional[float] = None) -> Optional[Any]:
        """
        1-click undo within a 5-second window.
        Returns the original raw_input of the last action if within the window, else None.
        """
        if not self._snapshots:
            return None

        if current_time is None:
            current_time = time.time()

        last_snapshot = self._snapshots[-1]

        if current_time - last_snapshot["timestamp"] <= self.undo_window_seconds:
            self._snapshots.pop()
            return last_snapshot["raw_input"]

        return None
