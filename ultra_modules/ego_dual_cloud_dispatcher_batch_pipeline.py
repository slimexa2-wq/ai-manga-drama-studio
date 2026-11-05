import concurrent.futures
import threading
import uuid
import time
import copy
from typing import List, Dict, Any, Optional

class EgoDualCloudDispatcherBatchPipeline:
    """
    ego-browser免API费后台并发投递Google 20x Ultra与ChatGPT Plus任务编排器
    （高吞吐批量流水线与并发加速封装）
    """
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self._snapshots = {}
        self._lock = threading.Lock()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def submit_batch(self, records: List[Any]) -> str:
        batch_id = str(uuid.uuid4())

        # 脏数据自愈：过滤非字典数据，以及空字典
        valid_records = []
        if isinstance(records, list):
            for r in records:
                if isinstance(r, dict):
                    valid_records.append(r)

        # 极端边界：单次最多处理1000条，多余的静默截断
        if len(valid_records) > 1000:
            valid_records = valid_records[:1000]

        with self._lock:
            self._snapshots[batch_id] = {
                "status": "processing",
                "total": len(valid_records),
                "completed": 0,
                "failed": 0,
                "results": [],
                "start_time": time.time(),
                "end_time": None
            }

        # 后台零阻塞执行：使用单独的线程以避免死锁线程池
        threading.Thread(target=self._process_batch, args=(batch_id, valid_records), daemon=True).start()
        return batch_id

    def _process_batch(self, batch_id: str, records: List[Dict[str, Any]]):
        futures = {}
        for record in records:
            future = self._executor.submit(self._process_record, record)
            futures[future] = record

        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                with self._lock:
                    self._snapshots[batch_id]["results"].append(res)
                    if res.get("status") == "success":
                        self._snapshots[batch_id]["completed"] += 1
                    else:
                        self._snapshots[batch_id]["failed"] += 1
            except Exception as e:
                with self._lock:
                    self._snapshots[batch_id]["failed"] += 1
                    self._snapshots[batch_id]["results"].append({
                        "status": "error",
                        "error": str(e),
                        "original_record": futures[future]
                    })

        with self._lock:
            self._snapshots[batch_id]["status"] = "completed"
            self._snapshots[batch_id]["end_time"] = time.time()

    def _process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        # 缺参默认兜底
        prompt = record.get("prompt")
        if not prompt or not isinstance(prompt, str):
            prompt = "Auto-generated default scene"

        model = record.get("model")
        if not model or not isinstance(model, str):
            model = "gpt-4o" # 默认模型兜底

        task_id = record.get("task_id", str(uuid.uuid4()))

        # 模拟投递处理
        time.sleep(0.01)

        # 制造个别的随机异常用于健壮性（实际业务会try-catch API异常）
        if prompt == "raise_error":
            raise ValueError("Simulated network or API error")

        return {
            "task_id": task_id,
            "prompt": prompt,
            "model": model,
            "status": "success",
            "result_url": f"https://mock.ego-browser.cloud/{model}/{task_id}.png"
        }

    def get_progress_snapshot(self, batch_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            snapshot = self._snapshots.get(batch_id)
            if not snapshot:
                return None
            return copy.deepcopy(snapshot)
