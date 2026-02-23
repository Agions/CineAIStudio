"""
AI建议组件
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont


class AISuggestion(QPushButton):
    """AI建议按钮"""

    def __init__(self, text: str, action: str):
        super().__init__()

        self.text = text
        self.action = action

        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setText(self.text)
        self.setToolTip(f"点击执行: {self.action}")

        # 设置字体
        font = QFont("Microsoft YaHei", 11)
        font.setWeight(QFont.Weight.Normal)
        self.setFont(font)

        # 设置大小策略
        self.setFixedSize(120, 35)

        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
                border-color: #2196F3;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #2196F3;
                border-color: #2196F3;
            }
        """)

    def get_action(self) -> str:
        """获取动作"""
        return self.action

    def set_action(self, action: str) -> None:
        """设置动作"""
        self.action = action

    def update_theme(self, is_dark: bool = True) -> None:
        """更新主题"""
        if is_dark:
            normal_bg = "#3D3D3D"
            hover_bg = "#4D4D4D"
            pressed_bg = "#2196F3"
            border_color = "#555555"
            text_color = "#FFFFFF"
        else:
            normal_bg = "#F5F5F5"
            hover_bg = "#E8E8E8"
            pressed_bg = "#2196F3"
            border_color = "#DDDDDD"
            text_color = "#000000"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {normal_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                border-color: #2196F3;
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
                border-color: {pressed_bg};
                color: #FFFFFF;
            }}
        """)