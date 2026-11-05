import concurrent.futures
import threading
import uuid
import time
from typing import List, Dict, Any, Optional

class PromptCompiler:
    """
    Compiler for Google Veo 3 and Sora 2 cinematic camera motion prompts.
    Provides dirty data self-healing and missing parameter fallback.
    """

    DEFAULT_SUBJECT = "cinematic scene, ultra high quality, 8k resolution"
    DEFAULT_LENS = "35mm prime lens"
    DEFAULT_CAMERA_MOTION = "static shot, steady camera"
    DEFAULT_LIGHTING = "natural dramatic lighting"
    DEFAULT_SPEED = "normal speed (1.0x)"

    @classmethod
    def compile_prompt(cls, record: Dict[str, Any]) -> str:
        """
        Compiles a structured prompt from raw record data.
        Handles missing keys, incorrect types, and None values automatically.
        """
        if not isinstance(record, dict):
            record = {}

        # Self-healing and fallback
        subject = cls._clean_string(record.get('subject'), cls.DEFAULT_SUBJECT)
        lens = cls._clean_string(record.get('lens'), cls.DEFAULT_LENS)
        motion = cls._clean_string(record.get('camera_motion'), cls.DEFAULT_CAMERA_MOTION)
        lighting = cls._clean_string(record.get('lighting'), cls.DEFAULT_LIGHTING)
        speed = cls._clean_string(record.get('speed'), cls.DEFAULT_SPEED)

        # Structure compilation for Veo 3 / Sora 2
        prompt = (
            f"Subject: {subject}. "
            f"Lens & Framing: {lens}. "
            f"Camera Motion: {motion}. "
            f"Lighting: {lighting}. "
            f"Playback Speed: {speed}."
        )
        return prompt

    @staticmethod
    def _clean_string(value: Any, default: str) -> str:
        if value is None or not isinstance(value, str) or not value.strip():
            return default
        return value.strip()


class Veo3CameraMotionPrompterBatchPipeline:
    """
    Batch processing pipeline for camera motion prompting.
    Supports high-throughput processing, non-blocking execution, and snapshot progress.
    """

    def __init__(self, max_workers: int = 10):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.jobs_lock = threading.Lock()

    def submit_batch(self, records: List[Dict[str, Any]]) -> str:
        """
        Submits a batch of records for processing.
        Returns a job_id immediately (non-blocking).
        """
        job_id = str(uuid.uuid4())

        # Self-healing: if records is not a list or empty, handle gracefully
        if not isinstance(records, list):
            records = []

        with self.jobs_lock:
            self.jobs[job_id] = {
                "total": len(records),
                "completed": 0,
                "status": "processing" if records else "completed",
                "results": [None] * len(records),
                "errors": []
            }

        if records:
            # Submit in background
            threading.Thread(target=self._process_batch_background, args=(job_id, records), daemon=True).start()

        return job_id

    def _process_batch_background(self, job_id: str, records: List[Dict[str, Any]]):
        """Internal method to process the batch in parallel."""

        def process_single(index: int, record: Dict[str, Any]):
            try:
                # Simulate compilation time / external API call
                time.sleep(0.01)
                compiled = PromptCompiler.compile_prompt(record)

                with self.jobs_lock:
                    self.jobs[job_id]["results"][index] = compiled
                    self.jobs[job_id]["completed"] += 1
            except Exception as e:
                with self.jobs_lock:
                    self.jobs[job_id]["errors"].append({"index": index, "error": str(e)})
                    self.jobs[job_id]["completed"] += 1

        futures = []
        for i, record in enumerate(records):
            futures.append(self.executor.submit(process_single, i, record))

        concurrent.futures.wait(futures)

        with self.jobs_lock:
            self.jobs[job_id]["status"] = "completed"

    def get_progress_snapshot(self, job_id: str) -> Dict[str, Any]:
        """
        Returns a non-blocking snapshot of the job progress.
        """
        with self.jobs_lock:
            if job_id not in self.jobs:
                return {"status": "not_found", "total": 0, "completed": 0}

            job = self.jobs[job_id]
            return {
                "status": job["status"],
                "total": job["total"],
                "completed": job["completed"],
                "progress_percentage": (job["completed"] / job["total"] * 100) if job["total"] > 0 else 100,
                "results": list(job["results"]) if job["status"] == "completed" else None
            }

    def shutdown(self):
        """Cleanup resources."""
        self.executor.shutdown(wait=False)
