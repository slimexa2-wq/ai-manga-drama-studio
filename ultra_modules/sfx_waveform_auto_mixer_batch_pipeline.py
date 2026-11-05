import math
import struct
import wave
import os
import uuid
import tempfile
import subprocess
import concurrent.futures
from typing import List, Dict, Any, Optional

class SFXGenerator:
    """Pure Python waveform generation for SFX."""
    SAMPLE_RATE = 44100

    @classmethod
    def generate_waveform(cls, sfx_type: str, duration_sec: float, intensity: float, output_path: str) -> str:
        """
        Generates a .wav file with the specified SFX type.
        sfx_type: 'bass_drop', 'sword_clash', 'whoosh'
        """
        duration_sec = min(max(duration_sec, 0.1), 10.0)
        intensity = min(max(intensity, 0.1), 1.0)
        num_samples = int(cls.SAMPLE_RATE * duration_sec)

        audio_data = bytearray()

        for i in range(num_samples):
            t = float(i) / cls.SAMPLE_RATE
            val = 0.0

            if sfx_type == "bass_drop":
                # Heavy bass: sweeping frequency from ~150Hz down to ~20Hz
                freq = 150.0 - (130.0 * (t / duration_sec))
                val = math.sin(2.0 * math.pi * freq * t)
                # Apply envelope: quick attack, slow decay
                env = math.exp(-3.0 * (t / duration_sec))
                val *= env

            elif sfx_type == "sword_clash":
                # Sword clash: high frequency metallic ring with noise
                val1 = math.sin(2.0 * math.pi * 3500.0 * t)
                val2 = math.sin(2.0 * math.pi * 5000.0 * t)
                # Pseudo-random noise
                noise_val = (hash(str(t)) % 200 - 100) / 100.0
                val = (val1 * 0.4 + val2 * 0.4 + noise_val * 0.2)
                # Sharp attack, fast decay
                env = math.exp(-15.0 * t)
                val *= env

            elif sfx_type == "whoosh":
                # Transition whoosh: filtered noise envelope
                noise_val = (hash(str(t)) % 200 - 100) / 100.0
                # Envelope: fade in then fade out (bell curve like)
                mid = duration_sec / 2.0
                env = math.exp(-20.0 * ((t - mid) ** 2))
                val = noise_val * env

            else:
                # Default to a simple sine wave beep
                freq = 440.0
                val = math.sin(2.0 * math.pi * freq * t)
                env = math.exp(-5.0 * t)
                val *= env

            val = val * intensity

            # Clip
            val = max(-1.0, min(1.0, val))

            # Convert to 16-bit PCM
            packed_val = struct.pack('<h', int(val * 32767))
            audio_data.extend(packed_val)

        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(cls.SAMPLE_RATE)
            wav_file.writeframes(audio_data)

        return output_path

class FFmpegAutoMixer:
    """Handles mixing using FFmpeg, with silent fallback."""

    @classmethod
    def mix_tracks(cls, input_paths: List[str], output_path: str) -> bool:
        if not input_paths:
            return False

        if len(input_paths) == 1:
            # Just copy if there's only one
            try:
                import shutil
                shutil.copy(input_paths[0], output_path)
                return True
            except Exception:
                return False

        # Build FFmpeg command for mixing
        cmd = ['ffmpeg', '-y']
        for path in input_paths:
            cmd.extend(['-i', path])

        # amix filter
        inputs_str = ''.join([f'[{i}:a]' for i in range(len(input_paths))])
        filter_str = f'{inputs_str}amix=inputs={len(input_paths)}:duration=longest:dropout_transition=2[a]'
        cmd.extend(['-filter_complex', filter_str, '-map', '[a]', output_path])

        try:
            # Try to run FFmpeg
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode != 0:
                # FFmpeg failed (maybe installed but error)
                return cls._fallback_mix(input_paths, output_path)
            return True
        except FileNotFoundError:
            # FFmpeg not found, use fallback
            return cls._fallback_mix(input_paths, output_path)
        except Exception:
            return cls._fallback_mix(input_paths, output_path)

    @classmethod
    def _fallback_mix(cls, input_paths: List[str], output_path: str) -> bool:
        """A very simple pure-Python mixer as fallback."""
        try:
            waves = []
            for path in input_paths:
                try:
                    w = wave.open(path, 'rb')
                    waves.append(w)
                except Exception:
                    continue

            if not waves:
                return False

            # Read all frames and mix them
            # For simplicity in fallback, we'll just sum and clip
            # We assume all are 1 channel, 16-bit, 44100Hz
            max_frames = max([w.getnframes() for w in waves])
            mixed_data = bytearray()

            # Load all data into memory
            all_samples = []
            for w in waves:
                frames = w.readframes(w.getnframes())
                samples = struct.unpack(f'<{w.getnframes()}h', frames)
                all_samples.append(samples)
                w.close()

            for i in range(max_frames):
                val = 0
                for samples in all_samples:
                    if i < len(samples):
                        val += samples[i]

                # Simple clipping
                val = max(-32768, min(32767, val))
                mixed_data.extend(struct.pack('<h', int(val)))

            with wave.open(output_path, 'wb') as out_w:
                out_w.setnchannels(1)
                out_w.setsampwidth(2)
                out_w.setframerate(44100)
                out_w.writeframes(mixed_data)

            return True
        except Exception:
            return False


class SFXWaveformAutoMixerBatchPipeline:
    """High throughput batch pipeline for SFX waveform generation and mixing."""

    def __init__(self, output_dir: Optional[str] = None, max_workers: int = 4):
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="sfx_pipeline_")
        os.makedirs(self.output_dir, exist_ok=True)
        self.max_workers = max_workers

    def _sanitize_and_fill_defaults(self, item: Any) -> Dict[str, Any]:
        """Auto-heals dirty data and fills missing parameters."""
        default_item = {
            "id": str(uuid.uuid4()),
            "type": "whoosh",
            "duration": 1.0,
            "intensity": 0.8
        }

        if not isinstance(item, dict):
            return default_item

        # ID
        clean_item = {}
        clean_item["id"] = str(item.get("id", default_item["id"]))

        # Type
        raw_type = item.get("type")
        valid_types = ["bass_drop", "sword_clash", "whoosh"]
        if not isinstance(raw_type, str) or raw_type not in valid_types:
            clean_item["type"] = default_item["type"]
        else:
            clean_item["type"] = raw_type

        # Duration
        try:
            dur = float(item.get("duration", default_item["duration"]))
            if dur <= 0:
                dur = default_item["duration"]
            clean_item["duration"] = min(dur, 30.0) # Cap at 30 seconds
        except (ValueError, TypeError):
            clean_item["duration"] = default_item["duration"]

        # Intensity
        try:
            intensity = float(item.get("intensity", default_item["intensity"]))
            if intensity <= 0:
                intensity = default_item["intensity"]
            clean_item["intensity"] = min(intensity, 1.0)
        except (ValueError, TypeError):
            clean_item["intensity"] = default_item["intensity"]

        return clean_item

    def _process_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a single item and returns the result."""
        item = self._sanitize_and_fill_defaults(item)

        filename = f"{item['id']}_{item['type']}.wav"
        output_path = os.path.join(self.output_dir, filename)

        try:
            SFXGenerator.generate_waveform(
                sfx_type=item["type"],
                duration_sec=item["duration"],
                intensity=item["intensity"],
                output_path=output_path
            )
            return {"id": item["id"], "status": "success", "file_path": output_path, "error": None}
        except Exception as e:
            return {"id": item["id"], "status": "error", "file_path": None, "error": str(e)}

    def process_batch(self, items: List[Any]) -> Dict[str, Any]:
        """
        Processes a batch of items concurrently.
        Returns a summary and list of individual results.
        """
        if not items:
            return {"status": "success", "total": 0, "successful": 0, "failed": 0, "results": [], "mixed_output": None}

        results = []
        successful_paths = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item = {executor.submit(self._process_single_item, item): item for item in items}
            for future in concurrent.futures.as_completed(future_to_item):
                res = future.result()
                results.append(res)
                if res["status"] == "success" and res["file_path"]:
                    successful_paths.append(res["file_path"])

        # Mix the successful tracks
        mixed_output = None
        if successful_paths:
            mix_filename = f"mixed_{uuid.uuid4().hex[:8]}.wav"
            mix_path = os.path.join(self.output_dir, mix_filename)
            success = FFmpegAutoMixer.mix_tracks(successful_paths, mix_path)
            if success:
                mixed_output = mix_path

        summary = {
            "status": "success" if mixed_output else "partial_or_failed",
            "total": len(items),
            "successful": len(successful_paths),
            "failed": len(items) - len(successful_paths),
            "results": results,
            "mixed_output": mixed_output
        }

        return summary
