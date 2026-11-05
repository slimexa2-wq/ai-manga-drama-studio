import re
from typing import Dict, List, Optional, Any, Union

class DialogueTimerAuditTrace:
    """
    Dialogue duration calculator based on word count, punctuation pause, and audio peaks alignment.
    Provides backend full-chain audit logging and difference highlight comparator.
    Frontend only needs to use the clean_result.
    """
    def __init__(self, base_cps: Any = 5.0, default_pause: Any = 0.5, punctuation_pauses: Any = None):
        # Zero-configuration fault tolerance: self-healing base_cps
        try:
            self.base_cps = float(base_cps)
            if self.base_cps <= 0:
                self.base_cps = 5.0
        except (ValueError, TypeError):
            self.base_cps = 5.0

        # Zero-configuration fault tolerance: self-healing default_pause
        try:
            self.default_pause = float(default_pause)
            if self.default_pause < 0:
                self.default_pause = 0.5
        except (ValueError, TypeError):
            self.default_pause = 0.5

        # Default punctuation pauses
        self.punctuation_pauses = {
            ',': 0.3, '，': 0.3,
            '.': 0.6, '。': 0.6,
            '?': 0.6, '？': 0.6,
            '!': 0.6, '！': 0.6,
            ';': 0.4, '；': 0.4,
            ':': 0.4, '：': 0.4,
            '…': 1.0, '...': 1.0
        }

        # Self-healing custom punctuation pauses
        if isinstance(punctuation_pauses, dict):
            for k, v in punctuation_pauses.items():
                try:
                    val = float(v)
                    if val >= 0:
                        self.punctuation_pauses[str(k)] = val
                except (ValueError, TypeError):
                    pass

    def calculate_duration(self, text: Any, audio_duration: Any = None, audio_peaks: Any = None) -> Dict[str, Any]:
        """
        Calculates the expected duration and aligns it with provided audio metrics.
        Returns a dictionary containing clean_result for frontend and audit_trace for backend.
        """
        audit_trace = []

        # 1. Text sanitization & Dirty data self-healing
        original_text = text
        if not isinstance(text, str):
            audit_trace.append(f"Auto-healed invalid text type '{type(text).__name__}' to string or empty.")
            if text is None:
                text = ""
            else:
                try:
                    text = str(text)
                except Exception:
                    text = ""

        clean_text = re.sub(r'\s+', ' ', text).strip()
        if str(original_text) != clean_text:
            audit_trace.append("Cleaned extra spaces/newlines from text.")

        # 2. Duration calculation
        valid_char_count = 0
        punctuation_pause_total = 0.0

        # Treat '...' as a single token for simplicity
        temp_text = clean_text.replace('...', '…')

        for c in temp_text:
            if c in self.punctuation_pauses:
                punctuation_pause_total += self.punctuation_pauses[c]
            elif c.isspace():
                continue
            else:
                valid_char_count += 1

        base_duration = valid_char_count / self.base_cps
        text_based_duration = base_duration + punctuation_pause_total

        audit_trace.append(f"Calculated text-based duration: {text_based_duration:.3f}s (Base: {base_duration:.3f}s for {valid_char_count} chars at {self.base_cps} cps, Punctuation: {punctuation_pause_total:.3f}s)")

        # 3. Audio processing & Validation
        valid_peaks = []
        if audio_peaks is not None:
            if isinstance(audio_peaks, list):
                for p in audio_peaks:
                    try:
                        peak_val = float(p)
                        if peak_val >= 0:
                            valid_peaks.append(peak_val)
                    except (ValueError, TypeError):
                        pass
                if valid_peaks:
                    audit_trace.append(f"Extracted {len(valid_peaks)} valid audio peaks. Max peak at: {max(valid_peaks):.3f}s")
                else:
                    audit_trace.append("No valid audio peaks found in provided list. Ignored.")
            else:
                audit_trace.append(f"Auto-healed invalid audio_peaks type '{type(audio_peaks).__name__}'. Ignored.")

        max_peak = max(valid_peaks) if valid_peaks else 0.0

        valid_audio_duration = None
        if audio_duration is not None:
            try:
                ad = float(audio_duration)
                if ad >= 0:
                    valid_audio_duration = ad
                    audit_trace.append(f"Parsed valid audio_duration: {valid_audio_duration:.3f}s")
                else:
                    audit_trace.append("Negative audio_duration ignored.")
            except (ValueError, TypeError):
                audit_trace.append(f"Auto-healed invalid audio_duration '{audio_duration}'. Ignored.")

        # 4. Alignment & Diff Highlight
        audio_based_duration = max_peak
        if valid_audio_duration is not None:
            audio_based_duration = max(audio_based_duration, valid_audio_duration)

        final_duration = text_based_duration
        action = "used_text_duration"

        if audio_based_duration > 0:
            if audio_based_duration > text_based_duration:
                final_duration = audio_based_duration
                action = "aligned_to_audio_expansion"
                audit_trace.append(f"Expanded final duration to match audio constraints: {final_duration:.3f}s (Text was {text_based_duration:.3f}s)")
            elif valid_audio_duration is not None and valid_audio_duration < text_based_duration:
                # If explicit audio duration is strictly less than text expected duration, cap it to sync with audio.
                final_duration = valid_audio_duration
                action = "truncated_to_audio_duration"
                audit_trace.append(f"Truncated final duration to strictly match provided audio_duration: {final_duration:.3f}s (Text was {text_based_duration:.3f}s)")

        final_duration = round(final_duration, 3)
        text_based_duration = round(text_based_duration, 3)
        audio_based_duration = round(audio_based_duration, 3)
        diff_val = round(final_duration - text_based_duration, 3)

        audit_trace.append(f"Final calculated duration resolved to: {final_duration}s. Action taken: {action}")

        return {
            "clean_result": {
                "duration": final_duration
            },
            "audit_trace": audit_trace,
            "diff_highlight": {
                "text_based_duration": text_based_duration,
                "audio_based_duration": audio_based_duration,
                "diff": diff_val,
                "action": action
            }
        }
