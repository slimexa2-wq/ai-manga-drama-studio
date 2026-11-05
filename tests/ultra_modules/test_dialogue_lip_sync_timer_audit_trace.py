import unittest
from ultra_modules.dialogue_lip_sync_timer_audit_trace import DialogueTimerAuditTrace

class TestDialogueTimerAuditTrace(unittest.TestCase):
    def setUp(self):
        self.calculator = DialogueTimerAuditTrace()

    def test_normal_execution(self):
        # "Hello today." -> 10 chars
        # 10 chars at 5.0 cps = 2.0s
        # 1 period (0.6s) = 0.6s
        # Total text duration: 2.6s
        text = "Hello today."
        result = self.calculator.calculate_duration(text)
        self.assertEqual(result["clean_result"]["duration"], 2.6)
        self.assertEqual(result["diff_highlight"]["action"], "used_text_duration")
        self.assertIn("Calculated text-based duration: 2.600s", result["audit_trace"][0])

    def test_dirty_data_self_healing(self):
        # Test with None
        result_none = self.calculator.calculate_duration(None)
        self.assertEqual(result_none["clean_result"]["duration"], 0.0)
        self.assertTrue(any("Auto-healed invalid text type 'NoneType'" in msg for msg in result_none["audit_trace"]))

        # Test with integer
        result_int = self.calculator.calculate_duration(12345)
        self.assertEqual(result_int["clean_result"]["duration"], 1.0) # 5 chars at 5 cps
        self.assertTrue(any("Auto-healed invalid text type 'int'" in msg for msg in result_int["audit_trace"]))

        # Test with extra spaces
        result_spaces = self.calculator.calculate_duration("  Test  text  ")
        self.assertEqual(result_spaces["clean_result"]["duration"], 1.6) # 8 chars at 5 cps
        self.assertTrue(any("Cleaned extra spaces/newlines from text" in msg for msg in result_spaces["audit_trace"]))

    def test_missing_parameter_fallbacks(self):
        # Initialize with dirty params
        dirty_calc = DialogueTimerAuditTrace(base_cps="invalid", default_pause=-1, punctuation_pauses="not_a_dict")

        # Should fallback to base_cps=5.0
        text = "12345"
        result = dirty_calc.calculate_duration(text)
        self.assertEqual(result["clean_result"]["duration"], 1.0)

        # Invalid audio duration and peaks
        result_invalid_audio = dirty_calc.calculate_duration(text, audio_duration="not_a_number", audio_peaks="invalid")
        self.assertEqual(result_invalid_audio["clean_result"]["duration"], 1.0)
        self.assertTrue(any("Auto-healed invalid audio_duration 'not_a_number'" in msg for msg in result_invalid_audio["audit_trace"]))
        self.assertTrue(any("Auto-healed invalid audio_peaks type 'str'" in msg for msg in result_invalid_audio["audit_trace"]))

    def test_audio_peak_alignment_expansion(self):
        text = "Hello" # 5 chars = 1.0s
        # audio duration is 2.5s, peaks max at 2.8s
        # audio_based_duration = max(2.5, 2.8) = 2.8s > 1.0s -> expand
        result = self.calculator.calculate_duration(text, audio_duration=2.5, audio_peaks=[1.0, 2.8, 1.5])
        self.assertEqual(result["clean_result"]["duration"], 2.8)
        self.assertEqual(result["diff_highlight"]["action"], "aligned_to_audio_expansion")
        self.assertEqual(result["diff_highlight"]["diff"], 1.8)

    def test_audio_peak_alignment_truncation(self):
        # 20 chars at 5.0 cps = 4.0s
        text = "A" * 20
        # Explicit audio duration is 3.0s, no peaks
        result = self.calculator.calculate_duration(text, audio_duration=3.0)
        self.assertEqual(result["clean_result"]["duration"], 3.0)
        self.assertEqual(result["diff_highlight"]["action"], "truncated_to_audio_duration")
        self.assertEqual(result["diff_highlight"]["diff"], -1.0)

    def test_extreme_boundary_cases(self):
        # Empty string
        res1 = self.calculator.calculate_duration("")
        self.assertEqual(res1["clean_result"]["duration"], 0.0)

        # Only punctuation
        res2 = self.calculator.calculate_duration("...,,,")
        # '...' is 1.0s, three commas are 3*0.3=0.9s -> 1.9s
        self.assertEqual(res2["clean_result"]["duration"], 1.9)

        # Huge string
        res3 = self.calculator.calculate_duration("A" * 10000)
        self.assertEqual(res3["clean_result"]["duration"], 2000.0)

        # Dirty audio peaks with strings and negatives
        res4 = self.calculator.calculate_duration("Hello", audio_peaks=["not_a_number", -5.0, 2.0])
        # Text = 1.0s, max valid peak = 2.0s -> 2.0s
        self.assertEqual(res4["clean_result"]["duration"], 2.0)

if __name__ == '__main__':
    unittest.main()
