import unittest
from ultra_modules.veo3_camera_motion_prompter_core_engine import compile_camera_prompt

class TestCameraMotionPrompter(unittest.TestCase):

    def test_normal_generation_veo3(self):
        prompt = compile_camera_prompt(
            subject="a futuristic cyberpunk city",
            motion_type="pan",
            direction="right",
            speed="slow",
            shot_type="extreme_wide_shot",
            lens="14mm",
            lighting="neon lighting",
            engine="veo3"
        )
        self.assertIn("[Veo 3 Optimized]", prompt)
        self.assertIn("Extreme Wide Shot", prompt)
        self.assertIn("a futuristic cyberpunk city", prompt)
        self.assertIn("Camera Motion: Pan Right at Slow speed", prompt)
        self.assertIn("Lens: 14Mm", prompt)
        self.assertIn("Lighting: Neon Lighting", prompt)

    def test_normal_generation_sora2(self):
        prompt = compile_camera_prompt(
            subject="a gentle stream in a forest",
            motion_type="dolly",
            direction="forward",
            speed="medium",
            shot_type="medium_shot",
            lens="50mm",
            lighting="natural sunlight",
            engine="sora2"
        )
        self.assertIn("(Sora 2 Cinematic)", prompt)
        self.assertIn("Medium Shot", prompt)
        self.assertIn("a gentle stream in a forest", prompt)
        self.assertIn("Camera Motion: Dolly Forward at Medium speed", prompt)

    def test_missing_params_fallback(self):
        prompt = compile_camera_prompt()
        self.assertIn("[Veo 3 Optimized]", prompt) # Default engine
        self.assertIn("Wide Shot", prompt) # Default shot
        self.assertIn("a stunning cinematic scene", prompt) # Default subject
        self.assertIn("Static Camera", prompt) # Default motion
        self.assertIn("Lens: 35Mm", prompt) # Default lens
        self.assertIn("Lighting: Cinematic Lighting", prompt) # Default lighting

    def test_dirty_data_cleansing(self):
        prompt = compile_camera_prompt(
            subject=12345, # Invalid type, should fallback
            motion_type=["dolly"], # Invalid type, should fallback
            direction={"dir": "forward"}, # Invalid type, should fallback
            speed=3.14, # Invalid type, should fallback
            shot_type=None, # None, should fallback
            lens=False, # Invalid type, should fallback
            lighting=object(), # Invalid type, should fallback
            engine=999 # Invalid type, should fallback
        )
        self.assertIn("[Veo 3 Optimized]", prompt)
        self.assertIn("Wide Shot", prompt)
        self.assertIn("a stunning cinematic scene", prompt)
        self.assertIn("Static Camera", prompt)

    def test_invalid_choices_fallback(self):
        prompt = compile_camera_prompt(
            motion_type="barrel_roll", # Not a valid choice
            direction="diagonal_up", # Not a valid choice
            speed="warp_speed", # Not a valid choice
            shot_type="microscopic_shot", # Not a valid choice
            engine="midjourney_v6" # Not a valid choice
        )
        self.assertIn("[Veo 3 Optimized]", prompt)
        self.assertIn("Wide Shot", prompt)
        self.assertIn("Static Camera", prompt)

    def test_extreme_edge_cases(self):
        prompt = compile_camera_prompt(
            subject="   \t\n  ", # Whitespace string
            motion_type="", # Empty string
            engine="   " # Whitespace string
        )
        self.assertIn("[Veo 3 Optimized]", prompt)
        self.assertIn("Wide Shot", prompt)
        self.assertIn("a stunning cinematic scene", prompt)
        self.assertIn("Static Camera", prompt)

if __name__ == "__main__":
    unittest.main()
