import math
from typing import List, Dict, Any, Union

def _safe_float(val: Any, default: float = 0.0) -> float:
    """Helper to convert to float safely with default fallback for NaNs or errors."""
    try:
        if val is None:
            return default
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return default
        return f_val
    except (ValueError, TypeError):
        return default

def _clean_tts_data(item: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures a dict has the required keys with valid numeric types."""
    # Create a new dict to avoid mutating the original input if possible,
    # but the requirement states pure functions when possible.
    # For now, we will return a shallow copy with cleaned keys.
    cleaned = dict(item)

    cleaned['role'] = str(cleaned.get('role', 'unknown_role'))
    cleaned['pitch'] = _safe_float(cleaned.get('pitch', 0.0), default=0.0)
    cleaned['speed'] = _safe_float(cleaned.get('speed', 1.0), default=1.0)
    cleaned['duration_ms'] = _safe_float(cleaned.get('duration_ms', 1000.0), default=1000.0)

    return cleaned

def _calculate_z_scores_for_feature(items: List[Dict[str, Any]], feature: str) -> List[float]:
    n = len(items)
    if n == 0:
        return []
    if n == 1:
        return [0.0]

    values = [item[feature] for item in items]
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_dev = math.sqrt(variance)

    if std_dev == 0:
        return [0.0 for _ in values]

    return [(x - mean) / std_dev for x in values]

def _evaluate_anomalies(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not items:
        return []

    # Calculate Z-Scores for each numerical feature
    pitch_z = _calculate_z_scores_for_feature(items, 'pitch')
    speed_z = _calculate_z_scores_for_feature(items, 'speed')
    duration_z = _calculate_z_scores_for_feature(items, 'duration_ms')

    # Calculate an anomaly score for each item (max absolute Z-score across features)
    anomaly_scores = []
    for i in range(len(items)):
        score = max(abs(pitch_z[i]), abs(speed_z[i]), abs(duration_z[i]))
        anomaly_scores.append((i, score, pitch_z[i], speed_z[i], duration_z[i]))

    # Determine the threshold for the top 3%
    # Sort in descending order of anomaly score
    anomaly_scores.sort(key=lambda x: x[1], reverse=True)

    num_top_3_percent = max(1, int(len(items) * 0.03)) if len(items) >= 34 else (1 if len(items) > 1 else 0)
    # Actually, the requirement says "Top 3% anomalies (if Z-score > 1.5) are marked RED".
    # We should identify the indices of the top 3% that ALSO meet the Z-score > 1.5 criteria.
    top_indices = set()
    count = 0
    for idx, score, p_z, s_z, d_z in anomaly_scores:
        if count < num_top_3_percent and score > 1.5:
            top_indices.add(idx)
            count += 1
        elif score <= 1.5:
            # Since it's sorted, we can stop early if we drop below 1.5, but we just continue to not break loop logic unnecessarily.
            pass

    results = []
    for i, item in enumerate(items):
        result_item = dict(item)
        score_info = next(info for info in anomaly_scores if info[0] == i)
        _, score, p_z, s_z, d_z = score_info

        # Default green
        status = 'GREEN'
        reason = '正常'

        # Determine specific reason if anomalous
        if score > 1.5:
            anomalous_features = []
            if abs(p_z) == score:
                anomalous_features.append(f"音高偏{'高' if p_z > 0 else '低'}")
            elif abs(s_z) == score:
                anomalous_features.append(f"语速偏{'快' if s_z > 0 else '慢'}")
            elif abs(d_z) == score:
                anomalous_features.append(f"时长偏{'长' if d_z > 0 else '短'}")
            reason = "，".join(anomalous_features) + "异常明显"

            if i in top_indices:
                status = 'RED'
            else:
                status = 'YELLOW'
                reason += "（轻微偏差静默放行）"

        result_item['anomaly_status'] = status
        result_item['anomaly_reason'] = reason
        results.append(result_item)

    return results

class MultiRolePitchTTSAnomalyRadar:
    @staticmethod
    def scan_and_modulate(tts_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Validate data
        cleaned_items = [_clean_tts_data(item) for item in tts_items]

        # Group items by role for Z-score calculation
        roles = {}
        for idx, item in enumerate(cleaned_items):
            role = item['role']
            if role not in roles:
                roles[role] = []
            roles[role].append((idx, item))

        evaluated_items_by_idx = {}
        for role, role_items_with_idx in roles.items():
            role_items = [item for _, item in role_items_with_idx]
            evaluated_role_items = _evaluate_anomalies(role_items)
            for (idx, _), eval_item in zip(role_items_with_idx, evaluated_role_items):
                evaluated_items_by_idx[idx] = eval_item

        # Reconstruct the list in original order
        final_results = [evaluated_items_by_idx[i] for i in range(len(cleaned_items))]
        return final_results
