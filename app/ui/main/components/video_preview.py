"""
视频预览组件（占位符）
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal, Qt


class VideoPreview(QWidget):
    """视频预览组件"""

    # 信号定义
    playback_position_changed = pyqtSignal(int)

    def __init__(self, application):
        super().__init__()
        self.application = application
        self.current_video = None

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("🎬 视频预览区域")
        label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 18px;
                background-color: #2D2D2D;
                border: 2px dashed #555555;
                border-radius: 8px;
                padding: 40px;
            }
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def load_video(self, video_path: str):
        """加载视频"""
        self.current_video = video_path
        # TODO: 实现视频加载逻辑

    def cleanup(self):
        """清理资源"""
        pass

    def update_theme(self, is_dark: bool = True):
        """更新主题"""
        pass