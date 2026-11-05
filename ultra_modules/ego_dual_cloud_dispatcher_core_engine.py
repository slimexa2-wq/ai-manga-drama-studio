import uuid

def build_dispatch_schedule(tasks, fallback_cloud="google_ultra", default_prompt="generate image"):
    """
    Core Pure Function Dispatcher for Ego Browser

    Silent fallback, zero config, auto heals dirty data.
    """
    VALID_CLOUDS = {"google_ultra", "chatgpt_plus"}

    # Ensure fallback_cloud is valid, if not force default
    safe_fallback_cloud = fallback_cloud if fallback_cloud in VALID_CLOUDS else "google_ultra"

    schedule = {
        "google_ultra": [],
        "chatgpt_plus": []
    }

    # Silently handle None or non-list inputs
    if not isinstance(tasks, list):
        return schedule

    for task in tasks:
        # Ignore completely invalid elements
        if not isinstance(task, dict):
            continue

        # Clean task ID
        task_id = task.get("id")
        if not task_id or not isinstance(task_id, (str, int)) or (isinstance(task_id, str) and not task_id.strip()):
            task_id = f"auto-{uuid.uuid4().hex[:8]}"
        elif isinstance(task_id, str):
            task_id = task_id.strip()

        # Clean prompt
        prompt = task.get("prompt")
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            prompt = default_prompt
        else:
            prompt = prompt.strip()

        # Determine target cloud
        target = task.get("target_cloud")
        if not target or not isinstance(target, str):
            target = safe_fallback_cloud
        else:
            target = target.strip().lower()
            if target not in VALID_CLOUDS:
                target = safe_fallback_cloud

        # Cleaned task
        cleaned_task = {
            "id": str(task_id),
            "prompt": prompt,
            "target_cloud": target
        }

        schedule[target].append(cleaned_task)

    return schedule
