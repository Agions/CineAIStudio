"""
ClipFlow 服务模块

提供以下核心服务:
- ai: AI大模型、视觉、语音服务
- video: 视频制作（解说、混剪、独白）
- audio: 音频处理（节拍检测、音画同步）
- export: 导出服务（剪映、PR、FCP、DaVinci）
- viral_video: 病毒视频处理（字幕、节奏分析）
- core: 核心功能（工作流、撤销管理）
"""

# 子模块
from . import ai
from . import video
from . import audio
from . import export
from . import viral_video
from . import core

# 兼容层
from .ai_service_manager import AIServiceManager, ServiceStatus, get_ai_service_manager


__all__ = [
    # 子模块
    "ai",
    "video",
    "audio",
    "export",
    "viral_video",
    "core",
    # 兼容层
    "AIServiceManager",
    "ServiceStatus",
    "get_ai_service_manager",
]
