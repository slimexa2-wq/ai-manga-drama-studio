import os
import zipfile
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class BatchEpisodeZipPackagerPlainExplainer:
    """
    多集连载漫剧MP4成片+SRT字幕+剪映草稿+双生态提示词一键ZIP归档打包器
    及大白话摘要结论卡生成器。

    设计原则：
    - 前端极简：一键直达、零确认弹窗
    - 零配置容错：缺参自动设合理默认值
    - 脏数据自愈：对各种非预期格式进行平滑修复，拒绝崩溃
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化打包器
        :param output_dir: 输出目录，若为空则默认取当前目录下的 'manga_exports'
        """
        self.output_dir = output_dir if output_dir else os.path.join(os.getcwd(), "manga_exports")

        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"无法创建输出目录 {self.output_dir}, 降级到当前目录: {e}")
            self.output_dir = "."

    def package(self, batch_data: Any, zip_name: str = "manga_episodes.zip") -> Dict[str, Any]:
        """
        一键打包并生成白话文摘要

        :param batch_data: 包含多集信息的列表或字典
        :param zip_name: 输出的 ZIP 文件名
        :return: 包含生成的 ZIP 路径及不同格式摘要内容的字典
        """
        # 容错与脏数据自愈：确保 batch_data 是一个列表
        if batch_data is None:
            batch_data = []
        elif not isinstance(batch_data, list):
            if isinstance(batch_data, dict):
                batch_data = [batch_data]
            else:
                # 极端脏数据：如果是数字或字符串等
                logger.warning(f"预期列表格式的 batch_data 但收到 {type(batch_data)}，已强转为空列表")
                batch_data = []

        zip_path = os.path.join(self.output_dir, zip_name)

        # 脏数据自愈：清洗每一集的数据格式
        sanitized_data = []
        for i, ep in enumerate(batch_data):
            if not isinstance(ep, dict):
                logger.warning(f"单集数据格式错误，预期字典但收到 {type(ep)}，尝试忽略")
                continue

            sanitized_ep = {
                "episode": ep.get("episode", i + 1),
                "mp4": str(ep.get("mp4", "")).strip() if ep.get("mp4") is not None else "",
                "srt": str(ep.get("srt", "")).strip() if ep.get("srt") is not None else "",
                "draft": str(ep.get("draft", "")).strip() if ep.get("draft") is not None else "",
                "prompts": str(ep.get("prompts", "")).strip() if ep.get("prompts") is not None else "",
                "status": str(ep.get("status", "")).strip().lower() if ep.get("status") is not None else ""
            }

            # 推断缺失状态
            if not sanitized_ep["status"]:
                # 如果有至少一个核心产物，则认为是成功的，否则失败
                if any([sanitized_ep["mp4"], sanitized_ep["srt"], sanitized_ep["draft"], sanitized_ep["prompts"]]):
                    sanitized_ep["status"] = "success"
                else:
                    sanitized_ep["status"] = "failed"

            sanitized_data.append(sanitized_ep)

        # 容错执行打包，屏蔽底层文件异常
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 如果没有数据，至少生成一个空zip，不崩溃
                if not sanitized_data:
                    zipf.writestr("README.txt", "无任何漫剧产物。")

                for ep in sanitized_data:
                    ep_folder = f"episode_{ep['episode']}"

                    # 打包单文件
                    for key in ["mp4", "srt", "prompts"]:
                        filepath = ep[key]
                        if filepath and os.path.isfile(filepath):
                            arcname = f"{ep_folder}/{os.path.basename(filepath)}"
                            zipf.write(filepath, arcname)

                    # 打包目录（剪映草稿等）
                    draft_path = ep["draft"]
                    if draft_path:
                        if os.path.isdir(draft_path):
                            for root, _, files in os.walk(draft_path):
                                for f in files:
                                    abs_path = os.path.join(root, f)
                                    rel_path = os.path.relpath(abs_path, draft_path)
                                    arcname = f"{ep_folder}/draft_project/{rel_path}"
                                    zipf.write(abs_path, arcname)
                        elif os.path.isfile(draft_path):
                            # 如果意外是个单文件，兼容处理
                            arcname = f"{ep_folder}/draft_project/{os.path.basename(draft_path)}"
                            zipf.write(draft_path, arcname)
        except Exception as e:
            logger.error(f"打包 ZIP 过程中遇到非致命错误: {e}")
            # 退化处理，不阻断摘要卡的生成
            pass

        # === 以下为大白话摘要卡生成 ===
        total = len(sanitized_data)
        success_count = sum(1 for ep in sanitized_data if ep["status"] == "success")
        fail_count = total - success_count

        # 1. Markdown 格式
        md_lines = [
            "# 🎬 漫剧多集打包结果摘要",
            "",
            f"**总计处理**：{total} 集",
            f"**成功**：{success_count} 集 ✅",
            f"**失败**：{fail_count} 集 ❌",
            "",
            "## 📦 打包详情"
        ]

        if not sanitized_data:
            md_lines.append("未发现任何集数数据。")

        for ep in sanitized_data:
            icon = "✅" if ep["status"] == "success" else "❌"
            md_lines.append(f"- **第 {ep['episode']} 集** {icon}")

            files = []
            if ep['mp4']: files.append("成片视频")
            if ep['srt']: files.append("字幕")
            if ep['draft']: files.append("剪映草稿")
            if ep['prompts']: files.append("提示词")

            files_str = "、".join(files) if files else "无产物"
            md_lines.append(f"  - 包含: {files_str}")

        md_content = "\n".join(md_lines)

        # 2. HTML 格式 (精美可视化)
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head><meta charset='utf-8'><title>漫剧打包报告</title></head>",
            "<body style='font-family: sans-serif; max-width: 600px; margin: 20px auto; padding: 20px; background-color: #f9f9f9; border-radius: 8px;'>",
            "<h1 style='color: #333;'>🎬 漫剧多集打包结果摘要</h1>",
            "<div style='background: #fff; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;'>",
            f"<p><strong>总计处理</strong>：{total} 集</p>",
            f"<p><strong style='color: green;'>成功</strong>：{success_count} 集 ✅</p>",
            f"<p><strong style='color: red;'>失败</strong>：{fail_count} 集 ❌</p>",
            "</div>",
            "<h2>📦 打包详情</h2>",
            "<ul style='list-style-type: none; padding-left: 0;'>"
        ]

        if not sanitized_data:
            html_lines.append("<p style='color: #777;'>未发现任何集数数据。</p>")

        for ep in sanitized_data:
            icon = "✅" if ep["status"] == "success" else "❌"
            color = "#4CAF50" if ep["status"] == "success" else "#F44336"
            bg_color = "#E8F5E9" if ep["status"] == "success" else "#FFEBEE"

            html_lines.append(f"<li style='background: {bg_color}; margin-bottom: 10px; padding: 10px; border-left: 5px solid {color}; border-radius: 4px;'>")
            html_lines.append(f"<strong style='font-size: 1.1em;'>第 {ep['episode']} 集</strong> {icon}")

            files = []
            if ep['mp4']: files.append("成片视频")
            if ep['srt']: files.append("字幕")
            if ep['draft']: files.append("剪映草稿")
            if ep['prompts']: files.append("提示词")

            files_str = "、".join(files) if files else "无产物"
            html_lines.append(f"<p style='margin: 8px 0 0 0; color: #555; font-size: 0.9em;'>包含: {files_str}</p>")
            html_lines.append("</li>")

        html_lines.append("</ul>")
        html_lines.append("</body></html>")
        html_content = "\n".join(html_lines)

        # 3. JSON 格式
        json_content = json.dumps({
            "summary": {
                "total": total,
                "success": success_count,
                "fail": fail_count
            },
            "episodes": sanitized_data
        }, ensure_ascii=False, indent=2)

        # 静默尝试保存文件
        md_path = os.path.join(self.output_dir, "summary_card.md")
        html_path = os.path.join(self.output_dir, "summary_card.html")
        json_path = os.path.join(self.output_dir, "summary_card.json")

        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(json_content)
        except Exception as e:
            logger.error(f"写入报告文件失败, {e}")
            pass

        return {
            "zip_path": zip_path,
            "report_md": md_content,
            "report_html": html_content,
            "report_json": json_content,
            "md_path": md_path,
            "html_path": html_path,
            "json_path": json_path,
            "success": success_count > 0 or (total == 0) # 0集也算作空操作成功
        }
