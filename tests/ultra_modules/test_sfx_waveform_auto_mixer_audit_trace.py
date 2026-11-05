import unittest
from ultra_modules.sfx_waveform_auto_mixer_audit_trace import SFXAutoMixerAuditTrace

class TestSFXAutoMixerAuditTrace(unittest.TestCase):

    def test_normal_operation(self):
        mixer = SFXAutoMixerAuditTrace(base_volume=1.0)
        tracks = [
            {"path": "drum.wav", "volume": 1.0, "type": "bass_shake"},
            {"path": "sword.wav", "volume": 0.8, "type": "sword_clash"},
            {"path": "wind.wav", "volume": 0.5, "type": "transition_howl"},
            {"path": "voice.wav", "volume": 1.2, "type": "normal"}
        ]
        cmd = mixer.generate_mix_command(tracks, "final.wav")
        self.assertIn("ffmpeg", cmd)
        self.assertIn("-i \"drum.wav\"", cmd)
        self.assertIn("-i \"sword.wav\"", cmd)
        self.assertIn("-i \"wind.wav\"", cmd)
        self.assertIn("-i \"voice.wav\"", cmd)
        self.assertIn("bass=g=5:f=100", cmd)
        self.assertIn("treble=g=5:f=5000", cmd)
        self.assertIn("chorus=", cmd)
        self.assertIn("amix=inputs=4", cmd)

        audit = mixer.get_audit_trail()
        self.assertEqual(audit[0]["action"], "INIT")
        self.assertEqual(audit[-1]["action"], "GENERATE_COMMAND")

    def test_dirty_data_auto_healing(self):
        # Invalid base volume type
        mixer = SFXAutoMixerAuditTrace(base_volume="invalid_string")
        self.assertEqual(mixer.base_volume, 1.0)

        # Negative and excessive volume healing
        tracks = [
            {"path": "track1.wav", "volume": -5.0},
            {"path": "track2.wav", "volume": 50.0},
            {"path": "track3.wav", "volume": "not_a_number"}
        ]
        cmd = mixer.generate_mix_command(tracks, "output.wav")

        audit = mixer.get_audit_trail()
        heal_volume_actions = [a for a in audit if a["action"] == "HEAL_VOLUME"]

        self.assertIn("-i \"track1.wav\"", cmd)
        self.assertIn("-i \"track2.wav\"", cmd)
        self.assertIn("-i \"track3.wav\"", cmd)

        # 1 for base_volume + 3 for tracks = 4
        self.assertEqual(len(heal_volume_actions), 4)

    def test_missing_parameter_fallbacks(self):
        mixer = SFXAutoMixerAuditTrace()
        # Missing output file and tracks
        cmd = mixer.generate_mix_command(None, None)
        self.assertIn("anullsrc=r=44100:cl=stereo -t 1 output_mix.wav", cmd)

        audit = mixer.get_audit_trail()
        self.assertTrue(any(a["action"] == "HEAL_OUTPUT_FILE" for a in audit))
        self.assertTrue(any(a["action"] == "HEAL_TRACKS" for a in audit))
        self.assertTrue(any(a["action"] == "GENERATE_COMMAND" and a["details"]["type"] == "fallback_empty" for a in audit))

    def test_extreme_boundary_and_edge_cases(self):
        mixer = SFXAutoMixerAuditTrace()
        # Invalid tracks structure, non-dict elements, invalid paths
        tracks = [
            "not_a_dict",
            123,
            {"path": None, "volume": 1.0},
            {"path": "   ", "volume": 1.0},
            {"path": "", "volume": 1.0},
            {"path": "valid.wav", "volume": 1.0}
        ]
        cmd = mixer.generate_mix_command(tracks, "test_output.wav")

        audit = mixer.get_audit_trail()
        self.assertTrue(any(a["action"] == "HEAL_TRACK" for a in audit))
        self.assertTrue(any(a["action"] == "HEAL_PATH" for a in audit))

        # Only valid.wav should be processed (and maybe default_silence.wav but those get deduplicated or ignored properly in the final command inputs logic based on deduplication)
        # Actually our deduplication skips default_silence.wav from deduplication logic, but it adds it to processed_tracks. Let's check how many were added.
        process_action = next(a for a in audit if a["action"] == "PROCESS_TRACKS")

        # valid.wav + 3x default_silence.wav
        self.assertEqual(process_action["details"]["count"], 4)

        self.assertIn("amix=inputs=4", cmd)
        self.assertIn("-i \"valid.wav\"", cmd)
        self.assertIn("-i \"default_silence.wav\"", cmd)

    def test_track_deduplication(self):
        mixer = SFXAutoMixerAuditTrace()
        tracks = [
            {"path": "same.wav", "volume": 1.0},
            {"path": "same.wav", "volume": 0.5},
            {"path": "different.wav", "volume": 1.0}
        ]
        cmd = mixer.generate_mix_command(tracks, "dedup_output.wav")

        audit = mixer.get_audit_trail()
        self.assertTrue(any(a["action"] == "DEDUPLICATE_TRACK" and a["details"]["path"] == "same.wav" for a in audit))

        self.assertIn("amix=inputs=2", cmd)
        self.assertIn("-i \"same.wav\"", cmd)
        self.assertIn("-i \"different.wav\"", cmd)

        process_action = next(a for a in audit if a["action"] == "PROCESS_TRACKS")
        self.assertEqual(process_action["details"]["count"], 2)

if __name__ == '__main__':
    unittest.main()
