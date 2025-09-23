"""
分隔线组件
"""

from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt


class Separator(QFrame):
    """分隔线组件"""

    def __init__(self, orientation=Qt.Orientation.Horizontal, color="#404040", thickness=1):
        super().__init__()

        self.orientation = orientation
        self.color = color
        self.thickness = thickness

        self._setup_separator()

    def _setup_separator(self) -> None:
        """设置分隔线"""
        if self.orientation == Qt.Orientation.Horizontal:
            self.setFrameShape(QFrame.Shape.HLine)
            self.setFixedHeight(self.thickness)
        else:
            self.setFrameShape(QFrame.Shape.VLine)
            self.setFixedWidth(self.thickness)

        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color};
            }}
        """)

    def set_color(self, color: str) -> None:
        """设置颜色"""
        self.color = color
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color};
            }}
        """)

    def set_thickness(self, thickness: int) -> None:
        """设置粗细"""
        self.thickness = thickness
        if self.orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(thickness)
        else:
            self.setFixedWidth(thickness)