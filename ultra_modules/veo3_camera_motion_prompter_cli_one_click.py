import argparse
import json
import csv
import io
import random

def generate_motion_prompt(camera_movements=None, subjects=None, environment=None, seed=None):
    """
    Pure function to generate a structured camera motion prompt for Veo 3 and Sora 2.
    """
    # Default values for missing parameters (零配置容错、缺参自动设合理默认值)
    default_movements = ["slow push in", "dynamic crane shot", "fast pan right", "orbit around"]
    default_subjects = ["a lone wanderer", "a glowing artifact", "two people conversing"]
    default_env = "a foggy futuristic cityscape at dusk"

    if camera_movements is None:
        camera_movements = default_movements
    if subjects is None:
        subjects = default_subjects
    if environment is None:
        environment = default_env

    # Data self-healing / cleaning (脏数据自愈)
    if not isinstance(camera_movements, (list, tuple)):
        camera_movements = [camera_movements]
    if not isinstance(subjects, (list, tuple)):
        subjects = [subjects]

    clean_movements = [str(m).strip() for m in camera_movements if m is not None and str(m).strip()]
    clean_subjects = [str(s).strip() for s in subjects if s is not None and str(s).strip()]

    # Handle environment specifically
    if environment is not None:
        clean_env = str(environment).strip()
    else:
        clean_env = ""

    # Default fallback if empty after cleaning
    if not clean_movements:
        clean_movements = default_movements
    if not clean_subjects:
        clean_subjects = default_subjects
    if not clean_env:
        clean_env = default_env

    # Use localized random instance to avoid global state mutation
    rng = random.Random(seed)

    selected_movement = rng.choice(clean_movements)
    selected_subject = rng.choice(clean_subjects)

    prompt = (
        f"Cinematic {selected_movement}, focusing on {selected_subject}, "
        f"set in {clean_env}. Highly detailed, 8k resolution, photorealistic, "
        f"cinematic lighting, shot on 35mm lens, depth of field."
    )

    return {
        "movement": selected_movement,
        "subject": selected_subject,
        "environment": clean_env,
        "prompt": prompt,
        "model_target": "Veo 3 / Sora 2"
    }

def format_output_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False)

def format_output_excel(data):
    # Outputs CSV format which can be opened seamlessly in Excel
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data.keys())
    writer.writeheader()
    writer.writerow(data)
    return output.getvalue().strip()

def cli_entrypoint(output_format="json", seed=None):
    """
    一键直达、零确认弹窗 (One-click entrypoint, zero confirmation popups)
    """
    data = generate_motion_prompt(seed=seed)

    # Self-healing for output_format
    if not isinstance(output_format, str):
        output_format = "json"

    output_format = output_format.strip().lower()
    if output_format not in ["json", "excel", "csv"]:
        output_format = "json"

    if output_format in ["excel", "csv"]:
        return format_output_excel(data)
    return format_output_json(data)

def main():
    parser = argparse.ArgumentParser(description="Google Veo 3 / Sora 2 Camera Motion Prompter")
    parser.add_argument("--format", type=str, default="json", help="Output format: json or excel")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")

    args = parser.parse_args()

    print(cli_entrypoint(output_format=args.format, seed=args.seed))

if __name__ == "__main__":
    main()
