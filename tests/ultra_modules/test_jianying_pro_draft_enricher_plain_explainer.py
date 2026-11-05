import unittest
import json
from ultra_modules.jianying_pro_draft_enricher_plain_explainer import DraftExplainer

class TestDraftExplainer(unittest.TestCase):
    def setUp(self):
        self.explainer = DraftExplainer()

    def test_normal_valid_data(self):
        data = {
            'effects': [{'name': '闪电'}, {'name': '火焰'}],
            'transitions': [{'name': '向左推入'}, {'name': '黑场'}],
            'camera_moves': [{'name': '放大'}, '缩小'],
            'bgm': {'name': '激昂进行曲'}
        }
        result = self.explainer.explain(data, format_type='markdown')
        self.assertIn('闪电、火焰', result)
        self.assertIn('向左推入、黑场', result)
        self.assertIn('放大、缩小', result)
        self.assertIn('激昂进行曲', result)

    def test_dirty_data_self_healing(self):
        # Passing a string instead of a dict, dirty list items
        data = "This is not a dict"
        result = self.explainer.explain(data, format_type='markdown')
        self.assertIn('无特效', result)
        self.assertIn('无转场', result)
        self.assertIn('无运镜', result)
        self.assertIn('无背景音乐', result)

        # Passing wrong types for fields
        dirty_data = {
            'effects': "Not a list",
            'transitions': 123,
            'camera_moves': None,
            'bgm': ['Not', 'a', 'string', 'or', 'dict']
        }
        result_dirty = self.explainer.explain(dirty_data, format_type='markdown')
        self.assertIn('无特效', result_dirty)
        self.assertIn('无转场', result_dirty)
        self.assertIn('无运镜', result_dirty)
        self.assertIn('无背景音乐', result_dirty)

    def test_missing_parameters(self):
        # Empty dict should fallback to defaults
        data = {}
        result = self.explainer.explain(data, format_type='markdown')
        self.assertIn('无特效', result)
        self.assertIn('无转场', result)
        self.assertIn('无运镜', result)
        self.assertIn('无背景音乐', result)

        # Missing BGM specifically
        data_missing_bgm = {
            'effects': ['特效1']
        }
        result_bgm = self.explainer.explain(data_missing_bgm, format_type='markdown')
        self.assertIn('特效1', result_bgm)
        self.assertIn('无背景音乐', result_bgm)

    def test_extreme_edge_cases(self):
        # Extremely deep/nested or strange dict items in lists, testing the filtering behavior
        data = {
            'effects': [None, 123, {'name': '好特效'}, {'wrong_key': '坏特效'}, []],
            'bgm': {'wrong_key': 'bgm'} # dict without name
        }
        result = self.explainer.explain(data, format_type='markdown')
        self.assertIn('好特效', result)
        self.assertNotIn('坏特效', result)
        self.assertIn('默认背景音乐', result)

        # Invalid format string fallback
        result_format = self.explainer.explain(data, format_type=123)
        self.assertIn('### 剪映草稿效果大白话总结', result_format) # Markdown is default

    def test_format_variations(self):
        data = {
            'effects': ['发光'],
            'transitions': ['溶解'],
            'camera_moves': ['推摄'],
            'bgm': '舒缓钢琴'
        }

        # JSON format
        result_json = self.explainer.explain(data, format_type='json')
        parsed = json.loads(result_json)
        self.assertIn('总结卡片', parsed)
        self.assertEqual(parsed['总结卡片']['花字特效'], '发光')
        self.assertEqual(parsed['总结卡片']['震屏转场'], '溶解')
        self.assertEqual(parsed['总结卡片']['KenBurns运镜'], '推摄')
        self.assertEqual(parsed['总结卡片']['BGM注入'], '舒缓钢琴')

        # HTML format
        result_html = self.explainer.explain(data, format_type='html')
        self.assertIn("<div class='draft-summary-card'>", result_html)
        self.assertIn("<strong>花字特效：</strong>发光", result_html)
        self.assertIn("<strong>震屏转场：</strong>溶解", result_html)
        self.assertIn("<strong>KenBurns运镜：</strong>推摄", result_html)
        self.assertIn("<strong>BGM注入：</strong>舒缓钢琴", result_html)

if __name__ == '__main__':
    unittest.main()
