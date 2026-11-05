import os
import subprocess
import concurrent.futures
import threading
from typing import List, Dict, Any, Optional
import uuid

class SubtitleTask:
    def __init__(self, task_id: str, video_path: str, lyrics: List[Dict], output_path: Optional[str] = None, **kwargs):
        self.task_id = task_id
        # Self-healing: trim, default extension handling, missing parameters
        self.video_path = video_path.strip() if video_path else "default.mp4"
        self.lyrics = lyrics if lyrics else []
        self.kwargs = kwargs

        if not output_path:
            base, ext = os.path.splitext(self.video_path)
            # Self-healing: auto-correcting file extensions
            if not ext:
                ext = ".mp4"
            self.output_path = f"{base}_burned{ext}"
        else:
            self.output_path = output_path.strip()
            if not os.path.splitext(self.output_path)[1]:
                self.output_path += ".mp4"

        self.status = "PENDING"
        self.error_msg = ""

    def heal_lyrics(self):
        """Dirty data self-healing: fix missing/invalid timestamps and missing words."""
        healed = []
        current_time = 0
        for line in self.lyrics:
            start = line.get("start", current_time)
            end = line.get("end", start + 2000)

            if start < 0: start = current_time
            if end <= start: end = start + 2000

            words = line.get("words", [])
            healed_words = []
            word_current = start
            for w in words:
                w_dur = w.get("duration", 500)
                if w_dur < 0: w_dur = 500
                healed_words.append({"word": w.get("word", ""), "duration": w_dur})
                word_current += w_dur

            healed.append({
                "start": start,
                "end": max(end, word_current),
                "words": healed_words
            })
            current_time = max(end, word_current)
        self.lyrics = healed

def ms_to_ass_time(ms: int) -> str:
    """Convert milliseconds to ASS time format H:MM:SS.cs"""
    ms = max(0, ms)
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    cs = (ms % 1000) // 10
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def generate_karaoke_ass_content(lyrics: List[Dict], width=1080, height=1920) -> str:
    """Dynamically generates ASS subtitle content with karaoke styles (highlight/scale)."""
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass_lines = []
    for line in lyrics:
        start_time = ms_to_ass_time(line["start"])
        end_time = ms_to_ass_time(line["end"])

        karaoke_text = ""
        for w in line["words"]:
            dur_cs = max(1, w["duration"] // 10)
            # Karaoke highlight {\\kf} and scale effect {\\fscx\\fscy\\t()}
            karaoke_text += f"{{\\kf{dur_cs}\\fscx120\\fscy120\\t(0,{w['duration']}, \\fscx100\\fscy100)}}{w['word']}"

        ass_lines.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text}")

    return ass_header + "\n".join(ass_lines)

class KaraokeSubtitleBatchPipeline:
    """Batch pipeline for concurrently processing karaoke subtitle burning via FFmpeg."""
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, SubtitleTask] = {}
        self.lock = threading.Lock()

    def submit_batch(self, tasks_data: List[Dict[str, Any]]) -> List[str]:
        task_ids = []
        for data in tasks_data:
            task_id = data.get("task_id", f"task_{uuid.uuid4().hex[:8]}")
            task = SubtitleTask(
                task_id=task_id,
                video_path=data.get("video_path", ""),
                lyrics=data.get("lyrics", []),
                output_path=data.get("output_path"),
            )
            with self.lock:
                self.tasks[task_id] = task
            task_ids.append(task_id)
            self.executor.submit(self._process_task, task_id)
        return task_ids

    def _process_task(self, task_id: str):
        with self.lock:
            task = self.tasks[task_id]
            task.status = "PROCESSING"

        ass_path = f"{task_id}_temp.ass"
        try:
            task.heal_lyrics()
            ass_content = generate_karaoke_ass_content(task.lyrics)

            # Save temporary ASS file
            with open(ass_path, "w", encoding="utf-8") as f:
                f.write(ass_content)

            if not os.path.exists(task.video_path):
                raise FileNotFoundError(f"Video file not found: {task.video_path}")

            cmd = [
                "ffmpeg", "-y", "-i", task.video_path,
                "-vf", f"ass={ass_path}",
                task.output_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            with self.lock:
                task.status = "COMPLETED"

        except subprocess.CalledProcessError as e:
            with self.lock:
                task.status = "FAILED"
                task.error_msg = f"FFmpeg error: {e.stderr}" if e.stderr else str(e)
        except Exception as e:
            with self.lock:
                task.status = "FAILED"
                task.error_msg = str(e)
        finally:
            if os.path.exists(ass_path):
                os.remove(ass_path)

    def get_progress_snapshot(self) -> Dict[str, Any]:
        """Zero-blocking progress snapshot aggregation."""
        with self.lock:
            total = len(self.tasks)
            completed = sum(1 for t in self.tasks.values() if t.status == "COMPLETED")
            failed = sum(1 for t in self.tasks.values() if t.status == "FAILED")
            pending = total - completed - failed

            results = {
                t_id: {"status": t.status, "output_path": t.output_path, "error": t.error_msg}
                for t_id, t in self.tasks.items()
            }

            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "results": results
            }

    def shutdown(self, wait=True):
        self.executor.shutdown(wait=wait)
