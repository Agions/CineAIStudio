#!/usr/bin/env python3
"""测试 AI 服务管理器"""

import pytest
from datetime import datetime
from dataclasses import asdict

from app.services.ai_service_manager import (
    ServiceStatus,
    ServiceHealth,
    AIServiceManager,
)


class TestServiceStatus:
    """测试服务状态枚举"""

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = [
            ServiceStatus.ACTIVE,
            ServiceStatus.INACTIVE,
            ServiceStatus.ERROR,
            ServiceStatus.MAINTENANCE,
        ]
        
        assert len(statuses) == 4
        assert ServiceStatus.ACTIVE.value == "active"


class TestServiceHealth:
    """测试服务健康状态"""

    def test_creation(self):
        """测试创建"""
        health = ServiceHealth(
            service_name="test_service",
            status=ServiceStatus.ACTIVE,
            last_check=1234567890.0,
            response_time=0.5,
        )
        
        assert health.service_name == "test_service"
        assert health.status == ServiceStatus.ACTIVE
        assert health.response_time == 0.5

    def test_with_error(self):
        """测试带错误信息"""
        health = ServiceHealth(
            service_name="test",
            status=ServiceStatus.ERROR,
            last_check=1234567890.0,
            error_message="Connection failed",
        )
        
        assert health.error_message == "Connection failed"


class TestAIServiceManager:
    """测试 AI 服务管理器"""

    def test_init(self):
        """测试初始化"""
        manager = AIServiceManager()
        
        assert manager._services == {}
        assert manager._service_health == {}

    def test_register_service(self):
        """测试注册服务"""
        manager = AIServiceManager()
        
        class TestService:
            pass
        
        service = TestService()
        manager.register_service("test", service)
        
        assert "test" in manager._services

    def test_get_service(self):
        """测试获取服务"""
        manager = AIServiceManager()
        
        class TestService:
            pass
        
        service = TestService()
        manager.register_service("test", service)
        
        result = manager.get_service("test")
        
        assert result is service

    def test_get_nonexistent_service(self):
        """测试获取不存在的服务"""
        manager = AIServiceManager()
        
        result = manager.get_service("nonexistent")
        
        assert result is None

    def test_get_all_services(self):
        """测试获取所有服务"""
        manager = AIServiceManager()
        
        class S1:
            pass
        class S2:
            pass
        
        manager.register_service("s1", S1())
        manager.register_service("s2", S2())
        
        services = manager.get_all_services()
        
        assert len(services) == 2
        assert "s1" in services
        assert "s2" in services

    def test_update_service_health(self):
        """测试更新服务健康状态"""
        manager = AIServiceManager()
        
        manager.update_service_health(
            "test_service",
            ServiceStatus.ACTIVE,
            0.5
        )
        
        health = manager.get_service_health("test_service")
        
        assert health is not None
        assert health.status == ServiceStatus.ACTIVE

    def test_get_usage_stats(self):
        """测试获取使用统计"""
        manager = AIServiceManager()
        
        stats = manager.get_usage_stats("test")
        
        assert "total_requests" in stats
        assert "failed_requests" in stats
