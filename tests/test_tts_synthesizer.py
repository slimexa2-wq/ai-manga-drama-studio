import unittest
import tempfile
import os
import wave
from src.tts_synthesizer import calculate_prosody, generate_offline_wav, process_storyboard

class TestTTSSynthesizer(unittest.TestCase):
    def test_calculate_prosody(self):
        # Test emotion modifiers
        prosody_angry = calculate_prosody("🔥暴怒", "男主")
        self.assertEqual(prosody_angry["rate"], "+15%")
        self.assertEqual(prosody_angry["pitch"], "+10Hz")

        prosody_sad = calculate_prosody("🎯悬念悲伤", "男主")
        self.assertEqual(prosody_sad["rate"], "-10%")
        self.assertEqual(prosody_sad["pitch"], "-10Hz")

        # Test role modifiers
        prosody_narrator = calculate_prosody("🎬平静", "旁白")
        self.assertEqual(prosody_narrator["rate"], "-5%")
        self.assertEqual(prosody_narrator["pitch"], "-5Hz")

    def test_generate_offline_wav(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, "test.wav")
            target_duration_ms = 1500

            generate_offline_wav(wav_path, target_duration_ms)

            self.assertTrue(os.path.exists(wav_path))

            # Verify WAV properties
            with wave.open(wav_path, 'r') as wav_file:
                self.assertEqual(wav_file.getnchannels(), 1)
                self.assertEqual(wav_file.getsampwidth(), 2)
                self.assertEqual(wav_file.getframerate(), 44100)

                # Verify exact duration (num frames = duration_s * framerate)
                expected_frames = int((target_duration_ms / 1000.0) * 44100)
                self.assertEqual(wav_file.getnframes(), expected_frames)

    def test_process_storyboard(self):
        storyboard = {
            "shots": [
                {
                    "shot_id": "SHOT_01",
                    "speaker": "男主",
                    "subtitle_text": "这是一个测试句子，字数不多。",
                    "emotion": "🔥暴怒",
                },
                {
                    "shot_id": "SHOT_02",
                    "speaker": "旁白",
                    "subtitle_text": "旁白的句子稍微长一点，用来测试时间是否增加。",
                    "emotion": "🎬平静",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            process_storyboard(storyboard, tmpdir)

            self.assertIn("total_duration_sec", storyboard)
            self.assertGreater(storyboard["total_duration_sec"], 0)

            # Check shot 1
            shot1 = storyboard["shots"][0]
            self.assertIn("audio_path", shot1)
            self.assertTrue(os.path.exists(shot1["audio_path"]))
            self.assertIn("duration_ms", shot1)
            self.assertGreater(shot1["duration_ms"], 0)
            self.assertEqual(shot1["start_ms"], 0)

            # Check shot 2
            shot2 = storyboard["shots"][1]
            self.assertIn("audio_path", shot2)
            self.assertTrue(os.path.exists(shot2["audio_path"]))
            self.assertIn("duration_ms", shot2)
            self.assertEqual(shot2["start_ms"], shot1["end_ms"])

if __name__ == '__main__':
    unittest.main()
