import math
import statistics
import copy

def _percentile(data, p):
    n = len(data)
    if n == 0: return 0.0
    if n == 1: return data[0]
    k = (n - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(data[int(k)])
    d0 = float(data[int(f)]) * (c - k)
    d1 = float(data[int(c)]) * (k - f)
    return d0 + d1

def analyze_anomalies(tasks, metric_key="duration_ms", top_percent=3.0):
    """
    Pure function to analyze tasks for anomalies using Z-Score and IQR.
    Provides zero-configuration defaults, dirty data self-healing, and extreme boundary handling.
    """
    if not tasks:
        return []

    valid_vals = []
    parsed_tasks = []

    # 1. Self-healing and data extraction
    for task in tasks:
        val_raw = task.get(metric_key)
        is_dirty = False
        val = 0.0

        try:
            if val_raw is None:
                is_dirty = True
            else:
                val = float(val_raw)
                if math.isnan(val) or math.isinf(val):
                    is_dirty = True
        except (ValueError, TypeError):
            is_dirty = True

        if not is_dirty:
            valid_vals.append(val)

        parsed_tasks.append({
            "original": task,
            "is_dirty": is_dirty,
            "val": val if not is_dirty else None
        })

    # 2. Extreme boundary: empty valid vals or single value
    if not valid_vals:
        median = 0.0
        mean = 0.0
        std = 0.0
        q1 = 0.0
        q3 = 0.0
        iqr = 0.0
    elif len(valid_vals) == 1:
        median = valid_vals[0]
        mean = valid_vals[0]
        std = 0.0
        q1 = valid_vals[0]
        q3 = valid_vals[0]
        iqr = 0.0
    else:
        valid_vals.sort()
        median = statistics.median(valid_vals)
        mean = statistics.mean(valid_vals)
        std = statistics.stdev(valid_vals) if len(valid_vals) > 1 else 0.0

        q1 = _percentile(valid_vals, 0.25)
        q3 = _percentile(valid_vals, 0.75)
        iqr = q3 - q1

    # 3. Compute anomaly scores
    scored_tasks = []
    for item in parsed_tasks:
        if item["is_dirty"]:
            val = median
            item["val"] = val
        else:
            val = item["val"]

        z_score = abs(val - mean) / std if std > 0 else 0.0

        denom = iqr if iqr > 0 else (std if std > 0 else 1.0)
        iqr_score = abs(val - median) / denom

        score = max(z_score, iqr_score)

        direction = "high" if val > median else ("low" if val < median else "normal")

        scored_tasks.append({
            "task": item["original"],
            "val": val,
            "score": score,
            "is_dirty": item["is_dirty"],
            "direction": direction
        })

    # 4. Sort by anomaly score descending, preserving original order for ties
    for i, st in enumerate(scored_tasks):
        st["original_index"] = i

    scored_tasks.sort(key=lambda x: (-x["score"], x["original_index"]))

    # 5. Mark Red, Yellow, Green
    n_tasks = len(scored_tasks)
    max_reds = int(n_tasks * (top_percent / 100.0))

    # Small dataset fallback
    if max_reds == 0 and n_tasks > 0:
        if scored_tasks[0]["score"] > 3.0 and not scored_tasks[0]["is_dirty"]:
            max_reds = 1

    result = [None] * n_tasks

    for i, st in enumerate(scored_tasks):
        orig_task = copy.deepcopy(st["task"])
        val = st["val"]
        idx = st["original_index"]

        if st["is_dirty"]:
            color = "yellow"
            reason = f"数据缺失或格式损坏，已自动自愈为中位数 ({median:.2f})，后台静默放行。"
        elif i < max_reds and st["score"] > 2.0:
            color = "red"
            if st["direction"] == "high":
                reason = f"该任务的 {metric_key} 指标 ({val:.2f}) 异常偏高，大幅偏离正常中位数 ({median:.2f})，需排查是否卡死或资源耗尽。"
            else:
                reason = f"该任务的 {metric_key} 指标 ({val:.2f}) 异常偏低，大幅偏离正常中位数 ({median:.2f})，可能被意外中断或空跑。"
        elif st["score"] > 1.5:
            color = "yellow"
            reason = "指标略微偏离正常范围，后台静默放行，无需人工干预。"
        else:
            color = "green"
            reason = "指标正常，后台静默放行。"

        orig_task["_anomaly_color"] = color
        orig_task["_anomaly_reason"] = reason
        orig_task["_anomaly_score"] = round(st["score"], 4)

        result[idx] = orig_task

    return result
