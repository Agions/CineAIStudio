#!/usr/bin/env python3
"""测试 macOS 主题管理器"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.core.macOS_theme_manager import macOS_ThemeManager


class TestMacOSThemeManager:
    """测试 macOS 主题管理器"""

    @patch('app.core.macOS_theme_manager.QApplication')
    @patch('app.core.macOS_theme_manager.Path')
    def test_init(self, mock_path, mock_app):
        """测试初始化"""
        mock_path_instance = Mock()
        mock_path_instance.parent.parent.parent = Mock()
        mock_path_instance.parent.parent.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance
        
        mock_qapp = Mock()
        
        manager = macOS_ThemeManager(mock_qapp)
        
        assert manager.current_theme == "dark"

    @patch('app.core.macOS_theme_manager.QApplication')
    @patch('app.core.macOS_theme_manager.Path')
    def test_default_theme(self, mock_path, mock_app):
        """测试默认主题"""
        mock_path_instance = Mock()
        mock_path_instance.parent.parent.parent = Mock()
        mock_path_instance.parent.parent.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance
        
        mock_qapp = Mock()
        
        manager = macOS_ThemeManager(mock_qapp)
        
        assert manager.current_theme == "dark"

    @patch('app.core.macOS_theme_manager.QApplication')
    @patch('app.core.macOS_theme_manager.Path')
    def test_signals_exist(self, mock_path, mock_app):
        """测试信号存在"""
        mock_path_instance = Mock()
        mock_path_instance.parent.parent.parent = Mock()
        mock_path_instance.parent.parent.parent.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance
        
        mock_qapp = Mock()
        
        manager = macOS_ThemeManager(mock_qapp)
        
        assert hasattr(manager, 'theme_changed')
        assert hasattr(manager, 'before_apply')
        assert hasattr(manager, 'after_apply')
