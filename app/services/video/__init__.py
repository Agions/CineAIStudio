"""
视频制作服务

保留的活跃模块：
- monologue_maker.py  第一人称解说视频制作（核心）
- base_maker.py        视频 Maker 基类
"""

from .base_maker import BaseVideoMaker
from .monologue_maker import (
    MonologueMaker,
    MonologueProject,
    MonologueSegment,
    MonologueStyle,
)

__all__ = [
    "BaseVideoMaker",
    "MonologueMaker",
    "MonologueProject",
    "MonologueSegment",
    "MonologueStyle",
]
