import zipfile
import json
import io

class AuditTracer:
    """后台静默记录每一步折算/去重/修复依据供复盘的审计追踪器。"""
    def __init__(self):
        self.traces = []

    def log_correction(self, episode_idx, field, old_val, new_val, reason):
        # 记录差异高亮对比的依据
        self.traces.append({
            "episode_index": episode_idx,
            "field": field,
            "old_value": str(old_val) if old_val is not None else "None",
            "new_value": str(new_val),
            "reason": reason,
            "diff_highlight": f"Changed '{field}' from '{old_val}' to '{new_val}'"
        })

    def get_trace(self):
        return self.traces


def sanitize_episode_data(episode_raw, idx, tracer):
    """清理并修复单集数据，同时将修改记录写入tracer"""
    if not isinstance(episode_raw, dict):
        tracer.log_correction(idx, "episode_type", type(episode_raw).__name__, "dict", "Invalid episode type, auto-fallback to empty dict")
        episode_raw = {}

    clean_ep = {}

    # 1. Episode Number
    raw_ep_num = episode_raw.get('episode_number', idx + 1)
    ep_num = raw_ep_num
    try:
        ep_num = int(ep_num)
    except (ValueError, TypeError):
        ep_num = idx + 1
        tracer.log_correction(idx, "episode_number", raw_ep_num, ep_num, "Invalid episode number type, fallback to index + 1")

    clean_ep['episode_number'] = ep_num

    # 2. Title
    raw_title = episode_raw.get('title')
    title = raw_title
    if title is None:
        title = f"Episode_{ep_num}"
        tracer.log_correction(idx, "title", "None", title, "Title missing, fallback to default")
    elif not isinstance(title, str) or not title.strip():
        title = f"Episode_{ep_num}"
        tracer.log_correction(idx, "title", type(raw_title).__name__ if raw_title is not None else "Empty string", title, "Title empty or invalid type, fallback to default")
    else:
        title = title.strip()
        filtered_title = "".join(c for c in title if c.isalnum() or c in ("_", "-", " "))
        if not filtered_title or not any(c.isalnum() for c in filtered_title):
            title = f"Episode_{ep_num}"
            tracer.log_correction(idx, "title", raw_title, title, "Title contains only invalid chars, fallback to default")
        elif filtered_title != raw_title:
            title = filtered_title
            tracer.log_correction(idx, "title", raw_title, title, "Sanitized invalid characters from title")

    clean_ep['title'] = title

    # 3. MP4
    raw_mp4 = episode_raw.get('mp4_content', b"")
    mp4_content = raw_mp4
    if isinstance(mp4_content, str):
        mp4_content = mp4_content.encode('utf-8')
        tracer.log_correction(idx, "mp4_content", "str", "bytes", "Encoded string to bytes")
    elif not isinstance(mp4_content, bytes):
        mp4_content = b""
        tracer.log_correction(idx, "mp4_content", type(raw_mp4).__name__, "bytes", "Invalid mp4_content type, fallback to empty")

    if not mp4_content:
        mp4_content = b"fake_mp4_header"
        if not raw_mp4:
             # Just providing fallback for missing data, no type error
             tracer.log_correction(idx, "mp4_content", "None/Empty", "fake_mp4_header", "Empty MP4 content, fallback to default fake header")

    clean_ep['mp4_content'] = mp4_content

    # 4. SRT
    raw_srt = episode_raw.get('srt_content')
    srt_content = raw_srt
    if not srt_content or not isinstance(srt_content, str):
        srt_content = "1\n00:00:00,000 --> 00:00:05,000\n[Auto-generated Subtitles]"
        tracer.log_correction(idx, "srt_content", type(raw_srt).__name__ if raw_srt is not None else "None", "default_srt_string", "Missing or invalid SRT content, fallback to default")

    clean_ep['srt_content'] = srt_content

    # 5. Draft Content
    raw_draft = episode_raw.get('draft_content')
    draft_content = raw_draft
    if not draft_content or not isinstance(draft_content, (dict, list)):
        draft_content = {"version": "1.0", "type": "auto-fallback-draft"}
        tracer.log_correction(idx, "draft_content", type(raw_draft).__name__ if raw_draft is not None else "None", "default_draft_dict", "Missing or invalid draft content, fallback to default JSON")

    clean_ep['draft_content'] = draft_content

    # 6. Prompts
    raw_prompts = episode_raw.get('prompts')
    prompts = raw_prompts
    if isinstance(prompts, dict) or isinstance(prompts, list):
         prompts_str = json.dumps(prompts, ensure_ascii=False, indent=2)
         tracer.log_correction(idx, "prompts", type(raw_prompts).__name__, "json_string", "Serialized dict/list to JSON string")
    elif not prompts or not isinstance(prompts, str):
         prompts_str = "Auto-fallback dual ecosystem prompts."
         tracer.log_correction(idx, "prompts", type(raw_prompts).__name__ if raw_prompts is not None else "None", "default_prompts_string", "Missing or invalid prompts, fallback to default string")
    else:
         prompts_str = prompts

    clean_ep['prompts'] = prompts_str

    return clean_ep

def pack_episodes_with_audit(episodes=None, output_path=None, **kwargs):
    """
    带审计追踪的一键 ZIP 归档打包器
    返回 (zip_result, audit_trace)
    """
    tracer = AuditTracer()

    if episodes is None:
        tracer.log_correction(-1, "episodes", "None", "[]", "Episodes is None, fallback to empty list")
        episodes = []
    elif not isinstance(episodes, list):
        if isinstance(episodes, dict):
            tracer.log_correction(-1, "episodes", "dict", "list[dict]", "Episodes is dict, wrapping in list")
            episodes = [episodes]
        else:
            tracer.log_correction(-1, "episodes", type(episodes).__name__, "[]", "Episodes is invalid type, fallback to empty list")
            episodes = []

    out_zip = io.BytesIO() if not output_path else output_path

    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        if not episodes:
            zf.writestr("README.md", b"Empty Manga Drama Studio Archive - Auto Generated")

        for idx, raw_ep in enumerate(episodes):
            clean_ep = sanitize_episode_data(raw_ep, idx, tracer)

            ep_num = clean_ep['episode_number']
            title = clean_ep['title']

            base_dir = f"Ep{ep_num:03d}_{title.replace(' ', '_')}"

            # Write files
            zf.writestr(f"{base_dir}/video.mp4", clean_ep['mp4_content'])
            zf.writestr(f"{base_dir}/subtitles.srt", clean_ep['srt_content'].encode('utf-8'))
            zf.writestr(f"{base_dir}/draft_content.json", json.dumps(clean_ep['draft_content'], ensure_ascii=False, indent=2).encode('utf-8'))
            zf.writestr(f"{base_dir}/prompts.txt", clean_ep['prompts'].encode('utf-8'))

    zip_res = out_zip.getvalue() if not output_path else True
    return zip_res, tracer.get_trace()
