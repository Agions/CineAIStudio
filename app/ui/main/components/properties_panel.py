"""
属性面板组件（占位符）
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class PropertiesPanel(QWidget):
    """属性面板组件"""

    def __init__(self, application):
        super().__init__()
        self.application = application

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title = QLabel("⚙️ 属性面板")
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

        # 属性内容
        content = QLabel("""
        <div style="color: #CCCCCC; font-size: 12px; padding: 10px;">
        <b>选中对象属性</b><br><br>
        • 位置: X=0, Y=0<br>
        • 大小: 1920x1080<br>
        • 持续时间: 00:00:00<br>
        • 透明度: 100%<br><br>
        <b>视频属性</b><br><br>
        • 分辨率: 1920x1080<br>
        • 帧率: 30 FPS<br>
        • 编码: H.264<br>
        • 比特率: 8000 kbps
        </div>
        """)
        content.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                border: none;
                padding: 10px;
            }
        """)
        content.setWordWrap(True)
        layout.addWidget(content)

        layout.addStretch()

    def cleanup(self):
        """清理资源"""
        pass

    def update_theme(self, is_dark: bool = True):
        """更新主题"""
        pass