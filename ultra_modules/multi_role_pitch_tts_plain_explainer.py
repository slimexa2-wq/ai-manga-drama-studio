import json

class MultiRolePitchTTSPlainExplainer:
    """
    将复杂的后台TTS配置（音高、语速、情感、时长）转换为业务人员可读的大白话结论卡。
    支持脏数据自愈、缺参默认兜底、以及多种输出格式（JSON/Markdown/HTML）。
    """
    def __init__(self):
        self.default_role = "未知角色"
        self.default_pitch = 1.0
        self.default_speed = 1.0
        self.default_emotion = "平静"
        self.default_duration_ms = 0

    def _to_float(self, val, default):
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def _to_int(self, val, default):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default

    def _sanitize_data(self, data):
        # 脏数据自愈：处理非列表情况
        if data is None:
            return []

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            # 尝试从字符串解析 JSON
            try:
                if isinstance(data, str):
                    parsed = json.loads(data)
                    if isinstance(parsed, dict):
                        return self._sanitize_data([parsed])
                    if isinstance(parsed, list):
                        return self._sanitize_data(parsed)
            except Exception:
                pass
            return []

        sanitized_list = []
        for item in data:
            if not isinstance(item, dict):
                continue

            # 角色处理
            role = item.get("role", self.default_role)
            if not isinstance(role, str) or not role.strip():
                role = self.default_role

            # 音高处理 (小于0取绝对值，避免异常)
            pitch = self._to_float(item.get("pitch"), self.default_pitch)
            if pitch < 0:
                pitch = abs(pitch)

            # 语速处理 (小于0取绝对值，等于0兜底到默认值)
            speed = self._to_float(item.get("speed"), self.default_speed)
            if speed < 0:
                speed = abs(speed)
            if speed == 0:
                speed = self.default_speed

            # 情感处理
            emotion = item.get("emotion", self.default_emotion)
            if not isinstance(emotion, str) or not emotion.strip():
                emotion = self.default_emotion

            # 时长对齐处理 (负数时长归零)
            duration_ms = self._to_int(item.get("duration_ms"), self.default_duration_ms)
            if duration_ms < 0:
                duration_ms = 0

            sanitized_list.append({
                "role": role,
                "pitch": pitch,
                "speed": speed,
                "emotion": emotion,
                "duration_ms": duration_ms
            })

        return sanitized_list

    def explain(self, data, fmt="json"):
        """
        生成大白话结论卡
        :param data: 输入的配置数据，期望为列表格式的字典
        :param fmt: 输出格式，支持 'json', 'markdown', 'html', 默认为 'json'
        :return: 对应格式的大白话结论卡数据
        """
        sanitized_data = self._sanitize_data(data)

        explanations = []
        for item in sanitized_data:
            role = item["role"]
            pitch = item["pitch"]
            speed = item["speed"]
            emotion = item["emotion"]
            duration = item["duration_ms"]

            # 动态生成大白话解释
            pitch_desc = "偏高" if pitch > 1.2 else ("偏低" if pitch < 0.8 else "正常")
            speed_desc = "偏快" if speed > 1.2 else ("偏慢" if speed < 0.8 else "正常")

            description = f"角色【{role}】以{emotion}的情感发音，音调{pitch_desc}({pitch:.1f})，语速{speed_desc}({speed:.1f})，预计耗时{duration}毫秒。"

            explanations.append({
                "role": role,
                "description": description,
                "details": item
            })

        if fmt == "json":
            return json.dumps({
                "status": "success",
                "message": "大白话结论卡生成成功",
                "data": explanations
            }, ensure_ascii=False)

        elif fmt == "markdown":
            md = "### 多角色情感与语速分析卡片\n\n"
            if not explanations:
                md += "暂无有效角色配置。\n"
            else:
                for exp in explanations:
                    md += f"- **{exp['role']}**: {exp['description']}\n"
            return md

        elif fmt == "html":
            html = "<div class='tts-explainer-card'>\n  <h3>多角色情感与语速分析卡片</h3>\n  <ul>\n"
            if not explanations:
                html += "    <li>暂无有效角色配置。</li>\n"
            else:
                for exp in explanations:
                    html += f"    <li><strong>{exp['role']}</strong>: {exp['description']}</li>\n"
            html += "  </ul>\n</div>"
            return html

        else:
            return explanations
