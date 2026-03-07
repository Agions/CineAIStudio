#!/usr/bin/env python3
"""测试服务容器"""

import pytest

from app.core.service_container import ServiceContainer


class TestServiceContainer:
    """测试服务容器"""

    def test_init(self):
        """测试初始化"""
        container = ServiceContainer()
        
        assert isinstance(container._services, dict)
        assert isinstance(container._services_by_name, dict)

    def test_register_and_get(self):
        """测试注册和获取服务"""
        container = ServiceContainer()
        
        class TestService:
            pass
        
        service = TestService()
        container.register(TestService, service)
        
        result = container.get(TestService)
        assert result is service

    def test_register_by_name(self):
        """测试按名称注册"""
        container = ServiceContainer()
        
        service = object()
        container.register_by_name("my_service", service)
        
        result = container.get_by_name("my_service")
        assert result is service

    def test_get_not_exists(self):
        """测试获取不存在的服务"""
        container = ServiceContainer()
        
        class UnknownService:
            pass
        
        result = container.get(UnknownService)
        assert result is None

    def test_get_by_name_not_exists(self):
        """测试按名称获取不存在的服务"""
        container = ServiceContainer()
        
        result = container.get_by_name("unknown")
        assert result is None

    def test_has_service(self):
        """测试检查服务存在"""
        container = ServiceContainer()
        
        class MyService:
            pass
        
        container.register(MyService, MyService())
        
        assert container.has(MyService) is True
        assert container.has(object) is False

    def test_has_by_name(self):
        """测试按名称检查服务存在"""
        container = ServiceContainer()
        
        container.register_by_name("exists", object())
        
        assert container.has_by_name("exists") is True
        assert container.has_by_name("not_exists") is False

    def test_remove(self):
        """测试移除服务"""
        container = ServiceContainer()
        
        class RemovableService:
            pass
        
        container.register(RemovableService, RemovableService())
        assert container.has(RemovableService) is True
        
        container.remove(RemovableService)
        assert container.has(RemovableService) is False

    def test_remove_not_exists(self):
        """测试移除不存在的服务"""
        container = ServiceContainer()
        
        # 不应该抛出异常
        container.remove(object)

    def test_clear(self):
        """测试清空服务"""
        container = ServiceContainer()
        
        container.register_by_name("s1", object())
        container.register_by_name("s2", object())
        
        container.clear()
        
        assert container.has_by_name("s1") is False
        assert container.has_by_name("s2") is False
