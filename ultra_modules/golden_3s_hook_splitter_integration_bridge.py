import json
import re
from typing import Dict, Any, List, Optional

class Golden3sHookSplitterIntegrationBridge:
    """
    十万字网文小说按黄金前3秒强冲突钩子+集末悬念卡点一键多集拆解器
    (跨系统数据契约无缝桥接与Schema版本自动向前兼容转换器)

    Zero configuration, handles dirty data, auto fallbacks.
    """

    DEFAULT_TARGET_DURATION = 75

    @classmethod
    def process_payload(cls, payload: Any) -> Dict[str, Any]:
        """
        Main entry point for processing novel payload.
        Auto detects schemas, heals dirty data, and splits text into episodes.
        """
        # Self healing dirty data
        normalized_data = cls._normalize_payload(payload)

        # Schema version auto mapping
        text_content, target_duration = cls._extract_fields(normalized_data)

        if not text_content:
            return {
                "success": False,
                "error": "No valid text content found in payload.",
                "episodes": []
            }

        try:
            # Extreme boundary conditions: strip extreme spaces/newlines, handle very short strings
            text_content = str(text_content).strip()
            if not text_content:
                return {
                    "success": False,
                    "error": "Empty text content after stripping.",
                    "episodes": []
                }

            # Call the core engine to split (independently evolved logic)
            episodes = cls._split_long_novel_into_episodes(text_content, target_duration)

            return {
                "success": True,
                "episodes": episodes,
                "total_episodes": len(episodes),
                "original_duration_target": target_duration
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Internal splitting error: {str(e)}",
                "episodes": []
            }

    @staticmethod
    def _split_long_novel_into_episodes(long_text: str, target_duration_sec: int = 75) -> List[Dict[str, Any]]:
        cleaned = re.sub(r"\r\n", "\n", long_text.strip())
        paragraphs = [p.strip() for p in re.split(r"\n+", cleaned) if p.strip()]

        episodes = []
        current_episode_paragraphs = []
        current_duration_sec = 0.0

        for p in paragraphs:
            est_sec = len(p) / 4.2 + 0.8
            if current_duration_sec + est_sec > target_duration_sec * 1.2 and len(current_episode_paragraphs) > 0:
                episodes.append(Golden3sHookSplitterIntegrationBridge._create_episode_dict(current_episode_paragraphs))
                current_episode_paragraphs = []
                current_duration_sec = 0.0

            current_episode_paragraphs.append(p)
            current_duration_sec += est_sec

        if current_episode_paragraphs:
            episodes.append(Golden3sHookSplitterIntegrationBridge._create_episode_dict(current_episode_paragraphs))

        return episodes

    @staticmethod
    def _create_episode_dict(paragraphs: List[str]) -> Dict[str, Any]:
        text = "\n".join(paragraphs)
        golden_3s_hook = ""
        if len(paragraphs) > 0:
            golden_3s_hook = paragraphs[0][:60] + "..." if len(paragraphs[0]) > 60 else paragraphs[0]

        cliffhanger = ""
        if len(paragraphs) > 0:
            cliffhanger = paragraphs[-1][-60:]
            if len(paragraphs[-1]) > 60:
                cliffhanger = "..." + cliffhanger

        satisfying_beats = []
        for p in paragraphs:
            if any(k in p for k in ("怒", "杀", "死", "滚", "奉还", "轰", "碎", "剑", "斩", "反转", "觉醒", "冷笑")):
                satisfying_beats.append(p)
                if len(satisfying_beats) >= 3:
                    break

        return {
            "text": text,
            "golden_3s_hook": golden_3s_hook,
            "cliffhanger": cliffhanger,
            "satisfying_beats": satisfying_beats
        }

    @staticmethod
    def _normalize_payload(payload: Any) -> Dict[str, Any]:
        """
        Heal dirty data: string JSONs, Nones, primitives.
        """
        if payload is None:
            return {}

        if isinstance(payload, str):
            try:
                # Try parsing as JSON string
                parsed = json.loads(payload)
                if isinstance(parsed, dict):
                    return parsed
                else:
                    return {"text": payload}
            except json.JSONDecodeError:
                return {"text": payload}

        if isinstance(payload, (int, float, bool)):
            return {"text": str(payload)}

        if not isinstance(payload, dict):
            try:
                return dict(payload)
            except Exception:
                return {"text": str(payload)}

        return payload

    @staticmethod
    def _extract_fields(data: Dict[str, Any]) -> tuple[str, int]:
        """
        Automatically map old/new schema fields without manual configuration.
        """
        text = ""
        text_fields = ["text", "novel_text", "content", "story", "raw_text", "manuscript", "body"]
        for field in text_fields:
            if field in data and data[field]:
                text = str(data[field])
                break

        duration_fields = ["target_duration_sec", "target_duration", "duration", "episode_length", "length_sec"]
        target_duration = Golden3sHookSplitterIntegrationBridge.DEFAULT_TARGET_DURATION
        for field in duration_fields:
            if field in data and data[field] is not None:
                try:
                    val = int(data[field])
                    if val > 0:
                        target_duration = val
                        break
                except (ValueError, TypeError):
                    pass

        return text, target_duration
