#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 插件管理器
提供完整的插件系统管理功能
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass

from .plugin_interface import (
    PluginInterface, PluginContext, PluginType, PluginStatus, PluginInfo
)
from .plugin_registry import PluginRegistry, PluginRegistryEntry
from .plugin_loader import PluginLoader
from ..core.logger import Logger
from ..core.event_bus import EventBus


@dataclass
class PluginManagerConfig:
    """插件管理器配置"""
    plugin_directories: List[str]
    auto_load: bool = True
    auto_scan: bool = True
    enable_crash_recovery: bool = True
    max_load_time: float = 30.0  # 最大加载时间（秒）
    allow_sandboxing: bool = False
    require_signature: bool = False
    update_check_interval: int = 86400  # 24小时


class PluginManager:
    """插件管理器"""

    def __init__(self, config: PluginManagerConfig, logger: Logger, event_bus: EventBus):
        self.config = config
        self.logger = logger
        self.event_bus = event_bus

        # 创建插件上下文
        self._context = None

        # 初始化组件
        self.registry = PluginRegistry()
        self.loader = PluginLoader(logger, event_bus)

        # 事件回调
        self._event_callbacks: Dict[str, List[Callable]] = {}

        # 统计信息
        self._stats = {
            "total_loaded": 0,
            "total_failed": 0,
            "load_time_total": 0.0,
            "last_scan_time": 0.0
        }

        # 确保插件目录存在
        for plugin_dir in config.plugin_directories:
            Path(plugin_dir).mkdir(parents=True, exist_ok=True)

        # 订阅事件
        self._subscribe_events()

        # 初始化时扫描插件
        if config.auto_scan:
            self.scan_plugins()

    def initialize(self, context: PluginContext) -> bool:
        """初始化插件管理器"""
        try:
            self._context = context

            # 扫描并注册插件
            self.scan_plugins()

            # 自动加载插件
            if self.config.auto_load:
                self.load_all_plugins()

            self.logger.info("Plugin manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize plugin manager: {e}")
            return False

    def shutdown(self) -> bool:
        """关闭插件管理器"""
        try:
            # 卸载所有插件
            self.unload_all_plugins()

            self.logger.info("Plugin manager shutdown successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to shutdown plugin manager: {e}")
            return False

    def scan_plugins(self) -> int:
        """扫描插件目录"""
        self.logger.info("Starting plugin scan...")
        start_time = time.time()

        try:
            # 扫描所有插件目录
            registered_count = self.loader.scan_and_register_plugins(
                self.config.plugin_directories
            )

            scan_time = time.time() - start_time
            self._stats["last_scan_time"] = scan_time

            self.logger.info(
                f"Plugin scan completed: {registered_count} plugins registered "
                f"in {scan_time:.2f}s"
            )

            # 发布扫描完成事件
            self.event_bus.publish("plugin.scan_completed", {
                "registered_count": registered_count,
                "scan_time": scan_time
            })

            return registered_count

        except Exception as e:
            self.logger.error(f"Plugin scan failed: {e}")
            return 0

    def load_plugin(self, plugin_id: str, config: Dict[str, Any] = None) -> bool:
        """加载插件"""
        if not self._context:
            self.logger.error("Plugin manager not initialized")
            return False

        start_time = time.time()
        plugin = self.loader.load_plugin(plugin_id, self._context, config)

        if plugin:
            load_time = time.time() - start_time
            self._stats["total_loaded"] += 1
            self._stats["load_time_total"] += load_time

            # 调用插件加载回调
            self._call_event_callbacks("plugin_loaded", plugin)

            self.logger.info(f"Plugin loaded: {plugin_id} ({load_time:.3f}s)")
            return True
        else:
            self._stats["total_failed"] += 1
            self.logger.error(f"Failed to load plugin: {plugin_id}")
            return False

    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        plugin = self.loader.get_loaded_plugin(plugin_id)
        if not plugin:
            self.logger.warning(f"Plugin not loaded: {plugin_id}")
            return True

        success = self.loader.unload_plugin(plugin_id)
        if success:
            # 调用插件卸载回调
            self._call_event_callbacks("plugin_unloaded", plugin)

            self.logger.info(f"Plugin unloaded: {plugin_id}")

        return success

    def reload_plugin(self, plugin_id: str, config: Dict[str, Any] = None) -> bool:
        """重新加载插件"""
        self.logger.info(f"Reloading plugin: {plugin_id}")

        # 先卸载
        if plugin_id in self.loader.get_loaded_plugins():
            self.unload_plugin(plugin_id)

        # 重新加载
        return self.load_plugin(plugin_id, config)

    def load_all_plugins(self) -> Dict[str, bool]:
        """加载所有插件"""
        if not self._context:
            self.logger.error("Plugin manager not initialized")
            return {}

        self.logger.info("Loading all plugins...")
        return self.loader.load_all_plugins(self._context)

    def unload_all_plugins(self) -> Dict[str, bool]:
        """卸载所有插件"""
        self.logger.info("Unloading all plugins...")
        return self.loader.unload_all_plugins()

    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """获取已加载的插件实例"""
        return self.loader.get_loaded_plugin(plugin_id)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """按类型获取已加载的插件"""
        plugins = []
        for plugin in self.loader.get_loaded_plugins().values():
            if plugin.info.plugin_type == plugin_type:
                plugins.append(plugin)
        return plugins

    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """获取所有已加载的插件"""
        return self.loader.get_loaded_plugins()

    def get_plugin_info(self, plugin_id: str) -> Optional[PluginRegistryEntry]:
        """获取插件注册信息"""
        return self.registry.get_plugin_info(plugin_id)

    def get_available_plugins(self) -> Dict[str, PluginRegistryEntry]:
        """获取所有可用插件（包括未加载的）"""
        return self.registry.get_all_plugins()

    def get_plugins_by_status(self, status: PluginStatus) -> List[PluginRegistryEntry]:
        """按状态获取插件"""
        return self.registry.get_plugins_by_status(status)

    def search_plugins(self, query: str, plugin_type: Optional[PluginType] = None) -> List[PluginRegistryEntry]:
        """搜索插件"""
        return self.registry.search_plugins(query, plugin_type)

    def install_plugin(self, plugin_file: str) -> Optional[str]:
        """安装插件（从文件）"""
        try:
            # TODO: 实现插件安装逻辑
            # 1. 验证插件文件
            # 2. 解压缩到插件目录
            # 3. 验证插件清单
            # 4. 注册到注册表
            pass

        except Exception as e:
            self.logger.error(f"Failed to install plugin: {e}")
            return None

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """卸载插件（从磁盘删除）"""
        try:
            # 先卸载插件
            if plugin_id in self.loader.get_loaded_plugins():
                self.unload_plugin(plugin_id)

            # 从注册表移除
            if not self.registry.unregister_plugin(plugin_id):
                return False

            # TODO: 删除插件文件
            pass

            self.logger.info(f"Plugin uninstalled: {plugin_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to uninstall plugin {plugin_id}: {e}")
            return False

    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        entry = self.registry.get_plugin_info(plugin_id)
        if not entry or entry.status != PluginStatus.DISABLED:
            return False

        # 重新启用并尝试加载
        self.registry.update_plugin_status(plugin_id, PluginStatus.LOADED)
        return self.load_plugin(plugin_id)

    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        # 先卸载
        if plugin_id in self.loader.get_loaded_plugins():
            self.unload_plugin(plugin_id)

        # 标记为禁用
        self.registry.update_plugin_status(plugin_id, PluginStatus.DISABLED)
        return True

    def update_plugin(self, plugin_id: str, update_file: str) -> bool:
        """更新插件"""
        try:
            # TODO: 实现插件更新逻辑
            pass

        except Exception as e:
            self.logger.error(f"Failed to update plugin {plugin_id}: {e}")
            return False

    def get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """获取插件配置"""
        plugin = self.loader.get_loaded_plugin(plugin_id)
        if plugin:
            return plugin.config
        return {}

    def set_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """设置插件配置"""
        plugin = self.loader.get_loaded_plugin(plugin_id)
        if plugin:
            try:
                plugin.on_config_changed(config)
                return True
            except Exception as e:
                self.logger.error(f"Failed to set plugin config for {plugin_id}: {e}")
        return False

    def get_plugin_dependencies(self, plugin_id: str) -> List[str]:
        """获取插件依赖"""
        entry = self.registry.get_plugin_info(plugin_id)
        return entry.info.dependencies if entry else []

    def get_plugin_dependents(self, plugin_id: str) -> List[str]:
        """获取依赖此插件的其他插件"""
        return list(self.registry.get_dependents(plugin_id))

    def validate_plugin(self, plugin_id: str) -> Tuple[bool, List[str]]:
        """验证插件"""
        errors = self.loader.get_plugin_errors(plugin_id)
        return len(errors) == 0, errors

    def get_plugin_statistics(self) -> Dict[str, Any]:
        """获取插件统计信息"""
        registry_stats = self.registry.get_statistics()
        loaded_plugins = self.loader.get_loaded_plugins()

        stats = {
            **registry_stats,
            **self._stats,
            "loaded_plugins": len(loaded_plugins),
            "average_load_time": (
                self._stats["load_time_total"] / max(self._stats["total_loaded"], 1)
            )
        }

        return stats

    def export_plugin_list(self, export_path: str) -> bool:
        """导出插件列表"""
        return self.registry.export_registry(export_path)

    def import_plugin_list(self, import_path: str) -> bool:
        """导入插件列表"""
        return self.registry.import_registry(import_path)

    # 事件管理

    def add_event_callback(self, event_name: str, callback: Callable) -> None:
        """添加事件回调"""
        if event_name not in self._event_callbacks:
            self._event_callbacks[event_name] = []
        self._event_callbacks[event_name].append(callback)

    def remove_event_callback(self, event_name: str, callback: Callable) -> None:
        """移除事件回调"""
        if event_name in self._event_callbacks:
            self._event_callbacks[event_name].remove(callback)

    def _call_event_callbacks(self, event_name: str, plugin: PluginInterface) -> None:
        """调用事件回调"""
        if event_name in self._event_callbacks:
            for callback in self._event_callbacks[event_name]:
                try:
                    callback(plugin)
                except Exception as e:
                    self.logger.error(f"Event callback error: {e}")

    def _subscribe_events(self) -> None:
        """订阅事件总线事件"""
        self.event_bus.subscribe("project.opened", self._on_project_opened)
        self.event_bus.subscribe("project.saved", self._on_project_saved)
        self.event_bus.subscribe("project.closed", self._on_project_closed)

    def _on_project_opened(self, data: Dict[str, Any]) -> None:
        """项目打开事件处理"""
        for plugin in self.loader.get_loaded_plugins().values():
            try:
                plugin.on_project_opened(data.get("project"))
            except Exception as e:
                self.logger.error(f"Plugin project opened callback error: {e}")

    def _on_project_saved(self, data: Dict[str, Any]) -> None:
        """项目保存事件处理"""
        for plugin in self.loader.get_loaded_plugins().values():
            try:
                plugin.on_project_saved(data.get("project"))
            except Exception as e:
                self.logger.error(f"Plugin project saved callback error: {e}")

    def _on_project_closed(self, data: Dict[str, Any]) -> None:
        """项目关闭事件处理"""
        for plugin in self.loader.get_loaded_plugins().values():
            try:
                plugin.on_project_closed(data.get("project"))
            except Exception as e:
                self.logger.error(f"Plugin project closed callback error: {e}")


# 全局插件管理器
_plugin_manager = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器"""
    global _plugin_manager
    if _plugin_manager is None:
        raise RuntimeError("Plugin manager not initialized")
    return _plugin_manager


def set_plugin_manager(manager: PluginManager) -> None:
    """设置全局插件管理器"""
    global _plugin_manager
    _plugin_manager = manager


# 便捷函数
def load_plugin(plugin_id: str, config: Dict[str, Any] = None) -> bool:
    """加载插件"""
    return get_plugin_manager().load_plugin(plugin_id, config)


def unload_plugin(plugin_id: str) -> bool:
    """卸载插件"""
    return get_plugin_manager().unload_plugin(plugin_id)


def get_plugin(plugin_id: str) -> Optional[PluginInterface]:
    """获取插件实例"""
    return get_plugin_manager().get_plugin(plugin_id)