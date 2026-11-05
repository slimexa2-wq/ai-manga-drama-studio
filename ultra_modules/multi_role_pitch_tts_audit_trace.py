import math
from typing import Dict, Any, List

class MultiRoleTTSModulator:
    """
    Multi-Role Pitch and TTS Audit Trace Engine
    """
    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []

    def _log_audit(self, action: str, details: Dict[str, Any]) -> None:
        """Silently record steps for backend audit."""
        self.audit_log.append({
            "action": action,
            "details": details
        })

    def _sanitize_string(self, text: Any, default: str = "") -> str:
        """Clean string and deduplicate spaces."""
        if not isinstance(text, str):
            self._log_audit("sanitize_string_type_fix", {"original_type": type(text).__name__ if text is not None else "NoneType"})
            if text is None:
                text = default
            else:
                text = str(text)

        cleaned = " ".join(text.split())
        if cleaned != text:
            self._log_audit("sanitize_string_space_dedup", {"original_len": len(text), "cleaned_len": len(cleaned)})
        return cleaned

    def _sanitize_float(self, value: Any, default: float, min_val: float, max_val: float) -> float:
        """Clean float, handle missing, and clamp to boundaries."""
        if value is None:
            self._log_audit("sanitize_float_default", {"default_applied": default})
            return default
        try:
            val = float(value)
            if math.isnan(val) or math.isinf(val):
                raise ValueError
        except (ValueError, TypeError):
            self._log_audit("sanitize_float_invalid", {"value": str(value), "default_applied": default})
            return default

        if val < min_val:
            self._log_audit("sanitize_float_clamp_min", {"original": val, "clamped": min_val})
            return min_val
        if val > max_val:
            self._log_audit("sanitize_float_clamp_max", {"original": val, "clamped": max_val})
            return max_val
        return val

    def modulate(self, role: Any = None, emotion: Any = None, text: Any = None, target_duration_ms: Any = None) -> Dict[str, Any]:
        """
        Dynamically adjust pitch and speed.
        Returns minimal frontend output.
        """
        # Step 1: Sanitize Inputs
        role_clean = self._sanitize_string(role, default="narrator").lower()
        emotion_clean = self._sanitize_string(emotion, default="neutral").lower()
        text_clean = self._sanitize_string(text, default="")

        valid_roles = ["narrator", "male_lead", "female_lead", "villain"]
        if role_clean not in valid_roles:
            self._log_audit("unknown_role_fallback", {"original_role": role_clean, "fallback": "narrator"})
            role_clean = "narrator"

        # Step 2: Pitch and Speed Base Calculation
        pitch = 0.0
        base_speed = 1.0

        if role_clean == "narrator":
            pitch = 0.0
            base_speed = 1.0
        elif role_clean == "male_lead":
            pitch = -2.0
            base_speed = 1.1
        elif role_clean == "female_lead":
            pitch = 2.0
            base_speed = 1.05
        elif role_clean == "villain":
            pitch = -4.0
            base_speed = 0.95

        # Step 3: Emotion Modulation
        if emotion_clean == "angry":
            pitch -= 1.0
            base_speed *= 1.2
        elif emotion_clean == "sad":
            pitch -= 1.5
            base_speed *= 0.8
        elif emotion_clean == "happy":
            pitch += 1.5
            base_speed *= 1.15
        elif emotion_clean == "excited":
            pitch += 2.0
            base_speed *= 1.25
        else:
            if emotion_clean != "neutral":
                self._log_audit("unknown_emotion_fallback", {"original_emotion": emotion_clean, "fallback": "neutral"})
                emotion_clean = "neutral"

        final_speed = base_speed

        # Step 4: Millisecond duration alignment
        # Base speech rate approx: 250ms per character
        target_dur = self._sanitize_float(target_duration_ms, default=0.0, min_val=0.0, max_val=3600000.0)
        if target_dur > 0 and len(text_clean) > 0:
            base_estimated_duration_ms = len(text_clean) * 250.0
            calculated_speed = base_estimated_duration_ms / target_dur

            final_speed = self._sanitize_float(calculated_speed, default=base_speed, min_val=0.5, max_val=2.0)
            self._log_audit("duration_alignment", {
                "target_ms": target_dur,
                "base_est_ms": base_estimated_duration_ms,
                "calc_speed": calculated_speed,
                "final_speed": final_speed
            })
        elif target_duration_ms is not None:
            self._log_audit("duration_alignment_skip", {"reason": "zero_duration_or_empty_text"})

        # Step 5: Final Sanitize & Clamp
        pitch = self._sanitize_float(pitch, default=0.0, min_val=-10.0, max_val=10.0)
        final_speed = self._sanitize_float(final_speed, default=1.0, min_val=0.5, max_val=2.0)

        self._log_audit("modulate_success", {"role": role_clean, "emotion": emotion_clean})

        # Frontend Output
        return {
            "role": role_clean,
            "emotion": emotion_clean,
            "text": text_clean,
            "pitch": round(pitch, 2),
            "speed": round(final_speed, 2)
        }

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Retrieve backend audit logs."""
        return self.audit_log

    def clear_audit_trail(self) -> None:
        """Clear the audit log."""
        self.audit_log = []
