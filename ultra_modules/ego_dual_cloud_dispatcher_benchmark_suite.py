import asyncio
import time
from typing import Any, Dict, List, Optional
import uuid
import datetime

class SyntheticFixturesBuilder:
    """Builder for generating synthetic datasets for extreme edge cases."""

    @staticmethod
    def generate_normal_data() -> Dict[str, Any]:
        return {
            "task_id": str(uuid.uuid4()),
            "provider": "google",
            "model": "gemini-3.1-pro",
            "prompt": "Create a simple comic scene.",
            "timestamp": time.time()
        }

    @staticmethod
    def generate_missing_params_data() -> Dict[str, Any]:
        return {
            "prompt": "Create a comic scene."
        }

    @staticmethod
    def generate_dirty_data() -> Dict[str, Any]:
        return {
            "task_id": "invalid-uuid!@#$",
            "provider": None,
            "model": 12345,
            "prompt": "Create a scene \x00\x01\x02",
            "timestamp": "not-a-timestamp"
        }

    @staticmethod
    def generate_cross_boundary_data() -> Dict[str, Any]:
        # Generate timestamps for end of year/month transitions
        return {
            "task_id": str(uuid.uuid4()),
            "provider": "openai",
            "model": "gpt-4o",
            "prompt": "Boundary test",
            "timestamp": datetime.datetime(2023, 12, 31, 23, 59, 59).timestamp()
        }

    @staticmethod
    def generate_massive_concurrency_batch(size: int = 1000) -> List[Dict[str, Any]]:
        return [SyntheticFixturesBuilder.generate_normal_data() for _ in range(size)]


class EgoDualCloudDispatcher:
    """
    Dispatcher for Google 20x Ultra and ChatGPT Plus tasks.
    Implements auto-fallback, zero configuration, and dirty data sanitization.
    """

    def __init__(self):
        self.default_provider = "google"
        self.default_model = "gemini-3.1-pro"

    def _sanitize_and_fill_defaults(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizes dirty data and fills in missing parameters with defaults."""
        sanitized = {}

        # Task ID
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 100:
             sanitized["task_id"] = str(uuid.uuid4())
        else:
             # Remove non-alphanumeric chars just to be safe, except dashes
             sanitized["task_id"] = "".join(c for c in task_id if c.isalnum() or c == '-')
             if not sanitized["task_id"]:
                 sanitized["task_id"] = str(uuid.uuid4())

        # Provider
        provider = task.get("provider")
        if provider not in ["google", "openai"]:
            sanitized["provider"] = self.default_provider
        else:
            sanitized["provider"] = provider

        # Model
        model = task.get("model")
        if not isinstance(model, str):
            sanitized["model"] = self.default_model if sanitized["provider"] == "google" else "gpt-4o"
        else:
            sanitized["model"] = model

        # Prompt
        prompt = task.get("prompt")
        if not isinstance(prompt, str):
            sanitized["prompt"] = "Default fallback prompt for generation."
        else:
            # Strip weird control chars
            sanitized["prompt"] = "".join(c for c in prompt if c.isprintable() or c in ['\n', '\t'])
            if not sanitized["prompt"].strip():
                sanitized["prompt"] = "Default fallback prompt for generation."

        # Timestamp
        timestamp = task.get("timestamp")
        if not isinstance(timestamp, (int, float)):
            sanitized["timestamp"] = time.time()
        else:
            sanitized["timestamp"] = timestamp

        return sanitized

    async def _mock_dispatch(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Mocks the actual API dispatch, returning immediately for benchmark purposes."""
        # Simulated sub-millisecond processing
        await asyncio.sleep(0)

        return {
            "status": "success",
            "processed_task_id": task["task_id"],
            "provider": task["provider"],
            "model": task["model"],
            "result_length": len(task["prompt"]),
            "processed_at": time.time()
        }

    async def dispatch_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches a single task, ensuring sanitization."""
        safe_task = self._sanitize_and_fill_defaults(task)
        return await self._mock_dispatch(safe_task)

    async def dispatch_batch(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Dispatches a batch of tasks concurrently."""
        coroutines = [self.dispatch_task(task) for task in tasks]
        return await asyncio.gather(*coroutines)

    def dispatch_batch_sync(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Synchronous wrapper for batch dispatching."""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                raise RuntimeError("Event loop is already running, use async version.")
        except RuntimeError:
            pass
        return asyncio.run(self.dispatch_batch(tasks))
