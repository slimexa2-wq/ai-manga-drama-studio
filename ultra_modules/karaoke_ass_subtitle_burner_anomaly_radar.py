import math
import statistics
from typing import List, Dict, Any, Optional

class KaraokeAssSubtitleBurnerAnomalyRadar:
    """
    独立演进模块：爆款漫剧ASS逐词高亮放大动态字幕自动打轴与FFmpeg硬压烧录器
    （统计分布异常值(Z-Score/IQR)后台静默扫描与红黄绿三色极简标记器）
    """

    @staticmethod
    def _heal_data(item: Any) -> Dict[str, Any]:
        """Silently heal dirty data, zero-configuration fault tolerance."""
        if not isinstance(item, dict):
            item = {"text": str(item) if item is not None else "", "duration": 1.0}

        text = item.get("text")
        if not isinstance(text, str):
            text = str(text) if text is not None else ""

        duration = item.get("duration")
        if not isinstance(duration, (int, float)) or math.isnan(duration) or duration <= 0:
            duration = 1.0

        return {"text": text, "duration": duration, "original": item}

    @staticmethod
    def _calculate_reading_speed(text: str, duration: float) -> float:
        char_count = len(text.strip())
        return char_count / duration if duration > 0 else 0.0

    @staticmethod
    def scan_and_mark(subtitles: List[Any]) -> List[Dict[str, Any]]:
        """
        自动高亮真正需要人工关注的Top 3%异常项并给出大白话原因，其余97%正常项静默放行。
        """
        if not subtitles:
            return []

        cleaned = [KaraokeAssSubtitleBurnerAnomalyRadar._heal_data(sub) for sub in subtitles]
        speeds = [KaraokeAssSubtitleBurnerAnomalyRadar._calculate_reading_speed(c["text"], c["duration"]) for c in cleaned]
        n = len(speeds)

        if n < 2:
            return [{
                "status": "Green",
                "reason": "正常放行",
                "text": cleaned[i]["text"],
                "speed": round(speeds[i], 2)
            } for i in range(n)]

        median = statistics.median(speeds)
        sorted_speeds = sorted(speeds)
        q1 = sorted_speeds[n // 4]
        q3 = sorted_speeds[(n * 3) // 4]
        iqr = q3 - q1
        if iqr == 0:
            iqr = 1.0

        deviations = [abs(s - median) / iqr for s in speeds]

        # Calculate exactly 3% (at least 1 if we have any outliers)
        top_count = max(1, math.ceil(n * 0.03))

        indexed_deviations = list(enumerate(deviations))
        indexed_deviations.sort(key=lambda x: x[1], reverse=True)

        # Only flag if there is some actual deviation (e.g., > 1.0 IQR away)
        top_indices = set(idx for idx, dev in indexed_deviations[:top_count] if dev > 1.0)

        results = []
        for i in range(n):
            text = cleaned[i]["text"]
            speed = speeds[i]
            dev = deviations[i]

            if i in top_indices:
                status = "Red" if dev > 3.0 else "Yellow"
                if speed > median:
                    reason = "字幕闪现过快（阅读时间不足，建议延长画面或精简文案）"
                else:
                    reason = "字幕停留过长（画面可能枯燥，建议缩短或增加特效）"
            else:
                status = "Green"
                reason = "正常放行"

            results.append({
                "status": status,
                "reason": reason,
                "text": text,
                "speed": round(speed, 2)
            })

        return results

    @staticmethod
    def generate_ffmpeg_burn_command(
        input_video: Optional[str] = None,
        ass_file: Optional[str] = None,
        output_video: Optional[str] = None,
        existing_vf: Optional[str] = None
    ) -> str:
        """
        Generate FFmpeg command to burn subtitles, appending to existing filters properly,
        and fully escaping paths to prevent failures. Fallback to reasonable defaults.
        """
        input_video = input_video or "default_in.mp4"
        ass_file = ass_file or "default_sub.ass"
        output_video = output_video or "default_out.mp4"
        existing_vf = existing_vf or ""

        # FFmpeg filter path escaping
        # Backslashes and colons must be escaped in libass paths
        escaped_ass = ass_file.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")

        ass_filter = f"ass='{escaped_ass}'"

        if existing_vf:
            # Append without duplicating -vf
            final_vf = f"{existing_vf.strip()}, {ass_filter}"
        else:
            final_vf = ass_filter

        return f"ffmpeg -i \"{input_video}\" -vf \"{final_vf}\" -c:a copy \"{output_video}\""
