"""
视频制作服务

保留的活跃模块（5个）：
- commentary_maker.py  解说视频制作
- mashup_maker.py     混剪视频制作
- monologue_maker.py  单人口播视频制作
- beat_sync_maker.py  节拍同步混剪
- base_maker.py      视频 Maker 基类

已移至 _legacy/ 的历史模块（不再维护）：
effects_presets / highlight_detector / parallel_processor /
pipeline / presets / quality_analyzer / quick_export /
story_builder / subtitle_analyzer / subtitle_extractor /
subtitle_remover / thumbnail_cache / transition_effects /
video_deduplicator / video_enhancer
"""

from .base_maker import BaseVideoMaker
from .commentary_maker import CommentaryMaker
from .mashup_maker import MashupMaker
from .monologue_maker import MonologueMaker
from .beat_sync_maker import BeatSyncMashupMaker
from .transition_effects import TransitionType, TransitionEffects

__all__ = [
    "BaseVideoMaker",
    "CommentaryMaker",
    "MashupMaker",
    "MonologueMaker",
    "BeatSyncMashupMaker",
    "TransitionType",
    "TransitionEffects",
]
