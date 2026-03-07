#!/usr/bin/env python3
"""测试图标管理器"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.core.icon_manager import IconManager, STANDARD_ICONS


class TestStandardIcons:
    """测试标准图标映射"""

    def test_standard_icons_exist(self):
        """测试标准图标存在"""
        assert "home" in STANDARD_ICONS
        assert "settings" in STANDARD_ICONS
        assert "video" in STANDARD_ICONS

    def test_standard_icons_format(self):
        """测试标准图标格式"""
        for name, qt_icon in STANDARD_ICONS.items():
            assert name.islower()
            assert qt_icon.startswith("SP_")


class TestIconManager:
    """测试图标管理器"""

    @patch('app.core.icon_manager.QIcon')
    def test_init_default(self, mock_qicon):
        """测试默认初始化"""
        manager = IconManager()
        
        assert manager.icon_dir.name == "icons"
        assert manager._current_theme == "light"
        assert isinstance(manager._icon_cache, dict)

    @patch('app.core.icon_manager.QIcon')
    def test_init_custom_dir(self, mock_qicon):
        """测试自定义目录"""
        manager = IconManager("/custom/icons")
        
        assert str(manager.icon_dir) == "/custom/icons"

    @patch('app.core.icon_manager.QIcon')
    def test_cache_functionality(self, mock_qicon):
        """测试缓存功能"""
        manager = IconManager()
        
        # 设置一个缓存项
        manager._icon_cache["test_24_light"] = Mock()
        
        # 应该从缓存返回
        result = manager.get_icon("test", 24, "light")
        assert result == manager._icon_cache["test_24_light"]

    @patch('app.core.icon_manager.QIcon')
    def test_default_theme(self, mock_qicon):
        """测试默认主题"""
        manager = IconManager()
        
        assert manager._current_theme == "light"
        
        manager.set_theme("dark")
        assert manager._current_theme == "dark"

    @patch('app.core.icon_manager.QIcon')
    def test_clear_cache(self, mock_qicon):
        """测试清除缓存"""
        manager = IconManager()
        
        # 添加缓存
        manager._icon_cache["test"] = Mock()
        
        # 清除
        manager.clear_cache()
        
        assert len(manager._icon_cache) == 0


class TestIconManagerMethods:
    """测试图标管理器方法"""

    @patch('app.core.icon_manager.QIcon')
    def test_get_standard_icon(self, mock_qicon):
        """测试获取标准图标"""
        manager = IconManager()
        
        # 模拟 QIcon
        mock_icon_instance = Mock()
        mock_qicon.fromTheme.return_value = mock_icon_instance
        
        icon = manager._get_standard_icon("home", 24)
        
        assert icon is not None

    @patch('app.core.icon_manager.QIcon')
    def test_list_icons(self, mock_qicon):
        """测试列出图标"""
        manager = IconManager()
        
        icons = manager.list_icons()
        
        assert isinstance(icons, list)


class TestIconManagerTheme:
    """测试主题切换"""

    @patch('app.core.icon_manager.QIcon')
    def test_theme_switch(self, mock_qicon):
        """测试主题切换"""
        manager = IconManager()
        
        # 切换到深色主题
        manager.set_theme("dark")
        assert manager._current_theme == "dark"
        
        # 切换到浅色主题
        manager.set_theme("light")
        assert manager._current_theme == "light"

    @patch('app.core.icon_manager.QIcon')
    def test_invalid_theme(self, mock_qicon):
        """测试无效主题"""
        manager = IconManager()
        
        # 设置无效主题应该不崩溃
        manager.set_theme("invalid_theme")
        # 应该保持原主题
        assert manager._current_theme in ["light", "dark"]
