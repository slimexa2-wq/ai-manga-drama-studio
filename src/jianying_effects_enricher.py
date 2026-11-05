import json
import uuid
from typing import Dict, Any

def enrich_draft_content(draft_content: Dict[str, Any], storyboard: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriches the JianYing draft content by injecting text effects (花字),
    transitions (闪白), video effects (震屏), and BGM audio tracks.
    """

    # 1. Text Highlighting (花字样式)
    if "materials" in draft_content and "texts" in draft_content["materials"]:
        for text_mat in draft_content["materials"]["texts"]:
            if "content" in text_mat:
                try:
                    content_dict = json.loads(text_mat["content"])
                    text_val = content_dict.get("text", "")
                    # If subtitle contains strong punctuation, add a text effect
                    if any(p in text_val for p in ["!", "！", "?", "？"]):
                        text_mat["text_effects"] = [{
                            "id": str(uuid.uuid4()).upper(),
                            "name": "高亮花字",
                            "type": "outline_glow",
                        }]
                except json.JSONDecodeError:
                    pass

    # Ensure required material categories exist
    draft_content.setdefault("materials", {})
    draft_content["materials"].setdefault("transitions", [])
    draft_content["materials"].setdefault("video_effects", [])
    draft_content["materials"].setdefault("audios", [])
    draft_content.setdefault("tracks", [])

    video_track = next((t for t in draft_content.get("tracks", []) if t.get("type") == "video"), None)

    # 2. Transitions and Video Effects (闪白转场 & 震屏)
    if video_track and "segments" in video_track:
        shots = storyboard.get("shots", [])
        for i, shot in enumerate(shots):
            if i >= len(video_track["segments"]):
                break

            seg = video_track["segments"][i]
            emotion = shot.get("emotion", "").lower()
            motion = shot.get("camera_motion", "").lower()

            is_high_tension = any(k in emotion for k in ["angry", "shock", "tension", "愤怒", "震惊", "激昂"]) or \
                              any(k in motion for k in ["shake", "震"])

            if is_high_tension:
                # Add video effect (震屏)
                vfx_id = str(uuid.uuid4()).upper()
                draft_content["materials"]["video_effects"].append({
                    "id": vfx_id,
                    "name": "震屏",
                    "type": "video_effect",
                    "value": "camera_shake",
                })
                seg.setdefault("video_effects", []).append({"id": vfx_id})

                # Add transition (闪白)
                if i > 0:
                    trans_id = str(uuid.uuid4()).upper()
                    draft_content["materials"]["transitions"].append({
                        "id": trans_id,
                        "name": "闪白转场",
                        "type": "transition",
                        "duration": 500000, # 0.5s in microseconds
                    })
                    seg["transition_id"] = trans_id

    # 3. BGM Track (情绪BGM自动编排器)
    bgm_segments = []
    style_bgm_mood = storyboard.get("style", {}).get("default_bgm_mood", "cinematic_epic_trailer")

    shots = storyboard.get("shots", [])
    for shot in shots:
        bgm_id = str(uuid.uuid4()).upper()
        start_us = shot["start_ms"] * 1000
        dur_us = shot["duration_ms"] * 1000
        emotion = shot.get("emotion", "").lower()

        # Determine mood based on emotion, fallback to style default
        is_high_tension = any(k in emotion for k in ["angry", "shock", "tension", "愤怒", "震惊", "激昂"])
        mood = "epic_tension_bgm" if is_high_tension else style_bgm_mood

        draft_content["materials"]["audios"].append({
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
            "volume": 0.4, # Lower volume for background music
        })

    if bgm_segments:
        draft_content["tracks"].append({
            "id": str(uuid.uuid4()).upper(),
            "type": "audio",
            "flag": "bgm",
            "segments": bgm_segments,
        })

    return draft_content
