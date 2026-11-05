import unittest
import json
from ultra_modules.veo3_camera_motion_prompter_integration_bridge import Veo3Sora2PrompterBridge

class TestVeo3Sora2PrompterBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = Veo3Sora2PrompterBridge()

    def test_normal_new_schema(self):
        # Test 1: Normal behavior with modern schema
        data = {
            "camera_type": "Drone",
            "motion": "Flyover",
            "speed": "Fast",
            "focus": "Landscape"
        }
        result = self.bridge.convert_and_compile(data)
        self.assertEqual(result, "Camera: Drone shot, Motion: flyover, Speed: fast, Focus: Landscape.")

    def test_normal_old_schema(self):
        # Test 2: Normal behavior with old schema (type, movement, velocity, focus_on)
        data = {
            "type": "Handheld",
            "movement": "Zoom in",
            "velocity": "Medium",
            "focus_on": "Character face"
        }
        result = self.bridge.convert_and_compile(data)
        self.assertEqual(result, "Camera: Handheld shot, Motion: zoom in, Speed: medium, Focus: Character face.")

    def test_missing_parameters_fallback(self):
        # Test 3: Missing parameters fallback to defaults
        data = {}
        result = self.bridge.convert_and_compile(data)
        self.assertEqual(result, "Camera: Cinematic shot, Motion: pan right, Speed: slow, Focus: subject.")

    def test_dirty_data_self_healing(self):
        # Test 4: Dirty data self healing (e.g. wrong types)
        data = {
            "camera_type": 123, # should fallback to default string
            "motion": ["invalid"], # should fallback
            "speed": None, # should fallback
            "focus": {"bad": "data"} # should fallback
        }
        result = self.bridge.convert_and_compile(data)
        self.assertEqual(result, "Camera: Cinematic shot, Motion: pan right, Speed: slow, Focus: subject.")

        # Test parsing valid json string
        valid_json_str = json.dumps({"camera_type": "macro", "motion": "tilt up", "speed": "slow", "focus": "flower"})
        result2 = self.bridge.convert_and_compile(valid_json_str)
        self.assertEqual(result2, "Camera: Macro shot, Motion: tilt up, Speed: slow, Focus: flower.")

    def test_extreme_boundary_cases(self):
        # Test 5: Extreme boundary cases like invalid JSON string, completely unexpected types
        result1 = self.bridge.convert_and_compile("{invalid json}")
        self.assertEqual(result1, "Camera: Cinematic shot, Motion: pan right, Speed: slow, Focus: subject.")

        result2 = self.bridge.convert_and_compile(None)
        self.assertEqual(result2, "Camera: Cinematic shot, Motion: pan right, Speed: slow, Focus: subject.")

        result3 = self.bridge.convert_and_compile(12345)
        self.assertEqual(result3, "Camera: Cinematic shot, Motion: pan right, Speed: slow, Focus: subject.")

        # test empty values
        data = {
            "camera_type": "   ",
            "motion": "  ",
            "speed": "  ",
            "focus": "  "
        }
        result4 = self.bridge.convert_and_compile(data)
        self.assertEqual(result4, "Camera:  shot, Motion: , Speed: , Focus: .")

        # explicitly test speed fallback
        data2 = {
            "speed": 123
        }
        result5 = self.bridge.convert_and_compile(data2)
        self.assertEqual(result5, "Camera: Cinematic shot, Motion: pan right, Speed: slow, Focus: subject.")

if __name__ == '__main__': # pragma: no cover
    unittest.main()
