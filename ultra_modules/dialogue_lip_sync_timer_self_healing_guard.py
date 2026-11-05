import copy
import logging

logger = logging.getLogger(__name__)

class DialogueLipSyncTimerSelfHealingGuard:
    def __init__(self):
        self._snapshot_history = []
        self._current_state = {
            "last_calculated_duration": 0.0,
            "calculation_count": 0
        }

    def _save_snapshot(self):
        """Save a lightweight snapshot of the current state."""
        self._snapshot_history.append(copy.deepcopy(self._current_state))
        # Keep only the last 10 snapshots to stay lightweight
        if len(self._snapshot_history) > 10:
            self._snapshot_history.pop(0)

    def undo(self):
        """Revert to the previous snapshot in one click."""
        if self._snapshot_history:
            # Restore the previous state
            self._current_state = self._snapshot_history.pop()
            return True
        return False

    @property
    def last_calculated_duration(self):
        return self._current_state["last_calculated_duration"]

    @property
    def calculation_count(self):
        return self._current_state["calculation_count"]

    def calculate_duration(self, text=None, audio_peaks=None, options=None):
        """
        Calculate storyboard duration based on dialogue length, audio peaks, and punctuation.
        Includes dirty data healing and bounds checking.
        """
        self._save_snapshot()

        # 1. Self-healing & Fallbacks for inputs
        if text is None:
            text = ""
        elif not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                text = ""

        if audio_peaks is None:
            audio_peaks = []
        elif not isinstance(audio_peaks, list):
            # Try to convert if it's a single number or something else
            try:
                if isinstance(audio_peaks, (int, float)):
                    audio_peaks = [float(audio_peaks)]
                else:
                    audio_peaks = list(audio_peaks)
                    # Clean the list items
                    audio_peaks = [float(p) for p in audio_peaks if isinstance(p, (int, float, str))]
            except Exception:
                audio_peaks = []

        if options is None:
            options = {}
        elif not isinstance(options, dict):
            options = {}

        # Default options
        base_chars_per_second = options.get("chars_per_second", 5.0)
        if not isinstance(base_chars_per_second, (int, float)) or base_chars_per_second <= 0:
            base_chars_per_second = 5.0

        punctuation_pause = options.get("punctuation_pause", 0.5)
        if not isinstance(punctuation_pause, (int, float)) or punctuation_pause < 0:
            punctuation_pause = 0.5

        min_duration = options.get("min_duration", 1.0)
        if not isinstance(min_duration, (int, float)):
            min_duration = 1.0

        max_duration = options.get("max_duration", 30.0)
        if not isinstance(max_duration, (int, float)):
            max_duration = 30.0

        if min_duration > max_duration:
            min_duration, max_duration = max_duration, min_duration

        # 2. Calculation
        duration = 0.0

        # Calculate base duration from text length
        char_count = len(text.replace(" ", ""))
        text_duration = char_count / base_chars_per_second

        # Add punctuation pauses
        punctuation_marks = [',', '.', '!', '?', '，', '。', '！', '？', ';', '；']
        pause_count = sum(1 for char in text if char in punctuation_marks)
        punctuation_duration = pause_count * punctuation_pause

        duration += text_duration + punctuation_duration

        # Adjust with audio peaks if available (basic heuristic)
        if audio_peaks:
            # Assume each peak represents a stressed syllable adding 0.2s
            peak_duration = len(audio_peaks) * 0.2
            # Average text duration and peak duration if peak duration is significant
            if peak_duration > duration * 0.5:
                 duration = (duration + peak_duration) / 2

        # 3. Bounds checking
        if duration < min_duration:
            duration = min_duration
        elif duration > max_duration:
            duration = max_duration

        # Update state
        self._current_state["last_calculated_duration"] = duration
        self._current_state["calculation_count"] += 1

        return duration
