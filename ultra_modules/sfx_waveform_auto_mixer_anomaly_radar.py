import math
from typing import List, Dict, Any, Tuple, Optional

def generate_sfx_waveform_path(effect_type: Any = "heavy_bass", intensity: Any = 1.0) -> str:
    """
    高燃分镜重低音震屏/刀剑铮鸣/转场呼啸波形合成路径生成（纯函数）。
    包含脏数据自愈与缺参默认兜底。
    """
    # 脏数据自愈与缺参兜底
    if not isinstance(effect_type, str):
        effect_type = "heavy_bass"

    effect_type = effect_type.strip().lower()
    valid_effects = {"heavy_bass", "sword_clash", "transition_whoosh"}
    if effect_type not in valid_effects:
        effect_type = "heavy_bass"

    try:
        intensity_val = float(intensity)
        if intensity_val < 0:
            intensity_val = 1.0
    except (ValueError, TypeError):
        intensity_val = 1.0

    return f"/auto_mixer/sfx/{effect_type}_int{intensity_val:.2f}.wav"

def generate_ffmpeg_mix_command(track_paths: Optional[List[Any]] = None, output_path: Any = "final_mix.wav") -> str:
    """
    FFmpeg 多轨自动混音器命令生成（纯函数）。
    """
    if track_paths is None:
        track_paths = []

    if not isinstance(output_path, str) or not output_path.strip():
        output_path = "final_mix.wav"

    # 脏数据自愈：过滤非字符串或空路径
    clean_paths = []
    for p in track_paths:
        if isinstance(p, str) and p.strip():
            clean_paths.append(p.strip())

    if not clean_paths:
        return ""

    inputs_str = " ".join([f"-i '{p}'" for p in clean_paths])
    filter_complex = "".join([f"[{i}:a]" for i in range(len(clean_paths))])
    filter_complex += f"amix=inputs={len(clean_paths)}:duration=longest[a]"

    return f"ffmpeg {inputs_str} -filter_complex '{filter_complex}' -map '[a]' '{output_path}'"

def _calculate_z_scores(data: List[float]) -> List[float]:
    n = len(data)
    if n <= 1:
        return [0.0] * n

    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / n
    std_dev = math.sqrt(variance)

    if std_dev == 0:
        return [0.0 for _ in data]

    return [(x - mean) / std_dev for x in data]

def _calculate_iqr_q1_q3(data: List[float]) -> Tuple[float, float]:
    if not data:
        return 0.0, 0.0
    sorted_data = sorted(data)
    n = len(sorted_data)

    def get_median(lst: List[float]) -> float:
        l = len(lst)
        if l == 0: return 0.0
        if l % 2 == 1:
            return lst[l // 2]
        return (lst[l // 2 - 1] + lst[l // 2]) / 2.0

    mid = n // 2
    if n % 2 == 0:
        q1 = get_median(sorted_data[:mid])
        q3 = get_median(sorted_data[mid:])
    else:
        q1 = get_median(sorted_data[:mid])
        q3 = get_median(sorted_data[mid+1:])

    return q1, q3

def scan_anomalies_radar(values: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """
    统计分布异常值(Z-Score/IQR)后台静默扫描与红黄绿三色极简标记器。
    自动高亮真正需要人工关注的Top 3%异常项并给出大白话原因，其余97%正常项静默放行。
    """
    if values is None:
        values = []

    clean_vals = []
    for v in values:
        if v is None:
            clean_vals.append(0.0)
            continue
        try:
            clean_vals.append(float(v))
        except (ValueError, TypeError):
            clean_vals.append(0.0)

    n = len(clean_vals)
    if n == 0:
        return []

    z_scores = _calculate_z_scores(clean_vals)
    q1, q3 = _calculate_iqr_q1_q3(clean_vals)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    anomalies = []
    for i, val in enumerate(clean_vals):
        z = z_scores[i]
        is_iqr = (val < lower_bound or val > upper_bound)
        if is_iqr or abs(z) > 2.0:
            anomalies.append((abs(z), i))

    anomalies.sort(reverse=True, key=lambda x: x[0])

    top_k = math.ceil(n * 0.03)
    top_anomaly_indices = {idx for _, idx in anomalies[:top_k]}

    results = []
    for i, val in enumerate(clean_vals):
        z = z_scores[i]

        if i in top_anomaly_indices:
            if abs(z) > 3.0:
                status = "Red"
                reason = "极度偏离正常水平，存在严重风险，务必人工确认！"
            else:
                status = "Yellow"
                reason = "数值出现异常偏离，建议抽查确认。"
        else:
            status = "Green"
            reason = "正常，静默放行。"

        results.append({
            "index": i,
            "value": val,
            "z_score": z,
            "status": status,
            "reason": reason
        })

    return results
