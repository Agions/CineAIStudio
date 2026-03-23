#!/usr/bin/env python3
"""测试主窗口事件处理器"""

import pytest
from unittest.mock import Mock, MagicMock

from app.ui.main.event_handler import MainWindowEventHandler


class TestMainWindowEventHandler:
    """测试主窗口事件处理器"""

    def test_init(self):
        """测试初始化"""
        mock_window = Mock()
        handler = MainWindowEventHandler(mock_window)
        
        assert handler.window is mock_window
        assert handler.logger is not None

    def test_status_messages_exist(self):
        """测试状态消息存在"""
        mock_window = Mock()
        handler = MainWindowEventHandler(mock_window)
        
        assert "initializing" in handler._status_messages
        assert "ready" in handler._status_messages
        assert "error" in handler._status_messages

    def test_get_status_message(self):
        """测试获取状态消息"""
        mock_window = Mock()
        handler = MainWindowEventHandler(mock_window)
        
        message = handler.get_status_message("ready")
        assert message == "就绪"

    def test_get_unknown_status_message(self):
        """测试获取未知状态消息"""
        mock_window = Mock()
        handler = MainWindowEventHandler(mock_window)
        
        message = handler.get_status_message("unknown_state")
        assert message == "unknown_state"

    def test_on_theme_changed_dark(self):
        """测试主题变更为深色"""
        mock_window = Mock()
        mock_window.is_dark_theme = False
        
        handler = MainWindowEventHandler(mock_window)
        handler.on_theme_changed("dark")
        
        assert mock_window.is_dark_theme is True
        mock_window._apply_theme.assert_called_once()
        mock_window._apply_style.assert_called_once()

    def test_on_theme_changed_light(self):
        """测试主题变更为浅色"""
        mock_window = Mock()
        mock_window.is_dark_theme = True
        
        handler = MainWindowEventHandler(mock_window)
        handler.on_theme_changed("light")
        
        assert mock_window.is_dark_theme is False

    def test_on_layout_changed(self):
        """测试布局变更"""
        mock_window = Mock()
        mock_window.layout_changed = Mock()
        
        handler = MainWindowEventHandler(mock_window)
        handler.on_layout_changed("compact")
        
        mock_window.layout_changed.emit.assert_called_once_with("compact")

    def test_on_error(self):
        """测试错误处理"""
        mock_window = Mock()
        mock_window.statusBar = Mock(return_value=Mock())
        
        handler = MainWindowEventHandler(mock_window)
        handler.on_error("TestError", "测试错误消息")
        
        # 验证日志记录
        assert handler.logger.error.called

    def test_update_current_time(self):
        """测试更新时间"""
        mock_window = Mock()
        mock_window.current_time = Mock()
        
        handler = MainWindowEventHandler(mock_window)
        
        # 不应该抛出异常
        try:
            handler.update_current_time()
        except Exception as e:
            pytest.fail(f"update_current_time raised exception: {e}")

    def test_update_current_time_exception(self):
        """测试更新时间异常处理"""
        mock_window = Mock()
        mock_window.current_time = Mock()
        mock_window.current_time.setText.side_effect = Exception("Test error")
        
        handler = MainWindowEventHandler(mock_window)
        
        # 不应该抛出异常
        handler.update_current_time()
