import unittest
import json
from ultra_modules.golden_3s_hook_splitter_plain_explainer import Golden3sHookSplitter

class TestGolden3sHookSplitterPlainExplainer(unittest.TestCase):
    def setUp(self):
        self.splitter = Golden3sHookSplitter(chars_per_episode=50)

    def test_normal_split(self):
        """测试正常文本按指定字数切分及断句"""
        text = "这是一个非常普通的开头。主角发现了一个惊天大秘密，这个秘密关系到整个世界的存亡。他必须立刻出发，寻找传说中的神器来拯救大家。然而，反派已经设下了重重埋伏，第一场战斗即将打响！"
        episodes = self.splitter.split_to_episodes(text)

        self.assertGreater(len(episodes), 1, "应该被拆分为多集")
        self.assertEqual(episodes[0]["episode"], 1)
        self.assertTrue("这是一个非常普通的开头" in episodes[0]["hook"])
        self.assertTrue("战斗即将打响！" in episodes[-1]["cliffhanger"])
        self.assertTrue("开局" in episodes[0]["summary"])

    def test_dirty_data_healing(self):
        """测试脏数据自愈能力（如零宽字符、过多空格、非字符串输入）"""
        # 测试不可见字符和多余空格
        dirty_text = "男主\u200b\u200c重生了。    他决定\n\n\n复仇！\uFEFF"
        episodes = self.splitter.split_to_episodes(dirty_text)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["content"], "男主重生了。 他决定 复仇！")

        # 测试传入非字符串类型（如整数或None）
        episodes_int = self.splitter.split_to_episodes(12345)
        self.assertEqual(len(episodes_int), 1)
        self.assertEqual(episodes_int[0]["content"], "12345")

        episodes_none = self.splitter.split_to_episodes(None)
        self.assertEqual(len(episodes_none), 0)

    def test_missing_params_fallback(self):
        """测试缺参或参数类型错误的默认兜底机制"""
        text = "内容很长" * 500  # 2000字

        # 使用默认实例，未传 chars_per_episode
        default_splitter = Golden3sHookSplitter()
        episodes = default_splitter.split_to_episodes(text)
        # 默认应该是1000字一集，2000字切出来应该是2集
        self.assertEqual(len(episodes), 2)

        # 传入非法的 chars_per_episode（如字符串、负数、None）
        episodes_str = default_splitter.split_to_episodes(text, chars_per_episode="abc")
        self.assertEqual(len(episodes_str), 2, "非法参数应兜底为1000")

        episodes_neg = default_splitter.split_to_episodes(text, chars_per_episode=-10)
        self.assertEqual(len(episodes_neg), 2, "负数应兜底为1000")

    def test_empty_input(self):
        """测试极端边界：空字符串或纯空白字符"""
        episodes = self.splitter.split_to_episodes("")
        self.assertEqual(episodes, [])

        episodes_spaces = self.splitter.split_to_episodes("   \n\t  ")
        self.assertEqual(episodes_spaces, [])

    def test_export_formats(self):
        """测试大白话导出卡片格式及容错"""
        episodes = [{
            "episode": 1,
            "hook": "开局退婚...",
            "cliffhanger": "竟然是他！",
            "content": "开局退婚，三年之期已到。来人竟然是他！",
            "summary": "第1集：开局「开局退婚...」瞬间吸睛，结尾断在「竟然是他！」疯狂拉扯读者。"
        }]

        # JSON测试
        json_res = self.splitter.export_json(episodes)
        parsed = json.loads(json_res)
        self.assertEqual(parsed[0]["episode"], 1)

        # JSON 错参测试
        self.assertEqual(self.splitter.export_json(None), "[]")

        # Markdown测试
        md_res = self.splitter.export_markdown(episodes)
        self.assertIn("## 第1集", md_res)
        self.assertIn("开局退婚...", md_res)

        # Markdown 空参测试
        self.assertIn("> 暂无内容", self.splitter.export_markdown(None))

        # HTML测试
        html_res = self.splitter.export_html(episodes)
        self.assertIn("<!DOCTYPE html>", html_res)
        self.assertIn("业务一秒看懂", html_res)
        self.assertIn("第 1 集", html_res)

        # HTML 错参测试
        self.assertIn("暂无内容，请检查输入", self.splitter.export_html({}))

if __name__ == "__main__":
    unittest.main()
