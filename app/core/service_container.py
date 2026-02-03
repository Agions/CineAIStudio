#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 服务容器 - 依赖注入容器
支持按类型和名称注册获取服务
"""

from typing import Dict, Type, Any, Optional


class ServiceContainer:
    """服务容器"""

    def __init__(self):
        self._services_by_type: Dict[Type, Any] = {}
        self._services_by_name: Dict[str, Any] = {}

    def register(self, service_type: Type, instance: Any) -> None:
        """按类型注册服务实例"""
        self._services_by_type[service_type] = instance

    def register_by_name(self, name: str, instance: Any) -> None:
        """按名称注册服务实例"""
        self._services_by_name[name] = instance

    def get(self, service_type: Type) -> Any:
        """按类型获取服务实例"""
        if service_type not in self._services_by_type:
            raise ValueError(f"Service {service_type} not registered")
        return self._services_by_type[service_type]

    def get_by_name(self, name: str) -> Any:
        """按名称获取服务实例"""
        if name not in self._services_by_name:
            raise ValueError(f"Service '{name}' not registered")
        return self._services_by_name[name]

    def has(self, service_type: Type) -> bool:
        """检查服务类型是否存在"""
        return service_type in self._services_by_type

    def has_by_name(self, name: str) -> bool:
        """检查服务名称是否存在"""
        return name in self._services_by_name

    def remove(self, service_type: Type) -> None:
        """按类型移除服务实例"""
        if service_type in self._services_by_type:
            del self._services_by_type[service_type]

    def remove_by_name(self, name: str) -> None:
        """按名称移除服务实例"""
        if name in self._services_by_name:
            del self._services_by_name[name]

    def clear(self) -> None:
        """清除所有服务"""
        self._services_by_type.clear()
        self._services_by_name.clear()