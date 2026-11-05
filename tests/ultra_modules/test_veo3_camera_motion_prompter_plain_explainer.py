import unittest
import json
from ultra_modules.veo3_camera_motion_prompter_plain_explainer import Veo3CameraMotionPrompterPlainExplainer

class TestVeo3CameraMotionPrompterPlainExplainer(unittest.TestCase):
    def setUp(self):
        self.explainer = Veo3CameraMotionPrompterPlainExplainer()

    def test_normal_data_markdown(self):
        """Test well-formed data outputting to markdown."""
        data = {
            'pan': 5.0,
            'tilt': -2.5,
            'zoom': 1.0,
            'roll': 0.0,
            'speed': 1.5,
            'focus': '人脸锁定'
        }
        result = self.explainer.explain(data, format='markdown')
        self.assertIn("镜头向右平移（强度: 5.0）", result)
        self.assertIn("镜头向下摇摄（强度: 2.5）", result)
        self.assertIn("镜头推进，画面放大（强度: 1.0）", result)
        self.assertIn("*运镜节奏:* 快速", result)
        self.assertIn("*焦点策略:* 人脸锁定", result)

    def test_missing_parameters_fallback(self):
        """Test missing parameters falling back to default values."""
        data = {'pan': 2.0} # Missing tilt, zoom, roll, speed, focus
        result = self.explainer.explain(data, format='json')
        parsed = json.loads(result)
        self.assertEqual(parsed['raw_sanitized']['tilt'], 0.0)
        self.assertEqual(parsed['raw_sanitized']['zoom'], 0.0)
        self.assertEqual(parsed['raw_sanitized']['roll'], 0.0)
        self.assertEqual(parsed['raw_sanitized']['speed'], 1.0)
        self.assertEqual(parsed['raw_sanitized']['focus'], '自动对焦')
        self.assertEqual(parsed['speed'], '正常')

    def test_dirty_data_self_healing(self):
        """Test invalid types and negative speed being self-healed."""
        data = {
            'pan': "10",       # string instead of float
            'tilt': None,      # None instead of float
            'zoom': [1, 2],    # list instead of float
            'speed': "slow",   # string instead of float
            'focus': ""        # empty string
        }
        result = self.explainer.explain(data, format='json')
        parsed = json.loads(result)
        self.assertEqual(parsed['raw_sanitized']['pan'], 10.0)
        self.assertEqual(parsed['raw_sanitized']['tilt'], 0.0)
        self.assertEqual(parsed['raw_sanitized']['zoom'], 0.0)
        self.assertEqual(parsed['raw_sanitized']['speed'], 0.5)
        self.assertEqual(parsed['raw_sanitized']['focus'], '自动对焦')

        # Test negative speed
        data_neg = {'speed': -5.0}
        result_neg = self.explainer.explain(data_neg, format='json')
        parsed_neg = json.loads(result_neg)
        self.assertEqual(parsed_neg['raw_sanitized']['speed'], 1.0)

    def test_extreme_boundary_none_input(self):
        """Test passing None or unexpected types as the input."""
        result = self.explainer.explain(None, format='html')
        self.assertIn("镜头保持固定，无移动", result)
        self.assertIn("<strong>运镜节奏:</strong> 正常", result)
        self.assertIn("<strong>焦点:</strong> 自动对焦", result)

        result2 = self.explainer.explain("random string", format='markdown')
        self.assertIn("镜头保持固定，无移动", result2)

    def test_html_and_json_format_output(self):
        """Test outputting to HTML and JSON formats specifically."""
        data = {'roll': -3.0}

        html_result = self.explainer.explain(data, format='html')
        self.assertTrue(html_result.startswith('<div class="camera-motion-card">'))
        self.assertIn("<li>镜头向左侧翻滚倾斜（强度: 3.0）</li>", html_result)

        json_result = self.explainer.explain(data, format='json')
        parsed = json.loads(json_result)
        self.assertIn("镜头向左侧翻滚倾斜（强度: 3.0）", parsed['details'])

        # Test invalid format fallback to markdown
        invalid_format_result = self.explainer.explain(data, format='pdf')
        self.assertTrue(invalid_format_result.startswith("### 🎬 Veo 3 运镜大白话解析卡"))

if __name__ == '__main__':
    unittest.main()
