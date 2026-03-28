#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VideoForge 设计系统 - 统一 UI 组件
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QTextEdit, 
    QFrame, QProgressBar, QSlider, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class DesignSystem:
    """设计系统常量 - VideoForge 现代暗色主题"""

    COLORS = {
        # 主色调 - GitHub 风格暗色
        "primary": "#388BFD",
        "primary_dark": "#1F6FEB",
        "primary_light": "#58A6FF",

        # 成功/警告/错误
        "success": "#238636",
        "success_light": "#2EA043",
        "warning": "#D29922",
        "warning_light": "#E3B341",
        "error": "#DA3633",
        "error_light": "#F85149",

        # 背景色 - 层次分明
        "background": "#0D1117",       # 最深背景
        "surface": "#161B22",          # 卡片/面板背景
        "card": "#161B22",              # 卡片背景
        "card_hover": "#1C2128",       # 卡片悬停

        # 边框色
        "border": "#30363D",            # 默认边框
        "border_light": "#484F58",     # 浅色边框
        "divider": "#21262D",          # 分隔线

        # 文字色 - 清晰的层次
        "text": "#E6EDF3",             # 主要文字
        "text_secondary": "#C9D1D9",   # 次要文字
        "text_tertiary": "#8B949E",    # 辅助文字
        "text_disabled": "#484F58",    # 禁用文字

        # 强调色
        "accent": "#A371F7",           # 紫色强调
        "accent_light": "#BC8CFF",
    }

    # 渐变色
    GRADIENTS = {
        "primary": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #388BFD, stop:1 #79C0FF)",
        "surface": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #161B22, stop:1 #0D1117)",
    }

    # 阴影
    SHADOWS = {
        "card": "0 4px 12px rgba(0, 0, 0, 0.3)",
        "elevated": "0 8px 24px rgba(0, 0, 0, 0.4)",
    }

    FONT_SIZES = {
        "xs": 11,
        "sm": 12,
        "md": 14,
        "lg": 16,
        "xl": 18,
        "2xl": 24,
        "3xl": 32
    }

    SPACING = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
        "2xl": 48
    }

    BORDER_RADIUS = {
        "sm": 4,
        "md": 8,
        "lg": 12,
        "xl": 16,
        "full": 9999
    }

    # 字体
    FONTS = {
        "display": '"SF Pro Display", "Inter", "Segoe UI", -apple-system, sans-serif',
        "body": '"SF Pro Text", "Inter", "Segoe UI", -apple-system, sans-serif',
        "mono": '"SF Mono", "JetBrains Mono", "Consolas", monospace',
    }


class StyleSheet:
    """样式生成器 - VideoForge 现代暗色主题"""

    @staticmethod
    def button(variant="primary"):
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        spacing = DesignSystem.SPACING

        variants = {
            "primary": ("background-color: #238636;", "background-color: #2EA043;", "background-color: #238636;"),
            "secondary": ("background-color: transparent; border: 1px solid #30363D; color: #C9D1D9;",
                          "background-color: #21262D; border-color: #484F58;", "background-color: transparent;"),
            "danger": ("background-color: #DA3633; color: #FFFFFF;", "background-color: #F85149;", "background-color: #DA3633;"),
            "ghost": ("background-color: transparent; color: #8B949E;", "background-color: rgba(177, 186, 196, 0.08); color: #E6EDF3;", "background-color: transparent;"),
        }

        normal, hover, pressed = variants.get(variant, variants["primary"])
        return f"""
        QPushButton {{
            {normal}
            border-radius: {radius['md']}px;
            padding: {spacing['sm'] + 2}px {spacing['md'] + 2}px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{ {hover} }}
        QPushButton:pressed {{ {pressed} }}
        QPushButton:disabled {{ background-color: #21262D; color: #484F58; border: none; }}
        """
    
    @staticmethod
    def card():
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        return f"""
        QWidget {{
            background-color: {colors['card']};
            border: 1px solid {colors['border']};
            border-radius: {radius['lg']}px;
        }}
        QWidget:hover {{
            border-color: {colors['border_light']};
        }}
        """

    @staticmethod
    def input():
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        spacing = DesignSystem.SPACING
        return f"""
        QLineEdit, QTextEdit {{
            background-color: {colors['background']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: {radius['md']}px;
            padding: {spacing['sm'] + 2}px {spacing['sm'] + 4}px;
            font-size: 14px;
        }}
        QLineEdit:hover, QTextEdit:hover {{
            border-color: {colors['border_light']};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {colors['primary']};
            background-color: {colors['surface']};
        }}
        """
    
    @staticmethod
    def label(secondary=False):
        colors = DesignSystem.COLORS
        color = colors["text_secondary"] if secondary else colors["text"]
        return f"QLabel {{ color: {color}; font-size: 14px; }}"

    @staticmethod
    def panel():
        colors = DesignSystem.COLORS
        return f"QWidget {{ background-color: {colors['surface']}; }}"

    @staticmethod
    def progress_bar():
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        return f"""
        QProgressBar {{
            background-color: {colors['divider']};
            border: none;
            border-radius: {radius['md']}px;
            text-align: center;
            color: {colors['text']};
            font-size: 12px;
            font-weight: 600;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #388BFD, stop:1 #79C0FF);
            border-radius: {radius['md']}px;
        }}
        """

    @staticmethod
    def nav_button(selected=False):
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        if selected:
            bg = "rgba(56, 139, 253, 0.15)"
            color = "#388BFD"
        else:
            bg = "transparent"
            color = "#8B949E"
        return f"""
        QPushButton {{
            text-align: left;
            background-color: {bg};
            border: none;
            border-radius: {radius['md']}px;
            color: {color};
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: rgba(177, 186, 196, 0.08);
            color: #E6EDF3;
        }}
        """

    @staticmethod
    def card_elevated():
        """提升的卡片样式"""
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        return f"""
        QWidget {{
            background-color: {colors['card']};
            border: 1px solid {colors['border']};
            border-radius: {radius['lg']}px;
        }}
        """

    @staticmethod
    def tooltip():
        """提示框样式"""
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        return f"""
        QToolTip {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: {radius['md']}px;
            padding: 6px 10px;
            font-size: 12px;
        }}
        """


class CFButton(QPushButton):
    """VideoForge 按钮"""
    
    def __init__(self, text="", variant="primary", icon="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(StyleSheet.button(variant))
        if icon:
            self.setText(f"{icon} {text}")
        self.setCursor(Qt.PointingHandCursor)


class CFLabel(QLabel):
    """VideoForge 标签"""
    
    def __init__(self, text="", secondary=False, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(StyleSheet.label(secondary))


class CFCard(QWidget):
    """VideoForge 卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.card())


class CFPanel(QWidget):
    """VideoForge 面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.panel())


class CFInput(QLineEdit):
    """VideoForge 输入框"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(StyleSheet.input())


class CFProgressBar(QProgressBar):
    """VideoForge 进度条"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.progress_bar())


class CFNavButton(CFButton):
    """VideoForge 导航按钮"""
    
    def __init__(self, text="", icon="", selected=False, parent=None):
        super().__init__(text, variant="ghost", parent=parent)
        self.selected = selected
        if icon:
            self.setText(f"{icon} {text}")
        self._update_style()
    
    def _update_style(self):
        self.setStyleSheet(StyleSheet.nav_button(self.selected))
    
    def set_selected(self, selected):
        self.selected = selected
        self._update_style()
