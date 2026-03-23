"""
应用配置模块

提供应用程序运行所需的配置类
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ThemeConfig:
    """主题配置"""
    name: str = "light"
    primary_color: str = "#3B82F6"
    accent_color: str = "#10B981"
    font_family: str = "Microsoft YaHei, PingFang SC"
    font_size: int = 14


@dataclass
class WindowConfig:
    """窗口配置"""
    width: int = 1280
    height: int = 800
    x: Optional[int] = None
    y: Optional[int] = None
    maximized: bool = False
    fullscreen: bool = False


@dataclass
class EditorConfig:
    """编辑器配置"""
    auto_save: bool = True
    auto_save_interval: int = 300  # 秒
    undo_limit: int = 50
    grid_visible: bool = True
    snap_to_grid: bool = True
    thumbnail_size: int = 120


@dataclass
class PerformanceConfig:
    """性能配置"""
    max_cache_size: int = 500  # MB
    preview_quality: str = "medium"
    hardware_acceleration: bool = True
    parallel_tasks: int = 4
    thumbnail_cache: bool = True


@dataclass
class AIConfig:
    """AI 配置"""
    default_provider: str = "qwen"
    vision_enabled: bool = True
    voice_provider: str = "edge"
    auto_generate_subtitle: bool = True
    scene_analysis_threshold: float = 0.3


@dataclass
class AppConfig:
    """应用程序配置"""
    version: str = "3.0.0"
    language: str = "zh-CN"
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    window: WindowConfig = field(default_factory=WindowConfig)
    editor: EditorConfig = field(default_factory=EditorConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    recent_files: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


# 便捷函数
def create_default_config() -> AppConfig:
    """创建默认配置"""
    return AppConfig()


__all__ = [
    "AppConfig",
    "ThemeConfig",
    "WindowConfig",
    "EditorConfig",
    "PerformanceConfig",
    "AIConfig",
    "create_default_config",
]
