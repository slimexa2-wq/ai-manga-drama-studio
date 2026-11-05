import json
from typing import Dict, Any, Optional

class EightStyleMatrixPreviewerPlainExplainer:
    def __init__(self):
        self.default_message = "系统处理中或遇到未知数据，建议重新提交一次。"

    def explain(self, backend_result: Optional[Dict[str, Any]] = None, format_type: str = "json") -> str:
        """
        Translates complex backend output to plain language conclusion cards.
        Handles missing parameters, dirty data, and fallbacks cleanly.
        """
        # 1. Dirty data self-healing and missing parameter fallback
        if not backend_result or not isinstance(backend_result, dict):
            return self._format_output({"title": "结果为空", "summary": self.default_message, "styles": []}, format_type)

        # 2. Extract core information safely
        total = backend_result.get("total", 0)
        completed = backend_result.get("completed", 0)
        failed = backend_result.get("failed", 0)
        results = backend_result.get("results", [])

        if not isinstance(results, list):
            results = []

        # 3. Generate simple summaries
        if total == 0:
            return self._format_output({
                "title": "暂无处理任务",
                "summary": "您尚未提交任何内容进行画风对比。",
                "styles": []
            }, format_type)

        if failed > 0 and completed == 0:
            return self._format_output({
                "title": "任务处理失败",
                "summary": f"抱歉，提交的 {total} 个任务未能成功生成对比，请检查输入后重试。",
                "styles": []
            }, format_type)

        # Process successful results to extract styles
        style_previews = []
        for res in results:
            if not isinstance(res, dict) or res.get("status") != "success":
                continue

            previews = res.get("previews", {})
            if isinstance(previews, dict):
                for style, preview_text in previews.items():
                    style_previews.append(f"【{style}】: {preview_text}")

        # Remove duplicates while preserving order
        seen = set()
        unique_styles = []
        for sp in style_previews:
            if sp not in seen:
                seen.add(sp)
                unique_styles.append(sp)

        summary_text = f"成功为您生成了 {completed} 条内容的画风对比"
        if failed > 0:
            summary_text += f"，其中有 {failed} 条处理失败，但不影响成功部分查看"
        summary_text += "！一秒钟浏览如下："

        output_data = {
            "title": "8大画风对比一键摘要",
            "summary": summary_text,
            "styles": unique_styles
        }

        return self._format_output(output_data, format_type)

    def _format_output(self, data: Dict[str, Any], format_type: str) -> str:
        format_type = str(format_type).lower().strip() if isinstance(format_type, str) else "json"

        if format_type == "markdown":
            md = f"# {data.get('title', '')}\n\n**摘要**：{data.get('summary', '')}\n\n"
            if data.get('styles'):
                md += "## 画风预览卡片\n"
                for style in data.get('styles', []):
                    md += f"- {style}\n"
            else:
                md += "*暂无画风数据*\n"
            return md

        elif format_type == "html":
            html = f"<div><h1>{data.get('title', '')}</h1><p><strong>摘要</strong>：{data.get('summary', '')}</p>"
            if data.get('styles'):
                html += "<h2>画风预览卡片</h2><ul>"
                for style in data.get('styles', []):
                    html += f"<li>{style}</li>"
                html += "</ul>"
            else:
                html += "<p><em>暂无画风数据</em></p>"
            html += "</div>"
            return html

        else: # Default json
            return json.dumps(data, ensure_ascii=False, indent=2)

def explain_backend_result_to_plain_language(backend_result: Optional[Dict[str, Any]] = None, format_type: str = "json") -> str:
    """
    一键直达、零确认弹窗的前端极简接口。
    """
    explainer = EightStyleMatrixPreviewerPlainExplainer()
    return explainer.explain(backend_result=backend_result, format_type=format_type)
