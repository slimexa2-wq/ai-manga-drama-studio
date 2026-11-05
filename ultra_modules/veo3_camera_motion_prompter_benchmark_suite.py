import time
import random
import string
from typing import Dict, Any, List, Optional

class Veo3CameraMotionPrompter:
    """
    Google Veo 3 & Sora 2 专属电影级推拉摇移环绕运镜Prompt结构化编译器。
    支持自动脏数据清洗，零配置缺参容错。
    """
    VALID_MOTIONS = ["pan", "tilt", "zoom", "dolly", "track", "crane", "arc", "static"]

    def __init__(self, default_motion: str = "static", default_intensity: float = 0.5):
        self.default_motion = self._sanitize_motion(default_motion) or "static"
        self.default_intensity = self._sanitize_intensity(default_intensity)

    def _sanitize_string(self, text: Any) -> str:
        if not text or not isinstance(text, str):
            return ""
        # Basic sanitization to remove strange characters but keep alphanumeric and spaces
        return "".join(c for c in text if c.isprintable()).strip()

    def _sanitize_motion(self, motion: Any) -> str:
        if not motion or not isinstance(motion, str):
            return ""
        clean_motion = motion.lower().strip()
        if clean_motion in self.VALID_MOTIONS:
            return clean_motion

        # Self-healing for common misspellings or dirty data
        for valid in self.VALID_MOTIONS:
            if valid in clean_motion:
                return valid
        return ""

    def _sanitize_intensity(self, intensity: Any) -> float:
        try:
            val = float(intensity)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.5

    def compile_prompt(self,
                      motion_type: Optional[str] = None,
                      intensity: Optional[float] = None,
                      subject: Optional[str] = None,
                      environment: Optional[str] = None) -> str:

        m_type = self._sanitize_motion(motion_type) or self.default_motion
        m_intensity = self._sanitize_intensity(intensity) if intensity is not None else self.default_intensity

        clean_subject = self._sanitize_string(subject) or "a cinematic scene"
        clean_env = self._sanitize_string(environment) or "in an unknown environment"

        # Map intensity to cinematic terms for Veo 3 / Sora 2
        speed_modifier = "slow and steady"
        if m_intensity > 0.8:
            speed_modifier = "fast and dynamic"
        elif m_intensity > 0.5:
            speed_modifier = "moderate and smooth"

        prompt = f"Camera motion: {m_type}, {speed_modifier}. Subject: {clean_subject}. Environment: {clean_env}. High quality, cinematic lighting, 8k resolution."
        return prompt


class Veo3BenchmarkSuite:
    """
    合成数据集验证夹具 (Synthetic Fixtures) 与性能基准验证
    """
    def __init__(self, prompter: Veo3CameraMotionPrompter):
        self.prompter = prompter

    def _generate_garbage_string(self, length: int) -> str:
        return ''.join(random.choices(string.printable + '你我他💩🔥\x00\x01\x02', k=length))

    def generate_synthetic_fixture(self) -> Dict[str, Any]:
        """
        生成单个合成测试用例，可能是正常的，也可能是极端的、含脏数据的
        """
        scenario = random.randint(1, 5)

        if scenario == 1: # Normal
            return {
                "motion_type": random.choice(Veo3CameraMotionPrompter.VALID_MOTIONS),
                "intensity": random.uniform(0.1, 1.0),
                "subject": "A futuristic cyborg",
                "environment": "Cyberpunk city at night"
            }
        elif scenario == 2: # Missing params
            return {
                "motion_type": None,
                "intensity": None,
                "subject": None,
                "environment": None
            }
        elif scenario == 3: # Dirty data (Types)
            return {
                "motion_type": 123,
                "intensity": "very fast",
                "subject": ["not", "a", "string"],
                "environment": {"key": "value"}
            }
        elif scenario == 4: # Extreme boundary / Garbage strings
            return {
                "motion_type": self._generate_garbage_string(50),
                "intensity": -9999.99, # Will be clamped
                "subject": self._generate_garbage_string(10000), # Very large payload
                "environment": self._generate_garbage_string(10000)
            }
        else: # Partially dirty
            return {
                "motion_type": "   pAn  (fast)  ", # Should self-heal to 'pan'
                "intensity": 0.9,
                "subject": "",
                "environment": "    "
            }

    def run_benchmark(self, iterations: int = 10000) -> Dict[str, Any]:
        """
        验证零崩溃与毫秒级响应
        """
        start_time = time.time()
        successful_compilations = 0

        for _ in range(iterations):
            fixture = self.generate_synthetic_fixture()
            try:
                # Should never crash due to zero-configuration fault tolerance
                prompt = self.prompter.compile_prompt(
                    motion_type=fixture.get("motion_type"),
                    intensity=fixture.get("intensity"),
                    subject=fixture.get("subject"),
                    environment=fixture.get("environment")
                )
                if prompt:
                    successful_compilations += 1
            except Exception as e:
                # If it crashes, the benchmark fails the zero-crash guarantee
                return {
                    "success": False,
                    "error": str(e),
                    "crashed_on": fixture
                }

        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / iterations

        return {
            "success": True,
            "iterations": iterations,
            "total_time_ms": total_time_ms,
            "avg_time_ms": avg_time_ms,
            "zero_crash": successful_compilations == iterations
        }
