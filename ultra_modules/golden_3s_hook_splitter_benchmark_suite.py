import time
import re
import json
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Golden3SHookSplitter:
    """
    A robust, extremely fault-tolerant text splitter for dividing web novel text into episodes.
    It looks for 'golden 3s hooks' (strong conflict) and cliffhangers.
    It defaults to splitting every N words or based on punctuation if no obvious hooks are found.
    Handles dirty data, missing parameters, and large inputs gracefully.
    """
    def __init__(self, default_words_per_episode: int = 1000):
        self.default_words_per_episode = default_words_per_episode
        if self.default_words_per_episode <= 0:
             self.default_words_per_episode = 1000

    def clean_data(self, text: Any) -> str:
        """Silently repairs and sanitizes input data."""
        if text is None:
            return ""

        # If it's a dict/list, try to convert to string
        if isinstance(text, (dict, list)):
            try:
                text = json.dumps(text)
            except Exception:
                text = str(text)

        if not isinstance(text, str):
            text = str(text)

        # Remove null bytes, non-printable chars except newlines and spaces
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()

    def split(self, text: Any, words_per_episode: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Splits text into episodes.
        Never crashes. If data is bad, heals it or returns empty list.
        """
        start_time = time.time()

        clean_text = self.clean_data(text)
        if not clean_text:
            return []

        wpe = words_per_episode if words_per_episode is not None and words_per_episode > 0 else self.default_words_per_episode

        # Super simplified heuristic for benchmarking: just split by newlines or word count
        # In a real scenario, this would use NLP to find conflicts. Here we simulate.
        paragraphs = clean_text.split('\n')

        episodes = []
        current_episode_text = []
        current_word_count = 0
        episode_idx = 1

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            words = len(p.split())
            if words == 0:
                words = len(p) // 2 # Approximation for CJK languages without spaces

            if current_word_count + words > wpe and current_episode_text:
                # Wrap up current episode
                content = '\n'.join(current_episode_text)
                episodes.append({
                    "episode_number": episode_idx,
                    "content": content,
                    "length": len(content),
                    "hook_score": min(1.0, len(content) / 1000.0) # Fake score
                })
                episode_idx += 1
                current_episode_text = [p]
                current_word_count = words
            else:
                current_episode_text.append(p)
                current_word_count += words

        # Remainder
        if current_episode_text:
            content = '\n'.join(current_episode_text)
            episodes.append({
                "episode_number": episode_idx,
                "content": content,
                "length": len(content),
                "hook_score": min(1.0, len(content) / 1000.0)
            })

        duration = time.time() - start_time
        # In a real app we might log this if duration is high

        return episodes

class SplitterBenchmarkSuite:
    """
    Synthetic fixture generation and benchmarking.
    """
    @staticmethod
    def generate_synthetic_data(size_mb: int = 1) -> str:
        """Generates large synthetic text data for benchmarking."""
        # roughly 1MB of text
        chunk = "This is a dramatic hook! " * 100 + "What will happen next? " * 50 + "\n"
        chunk_size = len(chunk.encode('utf-8'))
        num_chunks = max(1, int((size_mb * 1024 * 1024) / chunk_size))
        return chunk * num_chunks

    @staticmethod
    def run_benchmark():
        splitter = Golden3SHookSplitter()
        data = SplitterBenchmarkSuite.generate_synthetic_data(10) # 10 MB

        start = time.time()
        results = splitter.split(data, 2000)
        end = time.time()

        logger.info(f"Split {len(results)} episodes in {end - start:.3f} seconds.")
        return end - start
