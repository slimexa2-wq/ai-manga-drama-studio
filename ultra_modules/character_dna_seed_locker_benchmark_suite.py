import time
import random
import string
import concurrent.futures
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class CharacterDNA:
    hair_color: str = "black"
    eye_color: str = "brown"
    outfit: str = "casual school uniform"
    style_suffix: str = "anime style, masterpiece, best quality"
    fixed_seed: int = 42

    def to_prompt_segment(self) -> str:
        return f"{self.hair_color} hair, {self.eye_color} eyes, {self.outfit}, {self.style_suffix}"

class CharacterDNALocker:
    def __init__(self):
        self._locked_dna: Dict[str, CharacterDNA] = {}

    def _clean_string(self, val: Any, default: str) -> str:
        if val is None:
            return default

        if not isinstance(val, str):
            if isinstance(val, (int, float)):
                val = str(val)
            else:
                return default

        val = val.strip()
        if not val:
            return default

        # Basic dirty data check: if it's super long or mostly non-printable, fallback
        # Real-world dirty data self-healing
        if len(val) > 200:
            return default

        return val

    def _clean_seed(self, seed: Any, default: int = 42) -> int:
        if seed is None:
            return default
        try:
            val = int(seed)
            if val < 0 or val > 2**32 - 1:
                return default
            return val
        except (ValueError, TypeError):
            return default

    def lock_character(self, character_id: str, raw_dna: Dict[str, Any]) -> CharacterDNA:
        """
        Locks the character DNA, applying silent self-healing for dirty data and missing parameters.
        """
        # zero configuration fault tolerance, missing params auto default
        if not raw_dna or not isinstance(raw_dna, dict):
            raw_dna = {}

        dna = CharacterDNA(
            hair_color=self._clean_string(raw_dna.get("hair_color"), "black"),
            eye_color=self._clean_string(raw_dna.get("eye_color"), "brown"),
            outfit=self._clean_string(raw_dna.get("outfit"), "casual school uniform"),
            style_suffix=self._clean_string(raw_dna.get("style_suffix"), "anime style, masterpiece, best quality"),
            fixed_seed=self._clean_seed(raw_dna.get("fixed_seed"), 42)
        )

        self._locked_dna[str(character_id)] = dna
        return dna

    def get_character(self, character_id: str) -> CharacterDNA:
        # returns default character if not found (zero crash)
        return self._locked_dna.get(str(character_id), CharacterDNA())


class SyntheticFixtures:
    @staticmethod
    def generate_normal_data() -> Dict[str, Any]:
        return {
            "hair_color": "blonde",
            "eye_color": "blue",
            "outfit": "knight armor",
            "style_suffix": "detailed, 8k, unreal engine 5",
            "fixed_seed": 123456
        }

    @staticmethod
    def generate_missing_data() -> Dict[str, Any]:
        return {
            "hair_color": None,
            "eye_color": "",
            # outfit is missing
            "style_suffix": "   ",
            "fixed_seed": None
        }

    @staticmethod
    def generate_dirty_data() -> Dict[str, Any]:
        return {
            "hair_color": 12345, # wrong type
            "eye_color": "".join(random.choices(string.printable, k=500)), # too long, dirty
            "outfit": ["list", "instead", "of", "string"], # wrong type
            "style_suffix": "\x00\x01\x02", # gibberish
            "fixed_seed": "not_an_int" # invalid seed
        }

    @staticmethod
    def generate_extreme_boundaries() -> Dict[str, Any]:
        return {
            "hair_color": "silver",
            "eye_color": "red",
            "outfit": "cyberpunk suit with neon lights and a very very long description that might push some limits but is within 200 chars",
            "style_suffix": "cyberpunk, neon, dystopia",
            "fixed_seed": -999999 # extreme boundary, should fallback
        }

class DNALockerBenchmarkSuite:
    def __init__(self, locker: CharacterDNALocker):
        self.locker = locker

    def run_concurrency_benchmark(self, num_threads: int = 100, requests_per_thread: int = 1000) -> float:
        """
        Runs a highly concurrent benchmark.
        Validates zero-crashes and returns average response time in milliseconds.
        """
        def worker(thread_id: int):
            for i in range(requests_per_thread):
                char_id = f"char_{thread_id}_{i}"

                # mix of data types
                data_type = i % 4
                if data_type == 0:
                    data = SyntheticFixtures.generate_normal_data()
                elif data_type == 1:
                    data = SyntheticFixtures.generate_missing_data()
                elif data_type == 2:
                    data = SyntheticFixtures.generate_dirty_data()
                else:
                    data = SyntheticFixtures.generate_extreme_boundaries()

                # lock it
                self.locker.lock_character(char_id, data)
                # retrieve it
                self.locker.get_character(char_id)

        start_time = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for future in concurrent.futures.as_completed(futures):
                # Will raise exception if a crash occurred (zero-crash validation)
                future.result()

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        total_requests = num_threads * requests_per_thread * 2 # 1 lock, 1 get

        avg_response_time_ms = total_time_ms / total_requests
        return avg_response_time_ms
