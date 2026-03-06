"""
FFmpeg 工具模块

提供 FFmpeg/FFprobe 调用的公共工具函数
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple


class FFmpegTool:
    """FFmpeg 工具类"""

    @staticmethod
    def get_duration(video_path: str) -> float:
        """获取视频时长（秒）"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json', video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return float(data.get('format', {}).get('duration', 0))
        except (subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError):
            return 0.0

    @staticmethod
    def get_resolution(video_path: str) -> Tuple[int, int]:
        """获取视频分辨率 (width, height)"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-print_format', 'json',
            '-show_streams', video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    return (stream.get('width', 1920), stream.get('height', 1080))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass
        return (1920, 1080)

    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, Any]:
        """获取完整视频信息"""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return {}

    @staticmethod
    def run_command(
        cmd: List[str],
        capture: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess:
        """运行 FFmpeg 命令"""
        return subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=check,
        )

    @staticmethod
    def parse_time_output(output: str, key: str) -> Optional[float]:
        """从 FFmpeg 输出解析时间值"""
        for line in output.split('\n'):
            if key in line:
                try:
                    # 格式: key=value 或 key: value
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        return float(parts[1].strip())
                except (ValueError, IndexError):
                    continue
        return None


__all__ = ["FFmpegTool"]
