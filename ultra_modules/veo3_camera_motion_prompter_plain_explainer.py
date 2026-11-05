import json
from typing import Any, Dict

class Veo3CameraMotionPrompterPlainExplainer:
    """
    Google Veo 3 / Sora 2 专属电影级推拉摇移环绕运镜 Prompt 结构化编译器。
    将复杂的后台运镜参数转化为普通业务人员一秒看懂的大白话结论卡。
    """

    def _sanitize_data(self, camera_data: Any) -> Dict[str, Any]:
        """
        零配置容错与脏数据自愈：
        对输入数据进行极致清洗，缺参自动设合理默认值。
        """
        if not isinstance(camera_data, dict):
            camera_data = {}

        sanitized = {
            'pan': 0.0,
            'tilt': 0.0,
            'zoom': 0.0,
            'roll': 0.0,
            'speed': 1.0,
            'focus': '自动对焦',
        }

        # Helper to convert to float safely
        def to_float(val: Any, default: float = 0.0) -> float:
            try:
                if val is None:
                    return default
                return float(val)
            except (ValueError, TypeError):
                return default

        sanitized['pan'] = to_float(camera_data.get('pan', 0.0))
        sanitized['tilt'] = to_float(camera_data.get('tilt', 0.0))
        sanitized['zoom'] = to_float(camera_data.get('zoom', 0.0))
        sanitized['roll'] = to_float(camera_data.get('roll', 0.0))

        # Speed logic with self-healing
        speed_val = camera_data.get('speed', 1.0)
        if isinstance(speed_val, str):
            val_lower = speed_val.lower().strip()
            if val_lower == 'slow':
                sanitized['speed'] = 0.5
            elif val_lower == 'fast':
                sanitized['speed'] = 2.0
            else:
                sanitized['speed'] = to_float(speed_val, 1.0)
        else:
            sanitized['speed'] = to_float(speed_val, 1.0)

        # Speed boundary checks (must be positive)
        if sanitized['speed'] <= 0:
            sanitized['speed'] = 1.0

        # Focus logic with self-healing
        focus_val = camera_data.get('focus', '自动对焦')
        if focus_val is None:
            sanitized['focus'] = '自动对焦'
        else:
            sanitized['focus'] = str(focus_val).strip() or '自动对焦'

        return sanitized

    def _generate_description(self, sanitized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将结构化清洗后的数据翻译为大白话解析字典。
        """
        descriptions = []

        # Pan (Horizontal)
        pan = sanitized_data['pan']
        if pan > 0:
            descriptions.append(f"镜头向右平移（强度: {pan:.1f}）")
        elif pan < 0:
            descriptions.append(f"镜头向左平移（强度: {abs(pan):.1f}）")

        # Tilt (Vertical)
        tilt = sanitized_data['tilt']
        if tilt > 0:
            descriptions.append(f"镜头向上摇摄（强度: {tilt:.1f}）")
        elif tilt < 0:
            descriptions.append(f"镜头向下摇摄（强度: {abs(tilt):.1f}）")

        # Zoom
        zoom = sanitized_data['zoom']
        if zoom > 0:
            descriptions.append(f"镜头推进，画面放大（强度: {zoom:.1f}）")
        elif zoom < 0:
            descriptions.append(f"镜头拉远，画面缩小（强度: {abs(zoom):.1f}）")

        # Roll
        roll = sanitized_data['roll']
        if roll > 0:
            descriptions.append(f"镜头向右侧翻滚倾斜（强度: {roll:.1f}）")
        elif roll < 0:
            descriptions.append(f"镜头向左侧翻滚倾斜（强度: {abs(roll):.1f}）")

        if not descriptions:
            descriptions.append("镜头保持固定，无移动")

        # Speed
        speed = sanitized_data['speed']
        speed_desc = "正常"
        if speed < 0.8:
            speed_desc = "缓慢"
        elif speed > 1.2:
            speed_desc = "快速"

        focus = sanitized_data['focus']

        summary = f"当前运镜模式为【{speed_desc}】节奏。主要动作包括：{'，'.join(descriptions)}。焦点策略：{focus}。"
        return {
            "summary": summary,
            "details": descriptions,
            "speed": speed_desc,
            "focus": focus,
            "raw_sanitized": sanitized_data
        }

    def explain(self, camera_data: Dict[str, Any], format: str = 'markdown') -> str:
        """
        核心暴露方法：输入可能很脏的后台运镜参数，输出一秒看懂的大白话解析卡片。
        支持 markdown, html, json。
        """
        sanitized = self._sanitize_data(camera_data)
        desc_data = self._generate_description(sanitized)

        fmt = str(format).lower().strip() if format is not None else 'markdown'
        if fmt not in ['markdown', 'html', 'json']:
            fmt = 'markdown'

        if fmt == 'json':
            return json.dumps(desc_data, ensure_ascii=False, indent=2)
        elif fmt == 'html':
            details_html = "".join([f"<li>{d}</li>" for d in desc_data['details']])
            return f"""<div class="camera-motion-card">
  <h3>🎬 Veo 3 运镜大白话解析卡</h3>
  <p><strong>【一句话概述】</strong> {desc_data['summary']}</p>
  <h4>动作拆解：</h4>
  <ul>
    {details_html}
  </ul>
  <p><strong>运镜节奏:</strong> {desc_data['speed']} | <strong>焦点:</strong> {desc_data['focus']}</p>
</div>"""
        else: # markdown
            details_md = "\n".join([f"- {d}" for d in desc_data['details']])
            return f"""### 🎬 Veo 3 运镜大白话解析卡

**【一句话概述】**
{desc_data['summary']}

**【动作拆解】**
{details_md}

---
*运镜节奏:* {desc_data['speed']} | *焦点策略:* {desc_data['focus']}
"""
