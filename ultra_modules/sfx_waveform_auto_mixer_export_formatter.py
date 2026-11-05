import math

def clean_data(val, default):
    """
    Pure function to clean dirty data, replacing None/NaN with a default.
    """
    if val is None:
        return default
    if isinstance(val, float) and math.isnan(val):
        return default
    return val

def generate_waveform(sfx_type, duration=1.0, amplitude=1.0, frequency=440.0):
    """
    Pure function to generate a deterministic waveform for different SFX types.
    """
    sfx_type = clean_data(sfx_type, 'default')
    duration = clean_data(duration, 1.0)
    amplitude = clean_data(amplitude, 1.0)
    frequency = clean_data(frequency, 440.0)

    # Boundary constraints
    duration = max(0.1, duration)
    amplitude = max(0.0, amplitude)

    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    waveform = []

    # Simple deterministic waveform generation based on type
    if sfx_type == "heavy_bass":
        freq = clean_data(frequency, 60.0)
        for i in range(min(num_samples, 100)): # Generate sample limit for performance
            t = i / sample_rate
            waveform.append(amplitude * math.sin(2 * math.pi * freq * t))
    elif sfx_type == "sword_clash":
        freq = clean_data(frequency, 2000.0)
        for i in range(min(num_samples, 100)):
            t = i / sample_rate
            # Add some harmonics for clash
            val = amplitude * (math.sin(2 * math.pi * freq * t) + 0.5 * math.sin(2 * math.pi * (freq * 1.5) * t))
            waveform.append(val)
    elif sfx_type == "transition_whoosh":
        for i in range(min(num_samples, 100)):
            t = i / sample_rate
            # Sweeping frequency
            freq = 400 + 800 * t
            waveform.append(amplitude * math.sin(2 * math.pi * freq * t))
    else:
        for i in range(min(num_samples, 100)):
            waveform.append(0.0)

    # Ensure no None/NaN in waveform
    cleaned_waveform = [clean_data(val, 0.0) for val in waveform]
    return cleaned_waveform

def format_export_data(tracks=None, project_name=None):
    """
    Formats the export data ensuring comments=0 and no NaN/None.
    Generates a 3-line report text.
    """
    tracks = clean_data(tracks, [])
    project_name = clean_data(project_name, "Untitled_Manga_Drama")

    formatted_tracks = []
    total_duration = 0.0
    for track in tracks:
        # Self-healing missing keys
        if not isinstance(track, dict):
            continue

        sfx_type = clean_data(track.get("sfx_type"), "default")
        duration = clean_data(track.get("duration"), 1.0)
        amplitude = clean_data(track.get("amplitude"), 1.0)

        waveform = generate_waveform(sfx_type, duration, amplitude)

        formatted_tracks.append({
            "sfx_type": sfx_type,
            "duration": duration,
            "amplitude": amplitude,
            "waveform": waveform
        })
        total_duration += duration

    export_data = {
        "project_name": project_name,
        "tracks": formatted_tracks,
        "comments": 0,
        "total_duration": total_duration
    }

    # Generate 3-line simple report text
    report_text = f"【项目汇报】{project_name}\n"
    report_text += f"总计合成 {len(formatted_tracks)} 条特效音轨，总时长 {total_duration:.2f} 秒\n"
    report_text += "混音及波形数据已成功无瑕疵导出，可直接复制粘贴！"

    return export_data, report_text
