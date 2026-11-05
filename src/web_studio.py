#!/usr/bin/env python3
"""
Zero-Friction One-Click Web Studio & CLI for Google 20x Ultra + ChatGPT Plus Manga Drama Workflow.
Philosophy: Complex backend, ultra-simple 1-click frontend. No login walls, no tedious popups.
"""

import argparse
import json
import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from .style_presets import STYLE_PRESETS
from .storyboard_engine import build_storyboard
from .studio_packager import package_project

DEFAULT_OUTPUT_ROOT = os.path.expanduser("~/Downloads/AI漫剧工程输出")

SAMPLE_SCRIPT = """三年前，林玄被挚爱苏清雪与族兄赵天辰联手算计，当众挖去至尊剑骨，打入万魔渊底！
赵天辰高坐青云宗主位，手挽苏清雪冷笑道：“林玄那个废物，恐怕早就被魔渊罡风撕成碎片了！”
话音未落，九天之上血雷炸裂，整座青云宗护山大阵轰然崩碎！
林玄身披玄黑魔帝长袍踏空而降，眸中金芒如剑：“三年前欠我的至尊骨，今日，我要你们全族拿命来偿！”"""


def render_studio_home_html() -> str:
    style_options = "\n".join(
        f'<option value="{k}">{v["name"]}</option>' for k, v in STYLE_PRESETS.items()
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Google 20x Ultra × ChatGPT Plus 极简漫剧工作台</title>
<style>
  :root {{ --bg: #090d16; --panel: #131b2e; --border: #283552; --primary: #6366f1; --green: #10b981; --text: #f8fafc; --muted: #94a3b8; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; background: var(--bg); color: var(--text); padding: 28px; }}
  .wrap {{ max-width: 1180px; margin: 0 auto; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }}
  .header h1 {{ margin: 0; font-size: 26px; }}
  .sub {{ color: var(--muted); font-size: 14px; margin-top: 4px; }}
  .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 22px; margin-bottom: 20px; }}
  .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 14px; }}
  label {{ display: block; font-size: 13px; color: var(--muted); margin-bottom: 6px; font-weight: 600; }}
  input, select, textarea {{ width: 100%; background: #0b1120; border: 1px solid var(--border); color: var(--text); border-radius: 10px; padding: 12px; font-size: 14px; }}
  textarea {{ min-height: 150px; resize: vertical; line-height: 1.6; }}
  .big-btn {{ width: 100%; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; border: none; padding: 15px; border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 10px; transition: 0.15s; }}
  .big-btn:hover {{ opacity: 0.94; transform: translateY(-1px); }}
  #result {{ display: none; }}
  .success-banner {{ background: rgba(16,185,129,0.14); border: 1px solid var(--green); border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
  .shot-item {{ background: #0b1120; border: 1px solid #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 12px; }}
  .prompt-row {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 10px; }}
  .pbox {{ background: #111827; padding: 10px; border-radius: 8px; font-size: 12px; }}
  .pbox button {{ background: var(--primary); color: #fff; border: none; padding: 4px 10px; border-radius: 6px; cursor: pointer; float: right; font-size: 11px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div>
      <h1>🎬 Google 20x Ultra × ChatGPT Plus 一键漫剧工作台</h1>
      <div class="sub">极简操作：粘贴小说/剧本 → 点选画风 → 一键出齐【角色锁脸卡 + 双生态分镜词 + SRT字幕 + 剪映专业版草稿】</div>
    </div>
  </div>

  <div class="panel">
    <div class="row">
      <div>
        <label>📌 剧集标题（可免填自动生成）</label>
        <input id="title" value="第一集：魔帝归来，踏碎青云" />
      </div>
      <div>
        <label>🎨 视觉画风（内置 awesome-gpt-image-2 工业模板）</label>
        <select id="style_id">{style_options}</select>
      </div>
    </div>
    <label>📖 粘贴小说章节 / 剧本正文 / 一句话故事梗概</label>
    <textarea id="script_text">{SAMPLE_SCRIPT}</textarea>
    <button class="big-btn" onclick="generateNow()">⚡ 一键生成漫剧全套工程（分镜 + 锁脸卡 + 剪映草稿）</button>
  </div>

  <div id="result" class="panel"></div>
</div>

<script>
async function generateNow() {{
  const btn = document.querySelector('.big-btn');
  btn.textContent = '⏳ 正在秒级拆解分镜、锁定角色 DNA 并生成剪映草稿...';
  const res = await fetch('/api/generate', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      title: document.getElementById('title').value,
      style_id: document.getElementById('style_id').value,
      text: document.getElementById('script_text').value
    }})
  }});
  const data = await res.json();
  btn.textContent = '⚡ 一键生成漫剧全套工程（分镜 + 锁脸卡 + 剪映草稿）';
  const box = document.getElementById('result');
  box.style.display = 'block';
  const sb = data.storyboard;
  let shotsHtml = sb.shots.map(s => `
    <div class="shot-item">
      <div><strong>${{s.shot_id}} (${{s.duration_sec}}s) · ${{s.emotion}} · ${{s.shot_type}}</strong></div>
      <div style="margin:6px 0;color:#cbd5e1;">剧情：${{s.narrative_beat}} | <span style="color:#fde047;">台词(${{s.speaker}})：“${{s.subtitle_text}}”</span></div>
      <div class="prompt-row">
        <div class="pbox"><button onclick="navigator.clipboard.writeText(this.nextElementSibling.textContent);this.textContent='✅已复制'">复制 ChatGPT 词</button><div style="display:none">${{s.chatgpt_plus_image_prompt}}</div><strong>🎨 ChatGPT (GPT-Image-2)</strong><br/>${{s.chatgpt_plus_image_prompt.slice(0,110)}}...</div>
        <div class="pbox"><button onclick="navigator.clipboard.writeText(this.nextElementSibling.textContent);this.textContent='✅已复制'">复制 Flow 词</button><div style="display:none">${{s.google_ultra_flow_image_prompt}}</div><strong>✨ Google Flow (Imagen 4)</strong><br/>${{s.google_ultra_flow_image_prompt.slice(0,110)}}...</div>
        <div class="pbox"><button onclick="navigator.clipboard.writeText(this.nextElementSibling.textContent);this.textContent='✅已复制'">复制 Veo 3 词</button><div style="display:none">${{s.google_ultra_veo3_video_prompt}}</div><strong>🎞️ Google Veo 3 运镜</strong><br/>${{s.google_ultra_veo3_video_prompt.slice(0,110)}}...</div>
      </div>
    </div>
  `).join('');

  box.innerHTML = `
    <div class="success-banner">
      <strong>✅ 已一键生成全套漫剧工程包！（共 ${{sb.total_shots}} 镜，总时长 ${{sb.total_duration_sec}} 秒）</strong><br/>
      📂 工程目录：<code>${{data.paths.output_dir}}</code><br/>
      🎬 剪映专业版草稿：<code>${{data.paths.draft_content_json}}</code> | 📝 字幕文件：<code>${{data.paths.subtitles_srt}}</code> | 🌐 独立交互看板：<code>${{data.paths.preview_html}}</code><br/>
      🎨 8大画风全景对比：<code>${{data.paths.style_comparison_html}}</code> | 📦 一键免安装打包ZIP：<code>${{data.paths.zip_package}}</code>
    </div>
    ${{shotsHtml}}
  `;
}}
</script>
</body>
</html>"""


class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(render_studio_home_html().encode("utf-8"))

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            title = body.get("title") or "未命名漫剧"
            style_id = body.get("style_id") or "xianxia"
            text = body.get("text") or SAMPLE_SCRIPT
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:30]
            out_dir = os.path.join(DEFAULT_OUTPUT_ROOT, safe_name)
            paths, sb = package_project(text, title=title, style_id=style_id, output_dir=out_dir)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "storyboard": sb, "paths": paths}, ensure_ascii=False).encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Google 20x Ultra + ChatGPT Plus 一键漫剧工作台")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="一键从小说/剧本生成全套漫剧工程包")
    p_run.add_argument("--title", default="第一集_魔帝归来", help="剧集标题")
    p_run.add_argument("--style", default="xianxia", choices=list(STYLE_PRESETS.keys()), help="视觉风格")
    p_run.add_argument("--text", default=None, help="直接传入小说/剧本文本")
    p_run.add_argument("--file", default=None, help="从文件读取小说/剧本文本")
    p_run.add_argument("--out", default=None, help="输出目录")

    p_serve = sub.add_parser("serve", help="启动零配置一键漫剧 Web 工作台")
    p_serve.add_argument("--port", type=int, default=8788, help="端口号 (默认 8788)")

    args = parser.parse_args()
    if args.cmd == "serve":
        server = HTTPServer(("127.0.0.1", args.port), StudioHandler)
        print(f"🎬 AI 漫剧极简工作台已启动: http://127.0.0.1:{args.port}")
        server.serve_forever()
    else:
        raw_text = SAMPLE_SCRIPT
        if getattr(args, "file", None) and os.path.exists(args.file):
            with open(args.file, "r", encoding="utf-8") as f:
                raw_text = f.read()
        elif getattr(args, "text", None):
            raw_text = args.text
        title = getattr(args, "title", "第一集_魔帝归来")
        style = getattr(args, "style", "xianxia")
        out_dir = getattr(args, "out", None) or os.path.join(DEFAULT_OUTPUT_ROOT, title)
        paths, sb = package_project(raw_text, title=title, style_id=style, output_dir=out_dir)
        print(json.dumps({"ok": True, "total_shots": sb["total_shots"], "total_duration_sec": sb["total_duration_sec"], "paths": paths}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
