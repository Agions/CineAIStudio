#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

from ..theme_manager import get_theme_manager, ThemeType


class ThemeToggle(QWidget):
    """主题切换控件"""
    
    theme_changed = pyqtSignal(str)  # 主题变更信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.theme_manager = get_theme_manager()
        self._setup_ui()
        self._connect_signals()
        self._load_current_theme()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 主题标签
        self.theme_label = QLabel("主题:")
        self.theme_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.theme_label)
        
        # 主题选择下拉框
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题", "自动"])
        self.theme_combo.setMinimumWidth(120)
        layout.addWidget(self.theme_combo)
        
        # 快速切换按钮
        self.quick_toggle_btn = QPushButton("🌓")
        self.quick_toggle_btn.setToolTip("快速切换明暗主题")
        self.quick_toggle_btn.setMaximumWidth(40)
        self.quick_toggle_btn.setObjectName("theme_toggle_button")
        layout.addWidget(self.quick_toggle_btn)
        
        # 设置样式
        self._apply_styles()
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                background-color: #ffffff;
                min-height: 28px;
            }
            
            QComboBox:hover {
                border-color: #40a9ff;
            }
            
            QPushButton#theme_toggle_button {
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 16px;
                min-height: 28px;
                max-height: 28px;
            }
            
            QPushButton#theme_toggle_button:hover {
                border-color: #40a9ff;
                background-color: #f0f9ff;
            }
            
            QLabel {
                color: #595959;
                font-weight: 500;
            }
        """)
    
    def _connect_signals(self):
        """连接信号"""
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.quick_toggle_btn.clicked.connect(self._quick_toggle_theme)
        self.theme_manager.theme_changed.connect(self._on_theme_manager_changed)
    
    def _load_current_theme(self):
        """加载当前主题设置"""
        current_theme = self.theme_manager.get_current_theme()
        
        theme_map = {
            ThemeType.LIGHT: "浅色主题",
            ThemeType.DARK: "深色主题",
            ThemeType.AUTO: "自动"
        }
        
        theme_text = theme_map.get(current_theme, "浅色主题")
        
        # 阻止信号触发，避免循环
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(theme_text)
        self.theme_combo.blockSignals(False)
        
        # 更新快速切换按钮图标
        self._update_toggle_button_icon(current_theme)
    
    def _on_theme_changed(self, theme_text: str):
        """主题选择变更"""
        # 映射主题文本到主题类型
        theme_map = {
            "浅色主题": "light",
            "深色主题": "dark",
            "自动": "auto"
        }
        
        theme_value = theme_map.get(theme_text, "light")
        
        # 应用主题
        self.theme_manager.set_theme(theme_value)
        
        # 发射信号
        self.theme_changed.emit(theme_value)
    
    def _quick_toggle_theme(self):
        """快速切换主题"""
        current_theme = self.theme_manager.get_current_theme()
        
        # 在浅色和深色主题之间切换
        if current_theme == ThemeType.LIGHT:
            new_theme = "深色主题"
        else:
            new_theme = "浅色主题"
        
        self.theme_combo.setCurrentText(new_theme)
    
    def _update_toggle_button_icon(self, theme_type: ThemeType):
        """更新快速切换按钮图标"""
        if theme_type == ThemeType.DARK:
            self.quick_toggle_btn.setText("🌙")
            self.quick_toggle_btn.setToolTip("切换到浅色主题")
        else:
            self.quick_toggle_btn.setText("☀️")
            self.quick_toggle_btn.setToolTip("切换到深色主题")
    
    def _on_theme_manager_changed(self, theme_value: str):
        """主题管理器主题变更"""
        # 更新UI状态
        theme_map = {
            "light": "浅色主题",
            "dark": "深色主题",
            "auto": "自动"
        }
        
        theme_text = theme_map.get(theme_value, "浅色主题")
        
        # 阻止信号触发
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(theme_text)
        self.theme_combo.blockSignals(False)
        
        # 更新按钮图标
        theme_type = ThemeType.LIGHT if theme_value == "light" else ThemeType.DARK
        self._update_toggle_button_icon(theme_type)
        
        # 更新样式以适应新主题
        self._update_styles_for_theme(theme_value)
    
    def _update_styles_for_theme(self, theme_value: str):
        """根据主题更新样式"""
        if theme_value == "dark":
            self.setStyleSheet("""
                QComboBox {
                    padding: 6px 12px;
                    border: 1px solid #434343;
                    border-radius: 6px;
                    background-color: #1f1f1f;
                    color: #ffffff;
                    min-height: 28px;
                }
                
                QComboBox:hover {
                    border-color: #3c9ae8;
                }
                
                QPushButton#theme_toggle_button {
                    border: 1px solid #434343;
                    border-radius: 6px;
                    background-color: #1f1f1f;
                    color: #ffffff;
                    font-size: 16px;
                    min-height: 28px;
                    max-height: 28px;
                }
                
                QPushButton#theme_toggle_button:hover {
                    border-color: #3c9ae8;
                    background-color: #111b26;
                }
                
                QLabel {
                    color: #a6a6a6;
                    font-weight: 500;
                }
            """)
        else:
            self._apply_styles()  # 使用默认浅色样式
    
    def set_theme(self, theme_value: str):
        """设置主题（外部调用）"""
        theme_map = {
            "light": "浅色主题",
            "dark": "深色主题", 
            "auto": "自动"
        }
        
        theme_text = theme_map.get(theme_value, "浅色主题")
        self.theme_combo.setCurrentText(theme_text)


class CompactThemeToggle(QWidget):
    """紧凑型主题切换控件（仅图标）"""
    
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.theme_manager = get_theme_manager()
        self._setup_ui()
        self._connect_signals()
        self._load_current_theme()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 主题切换按钮
        self.toggle_btn = QPushButton("🌓")
        self.toggle_btn.setToolTip("切换主题")
        self.toggle_btn.setMaximumSize(32, 32)
        self.toggle_btn.setObjectName("compact_theme_toggle")
        layout.addWidget(self.toggle_btn)
        
        self._apply_styles()
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QPushButton#compact_theme_toggle {
                border: 1px solid #d9d9d9;
                border-radius: 16px;
                background-color: #ffffff;
                font-size: 14px;
            }
            
            QPushButton#compact_theme_toggle:hover {
                border-color: #40a9ff;
                background-color: #f0f9ff;
            }
        """)
    
    def _connect_signals(self):
        """连接信号"""
        self.toggle_btn.clicked.connect(self._toggle_theme)
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _load_current_theme(self):
        """加载当前主题"""
        current_theme = self.theme_manager.get_current_theme()
        self._update_button_icon(current_theme)
    
    def _toggle_theme(self):
        """切换主题"""
        current_theme = self.theme_manager.get_current_theme()
        
        if current_theme == ThemeType.LIGHT:
            new_theme = "dark"
        else:
            new_theme = "light"
        
        self.theme_manager.set_theme(new_theme)
        self.theme_changed.emit(new_theme)
    
    def _update_button_icon(self, theme_type: ThemeType):
        """更新按钮图标"""
        if theme_type == ThemeType.DARK:
            self.toggle_btn.setText("🌙")
            self.toggle_btn.setToolTip("切换到浅色主题")
        else:
            self.toggle_btn.setText("☀️")
            self.toggle_btn.setToolTip("切换到深色主题")
    
    def _on_theme_changed(self, theme_value: str):
        """主题变更响应"""
        theme_type = ThemeType.LIGHT if theme_value == "light" else ThemeType.DARK
        self._update_button_icon(theme_type)
        
        # 更新样式
        if theme_value == "dark":
            self.setStyleSheet("""
                QPushButton#compact_theme_toggle {
                    border: 1px solid #434343;
                    border-radius: 16px;
                    background-color: #1f1f1f;
                    color: #ffffff;
                    font-size: 14px;
                }
                
                QPushButton#compact_theme_toggle:hover {
                    border-color: #3c9ae8;
                    background-color: #111b26;
                }
            """)
        else:
            self._apply_styles()
