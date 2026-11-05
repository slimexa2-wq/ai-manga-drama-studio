import json
import logging
from typing import List, Dict, Any, Optional

# Setup silent logger for audit tracing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sfx_mixer_audit")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)


class SFXAutoMixerAuditTrace:
    """
    SFX Waveform Auto Mixer & Audit Trace
    A production-grade class to build FFmpeg multi-track audio mixing commands,
    with built-in silent dirty-data auto-healing, duplicate removal, and audit logging.
    """

    def __init__(self, base_volume: float = 1.0) -> None:
        self.audit_log: List[Dict[str, Any]] = []
        # Auto-heal base_volume
        self.base_volume = self._heal_volume(base_volume)
        self._record_audit("INIT", {"base_volume": self.base_volume})

    def _record_audit(self, action: str, details: Dict[str, Any]) -> None:
        """Silently record backend audit trace."""
        entry = {"action": action, "details": details}
        self.audit_log.append(entry)
        # Log to debug for potential backend investigation, silent to user
        logger.debug(f"AUDIT_TRACE: {json.dumps(entry)}")

    def _heal_volume(self, volume: Any) -> float:
        """Dirty data auto-healing for volume values."""
        try:
            vol = float(volume)
            if vol < 0:
                self._record_audit("HEAL_VOLUME", {"reason": "negative_value", "original": volume, "fixed": 1.0})
                return 1.0
            if vol > 10.0: # Cap absurdly high volumes
                self._record_audit("HEAL_VOLUME", {"reason": "excessive_value", "original": volume, "fixed": 10.0})
                return 10.0
            return vol
        except (ValueError, TypeError):
            self._record_audit("HEAL_VOLUME", {"reason": "invalid_type", "original": volume, "fixed": 1.0})
            return 1.0

    def _heal_track_path(self, path: Any) -> str:
        """Dirty data auto-healing for file paths."""
        if not isinstance(path, str) or not path.strip():
            self._record_audit("HEAL_PATH", {"reason": "invalid_path", "original": path, "fixed": "default_silence.wav"})
            return "default_silence.wav"
        return path.strip()

    def generate_mix_command(self, tracks: List[Dict[str, Any]], output_file: Optional[str] = None) -> str:
        """
        Generate an FFmpeg multi-track auto-mixing command.

        Args:
            tracks: List of track dictionaries with keys like 'path', 'volume', 'type' (e.g., bass_shake, sword_clash).
            output_file: Optional output file path. Defaults to a reasonable value.
        """
        if not output_file or not isinstance(output_file, str):
            output_file = "output_mix.wav"
            self._record_audit("HEAL_OUTPUT_FILE", {"fixed": output_file})

        if not isinstance(tracks, list):
            self._record_audit("HEAL_TRACKS", {"reason": "not_a_list", "fixed": []})
            tracks = []

        # Deduplicate and heal tracks
        processed_tracks: List[Dict[str, Any]] = []
        seen_paths = set()

        for idx, track in enumerate(tracks):
            if not isinstance(track, dict):
                self._record_audit("HEAL_TRACK", {"reason": f"invalid_type_at_index_{idx}", "action": "skip"})
                continue

            raw_path = track.get("path")
            healed_path = self._heal_track_path(raw_path)

            # Simple deduplication strategy based on path
            if healed_path in seen_paths and healed_path != "default_silence.wav":
                self._record_audit("DEDUPLICATE_TRACK", {"path": healed_path, "action": "skip"})
                continue

            if healed_path != "default_silence.wav":
                seen_paths.add(healed_path)

            raw_vol = track.get("volume", 1.0)
            healed_vol = self._heal_volume(raw_vol)

            track_type = track.get("type", "normal")

            processed_tracks.append({
                "path": healed_path,
                "volume": healed_vol,
                "type": track_type
            })

        self._record_audit("PROCESS_TRACKS", {"count": len(processed_tracks)})

        if not processed_tracks:
            # Fallback for empty tracks
            cmd = f"ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 1 {output_file}"
            self._record_audit("GENERATE_COMMAND", {"type": "fallback_empty", "command": cmd})
            return cmd

        # Build FFmpeg complex filter command
        inputs = []
        filters = []
        for idx, trk in enumerate(processed_tracks):
            inputs.append(f"-i \"{trk['path']}\"")

            vol = trk['volume'] * self.base_volume
            # Apply basic effect logic based on type
            if trk['type'] == 'bass_shake':
                filter_str = f"[{idx}:a]volume={vol},bass=g=5:f=100[a{idx}];"
            elif trk['type'] == 'sword_clash':
                filter_str = f"[{idx}:a]volume={vol},treble=g=5:f=5000[a{idx}];"
            elif trk['type'] == 'transition_howl':
                filter_str = f"[{idx}:a]volume={vol},chorus=0.5:0.9:50|60:0.4|0.32:0.25|0.4:2|2.3[a{idx}];"
            else:
                filter_str = f"[{idx}:a]volume={vol}[a{idx}];"

            filters.append(filter_str)

        filter_complex = "".join(filters)
        mix_inputs = "".join([f"[a{i}]" for i in range(len(processed_tracks))])
        filter_complex += f"{mix_inputs}amix=inputs={len(processed_tracks)}:duration=longest[aout]"

        cmd = f"ffmpeg {' '.join(inputs)} -filter_complex \"{filter_complex}\" -map \"[aout]\" {output_file}"
        self._record_audit("GENERATE_COMMAND", {"type": "normal", "command": cmd})
        return cmd

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Return the clean audit trail for verification/debugging."""
        return self.audit_log
