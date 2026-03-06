"""
动效工具类 - 提供各种动画效果
"""

from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QLinearGradient


class AnimationHelper:
    """动画辅助类"""
    
    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300, easing: QEasingCurve.Type = QEasingCurve.Type.InOutQuad):
        """淡入动画"""
        opacity = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity)
        
        animation = QPropertyAnimation(opacity, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(easing)
        animation.start()
        
        return animation
        
    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300, easing: QEasingCurve.Type = QEasingCurve.Type.InOutQuad, 
                 hide_on_complete: bool = True):
        """淡出动画"""
        opacity = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity)
        
        animation = QPropertyAnimation(opacity, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.setEasingCurve(easing)
        
        if hide_on_complete:
            animation.finished.connect(widget.hide)
            
        animation.start()
        return animation
    
    @staticmethod
    def slide_in(widget: QWidget, direction: str = "left", duration: int = 300):
        """滑入动画
        
        Args:
            widget: 目标控件
            direction: 方向 ("left", "right", "top", "bottom")
            duration: 动画时长(毫秒)
        """
        # 保存原始位置
        original_geometry = widget.geometry()
        
        # 设置起始位置
        if direction == "left":
            widget.move(original_geometry.x() - original_geometry.width(), original_geometry.y())
        elif direction == "right":
            widget.move(original_geometry.x() + original_geometry.width(), original_geometry.y())
        elif direction == "top":
            widget.move(original_geometry.x(), original_geometry.y() - original_geometry.height())
        elif direction == "bottom":
            widget.move(original_geometry.x(), original_geometry.y() + original_geometry.height())
            
        widget.show()
        
        # 创建位置动画
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setStartValue(widget.geometry())
        animation.setEndValue(original_geometry)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        
        return animation
    
    @staticmethod
    def scale_in(widget: QWidget, duration: int = 250):
        """缩放入场动画"""
        # 保存原始大小
        original_size = widget.size()
        
        # 从小到大
        widget.resize(0, 0)
        widget.show()
        
        animation = QPropertyAnimation(widget, b"size")
        animation.setDuration(duration)
        animation.setStartValue(widget.size())
        animation.setEndValue(original_size)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        animation.start()
        
        return animation
    
    @staticmethod
    def pulse(widget: QWidget, duration: int = 150):
        """脉冲动画 - 用于按钮点击反馈"""
        original_scale = widget.property("transform")
        
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(1)
        animation.setEndValue(0.8)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        
        # 返回动画
        reverse = QPropertyAnimation(widget, b"windowOpacity")
        reverse.setDuration(duration)
        reverse.setStartValue(0.8)
        reverse.setEndValue(1)
        reverse.setEasingCurve(QEasingCurve.Type.InOutQuad)
        reverse.setStartTime(duration)
        reverse.start()
        
        return animation


class PageTransition:
    """页面切换动画管理器"""
    
    def __init__(self, stacked_widget):
        self.stacked_widget = stacked_widget
        
    def switch_page(self, index: int, animation_type: str = "fade"):
        """切换页面并播放动画
        
        Args:
            index: 目标页面索引
            animation_type: 动画类型 ("fade", "slide", "scale")
        """
        if index < 0 or index >= self.stacked_widget.count():
            return
            
        current_widget = self.stacked_widget.currentWidget()
        target_widget = self.stacked_widget.widget(index)
        
        if animation_type == "fade":
            self._fade_transition(current_widget, target_widget)
        elif animation_type == "slide":
            self._slide_transition(current_widget, target_widget)
        elif animation_type == "scale":
            self._scale_transition(current_widget, target_widget)
        else:
            self.stacked_widget.setCurrentIndex(index)
            
    def _fade_transition(self, from_widget: QWidget, to_widget: QWidget):
        """淡入淡出切换"""
        # 淡出当前页面
        self.fade_out(from_widget, duration=200)
        
        # 切换到目标页面并淡入
        QTimer.singleShot(200, lambda: [
            self.stacked_widget.setCurrentWidget(to_widget),
            self.fade_in(to_widget, duration=200)
        ])
        
    def _slide_transition(self, from_widget: QWidget, to_widget: QWidget):
        """滑动切换"""
        # 获取宽度
        width = self.stacked_widget.width()
        
        # 淡出当前页面
        self.fade_out(from_widget, duration=150)
        
        # 切换并淡入目标页面
        QTimer.singleShot(150, lambda: [
            self.stacked_widget.setCurrentWidget(to_widget),
            self.fade_in(to_widget, duration=150)
        ])
        
    def _scale_transition(self, from_widget: QWidget, to_widget: QWidget):
        """缩放切换"""
        self.scale_out(from_widget, duration=150)
        
        QTimer.singleShot(150, lambda: [
            self.stacked_widget.setCurrentWidget(to_widget),
            self.scale_in(to_widget, duration=150)
        ])
        
    def fade_in(self, widget: QWidget, duration: int = 200):
        """淡入"""
        opacity = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity)
        
        animation = QPropertyAnimation(opacity, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        
    def fade_out(self, widget: QWidget, duration: int = 200):
        """淡出"""
        opacity = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity)
        
        animation = QPropertyAnimation(opacity, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        
    def scale_in(self, widget: QWidget, duration: int = 150):
        """缩放入场"""
        opacity = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity)
        
        # 透明度动画
        opacity_anim = QPropertyAnimation(opacity, b"opacity")
        opacity_anim.setDuration(duration)
        opacity_anim.setStartValue(0)
        opacity_anim.setEndValue(1)
        
        # 大小动画
        size_anim = QPropertyAnimation(widget, b"size")
        size_anim.setDuration(duration)
        size_anim.setStartValue(widget.width() * 0.9, widget.height() * 0.9)
        size_anim.setEndValue(widget.width(), widget.height())
        size_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        opacity_anim.start()
        size_anim.start()
        
    def scale_out(self, widget: QWidget, duration: int = 150):
        """缩放退场"""
        opacity = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity)
        
        # 透明度动画
        opacity_anim = QPropertyAnimation(opacity, b"opacity")
        opacity_anim.setDuration(duration)
        opacity_anim.setStartValue(1)
        opacity_anim.setEndValue(0)
        
        # 大小动画
        size_anim = QPropertyAnimation(widget, b"size")
        size_anim.setDuration(duration)
        size_anim.setStartValue(widget.width(), widget.height())
        size_anim.setEndValue(widget.width() * 0.9, widget.height() * 0.9)
        size_anim.setEasingCurve(QEasingCurve.Type.InBack)
        
        opacity_anim.start()
        size_anim.start()


class AnimatedButton:
    """带动画效果的按钮辅助类"""
    
    @staticmethod
    def add_ripple_effect(button, color: str = "rgba(255, 255, 255, 0.3)"):
        """为按钮添加波纹效果（需要自定义绘制）"""
        # 这是一个占位实现，实际波纹效果需要重写 paintEvent
        button.setCursor(Qt.CursorShape.PointingHand)
        
    @staticmethod
    def add_click_animation(button):
        """为按钮添加点击动画"""
        button.setCursor(Qt.CursorShape.PointingHand)
        button.clicked.connect(lambda: AnimatedButton._pulse_click(button))
        
    @staticmethod
    def _pulse_click(button):
        """点击脉冲动画"""
        original_style = button.styleSheet()
        
        # 临时改变样式模拟按下效果
        button.setStyleSheet(button.styleSheet() + "transform: scale(0.95);")
        
        # 恢复
        QTimer.singleShot(100, lambda: button.setStyleSheet(original_style))


class LoadingAnimation:
    """加载动画组件"""
    
    @staticmethod
    def create_loading_dots(parent, count: int = 3, color: str = "#6366F1"):
        """创建加载点动画"""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
        from PyQt6.QtCore import QTimer
        
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        
        dots = []
        for i in range(count):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 10px;")
            layout.addWidget(dot)
            dots.append(dot)
            
        # 动画定时器
        def animate():
            for j, d in enumerate(dots):
                delay = (i + j) % count
                opacity = 0.3 if delay != 0 else 1.0
                d.setStyleSheet(f"color: {color}; font-size: 10px; opacity: {opacity};")
                
        timer = QTimer(parent)
        timer.timeout.connect(animate)
        timer.start(200)
        
        return container, timer
