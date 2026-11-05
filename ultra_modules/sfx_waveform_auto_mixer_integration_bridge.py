import uuid
import time
from typing import Any, Dict, List

class SFXWaveformAutoMixerIntegrationBridge:
    """
    Seamless bridge for SFX Waveform Auto Mixer.
    Handles dynamic schema mapping, backward/forward compatibility,
    dirty data self-healing, and missing parameter fallback.
    """

    DEFAULT_TYPE = "whoosh"
    DEFAULT_DURATION = 1.0
    DEFAULT_INTENSITY = 0.8
    VALID_TYPES = {"bass_drop", "sword_clash", "whoosh"}

    @classmethod
    def bridge_payload(cls, raw_payload: Any) -> Dict[str, Any]:
        """
        Receives external payload (possibly from old/new schemas, dirty data)
        and normalizes it into a strictly typed and standardized schema payload.
        """
        if not isinstance(raw_payload, dict):
            raw_payload = {}

        # Handle multiple possible keys for items for backward/forward compatibility
        items = raw_payload.get("items") or raw_payload.get("sfx_list") or raw_payload.get("tracks") or raw_payload.get("data")
        if not isinstance(items, list):
            items = []

        bridged_items = []
        for item in items:
            bridged_items.append(cls._bridge_single_item(item))

        return {
            "bridge_status": "success",
            "timestamp": time.time(),
            "bridged_items": bridged_items,
            "original_item_count": len(items)
        }

    @classmethod
    def _bridge_single_item(cls, item: Any) -> Dict[str, Any]:
        if not isinstance(item, dict):
            item = {}

        bridged = {}

        # ID mapping
        raw_id = item.get("id") or item.get("sfx_id") or item.get("uuid") or item.get("track_id")
        if not raw_id or not isinstance(raw_id, (str, int)):
            bridged["id"] = str(uuid.uuid4())
        else:
            bridged["id"] = str(raw_id)

        # Type mapping
        raw_type = item.get("type") or item.get("sfx_type") or item.get("sound_type") or item.get("effect_type")
        if not raw_type or not isinstance(raw_type, str) or raw_type not in cls.VALID_TYPES:
            # Map legacy types if any
            if isinstance(raw_type, str):
                lower_type = raw_type.lower()
                if "bass" in lower_type or "impact" in lower_type:
                    bridged["type"] = "bass_drop"
                elif "sword" in lower_type or "clash" in lower_type or "metal" in lower_type:
                    bridged["type"] = "sword_clash"
                elif "whoosh" in lower_type or "transition" in lower_type or "swipe" in lower_type:
                    bridged["type"] = "whoosh"
                else:
                    bridged["type"] = cls.DEFAULT_TYPE
            else:
                bridged["type"] = cls.DEFAULT_TYPE
        else:
            bridged["type"] = raw_type

        # Duration mapping
        raw_dur = item.get("duration") or item.get("duration_sec") or item.get("length") or item.get("time")
        try:
            dur = float(raw_dur)
            if dur <= 0:
                dur = cls.DEFAULT_DURATION
            bridged["duration"] = min(dur, 30.0) # Cap at 30.0 seconds
        except (ValueError, TypeError):
            bridged["duration"] = cls.DEFAULT_DURATION

        # Intensity mapping
        raw_int = item.get("intensity") or item.get("volume") or item.get("loudness") or item.get("gain")
        try:
            intensity = float(raw_int)
            if intensity <= 0:
                intensity = cls.DEFAULT_INTENSITY
            bridged["intensity"] = min(intensity, 1.0)
        except (ValueError, TypeError):
            bridged["intensity"] = cls.DEFAULT_INTENSITY

        return bridged
