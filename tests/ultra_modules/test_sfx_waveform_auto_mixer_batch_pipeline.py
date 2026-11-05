import unittest
import os
import shutil
import wave
from ultra_modules.sfx_waveform_auto_mixer_batch_pipeline import (
    SFXWaveformAutoMixerBatchPipeline,
    SFXGenerator,
    FFmpegAutoMixer
)

class TestSFXWaveformAutoMixerBatchPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = SFXWaveformAutoMixerBatchPipeline(max_workers=2)

    def tearDown(self):
        if os.path.exists(self.pipeline.output_dir):
            shutil.rmtree(self.pipeline.output_dir)

    def _verify_wav_file(self, filepath):
        self.assertTrue(os.path.exists(filepath))
        with wave.open(filepath, 'rb') as w:
            self.assertEqual(w.getnchannels(), 1)
            self.assertEqual(w.getsampwidth(), 2)
            self.assertEqual(w.getframerate(), 44100)
            self.assertGreater(w.getnframes(), 0)

    def test_normal_batch_processing(self):
        items = [
            {"id": "1", "type": "bass_drop", "duration": 0.5, "intensity": 1.0},
            {"id": "2", "type": "sword_clash", "duration": 0.5, "intensity": 0.8},
            {"id": "3", "type": "whoosh", "duration": 0.5, "intensity": 0.9},
        ]
        summary = self.pipeline.process_batch(items)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["successful"], 3)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["status"], "success")
        self.assertIsNotNone(summary["mixed_output"])

        # Verify individual files
        for res in summary["results"]:
            self.assertEqual(res["status"], "success")
            self._verify_wav_file(res["file_path"])

        # Verify mixed file
        self._verify_wav_file(summary["mixed_output"])

    def test_missing_parameters_fallback(self):
        # Empty dict, missing duration, missing intensity
        items = [
            {},
            {"id": "test2", "type": "bass_drop"},
            {"id": "test3", "duration": 2.0}
        ]

        summary = self.pipeline.process_batch(items)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["successful"], 3)
        self.assertIsNotNone(summary["mixed_output"])

    def test_dirty_data_auto_healing(self):
        items = [
            None,
            "not a dict",
            {"id": 123, "type": 999, "duration": "invalid", "intensity": None},
            {"id": "dirty4", "type": "unknown_type", "duration": -5.0, "intensity": 500.0}
        ]

        summary = self.pipeline.process_batch(items)
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["successful"], 4) # Should auto-heal and succeed
        self.assertIsNotNone(summary["mixed_output"])

        # Check that negative duration was clamped or defaulted, meaning it succeeded
        for res in summary["results"]:
            self.assertEqual(res["status"], "success")
            self._verify_wav_file(res["file_path"])

    def test_high_throughput_concurrency(self):
        # Process 20 items to ensure no concurrency issues
        items = [{"id": f"item_{i}", "type": "whoosh", "duration": 0.1, "intensity": 0.5} for i in range(20)]

        summary = self.pipeline.process_batch(items)
        self.assertEqual(summary["total"], 20)
        self.assertEqual(summary["successful"], 20)
        self.assertIsNotNone(summary["mixed_output"])

    def test_extreme_boundary_conditions(self):
        # Empty list
        empty_summary = self.pipeline.process_batch([])
        self.assertEqual(empty_summary["total"], 0)
        self.assertEqual(empty_summary["status"], "success")
        self.assertIsNone(empty_summary["mixed_output"])

        # Huge duration (should be capped to 30.0, but to avoid slow tests we cap test at 1.0 here by passing huge and seeing it doesn't crash)
        # We will use 100.0 and see if it caps (our code caps at 30)
        # To not make the test too slow, we'll test duration=0.0 which caps to default, and large duration.
        items = [
            {"id": "extreme1", "duration": 0.0},
            {"id": "extreme2", "duration": 100.0} # This will take ~30s of audio generation max. We can make it smaller in code or just test.
        ]
        # Actually generating 30s of pure python sin waves might take a second, which is fine.
        summary = self.pipeline.process_batch(items)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["successful"], 2)

    def test_fallback_mixer_direct(self):
        # Test the fallback mixer explicitly
        path1 = os.path.join(self.pipeline.output_dir, "mix1.wav")
        path2 = os.path.join(self.pipeline.output_dir, "mix2.wav")
        mixed = os.path.join(self.pipeline.output_dir, "mixed_out.wav")

        SFXGenerator.generate_waveform("bass_drop", 0.2, 1.0, path1)
        SFXGenerator.generate_waveform("whoosh", 0.2, 1.0, path2)

        success = FFmpegAutoMixer._fallback_mix([path1, path2], mixed)
        self.assertTrue(success)
        self._verify_wav_file(mixed)

if __name__ == '__main__':
    unittest.main()
