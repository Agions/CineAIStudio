#!/usr/bin/env python3
"""测试 UI 组件"""

import pytest
from unittest.mock import Mock, patch

# 由于 PyQt6 需要 QApplication，我们使用 mock


class TestMacButtonImports:
    """测试按钮组件导入"""

    def test_import_buttons(self):
        """测试导入按钮类"""
        from app.ui.components.buttons import (
            MacButton,
            MacPrimaryButton,
            MacSecondaryButton,
            MacDangerButton,
            MacIconButton,
            MacButtonGroup,
        )
        
        # 验证类存在
        assert MacButton is not None
        assert MacPrimaryButton is not None
        assert MacSecondaryButton is not None
        assert MacDangerButton is not None
        assert MacIconButton is not None
        assert MacButtonGroup is not None


class TestMacLabelImports:
    """测试标签组件导入"""

    def test_import_labels(self):
        """测试导入标签类"""
        from app.ui.components.labels import (
            MacLabel,
            MacTitleLabel,
            MacBadge,
            MacStatLabel,
        )
        
        assert MacLabel is not None
        assert MacTitleLabel is not None
        assert MacBadge is not None
        assert MacStatLabel is not None


class TestMacContainerImports:
    """测试容器组件导入"""

    def test_import_containers(self):
        """测试导入容器类"""
        from app.ui.components.containers import (
            MacCard,
            MacElevatedCard,
            MacSection,
        )
        
        assert MacCard is not None
        assert MacElevatedCard is not None
        assert MacSection is not None


class TestMacInputImports:
    """测试输入组件导入"""

    def test_import_inputs(self):
        """测试导入输入类"""
        from app.ui.components.inputs import MacSearchBox
        
        assert MacSearchBox is not None


class TestMacLayoutImports:
    """测试布局组件导入"""

    def test_import_layouts(self):
        """测试导入布局类"""
        from app.ui.components.layout import (
            MacScrollArea,
            MacGrid,
            MacPageToolbar,
            MacEmptyState,
        )
        
        assert MacScrollArea is not None
        assert MacGrid is not None
        assert MacPageToolbar is not None
        assert MacEmptyState is not None


class TestThemeImports:
    """测试主题模块导入"""

    def test_import_theme(self):
        """测试导入主题类"""
        from app.ui.theme import (
            ThemeManager,
            ThemeColors,
            ThemePreset,
            ThemePresets,
            ThemeToggleButton,
        )
        
        assert ThemeManager is not None
        assert ThemeColors is not None
        assert ThemePreset is not None
        assert ThemePresets is not None
        assert ThemeToggleButton is not None


class TestMainConstants:
    """测试主窗口常量"""

    def test_page_type_enum(self):
        """测试页面类型枚举"""
        from app.ui.main.constants import PageType
        
        assert PageType.HOME.value == "home"
        assert PageType.SETTINGS.value == "settings"
        assert PageType.PROJECTS.value == "projects"
        assert PageType.VIDEO_EDITOR.value == "video_editor"

    def test_window_config(self):
        """测试窗口配置"""
        from app.ui.main.constants import WindowConfig
        
        config = WindowConfig()
        
        assert config.title == "ClipFlowCut"
        assert config.width == 1200
        assert config.height == 800
        assert config.min_width == 800
        assert config.min_height == 600
