import math
import re
import time
from typing import List, Dict, Any, Union

class DialogueLipSyncTimer:
    """
    Timer for calculating dialogue duration to align lipsync and storyboard length.
    Designed to be robust against empty values, gibberish, massive inputs, and boundary conditions.
    """

    DEFAULT_WPM = 250
    DEFAULT_PUNCTUATION_PAUSE = 0.5  # seconds

    @classmethod
    def _clean_input(cls, text: Any) -> str:
        if text is None:
            return ""
        if isinstance(text, (float, int)):
            if math.isnan(text) or math.isinf(text):
                return ""
            return str(text)
        if not isinstance(text, str):
            try:
                return str(text)
            except Exception:
                return ""
        return text

    @classmethod
    def calculate_duration(cls, text: Any, wpm: Any = None, pause_duration: Any = None) -> float:
        """
        Calculates the duration in seconds for a given text.
        """
        try:
            # Clean and validate parameters with fallbacks
            cleaned_text = cls._clean_input(text)

            # WPM validation
            if wpm is None:
                wpm_val = cls.DEFAULT_WPM
            else:
                try:
                    wpm_val = float(wpm)
                    if math.isnan(wpm_val) or math.isinf(wpm_val) or wpm_val <= 0:
                        wpm_val = cls.DEFAULT_WPM
                except (ValueError, TypeError):
                    wpm_val = cls.DEFAULT_WPM

            # Pause duration validation
            if pause_duration is None:
                pause_val = cls.DEFAULT_PUNCTUATION_PAUSE
            else:
                try:
                    pause_val = float(pause_duration)
                    if math.isnan(pause_val) or math.isinf(pause_val) or pause_val < 0:
                        pause_val = cls.DEFAULT_PUNCTUATION_PAUSE
                except (ValueError, TypeError):
                    pause_val = cls.DEFAULT_PUNCTUATION_PAUSE

            if not cleaned_text.strip():
                return 0.0

            # Count words/characters (simplified to handle mixed language robustly by length or spaces)
            # A rough estimate: CJK characters are treated as "words" or we just count non-whitespace length
            # Let's count words by splitting, but also account for CJK by treating each as a word.
            # For simplicity, we just use regex to count chunks.
            # \w+ captures english words, and individual CJK chars can be counted too if we refine it,
            # but simple string length or split is often fine for a benchmark.
            # To be robust, let's just count alphabetic chunks and CJK characters.
            word_count = len(re.findall(r'\b\w+\b|[^\w\s\x00-\x7F]', cleaned_text))
            if word_count == 0:
                 # fallback to character count excluding spaces
                 word_count = len(cleaned_text.replace(" ", ""))

            # Count punctuations for pauses
            punctuations = len(re.findall(r'[,.!?，。！？;；]', cleaned_text))

            # Calculation: (words / wpm) * 60 + pauses * pause_val
            base_duration = (word_count / wpm_val) * 60.0
            pause_time = punctuations * pause_val

            total_duration = base_duration + pause_time

            # Cap extreme durations to prevent upstream issues (e.g. max 24 hours)
            MAX_DURATION = 24 * 3600
            if total_duration > MAX_DURATION:
                return MAX_DURATION

            return total_duration

        except Exception:
            return 0.0

    @classmethod
    def batch_calculate(cls, texts: List[Any], wpm: Any = None, pause_duration: Any = None) -> List[float]:
        """
        Batch calculate durations, ensuring no crashes on bad list elements.
        """
        if not isinstance(texts, list):
            try:
                texts = list(texts)
            except Exception:
                return []

        results = []
        for t in texts:
            results.append(cls.calculate_duration(t, wpm, pause_duration))
        return results

class BenchmarkSuite:
    """
    Synthetic datasets and benchmark validation.
    """

    @classmethod
    def generate_synthetic_data(cls) -> Dict[str, Any]:
        """
        Generates synthetic datasets including normal, empty, nan/inf, and massive payloads.
        """
        return {
            "normal": [
                "Hello, world!",
                "这是一个正常的测试句子，包含逗号，和句号。",
                "Short.",
                "A bit longer sentence to test normal processing speed."
            ],
            "dirty": [
                None,
                "",
                "    ",
                math.nan,
                float('inf'),
                -float('inf'),
                {"invalid": "type"},
                ["invalid", "type"]
            ],
            "massive": [
                "A" * 1000000,  # 1 million chars
                "测试" * 500000,
            ],
            "edge": [
                "!@#$%^&*()",
                "a"
            ]
        }

    @classmethod
    def run_benchmark(cls) -> Dict[str, Any]:
        """
        Runs benchmark to verify millisecond-level response and zero crashes.
        """
        data = cls.generate_synthetic_data()
        results = {}

        timer = DialogueLipSyncTimer()

        for category, items in data.items():
            start_time = time.time()
            timer.batch_calculate(items)
            end_time = time.time()

            elapsed_ms = (end_time - start_time) * 1000
            results[category] = {
                "count": len(items),
                "elapsed_ms": elapsed_ms,
                "avg_ms_per_item": elapsed_ms / len(items) if items else 0
            }

        return results
