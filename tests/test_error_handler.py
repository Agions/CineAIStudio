#!/usr/bin/env python3
"""测试错误处理器"""

import pytest
from dataclasses import asdict

from app.utils.error_handler import ErrorHandler, ErrorInfo


class TestErrorInfo:
    """测试错误信息数据类"""

    def test_creation_minimal(self):
        """测试创建最小错误信息"""
        info = ErrorInfo(
            error_type="ValueError",
            severity="error",
            message="测试错误"
        )
        
        assert info.error_type == "ValueError"
        assert info.severity == "error"
        assert info.message == "测试错误"
        assert info.exception is None
        assert info.details == ""

    def test_creation_full(self):
        """测试创建完整错误信息"""
        exc = ValueError("测试异常")
        info = ErrorInfo(
            error_type="ValueError",
            severity="critical",
            message="严重错误",
            exception=exc,
            details="详细错误信息"
        )
        
        assert info.error_type == "ValueError"
        assert info.severity == "critical"
        assert info.message == "严重错误"
        assert info.exception is exc
        assert info.details == "详细错误信息"


class TestErrorHandler:
    """测试错误处理器"""

    def test_init_without_logger(self):
        """测试无日志器初始化"""
        handler = ErrorHandler()
        assert handler.logger is None

    def test_init_with_logger(self):
        """测试有日志器初始化"""
        class MockLogger:
            def __init__(self):
                self.messages = []
                
            def critical(self, msg, exc_info=None):
                self.messages.append(("critical", msg))
                
            def error(self, msg, exc_info=None):
                self.messages.append(("error", msg))
                
            def warning(self, msg):
                self.messages.append(("warning", msg))
                
            def info(self, msg):
                self.messages.append(("info", msg))
        
        mock_logger = MockLogger()
        handler = ErrorHandler(logger=mock_logger)
        
        info = ErrorInfo(
            error_type="ValueError",
            severity="error",
            message="测试错误"
        )
        
        handler.handle_error(info)
        
        assert len(mock_logger.messages) == 1
        assert mock_logger.messages[0][0] == "error"
        assert "测试错误" in mock_logger.messages[0][1]

    def test_handle_error_no_logger(self):
        """测试无日志器时的错误处理"""
        handler = ErrorHandler()
        
        # 不应该抛出异常
        info = ErrorInfo(
            error_type="ValueError",
            severity="warning",
            message="测试警告"
        )
        
        handler.handle_error(info)  # 应该正常完成

    def test_handle_error_severity_levels(self):
        """测试不同严重级别的处理"""
        class MockLogger:
            def __init__(self):
                self.messages = []
                
            def _add(self, level, msg):
                self.messages.append((level, msg))
                
            def critical(self, msg, exc_info=None):
                self._add("critical", msg)
                
            def error(self, msg, exc_info=None):
                self._add("error", msg)
                
            def warning(self, msg):
                self._add("warning", msg)
                
            def info(self, msg):
                self._add("info", msg)
        
        mock_logger = MockLogger()
        handler = ErrorHandler(logger=mock_logger)
        
        levels = ["info", "warning", "error", "critical"]
        
        for level in levels:
            info = ErrorInfo(
                error_type="TestError",
                severity=level,
                message=f"测试{level}"
            )
            handler.handle_error(info)
        
        assert len(mock_logger.messages) == 4
        assert mock_logger.messages[0][0] == "info"
        assert mock_logger.messages[1][0] == "warning"
        assert mock_logger.messages[2][0] == "error"
        assert mock_logger.messages[3][0] == "critical"
