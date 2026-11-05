import math
import re

def calculate_expected_duration(text):
    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    # 假设：普通中文字符每个0.25秒
    # 标点符号额外增加停顿时间：
    # 逗号，顿号：0.2秒
    # 句号，问号，感叹号：0.4秒
    # 省略号，破折号：0.6秒

    char_count = len(re.sub(r'[^\w\s]', '', text))
    expected = char_count * 0.25

    comma_count = len(re.findall(r'[，、,]', text))
    expected += comma_count * 0.2

    period_count = len(re.findall(r'[。？！\.\?\!]', text))
    expected += period_count * 0.4

    dash_count = len(re.findall(r'[…—]', text))
    expected += dash_count * 0.6

    return expected

def scan_anomalies(dialogues):
    if not isinstance(dialogues, list):
        dialogues = []

    processed_dialogues = []
    differences = []

    for item in dialogues:
        if not isinstance(item, dict):
            item = {}

        # 兜底：处理脏数据
        text = item.get("text", "")
        if not isinstance(text, str):
            text = str(text) if text is not None else ""

        actual_duration = item.get("actual_duration")
        if actual_duration is None or not isinstance(actual_duration, (int, float)):
            try:
                actual_duration = float(actual_duration)
            except (ValueError, TypeError):
                # 缺参自动设合理默认值：如果没有实际时长，则默认它等于预期时长
                actual_duration = calculate_expected_duration(text)

        expected_duration = calculate_expected_duration(text)

        diff = abs(actual_duration - expected_duration)
        differences.append(diff)

        processed_dialogues.append({
            "original": item,
            "text": text,
            "actual_duration": actual_duration,
            "expected_duration": expected_duration,
            "diff": diff
        })

    if not processed_dialogues:
        return []

    # 计算统计分布（使用类似百分位数的方法来找到 Top 3% 异常值）
    # 由于数据可能很少，我们使用简单的方法，结合 z-score 或直接按排名
    n = len(differences)

    # 对 diff 排序，确定阈值
    sorted_diffs = sorted(differences)

    # IQR 和 Z-Score 结合
    # 当样本量少时，直接设定绝对阈值以确保正常工作。或者采用标准的分位数逻辑。

    # 获取 Top 3% 对应的索引
    # 对于 n=100, 97% 对应 index 97 (第 98 个元素，即后 3个为异常)
    # 对于 n < 34， 3% < 1，为了确保极端异常能被抓出，我们采用 IQR / Z-score 或者绝对阈值
    if n >= 3:
        # 使用简单的 Z-score 估算
        mean = sum(differences) / n
        variance = sum((x - mean) ** 2 for x in differences) / n
        std_dev = math.sqrt(variance)
    else:
        mean, std_dev = 0, 0

    # 计算百分位数阈值
    idx_97 = min(n - 1, int(n * 0.97))
    idx_90 = min(n - 1, int(n * 0.90))

    top_3_threshold = sorted_diffs[idx_97]
    yellow_threshold = sorted_diffs[idx_90]

    # 对于小样本，通过 std 补充判断极度异常
    if n < 34 and std_dev > 0:
        # 使用 Z-score 辅助
        top_3_threshold = min(top_3_threshold, mean + 1.5 * std_dev)
        yellow_threshold = min(yellow_threshold, mean + 0.5 * std_dev)

    # 硬性规定最低阈值，防止正常波动被误判
    if top_3_threshold < 1.0:
        top_3_threshold = 1.0
    if yellow_threshold < 0.5:
        yellow_threshold = 0.5

    results = []
    for p in processed_dialogues:
        diff = p["diff"]

        status = "GREEN"
        reason = ""

        if diff >= top_3_threshold and diff >= 1.0:
            status = "RED"
            if p["actual_duration"] > p["expected_duration"]:
                reason = f"实际配音({p['actual_duration']:.2f}秒)比预期({p['expected_duration']:.2f}秒)长太多了，可能是语速太慢或者音频包含无声段。"
            else:
                reason = f"实际配音({p['actual_duration']:.2f}秒)比预期({p['expected_duration']:.2f}秒)短太多了，可能是语速极快或者音频被截断了。"
        elif diff >= yellow_threshold and diff >= 0.5:
            status = "YELLOW"
            reason = "配音时长与预期有一定偏差，可能需要留意一下语速节奏。"

        p["status"] = status
        p["reason"] = reason
        results.append(p)

    return results

if __name__ == '__main__': # pragma: no cover
    pass
