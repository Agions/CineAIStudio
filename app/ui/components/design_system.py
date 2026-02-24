#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineFlow 设计系统 - 统一 UI 组件
提供所有组件的统一样式和行为
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette


class DesignSystem:
    """设计系统"""
    
    # 颜色常量
    COLORS = {
        # 主色
        "primary": "#2196F3",
        "primary_dark": "#1976D2",
        "primary_light": "#64B5F6",
        
        # 辅助色
        "secondary": "#9C27B0",
        "accent": "#FF4081",
        
        # 功能色
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
        
        # 背景色 (深色主题)
        "background": "#1E1E1E",
        "surface": "#2D2D2D",
        "card": "#2D2D2D",
        "border": "#404040",
        
        # 文字色
        "text": "#FFFFFF",
        "text_secondary": "#CCCCCC",
        "text_disabled": "#666666",
    }
    
    # 字体大小
    FONT_SIZES = {
        "xs": 10,
        "sm": 12,
        "md": 14,
        "lg": 16,
        "xl": 18,
        "xxl": 24,
    }
    
    # 间距
    SPACING = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
    }
    
    # 圆角
    BORDER_RADIUS = {
        "sm": 4,
        "md": 8,
        "lg": 12,
    }
    
    @classmethod
    def get_color(cls, name: str) -> str:
        """获取颜色"""
        return cls.COLORS.get(name, cls.COLORS["primary"])
    
    @classmethod
    def get_font_size(cls, size: str) -> int:
        """获取字体大小"""
        return cls.FONT_SIZES.get(size, cls.FONT_SIZES["md"])
    
    @classmethod
    def get_spacing(cls, size: str) -> int:
        """获取间距"""
        return cls.SPACING.get(size, cls.SPACING["md"])


class StyleSheet:
    """样式表生成器"""
    
    @staticmethod
    def button_primary() -> str:
        """主按钮样式"""
        return f"""
        QPushButton {{
            background-color: {DesignSystem.COLORS["primary"]};
            color: {DesignSystem.COLORS["text"]};
            border: none;
            border-radius: {DesignSystem.BORDER_RADIUS["md"]}px;
            padding: {DesignSystem.SPACING["sm"]}px {DesignSystem.SPACING["md"]}px;
            font-size: {DesignSystem.FONT_SIZES["md"]}px;
        }}
        QPushButton:hover {{
            background-color: {DesignSystem.COLORS["primary_dark"]};
        }}
        QPushButton:pressed {{
            background-color: {DesignSystem.COLORS["primary_dark"]};
        }}
        QPushButton:disabled {{
            background-color: {DesignSystem.COLORS["border"]};
            color: {DesignSystem.COLORS["text_disabled"]};
        }}
        """
    
    @staticmethod
    def button_secondary() -> str:
        """次按钮样式"""
        return f"""
        QPushButton {{
            background-color: {DesignSystem.COLORS["surface"]};
            color: {DesignSystem.COLORS["text"]};
            border: 1px solid {DesignSystem.COLORS["border"]};
            border-radius: {DesignSystem.BORDER_RADIUS["md"]}px;
            padding: {DesignSystem.SPACING["sm"]}px {DesignSystem.SPACING["md"]}px;
            font-size: {DesignSystem.FONT_SIZES["md"]}px;
        }}
        QPushButton:hover {{
            background-color: {DesignSystem.COLORS["border"]};
        }}
        """
    
    @staticmethod
    def card() -> str:
        """卡片样式"""
        return f"""
        QWidget {{
            background-color: {DesignSystem.COLORS["card"]};
            border: 1px solid {DesignSystem.COLORS["border"]};
            border-radius: {DesignSystem.BORDER_RADIUS["md"]}px;
        }}
        """
    
    @staticmethod
    def input() -> str:
        """输入框样式"""
        return f"""
        QLineEdit, QTextEdit {{
            background-color: {DesignSystem.COLORS["surface"]};
            color: {DesignSystem.COLORS["text"]};
            border: 1px solid {DesignSystem.COLORS["border"]};
            border-radius: {DesignSystem.BORDER_RADIUS["sm"]}px;
            padding: {DesignSystem.SPACING["sm"]}px;
            font-size: {DesignSystem.FONT_SIZES["md"]}px;
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {DesignSystem.COLORS["primary"]};
        }}
        """
    
    @staticmethod
    def label() -> str:
        """标签样式"""
        return f"""
        QLabel {{
            color: {DesignSystem.COLORS["text"]};
            font-size: {DesignSystem.FONT_SIZES["md"]}px;
        }}
        """
    
    @staticmethod
    def panel() -> str:
        """面板样式"""
        return f"""
        QWidget {{
            background-color: {DesignSystem.COLORS["surface"]};
        }}
        """


class CFButton(QPushButton):
    """CineFlow 按钮组件"""
    
    def __init__(self, text: str = "", variant: str = "primary", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.variant = variant
        self._apply_style()
    
    def _apply_style(self):
        """应用样式"""
        if self.variant == "primary":
            self.setStyleSheet(StyleSheet.button_primary())
        elif self.variant == "secondary":
            self.setStyleSheet(StyleSheet.button_secondary())
        else:
            self.setStyleSheet(StyleSheet.button_primary())
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class CFLabel(QLabel):
    """CineFlow 标签组件"""
    
    def __init__(self, text: str = "", size: str = "md", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.size = size
        self._apply_style()
    
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet(StyleSheet.label())
        font_size = DesignSystem.get_font_size(self.size)
        self.setFont(QFont("", font_size))


class CFCard(QWidget):
    """CineFlow 卡片组件"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._apply_style()
    
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet(StyleSheet.card())


class CFInput(QLineEdit):
    """CineFlow 输入框组件"""
    
    def __init__(self, placeholder: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._apply_style()
    
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet(StyleSheet.input())
