import zipfile
import json
import io

def pack_episodes_to_zip(episodes=None, output_path=None, **kwargs):
    """
    一键 ZIP 归档打包器
    :param episodes: list of dict, 多集漫剧数据。如果缺省或类型错误会自动容错清洗。
    :param output_path: str，输出的 zip 文件路径。如果不传，则返回 bytes。
    """
    # 缺参默认兜底与脏数据静默清洗
    if episodes is None:
        episodes = []
    elif not isinstance(episodes, list):
        if isinstance(episodes, dict):
            episodes = [episodes]
        else:
            episodes = []

    out_zip = io.BytesIO() if not output_path else output_path

    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        if not episodes:
            zf.writestr("README.md", b"Empty Manga Drama Studio Archive - Auto Generated")

        for idx, ep in enumerate(episodes):
            if not isinstance(ep, dict):
                ep = {} # 脏数据静默清洗为默认空集

            # 获取集数，容错非数字
            ep_num = ep.get('episode_number', idx + 1)
            try:
                ep_num = int(ep_num)
            except (ValueError, TypeError):
                ep_num = idx + 1

            # 清洗标题
            title = ep.get('title', f"Episode_{ep_num}")
            if not isinstance(title, str) or not title.strip():
                title = f"Episode_{ep_num}"
            else:
                title = title.strip()

            # 非法字符清理
            title = "".join(c for c in title if c.isalnum() or c in ("_", "-", " "))
            # 如果清理后全是下划线、短横线、空格，也算非法
            if not title or not any(c.isalnum() for c in title):
                title = f"Episode_{ep_num}"

            base_dir = f"Ep{ep_num:03d}_{title.replace(' ', '_')}"

            # 1. MP4成片 (假数据，如果有提供则写入)
            mp4_content = ep.get('mp4_content', b"")
            if isinstance(mp4_content, str):
                mp4_content = mp4_content.encode('utf-8')
            elif not isinstance(mp4_content, bytes):
                mp4_content = b""

            if not mp4_content:
                # 默认静默生成一段假数据
                mp4_content = b"fake_mp4_header"
            zf.writestr(f"{base_dir}/video.mp4", mp4_content)

            # 2. SRT 字幕
            srt_content = ep.get('srt_content')
            if not srt_content or not isinstance(srt_content, str):
                srt_content = "1\n00:00:00,000 --> 00:00:05,000\n[Auto-generated Subtitles]"
            zf.writestr(f"{base_dir}/subtitles.srt", srt_content.encode('utf-8'))

            # 3. 剪映草稿
            draft_content = ep.get('draft_content')
            if not draft_content or not isinstance(draft_content, (dict, list)):
                draft_content = {"version": "1.0", "type": "auto-fallback-draft"}
            zf.writestr(f"{base_dir}/draft_content.json", json.dumps(draft_content, ensure_ascii=False, indent=2).encode('utf-8'))

            # 4. 双生态提示词
            prompts = ep.get('prompts')
            if isinstance(prompts, dict) or isinstance(prompts, list):
                prompts_str = json.dumps(prompts, ensure_ascii=False, indent=2)
            elif not prompts or not isinstance(prompts, str):
                prompts_str = "Auto-fallback dual ecosystem prompts."
            else:
                prompts_str = prompts
            zf.writestr(f"{base_dir}/prompts.txt", prompts_str.encode('utf-8'))

    if not output_path:
        return out_zip.getvalue()

    return True
