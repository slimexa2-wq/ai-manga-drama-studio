import math

# Role Presets
ROLE_PRESETS = {
    "narrator": {"pitch": 1.0, "speed": 1.0},
    "male_lead": {"pitch": 0.8, "speed": 1.1},
    "female_lead": {"pitch": 1.2, "speed": 1.0},
    "villain": {"pitch": 0.6, "speed": 0.9}
}
DEFAULT_ROLE = "narrator"

def _is_valid_float(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(value) or math.isinf(value):
            return False
        return True
    return False

def _clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def align_and_modulate(segment: dict = None) -> dict:
    """
    Core engine to align and modulate pitch and speed for TTS generation.
    Provides dirty-data self-healing, zero-config fallbacks, and exact duration alignment.
    """
    if segment is None or not isinstance(segment, dict):
        segment = {}

    # 1. Text sanitization
    text = segment.get("text", "")
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    if not text.strip():
        text = "..." # Default fallback text

    # 2. Role resolution
    role = segment.get("role", DEFAULT_ROLE)
    if not isinstance(role, str) or role not in ROLE_PRESETS:
        role = DEFAULT_ROLE

    preset = ROLE_PRESETS[role]
    base_pitch = preset["pitch"]
    base_speed = preset["speed"]

    # 3. Modifiers (pitch_shift, speed_multiplier) with self-healing
    pitch_shift = segment.get("pitch_shift", 0.0)
    if not _is_valid_float(pitch_shift):
        pitch_shift = 0.0

    speed_multiplier = segment.get("speed_multiplier", 1.0)
    if not _is_valid_float(speed_multiplier) or speed_multiplier <= 0:
        speed_multiplier = 1.0

    final_pitch = base_pitch + pitch_shift
    final_pitch = _clamp(final_pitch, 0.1, 3.0)

    final_speed = base_speed * speed_multiplier
    final_speed = _clamp(final_speed, 0.1, 10.0)

    # 4. Duration alignment
    # We estimate base duration based on text length and some arbitrary heuristic
    # Let's say 1 character takes 200ms at speed 1.0
    base_char_duration_ms = 200.0
    estimated_duration_ms = (len(text) * base_char_duration_ms) / final_speed

    target_duration_ms = segment.get("target_duration_ms")
    if _is_valid_float(target_duration_ms) and target_duration_ms > 0:
        target_duration_ms = float(target_duration_ms)
        # Auto-adjust speed to meet target duration
        required_speed = (len(text) * base_char_duration_ms) / target_duration_ms
        final_speed = _clamp(required_speed, 0.1, 10.0)

        # Recalculate estimated duration after clamping
        estimated_duration_ms = (len(text) * base_char_duration_ms) / final_speed

    return {
        "text": text,
        "role": role,
        "pitch": round(final_pitch, 3),
        "speed": round(final_speed, 3),
        "duration_ms": round(estimated_duration_ms, 3)
    }
