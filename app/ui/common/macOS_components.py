#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
macOS 设计系统 - 通用组件库
提供所有页面可复用的标准 UI 组件
所有组件都使用纯 QSS 类名，无任何内联样式
"""

from typing import Optional, Callable, List
from PyQt6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QScrollArea, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont


# =============================================================================
# 基础容器组件
# =============================================================================

class MacCard(QFrame):
    """macOS 风格卡片容器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(20, 20, 20, 20)
        self.layout().setSpacing(12)

    def set_interactive(self, interactive: bool = True):
        """设置为可交互卡片"""
        if interactive:
            self.setProperty("class", "card card-interactive")
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setProperty("class", "card")
            self.setCursor(Qt.ArrowCursor)
        self._refresh_style()

    def _refresh_style(self):
        """刷新样式"""
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class MacElevatedCard(MacCard):
    """提升的卡片（带阴影）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card card-elevated")


class MacSection(QFrame):
    """带标题的区域容器"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if title:
            self.title_label = QLabel(title)
            self.title_label.setProperty("class", "section-title")
            layout.addWidget(self.title_label)

        self.content_area = QWidget()
        self.content_area.setProperty("class", "section-content")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)

        layout.addWidget(self.content_area)

    def add_content(self, widget):
        """向内容区域添加组件"""
        self.content_layout.addWidget(widget)


# =============================================================================
# 按钮组件
# =============================================================================

class MacButton(QPushButton):
    """macOS 标准按钮"""

    def __init__(self, text: str, icon: Optional[QIcon] = None, parent=None):
        super().__init__(parent)
        self.setText(text)
        if icon:
            self.setIcon(icon)

        self.setProperty("class", "button")
        self.setCursor(Qt.PointingHandCursor)

        # 最小尺寸保证
        self.setMinimumHeight(28)
        self.setMinimumWidth(80)


class MacPrimaryButton(MacButton):
    """主要按钮 - 蓝色"""

    def __init__(self, text: str, icon: Optional[QIcon] = None, parent=None):
        super().__init__(text, icon, parent)
        self.setProperty("class", "button primary")


class MacSecondaryButton(MacButton):
    """次要按钮 - 边框样式"""

    def __init__(self, text: str, icon: Optional[QIcon] = None, parent=None):
        super().__init__(text, icon, parent)
        self.setProperty("class", "button secondary")


class MacDangerButton(MacButton):
    """危险按钮 - 红色"""

    def __init__(self, text: str, icon: Optional[QIcon] = None, parent=None):
        super().__init__(text, icon, parent)
        self.setProperty("class", "button danger")


class MacIconButton(QPushButton):
    """图标按钮"""

    def __init__(self, icon: str = "⚙️", size: int = 28, parent=None):
        super().__init__(icon, parent)
        self.setProperty("class", "button icon-only")
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)


class MacButtonGroup(QWidget):
    """按钮组 - 分段控制器"""

    clicked = pyqtSignal(int)  # 返回选中索引

    def __init__(self, labels: List[str], parent=None):
        super().__init__(parent)
        self.setProperty("class", "button-group")
        self.labels = labels
        self.buttons = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for i, label in enumerate(labels):
            btn = QPushButton(label)
            btn.setProperty("class", "button-group-item")
            if i == 0:
                btn.setProperty("class", "button-group-item active")

            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.clicked.connect(lambda checked, idx=i: self._on_clicked(idx))

            self.buttons.append(btn)
            layout.addWidget(btn)

        self.current_index = 0

    def _on_clicked(self, index: int):
        """处理点击"""
        # 更新所有按钮状态
        for i, btn in enumerate(self.buttons):
            if i == index:
                btn.setProperty("class", "button-group-item active")
                btn.setChecked(True)
            else:
                btn.setProperty("class", "button-group-item")
                btn.setChecked(False)

            # 刷新样式
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.current_index = index
        self.clicked.emit(index)

    def set_current_index(self, index: int):
        """设置当前选中项"""
        if 0 <= index < len(self.buttons):
            self._on_clicked(index)


# =============================================================================
# 标签和文本组件
# =============================================================================

class MacLabel(QLabel):
    """通用标签 - 需要指定样式类"""

    def __init__(self, text: str = "", class_name: str = "text-base", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", class_name)


class MacTitleLabel(MacLabel):
    """标题标签"""

    def __init__(self, text: str = "", size: int = 2, parent=None):
        class_map = {
            1: "title-5xl",
            2: "title-4xl",
            3: "title-3xl",
            4: "title-2xl",
            5: "title-xl",
            6: "title-lg"
        }
        super().__init__(text, class_map.get(size, "title-xl"), parent)


class MacBadge(QLabel):
    """状态徽章"""

    def __init__(self, text: str = "", style: str = "neutral", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", f"badge badge-{style}")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(20)
        self.setMinimumWidth(60)


class MacStatLabel(QWidget):
    """统计标签 - 左侧标签，右侧数值"""

    def __init__(self, label: str, value: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.label = QLabel(f"{label}:")
        self.label.setProperty("class", "text-secondary")
        self.label.setProperty("class", "text-bold")

        self.value = QLabel(value)
        self.value.setProperty("class", "text-base")

        layout.addWidget(self.label)
        layout.addWidget(self.value)
        layout.addStretch()


# =============================================================================
# 输入组件
# =============================================================================

class MacSearchBox(QWidget):
    """搜索框组件"""

    searchRequested = pyqtSignal(str)

    def __init__(self, placeholder: str = "搜索...", parent=None):
        super().__init__(parent)
        self.setProperty("class", "input-group")

        from PyQt6.QtWidgets import QLineEdit
        from PyQt6.QtGui import QKeySequence

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 输入框
        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setProperty("class", "input")
        self.input.setMinimumHeight(32)

        # 搜索按钮
        self.button = MacIconButton("🔍", 32)
        self.button.setProperty("class", "button button-icon input-group-button")

        # 连接信号
        self.button.clicked.connect(self._on_search)
        self.input.returnPressed.connect(self._on_search)

        layout.addWidget(self.input)
        layout.addWidget(self.button)

    def _on_search(self):
        """触发搜索"""
        query = self.input.text().strip()
        if query:
            self.searchRequested.emit(query)

    def clear(self):
        """清空搜索框"""
        self.input.clear()


# =============================================================================
# 滚动区域
# =============================================================================

class MacScrollArea(QScrollArea):
    """macOS 风格滚动区域"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "scroll-area")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)


# =============================================================================
# 网格布局容器
# =============================================================================

class MacGrid(QWidget):
    """网格容器"""

    def __init__(self, columns: int = 3, gap: int = 16, parent=None):
        super().__init__(parent)
        self.setProperty("class", "grid")
        self.columns = columns

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(gap)

        self.layout = layout
        self.current_row = 0
        self.current_col = 0

    def add_widget(self, widget, row: Optional[int] = None, col: Optional[int] = None):
        """添加组件到网格"""
        if row is None:
            row = self.current_row
        if col is None:
            col = self.current_col

        self.layout.addWidget(widget, row, col)

        # 更新位置
        self.current_col += 1
        if self.current_col >= self.columns:
            self.current_col = 0
            self.current_row += 1


# =============================================================================
# 页面工具栏
# =============================================================================

class MacPageToolbar(QWidget):
    """页面顶部工具栏"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "page-toolbar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        # 标题区域
        self.title_area = QWidget()
        self.title_area.setProperty("class", "page-title-area")
        title_layout = QHBoxLayout(self.title_area)
        title_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "page-title")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        # 操作区域
        self.action_area = QWidget()
        self.action_area.setProperty("class", "page-actions")
        self.action_layout = QHBoxLayout(self.action_area)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setSpacing(8)

        layout.addWidget(self.title_area)
        layout.addStretch()
        layout.addWidget(self.action_area)

    def add_action(self, widget):
        """添加操作按钮"""
        self.action_layout.addWidget(widget)

    def set_subtitle(self, text: str):
        """设置副标题"""
        subtitle = QLabel(text)
        subtitle.setProperty("class", "page-subtitle")
        self.title_area.layout().insertWidget(1, subtitle)

    def clear_actions(self):
        """清空所有操作"""
        while self.action_layout.count():
            item = self.action_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# =============================================================================
# 空状态组件
# =============================================================================

class MacEmptyState(QWidget):
    """空状态展示"""

    def __init__(self, icon: str = "📭", title: str = "暂无内容",
                 description: str = "还没有相关数据，开始创造吧！", parent=None):
        super().__init__(parent)
        self.setProperty("class", "empty-state")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        # 图标
        self.icon_label = QLabel(icon)
        self.icon_label.setProperty("class", "empty-icon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        # 标题
        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "empty-title")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # 描述
        if description:
            self.desc_label = QLabel(description)
            self.desc_label.setProperty("class", "empty-description")
            self.desc_label.setAlignment(Qt.AlignCenter)
            self.desc_label.setWordWrap(True)
            layout.addWidget(self.desc_label)

        layout.addStretch()


# =============================================================================
# 组件工厂函数
# =============================================================================

def create_icon_text_row(icon: str, text: str, class_name: str = "text-base") -> QWidget:
    """创建图标+文本行"""
    widget = QWidget()
    widget.setProperty("class", "icon-text-row")
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    icon_label = QLabel(icon)
    icon_label.setProperty("class", "text-xl")

    text_label = QLabel(text)
    text_label.setProperty("class", class_name)

    layout.addWidget(icon_label)
    layout.addWidget(text_label)
    layout.addStretch()

    return widget


def create_status_badge_row(items: List[tuple]) -> QWidget:
    """创建状态徽章行"""
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    for label, value, badge_type in items:
        # 标签
        label_widget = QLabel(f"{label}:")
        label_widget.setProperty("class", "text-secondary")
        layout.addWidget(label_widget)

        # 徽章
        if badge_type:
            badge = MacBadge(badge_type.upper(), badge_type)
            badge.setFixedSize(70, 20)
            layout.addWidget(badge)
        else:
            value_widget = QLabel(value)
            value_widget.setProperty("class", "text-base")
            layout.addWidget(value_widget)

    return widget


__all__ = [
    "MacCard", "MacElevatedCard", "MacSection",
    "MacButton", "MacPrimaryButton", "MacSecondaryButton", "MacDangerButton",
    "MacIconButton", "MacButtonGroup",
    "MacLabel", "MacTitleLabel", "MacBadge", "MacStatLabel",
    "MacSearchBox", "MacScrollArea", "MacGrid",
    "MacPageToolbar", "MacEmptyState",
    "create_icon_text_row", "create_status_badge_row"
]
