import os
import subprocess
import time
from typing import List, Dict, Any, Optional

def generate_karaoke_ass(subtitles: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates ASS format subtitles with karaoke effect (dynamic zoom and highlighting).
    Implements self-healing for missing/dirty data and default fallbacks.
    """
    if options is None:
        options = {}

    # Default options fallback
    font_name = options.get('font_name', 'Arial')
    font_size = options.get('font_size', 48)
    primary_color = options.get('primary_color', '&H0000FFFF')  # Yellow
    secondary_color = options.get('secondary_color', '&H00FFFFFF') # White
    outline_color = options.get('outline_color', '&H00000000') # Black
    outline_size = options.get('outline_size', 2)
    zoom_effect = options.get('zoom_effect', '{\\t(0,200,\\fscx120\\fscy120)}')

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KaraokeDefault,{font_name},{font_size},{primary_color},{secondary_color},{outline_color},&H00000000,-1,0,0,0,100,100,0,0,1,{outline_size},0,2,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    def format_time(ms: int) -> str:
        ms = max(0, ms) # Prevent negative
        h = ms // 3600000
        m = (ms % 3600000) // 60000
        s = (ms % 60000) // 1000
        cs = (ms % 1000) // 10
        return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"

    for i, sub in enumerate(subtitles):
        # Self-healing missing or null data
        if not isinstance(sub, dict):
            continue

        start_time = sub.get('start', 0)
        end_time = sub.get('end', 0)
        words = sub.get('words', [])

        # Fix types
        try:
            start_time = int(start_time)
            end_time = int(end_time)
        except (ValueError, TypeError):
            start_time = 0
            end_time = 0

        # Boundary checks
        if start_time < 0: start_time = 0
        if end_time <= start_time: end_time = start_time + 1000
        if not isinstance(words, list):
            words = []

        ass_start = format_time(start_time)
        ass_end = format_time(end_time)

        # Build karaoke text
        ass_text = ""
        current_offset = start_time
        for word_info in words:
            if not isinstance(word_info, dict):
                continue
            word = word_info.get('word', '')
            if not word:
                continue

            # Extract duration, default 100ms
            try:
                w_start = int(word_info.get('start', current_offset))
                w_end = int(word_info.get('end', w_start + 100))
            except (ValueError, TypeError):
                w_start = current_offset
                w_end = w_start + 100

            duration_cs = max(0, (w_end - w_start) // 10) # Centiseconds for \k
            # apply zoom effect + karaoke highlight
            ass_text += f"{{\\k{duration_cs}}}{zoom_effect}{word}"
            current_offset = w_end

        # If no words, maybe it's just raw text
        if not ass_text:
            text = sub.get('text', '')
            if isinstance(text, str) and text:
                ass_text = text

        if ass_text:
            events.append(f"Dialogue: 0,{ass_start},{ass_end},KaraokeDefault,,0,0,0,,{ass_text}")

    return header + "\n".join(events)


def burn_subtitles(video_path: str, ass_path: str, output_path: str, timeout: int = 60) -> bool:
    """
    Burns ASS subtitles into a video using FFmpeg.
    """
    if not os.path.exists(video_path) or not os.path.exists(ass_path):
        return False

    # Escape path for FFmpeg filter
    escaped_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"ass='{escaped_ass_path}'",
        "-c:a", "copy",
        output_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False

class SyntheticBenchmarkSuite:
    """
    Constructs extreme boundary test datasets and measures execution performance.
    """
    @staticmethod
    def generate_massive_concurrent_dataset(size: int = 10000) -> List[Dict[str, Any]]:
        dataset = []
        for i in range(size):
            dataset.append({
                "start": i * 10,  # Highly overlapped
                "end": (i * 10) + 5000,
                "words": [
                    {"word": "Test", "start": i * 10, "end": (i * 10) + 2500},
                    {"word": "Data", "start": (i * 10) + 2500, "end": (i * 10) + 5000}
                ]
            })
        return dataset

    @staticmethod
    def generate_cross_year_dataset() -> List[Dict[str, Any]]:
        # Testing max timestamps, inverted, etc.
        return [
            {
                "start": 31536000000, # 1 year in ms
                "end": 31536001000,
                "words": [{"word": "Year", "start": 31536000000, "end": 31536001000}]
            },
            {
                "start": -1000, # Negative
                "end": -500,
                "words": [{"word": "Negative", "start": -1000, "end": -500}]
            },
            {
                "start": 5000, # Inverted
                "end": 2000,
                "words": [{"word": "Inverted", "start": 5000, "end": 2000}]
            }
        ]

    @staticmethod
    def run_benchmark(dataset: List[Dict[str, Any]], iterations: int = 5) -> float:
        """
        Runs the ASS generator on a dataset multiple times and returns the average execution time in ms.
        """
        total_time = 0.0
        for _ in range(iterations):
            start_time = time.perf_counter()
            generate_karaoke_ass(dataset)
            end_time = time.perf_counter()
            total_time += (end_time - start_time)

        return (total_time / iterations) * 1000.0 # Convert to ms
