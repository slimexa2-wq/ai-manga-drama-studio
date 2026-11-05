import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SFXWaveformAutoMixer:
    """
    高燃分镜重低音震屏/刀剑铮鸣/转场呼啸波形合成与FFmpeg多轨自动混音器
    核心纯函数算法与零配置自动容错实现
    """

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """安全转换浮点数，处理脏数据"""
        try:
            val = float(value)
            return max(0.0, val) if "time" in str(value).lower() else val
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _clean_track_data(track: Dict[str, Any]) -> Dict[str, Any]:
        """静默清洗音轨数据，缺参赋默认值，脏数据自愈"""
        if not isinstance(track, dict):
            return {}

        clean_track = {
            "file_path": str(track.get("file_path", "")).strip(),
            "start_time": max(0.0, SFXWaveformAutoMixer._safe_float(track.get("start_time"), 0.0)),
            "volume": SFXWaveformAutoMixer._safe_float(track.get("volume"), 1.0),
            "type": str(track.get("type", "sfx")).strip().lower()
        }

        # 确保音量在合理范围 (0.0 to 10.0)
        if clean_track["volume"] < 0.0:
            clean_track["volume"] = 1.0
        elif clean_track["volume"] > 10.0:
            clean_track["volume"] = 10.0

        # 如果类型不在允许的范围内，使用默认值
        valid_types = {"sfx", "bgm", "voice", "transition", "impact"}
        if clean_track["type"] not in valid_types:
            clean_track["type"] = "sfx"

        return clean_track

    def generate_ffmpeg_mix_command(self, tracks: List[Dict[str, Any]], output_path: str = "output.wav") -> str:
        """
        生成FFmpeg多轨混音命令。
        实现核心算法，边界条件自动兜底。
        """
        if not tracks:
            # 极端边界：空输入，生成一个极短的静音文件命令兜底
            return f"ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 0.1 -y {output_path}"

        cleaned_tracks = []
        for track in tracks:
            ct = self._clean_track_data(track)
            if ct and ct["file_path"]:
                cleaned_tracks.append(ct)

        if not cleaned_tracks:
            return f"ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 0.1 -y {output_path}"

        # 构建 FFmpeg 命令
        # ffmpeg -i input1.wav -i input2.wav -filter_complex "[0:a]volume=1.0,adelay=1000|1000[a0];[1:a]volume=0.8,adelay=2000|2000[a1];[a0][a1]amix=inputs=2:duration=longest[out]" -map "[out]" output.wav

        cmd_parts = ["ffmpeg"]

        # 输入文件
        for track in cleaned_tracks:
            cmd_parts.extend(["-i", f'"{track["file_path"]}"'])

        # 滤镜图
        filter_complex = []
        mix_inputs = []

        for i, track in enumerate(cleaned_tracks):
            # adelay in milliseconds
            delay_ms = int(track["start_time"] * 1000)
            vol = track["volume"]

            # 每个输入的滤镜链
            filters = []
            if vol != 1.0:
                filters.append(f"volume={vol}")

            if delay_ms > 0:
                filters.append(f"adelay={delay_ms}|{delay_ms}")

            if filters:
                filter_str = f"[{i}:a]" + ",".join(filters) + f"[a{i}]"
                filter_complex.append(filter_str)
                mix_inputs.append(f"[a{i}]")
            else:
                mix_inputs.append(f"[{i}:a]")

        # 混音节点
        mix_inputs_str = "".join(mix_inputs)
        num_inputs = len(cleaned_tracks)

        # amix filter
        if num_inputs > 1:
            amix_str = f"{mix_inputs_str}amix=inputs={num_inputs}:duration=longest:dropout_transition=2[out]"
            filter_complex.append(amix_str)

            cmd_parts.extend([
                "-filter_complex", f'"{";".join(filter_complex)}"',
                "-map", '"[out]"'
            ])
        else:
            # 只有一个输入时，如果有滤镜则应用滤镜，否则直接复制
            if filter_complex:
                cmd_parts.extend([
                    "-filter_complex", f'"{";".join(filter_complex)}"',
                    "-map", f'"[a0]"'
                ])
            else:
                # 只复制
                cmd_parts.extend(["-c:a", "copy"])

        cmd_parts.extend(["-y", f'"{output_path}"'])

        return " ".join(cmd_parts)

    def synthesize_waveform_data(self, tracks: List[Dict[str, Any]], duration: float) -> Dict[str, Any]:
        """
        波形合成数据生成，用于前端UI展示
        """
        duration = max(0.1, self._safe_float(duration, 1.0))

        waveform_data = {
            "duration": duration,
            "peaks": [],
            "events": []
        }

        if not tracks:
            return waveform_data

        cleaned_tracks = [self._clean_track_data(t) for t in tracks if isinstance(t, dict)]

        for track in cleaned_tracks:
            if not track.get("file_path"):
                continue

            start_t = track["start_time"]
            if start_t >= duration:
                continue

            intensity = track["volume"]
            event_type = track["type"]

            # 根据类型设置波形峰值特征
            peak_width = 0.5
            if event_type == "impact":
                peak_width = 0.2
                intensity *= 1.5
            elif event_type == "transition":
                peak_width = 1.0

            waveform_data["events"].append({
                "time": start_t,
                "type": event_type,
                "intensity": intensity
            })

        # 简单模拟合成波形包络
        for t in range(0, int(duration * 10)):
            current_time = t / 10.0
            val = 0.0
            for event in waveform_data["events"]:
                # 简单指数衰减模型
                if current_time >= event["time"]:
                    decay = max(0, 1.0 - (current_time - event["time"]) * 2.0) # 每0.5秒衰减完
                    val += event["intensity"] * decay

            waveform_data["peaks"].append(round(min(1.0, val / max(1.0, len(waveform_data["events"]) * 0.5)), 2))

        return waveform_data
