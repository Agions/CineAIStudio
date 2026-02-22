#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 服务容器 - 简单依赖注入容器

⚠️ 已弃用：推荐使用 service_registry.ServiceRegistry 替代。
此容器仅为向后兼容保留，新代码请使用 ServiceRegistry。
ServiceRegistry 支持：生命周期管理、依赖解析、健康检查、配置驱动等高级功能。
"""

import warnings

from typing import Dict, Type, Any, Optional


class ServiceContainer:
    """服务容器

    ⚠️ 已弃用，请使用 ServiceRegistry。
    """

    def __init__(self):
        warnings.warn(
            "ServiceContainer 已弃用，请迁移到 ServiceRegistry",
            DeprecationWarning,
            stacklevel=2,
        )
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