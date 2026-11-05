import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional


class AuditLogger:
    """Silently traces execution steps and records data transformations."""

    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def log(self, step: str, details: Dict[str, Any]) -> None:
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "details": details
        })

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.logs


class Golden3SHookSplitter:
    """
    Splits a novel/script into episodes based on 'Golden 3s hooks' and 'cliffhangers'.
    It includes robust data healing, sensible defaults, and silent audit tracing.
    """

    def __init__(self):
        self.audit_logger = AuditLogger()

    def _clean_and_heal_text(self, text: Any) -> str:
        """Self-heal dirty data: None, int, excessive whitespace, etc."""
        original_type = type(text).__name__
        if text is None:
            healed = ""
            original_str = ""
        elif not isinstance(text, str):
            healed = str(text)
            original_str = healed
        else:
            healed = text
            original_str = text

        # Normalize whitespace
        healed = re.sub(r'\s+', ' ', healed).strip()

        # Simple diff highlight (audit log): difference in length or exact mismatch
        diff_info = {
            "was_modified": original_str != healed,
            "original_length": len(original_str),
            "healed_length": len(healed)
        }

        self.audit_logger.log(
            "clean_and_heal_text",
            {"original_type": original_type, "diff_highlight": diff_info}
        )
        return healed

    def _resolve_params(self, min_len: Optional[int], max_len: Optional[int]) -> Tuple[int, int]:
        """Resolve missing parameters with sensible defaults."""
        default_min = 500
        default_max = 2000

        resolved_min = min_len if isinstance(min_len, int) and min_len > 0 else default_min
        resolved_max = max_len if isinstance(max_len, int) and max_len > resolved_min else default_max

        # If user provides a weird combination where min > max
        if resolved_min >= resolved_max:
            resolved_min = default_min
            resolved_max = max(default_max, resolved_min + 1000)

        self.audit_logger.log(
            "resolve_params",
            {
                "input_min": min_len,
                "input_max": max_len,
                "resolved_min": resolved_min,
                "resolved_max": resolved_max
            }
        )
        return resolved_min, resolved_max

    def _score_split_point(self, text: str, index: int) -> int:
        """
        Score a potential split point (punctuation).
        Higher score means a better hook/cliffhanger.
        """
        score = 0
        if index < 0 or index >= len(text):
            return score

        # Check context around the split point
        context_before = text[max(0, index - 50):index]
        context_after = text[index:min(len(text), index + 50)]

        # Cliffhanger patterns before the split (end of episode)
        cliffhanger_keywords = ['死', '惊', '绝望', '意外', '怎么会', '到底', '突然', '难道', '不可能']
        for keyword in cliffhanger_keywords:
            if keyword in context_before:
                score += 10

        # Question marks and exclamation marks are strong cliffhangers
        if context_before.endswith(('？', '！', '...', '???', '!!!', '?', '!')):
            score += 20

        # Hook patterns after the split (start of next episode)
        hook_keywords = ['重生', '系统', '叮', '复仇', '竟然', '但是', '就在这时']
        for keyword in hook_keywords:
            if keyword in context_after:
                score += 15

        return score

    def split(self, text: Any, min_length: Optional[int] = None, max_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Main entry point to split text into episodes.
        Returns a dict containing the episodes and the audit logs.
        """
        self.audit_logger.log("start_split", {"input_length": len(str(text)) if text is not None else 0})

        clean_text = self._clean_and_heal_text(text)
        min_len, max_len = self._resolve_params(min_length, max_length)

        if not clean_text:
            self.audit_logger.log("early_return", {"reason": "empty_text"})
            return {
                "episodes": [],
                "audit_logs": self.audit_logger.get_logs()
            }

        if len(clean_text) <= max_len:
            self.audit_logger.log("single_episode", {"reason": "text_shorter_than_max"})
            return {
                "episodes": [clean_text],
                "audit_logs": self.audit_logger.get_logs()
            }

        episodes = []
        current_idx = 0

        while True:
            remaining_len = len(clean_text) - current_idx
            if remaining_len <= max_len:
                episodes.append(clean_text[current_idx:])
                self.audit_logger.log("append_final_episode", {"length": remaining_len})
                break

            # Search for best split point in the window [current_idx + min_len, current_idx + max_len]
            search_start = current_idx + min_len
            search_end = min(current_idx + max_len, len(clean_text))

            # Find all punctuation marks in the window
            # We look for punctuation that usually ends a sentence
            window_text = clean_text[search_start:search_end]
            punctuation_indices = [
                m.start() + search_start for m in re.finditer(r'[。！？.!?\n]', window_text)
            ]

            best_split_idx = -1
            best_score = -1

            if punctuation_indices:
                for idx in punctuation_indices:
                    # The actual split point is right after the punctuation
                    split_candidate = idx + 1
                    score = self._score_split_point(clean_text, split_candidate)
                    if score > best_score:
                        best_score = score
                        best_split_idx = split_candidate
            else:
                # If no punctuation, we just split at max_len
                # Or at the last space if possible
                space_indices = [
                    m.start() + search_start for m in re.finditer(r'\s', window_text)
                ]
                if space_indices:
                    best_split_idx = space_indices[-1] + 1
                else:
                    best_split_idx = search_end
                best_score = 0

            episode = clean_text[current_idx:best_split_idx]
            episodes.append(episode)

            self.audit_logger.log(
                "split_episode",
                {
                    "episode_length": len(episode),
                    "score": best_score,
                    "is_fallback": not bool(punctuation_indices)
                }
            )

            current_idx = best_split_idx

        self.audit_logger.log("end_split", {"num_episodes": len(episodes)})

        return {
            "episodes": episodes,
            "audit_logs": self.audit_logger.get_logs()
        }
