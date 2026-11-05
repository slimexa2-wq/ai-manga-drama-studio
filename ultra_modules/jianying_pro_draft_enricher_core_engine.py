import json
import uuid
import copy
from typing import Any, Dict, Optional

def enrich_draft_content(
    draft_data: Optional[Dict[str, Any]] = None,
    storyboard: Optional[Dict[str, Any]] = None,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Enriches the JianYing draft content by injecting text effects (花字特效),
    transitions (震屏转场), KenBurns animations (运镜), and BGM audio tracks.
    """
    # 1. Zero-configuration fallback & Dirty data self-healing
    if not isinstance(draft_data, dict):
        draft_data = {}
    if not isinstance(storyboard, dict):
        storyboard = {}
    if not isinstance(options, dict):
        options = {}

    # Fill missing options with True
    enable_text_effects = options.get("enable_text_effects", True)
    enable_transitions = options.get("enable_transitions", True)
    enable_ken_burns = options.get("enable_ken_burns", True)
    enable_bgm = options.get("enable_bgm", True)

    # Pure function: Deep copy the input
    new_draft = copy.deepcopy(draft_data)

    # Ensure basic structure
    materials = new_draft.get("materials")
    if not isinstance(materials, dict):
        materials = {}
        new_draft["materials"] = materials

    for k in ["texts", "transitions", "video_effects", "audios", "animations"]:
        val = materials.get(k)
        if not isinstance(val, list):
            materials[k] = []

    tracks = new_draft.get("tracks")
    if not isinstance(tracks, list):
        tracks = []
        new_draft["tracks"] = tracks

    # Retrieve video track safely
    video_track = None
    for t in tracks:
        if isinstance(t, dict) and t.get("type") == "video":
            video_track = t
            break

    if not video_track:
        video_track = {"id": str(uuid.uuid4()).upper(), "type": "video", "segments": []}
        tracks.append(video_track)

    segments = video_track.get("segments")
    if not isinstance(segments, list):
        segments = []
        video_track["segments"] = segments

    shots = storyboard.get("shots")
    if not isinstance(shots, list):
        shots = []

    # 1. Text Effects (花字特效)
    if enable_text_effects:
        for text_mat in materials["texts"]:
            if isinstance(text_mat, dict) and "content" in text_mat:
                try:
                    content_str = text_mat["content"]
                    if isinstance(content_str, str):
                        content_dict = json.loads(content_str)
                        if isinstance(content_dict, dict):
                            text_val = content_dict.get("text", "")
                            if isinstance(text_val, str) and any(p in text_val for p in ["!", "！", "?", "？"]):
                                text_mat["text_effects"] = [{
                                    "id": str(uuid.uuid4()).upper(),
                                    "name": "高亮花字",
                                    "type": "outline_glow",
                                }]
                except (json.JSONDecodeError, TypeError):
                    pass

    # 2. Shake Transitions & Ken Burns (震屏转场 & 运镜)
    if enable_transitions or enable_ken_burns:
        for i, shot in enumerate(shots):
            if not isinstance(shot, dict):
                continue
            if i >= len(segments):
                break

            seg = segments[i]
            if not isinstance(seg, dict):
                continue

            emotion = str(shot.get("emotion", "")).lower()
            motion = str(shot.get("camera_motion", "")).lower()

            is_high_tension = any(k in emotion for k in ["angry", "shock", "tension", "愤怒", "震惊", "激昂"]) or \
                              any(k in motion for k in ["shake", "震"])

            if enable_transitions and is_high_tension:
                # Add Transition
                if i > 0:
                    trans_id = str(uuid.uuid4()).upper()
                    materials["transitions"].append({
                        "id": trans_id,
                        "name": "震屏转场",
                        "type": "transition",
                        "duration": 500000, # 0.5s in microseconds
                    })
                    seg["transition_id"] = trans_id

            if enable_ken_burns:
                # Ken Burns Effect (Animations)
                anim_id = str(uuid.uuid4()).upper()
                anim_type = "zoom_in" if "zoom" in motion else "pan"
                materials["animations"].append({
                    "id": anim_id,
                    "name": "KenBurns运镜",
                    "type": anim_type
                })
                if not isinstance(seg.get("animations"), list):
                    seg["animations"] = []
                seg["animations"].append({"id": anim_id})

    # 3. BGM Injector
    if enable_bgm:
        bgm_segments = []
        style_bgm_mood = storyboard.get("style", {})
        if not isinstance(style_bgm_mood, dict):
            style_bgm_mood = {}
        default_bgm = style_bgm_mood.get("default_bgm_mood", "cinematic_epic_trailer")

        for shot in shots:
            if not isinstance(shot, dict):
                continue

            start_ms = shot.get("start_ms", 0)
            duration_ms = shot.get("duration_ms", 3000)

            # Clean boundaries
            if not isinstance(start_ms, (int, float)) or start_ms < 0:
                start_ms = 0
            if not isinstance(duration_ms, (int, float)) or duration_ms < 0:
                duration_ms = 3000

            start_us = int(start_ms * 1000)
            dur_us = int(duration_ms * 1000)

            emotion = str(shot.get("emotion", "")).lower()
            is_high_tension = any(k in emotion for k in ["angry", "shock", "tension", "愤怒", "震惊", "激昂"])
            mood = "epic_tension_bgm" if is_high_tension else default_bgm

            bgm_id = str(uuid.uuid4()).upper()
            materials["audios"].append({
                "id": bgm_id,
                "type": "music",
                "name": f"mood_bgm_{mood}.mp3",
                "duration": dur_us,
            })

            bgm_segments.append({
                "id": str(uuid.uuid4()).upper(),
                "material_id": bgm_id,
                "target_timerange": {"start": start_us, "duration": dur_us},
                "source_timerange": {"start": 0, "duration": dur_us},
                "volume": 0.4,
            })

        if bgm_segments:
            tracks.append({
                "id": str(uuid.uuid4()).upper(),
                "type": "audio",
                "flag": "bgm",
                "segments": bgm_segments,
            })

    return new_draft
