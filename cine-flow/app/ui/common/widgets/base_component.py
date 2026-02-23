#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 基础UI组件
提供统一的UI组件基类和通用功能
"""

from typing import Optional, Dict, Any, List, Union

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPoint, QPropertyAnimation,
    QEasingCurve, QRect
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont,
    QPainterPath
)

from ...core.logger import Logger
from ...core.icon_manager import IconManager


class Theme:
    """主题类"""
    def __init__(self, name: str, colors: Dict[str, str], fonts: Dict[str, str]):
        self.name = name
        self.colors = colors
        self.fonts = fonts


class ThemeService:
    """主题服务类"""
    def __init__(self):
        self.current_theme = None
        self.themes = {}

    def get_current_theme(self) -> Optional[Theme]:
        return self.current_theme

    def set_theme(self, theme: Theme):
        self.current_theme = theme


class EventBus:
    """事件总线类"""
    def __init__(self):
        self.handlers = {}

    def subscribe(self, event_type: str, handler):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def publish(self, event_type: str, data=None):
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                handler(data)


class ThemeColors:
    """主题颜色类"""
    def __init__(self):
        self.background = "#ffffff"
        self.foreground = "#000000"
        self.primary = "#2196F3"
        self.secondary = "#666666"
        self.accent = "#FF4081"
        self.success = "#4CAF50"
        self.warning = "#FF9800"
        self.error = "#F44336"
        self.border = "#e0e0e0"
        self.shadow = "rgba(0, 0, 0, 0.1)"


class BaseComponent(QWidget):
    """基础UI组件类"""

    # 信号定义
    theme_changed = pyqtSignal(Theme)
    component_clicked = pyqtSignal()
    component_hovered = pyqtSignal(bool)
    data_changed = pyqtSignal(dict)

    def __init__(self, parent=None, theme_service: Optional[ThemeService] = None):
        super().__init__(parent)
        self.theme_service = theme_service
        self.logger: Optional[Logger] = None
        self.event_bus: Optional[EventBus] = None

        # 组件属性
        self._component_id = ""
        self._component_name = ""
        self._tooltip_text = ""
        self._enabled = True
        self._visible = True
        self._animation_enabled = True

        # 主题相关
        self._current_theme: Optional[Theme] = None
        self._custom_styles: Dict[str, str] = {}

        # 动画相关
        self._animations: Dict[str, QPropertyAnimation] = {}

        # 初始化
        self._init_component()
        self._setup_connections()

    def _init_component(self):
        """初始化组件（子类必须实现）"""
        pass

    def _setup_connections(self):
        """设置信号连接"""
        if self.theme_service:
            self.theme_service.theme_applied.connect(self._on_theme_changed)

    def set_services(self, logger: Logger, event_bus: EventBus):
        """设置服务"""
        self.logger = logger
        self.event_bus = event_bus

    def _on_theme_changed(self, theme: Theme):
        """处理主题变更"""
        self._current_theme = theme
        self._apply_theme()
        self.theme_changed.emit(theme)

    def _apply_theme(self):
        """应用主题（子类可以重写）"""
        if self._current_theme:
            self.update()

    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)
        if self._current_theme:
            self._draw_custom_paint(event)

    def _draw_custom_paint(self, event):
        """自定义绘制（子类可以重写）"""
        pass

    def set_component_id(self, component_id: str):
        """设置组件ID"""
        self._component_id = component_id

    def get_component_id(self) -> str:
        """获取组件ID"""
        return self._component_id

    def set_component_name(self, name: str):
        """设置组件名称"""
        self._component_name = name

    def get_component_name(self) -> str:
        """获取组件名称"""
        return self._component_name

    def set_tooltip(self, tooltip: str):
        """设置工具提示"""
        self._tooltip_text = tooltip
        self.setToolTip(tooltip)

    def get_tooltip(self) -> str:
        """获取工具提示"""
        return self._tooltip_text

    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        self._enabled = enabled
        self.setEnabled(enabled)
        self.update()

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled

    def set_visible(self, visible: bool):
        """设置可见状态"""
        self._visible = visible
        self.setVisible(visible)

    def is_visible(self) -> bool:
        """检查是否可见"""
        return self._visible

    def set_animation_enabled(self, enabled: bool):
        """设置动画启用状态"""
        self._animation_enabled = enabled

    def is_animation_enabled(self) -> bool:
        """检查动画是否启用"""
        return self._animation_enabled

    def add_custom_style(self, selector: str, style: str):
        """添加自定义样式"""
        self._custom_styles[selector] = style
        self._update_stylesheet()

    def remove_custom_style(self, selector: str):
        """移除自定义样式"""
        if selector in self._custom_styles:
            del self._custom_styles[selector]
            self._update_stylesheet()

    def _update_stylesheet(self):
        """更新样式表"""
        if self._custom_styles:
            stylesheet = ""
            for selector, style in self._custom_styles.items():
                stylesheet += f"{selector} {{ {style} }}\n"
            self.setStyleSheet(stylesheet)

    def fade_in(self, duration: int = 300):
        """淡入动画"""
        if self._animation_enabled:
            self._animate_property("opacity", 0.0, 1.0, duration)

    def fade_out(self, duration: int = 300):
        """淡出动画"""
        if self._animation_enabled:
            self._animate_property("opacity", 1.0, 0.0, duration)

    def slide_in(self, direction: str = "left", duration: int = 300):
        """滑入动画"""
        if self._animation_enabled:
            start_pos = self._get_start_position(direction)
            end_pos = self.pos()
            self._animate_position(start_pos, end_pos, duration)

    def slide_out(self, direction: str = "left", duration: int = 300):
        """滑出动画"""
        if self._animation_enabled:
            start_pos = self.pos()
            end_pos = self._get_end_position(direction)
            self._animate_position(start_pos, end_pos, duration)

    def _get_start_position(self, direction: str) -> QPoint:
        """获取动画起始位置"""
        width = self.width()
        height = self.height()
        current_pos = self.pos()

        if direction == "left":
            return QPoint(current_pos.x() - width, current_pos.y())
        elif direction == "right":
            return QPoint(current_pos.x() + width, current_pos.y())
        elif direction == "top":
            return QPoint(current_pos.x(), current_pos.y() - height)
        elif direction == "bottom":
            return QPoint(current_pos.x(), current_pos.y() + height)
        else:
            return current_pos

    def _get_end_position(self, direction: str) -> QPoint:
        """获取动画结束位置"""
        width = self.width()
        height = self.height()
        current_pos = self.pos()

        if direction == "left":
            return QPoint(current_pos.x() - width, current_pos.y())
        elif direction == "right":
            return QPoint(current_pos.x() + width, current_pos.y())
        elif direction == "top":
            return QPoint(current_pos.x(), current_pos.y() - height)
        elif direction == "bottom":
            return QPoint(current_pos.x(), current_pos.y() + height)
        else:
            return current_pos

    def _animate_property(self, property_name: str, start_value: float, end_value: float, duration: int):
        """动画属性"""
        animation = QPropertyAnimation(self, property_name.encode())
        animation.setDuration(duration)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

        self._animations[property_name] = animation

    def _animate_position(self, start_pos: QPoint, end_pos: QPoint, duration: int):
        """动画位置"""
        animation = QPropertyAnimation(self, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

        self._animations["position"] = animation

    def stop_animations(self):
        """停止所有动画"""
        for animation in self._animations.values():
            if animation.state() == QPropertyAnimation.State.Running:
                animation.stop()
        self._animations.clear()

    def emit_data_changed(self, data: Dict[str, Any]):
        """发送数据变更信号"""
        self.data_changed.emit(data)
        if self.event_bus:
            self.event_bus.emit(f"component.{self._component_id}.data_changed", data)

    def log_info(self, message: str):
        """记录信息日志"""
        if self.logger:
            self.logger.info(f"[{self._component_name}] {message}")

    def log_error(self, message: str):
        """记录错误日志"""
        if self.logger:
            self.logger.error(f"[{self._component_name}] {message}")

    def log_warning(self, message: str):
        """记录警告日志"""
        if self.logger:
            self.logger.warning(f"[{self._component_name}] {message}")


class BaseContainer(BaseComponent):
    """基础容器组件"""

    def __init__(self, parent=None, layout_type: str = "vertical", theme_service: Optional[ThemeService] = None):
        super().__init__(parent, theme_service)
        self.layout_type = layout_type
        self.child_components: List[BaseComponent] = []

    def _init_component(self):
        """初始化组件"""
        # 创建布局
        if self.layout_type == "vertical":
            self.layout = QVBoxLayout(self)
        elif self.layout_type == "horizontal":
            self.layout = QHBoxLayout(self)
        elif self.layout_type == "grid":
            self.layout = QGridLayout(self)
        else:
            self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def add_component(self, component: BaseComponent, stretch: int = 0, alignment: Optional[Qt.AlignmentFlag] = None):
        """添加子组件"""
        self.child_components.append(component)

        if isinstance(self.layout, QVBoxLayout) or isinstance(self.layout, QHBoxLayout):
            self.layout.addWidget(component, stretch)
            if alignment:
                self.layout.setAlignment(component, alignment)
        elif isinstance(self.layout, QGridLayout):
            # 简单的网格布局添加
            row = len(self.child_components) - 1
            self.layout.addWidget(component, row, 0)

    def add_stretch(self, stretch: int = 1):
        """添加弹性空间"""
        if isinstance(self.layout, QVBoxLayout) or isinstance(self.layout, QHBoxLayout):
            self.layout.addStretch(stretch)

    def add_spacing(self, spacing: int):
        """添加间距"""
        if isinstance(self.layout, QVBoxLayout) or isinstance(self.layout, QHBoxLayout):
            self.layout.addSpacing(spacing)

    def remove_component(self, component: BaseComponent):
        """移除子组件"""
        if component in self.child_components:
            self.child_components.remove(component)
            self.layout.removeWidget(component)
            component.setParent(None)

    def clear_components(self):
        """清空所有子组件"""
        for component in self.child_components[:]:
            self.remove_component(component)
        self.child_components.clear()

    def get_child_components(self) -> List[BaseComponent]:
        """获取子组件列表"""
        return self.child_components.copy()

    def find_component_by_id(self, component_id: str) -> Optional[BaseComponent]:
        """根据ID查找子组件"""
        for component in self.child_components:
            if component.get_component_id() == component_id:
                return component
        return None


class BaseFrame(BaseContainer):
    """基础框架组件"""

    def __init__(self, parent=None, layout_type: str = "vertical", frame_shape: QFrame.Shape = QFrame.Shape.Box,
                 theme_service: Optional[ThemeService] = None):
        super().__init__(parent, layout_type, theme_service)
        self.frame_shape = frame_shape
        self._border_width = 1
        self._border_radius = 4
        self._shadow_enabled = True

    def _init_component(self):
        """初始化组件"""
        super()._init_component()

        # 设置框架属性
        self.setFrameShape(self.frame_shape)
        self.setFrameShadow(QFrame.Shadow.Raised)

    def set_frame_shape(self, shape: QFrame.Shape):
        """设置框架形状"""
        self.frame_shape = shape
        self.setFrameShape(shape)

    def set_border_width(self, width: int):
        """设置边框宽度"""
        self._border_width = width
        self.update()

    def set_border_radius(self, radius: int):
        """设置边框圆角"""
        self._border_radius = radius
        self.update()

    def set_shadow_enabled(self, enabled: bool):
        """设置阴影启用状态"""
        self._shadow_enabled = enabled
        self.update()

    def _draw_custom_paint(self, event):
        """自定义绘制"""
        if self._current_theme and self._border_radius > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 绘制圆角边框
            rect = self.rect()
            path = QPainterPath()
            path.addRoundedRect(rect, self._border_radius, self._border_radius)

            # 设置边框
            pen = QPen(QColor(self._current_theme.colors.border_color))
            pen.setWidth(self._border_width)
            painter.setPen(pen)

            # 设置背景
            brush = QBrush(QColor(self._current_theme.colors.background_color))
            painter.setBrush(brush)

            painter.drawPath(path)

            # 绘制阴影
            if self._shadow_enabled:
                self._draw_shadow(painter, rect)

    def _draw_shadow(self, painter: QPainter, rect: QRect):
        """绘制阴影"""
        if not self._current_theme:
            return

        shadow_color = QColor(self._current_theme.colors.border_color)
        shadow_color.setAlpha(50)

        for i in range(3):
            shadow_rect = rect.adjusted(i + 1, i + 1, i + 1, i + 1)
            path = QPainterPath()
            path.addRoundedRect(shadow_rect, self._border_radius, self._border_radius)

            pen = QPen(shadow_color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)


class BasePanel(BaseFrame):
    """基础面板组件"""

    def __init__(self, parent=None, layout_type: str = "vertical", title: str = "",
                 theme_service: Optional[ThemeService] = None):
        super().__init__(parent, layout_type, QFrame.Shape.Box, theme_service)
        self.title = title
        self.title_label: Optional[QLabel] = None

    def _init_component(self):
        """初始化组件"""
        super()._init_component()

        # 如果有标题，创建标题标签
        if self.title:
            self._create_title_label()

    def _create_title_label(self):
        """创建标题标签"""
        self.title_label = QLabel(self.title)
        title_font = QFont("Arial", 12, QFont.Weight.Bold)
        self.title_label.setFont(title_font)

        # 添加到布局中
        if isinstance(self.layout, QVBoxLayout):
            self.layout.addWidget(self.title_label)
        elif isinstance(self.layout, QHBoxLayout):
            self.layout.addWidget(self.title_label)
        elif isinstance(self.layout, QGridLayout):
            self.layout.addWidget(self.title_label, 0, 0)

    def set_title(self, title: str):
        """设置标题"""
        self.title = title
        if self.title_label:
            self.title_label.setText(title)
        else:
            self._create_title_label()

    def get_title(self) -> str:
        """获取标题"""
        return self.title

    def set_title_visible(self, visible: bool):
        """设置标题可见性"""
        if self.title_label:
            self.title_label.setVisible(visible)


class BaseButton(BaseComponent):
    """基础按钮组件"""

    clicked = pyqtSignal()
    pressed = pyqtSignal()
    released = pyqtSignal()

    def __init__(self, text: str = "", parent=None, theme_service: Optional[ThemeService] = None):
        super().__init__(parent, theme_service)
        self.text = text
        self._is_pressed = False
        self._is_hovered = False

    def _init_component(self):
        """初始化组件"""
        self.setFixedSize(100, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        colors = self._get_colors()

        # 绘制按钮背景
        if self._is_pressed:
            bg_color = colors.pressed_color
        elif self._is_hovered:
            bg_color = colors.hover_color
        else:
            bg_color = colors.secondary_color

        painter.fillRect(rect, bg_color)

        # 绘制边框
        pen = QPen(QColor(colors.border_color))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(rect)

        # 绘制文本
        if self.text:
            painter.setPen(QColor(colors.foreground_color))
            font = QFont("Arial", 10)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text)

    def _get_colors(self) -> ThemeColors:
        """获取颜色"""
        if self._current_theme:
            return self._current_theme.colors
        else:
            return ThemeColors()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        self._is_pressed = True
        self.update()
        self.pressed.emit()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self._is_pressed = False
        self.update()
        self.released.emit()
        self.clicked.emit()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        """鼠标进入事件"""
        self._is_hovered = True
        self.update()
        self.component_hovered.emit(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self._is_hovered = False
        self.update()
        self.component_hovered.emit(False)
        super().leaveEvent(event)

    def set_text(self, text: str):
        """设置文本"""
        self.text = text
        self.update()

    def get_text(self) -> str:
        """获取文本"""
        return self.text

    def set_size(self, width: int, height: int):
        """设置大小"""
        self.setFixedSize(width, height)