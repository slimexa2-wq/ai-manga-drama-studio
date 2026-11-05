import json
import csv
import os
import concurrent.futures
import time
from typing import Any, Dict, List, Optional, Union

class EgoDualCloudDispatcher:
    def __init__(self, max_workers: int = 10, output_dir: str = "output"):
        self.max_workers = max_workers if isinstance(max_workers, int) and max_workers > 0 else 10
        self.output_dir = output_dir if output_dir else "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def _heal_task_data(self, task: Any) -> Dict[str, Any]:
        """
        Self-healing for dirty data:
        - If string, treat as text input.
        - If dict but missing required fields, fill defaults.
        - If list, join as string and treat as text.
        - If None, use default empty task.
        """
        if task is None:
            return {"text": "default_story_content", "type": "auto"}

        if isinstance(task, str):
            return {"text": task, "type": "auto"}

        if isinstance(task, list):
            return {"text": " ".join(str(item) for item in task), "type": "auto"}

        if isinstance(task, dict):
            healed = dict(task)
            if "text" not in healed and "content" in healed:
                healed["text"] = healed.pop("content")
            if "text" not in healed:
                healed["text"] = "default_story_content"
            if "type" not in healed:
                healed["type"] = "auto"
            return healed

        # Fallback for completely unrecognized types
        return {"text": str(task), "type": "auto"}

    def _mock_dispatch_to_cloud(self, task_id: int, task: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """
        Mock cloud dispatching logic. Returns fake generated results.
        """
        # Simulate network latency
        time.sleep(0.01)

        return {
            "task_id": task_id,
            "provider": provider,
            "original_text": task["text"],
            "status": "success",
            "generated_image_url": f"https://mock-{provider}.com/images/{task_id}.png",
            "generated_text": f"Processed by {provider}: {task['text'][:20]}..."
        }

    def _process_single_task(self, task_id: int, task: Any) -> Dict[str, Any]:
        healed_task = self._heal_task_data(task)

        # Dual cloud dispatch: Send to both Google Ultra and ChatGPT Plus
        # In a real app we might await both concurrently.
        res_google = self._mock_dispatch_to_cloud(task_id, healed_task, "google_ultra")
        res_gpt = self._mock_dispatch_to_cloud(task_id, healed_task, "chatgpt_plus")

        return {
            "task_id": task_id,
            "input": healed_task,
            "results": {
                "google_ultra": res_google,
                "chatgpt_plus": res_gpt
            }
        }

    def dispatch_tasks(self, tasks: List[Any]) -> List[Dict[str, Any]]:
        if not isinstance(tasks, list):
            tasks = [tasks]

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._process_single_task, i, t): i
                for i, t in enumerate(tasks)
            }
            for future in concurrent.futures.as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    task_id = future_to_task[future]
                    results.append({
                        "task_id": task_id,
                        "status": "error",
                        "error_message": str(e)
                    })

        # Sort results by task_id to maintain order
        results.sort(key=lambda x: x.get("task_id", -1))
        return results

    def export_results(self, results: List[Dict[str, Any]], format_type: str = "json", filename: str = "results") -> str:
        """
        Export results to JSON or Excel/CSV.
        """
        if format_type not in ["json", "excel", "csv"]:
            format_type = "json"

        filepath = os.path.join(self.output_dir, f"{filename}.{format_type}")

        if format_type == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
        else: # Handle ["excel", "csv"]
            # Fallback Excel to CSV for simplicity, using standard csv module
            filepath = os.path.join(self.output_dir, f"{filename}.csv")
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Task ID", "Input Text", "Google Image URL", "GPT Image URL"])
                for res in results:
                    if res.get("status") == "error":
                        writer.writerow([res.get("task_id", ""), "ERROR", "", ""])
                        continue

                    input_text = res.get("input", {}).get("text", "")
                    google_url = res.get("results", {}).get("google_ultra", {}).get("generated_image_url", "")
                    gpt_url = res.get("results", {}).get("chatgpt_plus", {}).get("generated_image_url", "")
                    writer.writerow([res.get("task_id", ""), input_text, google_url, gpt_url])

        return filepath

    def one_click_run(self) -> Dict[str, Any]:
        """
        Zero-parameter one-click execution.
        Provides a default task, dispatches it, and exports to JSON and CSV.
        """
        default_tasks = [
            "A breathtaking view of a cyberpunk city at night",
            {"content": "A hero with a glowing sword", "type": "character"},
            None # Dirty data test in one_click_run
        ]

        results = self.dispatch_tasks(default_tasks)
        json_path = self.export_results(results, format_type="json", filename="one_click_results")
        csv_path = self.export_results(results, format_type="csv", filename="one_click_results")

        return {
            "status": "success",
            "message": "One-click execution completed successfully.",
            "results_count": len(results),
            "exports": {
                "json": json_path,
                "csv": csv_path
            }
        }

def run_main():
    dispatcher = EgoDualCloudDispatcher()
    print("Running one-click dispatcher...")
    summary = dispatcher.one_click_run()
    print(json.dumps(summary, indent=4))

if __name__ == "__main__":
    run_main()  # pragma: no cover
