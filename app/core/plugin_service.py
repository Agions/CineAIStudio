#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 插件服务
将插件系统集成到核心服务中
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .logger import Logger
from .event_bus import EventBus
from ..plugins.plugin_manager import PluginManager, PluginManagerConfig
from ..plugins.plugin_interface import PluginContext, PluginInterface, PluginType


@dataclass
class PluginServiceConfig:
    """插件服务配置"""
    plugin_directories: List[str]
    auto_load: bool = True
    auto_scan: bool = True
    enable_sandboxing: bool = False
    require_signature: bool = False
    max_plugin_memory: int = 512 * 1024 * 1024  # 512MB


class PluginService:
    """插件服务"""

    def __init__(self, config: PluginServiceConfig, logger: Logger, event_bus: EventBus):
        self.config = config
        self.logger = logger
        self.event_bus = event_bus
        self._plugin_manager: Optional[PluginManager] = None
        self._context: Optional[PluginContext] = None

        # 初始化插件管理器
        self._init_plugin_manager()

    def _init_plugin_manager(self) -> None:
        """初始化插件管理器"""
        manager_config = PluginManagerConfig(
            plugin_directories=self.config.plugin_directories,
            auto_load=self.config.auto_load,
            auto_scan=self.config.auto_scan,
            enable_crash_recovery=True,
            max_load_time=30.0,
            allow_sandboxing=self.config.enable_sandboxing,
            require_signature=self.config.require_signature
        )

        self._plugin_manager = PluginManager(manager_config, self.logger, self.event_bus)

        # 设置全局插件管理器
        from ..plugins.plugin_manager import set_plugin_manager
        set_plugin_manager(self._plugin_manager)

    def initialize(self, main_window, ui_components, video_service,
                  ai_service, export_service, temp_dir: str) -> bool:
        """初始化插件服务"""
        try:
            # 创建插件上下文
            from ..core.config_manager import get_config_manager
            from ..core.project_manager import get_project_manager

            self._context = PluginContext(
                logger=self.logger,
                event_bus=self.event_bus,
                config_manager=get_config_manager(),
                project_manager=get_project_manager(),
                main_window=main_window,
                ui_components=ui_components,
                video_service=video_service,
                ai_service=ai_service,
                export_service=export_service,
                plugin_manager=self._plugin_manager,
                temp_dir=temp_dir,
                plugin_dir=self.config.plugin_directories[0] if self.config.plugin_directories else ""
            )

            # 初始化插件管理器
            success = self._plugin_manager.initialize(self._context)

            if success:
                self.logger.info("Plugin service initialized successfully")
                # 发布插件系统就绪事件
                self.event_bus.publish("plugin_system.ready", {})
            else:
                self.logger.error("Failed to initialize plugin service")

            return success

        except Exception as e:
            self.logger.error(f"Plugin service initialization failed: {e}")
            return False

    def shutdown(self) -> bool:
        """关闭插件服务"""
        try:
            if self._plugin_manager:
                self._plugin_manager.shutdown()
                self.logger.info("Plugin service shutdown successfully")
            return True

        except Exception as e:
            self.logger.error(f"Plugin service shutdown failed: {e}")
            return False

    # 插件管理接口

    def scan_plugins(self) -> int:
        """扫描插件"""
        if not self._plugin_manager:
            return 0
        return self._plugin_manager.scan_plugins()

    def load_plugin(self, plugin_id: str, config: Dict[str, Any] = None) -> bool:
        """加载插件"""
        if not self._plugin_manager:
            return False
        return self._plugin_manager.load_plugin(plugin_id, config)

    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if not self._plugin_manager:
            return False
        return self._plugin_manager.unload_plugin(plugin_id)

    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """获取插件实例"""
        if not self._plugin_manager:
            return None
        return self._plugin_manager.get_plugin(plugin_id)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """按类型获取插件"""
        if not self._plugin_manager:
            return []
        return self._plugin_manager.get_plugins_by_type(plugin_type)

    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """获取所有已加载的插件"""
        if not self._plugin_manager:
            return {}
        return self._plugin_manager.get_all_plugins()

    def get_available_plugins(self) -> Dict[str, Any]:
        """获取所有可用插件"""
        if not self._plugin_manager:
            return {}
        return self._plugin_manager.get_available_plugins()

    def search_plugins(self, query: str, plugin_type: Optional[PluginType] = None) -> List[Dict[str, Any]]:
        """搜索插件"""
        if not self._plugin_manager:
            return []
        return self._plugin_manager.search_plugins(query, plugin_type)

    # 特定类型插件访问

    def get_video_effects(self) -> List[Dict[str, Any]]:
        """获取所有视频效果"""
        effects = []
        video_effect_plugins = self.get_plugins_by_type(PluginType.VIDEO_EFFECT)

        for plugin in video_effect_plugins:
            try:
                plugin_effects = plugin.get_effects()
                for effect in plugin_effects:
                    effect["plugin_id"] = plugin.info.id
                    effect["plugin_name"] = plugin.info.name
                effects.extend(plugin_effects)
            except Exception as e:
                self.logger.error(f"Failed to get effects from plugin {plugin.info.id}: {e}")

        return effects

    def get_audio_effects(self) -> List[Dict[str, Any]]:
        """获取所有音频效果"""
        effects = []
        audio_effect_plugins = self.get_plugins_by_type(PluginType.AUDIO_EFFECT)

        for plugin in audio_effect_plugins:
            try:
                plugin_effects = plugin.get_effects()
                for effect in plugin_effects:
                    effect["plugin_id"] = plugin.info.id
                    effect["plugin_name"] = plugin.info.name
                effects.extend(plugin_effects)
            except Exception as e:
                self.logger.error(f"Failed to get effects from plugin {plugin.info.id}: {e}")

        return effects

    def get_transitions(self) -> List[Dict[str, Any]]:
        """获取所有转场效果"""
        transitions = []
        transition_plugins = self.get_plugins_by_type(PluginType.TRANSITION)

        for plugin in transition_plugins:
            try:
                plugin_transitions = plugin.get_effects()
                for transition in plugin_transitions:
                    transition["plugin_id"] = plugin.info.id
                    transition["plugin_name"] = plugin.info.name
                transitions.extend(plugin_transitions)
            except Exception as e:
                self.logger.error(f"Failed to get transitions from plugin {plugin.info.id}: {e}")

        return transitions

    def get_ai_enhancements(self) -> List[Dict[str, Any]]:
        """获取所有AI增强功能"""
        enhancements = []
        ai_plugins = self.get_plugins_by_type(PluginType.AI_ENHANCEMENT)

        for plugin in ai_plugins:
            try:
                if hasattr(plugin, 'get_enhancements'):
                    plugin_enhancements = plugin.get_enhancements()
                    for enhancement in plugin_enhancements:
                        enhancement["plugin_id"] = plugin.info.id
                        enhancement["plugin_name"] = plugin.info.name
                    enhancements.extend(plugin_enhancements)
            except Exception as e:
                self.logger.error(f"Failed to get enhancements from plugin {plugin.info.id}: {e}")

        return enhancements

    def get_export_presets(self) -> List[Dict[str, Any]]:
        """获取所有导出预设"""
        presets = []
        export_plugins = self.get_plugins_by_type(PluginType.EXPORT_FORMAT)

        for plugin in export_plugins:
            try:
                plugin_presets = plugin.get_export_presets()
                for preset in plugin_presets:
                    preset["plugin_id"] = plugin.info.id
                    preset["plugin_name"] = plugin.info.name
                presets.extend(plugin_presets)
            except Exception as e:
                self.logger.error(f"Failed to get export presets from plugin {plugin.info.id}: {e}")

        return presets

    # 效果处理接口

    def apply_video_effect(self, clip_id: str, effect_id: str,
                          plugin_id: str, parameters: Dict[str, Any]) -> bool:
        """应用视频效果"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            self.logger.error(f"Plugin not found: {plugin_id}")
            return False

        try:
            return plugin.process_video_effect(clip_id, effect_id, parameters)
        except Exception as e:
            self.logger.error(f"Failed to apply video effect: {e}")
            return False

    def apply_audio_effect(self, clip_id: str, effect_id: str,
                          plugin_id: str, parameters: Dict[str, Any]) -> bool:
        """应用音频效果"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            self.logger.error(f"Plugin not found: {plugin_id}")
            return False

        try:
            return plugin.process_audio_effect(clip_id, effect_id, parameters)
        except Exception as e:
            self.logger.error(f"Failed to apply audio effect: {e}")
            return False

    def apply_transition(self, from_clip_id: str, to_clip_id: str,
                        transition_id: str, plugin_id: str,
                        parameters: Dict[str, Any]) -> bool:
        """应用转场效果"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            self.logger.error(f"Plugin not found: {plugin_id}")
            return False

        try:
            return plugin.process_transition(from_clip_id, to_clip_id,
                                           transition_id, parameters)
        except Exception as e:
            self.logger.error(f"Failed to apply transition: {e}")
            return False

    def apply_ai_enhancement(self, clip_id: str, enhancement_id: str,
                           plugin_id: str, parameters: Dict[str, Any]) -> bool:
        """应用AI增强"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            self.logger.error(f"Plugin not found: {plugin_id}")
            return False

        try:
            return plugin.process_ai_enhancement(clip_id, enhancement_id, parameters)
        except Exception as e:
            self.logger.error(f"Failed to apply AI enhancement: {e}")
            return False

    # 配置管理

    def get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """获取插件配置"""
        if not self._plugin_manager:
            return {}
        return self._plugin_manager.get_plugin_config(plugin_id)

    def set_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """设置插件配置"""
        if not self._plugin_manager:
            return False
        return self._plugin_manager.set_plugin_config(plugin_id, config)

    # 统计信息

    def get_statistics(self) -> Dict[str, Any]:
        """获取插件系统统计信息"""
        if not self._plugin_manager:
            return {}

        stats = self._plugin_manager.get_plugin_statistics()

        # 添加插件服务特定的统计信息
        stats.update({
            "video_effects_count": len(self.get_video_effects()),
            "audio_effects_count": len(self.get_audio_effects()),
            "transitions_count": len(self.get_transitions()),
            "ai_enhancements_count": len(self.get_ai_enhancements()),
            "export_presets_count": len(self.get_export_presets())
        })

        return stats


# 全局插件服务
_plugin_service = None


def get_plugin_service() -> PluginService:
    """获取全局插件服务"""
    global _plugin_service
    if _plugin_service is None:
        raise RuntimeError("Plugin service not initialized")
    return _plugin_service


def set_plugin_service(service: PluginService) -> None:
    """设置全局插件服务"""
    global _plugin_service
    _plugin_service = service