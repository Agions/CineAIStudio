#!/usr/bin/env python3
"""测试服务注册表"""

import pytest
from unittest.mock import Mock, MagicMock

from app.core.service_registry import (
    ServiceState,
    ServiceLifetime,
    ServiceDependency,
    ServiceDefinition,
    ServiceRegistry,
)


class TestServiceState:
    """测试服务状态枚举"""

    def test_all_states(self):
        """测试所有状态"""
        states = [
            ServiceState.UNREGISTERED,
            ServiceState.REGISTERED,
            ServiceState.INITIALIZING,
            ServiceState.READY,
            ServiceState.STARTING,
            ServiceState.RUNNING,
            ServiceState.STOPPING,
            ServiceState.STOPPED,
            ServiceState.ERROR,
        ]
        
        assert len(states) == 9
        assert ServiceState.READY.value == "ready"


class TestServiceLifetime:
    """测试服务生命周期枚举"""

    def test_lifetime_values(self):
        """测试生命周期值"""
        assert ServiceLifetime.SINGLETON.value == "singleton"
        assert ServiceLifetime.TRANSIENT.value == "transient"
        assert ServiceLifetime.SCOPED.value == "scoped"


class TestServiceDependency:
    """测试服务依赖"""

    def test_creation_required(self):
        """测试创建必需依赖"""
        dep = ServiceDependency("database")
        
        assert dep.service_name == "database"
        assert dep.required is True
        assert dep.lazy is False

    def test_creation_optional_lazy(self):
        """测试创建可选延迟依赖"""
        dep = ServiceDependency("cache", required=False, lazy=True)
        
        assert dep.required is False
        assert dep.lazy is True


class TestServiceDefinition:
    """测试服务定义"""

    def test_basic_creation(self):
        """测试基本创建"""
        def factory():
            return Mock()
        
        definition = ServiceDefinition(
            name="test_service",
            service_type=Mock,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON,
        )
        
        assert definition.name == "test_service"
        assert definition.service_type == Mock
        assert definition.factory is factory
        assert definition.lifetime == ServiceLifetime.SINGLETON

    def test_with_dependencies(self):
        """测试带依赖的服务定义"""
        deps = [
            ServiceDependency("db", required=True),
            ServiceDependency("cache", required=False),
        ]
        
        definition = ServiceDefinition(
            name="test",
            service_type=Mock,
            dependencies=deps,
        )
        
        assert len(definition.dependencies) == 2


class TestServiceRegistry:
    """测试服务注册表"""

    def test_init(self):
        """测试初始化"""
        registry = ServiceRegistry()
        
        assert isinstance(registry._services, dict)
        assert isinstance(registry._definitions, dict)

    def test_register_definition(self):
        """测试注册服务定义"""
        registry = ServiceRegistry()
        
        definition = ServiceDefinition(
            name="test_service",
            service_type=Mock,
        )
        
        registry.register(definition)
        
        assert "test_service" in registry._definitions

    def test_register_factory(self):
        """测试注册工厂函数"""
        registry = ServiceRegistry()
        
        def my_factory():
            return Mock()
        
        registry.register_factory("my_service", my_factory)
        
        assert "my_service" in registry._definitions

    def test_get_not_registered(self):
        """测试获取未注册服务"""
        registry = ServiceRegistry()
        
        result = registry.get("nonexistent")
        
        assert result is None

    def test_has_service(self):
        """测试检查服务存在"""
        registry = ServiceRegistry()
        
        definition = ServiceDefinition(name="exists", service_type=Mock)
        registry.register(definition)
        
        assert registry.has_service("exists") is True
        assert registry.has_service("not_exists") is False
