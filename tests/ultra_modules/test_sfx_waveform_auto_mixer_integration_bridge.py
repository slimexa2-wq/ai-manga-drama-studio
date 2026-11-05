import unittest
from ultra_modules.sfx_waveform_auto_mixer_integration_bridge import SFXWaveformAutoMixerIntegrationBridge

class TestSFXWaveformAutoMixerIntegrationBridge(unittest.TestCase):

    def test_normal_schema_mapping(self):
        payload = {
            "items": [
                {
                    "id": "item1",
                    "type": "bass_drop",
                    "duration": 2.5,
                    "intensity": 0.9
                }
            ]
        }
        bridged = SFXWaveformAutoMixerIntegrationBridge.bridge_payload(payload)
        self.assertEqual(bridged["bridge_status"], "success")
        self.assertEqual(len(bridged["bridged_items"]), 1)
        item = bridged["bridged_items"][0]
        self.assertEqual(item["id"], "item1")
        self.assertEqual(item["type"], "bass_drop")
        self.assertEqual(item["duration"], 2.5)
        self.assertEqual(item["intensity"], 0.9)

    def test_legacy_schema_mapping(self):
        payload = {
            "sfx_list": [
                {
                    "sfx_id": "leg1",
                    "effect_type": "metal_clash",
                    "length": 1.5,
                    "volume": 0.7
                }
            ]
        }
        bridged = SFXWaveformAutoMixerIntegrationBridge.bridge_payload(payload)
        item = bridged["bridged_items"][0]
        self.assertEqual(item["id"], "leg1")
        self.assertEqual(item["type"], "sword_clash") # "metal_clash" -> "sword_clash"
        self.assertEqual(item["duration"], 1.5)
        self.assertEqual(item["intensity"], 0.7)

    def test_missing_parameters_fallback(self):
        payload = {
            "tracks": [
                {} # Empty item
            ]
        }
        bridged = SFXWaveformAutoMixerIntegrationBridge.bridge_payload(payload)
        item = bridged["bridged_items"][0]
        self.assertIsNotNone(item["id"])
        self.assertEqual(item["type"], "whoosh") # Default
        self.assertEqual(item["duration"], 1.0)  # Default
        self.assertEqual(item["intensity"], 0.8) # Default

    def test_dirty_data_self_healing(self):
        payload = {
            "data": [
                {
                    "uuid": 12345,
                    "sound_type": 999,
                    "time": "invalid_string",
                    "loudness": None
                }
            ]
        }
        bridged = SFXWaveformAutoMixerIntegrationBridge.bridge_payload(payload)
        item = bridged["bridged_items"][0]
        self.assertEqual(item["id"], "12345")
        self.assertEqual(item["type"], "whoosh")
        self.assertEqual(item["duration"], 1.0)
        self.assertEqual(item["intensity"], 0.8)

    def test_extreme_boundary_conditions(self):
        # Testing very large numbers and negative values
        payload = {
            "items": [
                {
                    "id": "ext1",
                    "type": "bass_drop",
                    "duration": 9999.9, # Should cap at 30.0
                    "intensity": 500.0  # Should cap at 1.0
                },
                {
                    "id": "ext2",
                    "type": "sword_clash",
                    "duration": -5.0,  # Should fallback to default
                    "intensity": -1.0  # Should fallback to default
                }
            ]
        }
        bridged = SFXWaveformAutoMixerIntegrationBridge.bridge_payload(payload)
        items = bridged["bridged_items"]

        self.assertEqual(items[0]["duration"], 30.0)
        self.assertEqual(items[0]["intensity"], 1.0)

        self.assertEqual(items[1]["duration"], 1.0)
        self.assertEqual(items[1]["intensity"], 0.8)

    def test_invalid_payload_fallback(self):
        # Pass something entirely invalid
        bridged = SFXWaveformAutoMixerIntegrationBridge.bridge_payload(None)
        self.assertEqual(bridged["bridge_status"], "success")
        self.assertEqual(len(bridged["bridged_items"]), 0)

        bridged2 = SFXWaveformAutoMixerIntegrationBridge.bridge_payload("not_a_dict")
        self.assertEqual(bridged2["bridge_status"], "success")
        self.assertEqual(len(bridged2["bridged_items"]), 0)

if __name__ == '__main__':
    unittest.main()
