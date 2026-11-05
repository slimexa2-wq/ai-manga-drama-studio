import concurrent.futures
import time
import uuid
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RoleTTSConfig:
    role_id: str
    base_pitch: float
    base_speed: float
    emotion: str

ROLE_PROFILES = {
    "narrator": RoleTTSConfig(role_id="narrator", base_pitch=1.0, base_speed=1.0, emotion="neutral"),
    "male_lead": RoleTTSConfig(role_id="male_lead", base_pitch=0.9, base_speed=1.0, emotion="confident"),
    "female_lead": RoleTTSConfig(role_id="female_lead", base_pitch=1.1, base_speed=1.0, emotion="gentle"),
    "villain": RoleTTSConfig(role_id="villain", base_pitch=0.8, base_speed=0.9, emotion="sinister"),
}

class DynamicTTSModulator:
    """Handles parameter adjustments based on role and text heuristics, with dirty data self-healing."""

    @staticmethod
    def modulate(role: str, text: str, user_pitch: Optional[float] = None, user_speed: Optional[float] = None) -> Dict[str, Any]:
        # Self-healing: Default to narrator if role is missing or invalid
        if not role or role.lower() not in ROLE_PROFILES:
            role = "narrator"

        role = role.lower()
        profile = ROLE_PROFILES[role]

        # Self-healing: bounds checking and default values
        pitch = user_pitch if user_pitch is not None else profile.base_pitch
        speed = user_speed if user_speed is not None else profile.base_speed

        # Enforce bounds
        pitch = max(0.5, min(2.0, float(pitch)))
        speed = max(0.5, min(2.0, float(speed)))

        # Text heuristics (ex: exclamation marks increase speed/pitch slightly)
        if "!" in text or "！" in text:
            pitch = min(2.0, pitch * 1.05)
            speed = min(2.0, speed * 1.05)
            emotion = "excited"
        elif "?" in text or "？" in text:
            pitch = min(2.0, pitch * 1.1)
            emotion = "curious"
        else:
            emotion = profile.emotion

        return {
            "role_id": profile.role_id,
            "pitch": round(pitch, 3),
            "speed": round(speed, 3),
            "emotion": emotion
        }

class DurationAlignmentEngine:
    """Computes millisecond-level duration alignment."""

    @staticmethod
    def compute_duration(text: str, speed: float) -> int:
        """Mocks synthesis length based on character count and speed (returns ms)."""
        if not text:
            return 0

        base_ms_per_char = 250 # Assume 250ms per character on average
        duration = (len(text) * base_ms_per_char) / speed

        return int(duration)

class BatchTTSPipeline:
    """High-throughput concurrency for TTS tasks."""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single record."""
        # Extract fields with safe defaults
        text = str(record.get("text", "") or "").strip()
        role = str(record.get("role", "narrator") or "")
        pitch = record.get("pitch")
        speed = record.get("speed")
        record_id = record.get("id", str(uuid.uuid4()))

        # Modulate
        mod_params = DynamicTTSModulator.modulate(role, text, pitch, speed)

        # Compute duration
        duration_ms = DurationAlignmentEngine.compute_duration(text, mod_params["speed"])

        # Simulate some processing time based on length, for realism in tests but very short to keep tests fast
        time.sleep(0.001)

        return {
            "id": record_id,
            "original_text": text,
            "tts_params": mod_params,
            "duration_ms": duration_ms,
            "status": "success" if text else "empty_text"
        }

    def run_batch(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of records concurrently."""
        batch_id = str(uuid.uuid4())
        results = []

        future_to_record = {self.executor.submit(self.process_record, r): r for r in records}

        for future in concurrent.futures.as_completed(future_to_record):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing record: {e}")
                record = future_to_record[future]
                results.append({
                    "id": record.get("id", "unknown"),
                    "status": "error",
                    "error_msg": str(e)
                })

        # Sort results to roughly match input order if possible, though ID might be random.
        # If input records had sequential IDs we could sort by that, but here we just return them.

        return {
            "batch_id": batch_id,
            "total": len(records),
            "processed": len(results),
            "results": results
        }

def run_batch_tts_pipeline(records: List[Dict[str, Any]], max_workers: int = 10) -> Dict[str, Any]:
    """
    1-click simple entry point for batch TTS processing.
    Fully resilient to missing or dirty data.
    """
    pipeline = BatchTTSPipeline(max_workers=max_workers)
    return pipeline.run_batch(records)
