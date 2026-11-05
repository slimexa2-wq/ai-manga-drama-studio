import unittest
from ultra_modules.golden_3s_hook_splitter_export_formatter import Golden3sHookSplitterExportFormatter

class TestGolden3sHookSplitterExportFormatter(unittest.TestCase):

    def test_normal_case(self):
        # Normal data
        text = "这是一个黄金前3秒的钩子，这是中间的内容，这是集末悬念卡点，这又是一个正常内容结尾。"
        result = Golden3sHookSplitterExportFormatter.split_and_format(text, target_episodes=2)

        self.assertEqual(result["comments"], 0)
        self.assertEqual(result["total_words"], len(text))
        self.assertEqual(result["target_episodes"], 2)
        self.assertEqual(len(result["episodes"]), 2)
        self.assertEqual(result["episodes"][0]["word_count"], 21)
        self.assertEqual(result["episodes"][1]["word_count"], 21)

        expected_summary = (
            f"📊 拆解汇报：总计 42 字，已拆分为 2 集。\n"
            f"🔥 黄金3秒钩子：这是一个黄金前3秒的钩子，这是\n"
            f"🎬 集末悬念卡点：卡点，这又是一个正常内容结尾。"
        )
        self.assertEqual(result["summary"], expected_summary)

    def test_dirty_inputs(self):
        # Dirty data self-healing: None, NaN replacements
        result = Golden3sHookSplitterExportFormatter.split_and_format(text=None, target_episodes=-5)

        self.assertEqual(result["comments"], 0)
        self.assertEqual(result["total_words"], 0)
        self.assertEqual(result["target_episodes"], 1)
        self.assertEqual(len(result["episodes"]), 1)
        self.assertEqual(result["episodes"][0]["content"], "")
        self.assertEqual(result["episodes"][0]["word_count"], 0)
        self.assertEqual(result["episodes"][0]["hook"], "")
        self.assertEqual(result["episodes"][0]["suspense"], "")

        expected_summary = (
            "📊 拆解汇报：总计 0 字，已拆分为 1 集。\n"
            "🔥 黄金3秒钩子：无\n"
            "🎬 集末悬念卡点：无"
        )
        self.assertEqual(result["summary"], expected_summary)

    def test_missing_parameters_default_fallback(self):
        # Missing parameter default fallbacks
        result = Golden3sHookSplitterExportFormatter.split_and_format()

        self.assertEqual(result["comments"], 0)
        self.assertEqual(result["total_words"], 0)
        self.assertEqual(result["target_episodes"], 1)
        self.assertEqual(len(result["episodes"]), 1)

    def test_extreme_boundary_case_more_episodes_than_words(self):
        # Extreme boundary cases: episodes > total_words
        text = "极少字"
        result = Golden3sHookSplitterExportFormatter.split_and_format(text, target_episodes=5)

        self.assertEqual(result["comments"], 0)
        self.assertEqual(result["total_words"], 3)
        self.assertEqual(result["target_episodes"], 5)
        self.assertEqual(len(result["episodes"]), 5)

        # Word counts should be: 1, 1, 1, 0, 0
        self.assertEqual(result["episodes"][0]["word_count"], 1)
        self.assertEqual(result["episodes"][1]["word_count"], 1)
        self.assertEqual(result["episodes"][2]["word_count"], 1)
        self.assertEqual(result["episodes"][3]["word_count"], 0)
        self.assertEqual(result["episodes"][4]["word_count"], 0)

        # Content verification
        self.assertEqual(result["episodes"][0]["content"], "极")
        self.assertEqual(result["episodes"][1]["content"], "少")
        self.assertEqual(result["episodes"][2]["content"], "字")
        self.assertEqual(result["episodes"][3]["content"], "")

        expected_summary = (
            "📊 拆解汇报：总计 3 字，已拆分为 5 集。\n"
            "🔥 黄金3秒钩子：极\n"
            "🎬 集末悬念卡点：无"
        )
        self.assertEqual(result["summary"], expected_summary)

    def test_exact_division_length(self):
        text = "十个字的测试文本正好" # 10 chars
        result = Golden3sHookSplitterExportFormatter.split_and_format(text, target_episodes=2)

        self.assertEqual(result["comments"], 0)
        self.assertEqual(result["total_words"], 10)
        self.assertEqual(result["target_episodes"], 2)
        self.assertEqual(len(result["episodes"]), 2)
        self.assertEqual(result["episodes"][0]["word_count"], 5)
        self.assertEqual(result["episodes"][1]["word_count"], 5)

        self.assertEqual(result["episodes"][0]["hook"], "十个字的测")
        self.assertEqual(result["episodes"][0]["suspense"], "十个字的测")
        self.assertEqual(result["episodes"][1]["hook"], "试文本正好")
        self.assertEqual(result["episodes"][1]["suspense"], "试文本正好")

    def test_non_string_input(self):
        # Non-string input should fallback to empty string
        result = Golden3sHookSplitterExportFormatter.split_and_format(text=12345, target_episodes=2)

        self.assertEqual(result["comments"], 0)
        self.assertEqual(result["total_words"], 0)
        self.assertEqual(result["target_episodes"], 2)
        self.assertEqual(len(result["episodes"]), 2)
        self.assertEqual(result["episodes"][0]["content"], "")

if __name__ == "__main__":
    unittest.main()
