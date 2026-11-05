import math
import statistics

class PacingAnomalyRadar:
    """
    爽文剧本情绪曲线自动诊断与节奏加密器。
    用于后台静默扫描情绪曲线（压抑->蓄力->爆发打脸->悬念）的分布异常值（Z-Score）。
    自动高亮真正需要人工关注的Top 3%异常项并给出大白话原因，其余97%正常项静默放行。
    """

    def __init__(self):
        pass

    def _clean_data(self, data_points):
        cleaned = []
        original_indices = []
        for i, val in enumerate(data_points):
            if val is None:
                continue
            try:
                float_val = float(val)
                if not math.isnan(float_val) and not math.isinf(float_val):
                    cleaned.append(float_val)
                    original_indices.append(i)
            except (ValueError, TypeError):
                continue
        return cleaned, original_indices

    def analyze_pacing(self, data_points=None):
        """
        分析节奏曲线，返回分析结果。
        缺参自动设合理默认值，零配置容错。
        """
        if data_points is None:
            data_points = []

        cleaned_data, original_indices = self._clean_data(data_points)

        if not cleaned_data:
            return {
                "status": "success",
                "results": [],
                "message": "Empty or entirely invalid data, defaulting to empty results."
            }

        n = len(cleaned_data)

        if n < 2:
            return {
                "status": "success",
                "results": [{
                    "index": original_indices[i],
                    "value": val,
                    "z_score": 0.0,
                    "marker": "Green",
                    "explanation": "数据点不足，静默放行。"
                } for i, val in enumerate(cleaned_data)],
                "message": "Not enough data points to compute anomalies."
            }

        mean = statistics.mean(cleaned_data)
        try:
            stddev = statistics.stdev(cleaned_data)
        except statistics.StatisticsError:
            stddev = 0.0

        z_scores = [0.0 if stddev == 0 else (val - mean) / stddev for val in cleaned_data]

        # 计算Top 3%的数量
        top_k = math.ceil(n * 0.03)

        # 按Z-Score绝对值降序排序
        indexed_z_scores = list(enumerate(z_scores))
        indexed_z_scores.sort(key=lambda x: abs(x[1]), reverse=True)

        anomaly_indices = set()
        for i in range(min(top_k, n)):
            idx, z = indexed_z_scores[i]
            if abs(z) > 0:
                anomaly_indices.add(idx)

        results = []
        for i, (orig_idx, val, z) in enumerate(zip(original_indices, cleaned_data, z_scores)):
            if i in anomaly_indices:
                if z > 0:
                    marker = "Red"
                    explanation = "峰值过高：情绪爆发过于突兀，可能导致逻辑断裂，建议人工复核。"
                else:
                    marker = "Yellow"
                    explanation = "谷值过低：剧情过于压抑或拖沓，存在读者弃文风险。"
            else:
                marker = "Green"
                explanation = "节奏正常，静默放行。"

            results.append({
                "index": orig_idx,
                "value": val,
                "z_score": z,
                "marker": marker,
                "explanation": explanation
            })

        return {
            "status": "success",
            "results": results,
            "message": f"Processed {n} data points, found {len(anomaly_indices)} anomalies."
        }
