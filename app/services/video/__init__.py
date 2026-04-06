"""
视频制作服务

保留的活跃模块：
- monologue_maker.py  第一人称解说视频制作（核心）
- base_maker.py        视频 Maker 基类

已移至 _legacy/ 的历史模块（不再维护）：
effects_presets / highlight_detector / parallel_processor /
pipeline / presets / quality_analyzer / quick_export /
story_builder / subtitle_analyzer / subtitle_extractor /
subtitle_remover / thumbnail_cache / transition_effects /
video_deduplicator / video_enhancer /
commentary_maker / mashup_maker / beat_sync_maker /
transition_effects
"""

from .base_maker import BaseVideoMaker
from .monologue_maker import MonologueMaker

__all__ = [
    "BaseVideoMaker",
    "MonologueMaker",
]
