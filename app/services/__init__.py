"""
VideoForge 服务模块

提供以下核心服务:
- ai: AI大模型、视觉、语音服务
- video: 视频制作（解说、混剪、独白）
- audio: 音频处理（节拍检测、音画同步）
- export: 导出服务（剪映、PR、FCP、DaVinci）
- video_tools: 病毒视频处理（字幕、节奏分析）
- core: 核心功能（工作流、撤销管理）
- publish: 多平台发布 [暂时关闭]
- ui: UI 图形界面（位于 app/ui/）
"""

# 子模块
from . import ai
from . import video
from . import audio
from . import export
from . import video_tools
from . import core

# 多平台发布功能暂时关闭
# from . import publish

# 兼容层
from .ai_service_manager import AIServiceManager, ServiceStatus, get_ai_service_manager
from .ai_service.mock_ai_service import MockAIService


__all__ = [
    # 子模块
    "ai",
    "video",
    "audio",
    "export",
    "video_tools",
    "core",
    # publish,  # 暂时关闭
    # 兼容层
    "AIServiceManager",
    "ServiceStatus",
    "get_ai_service_manager",
    "MockAIService",
]
