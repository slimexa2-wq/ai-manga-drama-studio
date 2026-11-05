import os
import zipfile
import html
from typing import Dict, Any
from .style_presets import STYLE_PRESETS
from typing import Dict, Any, Tuple
from .storyboard_engine import build_storyboard, split_into_narrative_beats
from .jianying_draft_exporter import export_full_bundle


def generate_style_comparison_html(raw_text: str, title: str, output_dir: str) -> str:
    """
    Generates an HTML grid comparing the first shot of the storyboard across all 8 predefined styles.
    """
    html_path = os.path.join(output_dir, "style_comparison.html")

    # Only use the first narrative beat to avoid generating the whole storyboard
    # for all 8 styles.
    beats = split_into_narrative_beats(raw_text)
    first_beat = beats[0] if beats else raw_text

    style_cards = []
    for style_id, style_info in STYLE_PRESETS.items():
        sb = build_storyboard(first_beat, title=title, style_id=style_id)
        if not sb["shots"]:
            continue
        first_shot = sb["shots"][0]

        style_cards.append(f"""
        <div class="style-card">
            <h3>{html.escape(style_info['name'])}</h3>
            <div class="prompt-section">
                <h4>🎨 ChatGPT Plus (GPT-Image-2)</h4>
                <code>{html.escape(first_shot['chatgpt_plus_image_prompt'])}</code>
            </div>
            <div class="prompt-section">
                <h4>✨ Google Flow (Imagen 4)</h4>
                <code>{html.escape(first_shot['google_ultra_flow_image_prompt'])}</code>
            </div>
            <div class="prompt-section">
                <h4>🎞️ Google Veo 3 运镜</h4>
                <code>{html.escape(first_shot['google_ultra_veo3_video_prompt'])}</code>
            </div>
        </div>
        """)

    page_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html.escape(title)} — 8大画风全景对比预览</title>
<style>
  :root {{ --bg: #090d16; --panel: #131b2e; --border: #283552; --text: #f8fafc; --muted: #94a3b8; --accent: #6366f1; }}
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; background: var(--bg); color: var(--text); padding: 28px; }}
  h1 {{ text-align: center; margin-bottom: 30px; font-size: 26px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }}
  .style-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
  .style-card h3 {{ margin-top: 0; color: #a5b4fc; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 15px; font-size: 18px; }}
  .prompt-section {{ margin-bottom: 15px; }}
  .prompt-section h4 {{ margin: 0 0 5px 0; font-size: 14px; color: #cbd5e1; }}
  code {{ display: block; background: #0b1120; padding: 10px; border-radius: 8px; font-size: 12px; color: #94a3b8; word-break: break-all; white-space: pre-wrap; }}
</style>
</head>
<body>
    <h1>🎬 8大画风一键对比预览 - 首镜直出效果</h1>
    <div class="grid">
        {''.join(style_cards)}
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page_html)

    return html_path


def create_zip_package(output_dir: str) -> str:
    """
    Recursively zips the output directory into a single .zip file.
    """
    dir_name = os.path.basename(os.path.normpath(output_dir))
    zip_path = f"{output_dir}.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join(dir_name, os.path.relpath(file_path, output_dir))
                zipf.write(file_path, arcname)

    return zip_path


def package_project(raw_text: str, title: str, style_id: str, output_dir: str) -> Tuple[Dict[str, str], Dict[str, Any]]:
    """
    Wrapper to export full bundle, generate style comparison HTML, zip the directory, and return paths and the storyboard.
    """
    sb = build_storyboard(raw_text, title=title, style_id=style_id)
    paths = export_full_bundle(sb, output_dir)

    style_comparison_path = generate_style_comparison_html(raw_text, title, output_dir)
    paths["style_comparison_html"] = style_comparison_path

    zip_path = create_zip_package(output_dir)
    paths["zip_package"] = zip_path

    return paths, sb
