import unittest
import time
from ultra_modules.eight_style_matrix_previewer_self_healing_guard import EightStyleMatrixPreviewerSelfHealingGuard

class TestEightStyleMatrixPreviewerSelfHealingGuard(unittest.TestCase):

    def setUp(self):
        self.previewer = EightStyleMatrixPreviewerSelfHealingGuard()

    def test_normal_execution(self):
        """Test normal execution with valid inputs"""
        prompt = "神秘少年的冒险"
        options = {"resolution": "1920x1080"}

        result = self.previewer.generate_preview(prompt, options)

        self.assertEqual(len(result), 8)
        self.assertIn("修仙", result)
        self.assertEqual(result["修仙"]["prompt"], "[修仙] 神秘少年的冒险")
        self.assertEqual(result["修仙"]["resolution"], "1920x1080")
        self.assertEqual(result["中式规则怪谈"]["status"], "success")

    def test_missing_parameter_fallback(self):
        """Test missing parameter fallback (defaults)"""
        # Call with no arguments
        result = self.previewer.generate_preview()

        self.assertEqual(len(result), 8)
        # Should use DEFAULT_PROMPT
        self.assertEqual(result["都市逆袭"]["prompt"], "[都市逆袭] 默认主角")
        # Should use DEFAULT_RESOLUTION
        self.assertEqual(result["韩漫财阀"]["resolution"], "1024x1024")

    def test_dirty_data_self_healing(self):
        """Test silent self-healing for dirty/invalid data"""
        # Dirty prompt: pass an object/list/dict/None instead of string
        # Dirty options: pass a string/list/None instead of dict

        dirty_prompt_1 = ["invalid", "list"]
        dirty_options_1 = "not_a_dict"

        result1 = self.previewer.generate_preview(dirty_prompt_1, dirty_options_1)
        self.assertEqual(result1["修仙"]["prompt"], "[修仙] 默认主角")
        self.assertEqual(result1["修仙"]["resolution"], "1024x1024")

        dirty_prompt_2 = None
        dirty_options_2 = {"wrong_key": 123} # Missing 'resolution'

        result2 = self.previewer.generate_preview(dirty_prompt_2, dirty_options_2)
        self.assertEqual(result2["修仙"]["prompt"], "[修仙] 默认主角")
        self.assertEqual(result2["修仙"]["resolution"], "1024x1024")

        dirty_prompt_3 = "   " # Empty string after strip
        result3 = self.previewer.generate_preview(dirty_prompt_3, None)
        self.assertEqual(result3["修仙"]["prompt"], "[修仙] 默认主角")

        dirty_prompt_4 = " None " # String 'None'
        result4 = self.previewer.generate_preview(dirty_prompt_4, None)
        self.assertEqual(result4["修仙"]["prompt"], "[修仙] 默认主角")

        # Test valid string prompt wrapped in strange whitespace
        valid_prompt = "  剑神归来  \n"
        result5 = self.previewer.generate_preview(valid_prompt, None)
        self.assertEqual(result5["修仙"]["prompt"], "[修仙] 剑神归来")

    def test_snapshot_undo_mechanism(self):
        """Test 5-second one-click undo snapshot mechanism"""
        self.previewer.generate_preview("第一个操作", {"resolution": "100x100"})
        state1 = self.previewer.get_current_state()

        self.previewer.generate_preview("第二个操作", {"resolution": "200x200"})
        state2 = self.previewer.get_current_state()

        self.assertEqual(state2["prompt"], "第二个操作")

        # Undo within 5 seconds
        undo_success = self.previewer.undo()
        self.assertTrue(undo_success)

        # State should be reverted to first operation
        reverted_state = self.previewer.get_current_state()
        self.assertEqual(reverted_state["prompt"], "第一个操作")
        self.assertEqual(reverted_state["options"]["resolution"], "100x100")

        # Undo when no more snapshots available
        undo_success_2 = self.previewer.undo()
        self.assertFalse(undo_success_2)

    def test_extreme_boundary_case(self):
        """Test extreme boundary cases (e.g. timeout on undo)"""
        self.previewer.generate_preview("初始状态")

        # Simulate time passing beyond 5 seconds by manually hacking timestamp
        # since time.sleep(5.1) would make tests unnecessarily slow
        state = self.previewer.get_current_state()
        state["timestamp"] = time.time() - 5.1

        # Try to undo after 5 seconds - should silently fail and return False
        undo_success = self.previewer.undo()
        self.assertFalse(undo_success)

        # State should remain unchanged
        self.assertEqual(self.previewer.get_current_state()["prompt"], "初始状态")

        # Try passing extremely deep/complex objects to test copy robustness
        class WeirdObj:
            def __str__(self):
                raise ValueError("Cannot convert to string")

        result = self.previewer.generate_preview(WeirdObj(), {"resolution": "valid"})
        self.assertEqual(result["修仙"]["prompt"], "[修仙] 默认主角")

        # Circular reference in options
        a = {}
        a["self"] = a
        result = self.previewer.generate_preview("正常提示词", a)
        self.assertEqual(result["修仙"]["prompt"], "[修仙] 正常提示词")
        self.assertEqual(result["修仙"]["resolution"], "1024x1024")

if __name__ == '__main__':
    unittest.main()
