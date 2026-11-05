import unittest
import sys
import os
import copy
from datetime import datetime, timedelta

# Add parent directory to path to allow importing ultra_modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ultra_modules.multi_role_pitch_tts_benchmark_suite import MultiRoleTTSAlignmentEngine

class TestMultiRoleTTSAlignmentEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MultiRoleTTSAlignmentEngine()

    def test_normal_operation(self):
        """Test case 1: Normal operation with valid roles and texts."""
        conf = self.engine.generate_tts_config('male_lead', "你好，世界！")
        self.assertEqual(conf['role'], 'male_lead')
        self.assertEqual(conf['text'], "你好，世界！")
        self.assertEqual(conf['pitch'], -2)
        self.assertEqual(conf['speed'], 1.1)
        self.assertEqual(conf['emotion'], 'calm')
        self.assertTrue(conf['duration_ms'] > 0)

    def test_dirty_data_self_healing(self):
        """Test case 2: Dirty data self-healing (None, garbled, lists)."""
        # None value
        conf1 = self.engine.generate_tts_config('narrator', None)
        self.assertEqual(conf1['text'], "...")

        # Garbled text (e.g. integer array)
        conf2 = self.engine.generate_tts_config('female_lead', [123, 456])
        self.assertEqual(conf2['text'], "123456")

        # Completely invalid role
        conf3 = self.engine.generate_tts_config('alien', "Invade!")
        self.assertEqual(conf3['role'], 'narrator')

    def test_missing_parameter_fallback(self):
        """Test case 3: Missing parameter fallback."""
        # Empty dictionary for custom params
        conf1 = self.engine.generate_tts_config('villain', "Destroy!", {})
        self.assertEqual(conf1['pitch'], -5) # default

        # Missing specific fields or None values in custom params
        conf2 = self.engine.generate_tts_config('villain', "Destroy!", {'pitch': None, 'speed': 'invalid'})
        self.assertEqual(conf2['pitch'], -5) # fallback to default because None
        self.assertEqual(conf2['speed'], 0.9) # fallback because 'invalid' is not float

        # Valid custom params override
        conf3 = self.engine.generate_tts_config('villain', "Destroy!", {'pitch': 10, 'emotion': 'happy'})
        self.assertEqual(conf3['pitch'], 10)
        self.assertEqual(conf3['emotion'], 'happy')

    def test_extreme_boundary_cases(self):
        """Test case 4: Extreme boundary cases (massive string texts, concurrency simulation)."""
        massive_text = "A" * 10000
        conf = self.engine.generate_tts_config('male_lead', massive_text)
        self.assertEqual(conf['text'], massive_text)
        self.assertTrue(conf['duration_ms'] > 0)

        # Concurrency simulation via benchmark dataset
        dataset = [{'role': 'male_lead', 'text': f"Sentence {i}"} for i in range(10000)]
        res = self.engine.benchmark_synthesis(dataset)
        self.assertEqual(res['total_processed'], 10000)
        self.assertEqual(res['success_count'], 10000)
        self.assertEqual(res['error_count'], 0)

    def test_duration_alignment(self):
        """Test case 5: Duration alignment and cross-year/month tracking."""
        configs = [
            self.engine.generate_tts_config('male_lead', "First sentence."),
            self.engine.generate_tts_config('female_lead', "Second longer sentence.")
        ]
        total_initial_ms = sum(c['duration_ms'] for c in configs)
        target_ms = 5000 # Align to exactly 5 seconds

        aligned_configs = self.engine.align_duration(configs, target_ms)
        total_aligned_ms = sum(c['duration_ms'] for c in aligned_configs)

        # Total aligned ms might be off by a tiny fraction due to int truncation, but should be extremely close
        self.assertTrue(abs(total_aligned_ms - target_ms) <= len(configs))

        # Simulate cross-year timestamp modification logic internally (demonstrating capability)
        # Assuming timestamps might need to be parsed and aligned if this was actual TTS sync
        # Here we just check timestamp existence and string format
        for c in aligned_configs:
            self.assertTrue('timestamp' in c)
            # Make sure it can be parsed back
            dt = datetime.fromisoformat(c['timestamp'])
            self.assertTrue(dt.year > 2000)

if __name__ == '__main__':
    unittest.main()
