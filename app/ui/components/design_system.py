#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlowCut 设计系统 - 统一 UI 组件
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QTextEdit, 
    QFrame, QProgressBar, QSlider, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class DesignSystem:
    """设计系统常量"""
    
    COLORS = {
        "primary": "#2196F3",
        "primary_dark": "#1976D2",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "background": "#1E1E1E",
        "surface": "#2D2D2D",
        "card": "#2D2D2D",
        "card_hover": "#383838",
        "border": "#404040",
        "text": "#FFFFFF",
        "text_secondary": "#CCCCCC",
        "text_disabled": "#666666",
    }
    
    FONT_SIZES = {"xs": 10, "sm": 12, "md": 14, "lg": 16, "xl": 18}
    SPACING = {"xs": 4, "sm": 8, "md": 16, "lg": 24}
    BORDER_RADIUS = {"sm": 4, "md": 8, "lg": 12}


class StyleSheet:
    """样式生成器"""
    
    @staticmethod
    def button(variant="primary"):
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        spacing = DesignSystem.SPACING
        bg = colors.get(variant, colors["primary"])
        return f"""
        QPushButton {{
            background-color: {bg};
            color: {colors['text']};
            border: none;
            border-radius: {radius['md']}px;
            padding: {spacing['sm']}px {spacing['md']}px;
            font-size: 14px;
        }}
        QPushButton:hover {{ background-color: {colors['primary_dark']}; }}
        QPushButton:disabled {{ background-color: {colors['border']}; color: {colors['text_disabled']}; }}
        """
    
    @staticmethod
    def card():
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        return f"""
        QWidget {{
            background-color: {colors['card']};
            border: 1px solid {colors['border']};
            border-radius: {radius['md']}px;
        }}
        """
    
    @staticmethod
    def input():
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        spacing = DesignSystem.SPACING
        return f"""
        QLineEdit, QTextEdit {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: {radius['sm']}px;
            padding: {spacing['sm']}px;
        }}
        QLineEdit:focus {{ border-color: {colors['primary']}; }}
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
        return f"""
        QProgressBar {{ background-color: {colors['surface']}; border: none; text-align: center; color: {colors['text']}; }}
        QProgressBar::chunk {{ background-color: {colors['primary']}; }}
        """
    
    @staticmethod
    def nav_button(selected=False):
        colors = DesignSystem.COLORS
        radius = DesignSystem.BORDER_RADIUS
        bg = colors["card"] if selected else "transparent"
        return f"""
        QPushButton {{
            text-align: left;
            background-color: {bg};
            border: none;
            border-radius: {radius['md']}px;
            color: {colors['text_secondary']};
            padding: 10px 16px;
        }}
        QPushButton:hover {{ background-color: {colors['border']}; color: {colors['text']}; }}
        """


class CFButton(QPushButton):
    """ClipFlowCut 按钮"""
    
    def __init__(self, text="", variant="primary", icon="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(StyleSheet.button(variant))
        if icon:
            self.setText(f"{icon} {text}")
        self.setCursor(Qt.PointingHandCursor)


class CFLabel(QLabel):
    """ClipFlowCut 标签"""
    
    def __init__(self, text="", secondary=False, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(StyleSheet.label(secondary))


class CFCard(QWidget):
    """ClipFlowCut 卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.card())


class CFPanel(QWidget):
    """ClipFlowCut 面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.panel())


class CFInput(QLineEdit):
    """ClipFlowCut 输入框"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(StyleSheet.input())


class CFProgressBar(QProgressBar):
    """ClipFlowCut 进度条"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.progress_bar())


class CFNavButton(CFButton):
    """ClipFlowCut 导航按钮"""
    
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
