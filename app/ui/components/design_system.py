#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlowCut 设计系统 - 统一 UI 组件

⚠️  注意：此模块已整合到 app.ui.theme.theme_manager
        样式定义已移至 ThemeManager.StyleSheet
        为保持向后兼容，此模块保留但从 theme_manager 导入样式
"""

# 从 theme_manager 导入样式类，保持向后兼容
from app.ui.theme.theme_manager import StyleSheet, ThemeColors

# 为保持向后兼容，导出 DesignSystem 作为 ThemeColors 的别名
DesignSystem = ThemeColors

# 导入 UI 组件（如果需要使用）
from app.ui.theme.theme_manager import (
    ThemeManager,
    ThemePreset,
    ThemeColors,
)

# ============ PyQt6 组件（已移至 theme_manager）===========
# 为保持向后兼容，这些组件现在从 theme_manager 导入

__all__ = [
    'DesignSystem',
    'StyleSheet',
    'ThemeManager',
    'ThemePreset',
    'ThemeColors',
]
