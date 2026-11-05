import time
from typing import Dict, List, Any, Optional

class CharacterDNALocker:
    """
    A unified class to lock character visual DNA, handle self-healing, defaults, and trace audit logs.
    """
    def __init__(self):
        # Store current DNA state: {char_id: {hair, eyes, clothing, style_suffix, seed}}
        self._dna_store: Dict[str, Dict[str, Any]] = {}
        # Store audit logs: {char_id: [{timestamp, operation, diff, new_state}]}
        self._audit_logs: Dict[str, List[Dict[str, Any]]] = {}

    def _get_default_dna(self) -> Dict[str, Any]:
        return {
            "hair": "black short hair",
            "eyes": "dark eyes",
            "clothing": "casual modern clothing",
            "style_suffix": "masterpiece, best quality",
            "seed": 42
        }

    def _clean_and_heal(self, dna_data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = self._get_default_dna()
        if not isinstance(dna_data, dict):
            return cleaned

        for key in ["hair", "eyes", "clothing", "style_suffix"]:
            val = dna_data.get(key)
            if val is not None:
                if not isinstance(val, str):
                    val = str(val)
                val = val.strip()
                if val:
                    cleaned[key] = val

        seed_val = dna_data.get("seed")
        if seed_val is not None:
            try:
                seed_int = int(seed_val)
                if 0 <= seed_int <= 4294967295:  # Standard 32-bit uint bounds for stable diffusion seeds
                    cleaned["seed"] = seed_int
            except (ValueError, TypeError):
                pass

        return cleaned

    def _compute_diff(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        diff = {}
        for k, v in new_state.items():
            if old_state.get(k) != v:
                diff[k] = {"from": old_state.get(k), "to": v}
        return diff

    def _record_audit(self, char_id: str, operation: str, diff: Optional[Dict[str, Any]] = None, state: Optional[Dict[str, Any]] = None):
        if char_id not in self._audit_logs:
            self._audit_logs[char_id] = []
        self._audit_logs[char_id].append({
            "timestamp": time.time(),
            "operation": operation,
            "diff": diff or {},
            "state": dict(state) if state else {}
        })

    def lock_dna(self, char_id: str, **kwargs) -> Dict[str, Any]:
        """
        Locks the DNA for a given character. Performs self-healing, assigns defaults for missing parameters,
        and logs the operation silently.
        """
        if char_id is None:
            char_id = "UNKNOWN_CHAR"
        elif not isinstance(char_id, str):
            char_id = str(char_id)

        char_id = char_id.strip() or "UNKNOWN_CHAR"

        new_state = self._clean_and_heal(kwargs)

        if char_id not in self._dna_store:
            self._dna_store[char_id] = new_state
            self._record_audit(char_id, "INIT", diff={}, state=new_state)
            return new_state

        old_state = self._dna_store[char_id]
        diff = self._compute_diff(old_state, new_state)

        if not diff:
            # Deduplicate - no change
            self._record_audit(char_id, "DEDUPLICATE", diff={}, state=new_state)
        else:
            self._dna_store[char_id] = new_state
            self._record_audit(char_id, "UPDATE", diff=diff, state=new_state)

        return new_state

    def get_dna(self, char_id: str) -> Dict[str, Any]:
        """
        Retrieves the DNA for a character. If not found, returns fallback DNA.
        """
        if char_id is None:
            char_id = "UNKNOWN_CHAR"
        elif not isinstance(char_id, str):
            char_id = str(char_id)

        char_id = char_id.strip() or "UNKNOWN_CHAR"

        if char_id in self._dna_store:
            return dict(self._dna_store[char_id])

        # Missing parameter fallback (Auto-fallback)
        fallback_state = self._get_default_dna()
        self._record_audit(char_id, "AUTO_FALLBACK", diff={}, state=fallback_state)
        return fallback_state

    def get_audit_trace(self, char_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the traceable audit logs for a character.
        """
        if char_id is None:
            char_id = "UNKNOWN_CHAR"
        elif not isinstance(char_id, str):
            char_id = str(char_id)

        char_id = char_id.strip() or "UNKNOWN_CHAR"
        return self._audit_logs.get(char_id, [])

    def generate_prompt_snippet(self, char_id: str) -> str:
        """
        Generates a clean prompt snippet based on the locked DNA.
        """
        dna = self.get_dna(char_id)
        components = []
        if dna.get("hair"):
            components.append(dna["hair"])
        if dna.get("eyes"):
            components.append(dna["eyes"])
        if dna.get("clothing"):
            components.append(dna["clothing"])
        if dna.get("style_suffix"):
            components.append(dna["style_suffix"])

        return ", ".join(components)
