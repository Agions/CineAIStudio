#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频服务模块
提供视频编辑、分析和导出功能
"""

from .video_editor import (
    MediaItem,
    VideoClip,
    AudioClip,
    Project,
    VideoEditorService
)

from .video_analyzer import (
    Scene,
    HighlightSegment,
    VideoAnalysisResult,
    VideoAnalyzerService
)


__all__ = [
    # video_editor.py
    "MediaItem",
    "VideoClip",
    "AudioClip",
    "Project",
    "VideoEditorService",
    # video_analyzer.py
    "Scene",
    "HighlightSegment",
    "VideoAnalysisResult",
    "VideoAnalyzerService"
]
