def _clean_string(value, default):
    if not isinstance(value, str):
        return default
    cleaned = value.strip().lower()
    if not cleaned:
        return default
    return cleaned

def _clean_choice(value, choices, default):
    cleaned = _clean_string(value, default)
    if cleaned not in choices:
        return default
    return cleaned

def compile_camera_prompt(
    subject=None,
    motion_type=None,
    direction=None,
    speed=None,
    shot_type=None,
    lens=None,
    lighting=None,
    engine=None
):
    """
    Compiles a structured cinematic camera prompt for Google Veo 3 or Sora 2.
    Implements pure function architecture with zero-configuration auto-fallback and silent data cleansing.
    """

    # Default values and constraints
    DEFAULT_SUBJECT = "a stunning cinematic scene"
    DEFAULT_LENS = "35mm"
    DEFAULT_LIGHTING = "cinematic lighting"

    VALID_ENGINES = {"veo3", "sora2"}
    VALID_MOTIONS = {"pan", "tilt", "dolly", "truck", "pedestal", "roll", "zoom", "static", "tracking", "crane", "aerial"}
    VALID_DIRECTIONS = {"forward", "backward", "left", "right", "up", "down", "clockwise", "counter_clockwise", "none"}
    VALID_SPEEDS = {"very_slow", "slow", "medium", "fast", "very_fast"}
    VALID_SHOTS = {"extreme_close_up", "close_up", "medium_shot", "wide_shot", "extreme_wide_shot", "point_of_view", "over_the_shoulder"}

    # Silent Data Cleansing and Auto-Fallback
    c_subject = _clean_string(subject, DEFAULT_SUBJECT)
    c_motion = _clean_choice(motion_type, VALID_MOTIONS, "static")
    c_direction = _clean_choice(direction, VALID_DIRECTIONS, "none")
    c_speed = _clean_choice(speed, VALID_SPEEDS, "medium")
    c_shot = _clean_choice(shot_type, VALID_SHOTS, "wide_shot")
    c_lens = _clean_string(lens, DEFAULT_LENS)
    c_lighting = _clean_string(lighting, DEFAULT_LIGHTING)
    c_engine = _clean_choice(engine, VALID_ENGINES, "veo3")

    # Structural Prompt Assembly based on Engine
    prompt = f"{c_shot.replace('_', ' ').title()}, {c_subject}, "

    if c_motion != "static":
        prompt += f"Camera Motion: {c_motion.title()}"
        if c_direction != "none":
            prompt += f" {c_direction.replace('_', ' ').title()}"
        prompt += f" at {c_speed.replace('_', ' ').title()} speed, "
    else:
        prompt += "Static Camera, "

    prompt += f"Lens: {c_lens.title()}, Lighting: {c_lighting.title()}."

    if c_engine == "veo3":
        # Veo 3 specific formatting
        prompt = f"[Veo 3 Optimized] {prompt} Ultra-realistic, 8k resolution, highly detailed."
    elif c_engine == "sora2":
        # Sora 2 specific formatting
        prompt = f"(Sora 2 Cinematic) {prompt} Photorealistic, smooth temporal consistency, 4k."

    return prompt
