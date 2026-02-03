#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 插件加载器
负责插件的动态加载、实例化和生命周期管理
"""

import os
import sys
import importlib
import importlib.util
import time
import traceback
from typing import Dict, List, Any, Optional, Type
from pathlib import Path

from .plugin_interface import PluginInterface, PluginContext, PluginStatus
from .plugin_registry import PluginRegistry, PluginRegistryEntry
from ..core.logger import Logger
from ..core.event_bus import EventBus


class PluginLoader:
    """插件加载器"""

    def __init__(self, logger: Logger, event_bus: EventBus):
        self.logger = logger
        self.event_bus = event_bus
        self.registry = PluginRegistry()
        self._loaded_plugins: Dict[str, PluginInterface] = {}
        self._plugin_modules: Dict[str, Any] = {}

    def load_plugin(self, plugin_id: str, context: PluginContext,
                   config: Dict[str, Any] = None) -> Optional[PluginInterface]:
        """加载插件"""
        try:
            # 获取插件注册信息
            entry = self.registry.get_plugin_info(plugin_id)
            if not entry:
                self.logger.error(f"Plugin not found in registry: {plugin_id}")
                return None

            # 检查插件状态
            if entry.status == PluginStatus.ACTIVE:
                self.logger.warning(f"Plugin already loaded: {plugin_id}")
                return self._loaded_plugins.get(plugin_id)

            # 更新状态
            self.registry.update_plugin_status(plugin_id, PluginStatus.LOADING)

            # 验证依赖
            if not self._verify_dependencies(entry.info.dependencies):
                self.registry.update_plugin_status(
                    plugin_id, PluginStatus.ERROR,
                    "Missing dependencies"
                )
                return None

            # 加载插件模块
            plugin_instance = self._load_plugin_module(entry, context)
            if plugin_instance is None:
                self.registry.update_plugin_status(
                    plugin_id, PluginStatus.ERROR,
                    "Failed to load plugin module"
                )
                return None

            # 初始化插件
            start_time = time.time()
            if plugin_instance.initialize(context, config):
                load_time = time.time() - start_time
                entry.load_time = load_time

                # 保存加载的插件
                self._loaded_plugins[plugin_id] = plugin_instance

                # 发布插件加载事件
                self.event_bus.publish("plugin.loaded", {
                    "plugin_id": plugin_id,
                    "plugin_name": entry.info.name,
                    "load_time": load_time
                })

                self.logger.info(f"Plugin loaded successfully: {plugin_id} ({load_time:.3f}s)")
                return plugin_instance
            else:
                self.registry.update_plugin_status(
                    plugin_id, PluginStatus.ERROR,
                    "Plugin initialization failed"
                )
                return None

        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_id}: {e}")
            self.logger.debug(f"Plugin load error details:\n{traceback.format_exc()}")
            self.registry.update_plugin_status(
                plugin_id, PluginStatus.ERROR,
                str(e)
            )
            return None

    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        try:
            # 检查依赖
            dependents = self.registry.get_dependents(plugin_id)
            if dependents:
                active_dependents = [
                    dep for dep in dependents
                    if self.registry.get_plugin_info(dep).status == PluginStatus.ACTIVE
                ]
                if active_dependents:
                    self.logger.error(
                        f"Cannot unload plugin {plugin_id}: required by {active_dependents}"
                    )
                    return False

            # 获取插件实例
            plugin_instance = self._loaded_plugins.get(plugin_id)
            if not plugin_instance:
                self.logger.warning(f"Plugin not loaded: {plugin_id}")
                return True

            # 调用插件关闭方法
            if plugin_instance.shutdown():
                # 从加载列表中移除
                del self._loaded_plugins[plugin_id]

                # 清理模块
                if plugin_id in self._plugin_modules:
                    del self._plugin_modules[plugin_id]

                # 更新状态
                self.registry.update_plugin_status(plugin_id, PluginStatus.LOADED)

                # 发布插件卸载事件
                self.event_bus.publish("plugin.unloaded", {
                    "plugin_id": plugin_id,
                    "plugin_name": plugin_instance.info.name
                })

                self.logger.info(f"Plugin unloaded successfully: {plugin_id}")
                return True
            else:
                self.registry.update_plugin_status(
                    plugin_id, PluginStatus.ERROR,
                    "Plugin shutdown failed"
                )
                return False

        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False

    def reload_plugin(self, plugin_id: str, context: PluginContext,
                     config: Dict[str, Any] = None) -> Optional[PluginInterface]:
        """重新加载插件"""
        if plugin_id in self._loaded_plugins:
            self.unload_plugin(plugin_id)
        return self.load_plugin(plugin_id, context, config)

    def get_loaded_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """获取已加载的插件实例"""
        return self._loaded_plugins.get(plugin_id)

    def get_loaded_plugins(self) -> Dict[str, PluginInterface]:
        """获取所有已加载的插件"""
        return self._loaded_plugins.copy()

    def load_all_plugins(self, context: PluginContext,
                        config: Dict[str, Any] = None) -> Dict[str, bool]:
        """加载所有插件"""
        results = {}
        all_plugins = self.registry.get_all_plugins()

        # 按依赖顺序排序
        sorted_plugins = self._sort_plugins_by_dependencies(list(all_plugins.keys()))

        for plugin_id in sorted_plugins:
            entry = all_plugins[plugin_id]
            # 只加载未禁用的插件
            if entry.status != PluginStatus.DISABLED:
                results[plugin_id] = self.load_plugin(plugin_id, context, config) is not None

        return results

    def unload_all_plugins(self) -> Dict[str, bool]:
        """卸载所有插件"""
        results = {}
        # 按依赖逆序卸载
        sorted_plugins = list(self._loaded_plugins.keys())
        sorted_plugins.reverse()

        for plugin_id in sorted_plugins:
            results[plugin_id] = self.unload_plugin(plugin_id)

        return results

    def scan_and_register_plugins(self, plugin_directories: List[str]) -> int:
        """扫描并注册插件"""
        registered_count = 0

        for plugin_dir in plugin_directories:
            self.logger.info(f"Scanning plugin directory: {plugin_dir}")
            discovered_plugins = self.registry.scan_plugin_directory(plugin_dir)

            for plugin_entry in discovered_plugins:
                if self.registry.register_plugin(plugin_entry):
                    self.logger.info(f"Registered plugin: {plugin_entry.info.id}")
                    registered_count += 1
                else:
                    self.logger.warning(f"Failed to register plugin: {plugin_entry.info.id}")

        return registered_count

    def validate_plugin(self, plugin_id: str) -> bool:
        """验证插件"""
        try:
            entry = self.registry.get_plugin_info(plugin_id)
            if not entry:
                return False

            # 验证文件完整性
            if not self.registry.validate_plugin_integrity(plugin_id):
                return False

            # 验证入口点
            if not os.path.exists(os.path.join(entry.plugin_path, entry.entry_point)):
                return False

            # 尝试加载模块（不初始化）
            if not self._test_plugin_module(entry):
                return False

            return True

        except Exception:
            return False

    def get_plugin_errors(self, plugin_id: str) -> List[str]:
        """获取插件错误信息"""
        errors = []

        entry = self.registry.get_plugin_info(plugin_id)
        if not entry:
            errors.append("Plugin not found in registry")
            return errors

        if entry.status == PluginStatus.ERROR and entry.error_message:
            errors.append(entry.error_message)

        # 验证插件
        if not self.registry.validate_plugin_integrity(plugin_id):
            errors.append("Plugin file integrity check failed")

        # 检查依赖
        for dep in entry.info.dependencies:
            dep_entry = self.registry.get_plugin_info(dep)
            if not dep_entry or dep_entry.status != PluginStatus.ACTIVE:
                errors.append(f"Missing or inactive dependency: {dep}")

        # 检查版本兼容性
        # TODO: 实现版本检查逻辑

        return errors

    # 私有方法

    def _load_plugin_module(self, entry: PluginRegistryEntry,
                          context: PluginContext) -> Optional[PluginInterface]:
        """加载插件模块"""
        try:
            # 构建模块路径
            plugin_path = entry.plugin_path
            entry_point = entry.entry_point

            if not os.path.isabs(entry_point):
                entry_point = os.path.join(plugin_path, entry_point)

            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                f"plugin_{entry.info.id}",
                entry_point
            )

            if spec is None or spec.loader is None:
                self.logger.error(f"Failed to create module spec for {entry.info.id}")
                return None

            module = importlib.util.module_from_spec(spec)

            # 添加插件路径到sys.path（临时）
            original_path = sys.path[:]
            sys.path.insert(0, plugin_path)

            try:
                spec.loader.exec_module(module)
            finally:
                # 恢复sys.path
                sys.path[:] = original_path

            # 保存模块引用
            self._plugin_modules[entry.info.id] = module

            # 查找插件类
            plugin_class = self._find_plugin_class(module, entry.info.id)
            if plugin_class is None:
                self.logger.error(f"Plugin class not found in {entry.info.id}")
                return None

            # 创建插件实例
            plugin_instance = plugin_class()
            if not isinstance(plugin_instance, PluginInterface):
                self.logger.error(f"Plugin class does not implement PluginInterface")
                return None

            return plugin_instance

        except Exception as e:
            self.logger.error(f"Failed to load plugin module {entry.info.id}: {e}")
            self.logger.debug(f"Module load error details:\n{traceback.format_exc()}")
            return None

    def _find_plugin_class(self, module: Any, plugin_id: str) -> Optional[Type[PluginInterface]]:
        """查找插件类"""
        # 首先查找与插件ID同名的类
        class_name = plugin_id.replace('-', '_').replace('.', '_')
        class_name = ''.join(word.capitalize() for word in class_name.split('_'))
        class_name = class_name + 'Plugin'

        if hasattr(module, class_name):
            plugin_class = getattr(module, class_name)
            if issubclass(plugin_class, PluginInterface):
                return plugin_class

        # 查找所有PluginInterface的子类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, PluginInterface) and
                attr != PluginInterface):
                return attr

        return None

    def _verify_dependencies(self, dependencies: List[str]) -> bool:
        """验证依赖是否满足"""
        for dep_id in dependencies:
            dep_entry = self.registry.get_plugin_info(dep_id)
            if not dep_entry or dep_entry.status != PluginStatus.ACTIVE:
                return False
        return True

    def _sort_plugins_by_dependencies(self, plugin_ids: List[str]) -> List[str]:
        """按依赖关系排序插件（拓扑排序）"""
        # 简单的拓扑排序实现
        sorted_plugins = []
        visited = set()
        visiting = set()

        def visit(plugin_id: str):
            if plugin_id in visiting:
                # 检测到循环依赖
                self.logger.warning(f"Circular dependency detected: {plugin_id}")
                return
            if plugin_id in visited:
                return

            visiting.add(plugin_id)

            entry = self.registry.get_plugin_info(plugin_id)
            if entry:
                for dep_id in entry.info.dependencies:
                    if dep_id in plugin_ids:
                        visit(dep_id)

            visiting.remove(plugin_id)
            visited.add(plugin_id)
            sorted_plugins.append(plugin_id)

        for plugin_id in plugin_ids:
            if plugin_id not in visited:
                visit(plugin_id)

        return sorted_plugins

    def _test_plugin_module(self, entry: PluginRegistryEntry) -> bool:
        """测试插件模块是否可以加载"""
        try:
            # 尝试加载模块（不执行）
            entry_point = entry.entry_point
            if not os.path.isabs(entry_point):
                entry_point = os.path.join(entry.plugin_path, entry_point)

            spec = importlib.util.spec_from_file_location(
                f"test_plugin_{entry.info.id}",
                entry_point
            )

            return spec is not None and spec.loader is not None

        except Exception:
            return False