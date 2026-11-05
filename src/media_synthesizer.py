"""
End-to-End 9:16 Vertical Manga Keyframe Compositor (1080x1920 PNG with Real AI Anime Artwork),
Multi-Role Voiceover + SFX Waveform Mixer (`SFXMixer`), Dynamic Video Clip Synthesizer (MP4),
and Full Episode Compositor (`episode_final.mp4`).
"""

import math
import os
import random
import shutil
import subprocess
from typing import Dict, Any, List, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont
from .sfx_mixer import SFXMixer

FFMPEG_BIN = shutil.which("ffmpeg") or "/Users/wangmini/.local/bin/ffmpeg"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RAW_ART_DIR = os.path.join(REPO_ROOT, "assets", "default_raw_art")

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]

STYLE_PALETTES: Dict[str, Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]] = {
    "xianxia": ((14, 18, 42), (76, 29, 149), (245, 158, 11)),
    "urban_counterattack": ((15, 23, 42), (30, 58, 138), (56, 189, 248)),
    "k_chaebol": ((24, 16, 36), (112, 26, 117), (251, 191, 36)),
    "shonen_battle": ((28, 12, 18), (153, 27, 27), (250, 204, 21)),
    "chinese_horror": ((8, 15, 18), (6, 78, 59), (239, 68, 68)),
    "cyberpunk": ((10, 12, 28), (109, 40, 217), (6, 182, 212)),
    "palace_intrigue": ((32, 16, 20), (136, 19, 55), (252, 211, 77)),
    "cg_3d_donghua": ((12, 20, 38), (29, 78, 216), (168, 85, 247)),
}


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, max_chars_per_line: int = 16) -> List[str]:
    clean = (text or "").strip()
    if not clean:
        return [""]
    lines = []
    while clean:
        lines.append(clean[:max_chars_per_line])
        clean = clean[max_chars_per_line:]
    return lines[:4]


def _find_raw_artwork(shot_id: str, shot_number: int, output_dir: Optional[str] = None) -> Optional[str]:
    candidates = []
    if output_dir:
        raw_dir = os.path.join(output_dir, "raw_art")
        for ext in ("jpg", "png", "jpeg", "webp"):
            candidates.append(os.path.join(raw_dir, f"{shot_id}.{ext}"))
            candidates.append(os.path.join(raw_dir, f"{shot_id}_raw.{ext}"))
    if os.path.isdir(DEFAULT_RAW_ART_DIR):
        cycle_idx = ((max(1, shot_number) - 1) % 4) + 1
        cycle_id = f"SHOT_{cycle_idx:02d}"
        for ext in ("jpg", "png", "jpeg", "webp"):
            candidates.append(os.path.join(DEFAULT_RAW_ART_DIR, f"{shot_id}.{ext}"))
            candidates.append(os.path.join(DEFAULT_RAW_ART_DIR, f"{cycle_id}.{ext}"))
    for c in candidates:
        if os.path.isfile(c) and os.path.getsize(c) > 1000:
            return c
    return None


def render_manga_keyframe_png(
    shot: Dict[str, Any],
    storyboard: Dict[str, Any],
    out_png: str,
    output_dir: Optional[str] = None,
) -> str:
    """
    Composite a 1080x1920 (9:16) vertical manga keyframe poster:
    - Uses real AI-generated 9:16 Chinese anime illustration when available
      (preserving 82% of the center canvas completely unobstructed for character & scene art).
    - Overlays a sleek top cinema badge and bottom lower-third double-stroked subtitle stage.
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    W, H = 1080, 1920
    style_id = storyboard.get("style", {}).get("id", "xianxia")
    c_top, c_mid, c_accent = STYLE_PALETTES.get(style_id, STYLE_PALETTES["xianxia"])

    emotion = shot.get("emotion", "")
    is_climax = any(k in emotion for k in ["🔥", "⚡", "怒", "爆发", "高燃", "震惊"])

    raw_art_path = _find_raw_artwork(shot.get("shot_id", "SHOT_01"), shot.get("shot_number", 1), output_dir)
    if raw_art_path:
        try:
            base_art = Image.open(raw_art_path).convert("RGB")
            img = base_art.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
        except Exception:
            raw_art_path = None

    if not raw_art_path:
        grad = Image.new("RGB", (1, 256))
        for y in range(256):
            ratio = y / 255.0
            t = ratio
            r = int(c_top[0] * (1 - t) + c_mid[0] * t)
            g = int(c_top[1] * (1 - t) + c_mid[1] * t)
            b = int(c_top[2] * (1 - t) + c_mid[2] * t)
            grad.putpixel((0, y), (r, g, b))
        img = grad.resize((W, H), Image.Resampling.BILINEAR).convert("RGBA")

    # Subtle bottom gradient vignette so subtitles pop clearly against any artwork
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    for y in range(1380, H):
        alpha = int(min(225, ((y - 1380) / (H - 1380)) * 220))
        vdraw.line([(0, y), (W, y)], fill=(5, 8, 16, alpha))

    img = Image.alpha_composite(img, vignette)
    draw_main = ImageDraw.Draw(img)

    font_tag = _load_font(26)
    font_title = _load_font(32)
    font_speaker = _load_font(38)
    font_sub = _load_font(48)

    # Compact translucent top cinema pill
    draw_main.rounded_rectangle(
        [42, 42, W - 42, 146],
        radius=20,
        fill=(8, 12, 22, 168),
        outline=(c_accent[0], c_accent[1], c_accent[2], 180),
        width=2,
    )
    def _strip_emoji(s: str) -> str:
        return "".join(c for c in s if ord(c) < 0x1F000).strip()

    ep_title = _strip_emoji(storyboard.get("title", "AI 漫剧"))
    shot_type_cn = _strip_emoji(shot.get("shot_type", ""))
    if "(" in shot_type_cn and ")" in shot_type_cn:
        shot_type_cn = shot_type_cn.split("(")[-1].rstrip(")")
    emotion_cn = _strip_emoji(shot.get("emotion", ""))
    cam_cn = _strip_emoji(shot.get("camera_motion", ""))
    if "(" in cam_cn and ")" in cam_cn:
        cam_cn = cam_cn.split("(")[-1].rstrip(")")
    sfx_cn = _strip_emoji(shot.get("sfx", "")).split("(")[0].strip()

    shot_badge = f"{shot['shot_id']} · {shot_type_cn} · {emotion_cn}"
    draw_main.text((64, 54), f"《{ep_title[:12]}》 {shot_badge[:22]}", font=font_title, fill=(248, 250, 252, 255))
    draw_main.text((64, 100), f"运镜：{cam_cn[:18]}  |  音效：{sfx_cn[:16]}", font=font_tag, fill=(c_accent[0], c_accent[1], c_accent[2], 240))

    if shot.get("is_golden_3s_hook") or is_climax:
        badge_label = "★ 黄金前3秒强钩子" if shot.get("is_golden_3s_hook") else "★ 高燃名场面"
        draw_main.rounded_rectangle([W - 295, 54, W - 58, 106], radius=14, fill=(220, 38, 38, 235))
        draw_main.text((W - 275, 65), badge_label, font=font_tag, fill=(255, 255, 255, 255))

    # Lower-third subtitle stage (1460..1830)
    draw_main.rounded_rectangle(
        [44, 1470, W - 44, 1835],
        radius=26,
        fill=(7, 10, 20, 196),
        outline=(c_accent[0], c_accent[1], c_accent[2], 215),
        width=3,
    )

    speaker = shot.get("speaker", "旁白")
    speaker_label = f"【{speaker}】"
    draw_main.rounded_rectangle(
        [76, 1494, 76 + max(170, len(speaker_label) * 40), 1554],
        radius=12,
        fill=(c_accent[0], c_accent[1], c_accent[2], 245),
    )
    draw_main.text((92, 1502), speaker_label, font=font_speaker, fill=(10, 14, 24, 255))

    sub_lines = _wrap_text(shot.get("subtitle_text", ""), max_chars_per_line=18)
    sub_color = (254, 240, 138, 255) if speaker != "旁白" else (255, 255, 255, 255)
    for idx, line in enumerate(sub_lines[:3]):
        ly = 1580 + idx * 72
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 3)]:
            draw_main.text((82 + dx, ly + dy), line, font=font_sub, fill=(0, 0, 0, 255))
        draw_main.text((82, ly), line, font=font_sub, fill=sub_color)

    img.convert("RGB").save(out_png, format="PNG", optimize=True)
    return out_png


def enrich_shot_audio_with_sfx(shot: Dict[str, Any], base_wav: str, assets_dir: str) -> str:
    """
    Use `SFXMixer` (`src/sfx_mixer.py`) to synthesize and mix dramatic sound effects
    (bass impact, sword clash, whoosh) into the shot's voiceover WAV track.
    """
    if not base_wav or not os.path.exists(base_wav):
        return base_wav
    mixer = SFXMixer()
    sid = shot.get("shot_id", "SHOT_01")
    mixed_wav = os.path.join(assets_dir, f"{sid}_mixed.wav")
    text_and_sfx = f"{shot.get('narrative_beat', '')} {shot.get('sfx', '')} {shot.get('emotion', '')}"
    sfx_list = []
    try:
        whoosh_file = os.path.join(assets_dir, f"_{sid}_whoosh.wav")
        mixer.generate_whoosh(whoosh_file, duration=0.45)
        sfx_list.append({"file": whoosh_file, "timestamp_ms": 0, "volume": 0.22})

        if any(k in text_and_sfx for k in ["雷", "碎", "崩", "轰", "渊", "🔥", "⚡", "怒"]):
            bass_file = os.path.join(assets_dir, f"_{sid}_bass.wav")
            mixer.generate_impact_bass(bass_file, duration=0.9)
            sfx_list.append({"file": bass_file, "timestamp_ms": 120, "volume": 0.38})

        if any(k in text_and_sfx for k in ["剑", "骨", "刀", "斩", "杀", "撕"]):
            sword_file = os.path.join(assets_dir, f"_{sid}_sword.wav")
            mixer.generate_sword_clash(sword_file, duration=0.45)
            sfx_list.append({"file": sword_file, "timestamp_ms": 350, "volume": 0.28})

        out = mixer.mix_sfx(base_wav, mixed_wav, sfx_list)
        mixer.cleanup()
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            shutil.move(out, base_wav)
    except Exception:
        mixer.cleanup()
    return base_wav


def render_shot_mp4(shot: Dict[str, Any], img_path: str, audio_path: str, out_mp4: str) -> str:
    """
    Combine the 1080x1920 keyframe PNG + spoken voiceover & SFX WAV into a playable 9:16 MP4 clip.
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    dur_sec = max(1.5, float(shot.get("duration_sec", 3.5)))

    if os.path.exists(FFMPEG_BIN) and os.path.exists(img_path) and os.path.exists(audio_path):
        cmd = [
            FFMPEG_BIN, "-y",
            "-loop", "1", "-framerate", "24", "-i", img_path,
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-t", f"{dur_sec:.2f}",
            "-shortest",
            out_mp4,
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=25)
        if res.returncode == 0 and os.path.exists(out_mp4):
            return out_mp4
    return out_mp4


def concatenate_episode_mp4(shot_mp4s: List[str], out_episode_mp4: str) -> str:
    """
    Concatenate all shot `.mp4` clips into a single seamless `episode_final.mp4`.
    """
    valid = [p for p in shot_mp4s if p and os.path.exists(p) and os.path.getsize(p) > 500]
    if not valid or not os.path.exists(FFMPEG_BIN):
        return out_episode_mp4

    os.makedirs(os.path.dirname(os.path.abspath(out_episode_mp4)), exist_ok=True)
    list_file = f"{out_episode_mp4}.concat.txt"
    try:
        with open(list_file, "w", encoding="utf-8") as f:
            for p in valid:
                escaped = os.path.abspath(p).replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")
        cmd = [
            FFMPEG_BIN, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            "-movflags", "+faststart",
            out_episode_mp4,
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
    finally:
        if os.path.exists(list_file):
            try:
                os.remove(list_file)
            except OSError:
                pass
    return out_episode_mp4


def synthesize_episode_media(storyboard: Dict[str, Any], assets_dir: str, output_dir: str) -> Dict[str, Any]:
    """
    Generate all 1080x1920 `.png` keyframes (compositing real AI artwork + subtitles),
    mix SFX into voiceovers, render per-shot `.mp4` clips, and build `episode_final.mp4`.
    """
    os.makedirs(assets_dir, exist_ok=True)
    shot_mp4s: List[str] = []

    for shot in storyboard.get("shots", []):
        sid = shot["shot_id"]
        png_path = os.path.join(assets_dir, f"{sid}.png")
        mp4_path = os.path.join(assets_dir, f"{sid}.mp4")
        aud_path = shot.get("audio_path") or os.path.join(assets_dir, f"{sid}_tts.wav")

        render_manga_keyframe_png(shot, storyboard, png_path, output_dir=output_dir)
        shot["image_path"] = png_path

        if os.environ.get("MANGA_SKIP_MP4") != "1":
            enrich_shot_audio_with_sfx(shot, aud_path, assets_dir)
            render_shot_mp4(shot, png_path, aud_path, mp4_path)
            if os.path.exists(mp4_path):
                shot["video_path"] = mp4_path
                shot_mp4s.append(mp4_path)

    episode_mp4 = os.path.join(output_dir, "episode_final.mp4")
    if shot_mp4s:
        concatenate_episode_mp4(shot_mp4s, episode_mp4)
        if os.path.exists(episode_mp4):
            storyboard["episode_mp4_path"] = episode_mp4

    return {
        "episode_mp4": episode_mp4 if os.path.exists(episode_mp4) else "",
        "shot_mp4_count": len(shot_mp4s),
    }
