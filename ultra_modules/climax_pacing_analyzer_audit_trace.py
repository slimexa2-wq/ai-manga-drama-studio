import hashlib
import copy
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class PacingAuditTracer:
    def __init__(self):
        self.logs = []

    def record(self, step: str, before: Any, after: Any, reason: str):
        self.logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "diff": {
                "before": copy.deepcopy(before),
                "after": copy.deepcopy(after)
            },
            "reason": reason
        })

def _parse_timestamp(ts_val) -> datetime:
    if not ts_val:
        return datetime.now(timezone.utc)
    if isinstance(ts_val, datetime):
        if ts_val.tzinfo is None:
            return ts_val.replace(tzinfo=timezone.utc)
        return ts_val
    if isinstance(ts_val, str):
        try:
            dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass
    return datetime.now(timezone.utc)

def _determine_pacing(text: str, index: int) -> str:
    text_lower = str(text).lower()
    if any(k in text_lower for k in ["压抑", "受辱", "被贬", "退婚", "嘲讽", "oppression"]):
        return "oppression"
    if any(k in text_lower for k in ["蓄力", "隐忍", "修炼", "得到系统", "觉醒", "gathering"]):
        return "gathering"
    if any(k in text_lower for k in ["爆发", "打脸", "震惊", "反杀", "跪下", "climax"]):
        return "climax"
    if any(k in text_lower for k in ["悬念", "危机", "神秘人", "未完", "suspense"]):
        return "suspense"

    # Fallback based on sequence progression
    pacing_sequence = ["oppression", "gathering", "climax", "suspense"]
    return pacing_sequence[index % 4]

def analyze_and_trace(segments: Optional[Any] = None) -> Dict[str, Any]:
    tracer = PacingAuditTracer()

    # 1. Missing parameter handling
    original_segments = segments
    if segments is None:
        segments = []
        tracer.record("init", original_segments, segments, "Missing parameter fallback to empty list")
    elif not isinstance(segments, list):
        segments = [segments]
        tracer.record("init", original_segments, segments, "Converted non-list input to list")

    # 2. Self-healing and deduplication
    healed_segments = []
    seen = set()
    for item in segments:
        original_item = item
        healed_item = {}
        if isinstance(item, str):
            healed_item = {"text": item}
            tracer.record("heal_type", original_item, healed_item, "Wrapped string into dict")
        elif isinstance(item, dict):
            healed_item = copy.deepcopy(item)
        else:
            # Handle other types like int by casting to str
            healed_item = {"text": str(item)}
            tracer.record("heal_type", original_item, healed_item, "Wrapped non-string/dict into dict text")

        if "text" not in healed_item or not healed_item.get("text"):
            healed_item["text"] = "默认剧情"
            tracer.record("heal_missing_text", original_item, healed_item, "Filled missing text with default")

        if "timestamp" not in healed_item:
            healed_item["timestamp"] = datetime.now(timezone.utc)
            tracer.record("heal_timestamp", original_item, healed_item, "Assigned current UTC timestamp")
        else:
            healed_item["timestamp"] = _parse_timestamp(healed_item["timestamp"])

        # Deduplication based on text
        text_key = str(healed_item["text"]).strip()
        if text_key in seen:
            tracer.record("deduplicate", original_item, None, "Removed duplicate segment based on text")
            continue
        seen.add(text_key)
        healed_segments.append(healed_item)

    # 3. Sort chronologically
    sorted_segments = sorted(healed_segments, key=lambda x: x["timestamp"])

    # We log sort only if order actually changed
    # compare text sequences
    healed_text_seq = [s["text"] for s in healed_segments]
    sorted_text_seq = [s["text"] for s in sorted_segments]
    if healed_text_seq != sorted_text_seq:
        tracer.record("sort", healed_text_seq, sorted_text_seq, "Sorted segments chronologically")

    # 4. Analyze pacing
    analyzed_results = []
    pacing_sequence = []
    for idx, seg in enumerate(sorted_segments):
        pacing = _determine_pacing(seg["text"], idx)
        analyzed_results.append({
            "text": seg["text"],
            "pacing": pacing,
            "timestamp": seg["timestamp"].isoformat()
        })
        pacing_sequence.append(pacing)

    # 5. Encrypted pacing signature
    signature_input = "-".join(pacing_sequence)
    pacing_signature = hashlib.sha256(signature_input.encode('utf-8')).hexdigest()

    # 6. Format clean UI output
    summary = f"Analyzed {len(analyzed_results)} segments."
    if analyzed_results:
        summary += f" Curve: {' -> '.join(pacing_sequence)}"

    return {
        "summary": summary,
        "pacing_signature": pacing_signature,
        "segments": analyzed_results,
        "_audit_logs": tracer.logs
    }
