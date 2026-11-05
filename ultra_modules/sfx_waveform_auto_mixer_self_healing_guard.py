import time
import copy
import logging
from typing import List, Dict, Any, Tuple

from ultra_modules.sfx_waveform_auto_mixer_core_engine import SFXWaveformAutoMixer

logger = logging.getLogger(__name__)

class SFXWaveformAutoMixerSelfHealingGuard:
    """
    高燃分镜重低音震屏/刀剑铮鸣/转场呼啸波形合成与FFmpeg多轨自动混音器
    静默自愈守护与一键撤回快照机制（自动修复异常，轻量化 Undo 栈）
    """

    def __init__(self, undo_window_seconds: Any = 5.0):
        self._mixer = SFXWaveformAutoMixer()
        self._snapshots: List[Tuple[float, List[Dict[str, Any]]]] = []

        # 处理异常的初始化参数
        try:
            val = float(undo_window_seconds)
            self._undo_window_seconds = max(1.0, val)
        except (ValueError, TypeError):
            self._undo_window_seconds = 5.0

        self._current_tracks: List[Dict[str, Any]] = []

    def _cleanup_old_snapshots(self) -> None:
        """静默清理超过有效时间的旧快照"""
        try:
            now = time.time()
            self._snapshots = [
                snap for snap in self._snapshots
                if (now - snap[0]) <= self._undo_window_seconds
            ]
        except Exception:
            pass # 严禁打断

    def _safe_normalize_input(self, raw_input: Any) -> List[Dict[str, Any]]:
        """极度宽容的输入规范化"""
        if raw_input is None:
            return []

        # 如果是单个字典或字符串，静默包装为列表
        if isinstance(raw_input, (dict, str)):
            raw_input = [raw_input]

        if not isinstance(raw_input, list):
            # 完全无法理解的格式，静默返回空
            return []

        normalized = []
        for item in raw_input:
            if isinstance(item, dict):
                normalized.append(copy.deepcopy(item))
            elif isinstance(item, str):
                normalized.append({"file_path": item.strip()})
        return normalized

    def set_tracks(self, tracks: Any) -> None:
        """
        设置当前混音轨道。设置前自动产生一次快照。
        输入任意脏数据都会被静默自愈。
        """
        try:
            self.save_snapshot()

            raw_list = self._safe_normalize_input(tracks)
            cleaned = []
            for t in raw_list:
                ct = self._mixer._clean_track_data(t)
                if ct and ct.get("file_path"):
                    cleaned.append(ct)
            self._current_tracks = cleaned
        except Exception:
            # 极端异常情况下，保持 _current_tracks 不变，不抛错
            pass

    def add_track(self, track: Any) -> None:
        """增量添加轨道，附带自愈与快照"""
        try:
            self.save_snapshot()
            raw_list = self._safe_normalize_input(track)
            for t in raw_list:
                ct = self._mixer._clean_track_data(t)
                if ct and ct.get("file_path"):
                    self._current_tracks.append(ct)
        except Exception:
            pass

    def save_snapshot(self) -> None:
        """主动打一个可撤销快照"""
        try:
            self._cleanup_old_snapshots()
            self._snapshots.append((time.time(), copy.deepcopy(self._current_tracks)))
        except Exception:
            pass

    def undo(self) -> bool:
        """
        一键撤回 (Undo)。
        恢复到时间窗口内最新的快照，成功返回 True，如果没有快照则静默返回 False。
        """
        try:
            self._cleanup_old_snapshots()
            if not self._snapshots:
                return False

            last_snap = self._snapshots.pop()
            self._current_tracks = copy.deepcopy(last_snap[1])
            return True
        except Exception:
            return False

    def clear_tracks(self) -> None:
        """清空轨道，同样可以撤销"""
        self.save_snapshot()
        self._current_tracks = []

    def get_tracks(self) -> List[Dict[str, Any]]:
        """获取当前工作轨道（自愈后的干净数据）"""
        return copy.deepcopy(self._current_tracks)

    def generate_ffmpeg_mix_command(self, output_path: Any = "output.wav") -> str:
        """安全生成命令，不抛异常"""
        try:
            out_str = str(output_path) if output_path else "output.wav"
            return self._mixer.generate_ffmpeg_mix_command(self._current_tracks, out_str)
        except Exception:
            out_str = str(output_path) if isinstance(output_path, str) and output_path else "output.wav"
            return f"ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 0.1 -y {out_str}"

    def synthesize_waveform_data(self, duration: Any = 1.0) -> Dict[str, Any]:
        """安全合成波形，不抛异常"""
        try:
            dur = float(duration)
            if dur <= 0: dur = 1.0
            return self._mixer.synthesize_waveform_data(self._current_tracks, dur)
        except Exception:
            return {
                "duration": 1.0,
                "peaks": [],
                "events": []
            }
