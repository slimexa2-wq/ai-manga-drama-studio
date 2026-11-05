import unittest
import json
from ultra_modules.dialogue_lip_sync_timer_plain_explainer import DialogueLipSyncTimerPlainExplainer, generate_sync_card

class TestDialogueLipSyncTimerPlainExplainer(unittest.TestCase):

    def test_normal_data_parsing_markdown(self):
        # Normal case, markdown output
        text = "你好，世界。这是一段测试。"
        explainer = DialogueLipSyncTimerPlainExplainer(text=text, audio_peaks=[1000, 2000])
        result = explainer.export('markdown')

        # '你好' (2) + '世界' (2) + '这是一段测试' (6) = 10 chars
        # 10 * 250 = 2500ms
        # '，' = 1 * 300 = 300ms
        # '。', '。' = 2 * 500 = 1000ms
        # Total text: 3800ms
        # Audio duration = max(1000, 2000) + 500 = 2500ms
        # Final duration = max(3800, 2500) = 3800ms

        self.assertIn("### 分镜时长建议卡", result)
        self.assertIn("10 个字", result)
        self.assertIn("1 个短停顿", result)
        self.assertIn("2 个长停顿", result)
        self.assertIn("3.80 秒", result) # text duration
        self.assertIn("2.50 秒", result) # audio duration
        self.assertIn("最少保留时长为：3.80 秒", result)

    def test_audio_peaks_override_text_duration_json(self):
        # Audio duration is longer, json output
        text = "快跑！" # 2 chars = 500ms, 1 period = 500ms -> 1000ms text
        explainer = DialogueLipSyncTimerPlainExplainer(text=text, audio_peaks=[500, 1500, 3000])
        result = explainer.export('json')

        data = json.loads(result)
        self.assertIn("conclusion", data)
        self.assertIn("details", data)

        self.assertEqual(data["details"]["text_duration_ms"], 1000)
        self.assertEqual(data["details"]["audio_duration_ms"], 3500)
        self.assertEqual(data["details"]["final_duration_ms"], 3500)

    def test_dirty_data_self_healing(self):
        # None text, invalid audio peak types, invalid export format
        explainer = DialogueLipSyncTimerPlainExplainer(text=None, audio_peaks=["invalid", 1000, None])
        # Text becomes "", peaks become [1000]
        # Text dur = 0, Audio dur = 1500 -> Final = 1500

        result = explainer.export(export_format=123) # fallback to markdown
        self.assertIn("### 分镜时长建议卡", result)
        self.assertIn("0 个字", result)
        self.assertIn("1 个音频波形峰值", result)
        self.assertIn("1.50 秒", result) # final duration

    def test_missing_parameters_fallback_helper(self):
        # Using helper with minimal args
        result = generate_sync_card() # default None, None, 'markdown'
        # Text="", Audio=[]
        # Text dur = 0, Audio dur = 0, Final = 0
        self.assertIn("### 分镜时长建议卡", result)
        self.assertIn("0 个字", result)
        self.assertIn("0.00 秒", result)
        self.assertNotIn("音频波形峰值", result) # No peaks detected

    def test_extreme_boundaries(self):
        # Very long string, HTML output
        text = "啊" * 10000 + "，" * 1000 + "。" * 1000
        # Text dur = 10000 * 250 + 1000 * 300 + 1000 * 500 = 2500000 + 300000 + 500000 = 3300000 ms
        explainer = DialogueLipSyncTimerPlainExplainer(text=text)
        result = explainer.export('HTML') # case insensitivity check

        self.assertIn("<div class=\"sync-card\">", result)
        self.assertIn("10000 个字", result)
        self.assertIn("1000 个短停顿", result)
        self.assertIn("1000 个长停顿", result)
        self.assertIn("3300.00 秒", result)

    def test_minimum_text_duration(self):
        # Test the minimum 1000ms rule for text
        text = "哈" # 1 char = 250ms -> minimum 1000ms
        explainer = DialogueLipSyncTimerPlainExplainer(text=text)
        result = explainer.calculate_duration_ms()
        self.assertEqual(result["text_duration_ms"], 1000)

if __name__ == '__main__':
    unittest.main()
