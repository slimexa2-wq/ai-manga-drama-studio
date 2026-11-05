def bridge_schema(input_data: any) -> dict:
    """
    Bridges incoming data schemas into a standardized format for the
    eight_style_matrix_previewer_core_engine.

    Handles modern schema, old schema, flat schema, or completely malformed data.
    Automatically maps common alternative fields and ensures valid defaults.
    """

    # 0. Handle dirty data (non-dictionary input)
    if not isinstance(input_data, dict):
        # Even if it's completely wrong, we self-heal to empty dict and let defaults take over
        input_data = {}

    normalized = {
        "prompt": None,
        "styles": None,
        "config": {
            "resolution": None,
            "aspect_ratio": None
        }
    }

    # 1. Map Prompt (modern: prompt, legacy: text, content, description)
    prompt_candidates = ["prompt", "text", "content", "description"]
    for candidate in prompt_candidates:
        if candidate in input_data and isinstance(input_data[candidate], str) and input_data[candidate].strip():
            normalized["prompt"] = input_data[candidate].strip()
            break

    # Default fallback for prompt if none found
    if normalized["prompt"] is None:
        normalized["prompt"] = "默认场景：主角站在城市废墟中，眼神坚定"

    # 2. Map Styles (modern: styles, legacy: tags, style_list)
    styles_candidates = ["styles", "tags", "style_list"]
    extracted_styles = []

    for candidate in styles_candidates:
        if candidate in input_data:
            val = input_data[candidate]
            if isinstance(val, list):
                extracted_styles.extend([str(item).strip() for item in val if item and str(item).strip()])
            elif isinstance(val, str):
                # Handle comma-separated string
                extracted_styles.extend([s.strip() for s in val.split(',') if s.strip()])

    if extracted_styles:
        # Deduplicate while preserving order (using dict fromkeys trick)
        normalized["styles"] = list(dict.fromkeys(extracted_styles))[:8] # cap at 8
    else:
        # Default fallback for styles
        normalized["styles"] = [
            "修仙", "都市逆袭", "韩漫财阀", "热血少年",
            "中式规则怪谈", "赛博朋克", "废土生存", "黑暗奇幻"
        ]

    # 3. Map Config (modern: config.resolution/aspect_ratio, legacy: flat width/height/ratio)

    # First, try to get from nested config
    if "config" in input_data and isinstance(input_data["config"], dict):
        config_data = input_data["config"]
        if "resolution" in config_data and isinstance(config_data["resolution"], str):
            normalized["config"]["resolution"] = config_data["resolution"].strip()
        if "aspect_ratio" in config_data and isinstance(config_data["aspect_ratio"], str):
            normalized["config"]["aspect_ratio"] = config_data["aspect_ratio"].strip()

    # If not found in nested config, look at flat structure
    if not normalized["config"]["resolution"]:
        if "resolution" in input_data and isinstance(input_data["resolution"], str):
            normalized["config"]["resolution"] = input_data["resolution"].strip()
        elif "width" in input_data and "height" in input_data:
            # Reconstruct from width and height
            try:
                w = int(input_data["width"])
                h = int(input_data["height"])
                normalized["config"]["resolution"] = f"{w}x{h}"
            except (ValueError, TypeError):
                pass

    if not normalized["config"]["aspect_ratio"]:
        if "aspect_ratio" in input_data and isinstance(input_data["aspect_ratio"], str):
            normalized["config"]["aspect_ratio"] = input_data["aspect_ratio"].strip()
        elif "ratio" in input_data and isinstance(input_data["ratio"], str):
            normalized["config"]["aspect_ratio"] = input_data["ratio"].strip()

    # Apply defaults if still missing
    if not normalized["config"]["resolution"]:
        normalized["config"]["resolution"] = "1024x1024"
    if not normalized["config"]["aspect_ratio"]:
        normalized["config"]["aspect_ratio"] = "1:1"

    return normalized
