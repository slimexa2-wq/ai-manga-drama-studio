import json
from typing import Dict, Any, Optional

class VerticalKeyframeCompositorPlainExplainer:
    def __init__(self, default_lighting: str = "柔和自然光", default_speedline: str = "无", default_subtitle_style: str = "默认双层描边"):
        self.default_lighting = default_lighting
        self.default_speedline = default_speedline
        self.default_subtitle_style = default_subtitle_style

    def process(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processes complex backend parameters into plain language explanation cards.
        Features zero-config fault tolerance and dirty data healing.
        """
        if params is None or not isinstance(params, dict):
            params = {}

        # Self-healing & extracting parameters
        lighting = str(params.get("lighting_effect") or self.default_lighting).strip()
        if not lighting or lighting == "None":
            lighting = self.default_lighting

        speedline = str(params.get("speed_line") or self.default_speedline).strip()
        if not speedline or speedline == "None":
            speedline = self.default_speedline

        subtitle = str(params.get("subtitle_style") or self.default_subtitle_style).strip()
        if not subtitle or subtitle == "None":
            subtitle = self.default_subtitle_style

        # Generate Plain Text Explanation
        explanation_text = f"【1080x1920 竖屏关键帧合成参数说明】\\n"
        explanation_text += f"- 光效渲染: {lighting}\\n"
        explanation_text += f"- 速度线合成: {speedline}\\n"
        explanation_text += f"- 字幕压制: {subtitle}"

        # Generate Markdown
        markdown_text = f"### 1080x1920 竖屏关键帧合成\\n* **光效渲染**: {lighting}\\n* **速度线合成**: {speedline}\\n* **字幕压制**: {subtitle}"

        # Generate HTML
        html_text = f"<div class='compositor-card'><h3>1080x1920 竖屏关键帧合成</h3><ul><li><b>光效渲染</b>: {lighting}</li><li><b>速度线合成</b>: {speedline}</li><li><b>字幕压制</b>: {subtitle}</li></ul></div>"

        # Generate JSON
        json_data = {
            "title": "1080x1920 竖屏关键帧合成",
            "resolution": "1080x1920",
            "lighting_effect": lighting,
            "speed_line": speedline,
            "subtitle_style": subtitle
        }

        return {
            "plain_text": explanation_text,
            "markdown": markdown_text,
            "html": html_text,
            "json": json.dumps(json_data, ensure_ascii=False)
        }

def run_explainer_pipeline(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Simplified one-click frontend function for the plain explainer.
    Zero configuration, complete fault-tolerance.
    """
    explainer = VerticalKeyframeCompositorPlainExplainer()
    return explainer.process(params)
