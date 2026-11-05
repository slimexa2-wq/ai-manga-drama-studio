import unittest
from ultra_modules.dialogue_lip_sync_timer_integration_bridge import DialogueLipSyncTimerBridge

class TestDialogueLipSyncTimerBridge(unittest.TestCase):
    def test_normal_v2_schema(self):
        """测试使用标准 V2 schema 的正常情况"""
        payload = {
            "dialogue_text": "你好，世界！",
            "audio_duration_ms": 2000.0,
            "waveform_peaks": [500.0, 1500.0],
            "punctuation_pause_ms": 500.0
        }
        result = DialogueLipSyncTimerBridge.calculate_sync(payload)

        self.assertEqual(result["schema_version"], "v2")
        self.assertEqual(result["dialogue_text"], "你好，世界！")
        self.assertEqual(result["audio_duration_ms"], 2000.0)
        self.assertEqual(result["waveform_peaks"], [500.0, 1500.0])
        self.assertEqual(result["punctuation_pause_ms"], 500.0)
        # base_duration = 2000.0, pauses = 2 (，和！) * 500.0 = 1000.0 -> total 3000.0
        self.assertEqual(result["calculated_storyboard_duration_ms"], 3000.0)
        self.assertFalse(result["is_fallback_used"])

    def test_schema_backward_compatibility(self):
        """测试旧版本字段静默映射兼容"""
        payload = {
            "text": "Hello World.",
            "voice_length": 1500.0,
            "peaks": [100.0, 1000.0],
            "pause": 400.0
        }
        result = DialogueLipSyncTimerBridge.calculate_sync(payload)

        self.assertEqual(result["dialogue_text"], "Hello World.")
        self.assertEqual(result["audio_duration_ms"], 1500.0)
        self.assertEqual(result["waveform_peaks"], [100.0, 1000.0])
        self.assertEqual(result["punctuation_pause_ms"], 400.0)
        # base_duration = 1500.0, pauses = 1 (.) * 400.0 = 400.0 -> total 1900.0
        self.assertEqual(result["calculated_storyboard_duration_ms"], 1900.0)

    def test_missing_parameters_fallback(self):
        """测试缺参情况下的合理默认值兜底计算（基于字数估算）"""
        payload = {
            "dialogue_text": "这是一个测试！"
        }
        result = DialogueLipSyncTimerBridge.calculate_sync(payload)

        # 字数 7, base_duration = 7 * 250.0 = 1750.0
        # 标点 1 (！), default pause = 500.0 -> total 2250.0
        self.assertEqual(result["calculated_storyboard_duration_ms"], 2250.0)
        self.assertEqual(result["audio_duration_ms"], 0.0)
        self.assertTrue(result["is_fallback_used"])

    def test_dirty_data_self_healing(self):
        """测试脏数据自愈（无效类型、负数等清洗）"""
        payload = {
            "dialogue_text": 12345,  # 应该转成 string "12345"
            "audio_duration_ms": "invalid_audio",
            "waveform_peaks": [100, "bad_peak", -50],
            "punctuation_pause_ms": -100  # 应该重置为 500.0
        }
        result = DialogueLipSyncTimerBridge.calculate_sync(payload)

        self.assertEqual(result["dialogue_text"], "12345")
        self.assertEqual(result["audio_duration_ms"], 0.0)
        self.assertEqual(result["waveform_peaks"], [100.0, -50.0])
        self.assertEqual(result["punctuation_pause_ms"], 500.0)

        # 字数 5, base_duration = 5 * 250.0 = 1250.0
        # 无标点 -> total 1250.0
        self.assertEqual(result["calculated_storyboard_duration_ms"], 1250.0)
        self.assertTrue(result["is_fallback_used"])

    def test_extreme_boundaries(self):
        """测试极端边界条件（如空输入、超长峰值等）"""
        # 1. 没有任何输入
        result_empty = DialogueLipSyncTimerBridge.calculate_sync(None)
        self.assertEqual(result_empty["calculated_storyboard_duration_ms"], 1000.0)
        self.assertTrue(result_empty["is_fallback_used"])

        # 2. peak 时间超过基础计算时间
        payload_peak = {
            "dialogue_text": "短",
            "audio_duration_ms": 100.0,
            "waveform_peaks": [5000.0]
        }
        result_peak = DialogueLipSyncTimerBridge.calculate_sync(payload_peak)
        # 预期时长必须包含最后的 peak，所以是 5000.0
        self.assertEqual(result_peak["calculated_storyboard_duration_ms"], 5000.0)

    def test_normalize_payload_precedence(self):
        """测试字段映射的优先级（标准字段优先）"""
        payload = {
            "dialogue_text": "标准文本",
            "text": "旧版文本"
        }
        normalized = DialogueLipSyncTimerBridge.normalize_payload(payload)
        self.assertEqual(normalized["dialogue_text"], "标准文本")

if __name__ == "__main__":
    unittest.main()
