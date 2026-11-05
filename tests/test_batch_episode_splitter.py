import unittest
from src.batch_episode_splitter import split_long_novel_into_episodes

class TestBatchEpisodeSplitter(unittest.TestCase):
    def test_split_long_novel_into_episodes(self):
        # A long text that should be split into multiple episodes
        long_text = """
第一段话，包含一些背景信息，这是一个很长的段落，大概需要好几秒钟才能读完，字数也要多一点。
第二段话，主角开始受欺负。这里也有很多字，我们需要凑字数。
第三段话，主角愤怒了，他大吼一声：“我要把你们全杀了！”这里的字数也要多。
第四段话，主角开始觉醒，他获得了强大的力量。字数，字数，更多的字数。
第五段话，主角开始反击，一剑斩杀了反派。战斗非常激烈。
第六段话，主角取得了胜利，但是新的敌人又出现了，悬念。
""" * 50 # Duplicate to make it very long

        episodes = split_long_novel_into_episodes(long_text, target_duration_sec=30) # Short target to force splits

        self.assertTrue(len(episodes) > 1, "Should split into multiple episodes")

        for ep in episodes:
            self.assertIn("text", ep)
            self.assertIn("golden_3s_hook", ep)
            self.assertIn("cliffhanger", ep)
            self.assertIn("satisfying_beats", ep)

            # Verify hook is from the beginning of the text
            self.assertTrue(ep["text"].startswith(ep["golden_3s_hook"].replace("...", "")))

            # Verify cliffhanger is from the end
            self.assertTrue(ep["text"].endswith(ep["cliffhanger"].replace("...", "")))

            # Satisfying beats should contain expected keywords
            for beat in ep["satisfying_beats"]:
                self.assertTrue(any(k in beat for k in ("怒", "杀", "死", "滚", "奉还", "轰", "碎", "剑", "斩", "反转", "觉醒", "冷笑")))

if __name__ == "__main__":
    unittest.main()
