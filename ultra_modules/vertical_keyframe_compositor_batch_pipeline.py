import concurrent.futures
import time
from typing import List, Dict, Any, Optional
import uuid
import threading

class RenderConfig:
    def __init__(self, width: int = 1080, height: int = 1920, enable_light_effects: bool = True, enable_speed_lines: bool = True):
        self.width = width if isinstance(width, int) and width > 0 else 1080
        self.height = height if isinstance(height, int) and height > 0 else 1920
        self.enable_light_effects = bool(enable_light_effects)
        self.enable_speed_lines = bool(enable_speed_lines)

class RenderTask:
    def __init__(self, task_id: str = "", image_data: Any = None, subtitle: str = "", subtitle_color: str = "#FFFFFF"):
        self.task_id = str(task_id) if task_id else str(uuid.uuid4())
        self.image_data = image_data if image_data is not None else "default_blank_image"
        self.subtitle = str(subtitle) if subtitle else ""
        self.subtitle_color = str(subtitle_color) if isinstance(subtitle_color, str) and subtitle_color.startswith("#") else "#FFFFFF"

class RenderResult:
    def __init__(self, task_id: str, success: bool, output_data: Any = None, error_message: str = ""):
        self.task_id = task_id
        self.success = success
        self.output_data = output_data
        self.error_message = error_message

class BatchProgressSnapshot:
    def __init__(self, batch_id: str, total: int, completed: int, successful: int, failed: int):
        self.batch_id = batch_id
        self.total = total
        self.completed = completed
        self.successful = successful
        self.failed = failed
        self.is_done = (completed == total) and (total > 0) or (total == 0)

class VerticalKeyframeCompositorBatchPipeline:
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers if isinstance(max_workers, int) and max_workers > 0 else 10
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)

        self._lock = threading.Lock()
        self._batches: Dict[str, Dict[str, Any]] = {}

    def _process_single(self, batch_id: str, task: RenderTask, config: RenderConfig) -> RenderResult:
        try:
            # Simulated rendering logic
            time.sleep(0.001) # Simulate some minimal work

            if task.image_data == "simulated_fatal_error":
                raise ValueError("Simulated rendering crash")

            processed_data = f"Rendered({config.width}x{config.height}): {str(task.image_data)}"
            if config.enable_light_effects:
                processed_data += " + LightEffects"
            if config.enable_speed_lines:
                processed_data += " + SpeedLines"
            if task.subtitle:
                processed_data += f" + DoubleStrokeSubtitle('{task.subtitle}', color={task.subtitle_color})"

            result = RenderResult(task_id=task.task_id, success=True, output_data=processed_data)
        except Exception as e:
            # Silent fix or fallback -> returning error in result
            result = RenderResult(task_id=task.task_id, success=False, error_message=str(e))

        with self._lock:
            if batch_id in self._batches:
                self._batches[batch_id]['completed'] += 1
                if result.success:
                    self._batches[batch_id]['successful'] += 1
                else:
                    self._batches[batch_id]['failed'] += 1
                self._batches[batch_id]['results'].append(result)

        return result

    def submit_batch(self, tasks: List[Any], config: Optional[RenderConfig] = None) -> str:
        """Submits a batch of tasks and returns a batch_id for non-blocking tracking."""
        if config is None:
            config = RenderConfig()

        batch_id = str(uuid.uuid4())

        with self._lock:
            self._batches[batch_id] = {
                'total': len(tasks),
                'completed': 0,
                'successful': 0,
                'failed': 0,
                'results': [],
                'futures': []
            }

        if not tasks:
            return batch_id

        futures = []
        for task in tasks:
            # Handle completely invalid task object silently by substituting with default
            if not isinstance(task, RenderTask):
                task = RenderTask(task_id=str(uuid.uuid4()), image_data=str(task) if task else "recovered_default_data")

            future = self.executor.submit(self._process_single, batch_id, task, config)
            futures.append(future)

        with self._lock:
            self._batches[batch_id]['futures'] = futures

        return batch_id

    def get_progress_snapshot(self, batch_id: str) -> Optional[BatchProgressSnapshot]:
        with self._lock:
            if batch_id not in self._batches:
                return None
            b = self._batches[batch_id]
            return BatchProgressSnapshot(
                batch_id=batch_id,
                total=b['total'],
                completed=b['completed'],
                successful=b['successful'],
                failed=b['failed']
            )

    def get_results(self, batch_id: str) -> List[RenderResult]:
        """Returns currently available results without blocking."""
        with self._lock:
            if batch_id not in self._batches:
                return []
            return list(self._batches[batch_id]['results'])

    def wait_for_completion(self, batch_id: str, timeout: Optional[float] = None) -> List[RenderResult]:
        """Optionally block to wait for completion."""
        futures = []
        with self._lock:
            if batch_id in self._batches:
                futures = self._batches[batch_id]['futures']

        if futures:
            concurrent.futures.wait(futures, timeout=timeout)

        return self.get_results(batch_id)

    def shutdown(self):
        self.executor.shutdown(wait=True)
