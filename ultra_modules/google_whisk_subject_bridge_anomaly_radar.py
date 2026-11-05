import math
from typing import List, Dict, Any

def scan_and_build_payloads(payloads: Any) -> List[Dict[str, Any]]:
    """
    Google Labs Whisk Subject/Style/Scene Payload Builder and Anomaly Radar.
    Self-heals dirty data, builds the payload, and applies a statistical anomaly radar (Z-Score/IQR).
    Marks top 3% anomalies (RED) with plain-text reasons, others (YELLOW/GREEN) are silently passed.
    """
    if not isinstance(payloads, list):
        if payloads is None:
            payloads = []
        else:
            payloads = [payloads]

    cleaned_payloads = []

    # 1. Data self-healing and default fallbacks
    for item in payloads:
        if not isinstance(item, dict):
            item = {"raw_data": item}

        subject = item.get("subject")
        if not subject or not isinstance(subject, str):
            subject = "default_subject"

        style = item.get("style")
        if not style or not isinstance(style, str):
            style = "default_style"

        scene = item.get("scene")
        if not scene or not isinstance(scene, str):
            scene = "default_scene"

        # Determine a numeric value for anomaly detection.
        # Fallback to the total string length of the payload if no value provided.
        if "value" in item and isinstance(item["value"], (int, float)):
            val = float(item["value"])
        else:
            val = float(len(subject) + len(style) + len(scene))

        cleaned_payloads.append({
            "subject": subject,
            "style": style,
            "scene": scene,
            "value": val,
            "original_data": item
        })

    n = len(cleaned_payloads)
    if n == 0:
        return []

    # 2. Statistical calculation (Z-Score & IQR)
    values = [p["value"] for p in cleaned_payloads]
    mean_val = sum(values) / n
    variance = sum((v - mean_val) ** 2 for v in values) / n
    std_dev = math.sqrt(variance) if variance > 0 else 0.0

    sorted_vals = sorted(values)

    def get_percentile(data: List[float], p: float) -> float:
        if not data: return 0.0
        if len(data) == 1: return data[0]
        k = (len(data) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return data[int(k)]
        return data[int(f)] * (c - k) + data[int(c)] * (k - f)

    q1 = get_percentile(sorted_vals, 0.25)
    q3 = get_percentile(sorted_vals, 0.75)
    iqr = q3 - q1
    iqr_upper = q3 + 1.5 * iqr
    iqr_lower = q1 - 1.5 * iqr

    # Calculate anomaly score (Z-score and IQR outliers)
    for p in cleaned_payloads:
        v = p["value"]
        if std_dev > 0:
            p["z_score"] = abs(v - mean_val) / std_dev
        else:
            p["z_score"] = 0.0

        # If IQR is 0 (e.g. all 10s in Q1 to Q3), anything outside is technically an outlier
        if iqr == 0:
            p["is_iqr_outlier"] = (v > q3 or v < q1)
        else:
            p["is_iqr_outlier"] = (v > iqr_upper or v < iqr_lower)

    # Sort by z_score descending to find top 3% most extreme values
    sorted_by_anomaly = sorted([p for p in cleaned_payloads], key=lambda x: x["z_score"], reverse=True)

    # 3% of N. We use math.ceil to ensure at least 1 item if N is small but we only mark RED if z > 0
    top_3_percent_count = math.ceil(n * 0.03)

    # 3. Assign RED/YELLOW/GREEN status
    for i, p in enumerate(sorted_by_anomaly):
        v = p["value"]
        z = p["z_score"]
        is_iqr_outlier = p["is_iqr_outlier"]

        is_in_top_3_percent = i < top_3_percent_count

        if is_in_top_3_percent and z > 1.0:
            p["status"] = "RED"
            p["reason"] = f"【需人工关注】该数据点数值({v:.2f})显著偏离。Z-Score为{z:.2f}，属于Top 3%极度异常值，请检查是否为错误配置。"
        elif z > 1.0 or is_iqr_outlier:
            p["status"] = "YELLOW"
            p["reason"] = f"【轻微波动】数据(Z-Score={z:.2f})略超常规范畴，可能是特殊场景。系统已自动兜底静默放行。"
        else:
            p["status"] = "GREEN"
            p["reason"] = "【数据正常】当前数值处于健康均值区间，一键全自动静默放行。"

    return cleaned_payloads
