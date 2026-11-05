import logging
import json
import time
from typing import Dict, Any, List, Optional
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiRoleTTSAlignmentEngine:
    """
    旁白/男主/女主/反派多角色情感音高语速动态调制与毫秒级时长对齐引擎
    Multi-role emotion, pitch, and speed dynamic modulation & millisecond duration alignment engine.
    """

    DEFAULT_ROLE_CONFIG = {
        'narrator': {'pitch': 0, 'speed': 1.0, 'emotion': 'neutral', 'voice': 'zh-CN-XiaoxiaoNeural'},
        'male_lead': {'pitch': -2, 'speed': 1.1, 'emotion': 'calm', 'voice': 'zh-CN-YunxiNeural'},
        'female_lead': {'pitch': 2, 'speed': 1.1, 'emotion': 'cheerful', 'voice': 'zh-CN-XiaoyiNeural'},
        'villain': {'pitch': -5, 'speed': 0.9, 'emotion': 'angry', 'voice': 'zh-CN-YunjianNeural'},
    }

    def __init__(self):
        # Initialize default configurations
        self.role_config = self.DEFAULT_ROLE_CONFIG.copy()

    def _sanitize_text(self, text: Any) -> str:
        """Sanitizes text, ensuring string format and handling mojibake/None."""
        if text is None:
            return ""
        if isinstance(text, list):
            # Try to convert list to string
            return "".join([str(t) for t in text])
        if not isinstance(text, str):
            return str(text)

        # Simple cleanup
        text = text.strip()
        # Assume valid UTF-8 encoding handling in python string
        return text

    def generate_tts_config(self, role: str, text: Any, custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generates TTS configuration for a given role, applying fault tolerance and defaults.
        """
        text = self._sanitize_text(text)
        if not text:
            # Fallback for empty text
            text = "..."

        # Auto-fallback for role
        if role not in self.role_config:
            logger.warning(f"Role '{role}' not found. Falling back to narrator.")
            role = 'narrator'

        config = self.role_config[role].copy()

        # Apply custom params if provided, with type checking and sanitization
        if custom_params:
            if not isinstance(custom_params, dict):
                logger.error("custom_params must be a dictionary. Ignoring.")
            else:
                for key in ['pitch', 'speed', 'emotion', 'voice']:
                    if key in custom_params and custom_params[key] is not None:
                        try:
                            if key in ['pitch', 'speed']:
                                config[key] = float(custom_params[key])
                            else:
                                config[key] = str(custom_params[key])
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid value for {key} in custom_params. Using default.")

        # Simulate millisecond alignment constraint based on text length and speed
        # Assume average 5 chars per second at speed 1.0
        base_duration_ms = max(len(text) * 200, 500) # At least 500ms
        aligned_duration_ms = int(base_duration_ms / max(config['speed'], 0.1))

        return {
            'role': role,
            'text': text,
            'pitch': config['pitch'],
            'speed': config['speed'],
            'emotion': config['emotion'],
            'voice': config['voice'],
            'duration_ms': aligned_duration_ms,
            'timestamp': datetime.datetime.now().isoformat()
        }

    def align_duration(self, configs: List[Dict[str, Any]], target_duration_ms: int) -> List[Dict[str, Any]]:
        """
        Adjusts speeds to fit multiple TTS configurations into a target duration.
        """
        if not configs:
            return []

        total_current_ms = sum(c['duration_ms'] for c in configs)
        if total_current_ms == 0:
            return configs

        ratio = target_duration_ms / total_current_ms

        for config in configs:
            config['duration_ms'] = int(config['duration_ms'] * ratio)
            # Adjust speed inversely proportional to duration change
            config['speed'] = round(config['speed'] / ratio, 2)

        return configs

    def benchmark_synthesis(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesizes a large dataset and measures performance metrics.
        Used for extreme edge case and concurrency simulation.
        """
        start_time = time.time()
        results = []
        errors = 0

        for item in dataset:
            try:
                role = item.get('role')
                text = item.get('text')
                custom = item.get('custom_params')

                res = self.generate_tts_config(role, text, custom)
                results.append(res)
            except Exception as e:
                logger.error(f"Error synthesizing item {item}: {e}")
                errors += 1

        end_time = time.time()

        return {
            'total_processed': len(dataset),
            'success_count': len(results),
            'error_count': errors,
            'time_taken_ms': int((end_time - start_time) * 1000),
            'results': results
        }
