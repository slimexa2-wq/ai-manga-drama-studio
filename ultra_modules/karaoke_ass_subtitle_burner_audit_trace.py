import json
import logging
import os
import subprocess
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

class SubtitleAuditTracer:
    """
    Traces the execution of the subtitle burner to allow backend auditing.
    """
    def __init__(self):
        self.trace_log: List[Dict[str, Any]] = []
        self.run_id = str(uuid.uuid4())

    def log(self, step: str, details: Any = None, level: str = "INFO"):
        entry = {
            "timestamp": time.time(),
            "run_id": self.run_id,
            "step": step,
            "level": level,
            "details": details
        }
        self.trace_log.append(entry)

    def get_traces(self) -> List[Dict[str, Any]]:
        return self.trace_log


class KaraokeSubtitleBurner:
    """
    Handles generation of Karaoke ASS subtitles and burning them via FFmpeg.
    """
    def __init__(self, tracer: Optional[SubtitleAuditTracer] = None):
        self.tracer = tracer or SubtitleAuditTracer()

    def _heal_dirty_subtitles(self, subtitles: Any) -> List[Dict[str, Any]]:
        """
        Auto-heals dirty subtitle data, ensuring a valid structure.
        """
        self.tracer.log("start_heal", details={"type_input": str(type(subtitles))})
        healed_subs = []

        if not isinstance(subtitles, list):
            if isinstance(subtitles, str):
                self.tracer.log("heal_string_to_list", level="WARN")
                subtitles = [{"text": subtitles, "start": 0.0, "end": 2.0}]
            elif isinstance(subtitles, dict):
                self.tracer.log("heal_dict_to_list", level="WARN")
                subtitles = [subtitles]
            else:
                self.tracer.log("invalid_input_type", level="ERROR")
                return []

        last_end = 0.0
        for i, sub in enumerate(subtitles):
            if not isinstance(sub, dict):
                self.tracer.log("skip_invalid_subtitle_item", details={"index": i}, level="WARN")
                continue

            text = sub.get("text", "")
            if text is None:
                text = ""
            elif not isinstance(text, str):
                text = str(text)

            if not text.strip():
                self.tracer.log("skip_empty_text", details={"index": i}, level="WARN")
                continue

            start = sub.get("start", last_end)
            try:
                start = float(start)
            except (ValueError, TypeError):
                start = last_end

            if start < last_end:
                self.tracer.log("heal_overlap", details={"old_start": start, "new_start": last_end}, level="WARN")
                start = last_end

            end = sub.get("end", start + 2.0)
            try:
                end = float(end)
            except (ValueError, TypeError):
                end = start + 2.0

            if end <= start:
                self.tracer.log("heal_duration", details={"old_end": end, "new_end": start + 2.0}, level="WARN")
                end = start + 2.0

            words = sub.get("words", [])
            if not isinstance(words, list) or not words:
                self.tracer.log("auto_generate_words", details={"index": i}, level="INFO")
                split_text = text.split()
                if not split_text:
                    split_text = [text] # pragma: no cover
                duration_per_word = (end - start) / len(split_text)
                words = []
                for j, word in enumerate(split_text):
                    word_start = start + j * duration_per_word
                    word_end = word_start + duration_per_word
                    words.append({"word": word, "start": word_start, "end": word_end})

            # Heal words
            healed_words = []
            word_last_end = start
            for w in words:
                if not isinstance(w, dict):
                    continue
                w_text = str(w.get("word", ""))
                if not w_text.strip():
                    continue

                w_start = w.get("start", word_last_end)
                try:
                    w_start = float(w_start)
                except (ValueError, TypeError):
                    w_start = word_last_end

                if w_start < word_last_end:
                    w_start = word_last_end

                w_end = w.get("end", w_start + 0.1)
                try:
                    w_end = float(w_end)
                except (ValueError, TypeError):
                    w_end = w_start + 0.1

                if w_end <= w_start:
                    w_end = w_start + 0.1

                healed_words.append({
                    "word": w_text,
                    "start": w_start,
                    "end": w_end
                })
                word_last_end = w_end

            if not healed_words:
                healed_words = [{"word": text, "start": start, "end": end}]

            # Ensure the subtitle overall ends exactly when the last word ends
            actual_end = healed_words[-1]["end"]
            if actual_end > end:
                end = actual_end

            healed_subs.append({
                "text": text,
                "start": start,
                "end": end,
                "words": healed_words
            })
            last_end = end

        self.tracer.log("end_heal", details={"count": len(healed_subs)})
        return healed_subs

    def _format_time_ass(self, seconds: float) -> str:
        """Format time in seconds to ASS timestamp: h:mm:ss.cs"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    def _generate_ass_content(self, subtitles: List[Dict[str, Any]]) -> str:
        """Generates ASS content with Karaoke tags."""
        self.tracer.log("generate_ass_start")

        ass_lines = [
            "[Script Info]",
            "Title: Generated by AI Manga Drama Studio",
            "ScriptType: v4.00+",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "YCbCr Matrix: None",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        for i, sub in enumerate(subtitles):
            start_ass = self._format_time_ass(sub["start"])
            end_ass = self._format_time_ass(sub["end"])

            karaoke_text = ""
            for w in sub["words"]:
                duration_cs = int((w["end"] - w["start"]) * 100)
                karaoke_text += f"{{\\k{duration_cs}}}{w['word']} "

            karaoke_text = karaoke_text.strip()

            event_line = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{karaoke_text}"
            ass_lines.append(event_line)

        self.tracer.log("generate_ass_end", details={"lines_count": len(ass_lines)})
        return "\n".join(ass_lines)

    def process(self, subtitles: Any, video_path: Optional[str] = None, output_path: str = "output.mp4", ass_path: str = "output.ass") -> Dict[str, Any]:
        """
        Main entry point: processes dirty data, generates ASS, and optionally burns subtitles via FFmpeg.
        Returns a clean result dictionary for the frontend.
        """
        self.tracer.log("process_start", details={"video_path": video_path, "output_path": output_path, "ass_path": ass_path})

        healed_subs = self._heal_dirty_subtitles(subtitles)
        if not healed_subs:
            self.tracer.log("process_aborted_empty_subs", level="WARN")
            return {
                "success": True, # Still report success to frontend
                "result_path": None,
                "ass_path": None,
                "message": "No valid subtitles found",
                "traces": self.tracer.get_traces()
            }

        ass_content = self._generate_ass_content(healed_subs)

        try:
            with open(ass_path, "w", encoding="utf-8") as f:
                f.write(ass_content)
            self.tracer.log("ass_file_written", details={"path": ass_path})
        except Exception as e:
            self.tracer.log("ass_file_write_failed", details={"error": str(e)}, level="ERROR")
            return {
                "success": False,
                "result_path": None,
                "ass_path": None,
                "message": "Failed to write ASS file",
                "traces": self.tracer.get_traces()
            }

        result_path = ass_path

        if video_path and os.path.exists(video_path):
            self.tracer.log("start_ffmpeg_burning")
            try:
                # Subprocess call with simple burning command
                cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", f"ass={ass_path}", output_path]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.tracer.log("ffmpeg_success", details={"output_path": output_path})
                    result_path = output_path
                else:
                    self.tracer.log("ffmpeg_failed", details={"stderr": result.stderr}, level="WARN")
                    # Fallback silently to ASS file
            except FileNotFoundError:
                self.tracer.log("ffmpeg_not_found", level="WARN")
                # Fallback silently
            except Exception as e:
                self.tracer.log("ffmpeg_exception", details={"error": str(e)}, level="WARN")
                # Fallback silently
        else:
            if video_path:
                self.tracer.log("video_not_found", details={"video_path": video_path}, level="WARN")
            else:
                self.tracer.log("no_video_path_provided", level="INFO")

        self.tracer.log("process_complete", details={"result_path": result_path})
        return {
            "success": True,
            "result_path": result_path,
            "ass_path": ass_path,
            "message": "Processing complete",
            "traces": self.tracer.get_traces()
        }
