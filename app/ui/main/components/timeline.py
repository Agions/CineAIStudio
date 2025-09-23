"""
时间线组件（占位符）
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class Timeline(QWidget):
    """时间线组件"""

    def __init__(self, application):
        super().__init__()
        self.application = application

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("⏱️ 时间线编辑区域")
        label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
                background-color: #2D2D2D;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 20px;
            }
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def set_playback_position(self, position_ms: int):
        """设置播放位置"""
        pass

    def cleanup(self):
        """清理资源"""
        pass

    def update_theme(self, is_dark: bool = True):
        """更新主题"""
        pass