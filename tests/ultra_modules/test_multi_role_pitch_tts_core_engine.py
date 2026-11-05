import unittest
import math
from ultra_modules.multi_role_pitch_tts_core_engine import align_and_modulate, ROLE_PRESETS

class TestMultiRolePitchTTSCoreEngine(unittest.TestCase):

    def test_normal_processing(self):
        """Test 1: Normal processing with predefined roles."""
        segment = {
            "text": "Hello world",
            "role": "male_lead"
        }
        res = align_and_modulate(segment)
        self.assertEqual(res["text"], "Hello world")
        self.assertEqual(res["role"], "male_lead")
        self.assertEqual(res["pitch"], ROLE_PRESETS["male_lead"]["pitch"])
        self.assertEqual(res["speed"], ROLE_PRESETS["male_lead"]["speed"])
        self.assertEqual(res["duration_ms"], round((11 * 200.0) / ROLE_PRESETS["male_lead"]["speed"], 3))

    def test_dirty_data_self_healing(self):
        """Test 2: Dirty data self-healing (NaNs, missing keys, invalid types where floats are expected)."""
        segment = {
            "text": 12345,  # int instead of str
            "role": {"invalid": "dict"}, # dict instead of str
            "pitch_shift": math.nan,
            "speed_multiplier": [1, 2], # list instead of float
            "target_duration_ms": "not_a_number"
        }
        res = align_and_modulate(segment)
        self.assertEqual(res["text"], "12345")
        self.assertEqual(res["role"], "narrator")  # default role
        self.assertEqual(res["pitch"], ROLE_PRESETS["narrator"]["pitch"])
        self.assertEqual(res["speed"], ROLE_PRESETS["narrator"]["speed"])

        # test inf
        segment2 = {
            "pitch_shift": float('inf'),
            "speed_multiplier": -1.0
        }
        res2 = align_and_modulate(segment2)
        self.assertEqual(res2["pitch"], ROLE_PRESETS["narrator"]["pitch"])
        self.assertEqual(res2["speed"], ROLE_PRESETS["narrator"]["speed"])

    def test_zero_config_fallback(self):
        """Test 3: Zero-config default fallback (empty dicts or None)."""
        res_none = align_and_modulate(None)
        res_empty = align_and_modulate({})
        res_invalid = align_and_modulate("invalid_type")

        for res in (res_none, res_empty, res_invalid):
            self.assertEqual(res["text"], "...")
            self.assertEqual(res["role"], "narrator")
            self.assertEqual(res["pitch"], 1.0)
            self.assertEqual(res["speed"], 1.0)
            self.assertEqual(res["duration_ms"], 3 * 200.0)

    def test_extreme_boundaries(self):
        """Test 4: Extreme boundaries (huge/negative `target_duration_ms`, massive `pitch_shift`, extremely long text)."""
        segment = {
            "text": "A" * 10000,
            "role": "villain",
            "pitch_shift": 100.0, # massive pitch shift
            "target_duration_ms": 1.0 # extremely small duration
        }
        res = align_and_modulate(segment)
        self.assertEqual(res["pitch"], 3.0) # clamped to max
        self.assertEqual(res["speed"], 10.0) # clamped to max
        # Since speed is clamped to 10.0, duration is re-calculated based on clamped speed
        self.assertEqual(res["duration_ms"], (10000 * 200.0) / 10.0)

        segment2 = {
            "role": "female_lead",
            "pitch_shift": -100.0, # massive negative pitch shift
            "target_duration_ms": -500.0 # negative duration
        }
        res2 = align_and_modulate(segment2)
        self.assertEqual(res2["pitch"], 0.1) # clamped to min
        # negative duration is ignored
        self.assertEqual(res2["speed"], ROLE_PRESETS["female_lead"]["speed"])

    def test_combination_boundary_missing(self):
        """Test 5: Combination of multiple boundary conditions and missing parameters fallback for a specific role."""
        segment = {
            "role": "non_existent_role",
            "speed_multiplier": 0.0001, # almost zero
            "target_duration_ms": 10000000.0 # very large duration
        }
        res = align_and_modulate(segment)
        self.assertEqual(res["role"], "narrator") # falls back to narrator
        self.assertEqual(res["speed"], 0.1) # required speed is tiny, clamped to min 0.1
        self.assertEqual(res["pitch"], 1.0)
        self.assertEqual(res["duration_ms"], (3 * 200.0) / 0.1) # text is "..."


if __name__ == '__main__':
    unittest.main()
