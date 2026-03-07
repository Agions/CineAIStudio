#!/usr/bin/env python3
"""测试应用程序核心类"""

import pytest
from enum import Enum

from app.core.application import (
    ApplicationState,
    ErrorType,
    ErrorSeverity,
    ErrorInfo,
    Application,
)


class TestApplicationState:
    """测试应用程序状态枚举"""

    def test_all_states(self):
        """测试所有状态"""
        states = [
            ApplicationState.INITIALIZING,
            ApplicationState.STARTING,
            ApplicationState.READY,
            ApplicationState.RUNNING,
            ApplicationState.PAUSED,
            ApplicationState.SHUTTING_DOWN,
            ApplicationState.ERROR,
        ]
        
        assert len(states) == 7
        assert ApplicationState.READY.value == "ready"


class TestErrorType:
    """测试错误类型枚举"""

    def test_all_types(self):
        """测试所有错误类型"""
        types = [
            ErrorType.SYSTEM,
            ErrorType.UI,
            ErrorType.FILE,
            ErrorType.NETWORK,
            ErrorType.AI,
            ErrorType.UNKNOWN,
        ]
        
        assert len(types) == 6
        assert ErrorType.UI.value == "ui"


class TestErrorSeverity:
    """测试错误严重程度枚举"""

    def test_all_severities(self):
        """测试所有严重程度"""
        severities = [
            ErrorSeverity.LOW,
            ErrorSeverity.MEDIUM,
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL,
        ]
        
        assert len(severities) == 4
        assert ErrorSeverity.HIGH.value == "high"


class TestErrorInfo:
    """测试错误信息数据类"""

    def test_creation(self):
        """测试创建"""
        info = ErrorInfo(
            error_type=ErrorType.UI,
            severity=ErrorSeverity.HIGH,
            message="测试错误",
        )
        
        assert info.error_type == ErrorType.UI
        assert info.severity == ErrorSeverity.HIGH
        assert info.message == "测试错误"

    def test_with_details(self):
        """测试带详情的错误"""
        info = ErrorInfo(
            error_type=ErrorType.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            message="严重错误",
            details="系统崩溃",
        )
        
        assert info.details == "系统崩溃"

    def test_with_exception(self):
        """测试带异常的错误"""
        exc = ValueError("测试异常")
        info = ErrorInfo(
            error_type=ErrorType.SYSTEM,
            severity=ErrorSeverity.HIGH,
            message="错误",
            exception=exc,
        )
        
        assert info.exception is exc


class TestApplicationClass:
    """测试 Application 类（如果可以实例化）"""

    def test_state_enum_access(self):
        """测试状态枚举访问"""
        assert ApplicationState.READY.value == "ready"
        assert ApplicationState.RUNNING.value == "running"

    def test_error_type_enum_access(self):
        """测试错误类型枚举访问"""
        assert ErrorType.UI.value == "ui"
        assert ErrorType.NETWORK.value == "network"

    def test_severity_enum_access(self):
        """测试严重程度枚举访问"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.CRITICAL.value == "critical"
