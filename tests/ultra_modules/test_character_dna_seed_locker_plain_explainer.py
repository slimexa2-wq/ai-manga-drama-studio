import unittest
import json
from ultra_modules.character_dna_seed_locker_plain_explainer import CharacterDNALockerExplainer

class TestCharacterDNALockerExplainer(unittest.TestCase):

    def test_normal_full_data(self):
        """测试1：正常的完整数据传入"""
        locker = CharacterDNALockerExplainer(
            hair_color="银白色",
            eye_color="血红色",
            clothing="黑色战甲",
            style_suffix="赛博朋克风格",
            fixed_seed=12345
        )
        self.assertEqual(locker.hair_color, "银白色")
        self.assertEqual(locker.eye_color, "血红色")
        self.assertEqual(locker.clothing, "黑色战甲")
        self.assertEqual(locker.style_suffix, "赛博朋克风格")
        self.assertEqual(locker.fixed_seed, 12345)

        d = locker.to_dict()
        self.assertIn("【银白色头发】", d['summary'])
        self.assertIn("【血红色眼睛】", d['summary'])
        self.assertIn("身穿【黑色战甲】", d['summary'])
        self.assertIn("限定为【赛博朋克风格】", d['summary'])
        self.assertIn("锁定为【12345】", d['summary'])

    def test_missing_parameters_default_fallback(self):
        """测试2：完全缺参时的默认兜底行为"""
        locker = CharacterDNALockerExplainer()
        self.assertEqual(locker.hair_color, "黑色")
        self.assertEqual(locker.eye_color, "黑色")
        self.assertEqual(locker.clothing, "日常便服")
        self.assertEqual(locker.style_suffix, "二次元动漫风格")
        self.assertEqual(locker.fixed_seed, 42)

    def test_dirty_data_auto_healing(self):
        """测试3：脏数据自愈，如负数种子、字符串数字、甚至传入数组等"""
        locker = CharacterDNALockerExplainer(
            hair_color="   ", # 空格应被忽略
            eye_color=["红色", "蓝色"], # 传错了结构，应当使用默认
            clothing=None,
            style_suffix="null", # 无效字符串
            fixed_seed="-9999.9" # 负数且带小数点的字符串
        )

        self.assertEqual(locker.hair_color, "黑色")
        self.assertEqual(locker.eye_color, "黑色")
        self.assertEqual(locker.clothing, "日常便服")
        self.assertEqual(locker.style_suffix, "二次元动漫风格")
        # 负数浮点数转成正整数
        self.assertEqual(locker.fixed_seed, 9999)

    def test_extreme_boundary_conditions(self):
        """测试4：极端边界，包含极其极端的长字符串或深层嵌套，要求不崩溃且保证一定鲁棒性"""
        extreme_str = "红" * 10000
        locker = CharacterDNALockerExplainer(
            hair_color={"deep": {"deeper": "data"}},
            eye_color=extreme_str,
            fixed_seed=99999999999999999999999999999999999
        )

        self.assertEqual(locker.hair_color, "黑色") # 深层嵌套退回默认
        self.assertEqual(locker.eye_color, extreme_str)
        self.assertEqual(locker.fixed_seed, 99999999999999999999999999999999999)

    def test_export_format_integrity(self):
        """测试5：验证输出的JSON、Markdown、HTML结构完整性"""
        locker = CharacterDNALockerExplainer(hair_color="金色")

        # JSON
        json_out = locker.export_json()
        parsed = json.loads(json_out)
        self.assertEqual(parsed['hair_color'], "金色")
        self.assertIn("summary", parsed)

        # Markdown
        md_out = locker.export_markdown()
        self.assertIn("# 🧑‍🎨 角色视觉DNA锁定卡", md_out)
        self.assertIn("**发色**：金色", md_out)
        self.assertIn("💡 极简大白话总结", md_out)

        # HTML
        html_out = locker.export_html()
        self.assertIn("<div class=\"dna-card\"", html_out)
        self.assertIn("<strong>发色：</strong> 金色", html_out)
        self.assertIn("<strong>💡 极简大白话总结：</strong>", html_out)

if __name__ == '__main__':
    unittest.main()
