import argparse
import json
import csv
import sys
from typing import Dict, Any, List, Optional

def get_default_config() -> Dict[str, Any]:
    """Returns the default turnaround sheet configuration."""
    return {
        "character_desc": "a young anime boy with black hair and blue eyes, wearing casual streetwear",
        "style": "anime style, masterpiece, best quality, flat color, concept art",
        "views": ["front view", "side view", "back view"],
        "expressions": ["neutral", "happy", "sad", "angry", "surprised"]
    }

def sanitize_input(input_data: Any) -> Dict[str, Any]:
    """
    Sanitizes the input data, providing default values for missing or invalid (dirty) data.
    Ensures zero-configuration fault tolerance.
    """
    defaults = get_default_config()

    if not isinstance(input_data, dict):
        return defaults.copy()

    clean_data = {}

    # String parameters
    for key in ["character_desc", "style"]:
        val = input_data.get(key)
        if not isinstance(val, str) or not val.strip():
            clean_data[key] = defaults[key]
        else:
            clean_data[key] = str(val).strip()

    # List parameters
    for key in ["views", "expressions"]:
        val = input_data.get(key)
        if not isinstance(val, list) or not val:
            clean_data[key] = defaults[key]
        else:
            # Clean list items
            cleaned_list = []
            for item in val:
                if isinstance(item, str) and item.strip():
                    cleaned_list.append(str(item).strip())

            if not cleaned_list:
                clean_data[key] = defaults[key]
            else:
                clean_data[key] = cleaned_list

    return clean_data

def generate_prompts(base_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generates the structured prompts for the turnaround sheet."""
    safe_data = sanitize_input(base_data)
    prompts = []

    char_desc = safe_data["character_desc"]
    style = safe_data["style"]

    # 1. Turnaround sheet (multiple views in one image)
    views_str = ", ".join(safe_data["views"])
    turnaround_prompt = f"Character design sheet, multiple views: {views_str}. {char_desc}. {style}. White background, full body."
    prompts.append({
        "type": "turnaround_sheet",
        "target": "multiple views",
        "prompt": turnaround_prompt
    })

    # 2. Individual expressions
    for expr in safe_data["expressions"]:
        expr_prompt = f"Character expression sheet, {expr} expression, face close-up. {char_desc}. {style}. White background."
        prompts.append({
            "type": "expression",
            "target": expr,
            "prompt": expr_prompt
        })

    return prompts

def export_to_json(data: List[Dict[str, str]], filepath: str) -> None:
    """Exports data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def export_to_csv(data: List[Dict[str, str]], filepath: str) -> None:
    """Exports data to a CSV (Excel compatible) file."""
    if not data:
        return
    keys = list(data[0].keys())
    # utf-8-sig adds BOM so Excel can open it seamlessly without garbled text
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

def run_pipeline(input_data: Optional[Dict[str, Any]] = None, output_format: str = 'both', output_prefix: str = 'gpt_image_turnaround_sheet') -> Dict[str, str]:
    """
    Runs the complete pipeline and returns paths to generated files.
    Returns a dict mapping format to file path.
    """
    if input_data is None:
        input_data = {}

    prompts = generate_prompts(input_data)
    generated_files = {}

    if output_format in ('json', 'both'):
        json_path = f"{output_prefix}.json"
        export_to_json(prompts, json_path)
        generated_files['json'] = json_path

    if output_format in ('excel', 'csv', 'both'):
        csv_path = f"{output_prefix}.csv"
        export_to_csv(prompts, csv_path)
        generated_files['csv'] = csv_path

    return generated_files

def main():
    parser = argparse.ArgumentParser(description="GPT-Image-2 Character Turnaround & Expression Sheet CLI (One-Click)")
    parser.add_argument("--character", type=str, default="", help="Character description")
    parser.add_argument("--style", type=str, default="", help="Art style")
    parser.add_argument("--views", type=str, default="", help="Comma separated views")
    parser.add_argument("--expressions", type=str, default="", help="Comma separated expressions")
    parser.add_argument("--format", type=str, choices=['json', 'excel', 'csv', 'both'], default='both', help="Output format")
    parser.add_argument("--prefix", type=str, default="gpt_image_turnaround_sheet", help="Output file prefix")

    args = parser.parse_args()

    input_data = {}
    if args.character: input_data["character_desc"] = args.character
    if args.style: input_data["style"] = args.style
    if args.views: input_data["views"] = [v.strip() for v in args.views.split(",") if v.strip()]
    if args.expressions: input_data["expressions"] = [e.strip() for e in args.expressions.split(",") if e.strip()]

    try:
        output_files = run_pipeline(input_data, args.format, args.prefix)
        print("Successfully generated GPT-Image-2 Turnaround and Expression Sheet Prompts.")
        for fmt, path in output_files.items():
            print(f"Generated {fmt.upper()}: {path}")
    except Exception as e:
        print(f"Error during generation: {e}")
        sys.exit(1)

if __name__ == "__main__":  # pragma: no cover
    main()
