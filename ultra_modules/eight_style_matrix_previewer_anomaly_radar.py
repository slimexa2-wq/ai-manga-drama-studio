import math
from typing import Dict, List, Any, Optional

class EightStyleAnomalyRadar:
    """
    EightStyleAnomalyRadar identifies statistical anomalies in style distributions.
    It highlights the top 3% of anomalous items using Z-Score and IQR.
    """

    def __init__(self):
        self.default_value = 0.0

    def _clean_value(self, val: Any) -> float:
        try:
            float_val = float(val)
            if math.isnan(float_val) or math.isinf(float_val):
                return self.default_value
            return float_val
        except (ValueError, TypeError):
            return self.default_value

    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        n = len(values)
        if n == 0:
            return {'mean': 0.0, 'std_dev': 0.0, 'q1': 0.0, 'q3': 0.0, 'iqr': 0.0}

        mean = sum(values) / n

        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)

        sorted_values = sorted(values)

        def get_percentile(p: float) -> float:
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return sorted_values[int(k)]
            d0 = sorted_values[int(f)] * (c - k)
            d1 = sorted_values[int(c)] * (k - f)
            return d0 + d1

        q1 = get_percentile(0.25)
        q3 = get_percentile(0.75)
        iqr = q3 - q1

        return {
            'mean': mean,
            'std_dev': std_dev,
            'q1': q1,
            'q3': q3,
            'iqr': iqr
        }

    def analyze_styles(self, data: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Analyzes style metrics, calculates statistics, and categorizes into Red (Top 3%), Yellow, and Green.
        """
        if data is None:
            data = []

        if not isinstance(data, list):
            data = []

        cleaned_data = []
        for item in data:
            if not isinstance(item, dict):
                continue

            style_name = str(item.get('style_name', 'Unknown'))
            raw_value = item.get('metric_value', self.default_value)

            cleaned_value = self._clean_value(raw_value)

            cleaned_data.append({
                'style_name': style_name,
                'metric_value': cleaned_value,
                'original_item': item
            })

        if not cleaned_data:
            return []

        values = [item['metric_value'] for item in cleaned_data]
        stats = self._calculate_stats(values)

        mean = stats['mean']
        std_dev = stats['std_dev']
        q1 = stats['q1']
        q3 = stats['q3']
        iqr = stats['iqr']

        # Upper bounds
        iqr_upper_bound = q3 + 1.5 * iqr
        z_score_threshold = 2.5 # Approximate for top ~1-3% depending on distribution

        results = []

        # To determine top 3%, we need to rank them.
        # But we also have thresholds. If N is small, top 3% is 0 items.
        # We will use Z-score > 2.5 OR IQR upper bound to flag anomalies,
        # AND enforce that only the actual top 3% gets red.
        # Wait, the requirement: "自动高亮真正需要人工关注的Top 3%异常项并给出大白话原因"
        # Let's calculate Z-score and sort by deviation to find top 3%.

        n = len(cleaned_data)
        top_3_count = max(1, math.ceil(n * 0.03)) if n >= 10 else (1 if n >= 3 else 0)

        # Calculate scores
        for item in cleaned_data:
            val = item['metric_value']
            z_score = 0.0
            if std_dev > 0:
                z_score = (val - mean) / std_dev
            item['z_score'] = z_score
            item['iqr_dev'] = val - iqr_upper_bound

        # Sort to find top 3% most extreme (highest values)
        # Assuming anomaly is high value
        sorted_by_z = sorted(cleaned_data, key=lambda x: x['z_score'], reverse=True)
        top_3_items = sorted_by_z[:top_3_count] if top_3_count > 0 else []
        top_3_ids = {id(item) for item in top_3_items}

        for item in cleaned_data:
            val = item['metric_value']
            z_score = item['z_score']

            is_top_3 = id(item) in top_3_ids
            is_anomaly = is_top_3 and (z_score > 2.0 or val > iqr_upper_bound)

            # Red criteria: top 3% and significantly above average (z>2.0 or val>iqr_upper_bound)
            if is_anomaly:
                color = 'Red'
                reason = f"数值极高，超过常规范围，Z-Score为{z_score:.2f}，属于Top 3%异常，请重点关注！"
            # Yellow criteria: above IQR upper bound or Z-score > 1.5
            elif z_score > 1.5 or val > iqr_upper_bound:
                color = 'Yellow'
                reason = "数值偏高，但尚未达到严重异常级别，可轻度关注。"
            else:
                color = 'Green'
                reason = "数值处于正常范围内，无需处理。"

            res = {
                'style_name': item['style_name'],
                'metric_value': val,
                'color_marker': color,
                'reason': reason,
                'z_score': round(z_score, 4)
            }
            results.append(res)

        return results

if __name__ == '__main__': # pragma: no cover
    radar = EightStyleAnomalyRadar()
    print(radar.analyze_styles([{'style_name': 'xianxia', 'metric_value': 95}]))
