import unittest
from ultra_modules.golden_3s_hook_splitter_core_engine import split_novel_into_episodes, clean_text

class TestGolden3sHookSplitter(unittest.TestCase):

    def test_clean_text_dirty_data(self):
        # Test silent cleaning of dirty data (zero width chars, extra spaces, extra newlines)
        dirty_text = "Hello\u200b world!  \n\n\n\nThis is\t a test.\r\nEnd."
        cleaned = clean_text(dirty_text)
        self.assertEqual(cleaned, "Hello world! \n\nThis is a test.\nEnd.")

    def test_split_empty_or_none(self):
        # 1. Extreme limits / empty
        self.assertEqual(split_novel_into_episodes(""), [])
        self.assertEqual(split_novel_into_episodes(None), [])

    def test_split_missing_params_fallback(self):
        # 2. Missing params fallback (no config provided)
        # Default target_length=1000, tolerance=200, max_length=1500
        # If we have paragraphs that exceed target_length + tolerance, it should split
        p1 = "A" * 600
        p2 = "B" * 650
        text = f"{p1}\n{p2}" # Total ~ 1251 chars

        episodes = split_novel_into_episodes(text)
        # current_length after p1 is 601
        # target_zone is 800 to 1200
        # current_length after p2 is 601 + 651 = 1252 > 1200
        # Should split.
        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0], p1)
        self.assertEqual(episodes[1], p2)

    def test_split_normal_with_hooks(self):
        # 3. Normal text with strong hooks
        config = {"target_length": 50, "tolerance": 20, "max_length": 100}

        # P1: 40 chars. P2: 20 chars ending in hook. Total = 60 (in target zone 30-70).
        # Should split after P2.
        p1 = "A" * 40
        p2 = "B" * 19 + "！"
        p3 = "C" * 40
        text = f"{p1}\n{p2}\n{p3}"

        episodes = split_novel_into_episodes(text, config)

        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0], f"{p1}\n{p2}")
        self.assertEqual(episodes[1], p3)

    def test_split_extreme_limits_huge_block(self):
        # 4. Extreme text length limit splitting
        config = {"target_length": 50, "tolerance": 20, "max_length": 100}

        # p1: 20 chars
        # p2: 150 chars
        p1 = "A" * 20
        p2 = "B" * 150
        text = f"{p1}\n{p2}"

        episodes = split_novel_into_episodes(text, config)

        # It should split before p2 because current_length (20) + p2_len (150) > max_length(100)
        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0], p1)
        self.assertEqual(episodes[1], p2)

    def test_split_hook_quote(self):
        # 5. Hook ending with quote
        config = {"target_length": 30, "tolerance": 10, "max_length": 100}

        # Target zone: 20-40
        p1 = "A" * 15
        p2 = '"B"!' # 4 chars
        p3 = "C" * 15 # 15 chars
        # Total after p1: 16 (not in zone)
        # Total after p2: 16 + 5 = 21 (in zone 20-40). Ends with quote/exclamation hook.
        # Should split after p2.

        text = f"{p1}\n{p2}\n{p3}"

        episodes = split_novel_into_episodes(text, config)

        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0], f"{p1}\n{p2}")
        self.assertEqual(episodes[1], p3)

if __name__ == '__main__':
    unittest.main()
