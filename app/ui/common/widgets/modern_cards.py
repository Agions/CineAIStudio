#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化玻璃拟态卡片组件
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPalette, QColor


class ModernCard(QWidget):
    """
    现代玻璃拟态卡片

    特点:
    - 半透明背景
    - 模糊效果
    - 渐变边框
    - 悬浮时高亮
    """

    clicked = pyqtSignal()

    def __init__(
        self,
        title: str = "",
        parent: QWidget = None,
        clickable: bool = False,
        padding: int = 24,
    ):
        super().__init__(parent)
        self.clickable = clickable
        self.padding = padding

        self._setup_ui(title)
        self._apply_style()

    def _setup_ui(self, title: str):
        """设置UI"""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
        self.layout.setSpacing(16)
        self.setLayout(self.layout)

        if title:
            title_label = QLabel(title)
            title_label.setProperty("class", "subtitle")
            title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #D1D5DB;")
            self.layout.addWidget(title_label)

        # 内容容器
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        self.layout.addLayout(self.content_layout)

        self.content_widget = QWidget()
        self.content_widget.setLayout(self.content_layout)
        self.layout.addWidget(self.content_widget)

    def _apply_style(self):
        """应用样式"""
        self.setObjectName("modern_card")
        self.setProperty("class", "card")

        if self.clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 玻璃拟态效果
        self.setStyleSheet("""
            ModernCard {
                background: rgba(31, 41, 55, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }

            ModernCard:hover {
                background: rgba(31, 41, 55, 0.8);
                border-color: rgba(255, 255, 255, 0.12);
            }
        """)

    def add_widget(self, widget: QWidget):
        """添加子控件"""
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        """添加布局"""
        self.content_layout.addLayout(layout)

    def add_spacer(self):
        """添加弹簧"""
        self.content_layout.addStretch()

    def set_padding(self, padding: int):
        """设置内边距"""
        self.padding = padding
        self.layout.setContentsMargins(padding, padding, padding, padding)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if self.clickable:
            self.clicked.emit()
        super().mousePressEvent(event)


class StatCard(ModernCard):
    """
    统计卡片

    用于展示关键指标的卡片布局
    """

    def __init__(self, title: str, value: str, subtitle: str = "", parent: QWidget = None):
        super().__init__(title, parent, padding=20)
        self._setup_stat_card(value, subtitle)

    def _setup_stat_card(self, value: str, subtitle: str):
        """设置统计卡片"""
        # 主数值
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #00D4FF;
        """)
        self.add_widget(value_label)

        # 副标题
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("""
                font-size: 13px;
                color: #9CA3AF;
            """)
            self.add_widget(sub_label)

    def update_value(self, value: str, subtitle: str = ""):
        """更新数值"""
        # 找到并更新标签
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                if i == 0:
                    widget.setText(value)
                elif subtitle and i == 1:
                    widget.setText(subtitle)


class FeatureCard(ModernCard):
    """
    功能卡片

    带图标和描述的功能卡片
    """

    def __init__(
        self,
        title: str,
        description: str,
        icon: str = "",
        parent: QWidget = None,
    ):
        super().__init__(parent=parent, clickable=True, padding=20)
        self._setup_feature_card(title, description, icon)

    def _setup_feature_card(self, title: str, description: str, icon: str):
        """设置功能卡片"""
        # 标题行
        title_layout = QHBoxLayout()

        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 24px;")
            title_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #F9FAFB;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        self.add_layout(title_layout)

        # 描述
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-size: 13px;
            color: #9CA3AF;
            line-height: 1.5;
        """)
        self.add_widget(desc_label)

        self.add_spacer()


class ActionCard(ModernCard):
    """
    操作卡片

    包含主要操作按钮的卡片
    """

    action_clicked = pyqtSignal()

    def __init__(
        self,
        title: str,
        action_text: str = "开始使用",
        parent: QWidget = None,
    ):
        super().__init__(title, parent=parent, padding=20)
        self._setup_action_card(action_text)

    def _setup_action_card(self, action_text: str):
        """设置操作卡片"""
        # 这里的按钮需要使用 ModernButton，简化处理
        from PyQt6.QtWidgets import QPushButton

        btn = QPushButton(action_text)
        btn.setProperty("class", "primary")
        btn.clicked.connect(self.action_clicked)
        self.add_widget(btn)
        self.add_spacer()


class CardGrid(QWidget):
    """
    卡片网格布局

    自动排列多张卡片
    """

    def __init__(self, columns: int = 2, spacing: int = 16, parent: QWidget = None):
        super().__init__(parent)
        self.columns = columns
        self.spacing = spacing
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        from PyQt6.QtWidgets import QGridLayout

        self.layout = QGridLayout()
        self.layout.setSpacing(self.spacing)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    def add_card(self, card: ModernCard, row: int = None, col: int = None):
        """添加卡片"""
        if row is None:
            row = len(self.cards) // self.columns
        if col is None:
            col = len(self.cards) % self.columns

        self.layout.addWidget(card, row, col, 1, 1)

    def clear(self):
        """清空所有卡片"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
