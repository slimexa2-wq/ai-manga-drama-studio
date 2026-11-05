import math
from typing import List, Dict, Any, Union

class Veo3CameraMotionPrompterAnomalyRadar:
    """
    Google Veo 3 & Sora 2 exclusive cinematic camera motion prompt structural compiler.
    Features IQR/Z-Score anomaly scanning, 97% silent pass-through, and top 3% human-attention highlighting.
    """

    @staticmethod
    def _calculate_percentile(data: List[float], percentile: float) -> float:
        n = len(data)
        if n == 0:
            return 0.0
        sorted_data = sorted(data)
        k = (n - 1) * percentile / 100.0
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        d0 = sorted_data[int(f)] * (c - k)
        d1 = sorted_data[int(c)] * (k - f)
        return d0 + d1

    @classmethod
    def compile_and_scan(cls, prompts_data: Union[List[Dict[str, Any]], Dict[str, Any], Any] = None) -> List[Dict[str, Any]]:
        # 1. Zero-configuration auto-fallback
        if prompts_data is None:
            prompts_data = [{}]
        if not isinstance(prompts_data, list):
            prompts_data = [prompts_data]
        if not prompts_data:
            prompts_data = [{}]

        processed = []
        for item in prompts_data:
            # 2. Dirty data self-healing
            if not isinstance(item, dict):
                item = {"subject": str(item)}

            subject = item.get("subject")
            if subject is not None:
                subject = str(subject)
            if not subject or not subject.strip():
                subject = "a highly detailed cinematic shot, 8k resolution"

            motion = item.get("motion", "cinematic pan")
            if motion is not None:
                motion = str(motion).lower().strip()
            if not motion or motion == "none":
                motion = "cinematic pan"

            raw_speed = item.get("speed", 1.0)
            try:
                speed = float(raw_speed)
                if math.isnan(speed) or math.isinf(speed) or speed <= 0:
                    speed = 1.0
            except (ValueError, TypeError):
                speed = 1.0

            # Complexity score calculation (proxy for anomaly detection)
            # A very long subject or an extreme speed will spike the score.
            complexity = len(subject) * speed
            if "zoom" in motion or "dolly" in motion:
                complexity *= 1.2
            if "extreme" in motion:
                complexity *= 1.5

            compiled_prompt = f"[Veo 3 / Sora 2 Optimized] {subject.title()} - Camera Motion: {motion.title()} at {speed}x speed."

            processed.append({
                "compiled_prompt": compiled_prompt,
                "complexity": complexity,
                "original": item
            })

        scores = [p["complexity"] for p in processed]
        n = len(scores)

        if n == 0:
            return []

        mean = sum(scores) / n
        std_dev = math.sqrt(sum((x - mean)**2 for x in scores) / n)

        q1 = cls._calculate_percentile(scores, 25)
        q3 = cls._calculate_percentile(scores, 75)
        iqr = q3 - q1
        upper_bound = q3 + 1.5 * iqr

        p97 = cls._calculate_percentile(scores, 97)

        results = []
        for p in processed:
            score = p["complexity"]

            # Anomaly checks: Top 3% AND statistically anomalous (IQR or Z-Score)
            is_top_3 = (score >= p97)
            is_iqr_outlier = (score > upper_bound)
            is_z_outlier = (std_dev > 0 and (score - mean) / std_dev > 2.0)

            # If dataset is small, 97th percentile might just be the max element.
            # We strictly only flag it if it's statistically anomalous to avoid false positives.
            # And also require length to be somewhat meaningful to not flag everything in small batches
            if is_top_3 and (is_iqr_outlier or is_z_outlier) and n > 5:
                marker = "🔴"
                reason = "运镜复杂度或参数异常极高（处于Top 3%异常分布），极易导致大模型生成崩坏，需人工重点核查！"
                requires_attention = True
            elif score > q3 and score > mean and n > 5:
                marker = "🟡"
                reason = "参数略高于常规水平，但已由后台静默兼容并放行。"
                requires_attention = False
            else:
                marker = "🟢"
                reason = "常规标准运镜指令，参数完全合规，自动静默放行。"
                requires_attention = False

            results.append({
                "compiled_prompt": p["compiled_prompt"],
                "complexity_score": score,
                "marker": marker,
                "reason": reason,
                "requires_attention": requires_attention
            })

        return results
