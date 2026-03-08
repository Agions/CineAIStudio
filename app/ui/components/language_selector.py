#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语言切换组件
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import pyqtSignal, Qt

from app.utils.i18n import (
    I18n,
    set_locale,
    get_locale,
    get_available_locales,
)


class LanguageSelector(QWidget):
    """语言选择器"""
    
    language_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._i18n = I18n(get_locale())
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签
        self.label = QLabel(self)
        self.label.setText("语言 / Language:")
        
        # 下拉框
        self.combo = QComboBox(self)
        
        # 添加语言选项
        locales = get_available_locales()
        for code, name in locales.items():
            self.combo.addItem(name, code)
        
        # 设置当前语言
        current = get_locale()
        index = self.combo.findData(current)
        if index >= 0:
            self.combo.setCurrentIndex(index)
        
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
    
    def _connect_signals(self):
        self.combo.currentIndexChanged.connect(self._on_language_changed)
    
    def _on_language_changed(self, index):
        code = self.combo.currentData()
        if code:
            set_locale(code)
            self.language_changed.emit(code)
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        return self.combo.currentData()
    
    def set_language(self, code: str):
        """设置语言"""
        index = self.combo.findData(code)
        if index >= 0:
            self.combo.setCurrentIndex(index)
            set_locale(code)


class LanguageMenu:
    """语言菜单（用于 QMenu）"""
    
    @staticmethod
    def create_menu(parent) -> QWidget:
        """创建语言选择菜单"""
        from PyQt6.QtWidgets import QMenu, QWidgetAction, QVBoxLayout, QRadioButton, QGroupBox
        
        menu = QMenu(parent)
        
        # 创建语言选项组
        group = QGroupBox()
        layout = QVBoxLayout()
        
        current = get_locale()
        locales = get_available_locales()
        
        for code, name in locales.items():
            radio = QRadioButton(name)
            radio.setData(code)
            if code == current:
                radio.setChecked(True)
            radio.toggled.connect(
                lambda checked, c=code: set_locale(c) if checked else None
            )
            layout.addWidget(radio)
        
        group.setLayout(layout)
        
        # 添加到菜单
        action = QWidgetAction(menu)
        action.setDefaultWidget(group)
        menu.addAction(action)
        
        return menu
