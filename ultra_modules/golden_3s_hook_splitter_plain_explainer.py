import json
import re

class Golden3sHookSplitter:
    """
    黄金前3秒强冲突钩子+集末悬念卡点一键多集拆解器。
    提供极简的前端输出接口，后台实现零配置容错、脏数据自愈和缺参默认兜底。
    """
    def __init__(self, chars_per_episode=None):
        self.chars_per_episode = chars_per_episode if chars_per_episode is not None else 1000

    def _clean_text(self, text):
        if text is None:
            return ""
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                text = ""
        # 移除零宽字符和异常空白字符
        text = re.sub(r'[\u200b\u200c\u200d\uFEFF]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def split_to_episodes(self, text, chars_per_episode=None):
        text = self._clean_text(text)
        if not text:
            return []

        limit = chars_per_episode
        if limit is None:
            limit = self.chars_per_episode

        # 脏数据自愈：处理非整数、负数等异常输入
        try:
            limit = int(limit)
            if limit <= 0:
                limit = 1000
        except (ValueError, TypeError):
            limit = 1000

        episodes = []
        start = 0
        episode_num = 1
        total_length = len(text)

        while start < total_length:
            end = min(start + limit, total_length)

            # 智能断句：尽量在句号等标点处截断，避免截断到一半
            if end < total_length:
                search_start = max(start, end - int(limit * 0.2))
                last_punct = -1
                for i in range(end - 1, search_start - 1, -1):
                    if text[i] in "。！？.!?\n":
                        last_punct = i
                        break
                if last_punct != -1:
                    end = last_punct + 1

            content = text[start:end].strip()
            if not content:
                start = end
                continue

            # 提取黄金前3秒钩子 (前30个字符)
            hook = content[:30] + ("..." if len(content) > 30 else "")

            # 提取集末悬念 (最后30个字符)
            cliffhanger = content[-30:] if len(content) > 30 else content

            # 生成大白话摘要
            summary = f"第{episode_num}集：开局「{hook}」瞬间吸睛，结尾断在「{cliffhanger}」疯狂拉扯读者。"

            episodes.append({
                "episode": episode_num,
                "hook": hook,
                "cliffhanger": cliffhanger,
                "content": content,
                "summary": summary
            })

            start = end
            episode_num += 1

        return episodes

    def export_json(self, episodes):
        # 缺参或错参默认兜底
        if not isinstance(episodes, list):
            episodes = []
        return json.dumps(episodes, ensure_ascii=False, indent=2)

    def export_markdown(self, episodes):
        if not isinstance(episodes, list):
            episodes = []
        md = "# 网文分集大纲（黄金3秒版）\n\n"
        if not episodes:
            return md + "> 暂无内容\n"

        for ep in episodes:
            md += f"## 第{ep.get('episode', 0)}集\n"
            md += f"- **🔥 强冲突钩子**：{ep.get('hook', '')}\n"
            md += f"- **😱 集末悬念卡点**：{ep.get('cliffhanger', '')}\n"
            md += f"- **📝 极简大白话摘要**：{ep.get('summary', '')}\n\n"
        return md

    def export_html(self, episodes):
        if not isinstance(episodes, list):
            episodes = []

        html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>一键拆集可视化卡片</title>
<style>
  body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 20px; color: #333; }
  .header { text-align: center; margin-bottom: 30px; }
  .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
  .card-title { margin-top: 0; color: #1a1a1a; font-size: 1.2em; border-bottom: 1px solid #eee; padding-bottom: 10px; }
  .hook { color: #e74c3c; font-weight: bold; }
  .cliffhanger { color: #8e44ad; font-weight: bold; }
  .summary { background: #f8f9fa; padding: 12px; border-radius: 6px; margin-top: 15px; font-size: 0.95em; color: #555; border-left: 4px solid #3498db; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-right: 8px; }
  .tag-hook { background: #fee2e2; color: #991b1b; }
  .tag-cliff { background: #f3e8ff; color: #6b21a8; }
</style>
</head>
<body>
<div class="header">
  <h1>📖 十万字网文一键拆解结论卡</h1>
  <p>大白话摘要 · 黄金三秒钩子 · 悬念卡点</p>
</div>
<div class="container">
"""
        if not episodes:
            html += "  <div class=\"card\"><p style=\"text-align:center; color:#999;\">暂无内容，请检查输入</p></div>\n"

        for ep in episodes:
            html += f"""  <div class="card">
    <h2 class="card-title">第 {ep.get('episode', 0)} 集</h2>
    <p><span class="tag tag-hook">黄金前3秒</span> <span class="hook">{ep.get('hook', '')}</span></p>
    <p><span class="tag tag-cliff">集末悬念</span> <span class="cliffhanger">{ep.get('cliffhanger', '')}</span></p>
    <div class="summary">
      <strong>💡 业务一秒看懂：</strong>{ep.get('summary', '')}
    </div>
  </div>
"""
        html += """</div>
</body>
</html>"""
        return html
