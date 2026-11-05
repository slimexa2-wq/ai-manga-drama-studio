import time
import copy
import uuid

class TaskSnapshot:
    def __init__(self, task_id, original_data):
        self.task_id = task_id
        self.original_data = copy.deepcopy(original_data)
        self.timestamp = time.time()

class EgoDualCloudDispatcher:
    def __init__(self, undo_window_seconds=5):
        self.undo_window_seconds = undo_window_seconds
        self.snapshots = {}  # task_id -> TaskSnapshot
        self.dispatched_tasks = {} # task_id -> healed_data

    def _heal_task_data(self, raw_data):
        """Silently heal dirty data and provide default fallbacks."""
        if not isinstance(raw_data, dict):
            raw_data = {}

        healed_data = copy.deepcopy(raw_data)

        # Default fallbacks
        if 'model' not in healed_data:
            healed_data['model'] = 'gemini-3.1-pro'

        if 'provider' not in healed_data:
            # Infer provider from model if possible, otherwise default to google
            model_name = healed_data.get('model', '').lower()
            if any(x in model_name for x in ['gpt', 'o3', 'sora']):
                healed_data['provider'] = 'openai'
            else:
                healed_data['provider'] = 'google'

        if 'parameters' not in healed_data or not isinstance(healed_data['parameters'], dict):
            healed_data['parameters'] = {}

        # Silent self-healing for extreme edge cases (e.g. string numbers, invalid types)
        if 'max_tokens' in healed_data['parameters']:
            try:
                healed_data['parameters']['max_tokens'] = int(healed_data['parameters']['max_tokens'])
            except (ValueError, TypeError):
                healed_data['parameters']['max_tokens'] = 2048 # Default reasonable value
        else:
            healed_data['parameters']['max_tokens'] = 2048

        if 'temperature' in healed_data['parameters']:
            try:
                temp = float(healed_data['parameters']['temperature'])
                healed_data['parameters']['temperature'] = max(0.0, min(1.0, temp)) # Bound between 0 and 1
            except (ValueError, TypeError):
                healed_data['parameters']['temperature'] = 0.7
        else:
            healed_data['parameters']['temperature'] = 0.7

        return healed_data

    def take_snapshot(self, task_id, original_data):
        self.snapshots[task_id] = TaskSnapshot(task_id, original_data)

        # Clean up old snapshots (simplified garbage collection)
        current_time = time.time()
        expired = [tid for tid, snap in self.snapshots.items()
                  if current_time - snap.timestamp > self.undo_window_seconds * 2] # Keep a bit longer for safety margin
        for tid in expired:
            del self.snapshots[tid]

    def dispatch_task(self, task_data=None):
        """
        Dispatches a task.
        - Automatically heals input data (no errors thrown).
        - Creates a snapshot for undo.
        """
        task_id = str(uuid.uuid4())

        # Save snapshot BEFORE healing
        self.take_snapshot(task_id, task_data)

        # Heal data
        healed_data = self._heal_task_data(task_data)
        healed_data['task_id'] = task_id

        # "Dispatch" task
        self.dispatched_tasks[task_id] = healed_data

        return task_id, healed_data

    def undo_task(self, task_id):
        """
        Attempts to undo a task if within the 5-second window.
        Returns (success: bool, message: str)
        """
        if task_id not in self.snapshots:
            return False, "Snapshot not found or expired."

        snapshot = self.snapshots[task_id]
        if time.time() - snapshot.timestamp > self.undo_window_seconds:
            # Too late to undo
            del self.snapshots[task_id] # Clean up
            return False, "Undo window expired."

        # Perform undo
        if task_id in self.dispatched_tasks:
            del self.dispatched_tasks[task_id]

        # Clean up snapshot
        del self.snapshots[task_id]

        return True, "Task successfully undone."
