"""
加载组件

提供各种加载状态和进度指示组件。
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QGraphicsOpacityEffect, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QFont


class LoadingSpinner(QWidget):
    """
    加载旋转器
    
    显示旋转动画表示加载中。
    """
    
    def __init__(self, size: int = 40, parent: Optional[QWidget] = None):
        """
        初始化旋转器
        
        Args:
            size: 大小（像素）
            parent: 父组件
        """
        super().__init__(parent)
        self._size = size
        self._angle = 0
        self._color = QColor("#2962FF")
        
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # 创建动画定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(30)  # 30ms更新一次
    
    def _rotate(self):
        """旋转动画"""
        self._angle = (self._angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算中心点和半径
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - 4
        
        # 绘制旋转弧
        pen = QPen(self._color)
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        painter.drawArc(
            int(center_x - radius), int(center_y - radius),
            int(radius * 2), int(radius * 2),
            int(self._angle * 16), int(120 * 16)
        )
    
    def set_color(self, color: QColor):
        """设置颜色"""
        self._color = color
        self.update()
    
    def start(self):
        """开始动画"""
        if not self._timer.isActive():
            self._timer.start()
    
    def stop(self):
        """停止动画"""
        if self._timer.isActive():
            self._timer.stop()


class CircularProgress(QWidget):
    """
    圆形进度条
    
    显示圆形进度指示器。
    """
    
    def __init__(self, size: int = 60, parent: Optional[QWidget] = None):
        """
        初始化
        
        Args:
            size: 大小
            parent: 父组件
        """
        super().__init__(parent)
        self._size = size
        self._progress = 0.0
        self._primary_color = QColor("#2962FF")
        self._secondary_color = QColor("#333333")
        self._line_width = 4
        
        self.setFixedSize(size, size)
    
    def set_progress(self, progress: float):
        """
        设置进度
        
        Args:
            progress: 进度值 (0.0 - 1.0)
        """
        self._progress = max(0.0, min(1.0, progress))
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - self._line_width
        
        # 绘制背景圆
        pen = QPen(self._secondary_color)
        pen.setWidth(self._line_width)
        painter.setPen(pen)
        painter.drawEllipse(
            int(center_x - radius), int(center_y - radius),
            int(radius * 2), int(radius * 2)
        )
        
        # 绘制进度弧
        pen = QPen(self._primary_color)
        pen.setWidth(self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        span_angle = int(-self._progress * 360 * 16)
        painter.drawArc(
            int(center_x - radius), int(center_y - radius),
            int(radius * 2), int(radius * 2),
            90 * 16, span_angle
        )
        
        # 绘制百分比文字
        if self._progress > 0:
            painter.setPen(QColor("#FFFFFF"))
            font = QFont()
            font.setPointSize(int(self._size / 5))
            font.setBold(True)
            painter.setFont(font)
            
            text = f"{int(self._progress * 100)}%"
            text_rect = painter.boundingRect(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)


class LinearProgress(QWidget):
    """
    线性进度条
    
    现代化的线性进度指示器。
    """
    
    progress_changed = pyqtSignal(float)
    
    def __init__(self, height: int = 4, parent: Optional[QWidget] = None):
        """
        初始化
        
        Args:
            height: 进度条高度
            parent: 父组件
        """
        super().__init__(parent)
        self._height = height
        self._progress = 0.0
        self._primary_color = QColor("#2962FF")
        self._secondary_color = QColor("#2C2C2C")
        self._animated = False
        
        self.setFixedHeight(height + 4)
        self.setMinimumWidth(100)
    
    def set_progress(self, progress: float):
        """
        设置进度
        
        Args:
            progress: 进度值 (0.0 - 1.0)
        """
        self._progress = max(0.0, min(1.0, progress))
        self.progress_changed.emit(self._progress)
        self.update()
    
    def set_animated(self, animated: bool):
        """
        设置是否显示动画
        
        Args:
            animated: 是否动画
        """
        self._animated = animated
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        
        # 绘制背景
        painter.setBrush(self._secondary_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, self._height / 2, self._height / 2)
        
        # 绘制进度
        if self._progress > 0:
            progress_width = rect.width() * self._progress
            progress_rect = rect.adjusted(0, 0, -(rect.width() - progress_width), 0)
            
            painter.setBrush(self._primary_color)
            painter.drawRoundedRect(progress_rect, self._height / 2, self._height / 2)


class ProgressIndicator(QWidget):
    """
    进度指示器
    
    显示带文字说明的进度。
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化"""
        super().__init__(parent)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 标签
        self._label = QLabel("准备中...")
        self._label.setStyleSheet("color: #B0B0B0; font-size: 13px;")
        layout.addWidget(self._label)
        
        # 进度条
        self._progress_bar = LinearProgress(height=6)
        layout.addWidget(self._progress_bar)
        
        # 详情标签
        self._detail_label = QLabel("")
        self._detail_label.setStyleSheet("color: #808080; font-size: 11px;")
        layout.addWidget(self._detail_label)
    
    def set_progress(self, progress: float, message: Optional[str] = None):
        """
        设置进度
        
        Args:
            progress: 进度值
            message: 进度消息
        """
        self._progress_bar.set_progress(progress)
        
        if message:
            self._label.setText(message)
    
    def set_detail(self, detail: str):
        """
        设置详情
        
        Args:
            detail: 详情文字
        """
        self._detail_label.setText(detail)
    
    def set_stage(self, stage: str, progress: float):
        """
        设置阶段
        
        Args:
            stage: 阶段名称
            progress: 进度
        """
        self.set_progress(progress, stage)


class LoadingOverlay(QWidget):
    """
    加载遮罩
    
    覆盖在内容上方显示加载状态。
    """
    
    def __init__(self, parent: QWidget, message: str = "加载中..."):
        """
        初始化
        
        Args:
            parent: 父组件
            message: 加载消息
        """
        super().__init__(parent)
        
        self._message = message
        self._setup_ui()
        self._setup_animation()
        
        # 设置透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
    
    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet("""
            LoadingOverlay {
                background-color: rgba(18, 18, 18, 0.85);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # 旋转器
        self._spinner = LoadingSpinner(size=48)
        layout.addWidget(self._spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 消息
        self._label = QLabel(self._message)
        self._label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 14px;
            font-weight: 500;
        """)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)
    
    def _setup_animation(self):
        """设置动画"""
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self._opacity_effect)
        
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(200)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        self._fade_animation.setStartValue(0)
        self._fade_animation.setEndValue(1)
        self._fade_animation.start()
        self._spinner.start()
    
    def hideEvent(self, event):
        """隐藏事件"""
        super().hideEvent(event)
        self._spinner.stop()
    
    def set_message(self, message: str):
        """
        设置消息
        
        Args:
            message: 消息文字
        """
        self._message = message
        self._label.setText(message)
    
    def resizeEvent(self, event):
        """调整大小事件"""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())


class SkeletonScreen(QWidget):
    """
    骨架屏
    
    显示内容加载前的占位骨架。
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化"""
        super().__init__(parent)
        
        self._shimmer_color = QColor("#333333")
        self._shimmer_highlight = QColor("#444444")
        self._shimmer_offset = 0
        
        # 动画定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_shimmer)
        self._timer.start(50)
    
    def _update_shimmer(self):
        """更新闪光效果"""
        self._shimmer_offset = (self._shimmer_offset + 2) % 100
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制骨架元素
        # 这里可以根据需要绘制不同的骨架形状
        # 简化实现：绘制几个矩形
        
        painter.setBrush(self._shimmer_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # 标题骨架
        painter.drawRoundedRect(16, 16, 200, 24, 4, 4)
        
        # 内容骨架
        for i in range(5):
            y = 60 + i * 40
            painter.drawRoundedRect(16, y, self.width() - 32, 20, 4, 4)
    
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start()
    
    def hideEvent(self, event):
        """隐藏事件"""
        super().hideEvent(event)
        if self._timer.isActive():
            self._timer.stop()


class LoadingManager:
    """
    加载管理器
    
    管理全局加载状态。
    """
    
    _instance: Optional['LoadingManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._overlays: dict = {}
            self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'LoadingManager':
        """获取实例"""
        return cls()
    
    def show_loading(self, widget: QWidget, message: str = "加载中...") -> LoadingOverlay:
        """
        显示加载遮罩
        
        Args:
            widget: 目标组件
            message: 消息
            
        Returns:
            加载遮罩
        """
        overlay = LoadingOverlay(widget, message)
        overlay.show()
        self._overlays[id(widget)] = overlay
        return overlay
    
    def hide_loading(self, widget: QWidget):
        """
        隐藏加载遮罩
        
        Args:
            widget: 目标组件
        """
        overlay_id = id(widget)
        if overlay_id in self._overlays:
            self._overlays[overlay_id].hide()
            self._overlays[overlay_id].deleteLater()
            del self._overlays[overlay_id]
    
    def update_message(self, widget: QWidget, message: str):
        """
        更新加载消息
        
        Args:
            widget: 目标组件
            message: 新消息
        """
        overlay_id = id(widget)
        if overlay_id in self._overlays:
            self._overlays[overlay_id].set_message(message)
