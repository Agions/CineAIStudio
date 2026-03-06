"""
ClipFlow 视频处理服务模块

提供三大核心视频制作功能:
- CommentaryMaker: AI 视频解说
- MashupMaker: AI 视频混剪
- MonologueMaker: AI 第一人称独白
- TransitionEffects: 视频转场效果
- ParallelProcessor: 并行处理器
- BaseVideoMaker: 视频制作器基类
"""

from .base_maker import BaseVideoMaker, BaseProject, ProgressMixin, merge_audio_files, composite_video_with_audio
from .commentary_maker import CommentaryMaker, CommentaryProject, CommentaryStyle, CommentarySegment
from .mashup_maker import MashupMaker, MashupProject, MashupStyle, ClipInfo, BeatInfo
from .monologue_maker import MonologueMaker, MonologueProject, MonologueStyle, MonologueSegment, EmotionType
from .transition_effects import TransitionEffects, TransitionType, TransitionConfig
from .parallel_processor import ParallelProcessor, TaskResult, ProcessingStats


__all__ = [
    # 基类
    "BaseVideoMaker",
    "BaseProject",
    "ProgressMixin",
    "merge_audio_files",
    "composite_video_with_audio",

    # 视频解说
    "CommentaryMaker",
    "CommentaryProject",
    "CommentaryStyle",
    "CommentarySegment",

    # 视频混剪
    "MashupMaker",
    "MashupProject",
    "MashupStyle",
    "ClipInfo",
    "BeatInfo",

    # 第一人称独白
    "MonologueMaker",
    "MonologueProject",
    "MonologueStyle",
    "MonologueSegment",
    "EmotionType",

    # 转场效果
    "TransitionEffects",
    "TransitionType",
    "TransitionConfig",

    # 并行处理
    "ParallelProcessor",
    "TaskResult",
    "ProcessingStats",
]
