#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用核心测试
测试 Application 类的核心功能
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from app.core.application import Application, ApplicationState, ErrorInfo, ErrorType, ErrorSeverity


class TestApplication:
    """应用核心功能测试"""

    @pytest.mark.unit
    def test_application_initialization(self, mock_config):
        """测试应用初始化"""
        with patch('app.core.config_manager.ConfigManager') as mock_config_manager:
            mock_config_manager.return_value.get_config.return_value = mock_config

            app = Application()
            app.initialize()

            assert app.get_state() == ApplicationState.READY
            assert app.get_config() == mock_config
            mock_config_manager.return_value.get_config.assert_called_once()

    @pytest.mark.unit
    def test_service_registration(self, test_application):
        """测试服务注册"""
        test_service = Mock()

        test_application.register_service("test_service", test_service)

        assert test_application.get_service_by_name("test_service") == test_service

    @pytest.mark.unit
    def test_error_handling(self, test_application, mock_logger):
        """测试错误处理"""
        error_info = ErrorInfo(
            error_type=ErrorType.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            message="测试错误",
            exception=Exception("测试异常")
        )

        test_application.handle_error(error_info)

        mock_logger.error.assert_called()

    @pytest.mark.unit
    def test_application_lifecycle(self, test_application):
        """测试应用生命周期"""
        # 测试启动
        test_application.start()
        assert test_application.get_state() == ApplicationState.RUNNING

        # 测试暂停
        test_application.pause()
        assert test_application.get_state() == ApplicationState.PAUSED

        # 测试恢复
        test_application.resume()
        assert test_application.get_state() == ApplicationState.RUNNING

        # 测试关闭
        test_application.shutdown()
        assert test_application.get_state() == ApplicationState.SHUTTING_DOWN

    @pytest.mark.unit
    def test_configuration_management(self, test_application):
        """测试配置管理"""
        test_config = {"test_key": "test_value"}

        test_application.set_config(test_config)
        retrieved_config = test_application.get_config()

        assert retrieved_config["test_key"] == "test_value"

    @pytest.mark.unit
    def test_service_dependency_injection(self, test_application):
        """测试服务依赖注入"""
        # 注册依赖服务
        dependency_service = Mock()
        test_application.register_service("dependency", dependency_service)

        # 注册主服务
        main_service = Mock()
        test_application.register_service("main", main_service)

        # 验证依赖注入
        assert test_application.get_service_by_name("dependency") == dependency_service
        assert test_application.get_service_by_name("main") == main_service

    @pytest.mark.unit
    def test_error_severity_levels(self, test_application):
        """测试不同错误严重级别的处理"""
        errors = [
            ErrorInfo(ErrorType.UI, ErrorSeverity.LOW, "低级错误"),
            ErrorInfo(ErrorType.SERVICE, ErrorSeverity.MEDIUM, "中级错误"),
            ErrorInfo(ErrorType.SYSTEM, ErrorSeverity.HIGH, "高级错误"),
            ErrorInfo(ErrorType.CRITICAL, ErrorSeverity.CRITICAL, "关键错误"),
        ]

        for error in errors:
            test_application.handle_error(error)
            # 验证每种错误都被正确处理
            assert test_application.get_state() != ApplicationState.ERROR

    @pytest.mark.integration
    def test_multiple_services_interaction(self, test_application):
        """测试多服务交互"""
        # 创建多个模拟服务
        logger_service = Mock()
        config_service = Mock()
        event_service = Mock()

        # 注册服务
        test_application.register_service("logger", logger_service)
        test_application.register_service("config", config_service)
        test_application.register_service("event", event_service)

        # 验证服务可用性
        assert test_application.get_service_by_name("logger") is logger_service
        assert test_application.get_service_by_name("config") is config_service
        assert test_application.get_service_by_name("event") is event_service

    @pytest.mark.unit
    def test_invalid_service_access(self, test_application):
        """测试无效服务访问"""
        with pytest.raises(KeyError):
            test_application.get_service_by_name("non_existent_service")

    @pytest.mark.unit
    def test_duplicate_service_registration(self, test_application):
        """测试重复服务注册"""
        service1 = Mock()
        service2 = Mock()

        test_application.register_service("test", service1)

        # 应该允许覆盖注册
        test_application.register_service("test", service2)
        assert test_application.get_service_by_name("test") == service2