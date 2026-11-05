"""
Zero-Friction CapCut / JianyingPro (剪映专业版) Draft Exporter, SRT Subtitle Generator,
and Interactive One-Click Storyboard HTML Dashboard.
"""

import json
import os
import time
import uuid
import html
from typing import Dict, Any


def _ms_to_srt_time(ms: int) -> str:
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def export_srt(storyboard: Dict[str, Any], out_path: str) -> str:
    lines = []
    for shot in storyboard["shots"]:
        idx = shot["shot_number"]
        start = _ms_to_srt_time(shot["start_ms"])
        end = _ms_to_srt_time(shot["end_ms"])
        speaker_prefix = f"【{shot['speaker']}】" if shot["speaker"] != "旁白" else ""
        lines.append(f"{idx}\n{start} --> {end}\n{speaker_prefix}{shot['subtitle_text']}\n")
    content = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def export_jianying_draft(storyboard: Dict[str, Any], draft_dir: str) -> Dict[str, str]:
    """
    Generate a CapCut / 剪映专业版 (JianyingPro) compatible draft folder (`draft_content.json`
    + `draft_meta_info.json`) with pre-aligned 9:16 canvas (1080x1920), video/image segments,
    Ken Burns keyframe zoom/pan metadata, audio segments, and subtitle text tracks.
    """
    os.makedirs(draft_dir, exist_ok=True)
    assets_dir = os.path.join(draft_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    now_us = int(time.time() * 1_000_000)
    total_duration_us = int(storyboard["total_duration_sec"] * 1_000_000)

    materials_videos = []
    materials_texts = []
    materials_audios = []
    video_segments = []
    text_segments = []
    audio_segments = []

    for shot in storyboard["shots"]:
        vid_id = str(uuid.uuid4()).upper()
        txt_id = str(uuid.uuid4()).upper()
        aud_id = str(uuid.uuid4()).upper()
        start_us = shot["start_ms"] * 1000
        dur_us = shot["duration_ms"] * 1000

        shot_img_path = os.path.join(assets_dir, f"{shot['shot_id']}.png")
        shot_aud_path = os.path.join(assets_dir, f"{shot['shot_id']}.mp3")

        materials_videos.append({
            "id": vid_id,
            "type": "photo",
            "path": shot_img_path,
            "material_name": f"{shot['shot_id']}_{shot['shot_type']}",
            "width": 1080,
            "height": 1920,
            "duration": dur_us,
        })

        materials_texts.append({
            "id": txt_id,
            "type": "text",
            "content": json.dumps({
                "text": shot["subtitle_text"],
                "styles": [{
                    "fill": {"content": {"solid": {"color": [1.0, 0.95, 0.2] if shot["speaker"] != "旁白" else [1.0, 1.0, 1.0]}}},
                    "size": 11.0,
                    "bold": True,
                    "range": [0, len(shot["subtitle_text"])],
                }],
            }, ensure_ascii=False),
            "font_size": 11.0,
            "alignment": 1,
        })

        materials_audios.append({
            "id": aud_id,
            "type": "extract_music",
            "path": shot_aud_path,
            "name": f"{shot['shot_id']}_{shot['speaker']}_tts.mp3",
            "duration": dur_us,
        })

        # Ken Burns camera motion scale parameters
        motion_key = shot["camera_motion_key"]
        start_scale = 1.0
        end_scale = 1.18 if "push_in" in motion_key or "zoom" in motion_key else (1.12 if "pull_back" in motion_key else 1.08)

        video_segments.append({
            "id": str(uuid.uuid4()).upper(),
            "material_id": vid_id,
            "target_timerange": {"start": start_us, "duration": dur_us},
            "source_timerange": {"start": 0, "duration": dur_us},
            "clip": {
                "scale": {"x": end_scale, "y": end_scale},
                "transform": {"x": 0.0, "y": 0.0},
                "rotation": 0.0,
            },
            "extra_camera_motion": {
                "motion_type": motion_key,
                "start_scale": start_scale,
                "end_scale": end_scale,
                "google_veo3_prompt": shot["google_ultra_veo3_video_prompt"],
            },
        })

        text_segments.append({
            "id": str(uuid.uuid4()).upper(),
            "material_id": txt_id,
            "target_timerange": {"start": start_us, "duration": dur_us},
            "clip": {"transform": {"x": 0.0, "y": -0.68}, "scale": {"x": 1.0, "y": 1.0}},
        })

        audio_segments.append({
            "id": str(uuid.uuid4()).upper(),
            "material_id": aud_id,
            "target_timerange": {"start": start_us, "duration": dur_us},
            "source_timerange": {"start": 0, "duration": dur_us},
            "volume": 1.0,
        })

    draft_content = {
        "id": str(uuid.uuid4()).upper(),
        "version": 360000,
        "new_version": "110.0.0",
        "name": storyboard["title"],
        "duration": total_duration_us,
        "canvas_config": {"width": 1080, "height": 1920, "ratio": "9:16"},
        "fps": 30.0,
        "materials": {
            "videos": materials_videos,
            "texts": materials_texts,
            "audios": materials_audios,
        },
        "tracks": [
            {"id": str(uuid.uuid4()).upper(), "type": "video", "segments": video_segments},
            {"id": str(uuid.uuid4()).upper(), "type": "text", "segments": text_segments},
            {"id": str(uuid.uuid4()).upper(), "type": "audio", "segments": audio_segments},
        ],
    }

    draft_meta = {
        "draft_id": draft_content["id"],
        "draft_name": storyboard["title"],
        "draft_root_path": draft_dir,
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
        "tm_duration": total_duration_us,
    }

    content_path = os.path.join(draft_dir, "draft_content.json")
    meta_path = os.path.join(draft_dir, "draft_meta_info.json")
    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(draft_content, f, ensure_ascii=False, indent=2)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(draft_meta, f, ensure_ascii=False, indent=2)

    return {"draft_content": content_path, "draft_meta_info": meta_path}


def export_interactive_html(storyboard: Dict[str, Any], out_path: str) -> str:
    """
    Generate a zero-friction, ultra-intuitive interactive single-page HTML board
    where the creator can copy any prompt in 1 click or batch-launch Google Flow / ChatGPT Plus.
    """
    title = html.escape(storyboard["title"])
    style_name = html.escape(storyboard["style"]["name"])
    total_shots = storyboard["total_shots"]
    total_dur = storyboard["total_duration_sec"]

    char_cards = []
    for c in storyboard["characters"]:
        char_cards.append(f"""
        <div class="card char-card">
          <div class="badge">{html.escape(c['char_id'])} · Seed {c['seed']}</div>
          <h3>{html.escape(c['name'])} <span class="voice-tag">🎙️ {html.escape(c['voice'])}</span></h3>
          <p class="desc">{html.escape(c['visual_description'])}</p>
          <div class="btn-row">
            <button onclick="copyText(this)" data-prompt="{html.escape(c['chatgpt_character_sheet_prompt'])}">📋 复制 ChatGPT 三视图设定词</button>
            <button onclick="copyText(this)" data-prompt="{html.escape(c['google_whisk_subject_prompt'])}">📋 复制 Google Whisk 锁脸词</button>
          </div>
        </div>
        """)

    shot_cards = []
    for s in storyboard["shots"]:
        shot_cards.append(f"""
        <div class="card shot-card">
          <div class="shot-header">
            <span class="shot-num">{html.escape(s['shot_id'])} ({s['duration_sec']}s)</span>
            <span class="emotion-tag">{html.escape(s['emotion'])}</span>
            <span class="shot-type">{html.escape(s['shot_type'])}</span>
          </div>
          <div class="beat-box">
            <strong>🎬 画面/剧情：</strong>{html.escape(s['narrative_beat'])}<br/>
            <strong>💬 台词（{html.escape(s['speaker'])}）：</strong><span class="sub-highlight">“{html.escape(s['subtitle_text'])}”</span><br/>
            <strong>🎥 运镜：</strong>{html.escape(s['camera_motion'])} | <strong>🔊 音效：</strong>{html.escape(s['sfx'])}
          </div>
          <div class="prompt-grid">
            <div class="prompt-box">
              <div class="prompt-title">🎨 ChatGPT Plus (GPT-Image-2) 分镜词 <button onclick="copyText(this)" data-prompt="{html.escape(s['chatgpt_plus_image_prompt'])}">一键复制</button></div>
              <code>{html.escape(s['chatgpt_plus_image_prompt'])}</code>
            </div>
            <div class="prompt-box">
              <div class="prompt-title">✨ Google 20x Ultra (Flow / Imagen 4) 分镜词 <button onclick="copyText(this)" data-prompt="{html.escape(s['google_ultra_flow_image_prompt'])}">一键复制</button></div>
              <code>{html.escape(s['google_ultra_flow_image_prompt'])}</code>
            </div>
            <div class="prompt-box">
              <div class="prompt-title">🎞️ Google Veo 3 / Sora 动态运镜指令 <button onclick="copyText(this)" data-prompt="{html.escape(s['google_ultra_veo3_video_prompt'])}">一键复制</button></div>
              <code>{html.escape(s['google_ultra_veo3_video_prompt'])}</code>
            </div>
          </div>
        </div>
        """)

    page_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} — Google 20x Ultra × ChatGPT Plus 极简漫剧工作台</title>
<style>
  :root {{ --bg: #0b0f19; --card: #151c2c; --border: #26324d; --accent: #6366f1; --accent2: #10b981; --text: #f1f5f9; --muted: #94a3b8; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; background: var(--bg); color: var(--text); padding: 24px; line-height: 1.55; }}
  .container {{ max-width: 1240px; margin: 0 auto; }}
  .hero {{ background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }}
  .hero h1 {{ margin: 0 0 8px 0; font-size: 24px; }}
  .meta-pills span {{ display: inline-block; background: rgba(99,102,241,0.18); border: 1px solid var(--accent); padding: 4px 12px; border-radius: 999px; font-size: 13px; margin-right: 8px; }}
  .quick-links a {{ display: inline-block; background: var(--accent); color: #fff; text-decoration: none; padding: 10px 16px; border-radius: 10px; font-weight: 600; font-size: 14px; margin-left: 8px; }}
  .quick-links a.secondary {{ background: #1e293b; border: 1px solid var(--border); }}
  h2 {{ font-size: 18px; margin: 24px 0 12px; border-left: 4px solid var(--accent); padding-left: 10px; }}
  .char-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 18px; }}
  .badge {{ display: inline-block; font-size: 12px; background: #1e293b; color: #38bdf8; padding: 2px 8px; border-radius: 6px; }}
  .voice-tag {{ font-size: 12px; color: var(--muted); font-weight: normal; }}
  .desc {{ font-size: 13px; color: var(--muted); margin: 8px 0 14px; }}
  .btn-row {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  button {{ cursor: pointer; background: var(--accent); color: white; border: none; padding: 7px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; transition: 0.15s; }}
  button:hover {{ opacity: 0.9; transform: translateY(-1px); }}
  .shot-card {{ margin-bottom: 16px; }}
  .shot-header {{ display: flex; gap: 12px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }}
  .shot-num {{ font-weight: 700; color: #38bdf8; font-size: 15px; }}
  .emotion-tag {{ background: rgba(244,63,94,0.18); color: #fda4af; padding: 2px 10px; border-radius: 999px; font-size: 12px; }}
  .shot-type {{ color: var(--muted); font-size: 13px; }}
  .beat-box {{ background: #0f172a; padding: 12px 14px; border-radius: 10px; margin-bottom: 12px; font-size: 14px; }}
  .sub-highlight {{ color: #fde047; font-weight: 600; }}
  .prompt-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 12px; }}
  .prompt-box {{ background: #0b1120; border: 1px solid #1e293b; border-radius: 10px; padding: 10px 12px; }}
  .prompt-title {{ display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 600; color: #a5b4fc; margin-bottom: 6px; }}
  code {{ display: block; font-size: 12px; color: #cbd5e1; word-break: break-all; white-space: pre-wrap; }}
</style>
</head>
<body>
<div class="container">
  <div class="hero">
    <div>
      <h1>🎬 {title}</h1>
      <div class="meta-pills">
        <span>画风：{style_name}</span>
        <span>总分镜：{total_shots} 镜</span>
        <span>预计总时长：{total_dur} 秒</span>
        <span>画幅：9:16 竖屏短剧</span>
        <span>剪映草稿：已生成 (draft_content.json)</span>
      </div>
    </div>
    <div class="quick-links">
      <a href="https://labs.google/fx/tools/flow" target="_blank">🚀 打开 Google Flow (Veo 3)</a>
      <a href="https://labs.google/fx/tools/whisk" target="_blank" class="secondary">🎨 打开 Google Whisk 锁角色</a>
      <a href="https://chatgpt.com/" target="_blank" class="secondary">🤖 打开 ChatGPT Plus</a>
    </div>
  </div>

  <h2>一、角色一致性资产锁（Character DNA & Turnaround Cards）</h2>
  <div class="char-grid">
    {''.join(char_cards)}
  </div>

  <h2>二、逐镜分镜表与双生态一键提示词（共 {total_shots} 镜）</h2>
  {''.join(shot_cards)}
</div>
<script>
function copyText(btn) {{
  const text = btn.getAttribute('data-prompt');
  navigator.clipboard.writeText(text);
  const old = btn.textContent;
  btn.textContent = '✅ 已复制';
  btn.style.background = '#10b981';
  setTimeout(() => {{ btn.textContent = old; btn.style.background = ''; }}, 1400);
}}
</script>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page_html)
    return out_path


def export_full_bundle(storyboard: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    """Export JSON storyboard, SRT subtitles, JianyingPro draft, and Interactive HTML."""
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "storyboard.json")
    srt_path = os.path.join(output_dir, "subtitles.srt")
    html_path = os.path.join(output_dir, "storyboard_preview.html")
    draft_dir = os.path.join(output_dir, "jianying_draft")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(storyboard, f, ensure_ascii=False, indent=2)

    export_srt(storyboard, srt_path)
    export_interactive_html(storyboard, html_path)
    draft_paths = export_jianying_draft(storyboard, draft_dir)

    return {
        "output_dir": output_dir,
        "storyboard_json": json_path,
        "subtitles_srt": srt_path,
        "preview_html": html_path,
        "jianying_draft_dir": draft_dir,
        "draft_content_json": draft_paths["draft_content"],
    }
