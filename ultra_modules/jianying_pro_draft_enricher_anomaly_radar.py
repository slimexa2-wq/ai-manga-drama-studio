import math
import copy

def enrich_and_scan_draft(draft_content=None, options=None):
    """
    一键注入花字特效、震屏转场、KenBurns运镜与BGM。
    自动静默扫描时长异常值(IQR/Percentile)并进行红黄绿标记。
    缺参自动兜底，脏数据自动自愈。
    """
    if draft_content is None:
        draft_content = {}
    if not isinstance(draft_content, dict):
        draft_content = {"tracks": [], "materials": {}}

    draft = copy.deepcopy(draft_content)

    if options is None:
        options = {}
    if not isinstance(options, dict):
        options = {}

    bgm_path = options.get("bgm_path", "default_bgm.mp3")
    enable_kenburns = options.get("enable_kenburns", True)
    enable_shake = options.get("enable_shake", True)

    # 脏数据自愈：处理缺失的材料和轨道
    materials = draft.get("materials")
    if not isinstance(materials, dict):
        materials = {}

    tracks = draft.get("tracks")
    if not isinstance(tracks, list):
        tracks = []

    # BGM注入
    if "audios" not in materials or not isinstance(materials["audios"], list):
        materials["audios"] = []
    materials["audios"].append({"id": "auto_bgm_1", "path": bgm_path, "type": "bgm"})

    # 花字特效、震屏转场等注入
    if "effects" not in materials or not isinstance(materials["effects"], list):
        materials["effects"] = []

    if enable_kenburns:
        materials["effects"].append({"id": "fx_kenburns", "name": "KenBurns运镜", "type": "video_effect"})
    if enable_shake:
        materials["effects"].append({"id": "tx_shake", "name": "震屏转场", "type": "transition"})

    draft["materials"] = materials

    # 异常值扫描雷达 (Anomaly Radar)
    durations = []
    segments_ref = []

    for track in tracks:
        if not isinstance(track, dict):
            continue
        segments = track.get("segments")
        if not isinstance(segments, list):
            continue

        for seg in segments:
            if not isinstance(seg, dict):
                continue
            dur = seg.get("duration")
            # 脏数据自愈：缺失、非数字、NaN、负数等
            if dur is None or not isinstance(dur, (int, float)) or math.isnan(dur) or dur <= 0:
                dur = 3000000  # 合理默认值：3秒 (微秒级)
                seg["duration"] = dur
                seg["_auto_healed"] = True

            durations.append(dur)
            segments_ref.append(seg)

    # 统计分布扫描
    n = len(durations)
    if n > 0:
        sorted_durs = sorted(durations)

        # 极简红黄绿三色标记器 (Top 3% / Bottom 3%)
        count_3 = int(n * 0.03)
        has_3_percent = count_3 > 0

        if has_3_percent:
            p_bottom = sorted_durs[count_3 - 1]
            p_top = sorted_durs[n - count_3]
        else:
            p_bottom = -1
            p_top = float('inf')

        # IQR 计算用于黄色警告
        q1_idx = int(n * 0.25)
        q3_idx = int(n * 0.75)
        q1 = sorted_durs[q1_idx]
        q3 = sorted_durs[q3_idx]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        for seg in segments_ref:
            d = seg["duration"]

            # 判断是否是 Top 3% 异常
            is_extreme = False
            if has_3_percent and (d <= p_bottom or d >= p_top) and (p_bottom < p_top):
                # 进一步判断是否真的偏离，防止所有值一样
                is_extreme = True

            if is_extreme:
                seg["anomaly_marker"] = "RED"
                seg["anomaly_reason"] = f"人工关注：时长 {d} 属于前3%或后3%极端异常值"
            elif (d < lower_bound or d > upper_bound) and iqr > 0:
                seg["anomaly_marker"] = "YELLOW"
                seg["anomaly_reason"] = f"静默放行：时长 {d} 偏离常规IQR范围"
            else:
                seg["anomaly_marker"] = "GREEN"
                seg["anomaly_reason"] = "正常"

    draft["tracks"] = tracks
    return draft

if __name__ == '__main__':  # pragma: no cover
    print("AI Manga Drama Studio - Jianying Pro Draft Enricher & Anomaly Radar")
