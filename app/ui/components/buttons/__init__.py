"""
按钮组件 - MacButton 系列
"""

from typing import Optional
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt


class MacButton(QPushButton):
    """macOS 风格按钮基类"""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setProperty("class", "button")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class MacPrimaryButton(MacButton):
    """主要按钮"""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setProperty("class", "primary")


class MacSecondaryButton(MacButton):
    """次要按钮"""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setProperty("class", "secondary")


class MacDangerButton(MacButton):
    """危险操作按钮"""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setProperty("class", "danger")


class MacIconButton(QPushButton):
    """图标按钮"""

    def __init__(self, icon: str = "", parent: Optional[QWidget] = None):
        super().__init__(icon, parent)
        self.setProperty("class", "icon-button")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class MacButtonGroup(QWidget):
    """按钮组"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

    def add_button(self, button: QPushButton):
        self.layout().addWidget(button)
