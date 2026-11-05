import math
from typing import Dict, Any, Tuple

def clean_numeric(val: Any, default: float) -> float:
    """
    Cleans numeric values by replacing None, NaN, Inf, or unparseable values with a default.
    """
    if val is None:
        return float(default)
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return float(default)
        return float(val)
    try:
        val_float = float(val)
        if math.isnan(val_float) or math.isinf(val_float):
            return float(default)
        return val_float
    except (ValueError, TypeError):
        return float(default)

def format_export_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Formats vertical keyframe compositor data, enforcing 1080x1920 resolution,
    cleaning dirty data (NaN/None), setting comments=0, and generating a 3-line minimalist report.

    Args:
        data: The raw input dictionary containing rendering parameters.

    Returns:
        A tuple of (formatted_export_data, report_string).
    """
    if not isinstance(data, dict):
        data = {}

    export_data: Dict[str, Any] = {}

    # Enforce 1080x1920 vertical format
    export_data['resolution'] = {
        'width': 1080,
        'height': 1920
    }

    # Ensure export data has 0 comments (zero annotation pure export)
    export_data['comments'] = 0

    # Process and heal numeric fields for light effect and speedline
    export_data['speedline_intensity'] = clean_numeric(data.get('speedline_intensity'), 0.5)
    export_data['light_effect_opacity'] = clean_numeric(data.get('light_effect_opacity'), 0.8)

    # Process double-layer stroke subtitle
    subtitle = data.get('subtitle')
    if not isinstance(subtitle, dict):
        subtitle = {}

    export_data['subtitle'] = {
        'text': str(subtitle.get('text')) if subtitle.get('text') else "默认字幕",
        'inner_stroke_width': clean_numeric(subtitle.get('inner_stroke_width'), 2.0),
        'outer_stroke_width': clean_numeric(subtitle.get('outer_stroke_width'), 4.0),
        'font_size': clean_numeric(subtitle.get('font_size'), 72.0)
    }

    # Additional state
    export_data['export_status'] = "SUCCESS"

    # Generate exactly 3 lines of minimalist report for WeChat/Feishu one-click copy
    report_lines = [
        f"【渲染完成】1080x1920竖屏国漫关键帧已导出，批注清理完毕（comments={export_data['comments']}）。",
        f"【特效参数】光效透明度：{export_data['light_effect_opacity']:.2f} | 速度线强度：{export_data['speedline_intensity']:.2f}",
        f"【字幕压制】「{export_data['subtitle']['text']}」（字号{export_data['subtitle']['font_size']:.0f}，内描边{export_data['subtitle']['inner_stroke_width']:.1f}，外描边{export_data['subtitle']['outer_stroke_width']:.1f}）"
    ]
    report = "\n".join(report_lines)

    return export_data, report
