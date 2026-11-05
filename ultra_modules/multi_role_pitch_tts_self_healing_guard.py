import time
import copy
import math
from typing import Dict, Any, List, Tuple

def _sanitize_input(data: Any, default_val: float) -> float:
    """Silent self-healing for abnormal inputs."""
    if data is None:
        return default_val
    try:
        val = float(data)
        if math.isinf(val) or math.isnan(val):
            return default_val
        if val <= 0 and default_val > 0:
            return default_val
        return val
    except (ValueError, TypeError):
        return default_val

def _get_role_base_params(role: str) -> Tuple[float, float]:
    """Returns base (pitch, speed) for a given role."""
    roles = {
        "narrator": (0.9, 1.0),
        "hero": (1.0, 1.1),
        "heroine": (1.2, 1.05),
        "villain": (0.8, 0.95),
    }
    return roles.get(str(role).lower(), (1.0, 1.0))

def _get_emotion_modifiers(emotion: str) -> Tuple[float, float]:
    """Returns (pitch_mod, speed_mod) for a given emotion."""
    emotions = {
        "angry": (1.2, 1.2),
        "sad": (0.9, 0.8),
        "happy": (1.1, 1.1),
        "calm": (1.0, 1.0),
    }
    return emotions.get(str(emotion).lower(), (1.0, 1.0))

def modulate_tts_params(
    role: Any,
    emotion: Any,
    base_pitch: Any = None,
    base_speed: Any = None
) -> Dict[str, float]:
    """
    Dynamic pitch and speed modulation for different roles based on emotion.
    Self-heals dirty data silently.
    """
    role_str = str(role) if role is not None else "narrator"
    emotion_str = str(emotion) if emotion is not None else "calm"

    r_pitch, r_speed = _get_role_base_params(role_str)
    e_pitch, e_speed = _get_emotion_modifiers(emotion_str)

    final_base_pitch = _sanitize_input(base_pitch, r_pitch)
    final_base_speed = _sanitize_input(base_speed, r_speed)

    pitch = final_base_pitch * e_pitch
    speed = final_base_speed * e_speed

    return {
        "pitch": round(pitch, 3),
        "speed": round(speed, 3)
    }

def align_duration_ms(
    target_duration_ms: Any,
    current_duration_ms: Any,
) -> Dict[str, float]:
    """
    Millisecond duration alignment.
    Calculates the required speed to match the target duration exactly.
    Silently handles invalid inputs.
    """
    target = _sanitize_input(target_duration_ms, 1000.0)
    current = _sanitize_input(current_duration_ms, 1000.0)

    required_speed = current / target

    return {
        "aligned_speed": round(required_speed, 3),
        "target_duration_ms": target
    }

class TTSStateSnapshot:
    def __init__(self, state: Dict[str, Any]):
        self.state = copy.deepcopy(state)
        self.timestamp = time.time()

class MultiRolePitchTTSGuard:
    """
    Engine for multi-role emotion pitch/speed modulation & duration alignment.
    Implements a 5-second one-click undo (snapshot) mechanism.
    """
    def __init__(self, undo_window_seconds: float = 5.0):
        self.undo_window_seconds = undo_window_seconds
        self.current_state: Dict[str, Any] = {}
        self.snapshots: List[TTSStateSnapshot] = []

    def process_tts_request(
        self,
        role: Any = None,
        emotion: Any = None,
        target_duration_ms: Any = None,
        base_duration_ms: Any = None
    ) -> Dict[str, Any]:
        """
        Process TTS modulation and alignment. Takes a snapshot before changing state.
        Silent self-healing on dirty data to ensure front-end stability.
        """
        self._take_snapshot()

        mod_params = modulate_tts_params(role, emotion)

        aligned_speed = mod_params["speed"]
        final_target_duration = None

        if target_duration_ms is not None or base_duration_ms is not None:
             aligned_params = align_duration_ms(
                 target_duration_ms=target_duration_ms,
                 current_duration_ms=base_duration_ms
             )
             aligned_speed = aligned_params["aligned_speed"]
             final_target_duration = aligned_params["target_duration_ms"]

        self.current_state = {
            "role": str(role) if role is not None else "narrator",
            "emotion": str(emotion) if emotion is not None else "calm",
            "pitch": mod_params["pitch"],
            "speed": aligned_speed,
            "target_duration_ms": final_target_duration
        }

        return copy.deepcopy(self.current_state)

    def _take_snapshot(self) -> None:
        """Takes a lightweight snapshot of the current state."""
        self.snapshots.append(TTSStateSnapshot(self.current_state))
        self._cleanup_snapshots()

    def _cleanup_snapshots(self) -> None:
        """Removes snapshots older than the undo window."""
        now = time.time()
        self.snapshots = [
            snap for snap in self.snapshots
            if now - snap.timestamp <= self.undo_window_seconds
        ]

    def undo(self) -> bool:
        """
        One-click undo to the most recent snapshot within the 5-second window.
        Returns True if successful, False if no valid snapshot is available.
        Silent failure (returns False) instead of raising exceptions.
        """
        self._cleanup_snapshots()
        if not self.snapshots:
            return False

        latest_snapshot = self.snapshots.pop()
        self.current_state = copy.deepcopy(latest_snapshot.state)
        return True

    def get_current_state(self) -> Dict[str, Any]:
        return copy.deepcopy(self.current_state)
