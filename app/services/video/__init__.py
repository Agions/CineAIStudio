"""
ClipFlow 视频处理服务模块

提供三大核心视频制作功能:
- CommentaryMaker: AI 视频解说
- MashupMaker: AI 视频混剪  
- MonologueMaker: AI 第一人称独白
- TransitionEffects: 视频转场效果
- ParallelProcessor: 并行处理器
"""

from .commentary_maker import CommentaryMaker, CommentaryProject, CommentaryStyle
from .mashup_maker import MashupMaker, MashupProject, MashupStyle
from .monologue_maker import MonologueMaker, MonologueProject, MonologueStyle
from .transition_effects import TransitionEffects, TransitionType, TransitionConfig
from .parallel_processor import ParallelProcessor, TaskResult, ProcessingStats


__all__ = [
    # 视频解说
    'CommentaryMaker',
    'CommentaryProject',
    'CommentaryStyle',
    
    # 视频混剪
    'MashupMaker',
    'MashupProject',
    'MashupStyle',
    
    # 第一人称独白
    'MonologueMaker',
    'MonologueProject',
    'MonologueStyle',
    
    # 转场效果
    'TransitionEffects',
    'TransitionType',
    'TransitionConfig',
    
    # 并行处理
    'ParallelProcessor',
    'TaskResult',
    'ProcessingStats',
]
