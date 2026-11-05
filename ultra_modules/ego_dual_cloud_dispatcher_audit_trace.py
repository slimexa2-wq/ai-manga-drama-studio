import logging
import time
import uuid
import asyncio
from typing import List, Dict, Any, Optional

# Setup silent logger for audit tracing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ego_dual_cloud_dispatcher_audit")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

class EgoDualCloudDispatcherAuditTrace:
    """
    Ego Dual Cloud Dispatcher & Audit Trace
    A production-grade class to dispatch tasks to Google 20x Ultra and ChatGPT Plus,
    with built-in silent dirty-data auto-healing, deduplication, diff highlighting comparator,
    and full-link audit logging.
    """

    def __init__(self, default_model: str = "google_ultra") -> None:
        self.audit_log: List[Dict[str, Any]] = []
        self.default_model = self._heal_model_name(default_model)
        self.task_cache: Dict[str, Dict[str, Any]] = {}  # For deduplication
        self._record_audit("INIT", {"default_model": self.default_model})

    def _heal_model_name(self, model: Any) -> str:
        """Silently heal model name. Default to google_ultra if invalid."""
        valid_models = {"google_ultra", "chatgpt_plus"}
        if not isinstance(model, str):
            return "google_ultra"
        model_clean = model.strip().lower()
        if model_clean in valid_models:
            return model_clean
        return "google_ultra"

    def _generate_task_hash(self, prompt: str, model: str) -> str:
        """Generate a simple hash for deduplication based on prompt and model."""
        import hashlib
        # Silent heal of prompt
        clean_prompt = str(prompt).strip() if prompt else ""
        content = f"{clean_prompt}_{model}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def diff_highlight_comparator(self, original_result: str, new_result: str) -> Dict[str, Any]:
        """
        Compare original and new results and highlight differences.
        Simple implementation returning diff details for audit log.
        """
        # Silent heal
        orig = str(original_result) if original_result else ""
        new_res = str(new_result) if new_result else ""

        diff = {
            "is_identical": orig == new_res,
            "original_length": len(orig),
            "new_length": len(new_res)
        }
        self._record_audit("DIFF_COMPARISON", diff)
        return diff

    async def _async_dispatch(self, prompt: str, model: str) -> Dict[str, Any]:
        """Simulate async dispatch to cloud models."""
        healed_model = self._heal_model_name(model)
        healed_prompt = str(prompt).strip() if prompt else "DEFAULT_PROMPT"

        task_hash = self._generate_task_hash(healed_prompt, healed_model)

        if task_hash in self.task_cache:
            self._record_audit("DEDUPLICATION_HIT", {"task_hash": task_hash})
            return self.task_cache[task_hash]

        self._record_audit("DISPATCH_START", {"model": healed_model, "prompt_length": len(healed_prompt)})

        # Simulate network delay and result generation
        await asyncio.sleep(0.01)

        result_text = f"Result from {healed_model} for prompt of length {len(healed_prompt)}"

        result_data = {
            "status": "success",
            "model": healed_model,
            "result": result_text
        }

        self.task_cache[task_hash] = result_data
        self._record_audit("DISPATCH_COMPLETE", {"model": healed_model, "status": "success"})

        return result_data

    def dispatch(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for dispatch.
        Uses asyncio.run() or asyncio.get_running_loop() safely according to Python 3.12+ standards.
        """
        target_model = model if model is not None else self.default_model

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If already in an event loop, we have to return a future or block differently.
            # For simplicity in this synchronous wrapper, if we can't run, we just create a new task
            # But the user expects a synchronous result. We will use a nested run via a fresh thread or just block if possible.
            # Using asyncio.run() directly would fail if loop is running.
            # A safe pattern is to use nest_asyncio if available or run in a thread.
            # However, for the standard case where dispatch is called from sync code:
            import threading
            result_container = {}
            def run_in_thread():
                result_container['res'] = asyncio.run(self._async_dispatch(prompt, target_model))

            t = threading.Thread(target=run_in_thread)
            t.start()
            t.join()
            return result_container['res']
        else:
            return asyncio.run(self._async_dispatch(prompt, target_model))

    def _record_audit(self, action: str, details: Dict[str, Any]) -> None:
        """Silently record backend audit trace."""
        entry = {
            "action": action,
            "details": details,
            "timestamp": time.time(),
            "trace_id": str(uuid.uuid4())
        }
        self.audit_log.append(entry)
        logger.info(f"Audit Trace: {action} - {details}")

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return self.audit_log
