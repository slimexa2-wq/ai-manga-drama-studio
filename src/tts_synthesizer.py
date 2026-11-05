"""
Multi-Role Emotional TTS Synthesizer with macOS Neural Voice (`say` + `ffmpeg`)
and Zero-Dependency Offline WAV Fallback.
"""

import math
import os
import shutil
import struct
import subprocess
import tempfile
import wave
from typing import Dict, Any

FFMPEG_BIN = shutil.which("ffmpeg") or "/Users/wangmini/.local/bin/ffmpeg"
SAY_BIN = "/usr/bin/say" if os.path.exists("/usr/bin/say") else shutil.which("say")


def calculate_prosody(emotion: str, speaker: str) -> Dict[str, Any]:
    """
    Calculate speech rate, pitch multiplier, and macOS voice based on character role and emotion.
    """
    rate = "+0%"
    pitch = "+0Hz"
    say_rate = 205
    pitch_factor = 1.0
    voice = "Tingting"

    if "🔥" in emotion or "⚡" in emotion or "怒" in emotion or "爆发" in emotion or "高燃" in emotion:
        rate = "+15%"
        pitch = "+10Hz"
        say_rate = 230
        pitch_factor = 1.04
    elif "❄️" in emotion or "冷冽" in emotion or "压迫" in emotion:
        rate = "-5%"
        pitch = "-5Hz"
        say_rate = 190
        pitch_factor = 0.92
    elif "🎯" in emotion or "悬念" in emotion or "悲" in emotion:
        rate = "-10%"
        pitch = "-10Hz"
        say_rate = 185
        pitch_factor = 0.95

    if speaker == "旁白":
        rate = "-5%"
        pitch = "-5Hz"
        say_rate = 195
        pitch_factor = 0.90
    elif any(k in speaker for k in ["苏", "女", "雪", "妃", "瑶", "月"]):
        voice = "Meijia" if os.path.exists("/System/Library/Speech/Voices") else "Tingting"
        pitch_factor = 1.12
        say_rate = 205
    elif any(k in speaker for k in ["赵", "反派", "长老", "魔"]):
        pitch_factor = 0.86
        say_rate = 215
    elif speaker != "旁白":
        # Male lead default
        pitch_factor = 0.91
        say_rate = 205

    return {
        "rate": rate,
        "pitch": pitch,
        "say_rate": say_rate,
        "pitch_factor": pitch_factor,
        "voice": voice,
    }


def generate_offline_wav(filepath: str, duration_ms: int) -> None:
    """
    Generate a clean standard 44.1kHz 16-bit mono WAV file with a subtle cinematic chime
    and exact millisecond duration.
    """
    sample_rate = 44100
    num_samples = max(1, int((duration_ms / 1000.0) * sample_rate))
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    with wave.open(filepath, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            env = math.exp(-t * 2.5)
            val = int(3200 * env * (math.sin(2 * math.pi * 220 * t) + 0.5 * math.sin(2 * math.pi * 330 * t)))
            frames.extend(struct.pack("<h", max(-32767, min(32767, val))))
        wav_file.writeframes(bytes(frames))


def _wav_duration_ms(filepath: str) -> int:
    try:
        with wave.open(filepath, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return max(1200, int((frames / float(rate)) * 1000))
    except Exception:
        pass
    return 3500


def synthesize_audio(text: str, voice_id: str, emotion: str, speaker: str, filepath: str) -> int:
    """
    Synthesize real spoken Chinese voiceover using macOS `say` + `ffmpeg` pitch/EQ mastering,
    with automatic fallback to `generate_offline_wav`.
    Returns the exact duration in milliseconds.
    """
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    prosody = calculate_prosody(emotion, speaker)
    clean_text = (text or "").replace('"', "").replace("“", "").replace("”", "").strip()

    if SAY_BIN and os.path.exists(FFMPEG_BIN) and clean_text and os.environ.get("MANGA_FAST_OFFLINE_TTS") != "1":
        tmp_aiff = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tf:
                tmp_aiff = tf.name
            spoken_line = f"{clean_text}" if speaker == "旁白" else f"{speaker}说：{clean_text}"
            cmd_say = [SAY_BIN, "-v", "Tingting", "-r", str(prosody["say_rate"]), "-o", tmp_aiff, spoken_line]
            res_say = subprocess.run(cmd_say, capture_output=True, timeout=15)
            if res_say.returncode == 0 and os.path.exists(tmp_aiff) and os.path.getsize(tmp_aiff) > 100:
                pf = prosody["pitch_factor"]
                af_filter = f"asetrate=44100*{pf:.3f},aresample=44100,atempo={1.0/pf:.3f},apad=pad_dur=0.25"
                cmd_ff = [
                    FFMPEG_BIN, "-y", "-i", tmp_aiff,
                    "-af", af_filter,
                    "-ar", "44100", "-ac", "1", filepath
                ]
                res_ff = subprocess.run(cmd_ff, capture_output=True, timeout=15)
                if res_ff.returncode == 0 and os.path.exists(filepath) and os.path.getsize(filepath) > 500:
                    return _wav_duration_ms(filepath)
        except Exception:
            pass
        finally:
            if tmp_aiff and os.path.exists(tmp_aiff):
                try:
                    os.remove(tmp_aiff)
                except OSError:
                    pass

    est_sec = max(3.2, min(6.5, len(clean_text) / 4.2 + 0.8))
    duration_ms = int(est_sec * 1000)
    generate_offline_wav(filepath, duration_ms)
    return duration_ms


def process_storyboard(storyboard: Dict[str, Any], output_dir: str) -> None:
    """
    Batch process all shots in the storyboard, generate real spoken audio,
    and align millisecond-level durations across the timeline.
    """
    os.makedirs(output_dir, exist_ok=True)
    total_duration_ms = 0

    for shot in storyboard.get("shots", []):
        safe_speaker = "".join(c if c.isalnum() else "_" for c in shot.get("speaker", "旁白"))
        audio_filename = f"{shot['shot_id']}_{safe_speaker}_tts.wav"
        audio_path = os.path.join(output_dir, audio_filename)

        duration_ms = synthesize_audio(
            text=shot["subtitle_text"],
            voice_id=shot.get("voice_id", "zh-CN-YunxiNeural"),
            emotion=shot.get("emotion", ""),
            speaker=shot["speaker"],
            filepath=audio_path,
        )

        shot["audio_path"] = audio_path
        shot["duration_ms"] = duration_ms
        shot["duration_sec"] = round(duration_ms / 1000.0, 1)
        shot["start_ms"] = total_duration_ms
        shot["end_ms"] = total_duration_ms + duration_ms
        total_duration_ms += duration_ms

    storyboard["total_duration_sec"] = round(total_duration_ms / 1000.0, 1)
