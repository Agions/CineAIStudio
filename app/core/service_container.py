#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单服务容器 - 简化的依赖注入
"""

from typing import Dict, Type, Any, Optional


class ServiceContainer:
    """简化服务容器"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}

    def register(self, service_type: Type, instance: Any) -> None:
        """注册服务实例"""
        self._services[service_type] = instance

    def get(self, service_type: Type) -> Any:
        """获取服务实例"""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type} not registered")
        return self._services[service_type]

    def has(self, service_type: Type) -> bool:
        """检查服务是否存在"""
        return service_type in self._services

    def clear(self) -> None:
        """清除所有服务"""
        self._services.clear()