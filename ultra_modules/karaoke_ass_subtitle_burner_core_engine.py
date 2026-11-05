import re

def format_timestamp_ass(seconds: float) -> str:
    """Format seconds to ASS timestamp (H:MM:SS.cs)"""
    try:
        seconds = float(seconds)
        if seconds < 0:
            seconds = 0.0
    except (TypeError, ValueError):
        seconds = 0.0
    total_cs = int(round(seconds * 100))
    hours = total_cs // 360000
    total_cs %= 360000
    minutes = total_cs // 6000
    total_cs %= 6000
    secs = total_cs // 100
    cs = total_cs % 100
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

def clean_text(text) -> str:
    """Silent dirty data cleaning for strings."""
    if not isinstance(text, str):
        if text is None:
            return ""
        return str(text)
    return text.strip()

def generate_karaoke_ass_content(text: str = None, duration_sec: float = None, highlight_keywords: list = None) -> str:
    """
    Generates ASS subtitle content with karaoke effect and keyword highlighting/zooming.
    Implements zero-config auto-fallback and silent dirty-data cleaning.
    """
    text = clean_text(text)
    if not text:
        text = "默认字幕"

    try:
        duration_sec = float(duration_sec)
        if duration_sec <= 0:
            duration_sec = 3.0
    except (TypeError, ValueError):
        duration_sec = 3.0

    if not isinstance(highlight_keywords, list):
        highlight_keywords = ["震惊", "系统", "魔帝", "爆发", "无敌", "逆天", "神级", "重生", "觉醒", "打脸", "反转"]

    # Filter non-string or empty keywords
    highlight_keywords = [clean_text(kw) for kw in highlight_keywords if clean_text(kw)]

    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,PingFang SC,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    pattern = r'([^。！？，,!.?]+[。！？，,!.?]*)'
    sentences = re.findall(pattern, text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        sentences = [text]

    events = []
    time_per_sentence = duration_sec / len(sentences)
    current_time = 0.0

    for sentence in sentences:
        start_time = current_time
        end_time = current_time + time_per_sentence
        current_time = end_time

        chars = list(sentence)
        if not chars:
            continue

        time_per_char_cs = int((time_per_sentence / len(chars)) * 100)
        if time_per_char_cs < 1:
            time_per_char_cs = 1

        karaoke_text = ""
        for c in chars:
            karaoke_text += f"{{\\k{time_per_char_cs}}}{c}"

        for keyword in highlight_keywords:
            k_keyword = ""
            for c in keyword:
                k_keyword += f"{{\\k{time_per_char_cs}}}{c}"

            if k_keyword in karaoke_text:
                replacement = f"{{\\c&H0000FF&\\fscx150\\fscy150\\t(0,200,\\fscx120\\fscy120)}}{k_keyword}{{\\r}}"
                karaoke_text = karaoke_text.replace(k_keyword, replacement)

        event = f"Dialogue: 0,{format_timestamp_ass(start_time)},{format_timestamp_ass(end_time)},Default,,0,0,0,,{karaoke_text}"
        events.append(event)

    return ass_header + "\n".join(events) + "\n"

def get_ffmpeg_burn_command(input_video: str = None, ass_file_path: str = None, output_video: str = None, existing_vf: str = None) -> list:
    """
    Generates the FFmpeg command list for burning ASS subtitles.
    Includes zero-config auto-fallback and appends to existing video filters if provided.
    """
    input_video = clean_text(input_video) or "input.mp4"
    ass_file_path = clean_text(ass_file_path) or "subtitles.ass"
    output_video = clean_text(output_video) or "output.mp4"
    existing_vf = clean_text(existing_vf)

    escaped_ass = ass_file_path.replace("\\", "/").replace("'", r"\'")
    ass_filter = f"ass='{escaped_ass}'"

    vf_arg = f"{existing_vf},{ass_filter}" if existing_vf else ass_filter

    return [
        "ffmpeg",
        "-y",
        "-i", input_video,
        "-vf", vf_arg,
        "-c:a", "copy",
        output_video
    ]
