import math
from typing import List, Dict, Any, Optional, Union

def scan_turnaround_sheet_anomalies(
    data_points: Optional[Union[List[Any], Any]] = None,
    metrics_key: str = 'complexity_score'
) -> List[Dict[str, Any]]:
    """
    ChatGPT Plus (GPT-Image-2) 角色正侧背三视图与表情设定集一键生成指令器
    统计分布异常值(Z-Score/IQR)后台静默扫描与红黄绿三色极简标记器。

    自动高亮真正需要人工关注的Top 3%异常项并给出大白话原因，其余97%正常项静默放行。
    零配置容错、缺参自动设合理默认值，极度简单直观。
    """
    # 缺参自动设合理默认值
    if data_points is None:
        data_points = []

    if not isinstance(data_points, list):
        data_points = [data_points]

    cleaned_data = []
    for i, dp in enumerate(data_points):
        # 脏数据自愈：不是字典的转为字典
        if not isinstance(dp, dict):
            dp = {'id': f'item_{i}', metrics_key: 0.0, 'original_data': dp}
        else:
            dp = dp.copy()

        # 缺参默认兜底：如果没有指标字段，默认设为 0.0
        if metrics_key not in dp:
            dp[metrics_key] = 0.0
        else:
            try:
                dp[metrics_key] = float(dp[metrics_key])
            except (ValueError, TypeError):
                dp[metrics_key] = 0.0

        cleaned_data.append(dp)

    n = len(cleaned_data)
    if n == 0:
        return []

    # 如果数据量极少，无法进行有意义的统计学分析，全部静默放行（绿灯）
    if n < 3:
        for dp in cleaned_data:
            dp['anomaly_color'] = 'Green'
            dp['anomaly_reason'] = '数据量过少，不足以构成统计学分布，默认正常放行。'
        return cleaned_data

    # 计算均值和标准差 (Z-Score需要)
    scores = [dp[metrics_key] for dp in cleaned_data]
    mean = sum(scores) / n
    variance = sum((x - mean) ** 2 for x in scores) / (n - 1)
    std_dev = math.sqrt(variance) if variance > 0 else 0.0

    # 计算 IQR (四分位距需要)
    sorted_scores = sorted(scores)
    q1_idx = max(0, int(n * 0.25))
    q3_idx = min(n - 1, int(n * 0.75))
    q1 = sorted_scores[q1_idx]
    q3 = sorted_scores[q3_idx]
    iqr = q3 - q1
    median = sorted_scores[int(n * 0.5)]

    for dp in cleaned_data:
        val = dp[metrics_key]

        # Z-Score：数值偏离均值的标准差倍数
        z_score = abs((val - mean) / std_dev) if std_dev > 0 else 0.0

        # IQR deviation：数值偏离中位数的IQR倍数
        iqr_dev = abs(val - median) / iqr if iqr > 0 else 0.0

        # 异常判断逻辑：
        # 统计学上，Z-Score > 2.17 约对应正态分布的 Top 3%
        # Z-Score > 1.64 约对应 Top 10%
        # 结合 IQR 提升对非正态分布偏态数据的鲁棒性

        is_top_3_percent = z_score > 2.17 or iqr_dev > 2.5
        is_top_10_percent = z_score > 1.64 or iqr_dev > 1.5

        if is_top_3_percent:
            dp['anomaly_color'] = 'Red'
            dp['anomaly_reason'] = '该设定参数极其离谱（处于前3%极度异常范围），强行生成极可能导致三视图肢体崩坏或表情扭曲，请务必人工重新确认。'
        elif is_top_10_percent:
            dp['anomaly_color'] = 'Yellow'
            dp['anomaly_reason'] = '参数略微偏离正常人群（边缘10%），可能导致角色特征细微不稳定，建议扫一眼。'
        else:
            dp['anomaly_color'] = 'Green'
            dp['anomaly_reason'] = '设定参数在97%正常分布范围内，静默放行，直接提交生成。'

    return cleaned_data
