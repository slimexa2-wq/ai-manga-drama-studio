def build_gpt_image_turnaround_prompt(
    character_desc=None,
    style=None,
    include_expressions=None,
    aspect_ratio=None,
    **kwargs
):
    """
    Builds a ChatGPT Plus (GPT-Image-2) prompt for generating a character turnaround sheet
    (front, side, back views) and expressions.

    Ensures zero-configuration auto-fallback and dirty data self-healing.
    """

    # 1. Clean and fallback `character_desc`
    if not isinstance(character_desc, str):
        if isinstance(character_desc, (dict, list)):
            import json
            character_desc = json.dumps(character_desc, ensure_ascii=False)
        else:
            character_desc = str(character_desc) if character_desc is not None else ""
    character_desc = character_desc.strip()
    if not character_desc:
        character_desc = "A handsome anime protagonist with a mysterious aura, wearing a dark cloak."

    # 2. Clean and fallback `style`
    if not isinstance(style, str):
        style = str(style) if style is not None else ""
    style = style.strip()
    if not style:
        style = "high quality anime style, masterpiece, best quality, ultra-detailed"

    # 3. Clean and fallback `include_expressions`
    if include_expressions is None:
        include_expressions = True
    elif isinstance(include_expressions, str):
        val = include_expressions.strip().lower()
        include_expressions = val not in ("false", "0", "no", "f", "n", "")
    else:
        include_expressions = bool(include_expressions)

    # 4. Clean and fallback `aspect_ratio`
    if not isinstance(aspect_ratio, str):
        aspect_ratio = str(aspect_ratio) if aspect_ratio is not None else ""
    aspect_ratio = aspect_ratio.strip().lower()

    valid_aspect_ratios = {"16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "9:21"}
    if aspect_ratio not in valid_aspect_ratios:
        # Try to clean common malformed strings like "16x9" or "16-9"
        cleaned_ar = aspect_ratio.replace("x", ":").replace("-", ":").replace(" ", "")
        if cleaned_ar in valid_aspect_ratios:
            aspect_ratio = cleaned_ar
        else:
            aspect_ratio = "16:9" # Default fallback

    # 5. Build prompt
    prompt_lines = [
        "Create a character design turnaround sheet for the following character:",
        f"Character Description: {character_desc}",
        f"Style: {style}",
        "",
        "The sheet MUST include full-body views of the character from the following angles:",
        "- Front view",
        "- Side view",
        "- Back view",
        "Align all views on the same ground line. Ensure consistent clothing, anatomy, and proportions across all angles."
    ]

    if include_expressions:
        prompt_lines.extend([
            "",
            "Additionally, include a section with 3-4 different facial expressions for the character (e.g., smiling, angry, sad, surprised)."
        ])

    prompt_lines.extend([
        "",
        f"--ar {aspect_ratio} --niji 6" # Added some dummy parameter style text
    ])

    prompt = "\n".join(prompt_lines)

    return {
        "prompt": prompt,
        "config": {
            "character_desc": character_desc,
            "style": style,
            "include_expressions": include_expressions,
            "aspect_ratio": aspect_ratio
        }
    }
