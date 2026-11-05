import concurrent.futures
import re
from typing import List, Dict, Any, Generator

class DialogueLipSyncTimerBatchPipeline:
    """
    台词字数、标点停顿与配音音频波形峰值自动对齐分镜时长计算器
    (Dialogue Lip-Sync Timer Batch Pipeline)

    支持批量流式处理、高吞吐并发加速、进度快照与零阻塞自愈兜底。
    """
    def __init__(self, max_workers: int = 20, default_words_per_second: float = 4.0):
        self.max_workers = max_workers
        self.default_words_per_second = default_words_per_second

    def _calculate_duration(self, text: str) -> float:
        """根据文本长度和标点符号停顿计算预期时长"""
        if not isinstance(text, str):
            text = str(text) if text is not None else ""

        text = text.strip()
        if not text:
            return 1.0 # 默认最短时长 1 秒

        word_count = len(text)
        major_pauses = len(re.findall(r'[。！？\n.!?]', text))
        minor_pauses = len(re.findall(r'[，；,;]', text))

        base_time = word_count / self.default_words_per_second
        pause_time = (major_pauses * 0.5) + (minor_pauses * 0.25)

        total_time = base_time + pause_time
        return max(1.0, round(total_time, 2))

    def _process_single_record(self, index: int, record: Any) -> Dict[str, Any]:
        """处理单条记录，包含脏数据自愈和默认兜底（零阻塞）"""
        if not isinstance(record, dict):
            record = {"original_data": record, "text": str(record) if record is not None else ""}

        text = record.get("text", "")
        if not isinstance(text, str):
            text = str(text) if text is not None else ""

        duration = record.get("duration", None)

        try:
            if duration is None or not isinstance(duration, (int, float)) or duration <= 0:
                duration = self._calculate_duration(text)
            else:
                duration = float(duration)
        except Exception:
            duration = 1.0

        has_audio = bool(record.get("audio_url") or record.get("audio_path") or record.get("waveform_peaks"))

        # 模拟音频波形峰值对齐：如果提供了波形峰值数据，根据波形估算时长并取最大值
        if has_audio and record.get("waveform_peaks"):
            peaks = record.get("waveform_peaks")
            if isinstance(peaks, list) and len(peaks) > 0:
                audio_estimated_duration = len(peaks) * 0.1
                duration = max(duration, audio_estimated_duration)

        result = dict(record) if isinstance(record, dict) else {}
        result["_index"] = index
        result["text"] = text
        result["calculated_duration"] = round(duration, 2)
        result["has_audio_aligned"] = has_audio
        result["status"] = "success"

        return result

    def stream_process_batch(self, records: List[Any]) -> Generator[Dict[str, Any], None, None]:
        """
        流式处理批量任务，每次完成一条记录时 yield 进度快照。
        """
        if not isinstance(records, list):
            records = [records] if records else []

        total_records = len(records)
        if total_records == 0:
            yield {
                "progress": 1.0,
                "completed": 0,
                "total": 0,
                "latest_result": None,
                "all_results_so_far": [],
                "is_final": True
            }
            return

        completed = 0
        all_results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(self._process_single_record, i, record): i
                for i, record in enumerate(records)
            }

            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                except Exception as e:
                    # 极端异常兜底，静默修复
                    result = {
                        "_index": index,
                        "status": "error",
                        "calculated_duration": 1.0,
                        "error_msg": str(e)
                    }

                all_results.append(result)
                completed += 1

                snapshot = {
                    "progress": round(completed / total_records, 4),
                    "completed": completed,
                    "total": total_records,
                    "latest_result": result,
                    "all_results_so_far": list(all_results),
                    "is_final": completed == total_records
                }
                yield snapshot

    def process_batch(self, records: List[Any]) -> Dict[str, Any]:
        """
        一次性处理批量任务，并返回有序的汇总结果。
        """
        final_snapshot = None
        for snapshot in self.stream_process_batch(records):
            final_snapshot = snapshot

        if not final_snapshot:
            return {"total_processed": 0, "success_count": 0, "results": []}

        sorted_results = sorted(final_snapshot["all_results_so_far"], key=lambda x: x.get("_index", 0))

        for r in sorted_results:
            r.pop("_index", None)

        return {
            "total_processed": final_snapshot["total"],
            "success_count": len([r for r in sorted_results if r.get("status") == "success"]),
            "results": sorted_results
        }
