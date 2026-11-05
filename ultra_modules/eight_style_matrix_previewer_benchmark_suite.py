import time
import random
import concurrent.futures
from datetime import datetime, timezone
import threading

class EightStyleMatrixPreviewerBenchmarkSuite:
    STYLES = [
        "cultivation",          # 修仙
        "urban_counterattack",  # 都市逆袭
        "chaebol",              # 韩漫财阀
        "shonen",               # 热血少年
        "rule_horror",          # 中式规则怪谈
        "cyberpunk",            # 赛博朋克
        "wasteland_survival",   # 废土生存
        "palace_intrigue"       # 宫廷内推
    ]

    DEFAULT_TEXT = "Default Story"
    DEFAULT_RESOLUTION = "1920x1080"

    def __init__(self, concurrency_limit=100):
        self.concurrency_limit = concurrency_limit

    def _clean_text(self, text):
        if not text or not isinstance(text, str):
            return self.DEFAULT_TEXT
        cleaned = "".join(c for c in text if c.isprintable()).strip()
        return cleaned if cleaned else self.DEFAULT_TEXT

    def _clean_timestamp(self, timestamp_str):
        now_iso = datetime.now(timezone.utc).isoformat()
        if not timestamp_str or not isinstance(timestamp_str, str):
            return now_iso
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.isoformat()
        except ValueError:
            return now_iso

    def _clean_resolution(self, res):
        if not res or not isinstance(res, str):
            return self.DEFAULT_RESOLUTION
        if 'x' not in res:
            return self.DEFAULT_RESOLUTION
        parts = res.split('x')
        if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
            w, h = int(parts[0].strip()), int(parts[1].strip())
            if 0 < w <= 8192 and 0 < h <= 8192:
                return f"{w}x{h}"
        return self.DEFAULT_RESOLUTION

    def generate_matrix_preview(self, payload):
        """
        Generates an 8-style matrix preview for a given payload.
        Zero-configuration fault tolerance, silently clean dirty data.
        """
        if not isinstance(payload, dict):
            payload = {}

        start_time = time.time()

        text = self._clean_text(payload.get("text"))
        timestamp = self._clean_timestamp(payload.get("timestamp"))
        resolution = self._clean_resolution(payload.get("resolution"))

        # Simulate processing work
        time.sleep(0.001)  # Simulate 1 millisecond processing

        matrix_results = {}
        for style in self.STYLES:
            matrix_results[style] = {
                "text_snippet": text[:50] + "..." if len(text) > 50 else text,
                "preview_url": f"https://mock-storage.local/{style}_{int(time.time()*1000)}.png"
            }

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        return {
            "status": "success",
            "original_text": text,
            "timestamp": timestamp,
            "resolution": resolution,
            "matrix": matrix_results,
            "processing_time_ms": round(duration_ms, 2)
        }

    def run_batch_matrix_previews(self, payloads):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency_limit) as executor:
            futures = {executor.submit(self.generate_matrix_preview, p): p for p in payloads}
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    results.append({
                        "status": "error_recovered",
                        "original_text": self.DEFAULT_TEXT,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "resolution": self.DEFAULT_RESOLUTION,
                        "matrix": {s: {"preview_url": "", "text_snippet": self.DEFAULT_TEXT} for s in self.STYLES},
                        "processing_time_ms": 0.0
                    })
        return results

    @classmethod
    def generate_synthetic_fixtures(cls, count=1000):
        fixtures = []

        # 1. Normal data
        for _ in range(count // 4):
            fixtures.append({
                "text": f"Normal story {random.randint(1, 1000)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "resolution": "1920x1080"
            })

        # 2. Dirty/Empty data
        for _ in range(count // 4):
            fixtures.append({
                "text": None if random.random() > 0.5 else "   \n\t ",
                "timestamp": "invalid_date_format",
                "resolution": "99999x99999" if random.random() > 0.5 else "invalid"
            })

        # 3. Extreme Boundary data (Cross-year/month, non-printable chars)
        cross_year_dates = [
            "2023-12-31T23:59:59.999",
            "2024-01-01T00:00:00.001",
            "2024-02-29T23:59:59",  # Leap year
            "2024-03-01T00:00:00"
        ]
        for _ in range(count // 4):
            fixtures.append({
                "text": "Extreme boundary test \x00\x01\x02 \ud83d\ude00" * 100,
                "timestamp": random.choice(cross_year_dates),
                "resolution": " 1080 x 1920 "
            })

        # 4. Completely malformed payload (None, List, Integer)
        remaining = count - len(fixtures)
        for _ in range(remaining):
            malformed = random.choice([None, ["Not", "a", "dict"], 12345])
            fixtures.append(malformed)

        return fixtures

    def benchmark_performance(self, count=1000):
        data = self.generate_synthetic_fixtures(count=count)
        start_time = time.time()

        results = self.run_batch_matrix_previews(data)

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r["status"] in ("success", "error_recovered"))
        avg_processing_time = sum(r["processing_time_ms"] for r in results) / len(results) if results else 0

        return {
            "total_requests": len(data),
            "successful_requests": success_count,
            "total_time_seconds": round(total_time, 4),
            "avg_processing_time_ms": round(avg_processing_time, 4),
            "throughput_req_per_sec": round(len(data) / total_time, 2) if total_time > 0 else 0
        }
