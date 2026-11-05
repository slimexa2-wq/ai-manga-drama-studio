import uuid
import copy
from typing import Dict, Any, List
from datetime import datetime, timezone

class AuditLogger:
    """
    Backend full-chain traceable audit logger and difference highlight comparator.
    Quietly logs each conversion/deduplication/repair step for review.
    """
    def __init__(self) -> None:
        self.trace_log: List[Dict[str, Any]] = []
        self.trace_id: str = str(uuid.uuid4())

    def _generate_diff_highlight(self, original: Any, fixed: Any) -> str:
        orig_str = str(original)
        fixed_str = str(fixed)
        return f"Diff: [{orig_str}] -> [{fixed_str}]"

    def log_step(self, step_name: str, original: Any, fixed: Any, reason: str) -> None:
        self.trace_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step_name,
            "original_value": copy.deepcopy(original) if original is not None else None,
            "fixed_value": copy.deepcopy(fixed) if fixed is not None else None,
            "diff_highlight": self._generate_diff_highlight(original, fixed),
            "reason": reason
        })

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.trace_log


class WhiskSubjectBridge:
    """
    Google Labs Whisk Subject/Style/Scene 3-slot face lock and scene reproduction payload builder.
    """
    def __init__(self) -> None:
        pass

    @staticmethod
    def _clean_string(val: Any, default: str) -> tuple[str, bool]:
        """Returns cleaned string and a boolean indicating if a fix was applied."""
        if val is None:
            return default, True

        fixed = False
        if not isinstance(val, str):
            val = str(val)
            fixed = True

        stripped = val.strip()
        if stripped != val:
            fixed = True

        if not stripped:
            return default, True

        return stripped, fixed

    @staticmethod
    def _clean_list(val: Any, default: List[str]) -> tuple[List[str], bool]:
        """Returns cleaned list of strings and a boolean indicating if a fix was applied."""
        if val is None:
            return default, True

        fixed = False
        if not isinstance(val, list):
            if isinstance(val, str):
                cleaned = [x.strip() for x in val.split(',') if x.strip()]
                if not cleaned:
                    return default, True
                return cleaned, True
            val = [val]
            fixed = True

        seen = set()
        cleaned_list = []
        for item in val:
            if not isinstance(item, str):
                item = str(item)
                fixed = True
            stripped = item.strip()
            if stripped != item:
                fixed = True
            if stripped:
                if stripped not in seen:
                    seen.add(stripped)
                    cleaned_list.append(stripped)
                else:
                    fixed = True # Deduplicated
            else:
                fixed = True # Dropped empty

        if not cleaned_list:
            return default, True

        return cleaned_list, fixed

    def build_payload(self, subject: Any = None, style: Any = None, scene: Any = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Builds the clean payload, dropping unsupported kwargs and applying fallback/self-healing.
        """
        audit = AuditLogger()

        clean_subj, fixed_subj = self._clean_string(subject, "default_subject")
        if fixed_subj:
            audit.log_step("clean_subject", subject, clean_subj, "Type cast, strip, or fallback applied")

        clean_style, fixed_style = self._clean_string(style, "default_style")
        if fixed_style:
            audit.log_step("clean_style", style, clean_style, "Type cast, strip, or fallback applied")

        clean_scene, fixed_scene = self._clean_list(scene, ["default_scene"])
        if fixed_scene:
            audit.log_step("clean_scene", scene, clean_scene, "Type cast, strip, deduplicate, or fallback applied")

        if kwargs:
            audit.log_step("drop_unsupported_kwargs", kwargs, {}, "Dropped unsupported kwargs")

        current_time = datetime.now(timezone.utc)

        payload = {
            "subject": clean_subj,
            "style": clean_style,
            "scene": clean_scene,
            "timestamp": current_time.isoformat()
        }

        return {
            "payload": payload,
            "audit_trace": audit.get_logs()
        }
