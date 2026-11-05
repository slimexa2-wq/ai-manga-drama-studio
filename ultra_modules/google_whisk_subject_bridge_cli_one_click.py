import json
import csv
import io
import argparse
import sys

class WhiskPayloadBuilder:
    def __init__(self):
        pass

    def build_payload(self, subject=None, style=None, scene=None):
        # 脏数据自愈：处理非法类型和前后空格
        if subject is not None and not isinstance(subject, str):
            subject = str(subject)
        if style is not None and not isinstance(style, str):
            style = str(style)
        if scene is not None and not isinstance(scene, str):
            scene = str(scene)

        subject = subject.strip() if subject else ""
        style = style.strip() if style else ""
        scene = scene.strip() if scene else ""

        # 缺参自动设合理默认值
        subject = subject if subject else "Default Character"
        style = style if style else "Cinematic, detailed"
        scene = scene if scene else "Default Studio Background"

        return {
            "whisk_payload": {
                "subject_slot": subject,
                "style_slot": style,
                "scene_slot": scene
            }
        }

    def export_json(self, payload):
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def export_csv(self, payload):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Subject", "Style", "Scene"])
        data = payload.get("whisk_payload", {})
        writer.writerow([data.get("subject_slot", ""), data.get("style_slot", ""), data.get("scene_slot", "")])
        return output.getvalue()


def cli_main():
    parser = argparse.ArgumentParser(description="Google Labs Whisk Subject/Style/Scene CLI")
    # 极简调用，全是可选参数，默认运行跑通
    parser.add_argument("--subject", type=str, default="", help="Subject of the scene")
    parser.add_argument("--style", type=str, default="", help="Style of the scene")
    parser.add_argument("--scene", type=str, default="", help="Scene description")
    parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Output format")

    args = parser.parse_args()

    builder = WhiskPayloadBuilder()
    payload = builder.build_payload(args.subject, args.style, args.scene)

    if args.format == "json":
        output = builder.export_json(payload)
    else:
        output = builder.export_csv(payload)

    # 一键直出
    print(output)
    return output

if __name__ == "__main__":
    cli_main()
