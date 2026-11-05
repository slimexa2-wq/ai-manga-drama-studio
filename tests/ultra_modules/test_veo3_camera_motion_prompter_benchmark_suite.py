import unittest
from ultra_modules.veo3_camera_motion_prompter_benchmark_suite import Veo3CameraMotionPrompter, Veo3BenchmarkSuite

class TestVeo3CameraMotionPrompterBenchmarkSuite(unittest.TestCase):

    def setUp(self):
        self.prompter = Veo3CameraMotionPrompter()
        self.suite = Veo3BenchmarkSuite(self.prompter)

    def test_normal_execution(self):
        """测试正常执行情况"""
        prompt = self.prompter.compile_prompt(
            motion_type="pan",
            intensity=0.9,
            subject="A cyberpunk hero",
            environment="Neon lit city"
        )
        self.assertIn("Camera motion: pan, fast and dynamic", prompt)
        self.assertIn("Subject: A cyberpunk hero", prompt)
        self.assertIn("Environment: Neon lit city", prompt)

    def test_missing_parameter_fallback(self):
        """测试缺失参数时的自动兜底机制（零配置容错）"""
        prompt = self.prompter.compile_prompt()

        # default motion is static, default intensity 0.5 -> slow and steady
        self.assertIn("Camera motion: static, slow and steady", prompt)
        self.assertIn("Subject: a cinematic scene", prompt)
        self.assertIn("Environment: in an unknown environment", prompt)

    def test_dirty_data_self_healing(self):
        """测试脏数据自愈（自动洗白、容错）"""
        prompt = self.prompter.compile_prompt(
            motion_type="   tILt  (down)  ", # Should self-heal to tilt
            intensity="very fast", # Should fallback to default float
            subject=["invalid", "type"],
            environment={"key": "value"}
        )
        self.assertIn("Camera motion: tilt, slow and steady", prompt) # default intensity is 0.5, speed modifier becomes slow and steady
        self.assertIn("Subject: a cinematic scene", prompt) # invalid type should fallback to default
        self.assertIn("Environment: in an unknown environment", prompt)

    def test_extreme_boundary_cases(self):
        """测试极端的边界案例，如超大字符串、超界浮点数"""
        large_string = "a" * 100000
        prompt = self.prompter.compile_prompt(
            motion_type="zoom",
            intensity=-9999.0, # should be clamped to 0.0
            subject=large_string,
            environment=large_string
        )
        self.assertIn("Camera motion: zoom, slow and steady", prompt) # 0.0 -> slow and steady
        self.assertTrue(len(prompt) > 200000)
        self.assertIn("a"*10000, prompt)

    def test_benchmark_synthetic_dataset(self):
        """测试合成数据集验证零崩溃与响应速度"""
        result = self.suite.run_benchmark(iterations=10000)

        # 验证没有发生崩溃
        self.assertTrue(result["success"], f"Benchmark failed: {result.get('error')}")
        self.assertTrue(result["zero_crash"])

        # 验证响应速度（毫秒级响应要求），平均处理时间不应过长
        # 10000 requests usually should be well within a few seconds (e.g. 5 seconds -> avg 0.5ms)
        self.assertLess(result["avg_time_ms"], 5.0, "Average response time is too slow, expected < 5.0 ms")

if __name__ == "__main__":
    unittest.main()
