# ultra_modules/eight_style_matrix_previewer_core_engine.py

def generate_style_matrix(prompt=None, styles=None, config=None):
    """
    Generates a matrix preview configuration for up to 8 predefined styles.

    Provides zero-configuration automatic fallback and silent dirty data cleaning.
    """

    # 1. Clean and fallback prompt
    if not isinstance(prompt, str) or not prompt.strip():
        prompt = "默认场景：主角站在城市废墟中，眼神坚定"
    else:
        prompt = prompt.strip()

    # 2. Clean and fallback styles
    default_styles = [
        "修仙", "都市逆袭", "韩漫财阀", "热血少年",
        "中式规则怪谈", "赛博朋克", "废土生存", "黑暗奇幻"
    ]

    valid_styles = []
    if isinstance(styles, list):
        for s in styles:
            if isinstance(s, str) and s.strip():
                valid_styles.append(s.strip())

    if not valid_styles:
        valid_styles = default_styles
    else:
        # Cap at 8 styles max for the matrix
        valid_styles = valid_styles[:8]

    # 3. Clean and fallback config
    if not isinstance(config, dict):
        config = {}

    # Ensure sane defaults in config
    resolution = config.get("resolution", "1024x1024")
    if not isinstance(resolution, str) or not resolution.strip():
        resolution = "1024x1024"

    aspect_ratio = config.get("aspect_ratio", "1:1")
    if not isinstance(aspect_ratio, str) or not aspect_ratio.strip():
        aspect_ratio = "1:1"

    # 4. Generate matrix
    matrix = {
        "base_prompt": prompt,
        "config": {
            "resolution": resolution,
            "aspect_ratio": aspect_ratio
        },
        "previews": []
    }

    for style in valid_styles:
        matrix["previews"].append({
            "style": style,
            "combined_prompt": f"[{style}风格] {prompt}",
            "status": "ready"
        })

    return matrix
