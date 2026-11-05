import hashlib
import json
from typing import Any, Dict, Optional

class CharacterDNALockerCoreEngine:
    """
    Core engine for locking character visual DNA across episodes.
    Pure functions, zero-configuration automatic fallback, dirty data silent cleaning.
    """

    @staticmethod
    def _clean_string(value: Any, default: str) -> str:
        if value is None:
            return default
        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception:
                return default
        value = value.strip()
        return value if value else default

    @staticmethod
    def _clean_seed(value: Any, default: int) -> int:
        if value is None:
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                # Try to parse string as float then int, or just int
                return int(float(value.strip()))
            except (ValueError, TypeError):
                return default
        if isinstance(value, float):
            return int(value)
        return default

    @staticmethod
    def _generate_deterministic_seed(character_id: str, episode_id: str, base_seed: int) -> int:
        """
        Generates a deterministic seed based on character ID, episode ID, and base seed.
        Ensures the same character in the same episode gets the same seed, but seeds
        have pseudo-random variation across different characters/episodes.
        """
        seed_str = f"{character_id}_{episode_id}_{base_seed}"
        hash_obj = hashlib.sha256(seed_str.encode('utf-8'))
        # Use first 8 bytes of hash for seed
        hex_digest = hash_obj.hexdigest()[:16]
        # Modulo to keep it within standard 32-bit integer range typically used in generation
        return int(hex_digest, 16) % (2**31 - 1)

    @classmethod
    def lock_dna(cls,
                 character_id: Any,
                 episode_id: Any,
                 dna_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Locks the character's visual DNA for a specific episode.

        Args:
            character_id: Unique identifier for the character.
            episode_id: Identifier for the episode.
            dna_params: Dictionary of DNA parameters (hair_color, eye_color, clothing, style_suffix, base_seed).

        Returns:
            A cleaned and locked dictionary of DNA parameters.
        """
        # 1. Clean IDs
        char_id_clean = cls._clean_string(character_id, default="unknown_character")
        ep_id_clean = cls._clean_string(episode_id, default="unknown_episode")

        # 2. Parse and clean parameters with fallbacks
        params = dna_params if isinstance(dna_params, dict) else {}

        hair_color = cls._clean_string(params.get("hair_color"), default="black")
        eye_color = cls._clean_string(params.get("eye_color"), default="brown")
        clothing = cls._clean_string(params.get("clothing"), default="casual wear")
        style_suffix = cls._clean_string(params.get("style_suffix"), default="anime style, masterpiece, best quality")

        # Base seed default could be 42
        base_seed = cls._clean_seed(params.get("base_seed"), default=42)

        # 3. Generate locked seed
        locked_seed = cls._generate_deterministic_seed(char_id_clean, ep_id_clean, base_seed)

        # 4. Construct the locked DNA payload
        locked_dna = {
            "character_id": char_id_clean,
            "episode_id": ep_id_clean,
            "hair_color": hair_color,
            "eye_color": eye_color,
            "clothing": clothing,
            "style_suffix": style_suffix,
            "base_seed": base_seed,
            "locked_seed": locked_seed
        }

        return locked_dna
