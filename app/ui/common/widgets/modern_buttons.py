#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化按钮组件
"""

from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QPen, QFont


class ModernButton(QPushButton):
    """
    现代按钮

    特点:
    - 渐变背景
    - 平滑过渡
    - 多种样式变体
    - 支持图标
    """

    def __init__(
        self,
        text: str = "",
        style: str = "default",  # default, primary, secondary, danger, ghost
        size: str = "medium",    # small, medium, large
        icon: str = None,        # 图标（emoji或unicode字符）
        parent: QWidget = None,
    ):
        super().__init__(text, parent)
        self.style_type = style
        self.size_type = size
        self.icon = icon

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """设置UI"""
        size_map = {
            "small": (32, 12, 20),
            "medium": (40, 12, 24),
            "large": (48, 16, 32),
        }

        height, v_pad, h_pad = size_map.get(self.size_type, (40, 12, 24))

        self.setMinimumHeight(height)
        self.setStyleSheet(f"padding: {v_pad}px {h_pad}px;")

    def _apply_style(self):
        """应用样式"""
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 根据样式类型应用不同的CSS
        style_map = {
            "default": """
                QPushButton {
                    background-color: rgba(0, 212, 255, 0.1);
                    color: #00D4FF;
                    border: 1px solid rgba(0, 212, 255, 0.3);
                    border-radius: 8px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(0, 212, 255, 0.2),
                                stop:1 rgba(139, 92, 246, 0.2));
                    border-color: rgba(0, 212, 255, 0.5);
                    color: #4DE8FF;
                }
                QPushButton:pressed {
                    background: rgba(0, 212, 255, 0.15);
                }
            """,
            "primary": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #00D4FF,
                                stop:1 #8B5CF6);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #00A8CC,
                                stop:1 #7C3AED);
                    color: white;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #0096B4,
                                stop:1 #6D28D9);
                }
            """,
            "secondary": """
                QPushButton {
                    background: rgba(139, 92, 246, 0.1);
                    color: #8B5CF6;
                    border: 1px solid rgba(139, 92, 246, 0.3);
                    border-radius: 8px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(139, 92, 246, 0.2);
                    border-color: rgba(139, 92, 246, 0.5);
                    color: #A78BFA;
                }
            """,
            "danger": """
                QPushButton {
                    background: rgba(239, 68, 68, 0.15);
                    color: #EF4444;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 8px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(239, 68, 68, 0.25);
                    border-color: rgba(239, 68, 68, 0.5);
                }
            """,
            "ghost": """
                QPushButton {
                    background: transparent;
                    color: #F9FAFB;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.08);
                }
            """,
        }

        self.setStyleSheet(style_map.get(self.style_type, style_map["default"]))

    def set_size(self, size: str):
        """设置按钮大小"""
        self.size_type = size
        self._setup_ui()

    def set_style(self, style: str):
        """设置按钮样式"""
        self.style_type = style
        self._apply_style()


class IconButton(QPushButton):
    """
    图标按钮

    只显示图标的小型按钮
    """

    def __init__(
        self,
        icon: str,
        tooltip: str = "",
        size: int = 32,
        parent: QWidget = None,
    ):
        super().__init__(icon, parent)
        self.tooltip = tooltip
        self.icon_size = size
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedSize(self.icon_size, self.icon_size)
        self.setToolTip(self.tooltip)

        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 0px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.15);
            }
        """)

        self.setText(self.icon)


class ButtonGroup(QWidget):
    """
    按钮组

    水平排列的一组按钮
    """

    def __init__(self, buttons: list = None, spacing: int = 8, parent: QWidget = None):
        super().__init__(parent)
        self.buttons = buttons or []
        self.spacing = spacing
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.layout = QHBoxLayout()
        self.layout.setSpacing(self.spacing)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        for btn in self.buttons:
            self.add_button(btn)

    def add_button(self, button: QPushButton):
        """添加按钮"""
        self.layout.addWidget(button)

    def add_stretch(self):
        """添加弹簧"""
        self.layout.addStretch()


class ToggleButton(QPushButton):
    """
    切换按钮

    点击切换开/关状态
    """

    def __init__(
        self,
        text: str = "",
        checked: bool = False,
        parent: QWidget = None,
    ):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self._update_style(is_init=True)

        self.toggled.connect(self._update_style)

    def _update_style(self, is_init: bool = False):
        """更新样式"""
        if self.isChecked():
            style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #00D4FF,
                                stop:1 #8B5CF6);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                }
            """
        else:
            style = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    color: #D1D5DB;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                }
            """

        if not is_init:
            self.setStyleSheet(style)


class LoadingButton(QPushButton):
    """
    加载按钮

    带加载状态的按钮
    """

    def __init__(
        self,
        text: str = "",
        loading_text: str = "加载中...",
        parent: QWidget = None,
    ):
        super().__init__(text, parent)
        self.original_text = text
        self.loading_text = loading_text
        self.is_loading = False

    def set_loading(self, loading: bool):
        """设置加载状态"""
        self.is_loading = loading

        if loading:
            self.setEnabled(False)
            self.setText(self.loading_text)
            # 添加旋转动画标识（简化处理）
            self.setProperty("loading", "true")
        else:
            self.setEnabled(True)
            self.setText(self.original_text)
            self.setProperty("loading", "")

        self._update_style()

    def _update_style(self):
        """更新样式"""
        base_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #00D4FF,
                            stop:1 #8B5CF6);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }
        """

        if self.is_loading:
            # 加载状态样式（添加微妙的动画效果）
            self.setStyleSheet(base_style + """
                QPushButton[loading="true"] {
                    opacity: 0.8;
                }
            """)
        else:
            self.setStyleSheet(base_style)
