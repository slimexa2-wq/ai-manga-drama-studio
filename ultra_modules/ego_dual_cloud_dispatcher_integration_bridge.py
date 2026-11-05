import asyncio
import concurrent.futures
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator

logger = logging.getLogger(__name__)

class SchemaForwardCompatibilityConverter:
    """
    Silently and automatically maps fields using heuristic matching.
    Provides robust fallback defaults for missing fields without explicit mapping tables.
    """

    @staticmethod
    def map_payload(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw_payload, dict):
            # Self-healing: if it's completely wrong type, return an empty dict to be filled with defaults
            logger.warning("Payload is not a dictionary. Self-healing by substituting empty dict.")
            raw_payload = {}

        mapped = {}

        # 1. Prompt mapping
        prompt = raw_payload.get("prompt") or raw_payload.get("text_prompt") or raw_payload.get("user_prompt") or raw_payload.get("content")
        # Self-healing: if not string or empty, provide default
        if not isinstance(prompt, str) or not prompt.strip():
            mapped["prompt"] = "generate a default creative media"
        else:
            mapped["prompt"] = prompt.strip()

        # 2. Model mapping
        model = raw_payload.get("model") or raw_payload.get("engine") or raw_payload.get("model_name")
        if not isinstance(model, str) or not model.strip():
            mapped["model"] = "auto-default-model"
        else:
            mapped["model"] = model.strip()

        # 3. Cloud Provider Mapping
        provider = raw_payload.get("provider") or raw_payload.get("cloud")
        if not isinstance(provider, str) or not provider.strip():
            mapped["provider"] = "auto"
        else:
            provider = provider.strip().lower()
            if provider in ["google", "20x", "ultra", "veo"]:
                mapped["provider"] = "google_ultra"
            elif provider in ["chatgpt", "openai", "plus", "gpt"]:
                mapped["provider"] = "chatgpt_plus"
            else:
                mapped["provider"] = "auto"

        # 4. Params mapping
        params = raw_payload.get("params") or raw_payload.get("parameters") or raw_payload.get("config")
        if not isinstance(params, dict):
            mapped["params"] = {}
        else:
            mapped["params"] = params

        return mapped


class EgoDualCloudDispatcher:
    """
    Concurrency (ThreadPoolExecutor) for seamless dispatch to Google 20x Ultra and ChatGPT Plus,
    ensuring zero-configuration tolerance, self-healing, and defaults for missing parameters.
    """
    def __init__(self, max_workers: int = 10):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def _sync_dispatch_task(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous dispatch logic intended to run in a thread pool.
        """
        try:
            # 1. Schema mapping and healing
            clean_payload = SchemaForwardCompatibilityConverter.map_payload(raw_payload)

            # 2. Simulated routing and processing
            provider = clean_payload["provider"]
            if provider == "google_ultra":
                # Simulated Google 20x Ultra processing
                status = "success"
                result = f"Mocked Google Ultra result for: {clean_payload['prompt'][:20]}..."
            elif provider == "chatgpt_plus":
                # Simulated ChatGPT Plus processing
                status = "success"
                result = f"Mocked ChatGPT Plus result for: {clean_payload['prompt'][:20]}..."
            else:
                # Auto-routing based on some heuristic
                # We'll just default to chatgpt_plus
                status = "success"
                result = f"Mocked Auto-Routed result for: {clean_payload['prompt'][:20]}..."
                clean_payload["provider"] = "chatgpt_plus (auto-routed)"

            return {
                "status": status,
                "result": result,
                "processed_payload": clean_payload,
                "error": None
            }
        except Exception as e:
            # Zero-configuration tolerance: catch all, don't crash
            logger.error(f"Error during dispatch: {str(e)}")
            return {
                "status": "error",
                "result": None,
                "processed_payload": {},
                "error": str(e)
            }

    async def async_orchestrate_concurrent_tasks(self, payloads: List[Dict[str, Any]]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream-based non-blocking progress updates for batch tasks.
        """
        loop = asyncio.get_running_loop()

        # Self healing if not list
        if not isinstance(payloads, list):
            logger.warning("Payloads is not a list. Self-healing by wrapping in list.")
            payloads = [payloads] if payloads else []

        # Create futures
        futures = []
        for payload in payloads:
            future = loop.run_in_executor(self.executor, self._sync_dispatch_task, payload)
            futures.append(future)

        # Yield as they complete
        for completed_future in asyncio.as_completed(futures):
            try:
                result = await completed_future
                yield result
            except Exception as e:
                # Zero-configuration tolerance on the loop level
                logger.error(f"Error awaiting future: {str(e)}")
                yield {
                    "status": "error",
                    "result": None,
                    "processed_payload": {},
                    "error": str(e)
                }

    def shutdown(self):
        self.executor.shutdown(wait=True)
