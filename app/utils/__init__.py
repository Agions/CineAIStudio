#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具模块

提供通用工具函数和类：
- config: 配置管理
- logger: 日志系统
- i18n: 国际化
- performance: 性能优化
- task_manager: 任务管理
- video_utils: 视频处理
- error_handler: 错误处理
"""

# 配置管理
from app.utils.config import (
    ConfigManager,
    AppConfig,
    APIKeys,
    config,
    api_keys,
    get_config_manager,
)

# 日志
from app.utils.logger import (
    setup_logger,
    get_logger,
    debug,
    info,
    warning,
    error,
    critical,
)

# 国际化
from app.utils.i18n import I18n, t, set_locale, get_locale

# 性能
from app.utils.performance import (
    LazyLoader,
    MemoryCache,
    PerformanceMonitor,
    cached,
    cached_property,
    timed,
    default_cache,
    perf_monitor,
)

# 任务管理
from app.utils.task_manager import (
    TaskManager,
    Task,
    TaskStatus,
    task_manager,
    run_background,
    get_task_status,
    cancel_task,
)

# 视频工具
from app.utils.video_utils import (
    VideoInfo,
    get_video_info,
    extract_thumbnail,
    get_video_duration,
    get_video_resolution,
    get_video_fps,
    concat_videos,
    trim_video,
    add_subtitle,
    change_speed,
    generate_waveform,
)

# 错误处理
from app.utils.error_handler import (
    ErrorHandler,
    ErrorType,
    classify_error,
    handle_error,
)

__all__ = [
    # Config
    "ConfigManager",
    "AppConfig", 
    "APIKeys",
    "config",
    "api_keys",
    "get_config_manager",
    # Logger
    "setup_logger",
    "get_logger",
    "debug",
    "info",
    "warning", 
    "error",
    "critical",
    # I18n
    "I18n",
    "t",
    "set_locale",
    "get_locale",
    # Performance
    "LazyLoader",
    "MemoryCache",
    "PerformanceMonitor",
    "cached",
    "cached_property",
    "timed",
    "default_cache",
    "perf_monitor",
    # Task
    "TaskManager",
    "Task",
    "TaskStatus",
    "task_manager",
    "run_background",
    "get_task_status",
    "cancel_task",
    # Video
    "VideoInfo",
    "get_video_info",
    "extract_thumbnail",
    "get_video_duration",
    "get_video_resolution",
    "get_video_fps",
    "concat_videos",
    "trim_video",
    "add_subtitle",
    "change_speed",
    "generate_waveform",
    # Error
    "ErrorHandler",
    "ErrorType",
    "classify_error",
    "handle_error",
]
