import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultra_modules.multi_role_pitch_tts_core_engine import align_and_modulate


def bridge_and_modulate(payload: dict = None) -> dict:
    """
    Acts as a bridge and schema converter for multi-role pitch and TTS generation,
    handling cross-system data contract variations and automatic forward-compatibility.

    It maps legacy and alternative field names to the standard fields expected by the core engine:
    - text: 'msg_content', 'content', 'text'
    - role: 'actor_role', 'character', 'role'
    - pitch_shift: 'pitch_modifier', 'pitch_offset', 'pitch_shift'
    - speed_multiplier: 'play_speed', 'speed_rate', 'speed_multiplier'
    - target_duration_ms: 'target_time', 'duration_target', 'target_duration_ms'
    """
    if payload is None or not isinstance(payload, dict):
        payload = {}

    standardized_payload = {}

    # 1. Map Text
    if "text" in payload:
        standardized_payload["text"] = payload["text"]
    elif "msg_content" in payload:
        standardized_payload["text"] = payload["msg_content"]
    elif "content" in payload:
        standardized_payload["text"] = payload["content"]

    # 2. Map Role
    if "role" in payload:
        standardized_payload["role"] = payload["role"]
    elif "actor_role" in payload:
        standardized_payload["role"] = payload["actor_role"]
    elif "character" in payload:
        standardized_payload["role"] = payload["character"]

    # 3. Map Pitch Shift
    if "pitch_shift" in payload:
        standardized_payload["pitch_shift"] = payload["pitch_shift"]
    elif "pitch_modifier" in payload:
        standardized_payload["pitch_shift"] = payload["pitch_modifier"]
    elif "pitch_offset" in payload:
        standardized_payload["pitch_shift"] = payload["pitch_offset"]

    # 4. Map Speed Multiplier
    if "speed_multiplier" in payload:
        standardized_payload["speed_multiplier"] = payload["speed_multiplier"]
    elif "play_speed" in payload:
        standardized_payload["speed_multiplier"] = payload["play_speed"]
    elif "speed_rate" in payload:
        standardized_payload["speed_multiplier"] = payload["speed_rate"]

    # 5. Map Target Duration MS
    if "target_duration_ms" in payload:
        standardized_payload["target_duration_ms"] = payload["target_duration_ms"]
    elif "target_time" in payload:
        standardized_payload["target_duration_ms"] = payload["target_time"]
    elif "duration_target" in payload:
        standardized_payload["target_duration_ms"] = payload["duration_target"]

    return align_and_modulate(standardized_payload)
