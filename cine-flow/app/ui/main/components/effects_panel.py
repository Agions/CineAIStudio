"""
特效面板组件（占位符）
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget


class EffectsPanel(QWidget):
    """特效面板组件"""

    def __init__(self, application):
        super().__init__()
        self.application = application

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title = QLabel("✨ 特效库")
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

        # 特效列表
        effects_list = QListWidget()
        effects_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: none;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
            }
        """)
        layout.addWidget(effects_list)

        # 添加特效
        effects = [
            "🎨 色彩调整",
            "🌟 模糊效果",
            "⚡ 速度控制",
            "🔄 旋转效果",
            "💫 粒子效果",
            "🎭 滤镜效果"
        ]

        for effect in effects:
            effects_list.addItem(effect)

    def cleanup(self):
        """清理资源"""
        pass

    def update_theme(self, is_dark: bool = True):
        """更新主题"""
        pass