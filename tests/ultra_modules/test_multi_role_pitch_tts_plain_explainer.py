import unittest
import json
from ultra_modules.multi_role_pitch_tts_plain_explainer import MultiRolePitchTTSPlainExplainer

class TestMultiRolePitchTTSPlainExplainer(unittest.TestCase):
    def setUp(self):
        self.explainer = MultiRolePitchTTSPlainExplainer()

    def test_normal_standard_data(self):
        # 1. 正常标准数据
        data = [
            {"role": "旁白", "pitch": 1.0, "speed": 1.0, "emotion": "平静", "duration_ms": 3000},
            {"role": "男主", "pitch": 1.5, "speed": 1.3, "emotion": "愤怒", "duration_ms": 2500},
            {"role": "女主", "pitch": 0.5, "speed": 0.6, "emotion": "悲伤", "duration_ms": 4000}
        ]

        result_json = self.explainer.explain(data, fmt="json")
        result = json.loads(result_json)

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["data"]), 3)

        # 验证大白话描述
        desc_narrator = result["data"][0]["description"]
        self.assertIn("角色【旁白】", desc_narrator)
        self.assertIn("平静", desc_narrator)
        self.assertIn("音调正常", desc_narrator)
        self.assertIn("语速正常", desc_narrator)

        desc_hero = result["data"][1]["description"]
        self.assertIn("角色【男主】", desc_hero)
        self.assertIn("愤怒", desc_hero)
        self.assertIn("音调偏高", desc_hero)
        self.assertIn("语速偏快", desc_hero)

        desc_heroine = result["data"][2]["description"]
        self.assertIn("角色【女主】", desc_heroine)
        self.assertIn("悲伤", desc_heroine)
        self.assertIn("音调偏低", desc_heroine)
        self.assertIn("语速偏慢", desc_heroine)

    def test_dirty_data_self_healing(self):
        # 2. 脏数据自愈 (包含不能转换成数字的字符串, 负数情况, 以及各种异常类型)
        data = [
            {"role": "反派", "pitch": "非常高", "speed": None, "emotion": "得意", "duration_ms": "很久"},
            {"role": "路人", "pitch": "-1.5", "speed": "-2.0", "emotion": "", "duration_ms": -100},
            "这不是一个字典",
            123,
            {"role": None, "pitch": [], "speed": {}, "emotion": 123, "duration_ms": []}
        ]

        result_md = self.explainer.explain(data, fmt="markdown")

        # 反派应该使用默认pitch=1.0, speed=1.0, duration=0
        self.assertIn("- **反派**: 角色【反派】以得意的情感发音，音调正常(1.0)，语速正常(1.0)，预计耗时0毫秒。", result_md)

        # 路人的负数音高和语速应该取绝对值, 情感为空走默认，负数时长归零
        self.assertIn("- **路人**: 角色【路人】以平静的情感发音，音调偏高(1.5)，语速偏快(2.0)，预计耗时0毫秒。", result_md)

        # 非法数据如列表/字典，兜底为默认值
        self.assertIn("- **未知角色**: 角色【未知角色】以平静的情感发音，音调正常(1.0)，语速正常(1.0)，预计耗时0毫秒。", result_md)

    def test_missing_parameters_default_fallback(self):
        # 3. 缺参默认兜底
        data = [{}]

        result_html = self.explainer.explain(data, fmt="html")

        self.assertIn("<strong>未知角色</strong>", result_html)
        self.assertIn("音调正常(1.0)", result_html)
        self.assertIn("语速正常(1.0)", result_html)
        self.assertIn("平静", result_html)
        self.assertIn("0毫秒", result_html)

    def test_extreme_edge_cases(self):
        # 4. 极端边界情况
        data = [
            {"role": "   ", "speed": 0, "duration_ms": 0.5},  # 空白角色名 -> 未知角色, 语速0 -> 默认语速1.0
            {"pitch": 1.2},  # pitch等于1.2，没有大于1.2，所以应该是正常
            {"pitch": 0.8},  # pitch等于0.8，没有小于0.8，所以应该是正常
            {"speed": 1.2},
            {"speed": 0.8}
        ]

        result = self.explainer.explain(data, fmt="raw")

        # 第一条，空白角色名
        self.assertEqual(result[0]["role"], "未知角色")
        self.assertEqual(result[0]["details"]["speed"], 1.0) # 语速为0被兜底为1.0
        self.assertEqual(result[0]["details"]["duration_ms"], 0) # 0.5转换成int为0

        # pitch 边界
        self.assertIn("音调正常(1.2)", result[1]["description"])
        self.assertIn("音调正常(0.8)", result[2]["description"])

        # speed 边界
        self.assertIn("语速正常(1.2)", result[3]["description"])
        self.assertIn("语速正常(0.8)", result[4]["description"])

    def test_non_list_invalid_input_types(self):
        # 5. 非列表非法输入类型 (含字符串JSON)
        # null / None
        self.assertEqual(self.explainer.explain(None, fmt="raw"), [])

        # 单个字典自动转列表
        single_dict_res = self.explainer.explain({"role": "单人"}, fmt="raw")
        self.assertEqual(len(single_dict_res), 1)
        self.assertEqual(single_dict_res[0]["role"], "单人")

        # 字符串JSON (列表)
        json_str_list = '[{"role": "JSON角色"}]'
        json_res = self.explainer.explain(json_str_list, fmt="raw")
        self.assertEqual(len(json_res), 1)
        self.assertEqual(json_res[0]["role"], "JSON角色")

        # 字符串JSON (单字典)
        json_str_dict = '{"role": "JSON字典"}'
        json_dict_res = self.explainer.explain(json_str_dict, fmt="raw")
        self.assertEqual(len(json_dict_res), 1)
        self.assertEqual(json_dict_res[0]["role"], "JSON字典")

        # 乱码字符串
        self.assertEqual(self.explainer.explain("不是JSON的乱七八糟", fmt="raw"), [])
        self.assertEqual(self.explainer.explain(123, fmt="raw"), [])

    def test_empty_results_markdown_html(self):
        # 补充：覆盖空的 Markdown 和 HTML
        md = self.explainer.explain([], fmt="markdown")
        self.assertIn("暂无有效角色配置", md)

        html = self.explainer.explain([], fmt="html")
        self.assertIn("暂无有效角色配置", html)

if __name__ == '__main__':
    unittest.main()
