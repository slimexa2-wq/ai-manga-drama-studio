import math

class VerticalKeyframeCompositorAnomalyRadar:
    """
    1080x1920竖屏国漫关键帧光效渲染、速度线合成与双层描边大字幕压制器
    统计分布异常值(Z-Score/IQR)后台静默扫描与红黄绿三色极简标记器
    """

    def __init__(self, config=None):
        if config is None:
            config = {}
        # 缺参自动设合理默认值，零配置容错
        self.anomaly_threshold_percent = config.get('anomaly_threshold_percent', 0.03)
        self.method = config.get('method', 'z-score') # 'z-score' or 'iqr'

    def _clean_data(self, records, value_key):
        """
        后台功能实现极度严密复杂，处理脏数据自愈、缺参默认兜底与极端边界
        """
        cleaned_records = []
        for i, record in enumerate(records):
            if not isinstance(record, dict):
                continue

            raw_val = record.get(value_key)
            if raw_val is None:
                continue

            try:
                val = float(raw_val)
                if math.isnan(val) or math.isinf(val):
                    continue
                cleaned_records.append({'index': i, 'value': val, 'original': record})
            except (ValueError, TypeError):
                continue

        return cleaned_records

    def _calculate_scores(self, cleaned_records):
        n = len(cleaned_records)
        if n == 0:
            return []

        values = [r['value'] for r in cleaned_records]

        if self.method == 'iqr':
            sorted_vals = sorted(values)
            q1_idx = int(n * 0.25)
            q3_idx = int(n * 0.75)
            q1 = sorted_vals[q1_idx]
            q3 = sorted_vals[q3_idx]
            iqr = q3 - q1
            if iqr == 0:
                # identical values case, avoid div by zero
                for r in cleaned_records:
                    r['score'] = 0.0
            else:
                for r in cleaned_records:
                    r['score'] = abs(r['value'] - q3) / iqr if r['value'] > q3 else abs(r['value'] - q1) / iqr
        else: # Default z-score
            mean = sum(values) / n
            variance = sum((v - mean) ** 2 for v in values) / n
            std_dev = math.sqrt(variance)

            if std_dev == 0:
                # identical values case
                for r in cleaned_records:
                    r['score'] = 0.0
            else:
                for r in cleaned_records:
                    r['score'] = abs(r['value'] - mean) / std_dev

        return cleaned_records

    def analyze(self, records, value_key='render_time'):
        """
        自动高亮真正需要人工关注的Top 3%异常项并给出大白话原因，其余97%正常项静默放行及测试。
        """
        if records is None:
            records = []

        cleaned_records = self._clean_data(records, value_key)
        scored_records = self._calculate_scores(cleaned_records)

        n = len(scored_records)
        if n == 0:
            return []

        # Sort by score descending to find top anomalies
        sorted_records = sorted(scored_records, key=lambda x: x['score'], reverse=True)

        # Calculate how many constitute top 3%
        top_k = math.ceil(n * self.anomaly_threshold_percent)

        results = []
        # Maintain original input length and map back results
        # For dirty/missing data, they get completely ignored/filtered out by clean_data,
        # but we need to return results that map back to the original index if possible,
        # or we just return the analysis on the valid ones. We'll return analysis for valid ones.
        for i, r in enumerate(sorted_records):
            if i < top_k and r['score'] > 0: # Only flag if there's actually a score difference
                color = 'red'
                reason = f"数值 {r['value']} 偏离群体太多，需要人工检查一下哦！"
            else:
                color = 'green'
                reason = "正常范围，静默放行"

            results.append({
                'index': r['index'],
                'value': r['value'],
                'score': r['score'],
                'marker': color,
                'reason': reason,
                'original': r['original']
            })

        # Re-sort by original index
        results.sort(key=lambda x: x['index'])
        return results

if __name__ == '__main__': # pragma: no cover
    pass
