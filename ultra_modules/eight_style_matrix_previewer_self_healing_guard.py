import time
import copy
from typing import Any, Dict, Optional

class EightStyleMatrixPreviewerSelfHealingGuard:
    """
    Eight Style Matrix Previewer with Self-Healing Guard.
    Provides one-click matrix preview for 8 styles, auto-heals dirty data,
    and supports a 5-second one-click undo snapshot mechanism.
    """
    STYLES = [
        "修仙",
        "都市逆袭",
        "韩漫财阀",
        "热血少年",
        "中式规则怪谈",
        "赛博朋克",
        "末日废土",
        "克苏鲁神话"
    ]

    DEFAULT_PROMPT = "默认主角"
    DEFAULT_RESOLUTION = "1024x1024"

    def __init__(self):
        self._snapshots = []
        self._current_state = None

    def _heal_input(self, prompt: Any, options: Any) -> tuple[str, Dict[str, Any]]:
        # Heal prompt: Zero-configuration fault tolerance for dirty data
        healed_prompt = self.DEFAULT_PROMPT
        if prompt is not None:
            try:
                if isinstance(prompt, (list, dict)):
                    pass # Keep default
                else:
                    text = str(prompt).strip()
                    if text and text.lower() != "none":
                        healed_prompt = text
            except Exception:
                pass # Silently swallow and use default

        # Heal options
        if not isinstance(options, dict):
            healed_options = {}
        else:
            try:
                healed_options = copy.deepcopy(options)
            except Exception:
                healed_options = {}

        # Ensure critical parameter 'resolution' exists
        if 'resolution' not in healed_options or not isinstance(healed_options['resolution'], str):
            healed_options['resolution'] = self.DEFAULT_RESOLUTION

        return healed_prompt, healed_options

    def generate_preview(self, prompt: Any = None, options: Any = None) -> Dict[str, Any]:
        """
        Generate 8-style matrix preview.
        Automatically heals input, sets defaults for missing parameters,
        and saves a lightweight snapshot for 5-second undo.
        """
        healed_prompt, healed_options = self._heal_input(prompt, options)

        # Generate matrix
        matrix = {
            style: {
                "prompt": f"[{style}] {healed_prompt}",
                "resolution": healed_options['resolution'],
                "status": "success"
            }
            for style in self.STYLES
        }

        new_state = {
            "prompt": healed_prompt,
            "options": healed_options,
            "matrix": matrix,
            "timestamp": time.time()
        }

        # Save current state to snapshot before updating
        if self._current_state is not None:
            self._snapshots.append(copy.deepcopy(self._current_state))

        self._current_state = new_state
        return matrix

    def undo(self) -> bool:
        """
        One-click undo to previous snapshot within 5 seconds.
        Returns True if successful, False if no snapshot or time expired (strict silent fail).
        """
        if not self._snapshots or self._current_state is None:
            return False

        current_time = time.time()

        # Check if within 5 seconds
        if current_time - self._current_state["timestamp"] <= 5.0:
            self._current_state = self._snapshots.pop()
            return True

        return False

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        return self._current_state
