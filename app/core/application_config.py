#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 应用程序配置模块
定义应用程序的各种配置类
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path


@dataclass
class ThemeConfig:
    """主题配置"""
    mode: str = "dark"  # dark, light, auto
    primary_color: str = "#2196F3"
    secondary_color: str = "#FFC107"
    accent_color: str = "#FF5722"
    background_color: str = "#1a1a1a"
    text_color: str = "#ffffff"
    font_family: str = "Arial"
    font_size: int = 14
    enable_animations: bool = True
    custom_css: str = ""


@dataclass
class WindowConfig:
    """窗口配置"""
    title: str = "CineAIStudio v2.0"
    width: int = 1200
    height: int = 800
    min_width: int = 800
    min_height: int = 600
    max_width: int = 4096
    max_height: int = 2160
    is_maximized: bool = False
    is_fullscreen: bool = False
    remember_geometry: bool = True
    show_splash: bool = True
    enable_dpi_scaling: bool = True


@dataclass
class EditorConfig:
    """编辑器配置"""
    auto_save: bool = True
    auto_save_interval: int = 300  # 秒
    backup_count: int = 5
    undo_stack_size: int = 50
    default_project_template: str = "default"
    enable_timeline_cache: bool = True
    enable_preview_cache: bool = True
    proxy_resolution: str = "1280x720"
    export_quality: str = "high"
    timeline_fps: int = 30
    preview_fps: int = 30
    audio_sample_rate: int = 48000
    audio_bitrate: int = 320000


@dataclass
class PerformanceConfig:
    """性能配置"""
    max_cpu_usage: int = 80
    max_memory_usage: int = 2048  # MB
    enable_gpu_acceleration: bool = True
    gpu_memory_limit: int = 1024  # MB
    thread_pool_size: int = 4
    cache_size: int = 1024  # MB
    enable_background_processing: bool = True
    enable_preview_optimization: bool = True
    enable_proxy_generation: bool = True
    max_concurrent_tasks: int = 3


@dataclass
class AIConfig:
    """AI功能配置"""
    enable_ai_features: bool = True
    default_ai_provider: str = "openai"  # openai, local, etc.
    ai_api_key: Optional[str] = None
    ai_base_url: Optional[str] = None
    ai_model: str = "gpt-4"
    max_tokens: int = 2000
    temperature: float = 0.7
    enable_cache: bool = True
    cache_expire_time: int = 3600  # 秒
    enable_batch_processing: bool = True
    max_batch_size: int = 10
    enable_real_time_analysis: bool = True
    analysis_interval: int = 5  # 秒
    enable_auto_subtitle: bool = True
    subtitle_languages: List[str] = field(default_factory=lambda: ["zh-CN", "en"])
    enable_auto_enhancement: bool = True
    enhancement_quality: str = "high"


@dataclass
class AppConfig:
    """应用程序主配置"""
    version: str = "2.0.0"
    language: str = "zh-CN"
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    window: WindowConfig = field(default_factory=WindowConfig)
    editor: EditorConfig = field(default_factory=EditorConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    recent_files: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    # 系统配置
    app_data_dir: Optional[str] = None
    temp_dir: Optional[str] = None
    log_dir: Optional[str] = None
    plugin_dir: Optional[str] = None

    # 用户配置
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    license_key: Optional[str] = None

    # 开发配置
    debug_mode: bool = False
    log_level: str = "INFO"
    enable_console: bool = True
    enable_dev_tools: bool = False

    # 更新配置
    auto_update: bool = True
    update_channel: str = "stable"  # stable, beta, dev
    last_update_check: Optional[str] = None

    # 网络配置
    enable_proxy: bool = False
    proxy_url: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    timeout: int = 30

    # 界面配置
    show_tips: bool = True
    show_welcome_screen: bool = True
    show_tooltips: bool = True
    enable_shortcuts: bool = True
    custom_shortcuts: Dict[str, str] = field(default_factory=dict)

    # 文件配置
    default_project_dir: Optional[str] = None
    default_export_dir: Optional[str] = None
    default_import_dir: Optional[str] = None
    file_filters: List[str] = field(default_factory=lambda: [
        "*.mp4", "*.avi", "*.mkv", "*.mov", "*.wmv", "*.flv", "*.webm",
        "*.mp3", "*.wav", "*.aac", "*.flac", "*.ogg",
        "*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif", "*.tiff"
    ])

    # 插件配置
    enable_plugins: bool = True
    plugin_load_path: List[str] = field(default_factory=list)
    disabled_plugins: List[str] = field(default_factory=list)

    # 快捷键配置
    shortcuts: Dict[str, str] = field(default_factory=lambda: {
        "new_project": "Ctrl+N",
        "open_project": "Ctrl+O",
        "save_project": "Ctrl+S",
        "save_as": "Ctrl+Shift+S",
        "export": "Ctrl+E",
        "undo": "Ctrl+Z",
        "redo": "Ctrl+Y",
        "cut": "Ctrl+X",
        "copy": "Ctrl+C",
        "paste": "Ctrl+V",
        "delete": "Delete",
        "select_all": "Ctrl+A",
        "play_pause": "Space",
        "stop": "Escape",
        "fullscreen": "F11",
        "help": "F1"
    })

    def __post_init__(self):
        """后初始化处理"""
        # 设置默认目录
        if not self.app_data_dir:
            import os
            self.app_data_dir = os.path.join(os.path.expanduser("~"), ".cineaistudio")

        if not self.temp_dir:
            import os
            self.temp_dir = os.path.join(self.app_data_dir, "temp")

        if not self.log_dir:
            import os
            self.log_dir = os.path.join(self.app_data_dir, "logs")

        if not self.plugin_dir:
            import os
            self.plugin_dir = os.path.join(self.app_data_dir, "plugins")

        if not self.default_project_dir:
            import os
            self.default_project_dir = os.path.join(os.path.expanduser("~"), "Documents", "CineAIStudio")

        if not self.default_export_dir:
            import os
            self.default_export_dir = os.path.join(os.path.expanduser("~"), "Videos", "CineAIStudio")

        if not self.default_import_dir:
            import os
            self.default_import_dir = os.path.join(os.path.expanduser("~"), "Videos")

    def get_theme_colors(self) -> Dict[str, str]:
        """获取主题颜色配置"""
        return {
            "primary": self.theme.primary_color,
            "secondary": self.theme.secondary_color,
            "accent": self.theme.accent_color,
            "background": self.theme.background_color,
            "text": self.theme.text_color
        }

    def get_window_geometry(self) -> Dict[str, int]:
        """获取窗口几何信息"""
        return {
            "width": self.window.width,
            "height": self.window.height,
            "min_width": self.window.min_width,
            "min_height": self.window.min_height
        }

    def get_editor_settings(self) -> Dict[str, Any]:
        """获取编辑器设置"""
        return {
            "auto_save": self.editor.auto_save,
            "auto_save_interval": self.editor.auto_save_interval,
            "backup_count": self.editor.backup_count,
            "undo_stack_size": self.editor.undo_stack_size,
            "timeline_fps": self.editor.timeline_fps,
            "preview_fps": self.editor.preview_fps
        }

    def get_performance_settings(self) -> Dict[str, Any]:
        """获取性能设置"""
        return {
            "max_cpu_usage": self.performance.max_cpu_usage,
            "max_memory_usage": self.performance.max_memory_usage,
            "enable_gpu_acceleration": self.performance.enable_gpu_acceleration,
            "thread_pool_size": self.performance.thread_pool_size,
            "cache_size": self.performance.cache_size
        }

    def get_ai_settings(self) -> Dict[str, Any]:
        """获取AI设置"""
        return {
            "enable_ai_features": self.ai.enable_ai_features,
            "default_ai_provider": self.ai.default_ai_provider,
            "ai_model": self.ai.ai_model,
            "max_tokens": self.ai.max_tokens,
            "temperature": self.ai.temperature,
            "enable_cache": self.ai.enable_cache,
            "enable_auto_subtitle": self.ai.enable_auto_subtitle,
            "subtitle_languages": self.ai.subtitle_languages
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """从字典创建配置"""
        return cls(**data)

    def save_to_file(self, file_path: str) -> bool:
        """保存配置到文件"""
        try:
            import json

            # 创建目录
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

            return True
        except Exception:
            return False

    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['AppConfig']:
        """从文件加载配置"""
        try:
            import json

            if not Path(file_path).exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return cls.from_dict(data)
        except Exception:
            return None