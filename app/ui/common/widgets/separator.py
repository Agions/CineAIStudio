"""
分隔线组件 - macOS 设计系统风格，使用 QSS 类名
"""

from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt


class Separator(QFrame):
    """分隔线组件 - macOS 风格"""

    def __init__(self, orientation=Qt.Orientation.Horizontal, style="default", thickness=1):
        super().__init__()

        self.orientation = orientation
        self.style = style
        self.thickness = thickness

        self._setup_separator()

    def _setup_separator(self) -> None:
        """设置分隔线 - 使用 QSS 类名，零内联样式"""
        # 设置基本属性
        self.setFrameShadow(QFrame.Shadow.Plain)

        # 设置样式类
        if self.orientation == Qt.Orientation.Horizontal:
            self.setFrameShape(QFrame.Shape.HLine)
            self.setFixedHeight(self.thickness)
            self.setProperty("class", f"separator-horizontal {self.style}")
        else:
            self.setFrameShape(QFrame.Shape.VLine)
            self.setFixedWidth(self.thickness)
            self.setProperty("class", f"separator-vertical {self.style}")

        # 启用样式支持
        self.setAttribute(Qt.WA_StyledBackground, True)

    def set_style(self, style: str) -> None:
        """设置样式类型"""
        if self.style != style:
            self.style = style
            if self.orientation == Qt.Orientation.Horizontal:
                self.setProperty("class", f"separator-horizontal {style}")
            else:
                self.setProperty("class", f"separator-vertical {style}")

            # 刷新样式
            self.style().unpolish(self)
            self.style().polish(self)

    def set_thickness(self, thickness: int) -> None:
        """设置粗细"""
        if self.thickness != thickness:
            self.thickness = thickness
            if self.orientation == Qt.Orientation.Horizontal:
                self.setFixedHeight(thickness)
            else:
                self.setFixedWidth(thickness)


class HSeparator(Separator):
    """水平分隔线（Separator的别名，方向固定为水平）"""

    def __init__(self, style="default", thickness=1):
        super().__init__(Qt.Orientation.Horizontal, style, thickness)


class VSeparator(Separator):
    """垂直分隔线（Separator的别名，方向固定为垂直）"""

    def __init__(self, style="default", thickness=1):
        super().__init__(Qt.Orientation.Vertical, style, thickness)