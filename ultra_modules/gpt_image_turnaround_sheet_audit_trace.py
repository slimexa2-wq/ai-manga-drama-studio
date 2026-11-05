import copy
from typing import Dict, Any, List

class AuditTraceManager:
    """
    Manages the audit trace for parameter transformation, logging steps
    for backend observability.
    """
    def __init__(self) -> None:
        self.traces: List[Dict[str, Any]] = []

    def log_change(self, step: str, original: Any, updated: Any, reason: str) -> None:
        self.traces.append({
            "step": step,
            "original": copy.deepcopy(original),
            "updated": copy.deepcopy(updated),
            "reason": reason
        })

    def get_traces(self) -> List[Dict[str, Any]]:
        return self.traces

    def clear(self) -> None:
        self.traces = []


class GPTImageTurnaroundSheetGenerator:
    """
    Generator for character turnaround sheets (front, side, back) and expressions
    optimized for GPT-Image-2. Includes silent fallback, self-healing of dirty data,
    and audit tracing for backend observability without front-end friction.
    """

    DEFAULT_CHARACTER_NAME = "Unknown Character"
    DEFAULT_STYLE = "anime style, flat color, clean lineart"
    DEFAULT_ANGLES = ["front view", "side view", "back view"]
    DEFAULT_EXPRESSIONS = ["neutral", "happy", "angry", "sad"]

    def __init__(self) -> None:
        self.audit_manager = AuditTraceManager()

    def _sanitize_list(self, raw_list: Any, default_list: List[str], step_name: str) -> List[str]:
        original = raw_list
        if not isinstance(raw_list, list):
            self.audit_manager.log_change(
                step=f"{step_name}_type_check",
                original=original,
                updated=default_list,
                reason="Input is not a list. Falling back to defaults."
            )
            return default_list.copy()

        # Sanitize and deduplicate
        cleaned = []
        for item in raw_list:
            if isinstance(item, str):
                item_clean = item.strip().lower()
                if item_clean and item_clean not in cleaned:
                    cleaned.append(item_clean)
            elif item is not None:
                # Auto-heal by converting to string
                item_clean = str(item).strip().lower()
                if item_clean and item_clean not in cleaned:
                    cleaned.append(item_clean)

        if not cleaned:
            self.audit_manager.log_change(
                step=f"{step_name}_empty_check",
                original=original,
                updated=default_list,
                reason="List became empty after sanitization. Falling back to defaults."
            )
            return default_list.copy()

        if cleaned != raw_list:
            self.audit_manager.log_change(
                step=f"{step_name}_sanitization",
                original=original,
                updated=cleaned,
                reason="Removed duplicates, stripped whitespace, or converted types."
            )

        return cleaned

    def _sanitize_string(self, raw_string: Any, default_string: str, step_name: str) -> str:
        original = raw_string
        if not isinstance(raw_string, str):
            if raw_string is None:
                self.audit_manager.log_change(
                    step=f"{step_name}_none_check",
                    original=original,
                    updated=default_string,
                    reason="Input is None. Falling back to default."
                )
                return default_string

            # Auto-heal by converting to string
            healed = str(raw_string).strip()
            self.audit_manager.log_change(
                step=f"{step_name}_type_cast",
                original=original,
                updated=healed,
                reason="Input is not a string. Auto-cast to string."
            )
            if not healed:
                self.audit_manager.log_change(
                    step=f"{step_name}_empty_cast_check",
                    original=original,
                    updated=default_string,
                    reason="Input casted to empty string. Falling back to default."
                )
                return default_string
            return healed

        healed = raw_string.strip()
        if not healed:
            self.audit_manager.log_change(
                step=f"{step_name}_empty_check",
                original=original,
                updated=default_string,
                reason="Input is empty string. Falling back to default."
            )
            return default_string

        if healed != raw_string:
            self.audit_manager.log_change(
                step=f"{step_name}_whitespace_strip",
                original=original,
                updated=healed,
                reason="Stripped leading/trailing whitespace."
            )

        return healed

    def generate(self,
                 character_name: Any = None,
                 style_description: Any = None,
                 angles: Any = None,
                 expressions: Any = None) -> Dict[str, Any]:
        """
        Generates the GPT-Image-2 prompt with extreme fault tolerance.
        Zero config, zero friction for the user. Missing parameters are safely defaulted.
        """
        self.audit_manager.clear()

        # 1. Sanitize Character Name
        safe_name = self._sanitize_string(
            character_name,
            self.DEFAULT_CHARACTER_NAME,
            "character_name"
        )

        # 2. Sanitize Style
        safe_style = self._sanitize_string(
            style_description,
            self.DEFAULT_STYLE,
            "style_description"
        )

        # 3. Sanitize Angles
        safe_angles = self._sanitize_list(
            angles if angles is not None else self.DEFAULT_ANGLES,
            self.DEFAULT_ANGLES,
            "angles"
        )

        # 4. Sanitize Expressions
        safe_expressions = self._sanitize_list(
            expressions if expressions is not None else self.DEFAULT_EXPRESSIONS,
            self.DEFAULT_EXPRESSIONS,
            "expressions"
        )

        # Build prompt
        angles_str = ", ".join(safe_angles)
        expressions_str = ", ".join(safe_expressions)

        prompt = (
            f"Character turnaround sheet of {safe_name}. "
            f"Style: {safe_style}. "
            f"Showing full body from {angles_str}. "
            f"Include additional headshots showing expressions: {expressions_str}. "
            f"White background, character design sheet layout."
        )

        return {
            "result": {
                "prompt": prompt,
                "clean_parameters": {
                    "character_name": safe_name,
                    "style_description": safe_style,
                    "angles": safe_angles,
                    "expressions": safe_expressions
                }
            },
            "audit_traces": self.audit_manager.get_traces()
        }
