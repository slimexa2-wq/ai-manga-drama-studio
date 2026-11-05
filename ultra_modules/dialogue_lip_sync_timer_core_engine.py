import math

def calculate_scene_duration(
    text=None,
    audio_duration=None,
    waveform_peaks=None,
    wpm=None,
    punctuation_pause=None,
    min_duration=None,
    padding=None
):
    """
    台词字数、标点停顿与配音音频波形峰值自动对齐分镜时长计算器
    """
    # 1. 脏数据静默清洗与缺参默认兜底
    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    try:
        audio_duration = float(audio_duration)
        if audio_duration < 0 or math.isnan(audio_duration):
            audio_duration = 0.0
    except (TypeError, ValueError):
        audio_duration = 0.0

    clean_peaks = []
    if isinstance(waveform_peaks, (list, tuple)):
        for p in waveform_peaks:
            try:
                val = float(p)
                if val >= 0 and not math.isnan(val):
                    clean_peaks.append(val)
            except (TypeError, ValueError):
                pass

    try:
        wpm = float(wpm)
        if wpm <= 0 or math.isnan(wpm):
            wpm = 250.0
    except (TypeError, ValueError):
        wpm = 250.0

    try:
        punctuation_pause = float(punctuation_pause)
        if punctuation_pause < 0 or math.isnan(punctuation_pause):
            punctuation_pause = 0.5
    except (TypeError, ValueError):
        punctuation_pause = 0.5

    try:
        min_duration = float(min_duration)
        if min_duration < 0 or math.isnan(min_duration):
            min_duration = 1.0
    except (TypeError, ValueError):
        min_duration = 1.0

    try:
        padding = float(padding)
        if padding < 0 or math.isnan(padding):
            padding = 0.5
    except (TypeError, ValueError):
        padding = 0.5

    # 2. 核心计算
    punctuations = set(".,!?;:，。！？；：、\n")
    punct_count = sum(1 for char in text if char in punctuations)

    valid_chars = sum(1 for char in text if char not in punctuations and not char.isspace())

    text_duration = (valid_chars / (wpm / 60.0)) + (punct_count * punctuation_pause)

    peak_duration = max(clean_peaks) if clean_peaks else 0.0

    if audio_duration > 0:
        base_duration = audio_duration
    elif peak_duration > 0:
        base_duration = max(peak_duration, text_duration)
    else:
        base_duration = text_duration

    final_duration = base_duration + padding

    return max(final_duration, min_duration)
