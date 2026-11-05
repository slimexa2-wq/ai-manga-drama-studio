import json
from typing import Any, Dict, List, Optional, Union

class EgoDualCloudDispatcherPlainExplainer:
    """
    ego-browser免API费后台并发投递Google 20x Ultra与ChatGPT Plus任务编排器
    （前端极简大白话一页纸摘要与可视化卡片导出）。

    后台可能产生非常复杂的执行链路和数据，本类负责将它们转化为普通业务人员
    1秒看懂的大白话结论卡，支持 HTML/JSON/Markdown 格式导出。
    """

    def __init__(self, fallback_title: str = "任务执行摘要"):
        # Zero-configuration fault tolerance: assign default value
        self.fallback_title = fallback_title if fallback_title and isinstance(fallback_title, str) else "任务执行摘要"

    def _heal_dirty_data(self, data: Any) -> Dict[str, Any]:
        """Silently cleans dirty data to ensure zero crash tolerance."""
        if not isinstance(data, dict):
            # If data is completely invalid, fallback to an empty but valid dict
            return {"status": "unknown", "message": str(data) if data is not None else "无数据", "models": [], "task": "未指定任务", "duration_sec": 0.0}

        cleaned = {}
        # Ensure status is string and valid
        raw_status = data.get("status")
        if isinstance(raw_status, str):
            cleaned["status"] = raw_status.strip().lower()
        else:
            cleaned["status"] = "unknown"

        # Ensure models data is a list of dicts
        raw_models = data.get("models")
        if isinstance(raw_models, list):
            cleaned["models"] = [m for m in raw_models if isinstance(m, dict)]
        else:
            cleaned["models"] = []

        # Ensure task details
        raw_task = data.get("task")
        cleaned["task"] = str(raw_task) if raw_task is not None else "未指定任务"

        # Ensure duration is numeric
        raw_duration = data.get("duration_sec")
        try:
            cleaned["duration_sec"] = float(raw_duration) if raw_duration is not None else 0.0
        except (ValueError, TypeError):
            cleaned["duration_sec"] = 0.0

        return cleaned

    def explain(self, raw_data: Any, format_type: str = "markdown") -> str:
        """
        Converts complex background calculation results into plain language summary cards.

        Args:
            raw_data: The complex output from the task dispatcher.
            format_type: Output format ("html", "json", "markdown"). Default is "markdown".
        """
        # Self-healing format type
        format_type = format_type.lower().strip() if isinstance(format_type, str) else "markdown"
        if format_type not in ["html", "json", "markdown"]:
            format_type = "markdown"

        data = self._heal_dirty_data(raw_data)

        status_cn = {
            "success": "✅ 成功",
            "failed": "❌ 失败",
            "partial": "⚠️ 部分成功",
            "unknown": "❓ 未知状态"
        }.get(data["status"], "❓ 未知状态")

        model_summaries = []
        for m in data["models"]:
            m_name = m.get("name", "未知模型")
            m_status = "成功" if str(m.get("status")).lower() == "success" else "失败"
            model_summaries.append(f" - {m_name}: {m_status}")

        if not model_summaries:
            model_summaries = [" - 未调用任何模型"]

        summary = {
            "title": self.fallback_title,
            "overall_status": status_cn,
            "task_description": data["task"],
            "duration": f"{data['duration_sec']:.1f} 秒",
            "model_details": model_summaries
        }

        if format_type == "json":
            return json.dumps(summary, ensure_ascii=False, indent=2)

        elif format_type == "html":
            models_html = "".join([f"<li>{m}</li>" for m in summary["model_details"]])
            html_content = (
                f"<div class='summary-card'>\n"
                f"  <h1>{summary['title']}</h1>\n"
                f"  <p><strong>状态:</strong> {summary['overall_status']}</p>\n"
                f"  <p><strong>任务:</strong> {summary['task_description']}</p>\n"
                f"  <p><strong>耗时:</strong> {summary['duration']}</p>\n"
                f"  <h3>模型调用详情:</h3>\n"
                f"  <ul>\n{models_html}\n  </ul>\n"
                f"</div>"
            )
            return html_content

        else: # markdown
            models_md = "\n".join(summary["model_details"])
            md_content = (
                f"# {summary['title']}\n\n"
                f"- **状态:** {summary['overall_status']}\n"
                f"- **任务:** {summary['task_description']}\n"
                f"- **耗时:** {summary['duration']}\n\n"
                f"### 模型调用详情:\n{models_md}"
            )
            return md_content
