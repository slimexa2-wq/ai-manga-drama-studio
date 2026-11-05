import concurrent.futures
import threading
import time
import uuid

class WhiskPayloadBuilder:
    @staticmethod
    def build(subject=None, style=None, scene=None):
        """
        构建 Google Labs Whisk 载荷，包含主题、风格、场景三槽位。
        缺参自动设合理默认值，脏数据自愈（非字符串转化为字符串，空值设为默认）。
        """
        # 脏数据自愈与默认值兜底
        if not isinstance(subject, str) or not subject.strip():
            subject = "default subject"
        if not isinstance(style, str) or not style.strip():
            style = "default style"
        if not isinstance(scene, str) or not scene.strip():
            scene = "default scene"

        return {
            "subject": subject.strip(),
            "style": style.strip(),
            "scene": scene.strip(),
            "timestamp": time.time(),
            "status": "built"
        }

class WhiskBatchPipeline:
    def __init__(self, max_workers=10):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.futures = {}
        self.results = {}
        self.progress = {
            "total": 0,
            "completed": 0,
            "failed": 0
        }
        self.lock = threading.Lock()
        self._current_batch_id = None

    def _process_item(self, item, task_id):
        try:
            # 模拟处理延迟
            # time.sleep(0.01)

            # 使用提取的字典值，并容错非字典类型的 item
            if not isinstance(item, dict):
                item = {"subject": str(item)}

            payload = WhiskPayloadBuilder.build(
                subject=item.get("subject"),
                style=item.get("style"),
                scene=item.get("scene")
            )
            payload["task_id"] = task_id
            payload["processed"] = True

            return payload
        except Exception as e:
            return {"error": str(e), "task_id": task_id, "failed": True}

    def _done_callback(self, future):
        try:
            result = future.result()
            task_id = result.get("task_id")
            with self.lock:
                if result.get("error"):
                    self.progress["failed"] += 1
                else:
                    self.progress["completed"] += 1
                self.results[task_id] = result
        except Exception as e:
            with self.lock:
                self.progress["failed"] += 1

    def submit_batch(self, items):
        """
        提交批量处理任务，返回批次 ID。非阻塞流式处理。
        """
        if not isinstance(items, list):
            items = []

        batch_id = str(uuid.uuid4())

        with self.lock:
            self._current_batch_id = batch_id
            self.progress["total"] += len(items)

        for idx, item in enumerate(items):
            task_id = f"{batch_id}_{idx}"
            future = self.executor.submit(self._process_item, item, task_id)
            future.add_done_callback(self._done_callback)

            with self.lock:
                self.futures[task_id] = future

        return batch_id

    def get_progress_snapshot(self):
        """
        获取当前进度快照。
        """
        with self.lock:
            total = self.progress["total"]
            completed = self.progress["completed"]
            failed = self.progress["failed"]
            results_count = len(self.results)
            current_batch_id = self._current_batch_id

        return {
            "batch_id": current_batch_id,
            "total": total,
            "completed": completed,
            "failed": failed,
            "is_done": (completed + failed) == total and total > 0,
            "results_count": results_count
        }

    def get_results(self):
        """
        获取处理结果（非阻塞汇总）。
        """
        with self.lock:
            return list(self.results.values())

    def shutdown(self):
        self.executor.shutdown(wait=True)
