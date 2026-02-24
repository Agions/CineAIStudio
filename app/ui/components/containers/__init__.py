"""
容器组件 - Card, Section, ElevatedCard
"""

from typing import Optional
from PyQt6.QtWidgets import QFrame, QVBoxLayout
from PyQt6.QtCore import Qt


class MacCard(QFrame):
    """macOS 风格卡片容器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(20, 20, 20, 20)
        self.layout().setSpacing(12)

    def set_interactive(self, interactive: bool = True):
        if interactive:
            self.setProperty("class", "card card-interactive")
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setProperty("class", "card")
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self._refresh_style()

    def _refresh_style(self):
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
        self.title = title
        self._setup_ui()

    def _setup_ui(self):
        from PyQt6.QtWidgets import QVBoxLayout, QLabel
        from PyQt6.QtGui import QFont
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        if self.title:
            title_label = QLabel(self.title)
            title_label.setFont(QFont("", 14, QFont.Weight.Bold))
            layout.addWidget(title_label)
        
        self.content = QFrame()
        self.content.setProperty("class", "section-content")
        layout.addWidget(self.content)
