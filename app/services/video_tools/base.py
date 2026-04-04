"""
视频处理服务基类

提供视频处理服务的公共基类和接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class VideoMetadata:
    """视频元数据"""
    path: str
    duration: float = 0.0
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    bitrate: int = 0
    codec: str = ""
    size_bytes: int = 0


@dataclass
class ProcessingResult:
    """处理结果基类"""
    success: bool
    output_path: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class IVideoProcessor(ABC):
    """视频处理器接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """处理器名称"""
        pass

    @abstractmethod
    def analyze(self, video_path: str) -> VideoMetadata:
        """分析视频获取元数据"""
        pass

    @abstractmethod
    def process(self, video_path: str, **kwargs) -> ProcessingResult:
        """处理视频"""
        pass

    @abstractmethod
    def validate_input(self, video_path: str) -> bool:
        """验证输入视频"""
        pass


class BaseVideoProcessor(IVideoProcessor):
    """
    视频处理器基类

    提供公共的视频处理功能
    """

    def __init__(self):
        self._supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']

    @property
    def supported_formats(self) -> List[str]:
        """支持的视频格式"""
        return self._supported_formats

    def validate_input(self, video_path: str) -> bool:
        """验证输入视频"""
        path = Path(video_path)

        if not path.exists():
            return False

        if path.suffix.lower() not in self._supported_formats:
            return False

        return True

    def analyze(self, video_path: str) -> VideoMetadata:
        """分析视频获取元数据"""
        from .ffmpeg_tool import FFmpegTool

        duration = FFmpegTool.get_duration(video_path)
        width, height = FFmpegTool.get_resolution(video_path)
        fps = FFmpegTool.get_framerate(video_path)

        # 获取文件大小
        size_bytes = 0
        try:
            size_bytes = Path(video_path).stat().st_size
        except OSError:
            pass

        # 获取码率
        bitrate = FFmpegTool.get_bitrate(video_path)

        return VideoMetadata(
            path=video_path,
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            bitrate=bitrate,
            size_bytes=size_bytes,
        )

    def get_output_path(self, input_path: str, suffix: str = "_processed") -> str:
        """生成输出路径"""
        path = Path(input_path)
        stem = path.stem
        suffix_str = f"{suffix}{path.suffix}"
        return str(path.parent / f"{stem}{suffix_str}")
