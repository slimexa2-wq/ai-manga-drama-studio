import unittest
import os
import wave
from unittest.mock import patch
from src.sfx_mixer import SFXMixer

class TestSFXMixer(unittest.TestCase):
    def setUp(self):
        self.mixer = SFXMixer(sample_rate=8000) # Lower sample rate for faster tests
        self.test_files = []

    def tearDown(self):
        self.mixer.cleanup()
        for f in self.test_files:
            if os.path.exists(f):
                os.remove(f)

    def _create_dummy_wav(self, filename: str):
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.mixer.sample_rate)
            wav_file.writeframesraw(b'\x00\x00' * 100) # 100 empty frames
        self.test_files.append(filename)

    def test_generate_impact_bass(self):
        filename = "test_impact.wav"
        self.mixer.generate_impact_bass(filename, duration=0.1)
        self.assertTrue(os.path.exists(filename))

        # Verify it's a valid wav
        with wave.open(filename, 'r') as w:
            self.assertEqual(w.getframerate(), self.mixer.sample_rate)
            self.assertEqual(w.getnchannels(), 1)
            self.assertEqual(w.getsampwidth(), 2)
            self.assertTrue(w.getnframes() > 0)

    def test_generate_sword_clash(self):
        filename = "test_sword.wav"
        self.mixer.generate_sword_clash(filename, duration=0.1)
        self.assertTrue(os.path.exists(filename))

    def test_generate_whoosh(self):
        filename = "test_whoosh.wav"
        self.mixer.generate_whoosh(filename, duration=0.1)
        self.assertTrue(os.path.exists(filename))

    @patch('shutil.which')
    def test_mix_sfx_no_ffmpeg_fallback(self, mock_which):
        mock_which.return_value = None # Simulate ffmpeg not installed
        base_audio = "test_base.wav"
        out_audio = "test_out.wav"

        self._create_dummy_wav(base_audio)
        self.test_files.append(out_audio)

        sfx_list = [{'file': 'dummy.wav', 'timestamp_ms': 1000}]

        result = self.mixer.mix_sfx(base_audio, out_audio, sfx_list)

        self.assertEqual(result, out_audio)
        self.assertTrue(os.path.exists(out_audio))

        # Check it's identical to base_audio (silently copied as fallback)
        with open(base_audio, 'rb') as f1, open(out_audio, 'rb') as f2:
            self.assertEqual(f1.read(), f2.read())

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_mix_sfx_ffmpeg_fails_fallback(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/ffmpeg"

        class MockResult:
            returncode = 1
            stderr = "Test Error"

        mock_run.return_value = MockResult()

        base_audio = "test_base2.wav"
        out_audio = "test_out2.wav"

        self._create_dummy_wav(base_audio)
        self.test_files.append(out_audio)

        sfx_list = [{'file': 'dummy.wav', 'timestamp_ms': 1000}]

        result = self.mixer.mix_sfx(base_audio, out_audio, sfx_list)

        self.assertEqual(result, out_audio)
        self.assertTrue(os.path.exists(out_audio))

        # Check it's identical to base_audio (silently copied as fallback)
        with open(base_audio, 'rb') as f1, open(out_audio, 'rb') as f2:
            self.assertEqual(f1.read(), f2.read())

if __name__ == '__main__':
    unittest.main()
