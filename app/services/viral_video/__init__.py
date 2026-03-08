"""
Viral Video Service
爆款视频处理服务
"""

from .ffmpeg_tool import FFmpegTool
from .silence_remover import SilenceRemover
from .pace_analyzer import PaceAnalyzer
from .caption_generator import CaptionGenerator, CaptionStyle
from .content_enhancer import ContentEnhancer, SmartClipSelector
from .video_deduplicator import VideoDeduplicator, make_video_unique


__all__ = [
    # 工具
    "FFmpegTool",
    
    # 静音处理
    "SilenceRemover",
    
    # 节奏分析
    "PaceAnalyzer",
    
    # 字幕
    "CaptionGenerator",
    "CaptionStyle",
    
    # 内容增强
    "ContentEnhancer",
    "SmartClipSelector",
    
    # 去重
    "VideoDeduplicator",
    "make_video_unique",
]
