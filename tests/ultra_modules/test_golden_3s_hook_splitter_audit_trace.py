import unittest
import os
import sys

# Ensure the project root is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from ultra_modules.golden_3s_hook_splitter_audit_trace import Golden3SHookSplitter, AuditLogger

class TestGolden3SHookSplitterAuditTrace(unittest.TestCase):
    def setUp(self):
        self.splitter = Golden3SHookSplitter()

    def test_normal_case_expected_boundaries(self):
        # Text with clear cliffhangers/hooks
        text = "这是第一集的开始。男主发现了系统的秘密！" + "叮！系统已绑定。" + "第二集的剧情展开。男主遇到危机，陷入绝望？" + "重生归来，他决定复仇。"
        # We need text long enough to trigger splitting. Let's adjust max_length to 20 for testing.
        result = self.splitter.split(text, min_length=10, max_length=30)

        episodes = result['episodes']
        logs = result['audit_logs']

        self.assertGreater(len(episodes), 1)
        self.assertTrue(any(log['step'] == 'split_episode' for log in logs))

        # Verify the split happened at a punctuation
        self.assertTrue(episodes[0].endswith('！') or episodes[0].endswith('。') or episodes[0].endswith('？'))

    def test_dirty_data_self_healing(self):
        # 1. None input
        res1 = self.splitter.split(None)
        self.assertEqual(res1['episodes'], [])

        # 2. Integer input
        res2 = self.splitter.split(12345)
        self.assertEqual(res2['episodes'], ["12345"])

        # 3. Excessive whitespace
        res3 = self.splitter.split("   大量   空白    数据  ", min_length=2, max_length=5)
        self.assertEqual("大量 空白 数据", "".join(res3['episodes']))

    def test_missing_parameter_fallback(self):
        # Test default resolving logic indirectly by passing bad params
        # Providing bad types or min > max
        long_text = "测" * 3000
        # Passing None for params
        res1 = self.splitter.split(long_text, min_length=None, max_length=None)
        self.assertGreater(len(res1['episodes']), 1)
        # Verify max_length fallback (default is 2000, so first episode should be around that or max 2000)
        self.assertLessEqual(len(res1['episodes'][0]), 2000)

        # Passing min > max
        res2 = self.splitter.split(long_text, min_length=2000, max_length=1000)
        # Should fallback to min=500, max=max(2000, 500+1000) = 2000
        self.assertGreater(len(res2['episodes']), 1)
        self.assertLessEqual(len(res2['episodes'][0]), 2000)

        # Passing non-int
        res3 = self.splitter.split(long_text, min_length="bad", max_length="worse")
        self.assertGreater(len(res3['episodes']), 1)

    def test_extreme_boundary_cases(self):
        # 1. Very short text
        res1 = self.splitter.split("极短文本", min_length=10, max_length=20)
        self.assertEqual(res1['episodes'], ["极短文本"])

        # 2. Text with no punctuation
        no_punct = "这就是一段完全没有任何标点符号的非常长的文本主要用来测试在找不到断句点的时候程序会不会崩溃或者报错我们的算法应该能在最大长度或者有空格的地方直接硬切保证不出错"
        res2 = self.splitter.split(no_punct, min_length=5, max_length=15)
        self.assertGreater(len(res2['episodes']), 1)
        self.assertEqual(len(res2['episodes'][0]), 15) # Hard split at max_length if no space

        # 3. Text with spaces but no punctuation
        no_punct_spaces = "测试 空格 分割 非常长 " * 10
        res3 = self.splitter.split(no_punct_spaces, min_length=10, max_length=20)
        self.assertGreater(len(res3['episodes']), 1)
        # Should split at a space
        self.assertTrue(res3['episodes'][0].endswith(' '))

        # 4. Out of bounds index test for score (internally called but we can force it)
        score = self.splitter._score_split_point("测试", -1)
        self.assertEqual(score, 0)
        score = self.splitter._score_split_point("测试", 10)
        self.assertEqual(score, 0)

    def test_hook_and_cliffhanger_matching(self):
        # Text crafted so that one punctuation has strong hook/cliffhanger, and another doesn't
        # The window [min, max] = [10, 30]
        # Punctuation 1 at idx 12: "。" (score 0)
        # Punctuation 2 at idx 22: "？" + "系统" (score 20+15 = 35)
        text = "前面是无聊的过渡句。男主突然陷入了绝望？系统觉醒了！后面的剧情。"
        #                 ^ idx 9.          ^ idx 19.

        res = self.splitter.split(text, min_length=5, max_length=25)
        episodes = res['episodes']
        logs = res['audit_logs']

        # Expected split at "绝望？", which gives a high score.
        self.assertTrue(episodes[0].endswith("？"))

        # Verify the logs show the scoring
        split_logs = [log for log in logs if log['step'] == 'split_episode']
        self.assertGreater(len(split_logs), 0)
        # Check that score is > 0 indicating keyword matching worked
        self.assertGreater(split_logs[0]['details']['score'], 0)

if __name__ == '__main__':
    unittest.main()
