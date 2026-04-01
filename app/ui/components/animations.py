#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动画效果组件
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt, QRect, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QLinearGradient


class FadeInWidget(QWidget):
    """淡入动画组件"""
    
    def __init__(self, duration: int = 300, parent=None):
        super().__init__(parent)
        self._duration = duration
        self.setWindowOpacity(0)
        self._animation = None
        
    def fade_in(self):
        """开始淡入"""
        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(self._duration)
        self._animation.setStartValue(0)
        self._animation.setEndValue(1)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._animation.start()
        
    def fade_out(self, callback=None):
        """开始淡出"""
        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(self._duration)
        self._animation.setStartValue(1)
        self._animation.setEndValue(0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        if callback:
            self._animation.finished.connect(callback)
        self._animation.start()


class SlideWidget(QWidget):
    """滑动动画组件"""
    
    def __init__(self, direction: str = "left", duration: int = 300, parent=None):
        super().__init__(parent)
        self._direction = direction
        self._duration = duration
        self._animation = None
        
    def slide_in(self):
        """滑入"""
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(self._duration)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if self._direction == "left":
            start = QRect(-self.width(), self.y(), self.width(), self.height())
            end = QRect(0, self.y(), self.width(), self.height())
        elif self._direction == "right":
            start = QRect(self.parent().width(), self.y(), self.width(), self.height())
            end = QRect(0, self.y(), self.width(), self.height())
        elif self._direction == "top":
            start = QRect(self.x(), -self.height(), self.width(), self.height())
            end = QRect(self.x(), 0, self.width(), self.height())
        else:  # bottom
            start = QRect(self.x(), self.parent().height(), self.width(), self.height())
            end = QRect(self.x(), 0, self.width(), self.height())
            
        self._animation.setStartValue(start)
        self._animation.setEndValue(end)
        self._animation.start()


class PulseWidget(QWidget):
    """脉冲动画组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        
    def start_pulse(self):
        """开始脉冲"""
        self._timer.start(1500)
        
    def stop_pulse(self):
        """停止脉冲"""
        self._timer.stop()
        
    def _pulse(self):
        """脉冲动画"""
        # 简化的脉冲效果
        self.update()


class GlowLabel(QWidget):
    """发光标签"""
    
    def __init__(self, text: str = "", color: str = "#7C3AED", parent=None):
        super().__init__(parent)
        self._text = text
        self._color = QColor(color)
        self._glow_radius = 20
        
    def setText(self, text: str):
        self._text = text
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制发光效果
        glow_color = QColor(self._color)
        glow_color.setAlpha(50)
        painter.setBrush(glow_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # 绘制发光
        painter.drawEllipse(self.rect().adjusted(-self._glow_radius, -self._glow_radius, 
                                                  self._glow_radius, self._glow_radius))


class ShimmerEffect:
    """闪烁效果"""
    
    @staticmethod
    def get_stylesheet(color: str = "#7C3AED") -> str:
        """获取闪烁样式"""
        return f"""
            QFrame {{
                background: linear-gradient(90deg,
                    rgba(255, 255, 255, 0.02) 0%,
                    {color}22 50%,
                    rgba(255, 255, 255, 0.02) 100%);
                background-size: 200% 100%;
                animation: shimmer 2s ease-in-out infinite;
            }}
            
            @keyframes shimmer {{
                0% {{ background-position: 200% 0; }}
                100% {{ background-position: -200% 0; }}
            }}
        """


class ParallaxWidget(QWidget):
    """视差滚动组件"""
    
    def __init__(self, layers: list, parent=None):
        super().__init__(parent)
        self._layers = layers
        self._offset = 0
        
    def setOffset(self, offset: int):
        """设置偏移量"""
        self._offset = offset
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        # 简化的视差效果
        for i, layer in enumerate(self._layers):
            parallax_factor = (i + 1) * 0.1
            y_offset = self._offset * parallax_factor
            # 绘制图层...


class ParticleWidget(QWidget):
    """粒子效果组件 (简化版)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._particles = []
        
    def add_particle(self, x: int, y: int, color: str = "#7C3AED"):
        """添加粒子"""
        self._particles.append({
            "x": x, "y": y,
            "color": QColor(color),
            "life": 100,
            "vx": (x - 100) / 50.0,
            "vy": -2
        })
        
    def update_particles(self):
        """更新粒子"""
        for p in self._particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 2
            
            if p["life"] <= 0:
                self._particles.remove(p)
                
        self.update()


class AnimatedCounter(QWidget):
    """数字滚动动画"""
    
    finished = Signal()
    valueChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._target = 0
        self._animation = None
        
    def setValue(self, value: int, duration: int = 1000):
        """设置目标值"""
        self._target = value
        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(duration)
        self._animation.setStartValue(self._value)
        self._animation.setEndValue(value)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.valueChanged.connect(lambda v: self._on_value_changed(v))
        self._animation.finished.connect(self.finished.emit)
        self._animation.start()
        
    def _on_value_changed(self, value: float):
        """值变化回调"""
        self._value = value
        self.valueChanged.emit(int(value))
        self.update()
        
    def value(self) -> int:
        return int(self._value)


class TransitionStack(QWidget):
    """过渡栈组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._widgets = []
        self._current = None
        
    def push(self, widget: QWidget):
        """推入组件"""
        if self._current:
            self._current.hide()
        self._widgets.append(widget)
        self._current = widget
        self._current.show()
        
    def pop(self):
        """弹出组件"""
        if self._widgets:
            old = self._widgets.pop()
            old.hide()
            if self._widgets:
                self._current = self._widgets[-1]
                self._current.show()
                
    def current(self) -> QWidget:
        """获取当前组件"""
        return self._current
