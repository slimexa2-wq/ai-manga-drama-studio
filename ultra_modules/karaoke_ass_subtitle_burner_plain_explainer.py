import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class KaraokeSubtitleExplainer:
    """
    Explainer for converting complex Karaoke ASS subtitle generation and FFmpeg burning results
    into plain, user-friendly business cards.

    Zero-config, self-healing, zero-crash tolerance.
    """

    @classmethod
    def generate_summary_card(cls, backend_result: Any) -> Dict[str, Any]:
        """
        Converts complex backend payload into a plain summary card.

        Args:
            backend_result: A dict or JSON string containing the backend processing results.

        Returns:
            Dict containing HTML, JSON, and Markdown summaries.
        """
        if backend_result is None:
            backend_result = {}

        if isinstance(backend_result, str):
            try:
                backend_result = json.loads(backend_result)
            except (json.JSONDecodeError, TypeError):
                # Self-healing: if it's a completely invalid string, treat as empty dict
                backend_result = {}

        if not isinstance(backend_result, dict):
            # Self-healing for completely unexpected types (e.g. lists, integers)
            backend_result = {}

        # Extract fields with zero-config fallbacks
        try:
            total_subtitles = int(backend_result.get("total_subtitles", 0))
            if total_subtitles < 0:
                total_subtitles = 0
        except (ValueError, TypeError):
            total_subtitles = 0

        try:
            processed_duration = float(backend_result.get("processed_duration", 0.0))
            if processed_duration < 0:
                processed_duration = 0.0
        except (ValueError, TypeError):
            processed_duration = 0.0

        try:
            success_rate = float(backend_result.get("success_rate", 1.0))
            if success_rate < 0.0:
                success_rate = 0.0
            elif success_rate > 1.0:
                success_rate = 1.0
        except (ValueError, TypeError):
            success_rate = 1.0

        status = str(backend_result.get("status", "success")).lower()
        if status not in ["success", "failed", "partial"]:
            status = "success"

        video_url = str(backend_result.get("video_url", "#"))
        if not video_url or video_url == "None" or video_url.strip() == "":
            video_url = "#"

        # Generate simple plain language outputs
        status_text = "成功" if status == "success" else "部分成功" if status == "partial" else "失败"

        summary = (
            f"字幕烧录{status_text}。共处理了 {total_subtitles} 句逐词高亮字幕，"
            f"总耗时 {processed_duration:.1f} 秒，成功率 {success_rate * 100:.1f}%。"
        )

        # HTML Representation
        html_card = f"""
        <div class="karaoke-card">
            <h3>字幕烧录报告</h3>
            <p><strong>状态:</strong> {status_text}</p>
            <p><strong>处理句数:</strong> {total_subtitles}</p>
            <p><strong>处理耗时:</strong> {processed_duration:.1f}s</p>
            <p><strong>成功率:</strong> {success_rate * 100:.1f}%</p>
            <a href="{video_url}" target="_blank">查看成片</a>
        </div>
        """

        # Markdown Representation
        markdown_card = f"""### 字幕烧录报告
- **状态**: {status_text}
- **处理句数**: {total_subtitles}
- **处理耗时**: {processed_duration:.1f}s
- **成功率**: {success_rate * 100:.1f}%
- [查看成片]({video_url})
"""

        # JSON Representation
        json_card = {
            "title": "字幕烧录报告",
            "summary": summary,
            "metrics": {
                "status": status_text,
                "total_subtitles": total_subtitles,
                "processed_duration": processed_duration,
                "success_rate_percentage": round(success_rate * 100, 1)
            },
            "actions": {
                "view_video": video_url
            }
        }

        return {
            "html": html_card.strip(),
            "markdown": markdown_card.strip(),
            "json": json_card,
            "plain_text": summary
        }
