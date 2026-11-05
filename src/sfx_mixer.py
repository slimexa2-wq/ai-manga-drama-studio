import wave
import struct
import math
import random
import os
import subprocess
import shutil
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SFXMixer:
    """
    Synthesizes basic sound effects (SFX) and mixes them into base audio
    using FFmpeg. Implements a backend fallback pattern: if FFmpeg fails or
    is unavailable, it silently falls back to the original base audio.
    """
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.temp_files = []

    def _write_wav(self, filename: str, samples: List[float]):
        """Helper to write raw float samples (-1.0 to 1.0) to a 16-bit WAV file."""
        try:
            with wave.open(filename, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)

                for sample in samples:
                    # Clip to [-1.0, 1.0]
                    s = max(-1.0, min(1.0, sample))
                    # Convert to 16-bit PCM
                    pcm = int(s * 32767.0)
                    data = struct.pack('<h', pcm)
                    wav_file.writeframesraw(data)
            self.temp_files.append(filename)
        except Exception as e:
            logger.error(f"Failed to write wav {filename}: {e}")
            raise

    def generate_impact_bass(self, filename: str, duration: float = 1.0):
        """Low frequency exponential decay sine wave for impact."""
        samples = []
        num_samples = int(duration * self.sample_rate)
        # Start at 80Hz, drop to 20Hz
        start_freq = 80.0
        end_freq = 20.0

        for i in range(num_samples):
            t = i / self.sample_rate
            # Exponential decay envelope
            env = math.exp(-3.0 * t)

            # Pitch drop
            freq = start_freq - (start_freq - end_freq) * (t / duration)

            # Sine wave
            val = math.sin(2 * math.pi * freq * t) * env
            samples.append(val)

        self._write_wav(filename, samples)
        return filename

    def generate_sword_clash(self, filename: str, duration: float = 0.5):
        """High frequency metallic ring with rapid decay."""
        samples = []
        num_samples = int(duration * self.sample_rate)

        # Frequencies for a somewhat metallic inharmonic chord
        freqs = [1200.0, 3150.0, 4800.0, 8000.0]

        for i in range(num_samples):
            t = i / self.sample_rate
            # Sharp transient attack, rapid decay
            if t < 0.01:
                env = t / 0.01
            else:
                env = math.exp(-8.0 * (t - 0.01))

            val = 0.0
            for f in freqs:
                val += math.sin(2 * math.pi * f * t)

            val = (val / len(freqs)) * env * 0.8 # Scale slightly
            samples.append(val)

        self._write_wav(filename, samples)
        return filename

    def generate_whoosh(self, filename: str, duration: float = 0.8):
        """Sweeping envelope noise for transition whoosh."""
        samples = []
        num_samples = int(duration * self.sample_rate)

        for i in range(num_samples):
            t = i / self.sample_rate

            # Envelope: rise and fall
            env = math.sin((math.pi * t) / duration) ** 2

            # White noise
            noise = random.uniform(-1.0, 1.0)

            val = noise * env * 0.5
            samples.append(val)

        self._write_wav(filename, samples)
        return filename

    def mix_sfx(self, base_audio: str, output_audio: str, sfx_list: List[Dict[str, Any]]) -> str:
        """
        Mixes generated or existing SFX files into the base audio at specified timestamps.

        sfx_list format: [{'file': 'sfx.wav', 'timestamp_ms': 1500, 'volume': 0.8}, ...]

        Falls back to simply copying base_audio to output_audio if ffmpeg fails.
        """
        if not shutil.which("ffmpeg"):
            logger.warning("ffmpeg not found, falling back to base audio")
            shutil.copy2(base_audio, output_audio)
            return output_audio

        if not sfx_list:
            shutil.copy2(base_audio, output_audio)
            return output_audio

        try:
            # Construct FFmpeg complex filter command
            cmd = ["ffmpeg", "-y", "-i", base_audio]
            filter_complex = []

            # Add inputs
            for idx, sfx in enumerate(sfx_list):
                cmd.extend(["-i", sfx['file']])

            # Delay and volume filters for each sfx
            amix_inputs = ["[0:a]"]
            for idx, sfx in enumerate(sfx_list):
                input_idx = idx + 1
                delay_ms = sfx.get('timestamp_ms', 0)
                vol = sfx.get('volume', 1.0)

                # Format: [1:a]volume=0.8,adelay=1500|1500[sfx1];
                filter_str = f"[{input_idx}:a]volume={vol},adelay={delay_ms}|{delay_ms}[sfx{input_idx}]"
                filter_complex.append(filter_str)
                amix_inputs.append(f"[sfx{input_idx}]")

            # Mix all together
            mix_inputs_str = "".join(amix_inputs)
            total_inputs = len(sfx_list) + 1
            mix_filter = f"{mix_inputs_str}amix=inputs={total_inputs}:duration=first:dropout_transition=2[out]"
            filter_complex.append(mix_filter)

            cmd.extend(["-filter_complex", ";".join(filter_complex), "-map", "[out]"])
            cmd.append(output_audio)

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg failed with return code {result.returncode}:\n{result.stderr}")
                raise RuntimeError("FFmpeg error")

            return output_audio
        except Exception as e:
            logger.error(f"SFX mixing failed: {e}. Falling back to base audio.")
            shutil.copy2(base_audio, output_audio)
            return output_audio

    def cleanup(self):
        """Remove generated temporary files."""
        for f in self.temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {f}: {e}")
        self.temp_files.clear()
