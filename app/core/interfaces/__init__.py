"""
核心接口定义模块

定义应用程序中使用的所有抽象接口，实现依赖倒置原则。
"""

from .service_interface import IService, IInitializable, IConfigurable
from .video_processor_interface import IVideoProcessor, IVideoAnalyzer
from .ai_service_interface import IAIService, IVisionService, IVoiceService
from .export_interface import IExporter, IProjectExporter
from .cache_interface import ICache, ICacheable
from .progress_interface import IProgressTracker, IProgressReporter

__all__ = [
    # 基础接口
    'IService',
    'IInitializable',
    'IConfigurable',
    # 视频处理接口
    'IVideoProcessor',
    'IVideoAnalyzer',
    # AI服务接口
    'IAIService',
    'IVisionService',
    'IVoiceService',
    # 导出接口
    'IExporter',
    'IProjectExporter',
    # 缓存接口
    'ICache',
    'ICacheable',
    # 进度接口
    'IProgressTracker',
    'IProgressReporter',
]
