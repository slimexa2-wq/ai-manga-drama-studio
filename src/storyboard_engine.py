"""
Zero-Friction Storyboard & Character DNA Engine for AI Manga Drama Studio.
Turns raw novel text or a 1-sentence premise into:
1. Locked Character DNA Cards (for Google Whisk / Imagen 4 & ChatGPT GPT-Image-2 consistency)
2. 9:16 Vertical Manga Drama Storyboard Shots (Golden 3s Hook + Camera Motion + Dual-Ecosystem Prompts)
"""

import re
import hashlib
from typing import Dict, List, Any
from .style_presets import get_style_preset

# Archetype visual DNA templates for automatic character locking
ARCHETYPE_DNA_POOL = [
    {
        "role": "protagonist_male",
        "voice": "zh-CN-YunxiNeural",
        "visual_dna": "handsome young man, sharp sword-like eyebrows, deep obsidian eyes with a cold resolute gaze, angular jawline, jet-black hair with subtle silver highlights, wearing a dark tailored high-collar trench/robe with gold trim",
    },
    {
        "role": "protagonist_female",
        "voice": "zh-CN-XiaoxiaoNeural",
        "visual_dna": "stunning young woman, luminous phoenix eyes, porcelain skin, flowing raven hair with an emerald hairpin, wearing an elegant frost-white silk dress/suit, aura of aloof nobility",
    },
    {
        "role": "antagonist_or_rival",
        "voice": "zh-CN-YunjianNeural",
        "visual_dna": "arrogant aristocratic figure, narrow calculating eyes, smirk on lips, slick platinum-blonde or dark crimson hair, wearing extravagant crimson-and-gold attire, oppressive presence",
    },
    {
        "role": " elder_or_mentor",
        "voice": "zh-CN-YunyangNeural",
        "visual_dna": "weathered mysterious master, piercing wise eyes, silver beard and hair, wearing weathered grey linen robes, surrounded by faint golden motes of light",
    },
]

CAMERA_MOTIONS = [
    ("fast_push_in", "Fast dramatic push-in zoom to extreme close-up on eyes (急推特写，强化开局3秒压迫感与情绪冲击)"),
    ("slow_dolly_in", "Slow cinematic dolly-in with shallow depth of field (慢推近景，聚焦人物微表情与心理张力)"),
    ("low_angle_tilt_up", "Low-angle仰拍 slow tilt up revealing overwhelming aura (低机位仰拍上摇，凸显主角气场觉醒)"),
    ("dynamic_pan_right", "Smooth lateral tracking pan following character movement with foreground parallax (横移跟拍，带前景视差虚化)"),
    ("pull_back_wide", "Dramatic crane pull-back from close-up to epic wide shot (镜头急速拉远，展现宏大对峙场面)"),
    ("impact_shake_zoom", "High-energy anime impact zoom with subtle camera shake and speed lines (高燃震屏推镜，配合爆发特效)"),
]

SHOT_TYPES = [
    "Extreme Close-Up (面部眼神大特写)",
    "Medium Close-Up (胸像近景)",
    "Low-Angle Hero Medium Shot (仰视中景)",
    "Over-the-Shoulder Two-Shot (过肩双人对峙镜头)",
    "Dramatic Wide Establish Shot (宏大远景环境镜头)",
    "Dutch-Angle Tension Shot (倾斜构图悬疑特写)",
]


def extract_characters(text: str, style_preset: dict) -> List[Dict[str, Any]]:
    """
    Automatically extract character names from Chinese novel/script text and assign
    immutable Character DNA anchors so every shot keeps 100% consistent faces & outfits.
    """
    # Common Chinese dialogue & name patterns
    candidates = []
    # 1. Explicit format like "林玄：" or "【苏清雪】"
    for m in re.finditer(r"(?:^|\n)\s*([一-龥]{2,4})\s*[：:]", text):
        name = m.group(1)
        if name not in ("旁白", "画面", "镜头", "音效", "场景", "字幕", "标题", "第一集") and name not in candidates:
            candidates.append(name)

    # 2. Names before speaking/expression verbs
    for m in re.finditer(r"(?:^|[，。！？\n\s]|手挽|与|被)([一-龥]{2,3})(?:冷笑|淡淡|怒吼|轻声|咬牙|转身|看着|盯着|沉声|嗤笑|开口|说道|喝道|脸色|大惊|闻言|摇头|点头|苦笑|叹息|皱眉|目光|眼神|身披|高坐)", text):
        name = m.group(1)
        if name not in ("众人", "所有人", "那人", "老者", "少年", "女子", "男人", "女人", "自己", "他们", "一股", "一道") and name not in candidates:
            candidates.append(name)

    if not candidates:
        candidates = ["林玄", "苏清雪", "赵天辰"]

    characters = []
    for idx, name in enumerate(candidates[:4]):
        tpl = ARCHETYPE_DNA_POOL[idx % len(ARCHETYPE_DNA_POOL)]
        seed = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:8], 16) % 900000 + 100000
        char_id = f"CHAR_{idx+1:02d}"
        dna_anchor = f"[{char_id}: {name}, {tpl['visual_dna']}, seed:{seed}]"
        characters.append({
            "char_id": char_id,
            "name": name,
            "seed": seed,
            "voice": tpl["voice"],
            "dna_anchor": dna_anchor,
            "visual_description": tpl["visual_dna"],
            "chatgpt_character_sheet_prompt": (
                f"Character turnaround reference sheet for '{name}', {tpl['visual_dna']}. "
                f"Three views: front view, side profile, 3/4 facial expression close-up. "
                f"Style: {style_preset['style_anchor']}. Clean neutral studio background, "
                f"consistent outfit details, vertical 9:16 reference sheet, no extra text artifacts."
            ),
            "google_whisk_subject_prompt": (
                f"Subject reference portrait of {name}: {tpl['visual_dna']}. "
                f"{style_preset['style_anchor']}, crisp lighting, 8k resolution."
            ),
        })
    return characters


def split_into_narrative_beats(text: str) -> List[str]:
    """Split raw novel or script text into high-tension narrative beats (6 to 16 shots)."""
    cleaned = re.sub(r"\r\n", "\n", text.strip())
    paragraphs = [p.strip() for p in re.split(r"\n+", cleaned) if p.strip()]
    beats: List[str] = []
    for p in paragraphs:
        if len(p) <= 65:
            beats.append(p)
        else:
            # Split long paragraph by sentence delimiters while preserving quotes
            parts = re.split(r"(?<=[。！？！”」])\s*", p)
            buf = ""
            for part in parts:
                if not part.strip():
                    continue
                if len(buf) + len(part) <= 65:
                    buf += part
                else:
                    if buf:
                        beats.append(buf.strip())
                    buf = part
            if buf.strip():
                beats.append(buf.strip())

    if not beats:
        beats = [
            "三年前，他被全族夺走至尊骨，像狗一样扔进万魔渊！",
            "所有人都以为他早已尸骨无存，未婚妻更是当众撕毁婚书。",
            "然而今天，大殿之外雷云翻涌，一道黑衣身影踏碎山门而入！",
            "“当年欠我的，今日我要你们百倍奉还！”",
        ]
    return beats[:18]


def infer_emotion_and_sfx(beat: str, idx: int, total: int) -> Dict[str, str]:
    if idx == 0:
        return {"emotion": "🔥 黄金前3秒强冲突/悬念开局", "sfx": "重低音轰鸣 + 玻璃碎裂/雷鸣音效 (Boom + Thunder Impact)"}
    if any(k in beat for k in ("怒", "杀", "死", "滚", "奉还", "轰", "碎", "剑", "斩")):
        return {"emotion": "⚡ 暴怒/高燃爆发", "sfx": "刀剑破空 + 气浪炸裂重音 (Sword Slash + Bass Drop)"}
    if any(k in beat for k in ("冷笑", "嗤", "废物", "凭你", "嘲", "跪")):
        return {"emotion": "❄️ 极度压迫/冷冽反转", "sfx": "心跳重拍 + 琴弦骤断 (Heartbeat + Sharp String Snap)"}
    if idx == total - 1:
        return {"emotion": "🎯 断章卡点悬念 (Cliffhanger)", "sfx": "骤然静音 + 悬疑回响尾音 (Sudden Silence + Eerie Riser)"}
    return {"emotion": "🎬 剧情推进/暗流涌动", "sfx": "环境氛围低音 + 衣袂风声 (Ambient Drone + Wind Whoosh)"}


def build_storyboard(
    raw_text: str,
    title: str = "未命名爆款漫剧",
    style_id: str = "xianxia",
    aspect_ratio: str = "9:16",
) -> Dict[str, Any]:
    """
    End-to-end deterministic storyboard & dual-ecosystem prompt compiler.
    Zero friction: works immediately on any Chinese novel snippet or 1-line idea.
    """
    style = get_style_preset(style_id)
    characters = extract_characters(raw_text, style)
    beats = split_into_narrative_beats(raw_text)

    shots: List[Dict[str, Any]] = []
    current_time_ms = 0

    for idx, beat in enumerate(beats):
        shot_num = idx + 1
        shot_type = SHOT_TYPES[idx % len(SHOT_TYPES)]
        motion_key, motion_desc = CAMERA_MOTIONS[idx % len(CAMERA_MOTIONS)]
        meta = infer_emotion_and_sfx(beat, idx, len(beats))

        # Identify active characters in this beat
        active_chars = [c for c in characters if c["name"] in beat]
        if not active_chars and characters:
            active_chars = [characters[0]]

        char_anchors = ", ".join(c["dna_anchor"] for c in active_chars)

        # Extract spoken dialogue vs narration
        quote_match = re.search(r"[“「\"]([^”」\"]+)[”」\"]", beat)
        if quote_match:
            dialogue = quote_match.group(1).strip()
            speaker = active_chars[0]["name"] if active_chars else "主角"
            voice_id = active_chars[0]["voice"] if active_chars else "zh-CN-YunxiNeural"
        else:
            dialogue = re.sub(r"^[一-龥]{2,4}[：:]\s*", "", beat).strip()
            speaker = "旁白"
            voice_id = "zh-CN-YunyangNeural"

        # Calculate natural speaking duration (roughly 4.2 chars/sec in dramatic pacing, bounded 3.2s - 6.5s)
        est_sec = round(max(3.2, min(6.5, len(dialogue) / 4.2 + 0.8)), 1)
        duration_ms = int(est_sec * 1000)

        # 1. ChatGPT Plus (GPT-Image-2 / awesome-gpt-image-2 structured 6-block prompt)
        chatgpt_prompt = (
            f"[Subject & Action]: Scene {shot_num}: {beat} Character consistency lock: {char_anchors}. "
            f"[Composition & Framing]: {shot_type}, vertical {aspect_ratio} mobile short-drama framing, strong foreground-background depth. "
            f"[Visual Style & Lighting]: {style['style_anchor']}. Emotion: {meta['emotion']}. "
            f"[Text & Subtitle Reserve]: Leave clean lower-third space for vertical subtitles; no gibberish text or watermarks. "
            f"[Aspect Ratio]: {aspect_ratio} vertical portrait (1080x1920). "
            f"[Negative Constraints]: no deformed hands, no inconsistent face, no extra fingers, no blurry background, no speech bubbles."
        )

        # 2. Google 20x Ultra (Google Flow / Whisk + Imagen 4) image prompt
        google_flow_image_prompt = (
            f"{style['style_anchor']}. {shot_type}. {char_anchors}. "
            f"Visual scene: {beat} Dramatic lighting, {aspect_ratio} vertical composition, ultra-crisp 8k anime keyframe."
        )

        # 3. Google 20x Ultra (Veo 3 / Flow Image-to-Video) & OpenAI Sora motion prompt
        veo3_video_prompt = (
            f"[Camera Motion]: {motion_desc}. "
            f"[Action & Physics]: Animate the keyframe smoothly over {est_sec:.0f}s: {beat} "
            f"{style['veo_motion_style']}. Maintain 100% facial identity of {char_anchors}."
        )

        shots.append({
            "shot_id": f"SHOT_{shot_num:02d}",
            "shot_number": shot_num,
            "start_ms": current_time_ms,
            "end_ms": current_time_ms + duration_ms,
            "duration_sec": est_sec,
            "duration_ms": duration_ms,
            "shot_type": shot_type,
            "camera_motion_key": motion_key,
            "camera_motion": motion_desc,
            "emotion": meta["emotion"],
            "sfx": meta["sfx"],
            "speaker": speaker,
            "voice_id": voice_id,
            "narrative_beat": beat,
            "subtitle_text": dialogue,
            "active_characters": [c["name"] for c in active_chars],
            "chatgpt_plus_image_prompt": chatgpt_prompt,
            "google_ultra_flow_image_prompt": google_flow_image_prompt,
            "google_ultra_veo3_video_prompt": veo3_video_prompt,
        })
        current_time_ms += duration_ms

    return {
        "title": title,
        "style": style,
        "aspect_ratio": aspect_ratio,
        "total_shots": len(shots),
        "total_duration_sec": round(current_time_ms / 1000.0, 1),
        "characters": characters,
        "shots": shots,
        "ecosystem_plan": {
            "google_20x_ultra": {
                "tools": ["Gemini 3.1 Pro (剧本精修与一致性校验)", "Google Whisk / Imagen 4 (三视图角色资产锁定)", "Google Flow + Veo 3 (分镜首尾帧生图与电影级动态视频)", "Jules Ultra (管线自动化演进)"],
                "flow_url": "https://labs.google/fx/tools/flow",
                "whisk_url": "https://labs.google/fx/tools/whisk",
                "gemini_url": "https://gemini.google.com/app",
            },
            "chatgpt_plus": {
                "tools": ["GPT-4o / o3 (黄金前3秒网文爽点钩子拆解)", "GPT-Image-2 + awesome-gpt-image-2 模板库 (高张力分镜关键帧)", "Sora (动态镜头补充)"],
                "chatgpt_url": "https://chatgpt.com/",
                "sora_url": "https://sora.com/",
            },
        },
    }
