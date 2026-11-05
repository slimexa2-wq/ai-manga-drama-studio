import json

class CharacterDNALockerExplainer:
    """
    全剧角色视觉DNA跨集硬锁定器（前端极简大白话一页纸摘要与可视化卡片导出）。
    实现思路：
    - 接受发色、瞳色、服饰、画风后缀、固定Seed。
    - 自动清理脏数据（自动纠正非法类型、负数、空字符串），缺参提供默认兜底。
    - 导出一秒看懂的大白话JSON、Markdown、HTML卡片。
    """
    def __init__(self, hair_color=None, eye_color=None, clothing=None, style_suffix=None, fixed_seed=None):
        self.hair_color = self._clean_string(hair_color, "黑色")
        self.eye_color = self._clean_string(eye_color, "黑色")
        self.clothing = self._clean_string(clothing, "日常便服")
        self.style_suffix = self._clean_string(style_suffix, "二次元动漫风格")
        self.fixed_seed = self._clean_seed(fixed_seed, 42)

    def _clean_string(self, val, default):
        if val is None:
            return default
        # 对于复杂结构等明显脏数据，直接返回兜底
        if isinstance(val, (list, dict, tuple, set, bool)):
            return default

        try:
            cleaned = str(val).strip()
            # 过滤常见的无效字符串
            if not cleaned or cleaned.lower() in ("none", "null", "nan", "undefined", "nil"):
                return default
            return cleaned
        except Exception:
            return default

    def _clean_seed(self, val, default):
        if val is None:
            return default
        if isinstance(val, (list, dict, tuple, set, bool)):
            return default
        try:
            if isinstance(val, int):
                return abs(val)
            val_str = str(val).strip()
            if val_str.lstrip('-').isdigit():
                return abs(int(val_str))

            # 尝试转为数字，兼容字符串形式的浮点数如 "123.45" 变为 123
            val_int = int(float(val))
            # 自动治愈负数，取绝对值
            return abs(val_int)
        except (ValueError, TypeError):
            return default

    def to_dict(self):
        return {
            "hair_color": self.hair_color,
            "eye_color": self.eye_color,
            "clothing": self.clothing,
            "style_suffix": self.style_suffix,
            "fixed_seed": self.fixed_seed,
            "summary": f"该角色特征为【{self.hair_color}头发】，【{self.eye_color}眼睛】，身穿【{self.clothing}】。画风被限定为【{self.style_suffix}】，随机种子锁定为【{self.fixed_seed}】以保证跨集长效稳定连贯一致。"
        }

    def export_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def export_markdown(self):
        data = self.to_dict()
        return f"""# 🧑‍🎨 角色视觉DNA锁定卡

**💡 极简大白话总结**
> {data['summary']}

## 🧬 核心特征参数
- **发色**：{data['hair_color']}
- **瞳色**：{data['eye_color']}
- **服饰**：{data['clothing']}
- **画风后缀**：{data['style_suffix']}
- **固定Seed**：{data['fixed_seed']}
"""

    def export_html(self):
        data = self.to_dict()
        return f"""<div class="dna-card" style="border: 1px solid #ccc; padding: 20px; border-radius: 10px; font-family: sans-serif;">
    <h2 style="margin-top: 0;">🧑‍🎨 角色视觉DNA锁定卡</h2>
    <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #007bff; margin-bottom: 20px;">
        <strong>💡 极简大白话总结：</strong><br>
        {data['summary']}
    </div>
    <ul style="list-style-type: none; padding-left: 0;">
        <li><strong>发色：</strong> {data['hair_color']}</li>
        <li><strong>瞳色：</strong> {data['eye_color']}</li>
        <li><strong>服饰：</strong> {data['clothing']}</li>
        <li><strong>画风后缀：</strong> {data['style_suffix']}</li>
        <li><strong>固定Seed：</strong> {data['fixed_seed']}</li>
    </ul>
</div>"""
