import unittest
from ultra_modules.dialogue_lip_sync_timer_self_healing_guard import DialogueLipSyncTimerSelfHealingGuard

class TestDialogueLipSyncTimerSelfHealingGuard(unittest.TestCase):
    def setUp(self):
        self.guard = DialogueLipSyncTimerSelfHealingGuard()

    def test_normal_calculation(self):
        # 10 chars, 2 chars/s = 5s
        # 2 punctuations, 0.5s each = 1s
        # Total = 6s
        # Default options: chars_per_second=5.0, punctuation_pause=0.5
        # 10 chars = 2s, 2 punct = 1s, total = 3s
        text = "Hello world! This is a test."
        duration = self.guard.calculate_duration(
            text=text,
            audio_peaks=[],
            options={"chars_per_second": 5.0, "punctuation_pause": 0.5}
        )
        # text="Hello world! This is a test." -> chars: 28 total, no space: Helloworld!Thisisatest. = 23 chars. 23/5.0 = 4.6.
        # punct: ! and . (2). 2*0.5 = 1.0. Total = 5.6
        self.assertAlmostEqual(duration, 5.6)
        self.assertEqual(self.guard.calculation_count, 1)

    def test_dirty_data_self_healing(self):
        # Incorrect types
        # int instead of string
        text = 12345
        # string as audio_peaks
        audio_peaks = "abc"
        # string as options
        options = "not a dict"

        duration = self.guard.calculate_duration(text=text, audio_peaks=audio_peaks, options=options)

        # text="12345" -> 5 chars. 5/5.0 = 1s. No punct.
        # audio_peaks becomes [].
        # options falls back to defaults.
        # min_duration falls back to 1.0. Total duration is 1.0.
        self.assertAlmostEqual(duration, 1.0)

        # Test converting single float to list for audio_peaks
        duration2 = self.guard.calculate_duration(text="A.", audio_peaks=0.5)
        # text="A." -> 2 chars. 2/5.0 = 0.4s. 1 punct = 0.5s. Total = 0.9s.
        # peak duration = 1 * 0.2 = 0.2s. duration = 0.9. peak_duration is not > duration * 0.5 (0.2 > 0.45 is False).
        # Duration = 0.9, bounded by min_duration (1.0).
        self.assertAlmostEqual(duration2, 1.0)

        # Try tuple of strings and ints
        duration3 = self.guard.calculate_duration(text="", audio_peaks=("0.1", "bad", 0.5))
        # "bad" can't convert to float, caught by Exception in comprehension
        # audio_peaks = [0.1, 0.5] (2 items) if list comprehension works properly, but actually float("bad") raises ValueError.
        # Wait, the try/except around list comprehension will catch ValueError and set audio_peaks = []
        # So duration3 will just be min_duration 1.0.
        self.assertAlmostEqual(duration3, 1.0)

    def test_missing_parameters(self):
        # Empty call
        duration = self.guard.calculate_duration()
        # text="", audio_peaks=[], options={}
        # Duration = 0, bounded by min_duration = 1.0
        self.assertEqual(duration, 1.0)

        # Empty text
        duration2 = self.guard.calculate_duration(text=None, audio_peaks=None, options=None)
        self.assertEqual(duration2, 1.0)

    def test_extreme_boundaries(self):
        # Extremely long string
        text = "A" * 1000
        duration = self.guard.calculate_duration(text=text)
        # 1000/5.0 = 200s. Bounded by max_duration = 30.0
        self.assertEqual(duration, 30.0)

        # Inverted min/max duration in options
        duration2 = self.guard.calculate_duration(text=text, options={"min_duration": 50.0, "max_duration": 10.0})
        # They should be swapped to min=10.0, max=50.0.
        # 1000/5.0 = 200s. Bounded by max=50.0
        self.assertEqual(duration2, 50.0)

        # Negative chars_per_second and punctuation_pause
        duration3 = self.guard.calculate_duration(text="A, B.", options={"chars_per_second": -1, "punctuation_pause": -0.5})
        # Falls back to 5.0 and 0.5.
        # "A,B." = 4 chars (4/5.0 = 0.8), 2 punct (2*0.5 = 1.0) = 1.8.
        self.assertAlmostEqual(duration3, 1.8)

    def test_undo_snapshot_mechanism(self):
        self.assertFalse(self.guard.undo()) # No history to undo initially (only 1 state)

        self.guard.calculate_duration(text="State 1")
        self.guard.calculate_duration(text="State 2", options={"min_duration": 2.0})
        self.assertEqual(self.guard.calculation_count, 2)
        self.assertEqual(self.guard.last_calculated_duration, 2.0)

        # Undo to State 1
        success = self.guard.undo()
        self.assertTrue(success)
        self.assertEqual(self.guard.calculation_count, 1)
        # "State 1" = 7 chars, no spaces = 6 chars. 6/5.0 = 1.2s. No punct.
        self.assertAlmostEqual(self.guard.last_calculated_duration, 1.2)

        # Undo to Initial State
        success = self.guard.undo()
        self.assertTrue(success)
        self.assertEqual(self.guard.calculation_count, 0)
        self.assertEqual(self.guard.last_calculated_duration, 0.0)

        # Cannot undo anymore
        self.assertFalse(self.guard.undo())

    def test_audio_peaks_heuristic(self):
        # A lot of audio peaks to trigger the peak heuristic
        peaks = [0.1] * 20 # 20 peaks, peak_duration = 4.0
        duration = self.guard.calculate_duration(text="Hi", audio_peaks=peaks)
        # text="Hi" -> 2 chars = 0.4s.
        # peak_duration = 4.0. peak_duration > 0.4 * 0.5 (4.0 > 0.2) is True.
        # duration = (0.4 + 4.0) / 2 = 2.2
        self.assertAlmostEqual(duration, 2.2)

        # Just enough peaks where peak_duration is evaluated
        # Not a string option
        self.guard.calculate_duration(text="A", options={"min_duration": "not_float", "max_duration": "not_float"})
        self.assertEqual(self.guard.last_calculated_duration, 1.0) # min defaults to 1.0, 0.2 text duration bounded by min 1.0

if __name__ == '__main__':
    unittest.main()
