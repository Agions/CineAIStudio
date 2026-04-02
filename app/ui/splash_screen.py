"""
VideoForge 启动画面 - 品牌升级版
渐变 Logo 动画 + 加载动画 + 版本显示
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QFont, QColor, QLinearGradient

# 色彩系统 - VideoForge 现代暗色主题
COLORS = {
    "primary": "#6366F1",
    "primary_end": "#8B5CF6",
    "primary_light": "#818CF8",
    "accent": "#06B6D4",
    "background": "#0A0A0F",
    "surface": "#12121A",
    "text": "#E6EDF3",
    "text_secondary": "#C9D1D9",
    "text_tertiary": "#8B949E",
}


class GradientLogoLabel(QWidget):
    """渐变 Logo 标签 - 带呼吸动画"""
    
    def __init__(self, size: int = 120, parent=None):
        super().__init__(parent)
        self.logo_size = size
        self._animation_value = 0
        self.setFixedSize(size, size)
        
        # 动画定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(50)  # 50ms 更新一次
        
    def _update_animation(self):
        self._animation_value = (self._animation_value + 2) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = self.rect().center()
        radius = self.logo_size // 2 - 10
        
        # 创建渐变
        gradient = QLinearGradient(
            center.x() - radius, center.y() - radius,
            center.x() + radius, center.y() + radius
        )
        
        # 呼吸效果
        pulse = (self._animation_value % 60) / 60.0
        alpha1 = 180 + int(75 * pulse)
        alpha2 = 255 - int(75 * pulse)
        
        gradient.setColorAt(0, QColor(COLORS["primary"]).withAlpha(alpha1))
        gradient.setColorAt(0.5, QColor(COLORS["primary_end"]).withAlpha(220))
        gradient.setColorAt(1, QColor(COLORS["accent"]).withAlpha(alpha2))
        
        # 绘制圆形背景
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(center, radius, radius)
        
        # 绘制内圈
        inner_gradient = QLinearGradient(
            center.x() - radius + 10, center.y() - radius + 10,
            center.x() + radius - 10, center.y() + radius - 10
        )
        inner_gradient.setColorAt(0, QColor("#FFFFFF").withAlpha(40))
        inner_gradient.setColorAt(1, QColor("#FFFFFF").withAlpha(10))
        
        painter.setBrush(inner_gradient)
        painter.drawEllipse(center, radius - 8, radius - 8)
        
        # 绘制 Logo 文字 "CF"
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Arial", int(radius * 0.5), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "CF"
        )


class LoadingIndicator(QWidget):
    """加载动画指示器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self.setFixedSize(40, 40)
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(30)
        
    def _rotate(self):
        self._angle = (self._angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = self.rect().center()
        radius = 16
        
        # 绘制背景圆环
        painter.setPen(QColor(COLORS["surface"]))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)
        
        # 绘制渐变进度弧
        pen = painter.pen()
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        gradient = QLinearGradient(
            center.x() - radius, center.y() - radius,
            center.x() + radius, center.y() + radius
        )
        gradient.setColorAt(0, QColor(COLORS["primary"]))
        gradient.setColorAt(1, QColor(COLORS["accent"]))
        
        pen.setBrush(gradient)
        painter.setPen(pen)
        
        # 绘制弧形
        rect = self.rect().adjusted(4, 4, -4, -4)
        painter.drawArc(rect, self._angle * 16, 270 * 16)


class PulsingDot(QWidget):
    """脉冲圆点 - 用于加载状态"""
    
    def __init__(self, color: str = COLORS["primary"], parent=None):
        super().__init__(parent)
        self._color = color
        self._scale = 0
        self._direction = 1
        self.setFixedSize(12, 12)
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._timer.start(50)
        
    def _pulse(self):
        self._scale += 0.1 * self._direction
        if self._scale >= 1.0:
            self._scale = 1.0
            self._direction = -1
        elif self._scale <= 0.3:
            self._scale = 0.3
            self._direction = 1
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = self.rect().center()
        radius = 4 * self._scale
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._color))
        painter.drawEllipse(center, int(radius), int(radius))


class SplashScreenWidget(QWidget):
    """启动画面组件 - 品牌升级版"""
    
    # 加载完成信号
    loading_finished = Signal()
    
    def __init__(self, app_name: str = "VideoForge", version: str = "v2.0.0", parent=None):
        super().__init__(parent)
        self._app_name = app_name
        self._version = version
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        self.setFixedSize(500, 400)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 主容器
        container = QWidget(self)
        container.setFixedSize(500, 400)
        container.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS["background"]},
                    stop:0.5 {COLORS["surface"]},
                    stop:1 {COLORS["background"]});
                border-radius: 20px;
            }}
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setSpacing(30)
        
        # Logo 区域
        self.logo_label = GradientLogoLabel(140)
        container_layout.addWidget(self.logo_label)
        
        # 应用名称
        name_label = QLabel(self._app_name)
        name_font = QFont()
        name_font.setPointSize(28)
        name_font.setWeight(QFont.Weight.Bold)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {COLORS['text']};")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(name_label)
        
        # 副标题
        subtitle_label = QLabel("智能视频创作平台")
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(subtitle_label)
        
        # 版本信息
        version_label = QLabel(self._version)
        version_font = QFont()
        version_font.setPointSize(11)
        version_label.setFont(version_font)
        version_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(version_label)
        
        # 加载指示器
        loading_container = QWidget()
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(8)
        
        self.loading_indicator = LoadingIndicator()
        loading_layout.addWidget(self.loading_indicator)
        
        self.loading_text = QLabel("正在初始化...")
        loading_font = QFont()
        loading_font.setPointSize(12)
        self.loading_text.setFont(loading_font)
        self.loading_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.loading_text)
        
        container_layout.addWidget(loading_container)
        
        layout.addWidget(container)
        
    def set_loading_text(self, text: str):
        """设置加载文本"""
        if hasattr(self, 'loading_text'):
            self.loading_text.setText(text)
            
    def finish_loading(self):
        """完成加载"""
        self.loading_finished.emit()


class AnimatedSplashScreen(QWidget):
    """动画启动画面 - 品牌升级完整版"""
    
    finished = Signal()
    
    def __init__(self, app_name: str = "VideoForge", version: str = "v2.0.0", parent=None):
        super().__init__(parent)
        self._app_name = app_name
        self._version = version
        self._setup_ui()
        self._start_animations()
        
    def _setup_ui(self):
        """设置UI"""
        self.setFixedSize(600, 450)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 主容器 - 带边框和阴影效果
        self.container = QWidget(self)
        self.container.setFixedSize(600, 450)
        
        # 使用setStyleSheet创建渐变背景
        self.container.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0A0A0F,
                    stop:0.3 #12121A,
                    stop:0.7 #12121A,
                    stop:1 #0A0A0F);
                border: 1px solid #30363D;
                border-radius: 24px;
            }}
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(40, 50, 40, 50)
        container_layout.setSpacing(24)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo 区域 - 居中
        self.logo_container = QWidget()
        self.logo_container.setFixedSize(160, 160)
        logo_layout = QVBoxLayout(self.logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logo = GradientLogoLabel(140)
        logo_layout.addWidget(self.logo)
        
        container_layout.addWidget(self.logo_container)
        
        # 应用名称 - 渐变文字效果
        self.name_label = QLabel(self._app_name)
        name_font = QFont()
        name_font.setFamily("Microsoft YaHei, PingFang SC, Arial")
        name_font.setPointSize(32)
        name_font.setWeight(QFont.Weight.Bold)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet(f"""
            color: {COLORS['text']};
            background: transparent;
        """)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.name_label)
        
        # 副标题
        self.subtitle_label = QLabel("智能视频创作平台 · AI Powered")
        subtitle_font = QFont()
        subtitle_font.setFamily("Microsoft YaHei, PingFang SC, Arial")
        subtitle_font.setPointSize(13)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.subtitle_label)
        
        # 版本信息
        self.version_label = QLabel(self._version)
        version_font = QFont()
        version_font.setPointSize(11)
        self.version_label.setFont(version_font)
        self.version_label.setStyleSheet(f"""
            color: {COLORS['text_tertiary']};
            padding: 6px 16px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
        """)
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.version_label)
        
        # 加载指示器区域
        self.loading_container = QWidget()
        self.loading_container.setFixedHeight(80)
        loading_layout = QVBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(12)
        
        # 加载动画
        self.loading_indicator = LoadingIndicator()
        loading_layout.addWidget(self.loading_indicator)
        
        # 加载文字和三个点
        self.loading_text_container = QWidget()
        loading_text_layout = QHBoxLayout(self.loading_text_container)
        loading_text_layout.setContentsMargins(0, 0, 0, 0)
        loading_text_layout.setSpacing(0)
        loading_text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.loading_text = QLabel("正在初始化")
        loading_font = QFont()
        loading_font.setPointSize(13)
        self.loading_text.setFont(loading_font)
        self.loading_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        loading_text_layout.addWidget(self.loading_text)
        
        # 脉冲点动画
        self.dots_container = QWidget()
        dots_layout = QHBoxLayout(self.dots_container)
        dots_layout.setContentsMargins(4, 0, 0, 0)
        dots_layout.setSpacing(4)
        
        self.dot1 = PulsingDot(COLORS["primary"])
        self.dot2 = PulsingDot(COLORS["primary_end"])
        self.dot3 = PulsingDot(COLORS["accent"])
        
        dots_layout.addWidget(self.dot1)
        dots_layout.addWidget(self.dot2)
        dots_layout.addWidget(self.dot3)
        
        loading_text_layout.addWidget(self.dots_container)
        
        loading_layout.addWidget(self.loading_text_container)
        
        container_layout.addWidget(self.loading_container)
        
    def _start_animations(self):
        """启动动画"""
        # Logo 淡入
        self.logo_container.setWindowOpacity(0)
        self.fade_in(self.logo_container, 300)
        
    def fade_in(self, widget, duration: int = 500):
        """淡入动画"""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        
    def set_loading_message(self, message: str):
        """设置加载消息"""
        if hasattr(self, 'loading_text'):
            self.loading_text.setText(message)
            
    def complete(self):
        """完成启动"""
        self.fade_out(300)
        QTimer.singleShot(350, self.finished)
        
    def fade_out(self, duration: int = 300):
        """淡出动画"""
        animation = QPropertyAnimation(self, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
