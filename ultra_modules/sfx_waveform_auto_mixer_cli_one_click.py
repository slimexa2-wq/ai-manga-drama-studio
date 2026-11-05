import json
import logging
import os
import subprocess
import sys
import wave
import math
import struct
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _safe_str(val: Any, default: str = "") -> str:
    if val is None:
        return default
    if isinstance(val, str):
        return val
    try:
        return str(val)
    except Exception:
        return default

def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(val)
    except Exception:
        return default

def _safe_dict(val: Any, default: Optional[Dict] = None) -> Dict:
    if default is None:
        default = {}
    if isinstance(val, dict):
        return val
    return default

def _safe_list(val: Any, default: Optional[List] = None) -> List:
    if default is None:
        default = []
    if isinstance(val, list):
        return val
    return default

class SFXWaveformAutoMixer:
    """
    SFX waveform auto-mixer that can synthesize waveform effects
    and construct FFmpeg multitrack mix commands with zero configuration.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the auto mixer.
        Missing parameters or dirty data will be auto-healed.
        """
        safe_cfg = _safe_dict(config)
        self.output_dir = _safe_str(safe_cfg.get("output_dir"), default="./sfx_output")
        self.default_volume = _safe_float(safe_cfg.get("default_volume"), default=1.0)
        self.tracks = _safe_list(safe_cfg.get("tracks"), default=[])

        # Ensure output directory exists (safely)
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
        except Exception as e:
            logger.warning(f"Could not create output dir {self.output_dir}: {e}. Falling back to current directory.")
            self.output_dir = "."

    def add_track(self, track_info: Any) -> None:
        """
        Adds a track with self-healing for invalid inputs.
        """
        track = _safe_dict(track_info)

        # Self-heal missing properties
        name = _safe_str(track.get("name"), default=f"track_{len(self.tracks)}")
        type_ = _safe_str(track.get("type"), default="bass_drop")
        volume = _safe_float(track.get("volume"), default=self.default_volume)

        self.tracks.append({
            "name": name,
            "type": type_,
            "volume": volume
        })

    def _synthesize_waveform(self, track: Dict[str, Any]) -> str:
        """
        Synthesizes a simple synthetic waveform for the given track type
        using standard wave/math libraries to produce a valid .wav file.
        """
        track_name = _safe_str(track.get("name"), "unknown")
        track_type = _safe_str(track.get("type"), "bass_drop").lower()
        file_path = os.path.join(self.output_dir, f"{track_name}.wav")
        try:
            # Basic audio parameters
            sample_rate = 44100
            duration_s = 2.0
            num_samples = int(sample_rate * duration_s)

            with wave.open(file_path, 'w') as f:
                f.setnchannels(1) # mono
                f.setsampwidth(2) # 2 bytes per sample (16-bit)
                f.setframerate(sample_rate)

                # Generate synthetic audio based on type
                for i in range(num_samples):
                    t = float(i) / sample_rate
                    val = 0.0

                    if track_type == "bass_drop":
                        # Frequency drops over time, e.g. from 100Hz to 20Hz
                        freq = 100.0 - 80.0 * (t / duration_s)
                        val = math.sin(2 * math.pi * freq * t)
                    elif track_type == "swoosh":
                        # White noise modulated by a fast envelope
                        import random
                        val = (random.random() * 2 - 1) * math.sin(math.pi * t / duration_s)
                    elif track_type == "sword_clash":
                        # Brief high-pitched clank
                        if t < 0.2:
                            val = math.sin(2 * math.pi * 3000 * t) * math.exp(-t * 20)
                        else:
                            val = 0.0
                    else:
                        # Default beep
                        val = math.sin(2 * math.pi * 440 * t)

                    # Convert to 16-bit PCM
                    pcm_val = int(val * 32767.0)
                    # Clamp
                    pcm_val = max(-32768, min(32767, pcm_val))
                    data = struct.pack('<h', pcm_val)
                    f.writeframesraw(data)

            return file_path
        except Exception as e:
            # Note: During mock testing, wave.open might raise exception early, which is fine to catch here.
            logger.error(f"Failed to synthesize waveform for {track_name}: {e}")
            return ""

    def process(self) -> Dict[str, Any]:
        """
        Processes the tracks, synthesizes waveforms, and builds the mix command.
        """
        generated_files = []
        for track in self.tracks:
            file_path = self._synthesize_waveform(track)
            if file_path:
                generated_files.append(file_path)

        mix_command = ""
        final_mix_path = os.path.join(self.output_dir, 'final_mix.wav')
        status = "success"

        if generated_files:
            # Build FFmpeg command for mixing
            cmd_args = ["ffmpeg", "-y"]
            for f in generated_files:
                cmd_args.extend(["-i", f])

            cmd_args.extend(["-filter_complex", f"amix=inputs={len(generated_files)}:duration=longest"])
            cmd_args.append(final_mix_path)

            mix_command = " ".join(cmd_args)

            try:
                # Actually execute FFmpeg
                subprocess.run(cmd_args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                logger.warning(f"FFmpeg mix failed or FFmpeg not installed: {e}. Falling back to copy first track.")
                status = "fallback_mix"
                try:
                    import shutil
                    if generated_files:
                        shutil.copy(generated_files[0], final_mix_path)
                except Exception as copy_e:
                    logger.error(f"Fallback mix failed: {copy_e}")
                    status = "failed_mix"

        return {
            "status": status,
            "generated_files": generated_files,
            "mix_command": mix_command
        }

    def export_metadata(self, metadata: Any, format_type: str = "json") -> str:
        """
        Exports metadata in the specified format (json or csv/excel).
        """
        meta_dict = _safe_dict(metadata)
        format_str = _safe_str(format_type, "json").lower()

        try:
            if format_str in ["csv", "excel"]:
                # simple CSV export
                out_path = os.path.join(self.output_dir, "metadata.csv")
                with open(out_path, 'w') as f:
                    keys = list(meta_dict.keys())
                    f.write(",".join(keys) + "\n")
                    f.write(",".join([_safe_str(meta_dict[k]) for k in keys]) + "\n")
                return out_path
            else:
                out_path = os.path.join(self.output_dir, "metadata.json")
                with open(out_path, 'w') as f:
                    json.dump(meta_dict, f, indent=2)
                return out_path
        except Exception as e:
            logger.error(f"Failed to export metadata: {e}")
            return ""

def run_auto_mixer_cli_one_click() -> None:
    """
    Zero-parameter one-click entry point.
    """
    mixer = SFXWaveformAutoMixer()

    # Add some default tracks for the one-click experience
    mixer.add_track({"name": "epic_bass_drop", "type": "bass_drop"})
    mixer.add_track({"name": "sword_clash", "type": "sword_clash"})
    mixer.add_track({"name": "transition_swoosh", "type": "swoosh"})

    result = mixer.process()
    mixer.export_metadata(result)
    print("Mixer processing complete:", result)

if __name__ == "__main__":
    run_auto_mixer_cli_one_click()
