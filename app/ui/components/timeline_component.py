#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 时间线组件模块
专业级时间线UI组件，提供直观的编辑界面、实时预览和丰富的交互功能
"""

import os
import time
from typing import Dict, List, Optional, Tuple, Union, Any, Set
from dataclasses import dataclass
from enum import Enum
import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QPushButton, QSlider, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox, QFrame, QSplitter,
    QToolBar, QMenu, QToolButton, QFileDialog,
    QMessageBox, QInputDialog, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QTextEdit, QProgressBar,
    QStatusBar, QToolTip, QApplication, QScrollArea
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QObject, QPoint, QRect, QSize,
    QTimer, QPropertyAnimation, QEasingCurve, QThread,
    pyqtSlot, QMimeData, QPointF, QRectF, QBuffer
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QCursor,
    QPixmap, QImage, QMouseEvent, QWheelEvent, QDragEnterEvent,
    QDropEvent, QDrag, QPainterPath, QLinearGradient,
    QKeySequence, QIcon, QMouseEvent, QPaintEvent, QAction,
    QContextMenuEvent
)

from ..components.base_component import BaseComponent, BaseContainer, BasePanel
from ...core.timeline_engine import (
    TimelineEngine, TimelineSettings, Track, Clip, TrackType,
    ClipState, PlaybackState, ZoomLevel, TimeCode
)
from ...core.clip_manager import ClipManager, ClipMetadata, ClipAnalysis
from ...core.keyframe_system import KeyframeSystem, KeyframeTrack, InterpolationType, EasingFunction
from ...core.logger import get_logger
from ...core.event_system import EventBus
from ...utils.error_handler import ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler


class TimelineDisplayMode(Enum):
    """时间线显示模式"""
    FRAMES = "frames"
    SECONDS = "seconds"
    TIMECODE = "timecode"
    SAMPLES = "samples"


class TimelineTool(Enum):
    """时间线工具"""
    SELECT = "select"
    TRIM = "trim"
    RAZOR = "razor"
    SLIP = "slip"
    SLIDE = "slide"
    PEN = "pen"
    HAND = "hand"
    ZOOM = "zoom"


@dataclass
class TimelineTheme:
    """时间线主题"""
    background_color: QColor = QColor(30, 30, 30)
    track_background: QColor = QColor(45, 45, 45)
    track_border: QColor = QColor(70, 70, 70)
    clip_normal: QColor = QColor(80, 120, 160)
    clip_selected: QColor = QColor(100, 140, 180)
    clip_hover: QColor = QColor(90, 130, 170)
    clip_border: QColor = QColor(255, 255, 255)
    text_color: QColor = QColor(255, 255, 255)
    grid_color: QColor = QColor(60, 60, 60)
    playhead_color: QColor = QColor(255, 100, 100)
    marker_color: QColor = QColor(255, 200, 100)
    keyframe_color: QColor = QColor(100, 255, 100)
    waveform_color: QColor = QColor(100, 200, 255)
    selection_color: QColor = QColor(255, 255, 100, 100)
    ruler_color: QColor = QColor(70, 70, 70)
    ruler_text: QColor = QColor(200, 200, 200)


class TimelineRuler(QWidget):
    """时间线标尺组件"""

    def __init__(self, timeline_engine: TimelineEngine, parent=None):
        super().__init__(parent)
        self.timeline_engine = timeline_engine
        self.theme = TimelineTheme()
        self.setFixedHeight(40)
        self.setMouseTracking(True)

        # 显示模式
        self.display_mode = TimelineDisplayMode.TIMECODE
        self.zoom_level = ZoomLevel.SECOND
        self.pixels_per_second = 100.0
        self.scroll_offset = 0.0

        # 鼠标位置
        self.mouse_time = 0.0
        self.show_mouse_time = False

        # 标记
        self.markers: List[float] = []
        self.in_point: Optional[float] = None
        self.out_point: Optional[float] = None

        # 连接事件
        self.timeline_engine.event_bus.subscribe("timeline_seeked", self._on_timeline_seeked)
        self.timeline_engine.event_bus.subscribe("zoom_changed", self._on_zoom_changed)

    def set_display_mode(self, mode: TimelineDisplayMode) -> None:
        """设置显示模式"""
        self.display_mode = mode
        self.update()

    def set_zoom_level(self, zoom_level: ZoomLevel, scale: float = 1.0) -> None:
        """设置缩放级别"""
        self.zoom_level = zoom_level

        # 更新像素/秒比例
        if zoom_level == ZoomLevel.FRAME:
            self.pixels_per_second = 30.0 * scale
        elif zoom_level == ZoomLevel.SECOND:
            self.pixels_per_second = 100.0 * scale
        elif zoom_level == ZoomLevel.MIN_ZOOM:
            self.pixels_per_second = 10.0 * scale
        elif zoom_level == ZoomLevel.FIT:
            self.pixels_per_second = 50.0 * scale
        else:
            self.pixels_per_second = 100.0 * scale

        self.update()

    def set_scroll_offset(self, offset: float) -> None:
        """设置滚动偏移"""
        self.scroll_offset = offset
        self.update()

    def add_marker(self, time: float) -> None:
        """添加标记"""
        if time not in self.markers:
            self.markers.append(time)
            self.markers.sort()
            self.update()

    def remove_marker(self, time: float) -> None:
        """移除标记"""
        if time in self.markers:
            self.markers.remove(time)
            self.update()

    def set_in_point(self, time: Optional[float]) -> None:
        """设置入点"""
        self.in_point = time
        self.update()

    def set_out_point(self, time: Optional[float]) -> None:
        """设置出点"""
        self.out_point = time
        self.update()

    def time_to_x(self, time: float) -> float:
        """时间转换为X坐标"""
        return time * self.pixels_per_second - self.scroll_offset

    def x_to_time(self, x: float) -> float:
        """X坐标转换为时间"""
        return (x + self.scroll_offset) / self.pixels_per_second

    def format_time(self, time: float) -> str:
        """格式化时间"""
        if self.display_mode == TimelineDisplayMode.TIMECODE:
            timecode = TimeCode.from_seconds(time, self.timeline_engine.settings.frame_rate)
            return str(timecode)
        elif self.display_mode == TimelineDisplayMode.SECONDS:
            return f"{time:.2f}s"
        elif self.display_mode == TimelineDisplayMode.FRAMES:
            frames = int(time * self.timeline_engine.settings.frame_rate)
            return f"{frames}f"
        else:
            return f"{time:.3f}"

    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景
        painter.fillRect(self.rect(), self.theme.background_color)

        # 计算可见时间范围
        start_time = self.x_to_time(0)
        end_time = self.x_to_time(self.width())

        # 绘制网格
        self._draw_grid(painter, start_time, end_time)

        # 绘制标记
        self._draw_markers(painter)

        # 绘制入点出点
        self._draw_in_out_points(painter)

        # 绘制播放头
        self._draw_playhead(painter)

        # 绘制鼠标时间
        if self.show_mouse_time:
            self._draw_mouse_time(painter)

    def _draw_grid(self, painter: QPainter, start_time: float, end_time: float) -> None:
        """绘制网格"""
        painter.setPen(QPen(self.theme.grid_color))

        # 确定网格间隔
        if self.zoom_level == ZoomLevel.FRAME:
            major_interval = 1.0 / self.timeline_engine.settings.frame_rate
            minor_interval = major_interval
        elif self.zoom_level == ZoomLevel.SECOND:
            major_interval = 1.0
            minor_interval = 0.1
        else:
            major_interval = 1.0
            minor_interval = 0.1

        # 绘制主刻度
        for time in range(int(start_time), int(end_time) + 1, int(major_interval)):
            x = self.time_to_x(time)
            if 0 <= x <= self.width():
                painter.drawLine(int(x), 0, int(x), self.height())

                # 绘制时间标签
                painter.setPen(QPen(self.theme.ruler_text))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(int(x) + 2, self.height() - 5, self.format_time(time))

        # 绘制次刻度
        painter.setPen(QPen(self.theme.grid_color, 1, Qt.PenStyle.DotLine))
        for time in range(int(start_time), int(end_time) + 1):
            for minor in range(1, int(major_interval / minor_interval)):
                minor_time = time + minor * minor_interval
                x = self.time_to_x(minor_time)
                if 0 <= x <= self.width():
                    painter.drawLine(int(x), 0, int(x), self.height() // 2)

    def _draw_markers(self, painter: QPainter) -> None:
        """绘制标记"""
        painter.setPen(QPen(self.theme.marker_color, 2))

        for marker_time in self.markers:
            x = self.time_to_x(marker_time)
            if 0 <= x <= self.width():
                # 绘制标记三角形
                path = QPainterPath()
                path.moveTo(x, 5)
                path.lineTo(x - 5, 15)
                path.lineTo(x + 5, 15)
                path.closeSubpath()

                painter.fillPath(path, QBrush(self.theme.marker_color))
                painter.drawPath(path)

    def _draw_in_out_points(self, painter: QPainter) -> None:
        """绘制入点出点"""
        # 入点
        if self.in_point is not None:
            x = self.time_to_x(self.in_point)
            if 0 <= x <= self.width():
                painter.setPen(QPen(self.theme.marker_color, 2))
                painter.setBrush(QBrush(self.theme.marker_color))
                painter.drawRect(int(x) - 2, 5, 4, 10)

                # 标签
                painter.setPen(QPen(self.theme.ruler_text))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(int(x) + 6, 15, "IN")

        # 出点
        if self.out_point is not None:
            x = self.time_to_x(self.out_point)
            if 0 <= x <= self.width():
                painter.setPen(QPen(self.theme.marker_color, 2))
                painter.setBrush(QBrush(self.theme.marker_color))
                painter.drawRect(int(x) - 2, 5, 4, 10)

                # 标签
                painter.setPen(QPen(self.theme.ruler_text))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(int(x) - 25, 15, "OUT")

    def _draw_playhead(self, painter: QPainter) -> None:
        """绘制播放头"""
        current_time = self.timeline_engine.state.current_time
        x = self.time_to_x(current_time)

        if 0 <= x <= self.width():
            # 绘制播放头线
            painter.setPen(QPen(self.theme.playhead_color, 2))
            painter.drawLine(int(x), 0, int(x), self.height())

            # 绘制播放头三角形
            path = QPainterPath()
            path.moveTo(x, self.height() - 5)
            path.lineTo(x - 5, self.height() - 15)
            path.lineTo(x + 5, self.height() - 15)
            path.closeSubpath()

            painter.fillPath(path, QBrush(self.theme.playhead_color))
            painter.drawPath(path)

    def _draw_mouse_time(self, painter: QPainter) -> None:
        """绘制鼠标时间"""
        painter.setPen(QPen(self.theme.text_color))
        painter.setFont(QFont("Arial", 10))

        time_text = self.format_time(self.mouse_time)
        painter.drawText(self.mouse_pos.x() + 10, self.mouse_pos.y() - 10, time_text)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            time = self.x_to_time(event.pos().x())

            # 跳转到指定时间
            self.timeline_engine.seek_to(time)

            # 检查是否点击了标记
            for marker_time in self.markers:
                marker_x = self.time_to_x(marker_time)
                if abs(event.pos().x() - marker_x) < 10:
                    # 右键删除标记
                    if event.button() == Qt.MouseButton.RightButton:
                        self.remove_marker(marker_time)
                    break

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """鼠标移动事件"""
        self.mouse_pos = event.pos()
        self.mouse_time = self.x_to_time(event.pos().x())
        self.show_mouse_time = True
        self.update()

    def mouseLeaveEvent(self, event: QMouseEvent) -> None:
        """鼠标离开事件"""
        self.show_mouse_time = False
        self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """滚轮事件"""
        # 缩放
        delta = event.angleDelta().y()
        if delta > 0:
            # 放大
            self.pixels_per_second *= 1.1
        else:
            # 缩小
            self.pixels_per_second *= 0.9

        self.update()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """右键菜单事件"""
        menu = QMenu(self)

        # 添加标记
        add_marker_action = menu.addAction("添加标记")
        add_marker_action.triggered.connect(lambda: self.add_marker(self.mouse_time))

        # 设置入点
        set_in_action = menu.addAction("设置入点")
        set_in_action.triggered.connect(lambda: self.set_in_point(self.mouse_time))

        # 设置出点
        set_out_action = menu.addAction("设置出点")
        set_out_action.triggered.connect(lambda: self.set_out_point(self.mouse_time))

        # 清除入点出点
        clear_points_action = menu.addAction("清除入点出点")
        clear_points_action.triggered.connect(lambda: [self.set_in_point(None), self.set_out_point(None)])

        menu.exec(event.globalPos())

    def _on_timeline_seeked(self, data: Any) -> None:
        """处理时间线跳转事件"""
        self.update()

    def _on_zoom_changed(self, data: Any) -> None:
        """处理缩放变更事件"""
        zoom_level = data.get('zoom_level')
        scale = data.get('scale', 1.0)
        self.set_zoom_level(ZoomLevel(zoom_level), scale)


class TrackWidget(QWidget):
    """轨道组件"""

    def __init__(self, track: Track, timeline_engine: TimelineEngine, parent=None):
        super().__init__(parent)
        self.track = track
        self.timeline_engine = timeline_engine
        self.theme = TimelineTheme()
        self.setMouseTracking(True)

        # 布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 轨道头部
        self.track_header = QWidget()
        self.track_header.setFixedWidth(150)
        self.track_header_layout = QHBoxLayout(self.track_header)
        self.track_header_layout.setContentsMargins(5, 0, 5, 0)

        # 轨道名称
        self.name_label = QLabel(track.name)
        self.name_label.setStyleSheet(f"color: {self.theme.text_color.name()}")
        self.track_header_layout.addWidget(self.name_label)

        # 轨道控制按钮
        self.mute_button = QPushButton("M")
        self.mute_button.setFixedSize(20, 20)
        self.mute_button.setCheckable(True)
        self.mute_button.setChecked(track.muted)
        self.mute_button.clicked.connect(self._toggle_mute)
        self.track_header_layout.addWidget(self.mute_button)

        self.solo_button = QPushButton("S")
        self.solo_button.setFixedSize(20, 20)
        self.solo_button.setCheckable(True)
        self.track_header_layout.addWidget(self.solo_button)

        self.lock_button = QPushButton("L")
        self.lock_button.setFixedSize(20, 20)
        self.lock_button.setCheckable(True)
        self.lock_button.setChecked(track.locked)
        self.lock_button.clicked.connect(self._toggle_lock)
        self.track_header_layout.addWidget(self.lock_button)

        self.track_header_layout.addStretch()

        # 轨道内容区域
        self.content_area = QWidget()
        self.content_area.setMinimumHeight(track.height)

        self.layout.addWidget(self.track_header)
        self.layout.addWidget(self.content_area)

        # 剪辑组件
        self.clip_widgets: List[ClipWidget] = []
        self._update_clips()

        # 连接事件
        self.timeline_engine.event_bus.subscribe("clip_added", self._on_clip_added)
        self.timeline_engine.event_bus.subscribe("clip_removed", self._on_clip_removed)
        self.timeline_engine.event_bus.subscribe("clip_moved", self._on_clip_moved)

    def _update_clips(self) -> None:
        """更新剪辑组件"""
        # 清除现有剪辑组件
        for clip_widget in self.clip_widgets:
            clip_widget.setParent(None)
            clip_widget.deleteLater()
        self.clip_widgets.clear()

        # 创建新的剪辑组件
        for clip in self.track.clips:
            clip_widget = ClipWidget(clip, self.timeline_engine, self.content_area)
            self.clip_widgets.append(clip_widget)

    def _toggle_mute(self, checked: bool) -> None:
        """切换静音"""
        self.track.muted = checked

    def _toggle_lock(self, checked: bool) -> None:
        """切换锁定"""
        self.track.locked = checked

    def _on_clip_added(self, data: Any) -> None:
        """处理剪辑添加事件"""
        if data.get('track_id') == self.track.id:
            self._update_clips()

    def _on_clip_removed(self, data: Any) -> None:
        """处理剪辑移除事件"""
        if data.get('track_id') == self.track.id:
            self._update_clips()

    def _on_clip_moved(self, data: Any) -> None:
        """处理剪辑移动事件"""
        if data.get('new_track_id') == self.track.id or data.get('old_track_id') == self.track.id:
            self._update_clips()

    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景
        painter.fillRect(self.rect(), self.theme.track_background)

        # 边框
        painter.setPen(QPen(self.theme.track_border))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))


class ClipWidget(QWidget):
    """剪辑组件"""

    def __init__(self, clip: Clip, timeline_engine: TimelineEngine, parent=None):
        super().__init__(parent)
        self.clip = clip
        self.timeline_engine = timeline_engine
        self.theme = TimelineTheme()
        self.setMouseTracking(True)

        # 设置剪辑大小和位置
        self.update_geometry()

        # 选择状态
        self.selected = False
        self.dragging = False
        self.resizing = False
        self.drag_start_pos = QPoint()
        self.drag_start_time = 0.0

        # 连接事件
        self.timeline_engine.event_bus.subscribe("clip_trimmed", self._on_clip_trimmed)

    def update_geometry(self) -> None:
        """更新几何形状"""
        # 获取父容器的缩放和滚动信息
        parent = self.parent()
        if parent:
            pixels_per_second = 100.0  # 需要从时间线获取
            scroll_offset = 0.0  # 需要从时间线获取

            x = self.clip.timeline_start * pixels_per_second - scroll_offset
            width = self.clip.get_timeline_duration() * pixels_per_second

            self.setGeometry(int(x), 0, int(width), parent.height())

    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 确定剪辑颜色
        if self.selected:
            color = self.theme.clip_selected
        elif self.underMouse():
            color = self.theme.clip_hover
        else:
            color = self.theme.clip_normal

        # 绘制剪辑背景
        painter.fillRect(self.rect(), color)

        # 绘制边框
        painter.setPen(QPen(self.theme.clip_border))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # 绘制剪辑名称
        painter.setPen(QPen(self.theme.text_color))
        painter.setFont(QFont("Arial", 10))
        text_rect = self.rect().adjusted(5, 5, -5, -5)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.clip.name)

        # 绘制时间信息
        time_text = f"{self.clip.start_time:.2f}s - {self.clip.end_time:.2f}s"
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, time_text)

        # 如果是音频剪辑，绘制波形
        if self.clip.track_type == TrackType.AUDIO:
            self._draw_waveform(painter)

        # 绘制关键帧
        self._draw_keyframes(painter)

    def _draw_waveform(self, painter: QPainter) -> None:
        """绘制波形"""
        # 从剪辑管理器获取波形数据
        clip_manager = get_clip_manager(self.timeline_engine)
        waveform = clip_manager.get_waveform(self.clip.id)

        if waveform:
            painter.setPen(QPen(self.theme.waveform_color))
            rect = self.rect().adjusted(2, 2, -2, -2)

            # 简化的波形绘制
            step = max(1, len(waveform) // rect.width())
            for i in range(0, len(waveform), step):
                x = rect.left() + (i / len(waveform)) * rect.width()
                amplitude = waveform[i] * rect.height() / 2
                y = rect.center().y()
                painter.drawLine(int(x), int(y - amplitude), int(x), int(y + amplitude))

    def _draw_keyframes(self, painter: QPainter) -> None:
        """绘制关键帧"""
        keyframe_system = get_keyframe_system(self.timeline_engine)

        # 绘制关键帧标记
        for property_name, keyframes in self.clip.keyframes.items():
            for keyframe in keyframes:
                # 计算关键帧在剪辑中的相对位置
                relative_time = keyframe.time - self.clip.start_time
                relative_duration = self.clip.get_duration()

                if relative_duration > 0:
                    x = (relative_time / relative_duration) * self.width()

                    # 绘制关键帧点
                    painter.setPen(QPen(self.theme.keyframe_color))
                    painter.setBrush(QBrush(self.theme.keyframe_color))
                    painter.drawEllipse(int(x) - 3, int(self.height() / 2) - 3, 6, 6)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected = True
            self.drag_start_pos = event.pos()
            self.drag_start_time = self.clip.timeline_start

            # 检查是否在调整大小区域
            if event.pos().x() < 10:  # 左边缘
                self.resizing = True
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
            elif event.pos().x() > self.width() - 10:  # 右边缘
                self.resizing = True
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
            else:
                self.dragging = True
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """鼠标移动事件"""
        if self.dragging:
            # 计算时间偏移
            pixels_per_second = 100.0  # 需要从时间线获取
            time_offset = (event.pos().x() - self.drag_start_pos.x()) / pixels_per_second

            # 更新剪辑位置
            new_start_time = self.drag_start_time + time_offset
            new_duration = self.clip.get_timeline_duration()

            # 移动剪辑
            self.timeline_engine.move_clip(
                self.clip.id,
                self.clip.track_id,
                new_start_time
            )

        elif self.resizing:
            # 调整剪辑大小
            pixels_per_second = 100.0  # 需要从时间线获取
            time_offset = (event.pos().x() - self.drag_start_pos.x()) / pixels_per_second

            if event.pos().x() < 10:  # 调整开始时间
                new_start_time = self.clip.start_time + time_offset
                new_end_time = self.clip.end_time
            else:  # 调整结束时间
                new_start_time = self.clip.start_time
                new_end_time = self.clip.end_time + time_offset

            # 修剪剪辑
            self.timeline_engine.trim_clip(
                self.clip.id,
                new_start_time,
                new_end_time
            )
        else:
            # 更新鼠标样式
            if event.pos().x() < 10 or event.pos().x() > self.width() - 10:
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件"""
        self.dragging = False
        self.resizing = False
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """双击事件"""
        # 打开剪辑属性对话框
        self._show_clip_properties()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """右键菜单事件"""
        menu = QMenu(self)

        # 属性
        properties_action = menu.addAction("属性")
        properties_action.triggered.connect(self._show_clip_properties)

        # 分割
        split_action = menu.addAction("分割")
        split_action.triggered.connect(self._split_clip)

        # 复制
        copy_action = menu.addAction("复制")
        copy_action.triggered.connect(self._copy_clip)

        # 删除
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(self._delete_clip)

        menu.exec(event.globalPos())

    def _show_clip_properties(self) -> None:
        """显示剪辑属性"""
        dialog = ClipPropertiesDialog(self.clip, self.timeline_engine, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 更新剪辑属性
            pass

    def _split_clip(self) -> None:
        """分割剪辑"""
        # 获取当前播放头位置
        current_time = self.timeline_engine.state.current_time

        # 检查播放头是否在剪辑范围内
        if (self.clip.timeline_start <= current_time <= self.clip.timeline_end):
            self.timeline_engine.split_clip(self.clip.id, current_time)

    def _copy_clip(self) -> None:
        """复制剪辑"""
        clip_manager = get_clip_manager(self.timeline_engine)
        clip_manager.duplicate_clip(self.clip.id, f"{self.clip.name}_copy")

    def _delete_clip(self) -> None:
        """删除剪辑"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除剪辑 '{self.clip.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.timeline_engine.remove_clip(self.clip.id)

    def _on_clip_trimmed(self, data: Any) -> None:
        """处理剪辑修剪事件"""
        if data.get('clip_id') == self.clip.id:
            self.update_geometry()


class ClipPropertiesDialog(QDialog):
    """剪辑属性对话框"""

    def __init__(self, clip: Clip, timeline_engine: TimelineEngine, parent=None):
        super().__init__(parent)
        self.clip = clip
        self.timeline_engine = timeline_engine

        self.setWindowTitle(f"剪辑属性 - {clip.name}")
        self.setModal(True)
        self.resize(400, 300)

        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 属性表单
        form_layout = QFormLayout()

        # 名称
        self.name_edit = QLineEdit(self.clip.name)
        form_layout.addRow("名称:", self.name_edit)

        # 开始时间
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setRange(0, 999999)
        self.start_time_spin.setValue(self.clip.start_time)
        self.start_time_spin.setSuffix("s")
        form_layout.addRow("开始时间:", self.start_time_spin)

        # 结束时间
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setRange(0, 999999)
        self.end_time_spin.setValue(self.clip.end_time)
        self.end_time_spin.setSuffix("s")
        form_layout.addRow("结束时间:", self.end_time_spin)

        # 音量
        self.volume_spin = QDoubleSpinBox()
        self.volume_spin.setRange(0, 2)
        self.volume_spin.setValue(self.clip.volume)
        self.volume_spin.setSingleStep(0.1)
        form_layout.addRow("音量:", self.volume_spin)

        # 透明度
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0, 1)
        self.opacity_spin.setValue(self.clip.opacity)
        self.opacity_spin.setSingleStep(0.1)
        form_layout.addRow("透明度:", self.opacity_spin)

        # 速度
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 10)
        self.speed_spin.setValue(self.clip.speed)
        self.speed_spin.setSingleStep(0.1)
        form_layout.addRow("速度:", self.speed_spin)

        layout.addLayout(form_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self) -> None:
        """接受对话框"""
        # 更新剪辑属性
        self.clip.name = self.name_edit.text()
        self.clip.volume = self.volume_spin.value()
        self.clip.opacity = self.opacity_spin.value()
        self.clip.speed = self.speed_spin.value()

        super().accept()


class TimelineComponent(BasePanel):
    """时间线组件主类"""

    # 信号定义
    timeline_ready = pyqtSignal()
    clip_selected = pyqtSignal(str)
    track_selected = pyqtSignal(str)
    time_changed = pyqtSignal(float)

    def __init__(self, timeline_engine: Optional[TimelineEngine] = None, parent=None):
        super().__init__(parent, layout_type="vertical", title="时间线")
        self.timeline_engine = timeline_engine or get_timeline_engine()
        self.clip_manager = get_clip_manager(self.timeline_engine)
        self.keyframe_system = get_keyframe_system(self.timeline_engine)
        self.theme = TimelineTheme()

        # 工具
        self.current_tool = TimelineTool.SELECT

        # 组件
        self.toolbar = None
        self.ruler = None
        self.track_area = None
        self.status_bar = None

        # 初始化
        self._init_component()
        self._setup_connections()

    def _init_component(self) -> None:
        """初始化组件"""
        # 工具栏
        self._create_toolbar()

        # 标尺
        self.ruler = TimelineRuler(self.timeline_engine)
        self.layout.addWidget(self.ruler)

        # 轨道区域
        self._create_track_area()

        # 状态栏
        self._create_status_bar()

        # 加载现有轨道
        self._load_tracks()

    def _create_toolbar(self) -> None:
        """创建工具栏"""
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))

        # 工具按钮
        tools_group = QActionGroup(self)

        select_action = QAction("选择", self)
        select_action.setCheckable(True)
        select_action.setChecked(True)
        select_action.triggered.connect(lambda: self.set_tool(TimelineTool.SELECT))
        tools_group.addAction(select_action)
        self.toolbar.addAction(select_action)

        trim_action = QAction("修剪", self)
        trim_action.setCheckable(True)
        trim_action.triggered.connect(lambda: self.set_tool(TimelineTool.TRIM))
        tools_group.addAction(trim_action)
        self.toolbar.addAction(trim_action)

        razor_action = QAction("切割", self)
        razor_action.setCheckable(True)
        razor_action.triggered.connect(lambda: self.set_tool(TimelineTool.RAZOR))
        tools_group.addAction(razor_action)
        self.toolbar.addAction(razor_action)

        hand_action = QAction("抓手", self)
        hand_action.setCheckable(True)
        hand_action.triggered.connect(lambda: self.set_tool(TimelineTool.HAND))
        tools_group.addAction(hand_action)
        self.toolbar.addAction(hand_action)

        zoom_action = QAction("缩放", self)
        zoom_action.setCheckable(True)
        zoom_action.triggered.connect(lambda: self.set_tool(TimelineTool.ZOOM))
        tools_group.addAction(zoom_action)
        self.toolbar.addAction(zoom_action)

        self.toolbar.addSeparator()

        # 播放控制
        play_action = QAction("播放", self)
        play_action.triggered.connect(self.timeline_engine.start_playback)
        self.toolbar.addAction(play_action)

        pause_action = QAction("暂停", self)
        pause_action.triggered.connect(self.timeline_engine.pause_playback)
        self.toolbar.addAction(pause_action)

        stop_action = QAction("停止", self)
        stop_action.triggered.connect(self.timeline_engine.stop_playback)
        self.toolbar.addAction(stop_action)

        self.toolbar.addSeparator()

        # 缩放控制
        zoom_in_action = QAction("放大", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        self.toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("缩小", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        self.toolbar.addAction(zoom_out_action)

        zoom_fit_action = QAction("适应", self)
        zoom_fit_action.triggered.connect(self.zoom_fit)
        self.toolbar.addAction(zoom_fit_action)

        self.layout.addWidget(self.toolbar)

    def _create_track_area(self) -> None:
        """创建轨道区域"""
        # 主轨道容器
        self.track_container = QWidget()
        self.track_layout = QVBoxLayout(self.track_container)
        self.track_layout.setContentsMargins(0, 0, 0, 0)
        self.track_layout.setSpacing(0)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.track_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.layout.addWidget(scroll_area)

    def _create_status_bar(self) -> None:
        """创建状态栏"""
        self.status_bar = QStatusBar()

        # 时间显示
        self.time_label = QLabel("00:00:00:00")
        self.status_bar.addWidget(self.time_label)

        # 播放状态
        self.playback_label = QLabel("停止")
        self.status_bar.addWidget(self.playback_label)

        # 剪辑数量
        self.clips_label = QLabel("剪辑: 0")
        self.status_bar.addWidget(self.clips_label)

        # 轨道数量
        self.tracks_label = QLabel("轨道: 0")
        self.status_bar.addWidget(self.tracks_label)

        self.layout.addWidget(self.status_bar)

    def _load_tracks(self) -> None:
        """加载轨道"""
        # 清除现有轨道
        for i in reversed(range(self.track_layout.count())):
            widget = self.track_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        # 添加轨道
        for track_id in self.timeline_engine.track_order:
            track = self.timeline_engine.get_track(track_id)
            if track:
                track_widget = TrackWidget(track, self.timeline_engine, self.track_container)
                self.track_layout.addWidget(track_widget)

        # 更新状态栏
        self._update_status_bar()

    def set_tool(self, tool: TimelineTool) -> None:
        """设置工具"""
        self.current_tool = tool

        # 更新鼠标样式
        if tool == TimelineTool.SELECT:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        elif tool == TimelineTool.HAND:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        elif tool == TimelineTool.ZOOM:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def zoom_in(self) -> None:
        """放大"""
        current_scale = self.ruler.pixels_per_second
        self.ruler.set_zoom_level(ZoomLevel.CUSTOM, current_scale * 1.2)

    def zoom_out(self) -> None:
        """缩小"""
        current_scale = self.ruler.pixels_per_second
        self.ruler.set_zoom_level(ZoomLevel.CUSTOM, current_scale * 0.8)

    def zoom_fit(self) -> None:
        """适应窗口"""
        self.ruler.set_zoom_level(ZoomLevel.FIT)

    def _update_status_bar(self) -> None:
        """更新状态栏"""
        # 更新时间显示
        current_time = self.timeline_engine.state.current_time
        timecode = TimeCode.from_seconds(current_time, self.timeline_engine.settings.frame_rate)
        self.time_label.setText(str(timecode))

        # 更新播放状态
        playback_state = self.timeline_engine.state.playback_state.value
        self.playback_label.setText(playback_state)

        # 更新剪辑数量
        total_clips = sum(len(track.clips) for track in self.timeline_engine.tracks.values())
        self.clips_label.setText(f"剪辑: {total_clips}")

        # 更新轨道数量
        total_tracks = len(self.timeline_engine.tracks)
        self.tracks_label.setText(f"轨道: {total_tracks}")

    def _setup_connections(self) -> None:
        """设置连接"""
        # 连接时间线事件
        self.timeline_engine.event_bus.subscribe("playback_state_changed", self._on_playback_state_changed)
        self.timeline_engine.event_bus.subscribe("timeline_seeked", self._on_timeline_seeked)
        self.timeline_engine.event_bus.subscribe("track_created", self._on_track_created)
        self.timeline_engine.event_bus.subscribe("track_deleted", self._on_track_deleted)

        # 定时更新状态栏
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status_bar)
        self.update_timer.start(100)  # 10FPS更新

    def _on_playback_state_changed(self, data: Any) -> None:
        """处理播放状态变更"""
        self._update_status_bar()

    def _on_timeline_seeked(self, data: Any) -> None:
        """处理时间线跳转"""
        self._update_status_bar()

    def _on_track_created(self, data: Any) -> None:
        """处理轨道创建"""
        self._load_tracks()

    def _on_track_deleted(self, data: Any) -> None:
        """处理轨道删除"""
        self._load_tracks()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path:
                # 创建剪辑
                clip = self.clip_manager.create_clip(file_path)
                if clip:
                    # 添加到时间线
                    track = self.timeline_engine.get_tracks_by_type(clip.track_type)[0]
                    self.timeline_engine.add_clip(clip, track.id)

    def keyPressEvent(self, event) -> None:
        """按键事件"""
        if event.key() == Qt.Key.Key_Space:
            # 空格键播放/暂停
            if self.timeline_engine.state.playback_state == PlaybackState.PLAYING:
                self.timeline_engine.pause_playback()
            else:
                self.timeline_engine.start_playback()
        elif event.key() == Qt.Key.Key_Delete:
            # 删除键删除选中剪辑
            pass
        elif event.key() == Qt.Key.Key_Left:
            # 左箭头后退
            self.timeline_engine.seek_to(self.timeline_engine.state.current_time - 0.1)
        elif event.key() == Qt.Key.Key_Right:
            # 右箭头前进
            self.timeline_engine.seek_to(self.timeline_engine.state.current_time + 0.1)
        else:
            super().keyPressEvent(event)

    def cleanup(self) -> None:
        """清理资源"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

        # 清理子组件
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()