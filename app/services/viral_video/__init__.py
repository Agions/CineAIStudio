"""
Viral Video Service
百万爆款视频处理服务

提供以下核心功能：
- 静音检测与移除 (Silence Removal)
- 智能节奏分析 (Pace Analysis)
- 动态字幕生成 (Dynamic Caption)
- 视觉冲击力增强 (Visual Impact Enhancement)
- FFmpeg 工具 (FFmpegTool)
"""

from .ffmpeg_tool import FFmpegTool
from .silence_remover import SilenceRemover, SilenceSegment, RemovalResult
from .pace_analyzer import PaceAnalyzer, PaceAnalysisResult, PaceMetrics, PaceLevel
from .caption_generator import CaptionGenerator, Caption, CaptionConfig, CaptionStyle

__all__ = [
    # 工具
    "FFmpegTool",

    # 静音处理
    "SilenceRemover",
    "SilenceSegment",
    "RemovalResult",

    # 节奏分析
    "PaceAnalyzer",
    "PaceAnalysisResult",
    "PaceMetrics",
    "PaceLevel",

    # 字幕生成
    "CaptionGenerator",
    "Caption",
    "CaptionConfig",
    "CaptionStyle",
]
