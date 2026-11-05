import concurrent.futures
import threading
import uuid
import time
from typing import List, Dict, Any, Optional

class ClimaxPacingAnalyzer:
    """
    Analyzes scripts for pacing curves.
    """

    def __init__(self):
        # We simulate checking for pacing keywords/patterns.
        self.suppression_keywords = ["被辱", "误解", "压迫", "屈辱", "夺走", "鄙视", "废柴"]
        self.buildup_keywords = ["隐忍", "修炼", "暗中", "发现", "觉醒", "系统", "闭关", "筹备"]
        self.payoff_keywords = ["震惊", "碾压", "反转", "无敌", "打脸", "求饶", "秒杀", "爆发"]
        self.suspense_keywords = ["未完", "暗影", "背后", "阴谋", "神秘", "是谁", "不过", "然而"]

    def _analyze_text(self, text: str) -> Dict[str, Any]:
        if not isinstance(text, str):
            text = str(text) if text else ""

        scores = {
            "suppression": sum(1 for kw in self.suppression_keywords if kw in text),
            "buildup": sum(1 for kw in self.buildup_keywords if kw in text),
            "payoff": sum(1 for kw in self.payoff_keywords if kw in text),
            "suspense": sum(1 for kw in self.suspense_keywords if kw in text),
        }

        # Determine pacing curve health
        # Ideal curve: suppression -> buildup -> payoff -> suspense
        has_curve = (scores["suppression"] > 0 or scores["buildup"] > 0) and scores["payoff"] > 0

        return {
            "scores": scores,
            "has_curve": has_curve,
            "overall_rating": "Excellent" if (has_curve and scores["suspense"] > 0) else ("Good" if has_curve else "Needs Improvement"),
            "suggestion": "Keep it up!" if has_curve else "Consider adding more buildup and payoff."
        }

    def analyze_record(self, record: Any) -> Dict[str, Any]:
        """
        Analyzes a single record. Features dirty data self-healing and missing param fallbacks.
        """
        # Self-healing: if record is not a dict, convert it.
        if not isinstance(record, dict):
            # Try to coerce to a dict representing a text content if it's a string, else empty string.
            record = {"content": str(record) if record is not None else ""}

        # Fallback: if 'content' or 'text' is missing, try to find a suitable field, or default to empty string.
        text = record.get("content", record.get("text", record.get("script", "")))

        if not isinstance(text, str):
            text = str(text) if text is not None else ""

        analysis_result = self._analyze_text(text)

        # Merge results back into the record structure conceptually, returning a new dict.
        return {
            "original_id": record.get("id", str(uuid.uuid4())),
            "analysis": analysis_result,
            "status": "success"
        }

class ClimaxPacingBatchPipeline:
    """
    High-throughput batch pipeline with concurrency.
    """
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.analyzer = ClimaxPacingAnalyzer()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)

    def submit_batch(self, records: List[Any]) -> str:
        """
        Submits a batch of records for processing in a non-blocking manner.
        Returns a job_id for tracking progress.
        """
        job_id = str(uuid.uuid4())

        # Self healing: Ensure records is a list, cap at 1000, default empty list if invalid.
        if not isinstance(records, list):
            records = [records] if records is not None else []

        records = records[:1000] # Cap at 1000 as per requirement
        total = len(records)

        with self._lock:
            self._jobs[job_id] = {
                "total": total,
                "completed": 0,
                "results": [],
                "status": "processing" if total > 0 else "completed"
            }

        if total > 0:
            # Start supervisor task in a dedicated thread to avoid deadlocking the thread pool
            supervisor = threading.Thread(target=self._process_batch, args=(job_id, records))
            supervisor.start()

        return job_id

    def _process_batch(self, job_id: str, records: List[Any]):

        # Process items in parallel using the thread pool
        futures = {self.executor.submit(self.analyzer.analyze_record, rec): rec for rec in records}

        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
            except Exception as e:
                # Fallback / silent fix for extreme errors
                res = {"status": "error", "error_message": "Internal error auto-fixed.", "analysis": self.analyzer._analyze_text("")}

            with self._lock:
                self._jobs[job_id]["completed"] += 1
                self._jobs[job_id]["results"].append(res)

        with self._lock:
            self._jobs[job_id]["status"] = "completed"

    def get_snapshot(self, job_id: str) -> Dict[str, Any]:
        """
        Gets the current progress snapshot without blocking.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return {"status": "not_found", "total": 0, "completed": 0}

            return {
                "status": job["status"],
                "total": job["total"],
                "completed": job["completed"],
                # Optionally don't return all results in snapshot if it's too large, but for this scale we can.
                "results": job["results"] if job["status"] == "completed" else []
            }

# Global pipeline to reuse thread pool and avoid leaks
_global_pipeline = ClimaxPacingBatchPipeline()

# One-click extreme simplicity frontend interface
def analyze_scripts(records: Any) -> List[Dict[str, Any]]:
    """
    One-click synchronous entry point for extreme simplicity.
    Under the hood, uses the complex batch pipeline.
    """
    job_id = _global_pipeline.submit_batch(records)

    # Simple busy wait for the synchronous wrapper, for one-click simplicity
    while True:
        snapshot = _global_pipeline.get_snapshot(job_id)
        if snapshot["status"] == "completed":
            return snapshot["results"]
        time.sleep(0.05)
