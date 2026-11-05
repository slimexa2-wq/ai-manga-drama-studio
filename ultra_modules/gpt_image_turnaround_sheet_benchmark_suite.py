import time
import uuid
import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional

class GPTImageTurnaroundGenerator:
    """
    Generator for ChatGPT Plus (GPT-Image-2) character turnaround sheets and expression sets.
    Features extreme zero-configuration fault tolerance and default fallbacks.
    """
    def __init__(self):
        self.default_prompt = "A character design sheet, anime style, showing front, side, and back views of a young protagonist."
        self.default_aspect_ratio = "16:9"

    def _clean_string(self, val: Any, default: str) -> str:
        if val is None:
            return default
        if not isinstance(val, str):
            try:
                val = str(val)
            except Exception:
                return default
        val = val.strip()
        if not val:
            return default
        # Attempt to sanitize dirty characters (e.g. non-printable)
        val = ''.join(c for c in val if c.isprintable() or c in '\n\r\t')
        if not val.strip():
            return default
        return val

    def generate_instruction(
        self,
        character_desc: Optional[str] = None,
        style: Optional[str] = None,
        views: Optional[List[str]] = None,
        expressions: Optional[List[str]] = None,
        date_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates the final instruction prompt for GPT-Image-2.
        Self-heals dirty data and fills in defaults.
        """
        # 1. Clean and fallback character desc
        safe_desc = self._clean_string(character_desc, "a young adventurer with standard fantasy attire")

        # 2. Clean and fallback style
        safe_style = self._clean_string(style, "Japanese anime style, clean line art, flat colors")

        # 3. Clean and fallback views
        if not views or not isinstance(views, list):
            safe_views = ["front", "side", "back"]
        else:
            safe_views = [self._clean_string(v, "front") for v in views]
            # Ensure unique and not completely empty list after cleaning
            safe_views = list(set(v for v in safe_views if v))
            if not safe_views:
                safe_views = ["front", "side", "back"]

        # 4. Clean and fallback expressions
        if not expressions or not isinstance(expressions, list):
            safe_expressions = ["neutral", "happy", "angry", "sad"]
        else:
            safe_expressions = [self._clean_string(e, "neutral") for e in expressions]
            safe_expressions = list(set(e for e in safe_expressions if e))
            if not safe_expressions:
                safe_expressions = ["neutral", "happy", "angry", "sad"]

        # 5. Date context self-healing & boundary logic
        if not date_context or not isinstance(date_context, str):
            # Default to current date if missing or invalid
            safe_date = datetime.datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                # Try parsing as ISO format to validate
                dt = datetime.datetime.fromisoformat(date_context)
                safe_date = dt.strftime("%Y-%m-%d")
            except Exception:
                safe_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # Compile final prompt
        prompt = (
            f"Generate a character turnaround sheet for {safe_desc}. "
            f"Style: {safe_style}. "
            f"Views to include: {', '.join(safe_views)}. "
            f"Expressions to include: {', '.join(safe_expressions)}. "
            f"Context Date: {safe_date}. "
            f"Layout: Arrange views logically with consistent proportions."
        )

        return {
            "request_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "model": "gpt-image-2",
            "prompt": prompt,
            "parameters": {
                "character_desc": safe_desc,
                "style": safe_style,
                "views": safe_views,
                "expressions": safe_expressions,
                "date_context": safe_date
            }
        }


class TurnaroundBenchmarkSuite:
    """
    Benchmark suite to test the GPTImageTurnaroundGenerator with synthetic fixtures
    and extreme boundaries.
    """
    def __init__(self, concurrency: int = 100):
        self.generator = GPTImageTurnaroundGenerator()
        self.concurrency = concurrency

    def run_benchmark(self, payload: Dict[str, Any], count: int) -> Dict[str, Any]:
        """
        Runs the benchmark with high concurrency and returns stats.
        """
        start_time = time.time()
        successes = 0
        failures = 0

        def task(_):
            try:
                res = self.generator.generate_instruction(**payload)
                if res and "prompt" in res:
                    return True
                return False
            except Exception:
                return False

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            results = list(executor.map(task, range(count)))

        successes = sum(1 for r in results if r)
        failures = count - successes
        end_time = time.time()

        total_time_ms = (end_time - start_time) * 1000
        avg_latency_ms = total_time_ms / count if count > 0 else 0

        return {
            "total_requests": count,
            "successes": successes,
            "failures": failures,
            "success_rate": (successes / count) * 100 if count > 0 else 0,
            "total_time_ms": total_time_ms,
            "avg_latency_ms": avg_latency_ms
        }
