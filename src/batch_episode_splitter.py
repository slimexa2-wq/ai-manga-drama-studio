import re
from typing import List, Dict, Any

def split_long_novel_into_episodes(long_text: str, target_duration_sec: int = 75) -> List[Dict[str, Any]]:
    """
    Split a long novel text into multiple episodes, targeting a specific duration per episode.
    Automatically extracts Golden 3-second Hook, Cliffhanger, and Satisfying Plot Beats for each episode.
    """
    cleaned = re.sub(r"\r\n", "\n", long_text.strip())
    paragraphs = [p.strip() for p in re.split(r"\n+", cleaned) if p.strip()]

    episodes = []
    current_episode_paragraphs = []
    current_duration_sec = 0.0

    for p in paragraphs:
        # Estimate duration: roughly 4.2 chars/sec for speaking/reading
        est_sec = len(p) / 4.2 + 0.8

        if current_duration_sec + est_sec > target_duration_sec * 1.2 and len(current_episode_paragraphs) > 0:
            # Time to split
            episodes.append(_create_episode_dict(current_episode_paragraphs))
            current_episode_paragraphs = []
            current_duration_sec = 0.0

        current_episode_paragraphs.append(p)
        current_duration_sec += est_sec

    if current_episode_paragraphs:
        episodes.append(_create_episode_dict(current_episode_paragraphs))

    return episodes

def _create_episode_dict(paragraphs: List[str]) -> Dict[str, Any]:
    text = "\n".join(paragraphs)

    golden_3s_hook = ""
    if len(paragraphs) > 0:
        golden_3s_hook = paragraphs[0][:60] + "..." if len(paragraphs[0]) > 60 else paragraphs[0]

    cliffhanger = ""
    if len(paragraphs) > 0:
        cliffhanger = paragraphs[-1][-60:]
        if len(paragraphs[-1]) > 60:
            cliffhanger = "..." + cliffhanger

    satisfying_beats = []
    for p in paragraphs:
        if any(k in p for k in ("怒", "杀", "死", "滚", "奉还", "轰", "碎", "剑", "斩", "反转", "觉醒", "冷笑")):
            satisfying_beats.append(p)
            if len(satisfying_beats) >= 3:
                break

    return {
        "text": text,
        "golden_3s_hook": golden_3s_hook,
        "cliffhanger": cliffhanger,
        "satisfying_beats": satisfying_beats
    }
