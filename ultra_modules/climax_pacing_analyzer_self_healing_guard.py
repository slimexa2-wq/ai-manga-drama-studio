import time
import copy
from typing import Dict, Any, List, Optional
import hashlib
import json

class ClimaxPacingAnalyzerSelfHealingGuard:
    """
    Analyzes dramatic pacing (Suppression -> Accumulation -> Payoff -> Suspense)
    with self-healing data and 5-second undo snapshots.
    """

    def __init__(self):
        self._snapshots = []
        self._current_state = None
        self._undo_time_limit_sec = 5

    def _heal_data(self, input_data: Any) -> List[Dict[str, Any]]:
        """Silently heal dirty data, setting defaults for missing parameters."""
        healed = []

        # Default empty input to a base pacing structure
        if not input_data or not isinstance(input_data, list):
            input_data = [{"phase": "suppression", "intensity": 50}]

        for item in input_data:
            if not isinstance(item, dict):
                continue

            phase = item.get("phase", "suppression")
            if not isinstance(phase, str):
                phase = "suppression"

            intensity = item.get("intensity", 50)
            try:
                intensity = float(intensity)
            except (ValueError, TypeError):
                intensity = 50.0

            # Cap intensity to bounds
            intensity = max(0.0, min(100.0, intensity))

            duration = item.get("duration_sec", 10.0)
            try:
                duration = float(duration)
            except (ValueError, TypeError):
                duration = 10.0
            duration = max(1.0, duration) # Minimum 1s

            healed.append({
                "phase": phase,
                "intensity": intensity,
                "duration_sec": duration
            })

        # Ensure at least one valid item
        if not healed:
            healed.append({"phase": "suppression", "intensity": 50.0, "duration_sec": 10.0})

        return healed

    def _diagnose_curve(self, data: List[Dict[str, Any]]) -> str:
        """Analyze the pacing curve and return a diagnosis string."""
        if not data:
            return "Flat"

        intensities = [item["intensity"] for item in data]
        if max(intensities) - min(intensities) < 10:
            return "Needs more dynamic range"

        # Simple detection of climax
        if any(item["intensity"] > 80 for item in data):
            return "Good climax detected"

        return "Steady buildup"

    def _encrypt_pacing(self, data: List[Dict[str, Any]]) -> str:
        """Encrypt the pacing layout into a signature hash for tracking."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def analyze(self, input_data: Any) -> Dict[str, Any]:
        """
        Main entry point for analysis. Heals input, diagnoses, encrypts, and snapshots.
        """
        # Save snapshot of previous state if it exists
        if self._current_state is not None:
            self._snapshots.append({
                "state": copy.deepcopy(self._current_state),
                "timestamp": time.time()
            })

            # Keep only recent snapshots to save memory
            self._snapshots = self._snapshots[-10:]

        healed_data = self._heal_data(input_data)
        diagnosis = self._diagnose_curve(healed_data)
        encryption_hash = self._encrypt_pacing(healed_data)

        self._current_state = {
            "healed_pacing": healed_data,
            "diagnosis": diagnosis,
            "signature": encryption_hash,
            "timestamp": time.time()
        }

        return copy.deepcopy(self._current_state)

    def undo(self) -> Optional[Dict[str, Any]]:
        """
        One-click undo to revert to the previous state, only if within 5 seconds.
        """
        if not self._snapshots:
            return self._current_state

        last_snapshot = self._snapshots.pop()
        time_elapsed = time.time() - last_snapshot["timestamp"]

        if time_elapsed <= self._undo_time_limit_sec:
            self._current_state = copy.deepcopy(last_snapshot["state"])
            return copy.deepcopy(self._current_state)
        else:
            # If expired, discard and return current
            # Put it back since we couldn't undo
            # Actually, per requirements, it should fail silently but not undo if > 5s
            # Or just ignore
            return self._current_state

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        return copy.deepcopy(self._current_state)
