import argparse
import json
import csv
import sys
import io
import os
from typing import Optional, Any
from ultra_modules.golden_3s_hook_splitter_plain_explainer import Golden3sHookSplitter

DEFAULT_NOVEL_TEXT = "这是一个默认的网文小说测试文本。开局主角就遭遇了退婚，这简直是奇耻大辱！三十年河东，三十年河西，莫欺少年穷！就在他绝望之际，突然发现戒指里藏着一个老爷爷..."


def process_novel_one_click(text: Optional[Any] = None, output_format: str = "json", output_path: Optional[str] = None) -> str:
    """
    一键极简拆解器核心逻辑：零配置、自适应容错
    """
    # 缺参自动设合理默认值 / 脏数据自愈
    if text is None or str(text).strip() == "":
        text = DEFAULT_NOVEL_TEXT
    else:
        text = str(text)

    if output_format not in ["json", "excel", "csv"]:
        output_format = "json"

    splitter = Golden3sHookSplitter()
    episodes = splitter.split_to_episodes(text, chars_per_episode=1000)

    # JSON 模式
    if output_format == "json":
        result = splitter.export_json(episodes)
    # Excel/CSV 模式
    else:
        output_io = io.StringIO()
        writer = csv.writer(output_io)
        writer.writerow(["集数", "黄金前3秒钩子", "集末悬念", "大白话摘要", "正文内容"])
        for ep in episodes:
            writer.writerow([
                ep.get("episode", ""),
                ep.get("hook", ""),
                ep.get("cliffhanger", ""),
                ep.get("summary", ""),
                ep.get("content", "")
            ])
        result = output_io.getvalue()

    # 尝试写入文件（零确认容错，若失败则退化为只返回字符串）
    if output_path:
        try:
            if os.path.isdir(output_path):
                # 如果传入的是目录，自动追加默认文件名
                ext = ".json" if output_format == "json" else ".csv"
                output_path = os.path.join(output_path, f"auto_export{ext}")

            with open(output_path, "w", encoding="utf-8", newline="") as f:
                f.write(result)
        except OSError:
            # 极度严密容错：失败不阻断，默默吞下异常，只在内存中返回
            pass

    return result


def main():
    parser = argparse.ArgumentParser(description="一键多集拆解器 CLI")
    parser.add_argument("--text", type=str, default="", help="输入的小说文本内容")
    parser.add_argument("--format", type=str, choices=["json", "excel", "csv"], default="json", help="输出格式：json 或 excel")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径")

    args = parser.parse_args()

    result = process_novel_one_click(args.text, args.format, args.output)

    # 命令行直接打印，方便对接
    print(result)


if __name__ == "__main__":
    main()
