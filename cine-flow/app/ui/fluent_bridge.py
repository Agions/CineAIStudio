#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow UI 基础设施
集成 PyQt6-Fluent-Widgets，提供统一的 UI 组件接口

即使 Fluent Widgets 未安装也能降级运行（使用原生 PyQt6 组件）
"""

from typing import Optional

# 尝试导入 Fluent Widgets
_HAS_FLUENT = False
try:
    from qfluentwidgets import (
        FluentWindow,
        NavigationInterface,
        NavigationItemPosition,
        FluentIcon,
        InfoBar,
        InfoBarPosition,
        IndeterminateProgressBar,
        ProgressBar,
        PushButton,
        PrimaryPushButton,
        TransparentPushButton,
        ToolButton,
        SwitchButton,
        ComboBox,
        LineEdit,
        TextEdit,
        SearchLineEdit,
        SpinBox,
        Slider,
        CardWidget,
        ElevatedCardWidget,
        SimpleCardWidget,
        IconWidget,
        BodyLabel,
        SubtitleLabel,
        TitleLabel,
        CaptionLabel,
        StrongBodyLabel,
        MessageBox,
        Dialog,
        Flyout,
        FlyoutView,
        TeachingTip,
        StateToolTip,
        setTheme,
        Theme,
        setThemeColor,
        isDarkTheme,
    )
    _HAS_FLUENT = True
except ImportError:
    pass


def has_fluent() -> bool:
    """是否有 Fluent Widgets 可用"""
    return _HAS_FLUENT


def apply_fluent_theme(dark: bool = True, accent_color: str = "#2962FF"):
    """
    应用 Fluent 主题

    Args:
        dark: 是否暗色主题
        accent_color: 强调色
    """
    if _HAS_FLUENT:
        setTheme(Theme.DARK if dark else Theme.LIGHT)
        setThemeColor(accent_color)
    else:
        print("⚠️ PyQt6-Fluent-Widgets 未安装，使用原生主题")


def show_success_toast(parent, title: str, content: str,
                       duration: int = 3000):
    """显示成功 Toast"""
    if _HAS_FLUENT:
        InfoBar.success(
            title=title,
            content=content,
            parent=parent,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
        )
    else:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(parent, title, content)


def show_error_toast(parent, title: str, content: str,
                     duration: int = 5000):
    """显示错误 Toast"""
    if _HAS_FLUENT:
        InfoBar.error(
            title=title,
            content=content,
            parent=parent,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
        )
    else:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(parent, title, content)


def show_warning_toast(parent, title: str, content: str,
                       duration: int = 4000):
    """显示警告 Toast"""
    if _HAS_FLUENT:
        InfoBar.warning(
            title=title,
            content=content,
            parent=parent,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
        )
    else:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(parent, title, content)


def show_info_toast(parent, title: str, content: str,
                    duration: int = 3000):
    """显示信息 Toast"""
    if _HAS_FLUENT:
        InfoBar.info(
            title=title,
            content=content,
            parent=parent,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
        )
    else:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(parent, title, content)


def create_loading_indicator(parent=None):
    """创建加载指示器"""
    if _HAS_FLUENT:
        bar = IndeterminateProgressBar(parent)
        bar.setFixedHeight(3)
        return bar
    else:
        from PyQt6.QtWidgets import QProgressBar
        bar = QProgressBar(parent)
        bar.setRange(0, 0)
        bar.setFixedHeight(3)
        return bar


def show_state_tooltip(parent, title: str, content: str):
    """显示状态提示（进行中）"""
    if _HAS_FLUENT:
        tip = StateToolTip(title, content, parent)
        tip.move(parent.width() - tip.width() - 20, 20)
        tip.show()
        return tip
    return None


# ========== 组件工厂 ==========
# 如果 Fluent 可用就用 Fluent 组件，否则降级到原生 PyQt6

def create_button(text: str, parent=None, primary: bool = False):
    """创建按钮"""
    if _HAS_FLUENT:
        if primary:
            return PrimaryPushButton(text, parent)
        return PushButton(text, parent)
    else:
        from PyQt6.QtWidgets import QPushButton
        btn = QPushButton(text, parent)
        if primary:
            btn.setStyleSheet("background-color: #2962FF; color: white; padding: 8px 16px; border-radius: 4px;")
        return btn


def create_card(parent=None, elevated: bool = False):
    """创建卡片"""
    if _HAS_FLUENT:
        if elevated:
            return ElevatedCardWidget(parent)
        return SimpleCardWidget(parent)
    else:
        from PyQt6.QtWidgets import QFrame
        card = QFrame(parent)
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet("QFrame { background: #1E1E1E; border-radius: 8px; padding: 16px; }")
        return card


def create_line_edit(placeholder: str = "", parent=None):
    """创建输入框"""
    if _HAS_FLUENT:
        edit = LineEdit(parent)
        edit.setPlaceholderText(placeholder)
        return edit
    else:
        from PyQt6.QtWidgets import QLineEdit
        edit = QLineEdit(parent)
        edit.setPlaceholderText(placeholder)
        return edit


def create_search_box(placeholder: str = "搜索...", parent=None):
    """创建搜索框"""
    if _HAS_FLUENT:
        search = SearchLineEdit(parent)
        search.setPlaceholderText(placeholder)
        return search
    else:
        return create_line_edit(placeholder, parent)


def create_combo_box(parent=None):
    """创建下拉框"""
    if _HAS_FLUENT:
        return ComboBox(parent)
    else:
        from PyQt6.QtWidgets import QComboBox
        return QComboBox(parent)


def create_label(text: str, level: str = "body", parent=None):
    """
    创建标签

    level: "title" / "subtitle" / "body" / "strong" / "caption"
    """
    if _HAS_FLUENT:
        label_map = {
            "title": TitleLabel,
            "subtitle": SubtitleLabel,
            "body": BodyLabel,
            "strong": StrongBodyLabel,
            "caption": CaptionLabel,
        }
        cls = label_map.get(level, BodyLabel)
        return cls(text, parent)
    else:
        from PyQt6.QtWidgets import QLabel
        label = QLabel(text, parent)
        size_map = {"title": 24, "subtitle": 18, "body": 14, "strong": 14, "caption": 12}
        font_size = size_map.get(level, 14)
        bold = "font-weight: bold;" if level in ("title", "subtitle", "strong") else ""
        label.setStyleSheet(f"font-size: {font_size}px; {bold}")
        return label
