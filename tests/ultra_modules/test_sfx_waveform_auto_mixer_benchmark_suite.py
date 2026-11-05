import unittest
import numpy as np
from ultra_modules.sfx_waveform_auto_mixer_benchmark_suite import (
    synthesize_waveform,
    generate_ffmpeg_mix_command,
    SFXBenchmarkSuite
)

class TestSFXWaveformAutoMixerBenchmarkSuite(unittest.TestCase):
    def test_synthesize_waveform_normal(self):
        """Test normal generation of procedural waveforms with varying types."""
        # Test sub_bass
        wave_bass = synthesize_waveform('sub_bass', duration=0.5, seed=1)
        self.assertEqual(len(wave_bass), 22050)

        # Test sword_clash
        wave_sword = synthesize_waveform('sword_clash', duration=0.5, seed=2)
        self.assertEqual(len(wave_sword), 22050)

        # Test whoosh
        wave_whoosh = synthesize_waveform('whoosh', duration=0.5, seed=3)
        self.assertEqual(len(wave_whoosh), 22050)

    def test_synthesize_waveform_dirty_data(self):
        """Test waveform generation gracefully handles invalid parameters (dirty data self-healing)."""
        # Test negative duration heals to 1.0 (44100 samples)
        wave_neg = synthesize_waveform('sub_bass', duration=-5.0, seed=42)
        self.assertEqual(len(wave_neg), 44100)

        # Test missing/unknown type falls back to default subtle noise
        wave_unknown = synthesize_waveform('unknown_type', duration=1.0, seed=42)
        self.assertEqual(len(wave_unknown), 44100)

    def test_generate_ffmpeg_mix_command_normal(self):
        """Test generation of FFmpeg command with valid sequences."""
        tracks = [
            {"filepath": "audio1.wav", "delay_ms": 100, "volume": 0.5},
            {"filepath": "audio2.wav", "delay_ms": 500, "volume": 1.0},
        ]
        cmd = generate_ffmpeg_mix_command(tracks, "output.wav")
        self.assertIn("-i audio1.wav", cmd)
        self.assertIn("-i audio2.wav", cmd)
        self.assertIn("[0:a]volume=0.5,adelay=100|100[a0]", cmd)
        self.assertIn("[1:a]volume=1.0,adelay=500|500[a1]", cmd)
        self.assertIn("[a0][a1]amix=inputs=2:duration=longest[aout]", cmd)
        self.assertIn("-metadata year=\"2025\"", cmd)

    def test_generate_ffmpeg_mix_command_dirty_data(self):
        """Test generation of FFmpeg command gracefully handles missing/null/corrupted data."""
        # Empty list
        cmd_empty = generate_ffmpeg_mix_command([], "out.wav")
        self.assertIn("anullsrc", cmd_empty)

        # Corrupted list
        tracks = [
            None,
            "not a dict",
            {"delay_ms": 100}, # Missing filepath
            {"filepath": "valid.wav", "delay_ms": -50, "volume": "LOUD"}, # Invalid types/negative
            {"filepath": "valid2.wav", "delay_ms": 100, "volume": 0.8} # Valid track
        ]
        cmd = generate_ffmpeg_mix_command(tracks, "out2.wav")

        # valid.wav should be healed: delay=0, volume=1.0
        self.assertIn("[0:a]volume=1.0,adelay=0|0[a0]", cmd)
        self.assertIn("-i valid.wav", cmd)

        # valid2.wav is normal
        self.assertIn("[1:a]volume=0.8,adelay=100|100[a1]", cmd)
        self.assertIn("-i valid2.wav", cmd)

        self.assertIn("[a0][a1]amix=inputs=2:duration=longest[aout]", cmd)

    def test_benchmark_suite_execution(self):
        """Test the benchmark suite to ensure no crashes under extreme load/boundaries."""
        result = SFXBenchmarkSuite.run_benchmark(num_tracks=1000)
        self.assertEqual(result["status"], "success")
        self.assertGreater(result["tracks_processed"], 0)
        self.assertTrue(result["millisecond_responsive"])
        self.assertGreater(result["command_length"], 100)

if __name__ == '__main__':
    unittest.main()
