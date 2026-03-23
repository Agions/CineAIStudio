#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 插件接口定义
定义插件必须实现的标准接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Callable
import os


class PluginType(Enum):
    """插件类型"""
    VIDEO_EFFECT = "video_effect"          # 视频效果
    AUDIO_EFFECT = "audio_effect"          # 音频效果
    TRANSITION = "transition"              # 转场效果
    TEXT_OVERLAY = "text_overlay"          # 文字叠加
    COLOR_GRADING = "color_grading"        # 调色
    MOTION_GRAPHICS = "motion_graphics"    # 动态图形
    AI_ENHANCEMENT = "ai_enhancement"      # AI增强
    EXPORT_FORMAT = "export_format"        # 导出格式
    IMPORT_FORMAT = "import_format"        # 导入格式
    ANALYSIS_TOOL = "analysis_tool"        # 分析工具
    UTILITY = "utility"                    # 实用工具
    THEME = "theme"                        # 主题
    INTEGRATION = "integration"            # 第三方集成


class PluginStatus(Enum):
    """插件状态"""
    UNLOADED = "unloaded"                  # 未加载
    LOADING = "loading"                    # 加载中
    LOADED = "loaded"                      # 已加载
    INITIALIZING = "initializing"          # 初始化中
    ACTIVE = "active"                      # 激活
    ERROR = "error"                        # 错误
    DISABLED = "disabled"                  # 禁用


@dataclass
class PluginInfo:
    """插件信息"""
    id: str                               # 插件唯一ID
    name: str                             # 插件名称
    version: str                          # 版本号
    description: str                      # 描述
    author: str                           # 作者
    email: Optional[str] = None           # 联系邮箱
    website: Optional[str] = None         # 官网
    plugin_type: PluginType = PluginType.UTILITY
    dependencies: List[str] = None        # 依赖的其他插件
    min_app_version: str = "1.0.0"        # 最低应用版本
    max_app_version: Optional[str] = None # 最高应用版本
    license: str = "MIT"                  # 许可证
    tags: List[str] = None                # 标签
    icon_path: Optional[str] = None       # 图标路径
    config_schema: Optional[Dict] = None  # 配置模式


@dataclass
class PluginContext:
    """插件上下文"""
    # 核心服务
    logger: Any
    event_bus: Any
    config_manager: Any
    project_manager: Any

    # UI相关
    main_window: Any
    ui_components: Any

    # 服务相关
    video_service: Any
    ai_service: Any
    export_service: Any

    # 插件系统
    plugin_manager: Any

    # 其他
    temp_dir: str
    plugin_dir: str


class PluginInterface(ABC):
    """插件接口基类"""

    def __init__(self):
        self._info: Optional[PluginInfo] = None
        self._context: Optional[PluginContext] = None
        self._status = PluginStatus.UNLOADED
        self._config: Dict[str, Any] = {}

    @property
    def info(self) -> PluginInfo:
        """获取插件信息"""
        if self._info is None:
            self._info = self.get_plugin_info()
        return self._info

    @property
    def context(self) -> PluginContext:
        """获取插件上下文"""
        if self._context is None:
            raise RuntimeError("Plugin context not set")
        return self._context

    @property
    def status(self) -> PluginStatus:
        """获取插件状态"""
        return self._status

    @property
    def config(self) -> Dict[str, Any]:
        """获取插件配置"""
        return self._config

    # 生命周期方法

    @abstractmethod
    def get_plugin_info(self) -> PluginInfo:
        """返回插件信息（必须实现）"""
        pass

    def initialize(self, context: PluginContext, config: Dict[str, Any] = None) -> bool:
        """初始化插件"""
        try:
            self._status = PluginStatus.INITIALIZING
            self._context = context
            self._config = config or {}

            # 记录日志
            context.logger.info(f"Initializing plugin: {self.info.name}")

            # 调用具体插件的初始化方法
            success = self.on_initialize()

            if success:
                self._status = PluginStatus.ACTIVE
                context.logger.info(f"Plugin initialized successfully: {self.info.name}")
                self.on_activated()
            else:
                self._status = PluginStatus.ERROR
                context.logger.error(f"Plugin initialization failed: {self.info.name}")

            return success

        except Exception as e:
            self._status = PluginStatus.ERROR
            if self._context:
                self._context.logger.error(f"Plugin initialization error: {e}")
            return False

    def shutdown(self) -> bool:
        """关闭插件"""
        try:
            self._status = PluginStatus.LOADED
            success = self.on_shutdown()

            if self._context:
                self._context.logger.info(f"Plugin shutdown: {self.info.name}")

            self._status = PluginStatus.UNLOADED
            return success

        except Exception as e:
            self._status = PluginStatus.ERROR
            if self._context:
                self._context.logger.error(f"Plugin shutdown error: {e}")
            return False

    def get_config_ui(self) -> Optional[Any]:
        """获取配置UI组件"""
        return None

    # 事件回调（可选实现）

    def on_initialize(self) -> bool:
        """插件初始化时调用（可选实现）"""
        return True

    def on_activated(self) -> None:
        """插件激活时调用（可选实现）"""
        pass

    def on_deactivated(self) -> None:
        """插件停用时调用（可选实现）"""
        pass

    def on_shutdown(self) -> bool:
        """插件关闭时调用（可选实现）"""
        return True

    def on_config_changed(self, config: Dict[str, Any]) -> None:
        """配置变更时调用（可选实现）"""
        self._config = config

    def on_project_opened(self, project: Any) -> None:
        """项目打开时调用（可选实现）"""
        pass

    def on_project_saved(self, project: Any) -> None:
        """项目保存时调用（可选实现）"""
        pass

    def on_project_closed(self, project: Any) -> None:
        """项目关闭时调用（可选实现）"""
        pass

    # 功能接口（根据插件类型选择性实现）

    def get_effects(self) -> List[Dict[str, Any]]:
        """获取效果列表（视频/音频/转场插件）"""
        return []

    def get_export_presets(self) -> List[Dict[str, Any]]:
        """获取导出预设（导出插件）"""
        return []

    def get_import_formats(self) -> List[str]:
        """获取支持的导入格式（导入插件）"""
        return []

    def get_analysis_tools(self) -> List[Dict[str, Any]]:
        """获取分析工具（分析插件）"""
        return []

    def get_theme_resources(self) -> Dict[str, str]:
        """获取主题资源（主题插件）"""
        return {}

    # 效果处理接口

    def process_video_effect(self, clip_id: str, effect_id: str,
                           parameters: Dict[str, Any]) -> bool:
        """处理视频效果"""
        raise NotImplementedError(f"Plugin {self.info.name} does not support video effects")

    def process_audio_effect(self, clip_id: str, effect_id: str,
                           parameters: Dict[str, Any]) -> bool:
        """处理音频效果"""
        raise NotImplementedError(f"Plugin {self.info.name} does not support audio effects")

    def process_transition(self, from_clip_id: str, to_clip_id: str,
                         transition_id: str, parameters: Dict[str, Any]) -> bool:
        """处理转场效果"""
        raise NotImplementedError(f"Plugin {self.info.name} does not support transitions")

    def process_color_grading(self, clip_id: str, grade_id: str,
                            parameters: Dict[str, Any]) -> bool:
        """处理调色"""
        raise NotImplementedError(f"Plugin {self.info.name} does not support color grading")

    # 导入导出接口

    def import_media(self, file_path: str, options: Dict[str, Any]) -> Optional[Any]:
        """导入媒体文件"""
        raise NotImplementedError(f"Plugin {self.info.name} does not support media import")

    def export_media(self, project: Any, output_path: str,
                    format_id: str, options: Dict[str, Any]) -> bool:
        """导出媒体文件"""
        raise NotImplementedError(f"Plugin {self.info.name} does not support media export")

    # AI功能接口

    def process_ai_enhancement(self, clip_id: str, enhancement_id: str,
                              parameters: Dict[str, Any]) -> bool:
        """处理AI增强"""
        raise NotImplementedError(f"Plugin {self.info.name} does not support AI enhancement")

    # 工具接口

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """获取菜单项"""
        return []

    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        """获取工具栏项"""
        return []

    def get_shortcuts(self) -> List[Dict[str, Any]]:
        """获取快捷键"""
        return []

    # 资源管理

    def get_resource_path(self, resource_name: str) -> str:
        """获取资源路径"""
        if self._context:
            return os.path.join(self._context.plugin_dir, self.info.id, resource_name)
        return resource_name

    def load_translation(self, language: str = "zh_CN") -> Dict[str, str]:
        """加载翻译文件"""
        try:
            translation_path = self.get_resource_path(f"translations/{language}.json")
            if os.path.exists(translation_path):
                import json
                with open(translation_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            if self._context:
                self._context.logger.warning(f"Failed to load translation: {e}")
        return {}


# 特化插件接口

class VideoEffectPlugin(PluginInterface):
    """视频效果插件基类"""

    def __init__(self):
        super().__init__()
        self._info.plugin_type = PluginType.VIDEO_EFFECT

    @abstractmethod
    def process_video_effect(self, clip_id: str, effect_id: str,
                           parameters: Dict[str, Any]) -> bool:
        """处理视频效果"""
        pass

    @abstractmethod
    def get_effects(self) -> List[Dict[str, Any]]:
        """获取效果列表"""
        pass


class AudioEffectPlugin(PluginInterface):
    """音频效果插件基类"""

    def __init__(self):
        super().__init__()
        self._info.plugin_type = PluginType.AUDIO_EFFECT

    @abstractmethod
    def process_audio_effect(self, clip_id: str, effect_id: str,
                           parameters: Dict[str, Any]) -> bool:
        """处理音频效果"""
        pass

    @abstractmethod
    def get_effects(self) -> List[Dict[str, Any]]:
        """获取效果列表"""
        pass


class TransitionPlugin(PluginInterface):
    """转场效果插件基类"""

    def __init__(self):
        super().__init__()
        self._info.plugin_type = PluginType.TRANSITION

    @abstractmethod
    def process_transition(self, from_clip_id: str, to_clip_id: str,
                         transition_id: str, parameters: Dict[str, Any]) -> bool:
        """处理转场效果"""
        pass

    @abstractmethod
    def get_effects(self) -> List[Dict[str, Any]]:
        """获取转场列表"""
        pass


class AIEnhancementPlugin(PluginInterface):
    """AI增强插件基类"""

    def __init__(self):
        super().__init__()
        self._info.plugin_type = PluginType.AI_ENHANCEMENT

    @abstractmethod
    def process_ai_enhancement(self, clip_id: str, enhancement_id: str,
                              parameters: Dict[str, Any]) -> bool:
        """处理AI增强"""
        pass

    @abstractmethod
    def get_enhancements(self) -> List[Dict[str, Any]]:
        """获取AI增强列表"""
        pass


class ExportPlugin(PluginInterface):
    """导出插件基类"""

    def __init__(self):
        super().__init__()
        self._info.plugin_type = PluginType.EXPORT_FORMAT

    @abstractmethod
    def export_media(self, project: Any, output_path: str,
                    format_id: str, options: Dict[str, Any]) -> bool:
        """导出媒体文件"""
        pass

    @abstractmethod
    def get_export_presets(self) -> List[Dict[str, Any]]:
        """获取导出预设"""
        pass


class ImportPlugin(PluginInterface):
    """导入插件基类"""

    def __init__(self):
        super().__init__()
        self._info.plugin_type = PluginType.IMPORT_FORMAT

    @abstractmethod
    def import_media(self, file_path: str, options: Dict[str, Any]) -> Optional[Any]:
        """导入媒体文件"""
        pass

    @abstractmethod
    def get_import_formats(self) -> List[str]:
        """获取支持的导入格式"""
        pass


class ThemePlugin(PluginInterface):
    """主题插件基类"""

    def __init__(self):
        super().__init__()
        self._info.plugin_type = PluginType.THEME

    @abstractmethod
    def get_theme_resources(self) -> Dict[str, str]:
        """获取主题资源"""
        pass

    @abstractmethod
    def apply_theme(self, target: Any) -> bool:
        """应用主题"""
        pass