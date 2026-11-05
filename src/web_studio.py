#!/usr/bin/env python3
"""
Zero-Friction One-Click Web Studio & CLI for Google 20x Ultra + ChatGPT Plus Manga Drama Workflow.
Philosophy: Complex backend, ultra-simple 1-click frontend. No login walls, no tedious popups, no manual copy-pasting.
"""

import argparse
import json
import mimetypes
import os
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from .style_presets import STYLE_PRESETS
from .studio_packager import package_project
from .batch_episode_splitter import split_long_novel_into_episodes

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
  .wrap {{ max-width: 1220px; margin: 0 auto; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }}
  .header h1 {{ margin: 0; font-size: 26px; }}
  .sub {{ color: var(--muted); font-size: 14px; margin-top: 4px; }}
  .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 22px; margin-bottom: 20px; }}
  .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 14px; }}
  label {{ display: block; font-size: 13px; color: var(--muted); margin-bottom: 6px; font-weight: 600; }}
  input, select, textarea {{ width: 100%; background: #0b1120; border: 1px solid var(--border); color: var(--text); border-radius: 10px; padding: 12px; font-size: 14px; }}
  textarea {{ min-height: 150px; resize: vertical; line-height: 1.6; }}
  .big-btn {{ width: 100%; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; border: none; padding: 16px; border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 10px; transition: 0.15s; }}
  .big-btn:hover {{ opacity: 0.94; transform: translateY(-1px); }}
  .action-btn {{ display: inline-block; background: var(--primary); color: #fff; text-decoration: none; border: none; padding: 10px 16px; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer; margin-right: 10px; margin-top: 8px; }}
  .action-btn.green {{ background: var(--green); }}
  .action-btn.secondary {{ background: #1e293b; border: 1px solid var(--border); }}
  #result {{ display: none; }}
  .success-banner {{ background: rgba(16,185,129,0.14); border: 1px solid var(--green); border-radius: 12px; padding: 18px; margin-bottom: 20px; }}
  .stage-grid {{ display: grid; grid-template-columns: 340px 1fr; gap: 22px; align-items: start; }}
  .video-card {{ background: #0b1120; border: 1px solid var(--border); border-radius: 14px; padding: 14px; text-align: center; position: sticky; top: 20px; }}
  .video-card video {{ width: 100%; max-height: 540px; border-radius: 10px; background: #000; }}
  .shot-item {{ background: #0b1120; border: 1px solid #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 12px; display: grid; grid-template-columns: 120px 1fr; gap: 14px; align-items: center; }}
  .shot-thumb {{ width: 120px; height: 213px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div>
      <h1>🎬 Google 20x Ultra × ChatGPT Plus 极简一键漫剧工作台</h1>
      <div class="sub">效率优先 · 前端极简：粘贴小说/剧本 → 点选画风 → 一键全自动产出【多角色真配音 + 9:16竖屏漫剧MP4成片 + 剪映专业版工程包 + 双生态后台投递】</div>
    </div>
  </div>

  <div class="panel">
    <div class="row">
      <div>
        <label>📌 剧集标题（免填自动生成）</label>
        <input id="title" value="第一集_魔帝归来" />
      </div>
      <div>
        <label>🎨 视觉画风（内置 8 大工业级短剧画风母版）</label>
        <select id="style_id">{style_options}</select>
      </div>
    </div>
    <label>📖 粘贴小说章节 / 剧本正文 / 一句话故事梗概（长文自动按黄金前3秒钩子分集）</label>
    <textarea id="script_text">{SAMPLE_SCRIPT}</textarea>
    <button class="big-btn" onclick="generateNow()">⚡ 一键全自动生成有声漫剧成片 + 剪映工程包（无需手工复制）</button>
  </div>

  <div id="result" class="panel"></div>
</div>

<script>
window.previousResultHtml = '';
window.lastOutputDir = '';

function undoGeneration() {{
  if (window.previousResultHtml) {{
    document.getElementById('result').innerHTML = window.previousResultHtml;
  }}
}}

async function dispatchCloudEcosystem() {{
  const btn = document.getElementById('cloud-btn');
  if (!btn) return;
  btn.textContent = '⏳ 正在通过 ego-browser 后台自动投递至 Google Flow (Veo 3) 与 ChatGPT Plus...';
  const res = await fetch('/api/dispatch-cloud', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{ output_dir: window.lastOutputDir }})
  }});
  const data = await res.json();
  btn.textContent = data.ok ? '✅ 已在后台投递至 Google 20x Ultra & ChatGPT Plus' : '⚠️ 投递提示：' + (data.error || '');
}}

async function generateNow() {{
  const btn = document.querySelector('.big-btn');
  btn.textContent = '⏳ 正在后台全自动拆解分镜、合成多角色语音、渲染 9:16 竖屏成片与剪映工程...';
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
  btn.textContent = '⚡ 一键全自动生成有声漫剧成片 + 剪映工程包（无需手工复制）';
  const box = document.getElementById('result');
  window.previousResultHtml = box.innerHTML;
  box.style.display = 'block';

  const ep = data.episodes ? data.episodes[0] : data;
  const sb = ep.storyboard;
  const paths = ep.paths;
  window.lastOutputDir = paths.output_dir;

  const mp4Url = '/media?path=' + encodeURIComponent(paths.episode_mp4 || '');
  const zipUrl = '/media?path=' + encodeURIComponent(paths.zip_package || '');
  const compareUrl = '/media?path=' + encodeURIComponent(paths.style_comparison_html || '');

  let shotsHtml = sb.shots.map(s => {{
    const imgUrl = '/media?path=' + encodeURIComponent(s.image_path || '');
    const audUrl = '/media?path=' + encodeURIComponent(s.audio_path || '');
    return `
      <div class="shot-item">
        <img class="shot-thumb" src="${{imgUrl}}" alt="${{s.shot_id}}" />
        <div>
          <div style="font-size:15px;font-weight:700;color:#38bdf8;">${{s.shot_id}} (${{s.duration_sec}}s) · ${{s.emotion}} · ${{s.shot_type}}</div>
          <div style="margin:6px 0;color:#cbd5e1;font-size:14px;">🎬 画面：${{s.narrative_beat}}</div>
          <div style="margin:6px 0;color:#fde047;font-size:14px;font-weight:600;">🎙️ ${{s.speaker}}：“${{s.subtitle_text}}”</div>
          <audio controls src="${{audUrl}}" style="height:32px;margin-top:4px;"></audio>
        </div>
      </div>
    `;
  }}).join('');

  box.innerHTML = `
    <div class="success-banner">
      <div style="font-size:17px;font-weight:700;">✅ 全自动漫剧成片与剪映工程已生成！（共 ${{sb.total_shots}} 镜，实测总时长 ${{sb.total_duration_sec}} 秒）</div>
      <div style="margin-top:6px;font-size:13px;color:#cbd5e1;">📂 工程目录：<code>${{paths.output_dir}}</code></div>
      <div>
        <a class="action-btn green" href="${{mp4Url}}" download>⬇️ 一键下载 9:16 漫剧 MP4 成片</a>
        <a class="action-btn" href="${{zipUrl}}" download>📦 一键下载全套剪映工程包 (.zip)</a>
        <a class="action-btn secondary" href="${{compareUrl}}" target="_blank">🎨 查看 8 大画风全景对比</a>
        <button id="cloud-btn" class="action-btn secondary" onclick="dispatchCloudEcosystem()">🚀 后台一键投递 Google Flow (Veo 3) + ChatGPT Plus</button>
        ${{window.previousResultHtml ? '<button class="action-btn secondary" onclick="undoGeneration()">↩️ 一键撤回上一版</button>' : ''}}
      </div>
    </div>
    <div class="stage-grid">
      <div class="video-card">
        <div style="font-weight:700;margin-bottom:8px;color:#a5b4fc;">📱 9:16 竖屏有声漫剧成片预览</div>
        <video controls autoplay src="${{mp4Url}}"></video>
      </div>
      <div>
        ${{shotsHtml}}
      </div>
    </div>
  `;
}}
</script>
</body>
</html>"""


class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/media":
            qs = urllib.parse.parse_qs(parsed.query)
            file_path = qs.get("path", [""])[0]
            real_root = os.path.realpath(DEFAULT_OUTPUT_ROOT)
            real_target = os.path.realpath(file_path) if file_path else ""
            if real_target.startswith(real_root) and os.path.isfile(real_target):
                mime, _ = mimetypes.guess_type(real_target)
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", str(os.path.getsize(real_target)))
                self.end_headers()
                with open(real_target, "rb") as f:
                    self.wfile.write(f.read())
                return
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(render_studio_home_html().encode("utf-8"))

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            base_title = body.get("title") or "未命名漫剧"
            style_id = body.get("style_id") or "xianxia"
            text = body.get("text") or SAMPLE_SCRIPT

            episodes_raw = split_long_novel_into_episodes(text)
            results = []
            for idx, ep in enumerate(episodes_raw, start=1):
                ep_title = base_title if len(episodes_raw) == 1 else f"{base_title}_第{idx}集"
                safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in ep_title)[:35]
                out_dir = os.path.join(DEFAULT_OUTPUT_ROOT, safe_name)
                paths, sb = package_project(ep["text"], title=ep_title, style_id=style_id, output_dir=out_dir)
                results.append({"title": ep_title, "storyboard": sb, "paths": paths})

            first = results[0]
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "ok": True,
                        "storyboard": first["storyboard"],
                        "paths": first["paths"],
                        "episodes": results,
                    },
                    ensure_ascii=False,
                ).encode("utf-8")
            )
            return

        if self.path == "/api/dispatch-cloud":
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            out_dir = body.get("output_dir") or ""
            sb_json = os.path.join(out_dir, "storyboard.json")
            runner = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "ego_dual_ecosystem_runner.mjs")
            if os.path.exists(sb_json) and os.path.exists(runner):
                subprocess.Popen(
                    ["/Applications/ego lite.app/Contents/MacOS/ego-browser", "nodejs", runner, sb_json],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "未找到分镜文件"}).encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Google 20x Ultra + ChatGPT Plus 一键漫剧工作台")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="一键从小说/剧本生成全套有声漫剧成片与剪映工程包")
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
        print(
            json.dumps(
                {
                    "ok": True,
                    "total_shots": sb["total_shots"],
                    "total_duration_sec": sb["total_duration_sec"],
                    "paths": paths,
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
