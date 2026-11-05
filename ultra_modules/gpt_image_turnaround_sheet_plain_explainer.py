import json

def generate_plain_explainer(backend_result=None, format="markdown"):
    """
    Transforms the complex backend GPT-Image-2 generation results into a
    simple, plain-text conclusion card suitable for non-technical business users.

    Args:
        backend_result (dict|str): The result dictionary from gpt_image_turnaround_sheet_core_engine
                                   or a JSON string representing it. If None or invalid, falls back.
        format (str): The desired output format ('markdown', 'html', or 'json').

    Returns:
        str: The formatted explanation.
    """
    # 1. Clean and parse input data
    if backend_result is None:
        backend_result = {}
    elif isinstance(backend_result, str):
        try:
            backend_result = json.loads(backend_result)
            if not isinstance(backend_result, dict):
                backend_result = {}
        except json.JSONDecodeError:
            # Dirty data fallback
            backend_result = {}
    elif not isinstance(backend_result, dict):
        backend_result = {}

    # Extract config and handle missing keys with defaults
    config = backend_result.get("config", {})
    if not isinstance(config, dict):
        config = {}

    character_desc = str(config.get("character_desc", "")).strip()
    if not character_desc:
        character_desc = "未指定角色设定 (默认：A handsome anime protagonist with a mysterious aura, wearing a dark cloak.)"

    style = str(config.get("style", "")).strip()
    if not style:
        style = "未指定风格 (默认：high quality anime style, masterpiece, best quality, ultra-detailed)"

    include_expressions = config.get("include_expressions", True)
    if not isinstance(include_expressions, bool):
        include_expressions = True
    expressions_text = "是 (包含3-4种不同表情)" if include_expressions else "否"

    ar_value = config.get("aspect_ratio", "")
    if ar_value is None:
        ar_value = ""
    aspect_ratio = str(ar_value).strip()
    if not aspect_ratio or aspect_ratio.lower() == "none":
        aspect_ratio = "未指定比例 (默认：16:9)"

    prompt = str(backend_result.get("prompt", "")).strip()
    if not prompt:
        prompt = "（未生成提示词）"

    # Clean and validate format parameter
    format_clean = str(format).strip().lower() if format is not None else "markdown"
    if format_clean not in ("markdown", "html", "json"):
        format_clean = "markdown"  # fallback

    # 2. Generate Output based on format
    if format_clean == "markdown":
        return f"""# 🧑‍🎨 角色三视图与表情设定集

**💡 一句话总结**：
为您生成了一个包含角色正、侧、背面视图的设定集。
{'同时包含了角色的多个面部表情。' if include_expressions else '本次未包含特殊面部表情。'}

### 📋 核心设定
- **角色描述**：{character_desc}
- **画面风格**：{style}
- **画面比例**：{aspect_ratio}
- **包含表情包**：{expressions_text}

### 🔮 最终送往 AI 绘画的指令 (供检查)：
```text
{prompt}
```
"""
    elif format_clean == "html":
        return f"""<div class="turnaround-explainer">
  <h2>🧑‍🎨 角色三视图与表情设定集</h2>
  <p><strong>💡 一句话总结</strong>：为您生成了一个包含角色正、侧、背面视图的设定集。{'同时包含了角色的多个面部表情。' if include_expressions else '本次未包含特殊面部表情。'}</p>
  <h3>📋 核心设定</h3>
  <ul>
    <li><strong>角色描述</strong>：{character_desc}</li>
    <li><strong>画面风格</strong>：{style}</li>
    <li><strong>画面比例</strong>：{aspect_ratio}</li>
    <li><strong>包含表情包</strong>：{expressions_text}</li>
  </ul>
  <h3>🔮 最终送往 AI 绘画的指令 (供检查)：</h3>
  <pre><code>{prompt}</code></pre>
</div>"""
    elif format_clean == "json":
        summary = f"为您生成了一个包含角色正、侧、背面视图的设定集。{'同时包含了角色的多个面部表情。' if include_expressions else '本次未包含特殊面部表情。'}"
        return json.dumps({
            "title": "🧑‍🎨 角色三视图与表情设定集",
            "summary": summary,
            "core_settings": {
                "character_desc": character_desc,
                "style": style,
                "aspect_ratio": aspect_ratio,
                "include_expressions": expressions_text
            },
            "final_prompt": prompt
        }, ensure_ascii=False, indent=2)
