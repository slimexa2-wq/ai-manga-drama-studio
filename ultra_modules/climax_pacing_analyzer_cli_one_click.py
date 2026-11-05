import argparse
import json
import csv
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_pacing(data: Any = None) -> List[Dict[str, Any]]:
    """
    Pure function to analyze emotional pacing of "shuangwen" scripts.
    Handles dirty data self-healing, missing parameter fallbacks, and boundaries.
    """
    default_data = [
        {"chapter": 1, "text": "主角被退婚，受尽屈辱，家族抛弃"},
        {"chapter": 2, "text": "主角意外获得神秘老爷爷传承，暗中修炼"},
        {"chapter": 3, "text": "家族大比，主角一招击败天才，震惊全场"},
        {"chapter": 4, "text": "神秘势力盯上主角，暗流涌动，不知前途如何"}
    ]

    if data is None or data == []:
        data = default_data

    if not isinstance(data, list):
        data = [{"chapter": 0, "text": str(data)}]

    keywords = {
        "suppression": ["退婚", "屈辱", "废柴", "嘲笑", "抛弃", "压抑"],
        "power_gathering": ["获得", "修炼", "秘籍", "传承", "突破", "蓄力"],
        "climax": ["大比", "击败", "震惊", "打脸", "爆发", "无敌"],
        "suspense": ["神秘", "暗流", "悬念", "危机", "未知", "前途"]
    }

    results = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            item = {"chapter": idx + 1, "text": str(item)}

        text = item.get("text", "")
        if text is None:
            text = ""
        elif not isinstance(text, str):
            text = str(text)

        chapter = item.get("chapter", idx + 1)
        if not isinstance(chapter, (int, float)):
            try:
                chapter = int(chapter)
            except (ValueError, TypeError):
                chapter = idx + 1

        scores = {k: 0.0 for k in keywords}
        for k, words in keywords.items():
            for w in words:
                if w in text:
                    scores[k] += 1.0

        max_score = -1.0
        dominant = "neutral"
        for k, v in scores.items():
            if v > max_score and v > 0:
                max_score = v
                dominant = k

        results.append({
            "chapter": chapter,
            "text": text,
            "suppression_score": scores["suppression"],
            "power_gathering_score": scores["power_gathering"],
            "climax_score": scores["climax"],
            "suspense_score": scores["suspense"],
            "dominant_emotion": dominant
        })

    return results

def output_adapter(data: List[Dict[str, Any]], format_type: str = "json", output_path: str = "output"):
    """
    Seamless JSON/Excel(CSV) dual-mode output adapter.
    """
    if format_type.lower() == "json":
        path = f"{output_path}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"JSON output saved to {path}")
    else:
        path = f"{output_path}.csv"
        if not data:
            with open(path, "w", encoding="utf-8-sig", newline='') as f:
                pass
            return path

        keys = list(data[0].keys())
        with open(path, "w", encoding="utf-8-sig", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Excel-compatible CSV output saved to {path}")
    return path

def main():
    parser = argparse.ArgumentParser(description="爽文剧本情绪曲线自动诊断与节奏加密器 (One-Click CLI)")
    parser.add_argument("--format", type=str, default="json", choices=["json", "excel", "csv"],
                        help="Output format: json, excel, or csv (default: json)")
    parser.add_argument("--output", type=str, default="pacing_analysis",
                        help="Output file prefix (default: pacing_analysis)")

    args = parser.parse_args()
    fmt = "csv" if args.format == "excel" else args.format

    logging.info("Starting Climax Pacing Analyzer...")
    analyzed_data = analyze_pacing()

    output_adapter(analyzed_data, fmt, args.output)
    logging.info("Analysis complete.")

if __name__ == "__main__":
    main()
