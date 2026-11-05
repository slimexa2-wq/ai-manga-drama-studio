import uuid
import time
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTImageTurnaroundSheetIntegrationBridge:
    """
    ChatGPT Plus (GPT-Image-2) character turnaround sheet cross-system data integration bridge.
    Automatically detects old and new versions, silently mapping and forward-converting the schema
    without requiring manual field mapping configurations.
    Implements dirty data self-healing, zero-configuration fault tolerance, and default fallbacks.
    """

    def __init__(self):
        # We enforce a simple interface, zero-configuration
        pass

    def _generate_default_id(self):
        return str(uuid.uuid4())

    def _get_current_timestamp(self):
        return int(time.time() * 1000)

    def _normalize_string(self, value, default=""):
        if value is None:
            return default
        try:
            cleaned = str(value).strip()
            return cleaned if cleaned else default
        except Exception:
            return default

    def bridge_payload(self, raw_payload):
        """
        Receives raw payload (potentially from old version, new version, or dirty data).
        Silently converts it to the unified V2 schema.
        """
        # Handle empty/null payload
        if raw_payload is None:
            return self._build_v2_schema()

        if isinstance(raw_payload, str):
            try:
                parsed = json.loads(raw_payload)
                if isinstance(parsed, dict):
                    raw_payload = parsed
                else:
                    return self._build_v2_schema(description=self._normalize_string(raw_payload, "default character"))
            except Exception:
                # If it's a raw string that's not JSON, treat it as description
                return self._build_v2_schema(description=self._normalize_string(raw_payload, "default character"))

        if not isinstance(raw_payload, dict):
            return self._build_v2_schema()

        # Identify schema version based on keys.
        # V1 old schema might have: "character_id", "char_desc", "art_style", "created_at" (seconds)
        # V2 new schema expects: "id", "description", "style", "metadata" -> "timestamp" (ms)

        # 1. Resolve ID
        r_id = raw_payload.get("id") or raw_payload.get("character_id") or raw_payload.get("uuid")
        r_id = self._normalize_string(r_id, self._generate_default_id())

        # 2. Resolve Description
        r_desc = raw_payload.get("description") or raw_payload.get("char_desc") or raw_payload.get("prompt")
        r_desc = self._normalize_string(r_desc, "default character")

        # 3. Resolve Style
        r_style = raw_payload.get("style") or raw_payload.get("art_style") or raw_payload.get("preset")
        r_style = self._normalize_string(r_style, "anime")

        # 4. Resolve Timestamp (v1 might use created_at in seconds)
        timestamp = self._get_current_timestamp()

        # Try finding a timestamp
        ts_raw = raw_payload.get("metadata", {}).get("timestamp") or raw_payload.get("created_at") or raw_payload.get("time")

        if ts_raw is not None:
            try:
                ts_float = float(ts_raw)
                # If it's in seconds (e.g. before year 3000 -> < 32503680000)
                if ts_float < 32503680000:
                    timestamp = int(ts_float * 1000)
                else:
                    timestamp = int(ts_float)
            except Exception:
                pass # Silently fallback to current timestamp

        return self._build_v2_schema(r_id, r_desc, r_style, timestamp)

    def _build_v2_schema(self, r_id=None, description="default character", style="anime", timestamp=None):
        if r_id is None:
            r_id = self._generate_default_id()
        if timestamp is None:
            timestamp = self._get_current_timestamp()

        return {
            "id": r_id,
            "description": description,
            "style": style,
            "metadata": {
                "version": "v2",
                "timestamp": timestamp,
                "schema_bridge_applied": True
            }
        }

def integrate_bridge(payload):
    """
    Frontend one-click entry point.
    Extremely simple invocation: just pass the payload.
    """
    bridge = GPTImageTurnaroundSheetIntegrationBridge()
    return bridge.bridge_payload(payload)
