import logging
from typing import Dict, List, Optional, Any, Tuple
import math

logger = logging.getLogger(__name__)

def split_text_into_episodes(text: str, num_episodes: int) -> List[str]:
    """Splits text into num_episodes as evenly as possible."""
    if not text:
        return []

    text = " ".join(text.split())
    if num_episodes <= 0:
        num_episodes = 1

    length = len(text)
    chunk_size = math.ceil(length / num_episodes)
    # To fix coverage for impossible branch (math.ceil won't result in chunk_size == 0 for length > 0)
    # And len(episodes) > num_episodes is mathematically impossible with math.ceil

    episodes = []
    for i in range(0, length, chunk_size):
        episodes.append(text[i:i + chunk_size])

    return episodes

def _calculate_score(segment: str) -> float:
    if not segment:
        return 0.0
    score = len(segment) * 0.1
    score += segment.count('!') * 5.0
    score += segment.count('?') * 5.0
    score += segment.count('？') * 5.0
    score += segment.count('！') * 5.0
    score += segment.count('…') * 3.0
    return score

def _calculate_z_scores(scores: List[float]) -> List[float]:
    n = len(scores)
    if n <= 1:
        return [0.0] * n
    mean = sum(scores) / n
    variance = sum((x - mean) ** 2 for x in scores) / n
    std_dev = math.sqrt(variance)
    if std_dev == 0:
        return [0.0] * n
    return [(x - mean) / std_dev for x in scores]

def _calculate_iqr_outliers(scores: List[float]) -> Tuple[float, float]:
    n = len(scores)
    if n < 4:
        return -float('inf'), float('inf')
    sorted_scores = sorted(scores)
    q1 = sorted_scores[int(n * 0.25)]
    q3 = sorted_scores[int(n * 0.75)]
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr

def parse_and_analyze_episodes(
    text: Optional[str] = None,
    episodes_count: Optional[int] = None,
    z_threshold: Optional[float] = None
) -> Dict[str, Any]:
    # 1. Missing parameter default fallback & dirty data self-healing
    is_dirty = False
    if text is None or not isinstance(text, str):
        text = ""
        is_dirty = True
        logger.warning("Text is missing or invalid. Defaulting to empty string.")

    if episodes_count is None or not isinstance(episodes_count, int) or episodes_count <= 0:
        episodes_count = max(1, len(text) // 500) if len(text) > 0 else 1
        is_dirty = True

    if z_threshold is None or not isinstance(z_threshold, (int, float)):
        z_threshold = 1.88

    episodes = split_text_into_episodes(text, episodes_count)
    if not episodes:
        return {"total_episodes": 0, "analyzed_results": []}

    hook_scores = []
    cliffhanger_scores = []
    for ep in episodes:
        hook = ep[:50]
        cliffhanger = ep[-50:] if len(ep) >= 50 else ep
        hook_scores.append(_calculate_score(hook))
        cliffhanger_scores.append(_calculate_score(cliffhanger))

    hook_z_scores = _calculate_z_scores(hook_scores)
    cliff_z_scores = _calculate_z_scores(cliffhanger_scores)
    hook_lower, hook_upper = _calculate_iqr_outliers(hook_scores)
    cliff_lower, cliff_upper = _calculate_iqr_outliers(cliffhanger_scores)

    num_episodes_actual = len(episodes)
    top_3_count = max(1, math.ceil(num_episodes_actual * 0.03))

    episode_anomalies = []
    for i in range(num_episodes_actual):
        hz = abs(hook_z_scores[i])
        cz = abs(cliff_z_scores[i])
        h_val = hook_scores[i]
        c_val = cliffhanger_scores[i]
        is_iqr = (h_val < hook_lower or h_val > hook_upper) or (c_val < cliff_lower or c_val > cliff_upper)

        score_sum = hz + cz + (2.0 if is_iqr else 0.0)
        episode_anomalies.append({
            'index': i,
            'score': score_sum,
            'hz': hook_z_scores[i],
            'cz': cliff_z_scores[i],
            'is_iqr': is_iqr
        })

    episode_anomalies.sort(key=lambda x: x['score'], reverse=True)
    top_anomalies_indices = {x['index'] for x in episode_anomalies[:top_3_count]} if top_3_count > 0 and num_episodes_actual > 1 else set()

    results = []
    for i, ep in enumerate(episodes):
        hz = hook_z_scores[i]
        cz = cliff_z_scores[i]

        # Find this episode's anomaly info
        ea = next(item for item in episode_anomalies if item['index'] == i)
        is_iqr = ea['is_iqr']

        h_val = hook_scores[i]
        c_val = cliffhanger_scores[i]

        is_top_anomaly = i in top_anomalies_indices and ea['score'] > 0

        if is_top_anomaly:
            reasons = []
            if h_val < hook_lower or hz < -1.0:
                reasons.append("开头太平淡，缺乏前3秒黄金钩子")
            elif h_val > hook_upper or hz > 1.0:
                reasons.append("开头元素堆砌过度，可能略显浮夸")
            if c_val < cliff_lower or cz < -1.0:
                reasons.append("结尾没有留悬念，读者容易流失")
            elif c_val > cliff_upper or cz > 1.0:
                reasons.append("结尾断章太刻意，情绪拉扯过头")

            status = "Red"
            reason = "；".join(reasons)
        elif abs(hz) > z_threshold or abs(cz) > z_threshold:
            status = "Yellow"
            reason = "边缘波动，可酌情关注"
        elif is_dirty and i == 0 and len(episodes) == 1:
            status = "Yellow"
            reason = "触发缺参兜底自愈，静默修复完成"
        else:
            status = "Green"
            reason = "正常"

        results.append({
            "episode": i + 1,
            "content_preview": ep[:20] + "..." if len(ep) > 20 else ep,
            "status": status,
            "reason": reason,
            "hook_score": h_val,
            "cliffhanger_score": c_val
        })

    return {
        "total_episodes": len(episodes),
        "analyzed_results": results
    }
