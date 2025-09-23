"""
媒体库组件（占位符）
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt6.QtCore import pyqtSignal


class MediaLibrary(QWidget):
    """媒体库组件"""

    # 信号定义
    video_selected = pyqtSignal(str)
    project_opened = pyqtSignal(str)

    def __init__(self, application):
        super().__init__()
        self.application = application

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title = QLabel("📁 媒体库")
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: #2D2D2D;
                border-bottom: 1px solid #555555;
            }
        """)
        layout.addWidget(title)

        # 媒体列表
        self.media_list = QListWidget()
        self.media_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #2D2D2D;
            }
        """)
        layout.addWidget(self.media_list)

        # 添加一些示例项
        items = [
            "🎥 示例视频1.mp4",
            "🎵 示例音频1.mp3",
            "🖼️ 示例图片1.png",
            "🎥 示例视频2.mp4"
        ]

        for item_text in items:
            item = QListWidgetItem(item_text)
            self.media_list.addItem(item)

        # 连接信号
        self.media_list.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _on_item_double_clicked(self, item):
        """双击项处理"""
        text = item.text()
        if "视频" in text:
            # 模拟视频选择
            video_path = f"/path/to/{text.replace('示例', '')}"
            self.video_selected.emit(video_path)

    def add_media_files(self, file_paths):
        """添加媒体文件"""
        for file_path in file_paths:
            import os
            filename = os.path.basename(file_path)
            item = QListWidgetItem(f"📄 {filename}")
            self.media_list.addItem(item)

    def cleanup(self):
        """清理资源"""
        pass

    def update_theme(self, is_dark: bool = True):
        """更新主题"""
        pass