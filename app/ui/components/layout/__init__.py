"""
布局组件 - Grid, PageToolbar, EmptyState, ScrollArea
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QFrame, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal


class MacScrollArea(QScrollArea):
    """滚动区域"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("class", "scroll-area")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)


class MacGrid(QWidget):
    """网格布局"""

    def __init__(self, columns: int = 3, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.columns = columns
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QGridLayout(self)
        self.layout.setSpacing(16)
        self.items: List[QWidget] = []

    def add_widget(self, widget: QWidget, row: int = -1, col: int = -1):
        self.items.append(widget)
        if row == -1:
            row = (len(self.items) - 1) // self.columns
        if col == -1:
            col = (len(self.items) - 1) % self.columns
        self.layout.addWidget(widget, row, col)


class MacPageToolbar(QWidget):
    """页面工具栏"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.left_layout = QHBoxLayout()
        self.left_layout.setSpacing(8)

        self.right_layout = QHBoxLayout()
        self.right_layout.setSpacing(8)

        layout.addLayout(self.left_layout)
        layout.addStretch()
        layout.addLayout(self.right_layout)

    def add_left_action(self, widget: QWidget):
        self.left_layout.addWidget(widget)

    def add_right_action(self, widget: QWidget):
        self.right_layout.addWidget(widget)


class MacEmptyState(QWidget):
    """空状态"""

    def __init__(self, icon: str = "📭", title: str = "暂无内容", 
                 description: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui(icon, title, description)

    def _setup_ui(self, icon: str, title: str, description: str):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self.icon = QLabel(icon)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon.setStyleSheet("font-size: 48px;")

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")

        layout.addWidget(self.icon)
        layout.addWidget(self.title)

        if description:
            self.description = QLabel(description)
            self.description.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.description.setStyleSheet("font-size: 14px; color: #CCCCCC;")
            layout.addWidget(self.description)
