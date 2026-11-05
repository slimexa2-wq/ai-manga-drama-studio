import json
import csv
import sys
import argparse
import os
from typing import Optional, Dict, Any

try:
    from ultra_modules.dialogue_lip_sync_timer_core_engine import calculate_scene_duration
except ImportError:
    from dialogue_lip_sync_timer_core_engine import calculate_scene_duration

class DialogueLipSyncTimerCLIOneClick:
    """
    一键运行的命令行封装，支持零参数调用和多格式无感直出。
    """

    @staticmethod
    def process_and_export(
        text: Optional[str] = None,
        output_format: str = "all",
        output_dir: str = "."
    ) -> Dict[str, Any]:
        """
        处理文本并导出 JSON / Excel(CSV)
        """
        # 容错：缺参自动设合理默认值，脏数据静默自愈
        if text is None or not isinstance(text, str) or not text.strip():
            text = "这是一段默认测试文本，包含了标点符号！用于一键跑通测试。"

        # 调用核心引擎，容错已在 engine 中处理
        duration = calculate_scene_duration(text=text)

        result_data = {
            "text": text,
            "duration": duration,
            "status": "success"
        }

        exports = {}

        # 确保输出目录存在
        if output_format in ["all", "json", "excel", "csv"]:
            os.makedirs(output_dir, exist_ok=True)

            if output_format in ["all", "json"]:
                json_path = os.path.join(output_dir, "dialogue_timing.json")
                try:
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(result_data, f, ensure_ascii=False, indent=2)
                    exports["json"] = json_path
                except Exception as e:
                    exports["json_error"] = str(e)

            if output_format in ["all", "excel", "csv"]:
                csv_path = os.path.join(output_dir, "dialogue_timing.csv")
                try:
                    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Text", "Duration", "Status"])
                        writer.writerow([result_data["text"], result_data["duration"], result_data["status"]])
                    exports["excel"] = csv_path
                except Exception as e:
                    exports["excel_error"] = str(e)

        result_data["exports"] = exports
        return result_data

def main():
    parser = argparse.ArgumentParser(description="Dialogue Lip Sync Timer CLI - 一键对齐计算器")
    parser.add_argument("--text", type=str, default=None, help="Input text, defaults to a test string if omitted")
    parser.add_argument("--output-format", type=str, default="all", choices=["all", "json", "excel", "csv"], help="Export format")
    parser.add_argument("--output-dir", type=str, default=".", help="Directory to save the exported files")

    # 零配置容错：直接解析
    args, _ = parser.parse_known_args()

    result = DialogueLipSyncTimerCLIOneClick.process_and_export(
        text=args.text,
        output_format=args.output_format,
        output_dir=args.output_dir
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
