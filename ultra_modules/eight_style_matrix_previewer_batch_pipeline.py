import concurrent.futures
import time
from typing import List, Dict, Any, Optional

class ProgressSnapshot:
    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.failed = 0
        self.results = []
        self.start_time = time.time()

    def add_result(self, result: Dict[str, Any]):
        self.results.append(result)
        if result.get("status") == "success":
            self.completed += 1
        else:
            self.failed += 1

    def get_progress(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "elapsed_time": time.time() - self.start_time,
            "results": self.results
        }

class EightStyleMatrixPreviewerBatchPipeline:
    DEFAULT_STYLES = [
        "修仙", "都市逆袭", "韩漫财阀", "热血少年",
        "中式规则怪谈", "废土朋克", "赛博纪元", "末日生存"
    ]

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers

    def _normalize_styles(self, styles: Optional[List[str]]) -> List[str]:
        if not styles or not isinstance(styles, list):
            return self.DEFAULT_STYLES

        # Ensure it's exactly 8 styles
        cleaned_styles = [str(s) for s in styles if s]
        if len(cleaned_styles) >= 8:
            return cleaned_styles[:8]

        # Pad if less than 8
        padded_styles = cleaned_styles + [s for s in self.DEFAULT_STYLES if s not in cleaned_styles]
        return padded_styles[:8]

    def _process_single_record(self, record: Any, styles: List[str]) -> Dict[str, Any]:
        # Handle dirty data self-healing
        if not record or not isinstance(record, (str, dict)):
            record = str(record) if record is not None else "empty_record"

        record_id = id(record)
        record_content = record.get("content", str(record)) if isinstance(record, dict) else str(record)

        if not record_content.strip():
            record_content = "default_content"

        # Simulate processing logic for each style
        generated_previews = {style: f"Preview for {style}: {record_content[:10]}" for style in styles}

        return {
            "id": record_id,
            "status": "success",
            "previews": generated_previews
        }

    def process_batch(self, records: List[Any], styles: Optional[List[str]] = None) -> ProgressSnapshot:
        # Default empty list fallback
        if not records or not isinstance(records, list):
            records = []

        normalized_styles = self._normalize_styles(styles)
        snapshot = ProgressSnapshot(total=len(records))

        if not records:
            return snapshot

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._process_single_record, record, normalized_styles): record for record in records}

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    snapshot.add_result(result)
                except Exception as e:
                    snapshot.add_result({
                        "status": "failed",
                        "error": str(e)
                    })

        return snapshot

def run_matrix_preview_pipeline(records: Optional[List[Any]] = None, styles: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Simplified one-click frontend function.
    Zero configuration, complete fault-tolerance.
    """
    if records is None:
        records = ["default_record"]

    pipeline = EightStyleMatrixPreviewerBatchPipeline(max_workers=50) # High throughput
    snapshot = pipeline.process_batch(records, styles)
    return snapshot.get_progress()
