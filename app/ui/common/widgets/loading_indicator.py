"""
加载指示器组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont


class LoadingIndicator(QWidget):
    """加载指示器"""

    def __init__(self, message: str = "加载中..."):
        super().__init__()

        self.message = message
        self.is_animating = False

        self._setup_ui()
        self._create_layout()
        self._start_animation()

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setObjectName("loading_indicator")
        self.setFixedSize(200, 60)

        # 设置样式
        self.setStyleSheet("""
            QWidget#loading_indicator {
                background-color: rgba(0, 0, 0, 0.8);
                border-radius: 8px;
            }
        """)

    def _create_layout(self) -> None:
        """创建布局"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(10)

        # 加载动画标签
        self.animation_label = QLabel("⏳")
        self.animation_label.setStyleSheet("font-size: 20px;")
        self.animation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.animation_label)

        # 消息标签
        self.message_label = QLabel(self.message)
        self.message_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
            }
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(self.message_label)

        main_layout.addStretch()

    def _start_animation(self) -> None:
        """开始动画"""
        self.is_animating = True
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(500)  # 每500ms更新一次

    def _update_animation(self) -> None:
        """更新动画"""
        if not self.is_animating:
            return

        # 简单的旋转动画
        frames = ["⏳", "⌛", "⏳", "⌛"]
        current_frame = int((QTimer.currentTime().msecsSinceStartOfDay() / 500) % len(frames))
        self.animation_label.setText(frames[current_frame])

    def set_message(self, message: str) -> None:
        """设置消息"""
        self.message = message
        if self.message_label:
            self.message_label.setText(message)

    def stop_animation(self) -> None:
        """停止动画"""
        self.is_animating = False
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()

    def start_animation(self) -> None:
        """开始动画"""
        if not self.is_animating:
            self.is_animating = True
            if hasattr(self, 'animation_timer'):
                self.animation_timer.start(500)

    def update_theme(self, is_dark: bool = True) -> None:
        """更新主题"""
        if is_dark:
            bg_color = "rgba(0, 0, 0, 0.8)"
            text_color = "#FFFFFF"
        else:
            bg_color = "rgba(255, 255, 255, 0.9)"
            text_color = "#000000"

        self.setStyleSheet(f"""
            QWidget#loading_indicator {{
                background-color: {bg_color};
                border-radius: 8px;
            }}
            QLabel {{
                color: {text_color};
            }}
        """)

    def closeEvent(self, event) -> None:
        """关闭事件"""
        self.stop_animation()
        super().closeEvent(event)