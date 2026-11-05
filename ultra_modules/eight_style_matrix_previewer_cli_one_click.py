import json
import csv
import io
import sys
import argparse
import random
from typing import Dict, Any, List

class EightStyleMatrixPreviewer:
    """
    8-Style Matrix Previewer.
    Generates previews for 8 styles (e.g., Xianxia, Urban, Chaebol, Shounen, Chinese Rules).
    """

    STYLES = [
        "修仙 (Xianxia)",
        "都市逆袭 (Urban Rebirth)",
        "韩漫财阀 (Korean Chaebol)",
        "热血少年 (Shounen)",
        "中式规则怪谈 (Chinese Rules Horror)",
        "末日废土 (Post-Apocalyptic)",
        "赛博朋克 (Cyberpunk)",
        "古风大女主 (Historical Heroine)"
    ]

    def __init__(self, output_format: str = "json", fallback_mode: bool = True):
        self.output_format = output_format if output_format in ["json", "csv"] else "json"
        self.fallback_mode = fallback_mode

    def sanitize_input(self, text: Any) -> str:
        """Self-healing for dirty data: strip extra spaces and handle empty/None."""
        if not text or not isinstance(text, str) or not text.strip():
            if self.fallback_mode:
                return "默认极简片段"
            return ""
        return text.strip()

    def generate_matrix(self, script_text: Any) -> List[Dict[str, Any]]:
        """Generates the 8-style matrix."""
        clean_text = self.sanitize_input(script_text)

        matrix = []
        for i, style in enumerate(self.STYLES):
            # Deterministic simulation of output generation
            preview_url = f"https://mock-image-server.local/preview_{i}_{hash(clean_text) % 1000}.png"
            prompt = f"[{style}] style rendition of: {clean_text}"

            matrix.append({
                "style": style,
                "prompt": prompt,
                "preview_url": preview_url,
                "confidence_score": 0.85 + (random.random() * 0.15)
            })

        return matrix

    def export(self, matrix: List[Dict[str, Any]]) -> str:
        """Exports to JSON or CSV (acting as 'Excel' proxy)."""
        if self.output_format == "json":
            return json.dumps(matrix, ensure_ascii=False, indent=2)
        else:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["style", "prompt", "preview_url", "confidence_score"])
            writer.writeheader()
            for row in matrix:
                writer.writerow(row)
            return output.getvalue()

    def process_one_click(self, script_text: Any = None) -> str:
        """
        One-click entrypoint: takes an optional script_text, generates matrix,
        and returns the formatted output string.
        """
        # zero-config parameter fallback is handled inside generate_matrix via sanitize_input
        matrix = self.generate_matrix(script_text)
        return self.export(matrix)

def main():
    parser = argparse.ArgumentParser(description="One-Click 8-Style Matrix Previewer")
    # Using simple args to meet zero-param/config requirement
    parser.add_argument("--script", type=str, default="", help="Input script text (optional)")
    parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Output format (json/csv)")

    args = parser.parse_args()

    previewer = EightStyleMatrixPreviewer(output_format=args.format)
    result = previewer.process_one_click(args.script)
    print(result)

if __name__ == "__main__":
    main()
