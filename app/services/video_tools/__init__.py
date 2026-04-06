"""
视频工具服务

活跃模块：
- FFmpegTool        FFmpeg 封装（视频/音频处理）
- CaptionGenerator  动态字幕生成
- BaseVideoProcessor / IVideoProcessor  视频处理基类

已移至 _legacy/ 的历史模块（不再维护）：
clip_repurposing / clip_scorer / pace_analyzer /
silence_remover / content_enhancer
"""

from .ffmpeg_tool import FFmpegTool
from .base import (
    IVideoProcessor,
    BaseVideoProcessor,
    VideoMetadata,
    ProcessingResult,
)
from .caption_generator import CaptionGenerator, Caption, CaptionConfig, CaptionStyle

__all__ = [
    # 工具
    "FFmpegTool",

    # 基类
    "IVideoProcessor",
    "BaseVideoProcessor",
    "VideoMetadata",
    "ProcessingResult",

    # 字幕生成
    "CaptionGenerator",
    "Caption",
    "CaptionConfig",
    "CaptionStyle",
]
