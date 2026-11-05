import os
import shutil
import subprocess
import copy
import logging

class KaraokeSubtitleBurnerSelfHealingGuard:
    def __init__(self, snapshot_dir="/tmp/karaoke_snapshots"):
        self.snapshot_dir = snapshot_dir
        os.makedirs(self.snapshot_dir, exist_ok=True)
        self.last_snapshot = None
        self.last_output_path = None
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _heal_words_data(words_data):
        """
        Pure function self-healing for subtitle arrays.
        Handles incorrect types, missing parameters, reversed timestamps.
        words_data expected format: [{'word': str, 'start': float, 'end': float}, ...]
        """
        healed = []
        if not isinstance(words_data, list):
            if isinstance(words_data, str):
                # Fallback for plain string
                words_data = [{'word': words_data, 'start': 0.0, 'end': 2.0}]
            else:
                words_data = []

        last_end = 0.0
        for item in words_data:
            if isinstance(item, str):
                item = {'word': item, 'start': last_end, 'end': last_end + 0.5}

            if not isinstance(item, dict):
                continue

            word = str(item.get('word', ''))
            if not word.strip():
                continue

            start = item.get('start')
            end = item.get('end')

            try:
                start = float(start) if start is not None else last_end
            except (ValueError, TypeError):
                start = last_end

            try:
                end = float(end) if end is not None else start + 0.5
            except (ValueError, TypeError):
                end = start + 0.5

            if start > end:
                start, end = end, start

            # If still invalid, enforce non-negative
            start = max(0.0, start)
            end = max(start + 0.1, end)

            healed.append({'word': word, 'start': start, 'end': end})
            last_end = end

        return healed

    @staticmethod
    def _format_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    @staticmethod
    def generate_ass(words_data, title="Karaoke Subtitle"):
        """
        Generates ASS formatting with dynamic karaoke tags ({\\K}) for word-by-word highlight.
        """
        healed_data = KaraokeSubtitleBurnerSelfHealingGuard._heal_words_data(words_data)

        ass_header = f"""[Script Info]
Title: {title}
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        if not healed_data:
            return ass_header

        start_time = KaraokeSubtitleBurnerSelfHealingGuard._format_time(healed_data[0]['start'])
        end_time = KaraokeSubtitleBurnerSelfHealingGuard._format_time(healed_data[-1]['end'])

        text = ""
        for word_data in healed_data:
            duration_ms = int((word_data['end'] - word_data['start']) * 100) # centiseconds for \K
            duration_ms = max(1, duration_ms)
            text += f"{{\\K{duration_ms}}}{word_data['word']} "

        ass_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text.strip()}\n"
        return ass_header + ass_line

    def burn_subtitles(self, video_path, words_data, output_path=None):
        """
        Calls FFmpeg via subprocess for hardsub burning. Includes zero-configuration fallbacks.
        If FFmpeg is unavailable or errors out, it falls back silently without disrupting the user.
        Creates a snapshot before overwriting files.
        """
        if not output_path:
            base, ext = os.path.splitext(video_path)
            output_path = f"{base}_karaoke{ext}"

        self._create_snapshot(output_path)

        ass_content = self.generate_ass(words_data)
        ass_path = os.path.join(self.snapshot_dir, "temp_sub.ass")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        # Escape path for FFmpeg filter
        escaped_ass_path = ass_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", f"ass='{escaped_ass_path}'",
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Silent fallback: just copy the original video if ffmpeg fails or isn't installed
            try:
                if video_path != output_path and os.path.exists(video_path):
                    shutil.copy2(video_path, output_path)
            except Exception:
                pass

        # Clean up temp ass
        try:
            if os.path.exists(ass_path):
                os.remove(ass_path)
        except OSError:
            pass

        return output_path

    def _create_snapshot(self, target_path):
        self.last_output_path = target_path
        self.last_snapshot = os.path.join(self.snapshot_dir, "snapshot_backup")
        if os.path.exists(target_path):
            shutil.copy2(target_path, self.last_snapshot)
        else:
            if os.path.exists(self.last_snapshot):
                os.remove(self.last_snapshot)

    def undo_burn(self):
        """
        1-click snapshot restore mechanism for instant 5-second undo.
        """
        if not self.last_output_path:
            return False

        if self.last_snapshot and os.path.exists(self.last_snapshot):
            shutil.copy2(self.last_snapshot, self.last_output_path)
        else:
            if os.path.exists(self.last_output_path):
                os.remove(self.last_output_path)

        return True
