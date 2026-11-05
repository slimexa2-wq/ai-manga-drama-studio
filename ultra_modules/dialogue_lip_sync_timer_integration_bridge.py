import re

class DialogueLipSyncTimerBridge:
    """
    台词字数、标点停顿与配音音频波形峰值自动对齐分镜时长计算器
    跨系统数据契约无缝桥接与Schema版本自动向前兼容转换器
    """

    SCHEMA_MAPPING = {
        "text": "dialogue_text",
        "content": "dialogue_text",
        "audio_length": "audio_duration_ms",
        "voice_length": "audio_duration_ms",
        "length_ms": "audio_duration_ms",
        "wave_peaks": "waveform_peaks",
        "peaks": "waveform_peaks",
        "pause": "punctuation_pause_ms",
        "pause_ms": "punctuation_pause_ms",
    }

    @classmethod
    def normalize_payload(cls, payload: dict) -> dict:
        """静默映射转换新旧字段"""
        if not isinstance(payload, dict):
            return {}

        normalized = {}
        for key in payload:
            if key not in cls.SCHEMA_MAPPING:
                normalized[key] = payload[key]

        for key, value in payload.items():
            if key in cls.SCHEMA_MAPPING:
                normalized_key = cls.SCHEMA_MAPPING[key]
                # 优先保留已存在的同名标准字段（假设标准字段优先级更高）
                if normalized_key not in normalized:
                    normalized[normalized_key] = value

        return normalized

    @classmethod
    def calculate_sync(cls, raw_payload: dict) -> dict:
        """
        核心对齐计算，包含自愈和兜底
        """
        payload = cls.normalize_payload(raw_payload)

        # 1. 缺参兜底与脏数据自愈
        try:
            dialogue_text = str(payload.get("dialogue_text") or "")
        except Exception:
            dialogue_text = ""

        try:
            audio_duration_ms = float(payload.get("audio_duration_ms") or 0)
        except (ValueError, TypeError):
            audio_duration_ms = 0.0

        waveform_peaks = payload.get("waveform_peaks")
        if not isinstance(waveform_peaks, list):
            waveform_peaks = []

        # 清洗 peak 数据
        clean_peaks = []
        for p in waveform_peaks:
            try:
                clean_peaks.append(float(p))
            except (ValueError, TypeError):
                continue

        try:
            punctuation_pause_ms = float(payload.get("punctuation_pause_ms") or 500.0)
        except (ValueError, TypeError):
            punctuation_pause_ms = 500.0

        if punctuation_pause_ms < 0:
            punctuation_pause_ms = 500.0

        if audio_duration_ms < 0:
            audio_duration_ms = 0.0

        # 2. 计算时长
        # 字数基础时长估算 (假定 250ms/字)
        char_count_duration = len(dialogue_text) * 250.0

        # 标点符号停顿估算
        # 中英文常见标点
        punctuations = re.findall(r'[,.!?，。！？;；、]', dialogue_text)
        total_pause_ms = len(punctuations) * punctuation_pause_ms

        # 如果提供了音频长度且大于0，以音频为基础，否则用字数估算
        base_duration = audio_duration_ms if audio_duration_ms > 0 else char_count_duration

        # 结合波形峰值，如果峰值时间超出了 base_duration，那么时长至少要包含最后一个峰值
        max_peak = max(clean_peaks) if clean_peaks else 0.0

        final_duration_ms = base_duration + total_pause_ms

        if max_peak > final_duration_ms:
            final_duration_ms = max_peak

        # 极端的边界情况：没有任何有效输入时，给一个合理的最小分镜时长 (例如 1000ms)
        if final_duration_ms <= 0:
            final_duration_ms = 1000.0

        # 构建统一向下游输出的 Schema 版本
        return {
            "schema_version": "v2",
            "dialogue_text": dialogue_text,
            "audio_duration_ms": audio_duration_ms,
            "waveform_peaks": clean_peaks,
            "punctuation_pause_ms": punctuation_pause_ms,
            "calculated_storyboard_duration_ms": final_duration_ms,
            "is_fallback_used": audio_duration_ms == 0.0 or len(dialogue_text) == 0
        }
