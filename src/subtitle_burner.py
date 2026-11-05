import re
import os
from typing import List, Tuple

HIGHLIGHT_KEYWORDS = [
    "震惊", "系统", "魔帝", "爆发", "无敌", "逆天", "神级", "重生", "觉醒", "打脸", "反转"
]

def split_sentences(text: str) -> List[str]:
    """
    Split subtitles into short sentences based on punctuation, retaining the punctuation.
    """
    if not text:
        return []
    # Use regular expression to split by Chinese and English punctuations
    pattern = r'([^。！？，,!.?]+[。！？，,!.?]*)'
    sentences = re.findall(pattern, text)
    # Filter out empty strings and strip whitespaces
    return [s.strip() for s in sentences if s.strip()]

def format_timestamp_ass(seconds: float) -> str:
    """Format seconds to ASS timestamp (H:MM:SS.cs)"""
    total_cs = int(round(seconds * 100))
    hours = total_cs // 360000
    total_cs %= 360000
    minutes = total_cs // 6000
    total_cs %= 6000
    secs = total_cs // 100
    cs = total_cs % 100
    # ASS format: 0:00:00.00
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

def format_timestamp_srt(seconds: float) -> str:
    """Format seconds to SRT timestamp (HH:MM:SS,mmm)"""
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    total_ms %= 3600000
    minutes = total_ms // 60000
    total_ms %= 60000
    secs = total_ms // 1000
    ms = total_ms % 1000
    # SRT format: 00:00:00,000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

def generate_ass(text: str, duration_sec: float) -> str:
    """
    Generate ASS subtitle format.
    Distribute short sentences evenly by duration.
    Apply ASS tags to highlight keywords.
    """
    sentences = split_sentences(text)
    if not sentences:
        return ""

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

    events = []
    time_per_sentence = duration_sec / len(sentences)
    current_time = 0.0

    for sentence in sentences:
        start_time = current_time
        end_time = current_time + time_per_sentence
        current_time = end_time

        # Highlight keywords
        highlighted_sentence = sentence
        for keyword in HIGHLIGHT_KEYWORDS:
            # ASS tag: {\c&H0000FF&\fscx120\fscy120}keyword{\r}
            # Note: &H0000FF& is red in BGR
            highlighted_sentence = highlighted_sentence.replace(
                keyword,
                f"{{\\c&H0000FF&\\fscx120\\fscy120}}{keyword}{{\\r}}"
            )

        event = f"Dialogue: 0,{format_timestamp_ass(start_time)},{format_timestamp_ass(end_time)},Default,,0,0,0,,{highlighted_sentence}"
        events.append(event)

    return ass_header + "\n".join(events) + "\n"


def generate_srt(text: str, duration_sec: float) -> str:
    """
    Generate SRT subtitle format.
    Distribute short sentences evenly by duration.
    Use HTML tags to highlight keywords.
    """
    sentences = split_sentences(text)
    if not sentences:
        return ""

    srt_content = []
    time_per_sentence = duration_sec / len(sentences)
    current_time = 0.0

    for i, sentence in enumerate(sentences):
        start_time = current_time
        end_time = current_time + time_per_sentence
        current_time = end_time

        # Highlight keywords
        highlighted_sentence = sentence
        for keyword in HIGHLIGHT_KEYWORDS:
            highlighted_sentence = highlighted_sentence.replace(
                keyword,
                f"<font color=\"#FF0000\"><b>{keyword}</b></font>"
            )

        srt_block = f"{i+1}\n{format_timestamp_srt(start_time)} --> {format_timestamp_srt(end_time)}\n{highlighted_sentence}\n"
        srt_content.append(srt_block)

    return "\n".join(srt_content)


def burn_subtitles(text: str, duration_sec: float, output_path: str, fmt: str = 'ass') -> str:
    """
    Entry-point function for easy integration.
    Generates ASS or SRT subtitle files based on format.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if fmt.lower() == 'ass':
        content = generate_ass(text, duration_sec)
    elif fmt.lower() == 'srt':
        content = generate_srt(text, duration_sec)
    else:
        raise ValueError("Unsupported format. Choose 'ass' or 'srt'.")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_path
