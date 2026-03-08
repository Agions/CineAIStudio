#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频服务模块

核心功能:
- CommentaryMaker: AI 视频解说
- MashupMaker: AI 视频混剪
- MonologueMaker: AI 第一人称独白
"""

from .commentary_maker import CommentaryMaker, create_commentary_video
from .mashup_maker import MashupMaker, create_mashup_video
from .monologue_maker import MonologueMaker, create_monologue_video

# 字幕相关
from .subtitle_extractor import SubtitleExtractor, extract_subtitles
from .subtitle_remover import remove_video_subtitles
from .subtitle_analyzer import analyze_subtitle_content, sync_narration

# 工具
from .story_builder import StoryBuilder, StoryLine, create_story
from .video_deduplicator import make_video_unique, differentiate_content

# 预设
from .presets import (
    CommentaryConfig,
    MashupConfig,
    MonologueConfig,
    PresetFactory,
)

# 导出
from .quick_export import quick_export, quick_export_with_filter


__all__ = [
    # 核心功能
    "CommentaryMaker",
    "create_commentary_video",
    "MashupMaker", 
    "create_mashup_video",
    "MonologueMaker",
    "create_monologue_video",
    
    # 字幕
    "SubtitleExtractor",
    "extract_subtitles",
    "remove_video_subtitles",
    "analyze_subtitle_content",
    "sync_narration",
    
    # 工具
    "StoryBuilder",
    "StoryLine",
    "create_story",
    "make_video_unique",
    "differentiate_content",
    
    # 预设
    "CommentaryConfig",
    "MashupConfig", 
    "MonologueConfig",
    "PresetFactory",
    
    # 导出
    "quick_export",
    "quick_export_with_filter",
]
