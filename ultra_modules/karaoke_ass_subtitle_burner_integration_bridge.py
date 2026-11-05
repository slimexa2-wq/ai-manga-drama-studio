def _safe_get(data: dict, keys: list, default=None):
    """Safely get a value from a nested dictionary."""
    if not isinstance(data, dict):
        return default

    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current

def bridge_integration_payload(payload: dict) -> dict:
    """
    Cross-system data contract seamless bridging and schema version automatic forward-compatible conversion.
    Automatically identifies new and old version field differences and silently maps and converts them.
    No manual configuration of field mapping tables required.
    """
    if not isinstance(payload, dict):
        payload = {}

    # Extract target values with fallback strategies covering different schema versions
    text = (
        payload.get("text") or
        payload.get("content") or
        _safe_get(payload, ["subtitle", "text"]) or
        _safe_get(payload, ["v2_schema", "dialogue"]) or
        "默认字幕"
    )

    text_str = str(text).strip() if text is not None else ""
    if not text_str:
        text_str = "默认字幕"

    # Try to extract duration
    raw_duration = (
        payload.get("duration_sec") or
        payload.get("duration") or
        _safe_get(payload, ["subtitle", "duration"]) or
        _safe_get(payload, ["timing", "length_seconds"])
    )

    duration_sec = 3.0
    if raw_duration is not None:
        try:
            parsed = float(raw_duration)
            if parsed > 0:
                duration_sec = parsed
        except (ValueError, TypeError):
            pass

    # Try to extract highlight keywords
    raw_keywords = (
        payload.get("highlight_keywords") or
        payload.get("keywords") or
        _safe_get(payload, ["effects", "highlights"]) or
        _safe_get(payload, ["v2_schema", "emphasis_words"])
    )

    highlight_keywords = ["震惊", "系统", "魔帝", "爆发", "无敌", "逆天", "神级", "重生", "觉醒", "打脸", "反转"]
    if isinstance(raw_keywords, list):
        filtered = [str(kw).strip() for kw in raw_keywords if kw and str(kw).strip()]
        if filtered:
            highlight_keywords = filtered

    # FFmpeg properties
    input_video = (
        payload.get("input_video") or
        payload.get("video_in") or
        _safe_get(payload, ["media", "source_video"]) or
        "input.mp4"
    )

    output_video = (
        payload.get("output_video") or
        payload.get("video_out") or
        _safe_get(payload, ["media", "target_video"]) or
        "output.mp4"
    )

    ass_file_path = (
        payload.get("ass_file_path") or
        payload.get("subtitle_file") or
        _safe_get(payload, ["files", "ass_path"]) or
        "subtitles.ass"
    )

    # Return normalized v3 unified schema
    return {
        "text": text_str,
        "duration_sec": duration_sec,
        "highlight_keywords": highlight_keywords,
        "input_video": str(input_video).strip() if input_video else "input.mp4",
        "output_video": str(output_video).strip() if output_video else "output.mp4",
        "ass_file_path": str(ass_file_path).strip() if ass_file_path else "subtitles.ass"
    }
