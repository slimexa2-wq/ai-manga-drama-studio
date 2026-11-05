import json
import time
import copy

class GPTImageTurnaroundSheetSelfHealingGuard:
    """
    ChatGPT Plus (GPT-Image-2) Turnaround Sheet Prompt Generator with Self-Healing Guard.
    Provides auto-fallback, dirty data self-healing, and a 5-second one-click undo snapshot mechanism.
    """
    def __init__(self):
        self._current_state = None
        self._snapshot_history = []
        self._undo_window_seconds = 5.0

    def generate(self, character_desc=None, style=None, include_expressions=None, aspect_ratio=None, **kwargs):
        # Save snapshot of the current state before overriding it
        if self._current_state is not None:
            snapshot = {
                "state": copy.deepcopy(self._current_state),
                "timestamp": time.time()
            }
            self._snapshot_history.append(snapshot)
            # Maintain a lightweight history (keep last 10 snapshots max)
            if len(self._snapshot_history) > 10:
                self._snapshot_history.pop(0)

        # 1. Clean and fallback `character_desc`
        if not isinstance(character_desc, str):
            if isinstance(character_desc, (dict, list)):
                character_desc = json.dumps(character_desc, ensure_ascii=False)
            else:
                character_desc = str(character_desc) if character_desc is not None else ""
        character_desc = character_desc.strip()
        if not character_desc:
            character_desc = "A handsome anime protagonist with a mysterious aura, wearing a dark cloak."

        # 2. Clean and fallback `style`
        if not isinstance(style, str):
            style = str(style) if style is not None else ""
        style = style.strip()
        if not style:
            style = "high quality anime style, masterpiece, best quality, ultra-detailed"

        # 3. Clean and fallback `include_expressions`
        if include_expressions is None:
            include_expressions = True
        elif isinstance(include_expressions, str):
            val = include_expressions.strip().lower()
            include_expressions = val not in ("false", "0", "no", "f", "n", "")
        else:
            include_expressions = bool(include_expressions)

        # 4. Clean and fallback `aspect_ratio`
        if not isinstance(aspect_ratio, str):
            aspect_ratio = str(aspect_ratio) if aspect_ratio is not None else ""
        aspect_ratio = aspect_ratio.strip().lower()

        valid_aspect_ratios = {"16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "9:21"}
        if aspect_ratio not in valid_aspect_ratios:
            # Try to clean common malformed strings like "16x9" or "16-9"
            cleaned_ar = aspect_ratio.replace("x", ":").replace("-", ":").replace(" ", "").replace("_", ":")
            if cleaned_ar in valid_aspect_ratios:
                aspect_ratio = cleaned_ar
            else:
                aspect_ratio = "16:9" # Default fallback

        # 5. Build prompt
        prompt_lines = [
            "Create a character design turnaround sheet for the following character:",
            f"Character Description: {character_desc}",
            f"Style: {style}",
            "",
            "The sheet MUST include full-body views of the character from the following angles:",
            "- Front view",
            "- Side view",
            "- Back view",
            "Align all views on the same ground line. Ensure consistent clothing, anatomy, and proportions across all angles."
        ]

        if include_expressions:
            prompt_lines.extend([
                "",
                "Additionally, include a section with 3-4 different facial expressions for the character (e.g., smiling, angry, sad, surprised)."
            ])

        prompt_lines.extend([
            "",
            f"--ar {aspect_ratio} --niji 6"
        ])

        prompt = "\n".join(prompt_lines)

        result = {
            "prompt": prompt,
            "config": {
                "character_desc": character_desc,
                "style": style,
                "include_expressions": include_expressions,
                "aspect_ratio": aspect_ratio
            }
        }

        self._current_state = copy.deepcopy(result)
        return result

    def undo(self):
        """
        Reverts to the previous state if within the 5-second window.
        Fails silently and returns None if no valid undo snapshot exists.
        """
        if not self._snapshot_history:
            return None

        last_snapshot = self._snapshot_history[-1]
        elapsed_time = time.time() - last_snapshot["timestamp"]

        if elapsed_time <= self._undo_window_seconds:
            # Valid undo
            self._snapshot_history.pop()
            self._current_state = copy.deepcopy(last_snapshot["state"])
            return copy.deepcopy(self._current_state)
        else:
            # Expired undo window, fail silently
            return None

    def get_current_state(self):
        """Returns the current state without generating a new one."""
        return copy.deepcopy(self._current_state)
