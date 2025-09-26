#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Interactions Components
增强交互体验组件，提供流畅的用户界面交互
"""

import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QFrame, QStackedWidget, QProgressBar,
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QApplication,
    QGraphicsOpacityEffect, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QThread, pyqtProperty, QParallelAnimationGroup,
    QSequentialAnimationGroup, QPoint, QRect, QSize, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QIcon


@dataclass
class AnimationConfig:
    """动画配置"""
    duration: int = 300
    easing_curve: QEasingCurve.Type = QEasingCurve.Type.OutCubic
    opacity: bool = True
    scale: bool = False
    position: bool = False


class EnhancedButton(QPushButton):
    """增强按钮，提供丰富的交互反馈"""

    clicked_with_animation = pyqtSignal()

    def __init__(self, text: str = "", parent: Optional[QWidget] = None,
                 config: Optional[AnimationConfig] = None):
        super().__init__(text, parent)
        self.config = config or AnimationConfig()
        self._scale = 1.0
        self._is_active = False
        self._setup_enhanced_styles()
        self._setup_animations()
        self._setup_connections()

    def _setup_enhanced_styles(self):
        """设置增强样式"""
        self.setStyleSheet("""
            EnhancedButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
                min-height: 40px;
            }
            EnhancedButton:hover {
                background-color: #1976D2;
                border: 2px solid #64B5F6;
            }
            EnhancedButton:pressed {
                background-color: #0D47A1;
                padding: 12px 18px 8px 22px;
            }
            EnhancedButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)

        # 设置光标
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _setup_animations(self):
        """设置动画效果"""
        self._opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self._opacity_effect)

        # 悬停动画
        self._hover_animation = QPropertyAnimation(self, b"scale")
        self._hover_animation.setDuration(self.config.duration)
        self._hover_animation.setStartValue(1.0)
        self._hover_animation.setEndValue(1.05)
        self._hover_animation.setEasingCurve(self.config.easing_curve)

        # 点击动画
        self._click_animation = QPropertyAnimation(self, b"scale")
        self._click_animation.setDuration(self.config.duration // 2)
        self._click_animation.setStartValue(1.0)
        self._click_animation.setEndValue(0.95)
        self._click_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def _setup_connections(self):
        """设置信号连接"""
        self.pressed.connect(self._on_pressed)
        self.released.connect(self._on_released)

    def _on_pressed(self):
        """按钮按下时的处理"""
        self._click_animation.start()
        self._opacity_effect.setOpacity(0.8)

    def _on_released(self):
        """按钮释放时的处理"""
        # 创建序列动画：先恢复大小，再淡入
        sequence = QSequentialAnimationGroup()

        # 恢复大小动画
        restore_anim = QPropertyAnimation(self, b"scale")
        restore_anim.setDuration(self.config.duration // 2)
        restore_anim.setStartValue(0.95)
        restore_anim.setEndValue(1.05)
        restore_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        # 淡入动画
        fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_anim.setDuration(self.config.duration // 2)
        fade_anim.setStartValue(0.8)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        sequence.addAnimation(restore_anim)
        sequence.addAnimation(fade_anim)
        sequence.start()

        self.clicked_with_animation.emit()

    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        if self.isEnabled():
            self._hover_animation.start()

    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        if self.isEnabled():
            # 恢复原始大小
            restore_anim = QPropertyAnimation(self, b"scale")
            restore_anim.setDuration(self.config.duration)
            restore_anim.setStartValue(self._hover_animation.currentValue())
            restore_anim.setEndValue(1.0)
            restore_anim.setEasingCurve(self.config.easing_curve)
            restore_anim.start()

    @pyqtProperty(float)
    def scale(self):
        """缩放属性"""
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.update_geometry()

    def update_geometry(self):
        """更新几何形状"""
        if hasattr(self, '_scale'):
            rect = self.rect()
            center = rect.center()
            new_size = QSize(int(rect.width() * self._scale), int(rect.height() * self._scale))
            new_rect = QRect(center - QPoint(new_size.width() // 2, new_size.height() // 2), new_size)
            self.setFixedSize(new_size)

    def set_active(self, active: bool):
        """设置按钮激活状态"""
        self._is_active = active
        if active:
            self.setStyleSheet("""
                EnhancedButton {
                    background-color: #1976D2;
                    color: white;
                    border: 2px solid #64B5F6;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 120px;
                    min-height: 40px;
                }
            """)
        else:
            self._setup_enhanced_styles()


class LoadingIndicator(QWidget):
    """加载指示器"""

    def __init__(self, size: int = 40, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._rotate)
        self.setFixedSize(size, size)

    def start_animation(self):
        """开始动画"""
        self._animation_timer.start(16)  # ~60 FPS
        self.show()

    def stop_animation(self):
        """停止动画"""
        self._animation_timer.stop()
        self.hide()

    def _rotate(self):
        """旋转动画"""
        self.angle = (self.angle + 5) % 360
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = self.rect().center()
        radius = self.size // 2 - 5

        # 绘制背景圆
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawEllipse(center, radius, radius)

        # 绘制旋转指示器
        painter.save()
        painter.translate(center)
        painter.rotate(self.angle)

        # 绘制三个点
        for i in range(3):
            angle = i * 120
            x = radius * 0.7 * self._cos(angle)
            y = radius * 0.7 * self._sin(angle)

            opacity = 1.0 - (i * 0.3)
            color = QColor(33, 150, 243, int(255 * opacity))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(int(x), int(y)), 4, 4)

        painter.restore()

    def _cos(self, angle):
        """计算余弦"""
        import math
        return math.cos(math.radians(angle))

    def _sin(self, angle):
        """计算正弦"""
        import math
        return math.sin(math.radians(angle))


class SmoothStackedWidget(QStackedWidget):
    """平滑堆叠窗口部件，提供页面切换动画"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._animation_duration = 400
        self._current_animation = None
        self._direction = 1

    def set_direction(self, direction: int):
        """设置动画方向"""
        self._direction = direction

    def setCurrentWidget(self, widget):
        """设置当前部件，带动画效果"""
        current_widget = self.currentWidget()
        if current_widget and current_widget != widget:
            self._animate_transition(current_widget, widget)
        else:
            super().setCurrentWidget(widget)

    def setCurrentIndex(self, index: int):
        """设置当前索引，带动画效果"""
        if 0 <= index < self.count():
            current_widget = self.currentWidget()
            target_widget = self.widget(index)
            if current_widget and current_widget != target_widget:
                self._animate_transition(current_widget, target_widget)
            else:
                super().setCurrentIndex(index)

    def _animate_transition(self, current_widget: QWidget, target_widget: QWidget):
        """执行页面切换动画"""
        if self._current_animation:
            self._current_animation.stop()

        # 设置目标部件位置
        if self._direction == 1:
            target_widget.move(self.width(), 0)
        else:
            target_widget.move(-self.width(), 0)

        target_widget.show()
        target_widget.raise_()

        # 创建动画组
        animation_group = QParallelAnimationGroup()

        # 当前部件淡出动画
        fade_out = QPropertyAnimation(current_widget, b"opacity")
        fade_out.setDuration(self._animation_duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        # 当前部件移动动画
        move_out = QPropertyAnimation(current_widget, b"pos")
        move_out.setDuration(self._animation_duration)
        start_pos = current_widget.pos()
        if self._direction == 1:
            end_pos = QPoint(-self.width() // 2, 0)
        else:
            end_pos = QPoint(self.width() // 2, 0)
        move_out.setStartValue(start_pos)
        move_out.setEndValue(end_pos)

        # 目标部件淡入动画
        fade_in = QPropertyAnimation(target_widget, b"opacity")
        fade_in.setDuration(self._animation_duration)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)

        # 目标部件移动动画
        move_in = QPropertyAnimation(target_widget, b"pos")
        move_in.setDuration(self._animation_duration)
        if self._direction == 1:
            start_pos = QPoint(self.width(), 0)
            end_pos = QPoint(0, 0)
        else:
            start_pos = QPoint(-self.width(), 0)
            end_pos = QPoint(0, 0)
        move_in.setStartValue(start_pos)
        move_in.setEndValue(end_pos)

        animation_group.addAnimation(fade_out)
        animation_group.addAnimation(move_out)
        animation_group.addAnimation(fade_in)
        animation_group.addAnimation(move_in)

        # 动画完成后切换部件
        animation_group.finished.connect(
            lambda: self._on_animation_finished(current_widget, target_widget)
        )

        self._current_animation = animation_group
        animation_group.start()

    def _on_animation_finished(self, current_widget: QWidget, target_widget: QWidget):
        """动画完成处理"""
        super().setCurrentWidget(target_widget)
        current_widget.hide()
        current_widget.move(0, 0)
        self._current_animation = None


class ToastNotification(QWidget):
    """Toast通知组件"""

    def __init__(self, message: str, duration: int = 3000,
                 notification_type: str = "info", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.message = message
        self.duration = duration
        self.notification_type = notification_type
        self._setup_ui()
        self._setup_position()
        self._start_show_animation()

    def _setup_ui(self):
        """设置UI"""
        self.setFixedWidth(300)
        self.setMinimumHeight(60)

        # 设置样式
        bg_color = self._get_background_color()
        text_color = "#FFFFFF"
        border_color = self._get_border_color()

        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {bg_color};
                color: {text_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 图标标签
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        icon = self._get_icon()
        self.icon_label.setPixmap(icon)
        layout.addWidget(self.icon_label)

        # 消息标签
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.message_label, 1)

        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
            }
        """)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

    def _get_background_color(self) -> str:
        """获取背景颜色"""
        colors = {
            "success": "#4CAF50",
            "error": "#F44336",
            "warning": "#FF9800",
            "info": "#2196F3"
        }
        return colors.get(self.notification_type, "#2196F3")

    def _get_border_color(self) -> str:
        """获取边框颜色"""
        colors = {
            "success": "#388E3C",
            "error": "#D32F2F",
            "warning": "#F57C00",
            "info": "#1976D2"
        }
        return colors.get(self.notification_type, "#1976D2")

    def _get_icon(self) -> QIcon:
        """获取图标（简化实现）"""
        # 在实际应用中，这里应该返回实际的图标
        return QIcon()

    def _setup_position(self):
        """设置位置"""
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 20
            y = 20
            self.move(x, y)

    def _start_show_animation(self):
        """开始显示动画"""
        self.setGraphicsEffect(QGraphicsOpacityEffect())

        show_animation = QPropertyAnimation(self.graphicsEffect(), b"opacity")
        show_animation.setDuration(300)
        show_animation.setStartValue(0.0)
        show_animation.setEndValue(1.0)
        show_animation.start()

        # 自动关闭
        QTimer.singleShot(self.duration, self._start_hide_animation)

    def _start_hide_animation(self):
        """开始隐藏动画"""
        hide_animation = QPropertyAnimation(self.graphicsEffect(), b"opacity")
        hide_animation.setDuration(300)
        hide_animation.setStartValue(1.0)
        hide_animation.setEndValue(0.0)
        hide_animation.finished.connect(self.close)
        hide_animation.start()

    @staticmethod
    def show_message(message: str, duration: int = 3000,
                    notification_type: str = "info", parent: Optional[QWidget] = None):
        """显示Toast消息"""
        toast = ToastNotification(message, duration, notification_type, parent)
        toast.show()


class ProgressOverlay(QWidget):
    """进度覆盖层，用于显示长时间操作的进度"""

    def __init__(self, message: str = "正在处理...", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.message = message
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        """设置UI"""
        if self.parent():
            self.resize(self.parent().size())

        # 设置半透明背景
        self.setStyleSheet("""
            ProgressOverlay {
                background-color: rgba(0, 0, 0, 128);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 创建内容面板
        content_panel = QFrame()
        content_panel.setFixedSize(300, 150)
        content_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #E0E0E0;
            }
        """)

        panel_layout = QVBoxLayout(content_panel)
        panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.setSpacing(20)

        # 加载指示器
        self.loading_indicator = LoadingIndicator(40)
        panel_layout.addWidget(self.loading_indicator, alignment=Qt.AlignmentFlag.AlignCenter)

        # 消息标签
        self.message_label = QLabel(self.message)
        self.message_label.setStyleSheet("font-size: 14px; color: #333333;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(self.message_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E0E0E0;
                border-radius: 3px;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        panel_layout.addWidget(self.progress_bar)

        layout.addWidget(content_panel)

    def _setup_animations(self):
        """设置动画"""
        self.setGraphicsEffect(QGraphicsOpacityEffect())

    def set_progress(self, value: int):
        """设置进度值"""
        self.progress_bar.setValue(value)

    def set_message(self, message: str):
        """设置消息"""
        self.message_label.setText(message)

    def show_overlay(self):
        """显示覆盖层"""
        self.show()
        self.raise_()
        self.loading_indicator.start_animation()

        # 淡入动画
        fade_in = QPropertyAnimation(self.graphicsEffect(), b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()

    def hide_overlay(self):
        """隐藏覆盖层"""
        self.loading_indicator.stop_animation()

        # 淡出动画
        fade_out = QPropertyAnimation(self.graphicsEffect(), b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.finished.connect(self.close)
        fade_out.start()


class InteractiveGuide:
    """交互式引导系统"""

    def __init__(self):
        self.guides = {}
        self.current_guide = None

    def add_guide(self, guide_id: str, guide_data: Dict[str, Any]):
        """添加引导"""
        self.guides[guide_id] = guide_data

    def show_guide(self, guide_id: str, parent: Optional[QWidget] = None):
        """显示引导"""
        if guide_id in self.guides:
            guide_data = self.guides[guide_id]
            self.current_guide = GuideDialog(guide_data, parent)
            self.current_guide.show()


class GuideDialog(QDialog):
    """引导对话框"""

    def __init__(self, guide_data: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.guide_data = guide_data
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("功能引导")
        self.setFixedSize(500, 400)
        self.setModal(True)

        # 创建布局
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel(self.guide_data.get('title', '功能介绍'))
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #333333;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)

        # 描述
        description = QLabel(self.guide_data.get('description', ''))
        description.setWordWrap(True)
        description.setStyleSheet("""
            font-size: 14px;
            color: #666666;
            line-height: 1.5;
        """)
        layout.addWidget(description)

        # 步骤
        steps = self.guide_data.get('steps', [])
        if steps:
            steps_label = QLabel("使用步骤：")
            steps_label.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #333333;
                margin-top: 10px;
            """)
            layout.addWidget(steps_label)

            steps_layout = QVBoxLayout()
            steps_layout.setSpacing(8)

            for i, step in enumerate(steps, 1):
                step_label = QLabel(f"{i}. {step}")
                step_label.setWordWrap(True)
                step_label.setStyleSheet("""
                    font-size: 13px;
                    color: #666666;
                    padding-left: 20px;
                """)
                steps_layout.addWidget(step_label)

            layout.addLayout(steps_layout)

        # 提示
        if 'tip' in self.guide_data:
            tip_frame = QFrame()
            tip_frame.setStyleSheet("""
                QFrame {
                    background-color: #E3F2FD;
                    border: 1px solid #BBDEFB;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
            tip_layout = QHBoxLayout(tip_frame)
            tip_label = QLabel(f"💡 {self.guide_data['tip']}")
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet("font-size: 12px; color: #1976D2;")
            tip_layout.addWidget(tip_label)
            layout.addWidget(tip_frame)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        if self.guide_data.get('show_dont_show_again', False):
            self.dont_show_again = QCheckBox("不再显示")
            self.dont_show_again.setStyleSheet("font-size: 12px; color: #666666;")
            button_layout.addWidget(self.dont_show_again)

        close_button = QPushButton("知道了")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)