import argparse
import json
import csv
import sys
from typing import Dict, Any, List, Optional

def get_default_dna() -> Dict[str, Any]:
    """Returns the default character DNA configuration."""
    return {
        "hair_color": "black",
        "eye_color": "dark brown",
        "clothing": "casual school uniform",
        "style_suffix": "anime style, masterpiece, best quality",
        "fixed_seed": 424242
    }

def sanitize_dna(input_dna: Any) -> Dict[str, Any]:
    """
    Sanitizes the input DNA, providing default values for missing or invalid (dirty) data.
    Ensures zero-configuration fault tolerance.
    """
    defaults = get_default_dna()

    # If the input is completely malformed (e.g., None, list, int), fallback to defaults.
    if not isinstance(input_dna, dict):
        return defaults.copy()

    clean_dna = {}

    # Text attributes: fallback if not string or empty string
    for key in ["hair_color", "eye_color", "clothing", "style_suffix"]:
        val = input_dna.get(key)
        if not isinstance(val, str) or not val.strip():
            clean_dna[key] = defaults[key]
        else:
            clean_dna[key] = str(val).strip()

    # Seed attribute: fallback if not int or convertible to int
    seed_val = input_dna.get("fixed_seed")
    if isinstance(seed_val, bool): # bool is subclass of int, so need to check explicitly
        clean_dna["fixed_seed"] = defaults["fixed_seed"]
    elif isinstance(seed_val, int):
        clean_dna["fixed_seed"] = seed_val
    elif isinstance(seed_val, str) and seed_val.strip().lstrip('-').isdigit():
        clean_dna["fixed_seed"] = int(seed_val.strip())
    else:
        clean_dna["fixed_seed"] = defaults["fixed_seed"]

    return clean_dna

def generate_episodes_dna(base_dna: Dict[str, Any], episodes: int = 100) -> List[Dict[str, Any]]:
    """Generates DNA profiles for the given number of episodes."""
    safe_dna = sanitize_dna(base_dna)
    # Ensure episode number is generated purely functionally
    return [{"episode": i, **safe_dna} for i in range(1, episodes + 1)]

def export_to_json(dna_list: List[Dict[str, Any]], filepath: str) -> None:
    """Exports DNA list to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(dna_list, f, indent=4, ensure_ascii=False)

def export_to_csv(dna_list: List[Dict[str, Any]], filepath: str) -> None:
    """Exports DNA list to a CSV (Excel compatible) file."""
    if not dna_list:
        return
    keys = list(dna_list[0].keys())
    # utf-8-sig adds BOM so Excel can open it seamlessly without garbled text
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(dna_list)

def run_pipeline(input_dna: Optional[Dict[str, Any]] = None, output_format: str = 'both', output_prefix: str = 'character_dna_100_episodes') -> Dict[str, str]:
    """
    Runs the complete pipeline and returns paths to generated files.
    Returns a dict mapping format to file path.
    """
    if input_dna is None:
        input_dna = {}

    dna_list = generate_episodes_dna(input_dna, 100)
    generated_files = {}

    if output_format in ('json', 'both'):
        json_path = f"{output_prefix}.json"
        export_to_json(dna_list, json_path)
        generated_files['json'] = json_path

    if output_format in ('excel', 'csv', 'both'):
        csv_path = f"{output_prefix}.csv"
        export_to_csv(dna_list, csv_path)
        generated_files['csv'] = csv_path

    return generated_files

def main():
    parser = argparse.ArgumentParser(description="Character DNA Seed Locker CLI (One-Click)")
    parser.add_argument("--hair", type=str, default="", help="Character hair color")
    parser.add_argument("--eye", type=str, default="", help="Character eye color")
    parser.add_argument("--clothing", type=str, default="", help="Character clothing")
    parser.add_argument("--style", type=str, default="", help="Art style suffix")
    parser.add_argument("--seed", type=str, default="", help="Fixed seed (integer)")
    parser.add_argument("--format", type=str, choices=['json', 'excel', 'csv', 'both'], default='both', help="Output format")
    parser.add_argument("--prefix", type=str, default="character_dna_100_episodes", help="Output file prefix")

    args = parser.parse_args()

    # Construct input dict, ignoring empty args to let sanitize handle defaults
    input_dna = {}
    if args.hair: input_dna["hair_color"] = args.hair
    if args.eye: input_dna["eye_color"] = args.eye
    if args.clothing: input_dna["clothing"] = args.clothing
    if args.style: input_dna["style_suffix"] = args.style
    if args.seed: input_dna["fixed_seed"] = args.seed

    try:
        output_files = run_pipeline(input_dna, args.format, args.prefix)
        print("Successfully locked Character DNA for 100 episodes.")
        for fmt, path in output_files.items():
            print(f"Generated {fmt.upper()}: {path}")
    except Exception as e:
        print(f"Error during DNA locking: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
