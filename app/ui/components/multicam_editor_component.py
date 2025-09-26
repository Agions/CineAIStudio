#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 多摄像机编辑器组件
专业级多摄像机编辑界面，提供实时预览、切换控制和智能分析功能
"""

import os
import json
import threading
import time
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QPushButton, QSlider, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox, QFrame, QSplitter,
    QToolBar, QMenu, QToolButton, QFileDialog,
    QMessageBox, QInputDialog, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QTextEdit, QProgressBar,
    QStatusBar, QToolTip, QApplication, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QListWidget,
    QListWidgetItem, QTabWidget, QRadioButton, QButtonGroup,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsEllipseItem
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QObject, QPoint, QRect, QSize,
    QTimer, QPropertyAnimation, QEasingCurve, QThread,
    pyqtSlot, QMimeData, QPointF, QRectF, QBuffer,
    QThread, QMutex, QWaitCondition, QThreadPool, QRunnable
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QCursor,
    QPixmap, QImage, QMouseEvent, QWheelEvent, QDragEnterEvent,
    QDropEvent, QDrag, QPainterPath, QLinearGradient,
    QKeySequence, QIcon, QMouseEvent, QPaintEvent, QAction,
    QContextMenuEvent, QMovie, QTransform, QFontMetrics,
    QPainterPath, QPolygonF, QRegion
)

from .base_component import BaseComponent, BaseContainer, BasePanel
from ...core.multicam_engine import (
    get_multicam_engine, MultiCamEngine, CameraSource, CameraAngle,
    SyncMethod, SwitchMode, MultiCamProject, MultiCamClip
)
from ...core.timeline_engine import TimelineEngine, TimeCode
from ...core.logger import get_logger
from ...core.event_system import EventBus
from ...utils.error_handler import ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler


class MultiCamDisplayMode(Enum):
    """多摄像机显示模式"""
    GRID = "grid"          # 网格视图
    MAIN_SECONDARY = "main_secondary"  # 主副视图
    SINGLE = "single"      # 单视图
    COMPARISON = "comparison"  # 对比视图
    MOSAIC = "mosaic"      # 马赛克视图


class PreviewQuality(Enum):
    """预览质量"""
    LOW = "low"        # 低质量
    MEDIUM = "medium"  # 中等质量
    HIGH = "high"      # 高质量
    ORIGINAL = "original"  # 原始质量


class CameraWidget(QWidget):
    """摄像机预览组件"""

    camera_selected = pyqtSignal(str)
    camera_double_clicked = pyqtSignal(str)
    sync_request = pyqtSignal(str, float)

    def __init__(self, camera_source: CameraSource, parent=None):
        super().__init__(parent)
        self.camera_source = camera_source
        self.multicam_engine = get_multicam_engine()
        self.logger = get_logger("CameraWidget")

        # UI组件
        self.preview_label = QLabel()
        self.info_label = QLabel()
        self.sync_offset_spin = QDoubleSpinBox()
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.enabled_checkbox = QCheckBox("启用")

        # 预览相关
        self.current_time = 0.0
        self.preview_quality = PreviewQuality.MEDIUM
        self.preview_size = (320, 180)
        self.is_selected = False
        self.is_playing = False

        # 初始化UI
        self._init_ui()
        self._setup_connections()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 预览区域
        self.preview_label.setMinimumSize(320, 180)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #333333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.preview_label)

        # 信息区域
        info_layout = QHBoxLayout()
        self.info_label.setText(f"{self.camera_source.name} ({self.camera_source.camera_angle.value})")
        self.info_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # 控制区域
        control_layout = QGridLayout()

        # 同步偏移
        control_layout.addWidget(QLabel("同步偏移:"), 0, 0)
        self.sync_offset_spin.setRange(-10.0, 10.0)
        self.sync_offset_spin.setSingleStep(0.01)
        self.sync_offset_spin.setSuffix("s")
        self.sync_offset_spin.setValue(self.camera_source.sync_offset)
        control_layout.addWidget(self.sync_offset_spin, 0, 1)

        # 音频增益
        control_layout.addWidget(QLabel("音频增益:"), 1, 0)
        self.gain_slider.setRange(0, 200)
        self.gain_slider.setValue(int(self.camera_source.gain * 100))
        self.gain_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        control_layout.addWidget(self.gain_slider, 1, 1)

        # 启用状态
        self.enabled_checkbox.setChecked(self.camera_source.is_enabled)
        control_layout.addWidget(self.enabled_checkbox, 2, 0, 1, 2)

        layout.addLayout(control_layout)

        # 设置组件样式
        self._update_style()

    def _setup_connections(self) -> None:
        """设置连接"""
        self.sync_offset_spin.valueChanged.connect(self._on_sync_offset_changed)
        self.gain_slider.valueChanged.connect(self._on_gain_changed)
        self.enabled_checkbox.toggled.connect(self._on_enabled_toggled)

    def _update_style(self) -> None:
        """更新样式"""
        if self.is_selected:
            self.setStyleSheet("""
                CameraWidget {
                    background-color: #2a2a2a;
                    border: 2px solid #4a9eff;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                CameraWidget {
                    background-color: #1a1a1a;
                    border: 1px solid #333333;
                    border-radius: 8px;
                }
            """)

    def update_preview(self, timeline_time: float) -> None:
        """更新预览"""
        try:
            self.current_time = timeline_time

            # 获取预览帧
            preview_path = self.multicam_engine.get_camera_preview(
                self.camera_source.id, timeline_time
            )

            if preview_path and os.path.exists(preview_path):
                pixmap = QPixmap(preview_path)
                if not pixmap.isNull():
                    # 调整大小
                    scaled_pixmap = pixmap.scaled(
                        self.preview_size[0], self.preview_size[1],
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled_pixmap)

        except Exception as e:
            self.logger.error(f"更新预览失败: {str(e)}")

    def set_preview_quality(self, quality: PreviewQuality) -> None:
        """设置预览质量"""
        self.preview_quality = quality

        # 更新预览大小
        quality_sizes = {
            PreviewQuality.LOW: (160, 90),
            PreviewQuality.MEDIUM: (320, 180),
            PreviewQuality.HIGH: (640, 360),
            PreviewQuality.ORIGINAL: (1280, 720)
        }
        self.preview_size = quality_sizes.get(quality, (320, 180))
        self.preview_label.setMinimumSize(*self.preview_size)

    def set_selected(self, selected: bool) -> None:
        """设置选中状态"""
        self.is_selected = selected
        self._update_style()

    def _on_sync_offset_changed(self, value: float) -> None:
        """同步偏移改变"""
        self.camera_source.sync_offset = value
        self.sync_request.emit(self.camera_source.id, value)

    def _on_gain_changed(self, value: int) -> None:
        """增益改变"""
        self.camera_source.gain = value / 100.0

    def _on_enabled_toggled(self, checked: bool) -> None:
        """启用状态切换"""
        self.camera_source.is_enabled = checked

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(True)
            self.camera_selected.emit(self.camera_source.id)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """双击事件"""
        self.camera_double_clicked.emit(self.camera_source.id)


class MultiCamTimelineWidget(QWidget):
    """多摄像机时间线组件"""

    def __init__(self, multicam_engine: MultiCamEngine, parent=None):
        super().__init__(parent)
        self.multicam_engine = multicam_engine
        self.logger = get_logger("MultiCamTimelineWidget")

        # 时间线参数
        self.timeline_duration = 0.0
        self.current_time = 0.0
        self.zoom_level = 1.0
        self.scroll_offset = 0.0
        self.pixels_per_second = 100.0

        # 鼠标状态
        self.is_dragging = False
        self.drag_start_time = 0.0
        self.mouse_time = 0.0

        # 初始化UI
        self._init_ui()
        self._setup_connections()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 时间线画布
        self.timeline_canvas = QWidget()
        self.timeline_canvas.setMinimumHeight(100)
        self.timeline_canvas.paintEvent = self._paint_timeline
        layout.addWidget(self.timeline_canvas)

        # 设置鼠标跟踪
        self.setMouseTracking(True)
        self.timeline_canvas.setMouseTracking(True)

    def _setup_connections(self) -> None:
        """设置连接"""
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_timeline)
        self.update_timer.start(50)  # 20 FPS

    def _update_timeline(self) -> None:
        """更新时间线"""
        if self.multicam_engine.current_project:
            self.timeline_duration = self.multicam_engine.current_project.timeline_duration

        # 更新当前时间（从播放器获取）
        # 这里简化处理，实际需要从播放器同步
        self.timeline_canvas.update()

    def _paint_timeline(self, event: QPaintEvent) -> None:
        """绘制时间线"""
        painter = QPainter(self.timeline_canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景
        painter.fillRect(self.timeline_canvas.rect(), QColor(30, 30, 30))

        # 计算可见时间范围
        start_time = self.scroll_offset / self.pixels_per_second
        end_time = start_time + self.timeline_canvas.width() / self.pixels_per_second

        # 绘制时间刻度
        self._draw_time_scale(painter, start_time, end_time)

        # 绘制剪辑段
        self._draw_clips(painter, start_time, end_time)

        # 绘制播放头
        self._draw_playhead(painter)

        # 绘制鼠标位置
        if hasattr(self, '_mouse_pos'):
            self._draw_mouse_time(painter)

    def _draw_time_scale(self, painter: QPainter, start_time: float, end_time: float) -> None:
        """绘制时间刻度"""
        painter.setPen(QPen(QColor(100, 100, 100)))

        # 确定刻度间隔
        if self.zoom_level > 2.0:
            major_interval = 1.0  # 1秒
            minor_interval = 0.1  # 0.1秒
        elif self.zoom_level > 1.0:
            major_interval = 5.0  # 5秒
            minor_interval = 1.0  # 1秒
        else:
            major_interval = 10.0  # 10秒
            minor_interval = 2.0  # 2秒

        # 绘制主刻度
        for time_val in range(int(start_time), int(end_time) + 1, int(major_interval)):
            x = (time_val - start_time) * self.pixels_per_second
            if 0 <= x <= self.timeline_canvas.width():
                painter.drawLine(int(x), 0, int(x), 20)

                # 时间标签
                time_str = TimeCode.from_seconds(time_val, 30.0).to_string()
                painter.setPen(QPen(QColor(200, 200, 200)))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(int(x) + 2, 15, time_str)

        # 绘制次刻度
        painter.setPen(QPen(QColor(60, 60, 60), 1, Qt.PenStyle.DotLine))
        for time_val in range(int(start_time), int(end_time) + 1):
            for minor in range(1, int(major_interval / minor_interval)):
                minor_time = time_val + minor * minor_interval
                x = (minor_time - start_time) * self.pixels_per_second
                if 0 <= x <= self.timeline_canvas.width():
                    painter.drawLine(int(x), 0, int(x), 10)

    def _draw_clips(self, painter: QPainter, start_time: float, end_time: float) -> None:
        """绘制剪辑段"""
        if not self.multicam_engine.current_project:
            return

        project = self.multicam_engine.current_project
        y_pos = 30
        clip_height = 40

        for clip in project.clips:
            if clip.end_time < start_time or clip.start_time > end_time:
                continue

            # 计算剪辑位置
            x = (clip.start_time - start_time) * self.pixels_per_second
            width = clip.duration * self.pixels_per_second

            # 绘制剪辑背景
            clip_color = QColor(80, 120, 160)
            if clip.id == self._get_current_clip_id():
                clip_color = QColor(120, 160, 200)

            painter.fillRect(int(x), y_pos, int(width), clip_height, clip_color)

            # 绘制剪辑边框
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawRect(int(x), y_pos, int(width), clip_height)

            # 绘制剪辑信息
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 9))
            clip_text = f"{clip.start_time:.1f}s - {clip.end_time:.1f}s"
            painter.drawText(int(x) + 5, y_pos + 25, clip_text)

            # 绘制切换点
            self._draw_switch_points(painter, clip, x, y_pos, width, clip_height)

            y_pos += clip_height + 10

    def _draw_switch_points(self, painter: QPainter, clip: MultiCamClip,
                          clip_x: float, clip_y: float, clip_width: float, clip_height: float) -> None:
        """绘制切换点"""
        for switch in clip.camera_switches:
            if clip.start_time <= switch['time'] <= clip.end_time:
                switch_x = clip_x + (switch['time'] - clip.start_time) * self.pixels_per_second

                # 绘制切换标记
                painter.setPen(QPen(QColor(255, 200, 100), 2))
                painter.drawLine(int(switch_x), clip_y, int(switch_x), clip_y + clip_height)

                # 绘制切换类型标记
                if switch['transition_type'] == 'fade':
                    # 淡入淡出标记
                    painter.setBrush(QBrush(QColor(255, 200, 100)))
                    painter.drawEllipse(int(switch_x) - 3, int(clip_y + clip_height / 2) - 3, 6, 6)

    def _draw_playhead(self, painter: QPainter) -> None:
        """绘制播放头"""
        x = (self.current_time - self.scroll_offset / self.pixels_per_second) * self.pixels_per_second

        if 0 <= x <= self.timeline_canvas.width():
            # 播放头线
            painter.setPen(QPen(QColor(255, 100, 100), 2))
            painter.drawLine(int(x), 0, int(x), self.timeline_canvas.height())

            # 播放头三角形
            painter.setBrush(QBrush(QColor(255, 100, 100)))
            triangle = QPolygonF([
                QPointF(x, 0),
                QPointF(x - 5, 10),
                QPointF(x + 5, 10)
            ])
            painter.drawPolygon(triangle)

    def _draw_mouse_time(self, painter: QPainter) -> None:
        """绘制鼠标时间"""
        if hasattr(self, '_mouse_time'):
            painter.setPen(QPen(QColor(255, 255, 100)))
            painter.setFont(QFont("Arial", 8))

            time_str = TimeCode.from_seconds(self._mouse_time, 30.0).to_string()
            painter.drawText(self._mouse_pos.x() + 10, self._mouse_pos.y() - 10, time_str)

    def _get_current_clip_id(self) -> Optional[str]:
        """获取当前剪辑ID"""
        if not self.multicam_engine.current_project:
            return None

        for clip in self.multicam_engine.current_project.clips:
            if clip.start_time <= self.current_time <= clip.end_time:
                return clip.id

        return None

    def time_to_x(self, time: float) -> float:
        """时间转换为X坐标"""
        return (time - self.scroll_offset / self.pixels_per_second) * self.pixels_per_second

    def x_to_time(self, x: float) -> float:
        """X坐标转换为时间"""
        return x / self.pixels_per_second + self.scroll_offset / self.pixels_per_second

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_time = self.current_time

            # 跳转到指定时间
            target_time = self.x_to_time(event.pos().x())
            self.current_time = target_time

            # 通知外部跳转
            self.parent().parent().seek_to_time(target_time)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """鼠标移动事件"""
        self._mouse_pos = event.pos()
        self._mouse_time = self.x_to_time(event.pos().x())

        if self.is_dragging:
            # 拖动播放头
            target_time = self.x_to_time(event.pos().x())
            self.current_time = target_time
            self.parent().parent().seek_to_time(target_time)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件"""
        self.is_dragging = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        """滚轮事件"""
        # 缩放
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_level *= 1.2
            self.pixels_per_second *= 1.2
        else:
            self.zoom_level *= 0.8
            self.pixels_per_second *= 0.8

        self.timeline_canvas.update()

    def set_current_time(self, time: float) -> None:
        """设置当前时间"""
        self.current_time = time


class MultiCamEditorComponent(BasePanel):
    """多摄像机编辑器主组件"""

    # 信号定义
    project_created = pyqtSignal(str)
    camera_added = pyqtSignal(str)
    sync_completed = pyqtSignal()
    switch_performed = pyqtSignal(str, float)
    export_completed = pyqtSignal(str)

    def __init__(self, multicam_engine: Optional[MultiCamEngine] = None, parent=None):
        super().__init__(parent, layout_type="vertical", title="多摄像机编辑器")
        self.multicam_engine = multicam_engine or get_multicam_engine()
        self.logger = get_logger("MultiCamEditorComponent")

        # 显示设置
        self.display_mode = MultiCamDisplayMode.GRID
        self.preview_quality = PreviewQuality.MEDIUM
        self.selected_camera_id: Optional[str] = None
        self.current_time = 0.0
        self.is_playing = False

        # UI组件
        self.toolbar = None
        self.camera_grid = None
        self.preview_area = None
        self.timeline_widget = None
        self.control_panel = None
        self.status_bar = None

        # 初始化
        self._init_component()
        self._setup_connections()
        self._setup_event_handlers()

    def _init_component(self) -> None:
        """初始化组件"""
        # 创建工具栏
        self._create_toolbar()

        # 主布局
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.layout.addWidget(main_splitter)

        # 上部分：预览区域
        preview_container = QWidget()
        preview_layout = QHBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # 摄像机网格
        self._create_camera_grid()
        preview_layout.addWidget(self.camera_grid, 2)

        # 控制面板
        self._create_control_panel()
        preview_layout.addWidget(self.control_panel, 1)

        main_splitter.addWidget(preview_container)

        # 下部分：时间线
        self._create_timeline_widget()
        main_splitter.addWidget(self.timeline_widget)

        # 创建状态栏
        self._create_status_bar()
        self.layout.addWidget(self.status_bar)

    def _create_toolbar(self) -> None:
        """创建工具栏"""
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))

        # 项目操作
        new_project_action = QAction("新建项目", self)
        new_project_action.triggered.connect(self._create_new_project)
        self.toolbar.addAction(new_project_action)

        self.toolbar.addSeparator()

        # 添加摄像机
        add_camera_action = QAction("添加摄像机", self)
        add_camera_action.triggered.connect(self._add_camera_source)
        self.toolbar.addAction(add_camera_action)

        # 同步操作
        sync_menu = QMenu("同步", self)
        sync_audio_action = QAction("音频同步", self)
        sync_audio_action.triggered.connect(lambda: self._synchronize_cameras(SyncMethod.AUDIO_WAVE))
        sync_menu.addAction(sync_audio_action)

        sync_timecode_action = QAction("时间码同步", self)
        sync_timecode_action.triggered.connect(lambda: self._synchronize_cameras(SyncMethod.TIMECODE))
        sync_menu.addAction(sync_timecode_action)

        sync_motion_action = QAction("运动同步", self)
        sync_motion_action.triggered.connect(lambda: self._synchronize_cameras(SyncMethod.MOTION_DETECT))
        sync_menu.addAction(sync_motion_action)

        self.toolbar.addAction(sync_menu.menuAction())

        self.toolbar.addSeparator()

        # 自动切换
        auto_switch_menu = QMenu("自动切换", self)
        auto_cut_action = QAction("自动剪辑", self)
        auto_cut_action.triggered.connect(lambda: self._start_auto_switch(SwitchMode.AUTO_CUT))
        auto_switch_menu.addAction(auto_cut_action)

        auto_mix_action = QAction("自动混合", self)
        auto_mix_action.triggered.connect(lambda: self._start_auto_switch(SwitchMode.AUTO_MIX))
        auto_switch_menu.addAction(auto_mix_action)

        follow_audio_action = QAction("跟随音频", self)
        follow_audio_action.triggered.connect(lambda: self._start_auto_switch(SwitchMode.FOLLOW_AUDIO))
        auto_switch_menu.addAction(follow_audio_action)

        self.toolbar.addAction(auto_switch_menu.menuAction())

        self.toolbar.addSeparator()

        # 显示模式
        display_menu = QMenu("显示模式", self)
        grid_action = QAction("网格视图", self)
        grid_action.triggered.connect(lambda: self._set_display_mode(MultiCamDisplayMode.GRID))
        display_menu.addAction(grid_action)

        main_secondary_action = QAction("主副视图", self)
        main_secondary_action.triggered.connect(lambda: self._set_display_mode(MultiCamDisplayMode.MAIN_SECONDARY))
        display_menu.addAction(main_secondary_action)

        single_action = QAction("单视图", self)
        single_action.triggered.connect(lambda: self._set_display_mode(MultiCamDisplayMode.SINGLE))
        display_menu.addAction(single_action)

        self.toolbar.addAction(display_menu.menuAction())

        self.toolbar.addSeparator()

        # 预览质量
        quality_menu = QMenu("预览质量", self)
        low_quality_action = QAction("低质量", self)
        low_quality_action.triggered.connect(lambda: self._set_preview_quality(PreviewQuality.LOW))
        quality_menu.addAction(low_quality_action)

        medium_quality_action = QAction("中等质量", self)
        medium_quality_action.triggered.connect(lambda: self._set_preview_quality(PreviewQuality.MEDIUM))
        quality_menu.addAction(medium_quality_action)

        high_quality_action = QAction("高质量", self)
        high_quality_action.triggered.connect(lambda: self._set_preview_quality(PreviewQuality.HIGH))
        quality_menu.addAction(high_quality_action)

        self.toolbar.addAction(quality_menu.menuAction())

        self.toolbar.addSeparator()

        # 分析工具
        analyze_action = QAction("分析素材", self)
        analyze_action.triggered.connect(self._analyze_footage)
        self.toolbar.addAction(analyze_action)

        self.toolbar.addSeparator()

        # 导出
        export_action = QAction("导出编辑", self)
        export_action.triggered.connect(self._export_edit)
        self.toolbar.addAction(export_action)

        self.layout.addWidget(self.toolbar)

    def _create_camera_grid(self) -> None:
        """创建摄像机网格"""
        self.camera_grid = QScrollArea()
        self.camera_grid_widget = QWidget()
        self.camera_grid_layout = QGridLayout(self.camera_grid_widget)
        self.camera_grid_layout.setSpacing(10)
        self.camera_grid_layout.setContentsMargins(10, 10, 10, 10)

        self.camera_grid.setWidget(self.camera_grid_widget)
        self.camera_grid.setWidgetResizable(True)

    def _create_control_panel(self) -> None:
        """创建控制面板"""
        self.control_panel = QWidget()
        control_layout = QVBoxLayout(self.control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)

        # 播放控制
        playback_group = QGroupBox("播放控制")
        playback_layout = QHBoxLayout(playback_group)

        self.play_button = QPushButton("播放")
        self.play_button.clicked.connect(self._toggle_playback)
        playback_layout.addWidget(self.play_button)

        self.pause_button = QPushButton("暂停")
        self.pause_button.clicked.connect(self._pause_playback)
        playback_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self._stop_playback)
        playback_layout.addWidget(self.stop_button)

        control_layout.addWidget(playback_group)

        # 切换控制
        switch_group = QGroupBox("切换控制")
        switch_layout = QVBoxLayout(switch_group)

        # 摄像机选择
        self.camera_combo = QComboBox()
        self.camera_combo.currentTextChanged.connect(self._on_camera_selected)
        switch_layout.addWidget(QLabel("选择摄像机:"))
        switch_layout.addWidget(self.camera_combo)

        # 切换按钮
        self.switch_button = QPushButton("切换")
        self.switch_button.clicked.connect(self._switch_camera)
        switch_layout.addWidget(self.switch_button)

        # 切换模式
        self.switch_mode_combo = QComboBox()
        self.switch_mode_combo.addItems([mode.value for mode in SwitchMode])
        self.switch_mode_combo.currentTextChanged.connect(self._on_switch_mode_changed)
        switch_layout.addWidget(QLabel("切换模式:"))
        switch_layout.addWidget(self.switch_mode_combo)

        control_layout.addWidget(switch_group)

        # 同步信息
        sync_group = QGroupBox("同步信息")
        sync_layout = QVBoxLayout(sync_group)

        self.sync_status_label = QLabel("未同步")
        sync_layout.addWidget(self.sync_status_label)

        self.sync_details_label = QLabel("")
        sync_layout.addWidget(self.sync_details_label)

        control_layout.addWidget(sync_group)

        control_layout.addStretch()

    def _create_timeline_widget(self) -> None:
        """创建时间线组件"""
        self.timeline_widget = MultiCamTimelineWidget(self.multicam_engine)

    def _create_status_bar(self) -> None:
        """创建状态栏"""
        self.status_bar = QStatusBar()

        # 项目信息
        self.project_label = QLabel("项目: 无")
        self.status_bar.addWidget(self.project_label)

        # 摄像机数量
        self.camera_count_label = QLabel("摄像机: 0")
        self.status_bar.addWidget(self.camera_count_label)

        # 播放状态
        self.playback_status_label = QLabel("停止")
        self.status_bar.addWidget(self.playback_status_label)

        # 当前时间
        self.time_label = QLabel("00:00:00:00")
        self.status_bar.addWidget(self.time_label)

    def _setup_connections(self) -> None:
        """设置连接"""
        # 播放定时器
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self._update_playback)

        # 预览更新定时器
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self._update_previews)

    def _setup_event_handlers(self) -> None:
        """设置事件处理器"""
        # 多摄像机引擎事件
        self.multicam_engine.event_bus.subscribe("project_created", self._on_project_created)
        self.multicam_engine.event_bus.subscribe("camera_added", self._on_camera_added)
        self.multicam_engine.event_bus.subscribe("sync_completed", self._on_sync_completed)
        self.multicam_engine.event_bus.subscribe("switch_performed", self._on_switch_performed)

    def _create_new_project(self) -> None:
        """创建新项目"""
        dialog = QInputDialog(self)
        dialog.setLabelText("项目名称:")
        dialog.setWindowTitle("新建多摄像机项目")

        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_name = dialog.textValue()
            if project_name:
                project_id = self.multicam_engine.create_project(project_name)
                if project_id:
                    self.project_created.emit(project_id)

    def _add_camera_source(self) -> None:
        """添加摄像机源"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm)")

        if file_dialog.exec() == QDialog.DialogCode.Accepted:
            file_paths = file_dialog.selectedFiles()

            for file_path in file_paths:
                # 输入摄像机名称
                name_dialog = QInputDialog(self)
                name_dialog.setLabelText("摄像机名称:")
                name_dialog.setTextValue(os.path.basename(file_path))
                name_dialog.setWindowTitle("添加摄像机")

                if name_dialog.exec() == QDialog.DialogCode.Accepted:
                    camera_name = name_dialog.textValue()
                    if camera_name:
                        # 输入摄像机角度
                        angle_dialog = QInputDialog(self)
                        angle_dialog.setLabelText("摄像机角度:")
                        angle_dialog.setComboBoxItems([angle.value for angle in CameraAngle])
                        angle_dialog.setWindowTitle("摄像机角度")

                        if angle_dialog.exec() == QDialog.DialogCode.Accepted:
                            angle_value = angle_dialog.textValue()
                            camera_angle = CameraAngle(angle_value)

                            camera_id = self.multicam_engine.add_camera_source(
                                file_path, camera_name, camera_angle
                            )
                            if camera_id:
                                self.camera_added.emit(camera_id)

    def _synchronize_cameras(self, method: SyncMethod) -> None:
        """同步摄像机"""
        if len(self.multicam_engine.camera_sources) < 2:
            QMessageBox.warning(self, "警告", "需要至少2个摄像机源才能进行同步")
            return

        # 选择参考摄像机
        reference_camera_id = None
        if self.selected_camera_id:
            reference_camera_id = self.selected_camera_id
        else:
            camera_names = [
                f"{camera.name} ({camera.camera_angle.value})"
                for camera in self.multicam_engine.camera_sources.values()
            ]
            camera_dialog = QInputDialog(self)
            camera_dialog.setLabelText("选择参考摄像机:")
            camera_dialog.setComboBoxItems(camera_names)
            camera_dialog.setWindowTitle("参考摄像机")

            if camera_dialog.exec() == QDialog.DialogCode.Accepted:
                camera_name = camera_dialog.textValue()
                for camera in self.multicam_engine.camera_sources.values():
                    if f"{camera.name} ({camera.camera_angle.value})" == camera_name:
                        reference_camera_id = camera.id
                        break

        if reference_camera_id:
            success = self.multicam_engine.synchronize_cameras(method, reference_camera_id)
            if success:
                QMessageBox.information(self, "成功", "摄像机同步完成")
                self.sync_completed.emit()

    def _start_auto_switch(self, mode: SwitchMode) -> None:
        """启动自动切换"""
        settings_dialog = AutoSwitchSettingsDialog(mode, self)
        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            settings = settings_dialog.get_settings()
            success = self.multicam_engine.switch_engine.start_auto_switch(mode, settings)
            if success:
                QMessageBox.information(self, "成功", f"自动切换已启动: {mode.value}")

    def _analyze_footage(self) -> None:
        """分析素材"""
        if not self.multicam_engine.camera_sources:
            QMessageBox.warning(self, "警告", "没有可分析的摄像机源")
            return

        # 显示进度对话框
        progress_dialog = QMessageBox(self)
        progress_dialog.setWindowTitle("分析素材")
        progress_dialog.setText("正在分析素材...")
        progress_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress_dialog.show()

        # 在后台线程中执行分析
        def analyze_worker():
            try:
                analysis_results = self.multicam_engine.analyze_footage()

                # 在主线程中显示结果
                QApplication.postEvent(self, AnalysisCompletedEvent(analysis_results))

            except Exception as e:
                self.logger.error(f"素材分析失败: {str(e)}")

        analysis_thread = threading.Thread(target=analyze_worker, daemon=True)
        analysis_thread.start()

    def _export_edit(self) -> None:
        """导出编辑"""
        if not self.multicam_engine.current_project:
            QMessageBox.warning(self, "警告", "没有当前项目")
            return

        # 选择输出文件
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("MP4 文件 (*.mp4)")
        file_dialog.setDefaultSuffix("mp4")

        if file_dialog.exec() == QDialog.DialogCode.Accepted:
            output_path = file_dialog.selectedFiles()[0]

            # 显示导出设置对话框
            export_dialog = ExportSettingsDialog(self)
            if export_dialog.exec() == QDialog.DialogCode.Accepted:
                export_settings = export_dialog.get_settings()

                # 显示进度对话框
                progress_dialog = ExportProgressDialog(self)
                progress_dialog.show()

                # 在后台线程中执行导出
                def export_worker():
                    try:
                        success = self.multicam_engine.export_multicam_edit(
                            output_path, export_settings
                        )

                        # 在主线程中显示结果
                        QApplication.postEvent(self, ExportCompletedEvent(success, output_path))

                    except Exception as e:
                        self.logger.error(f"导出失败: {str(e)}")

                export_thread = threading.Thread(target=export_worker, daemon=True)
                export_thread.start()

    def _toggle_playback(self) -> None:
        """切换播放状态"""
        if self.is_playing:
            self._pause_playback()
        else:
            self._start_playback()

    def _start_playback(self) -> None:
        """开始播放"""
        self.is_playing = True
        self.playback_timer.start(50)  # 20 FPS
        self.preview_timer.start(100)  # 10 FPS
        self.playback_status_label.setText("播放中")

    def _pause_playback(self) -> None:
        """暂停播放"""
        self.is_playing = False
        self.playback_timer.stop()
        self.preview_timer.stop()
        self.playback_status_label.setText("暂停")

    def _stop_playback(self) -> None:
        """停止播放"""
        self.is_playing = False
        self.playback_timer.stop()
        self.preview_timer.stop()
        self.current_time = 0.0
        self.playback_status_label.setText("停止")
        self._update_time_display()

    def _update_playback(self) -> None:
        """更新播放"""
        if self.is_playing:
            self.current_time += 0.05  # 50ms步进
            self._update_time_display()
            self.timeline_widget.set_current_time(self.current_time)

    def _update_previews(self) -> None:
        """更新预览"""
        for i in range(self.camera_grid_layout.count()):
            widget = self.camera_grid_layout.itemAt(i).widget()
            if isinstance(widget, CameraWidget):
                widget.update_preview(self.current_time)

    def _update_time_display(self) -> None:
        """更新时间显示"""
        timecode = TimeCode.from_seconds(self.current_time, 30.0)
        self.time_label.setText(timecode.to_string())

    def _set_display_mode(self, mode: MultiCamDisplayMode) -> None:
        """设置显示模式"""
        self.display_mode = mode
        self._update_camera_grid_layout()

    def _set_preview_quality(self, quality: PreviewQuality) -> None:
        """设置预览质量"""
        self.preview_quality = quality

        # 更新所有摄像机组件的质量设置
        for i in range(self.camera_grid_layout.count()):
            widget = self.camera_grid_layout.itemAt(i).widget()
            if isinstance(widget, CameraWidget):
                widget.set_preview_quality(quality)

    def _update_camera_grid_layout(self) -> None:
        """更新摄像机网格布局"""
        # 清除现有组件
        for i in reversed(range(self.camera_grid_layout.count())):
            widget = self.camera_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        # 重新添加摄像机组件
        cameras = list(self.multicam_engine.camera_sources.values())
        if self.display_mode == MultiCamDisplayMode.GRID:
            # 网格布局
            cols = min(3, len(cameras))
            for i, camera in enumerate(cameras):
                camera_widget = self._create_camera_widget(camera)
                row = i // cols
                col = i % cols
                self.camera_grid_layout.addWidget(camera_widget, row, col)

        elif self.display_mode == MultiCamDisplayMode.MAIN_SECONDARY:
            # 主副视图
            if cameras:
                # 主摄像机
                main_camera = cameras[0]
                main_widget = self._create_camera_widget(main_camera)
                self.camera_grid_layout.addWidget(main_widget, 0, 0)

                # 副摄像机网格
                secondary_grid = QGridLayout()
                secondary_cols = min(3, len(cameras) - 1)
                for i, camera in enumerate(cameras[1:], 1):
                    secondary_widget = self._create_camera_widget(camera)
                    row = (i - 1) // secondary_cols
                    col = (i - 1) % secondary_cols
                    secondary_grid.addWidget(secondary_widget, row, col)

                self.camera_grid_layout.addLayout(secondary_grid, 1, 0)

        elif self.display_mode == MultiCamDisplayMode.SINGLE:
            # 单视图（显示选中的摄像机）
            if self.selected_camera_id:
                selected_camera = self.multicam_engine.camera_sources.get(self.selected_camera_id)
                if selected_camera:
                    camera_widget = self._create_camera_widget(selected_camera)
                    self.camera_grid_layout.addWidget(camera_widget, 0, 0)

    def _create_camera_widget(self, camera: CameraSource) -> CameraWidget:
        """创建摄像机组件"""
        camera_widget = CameraWidget(camera, self.camera_grid_widget)
        camera_widget.set_preview_quality(self.preview_quality)
        camera_widget.camera_selected.connect(self._on_camera_widget_selected)
        camera_widget.camera_double_clicked.connect(self._on_camera_widget_double_clicked)
        camera_widget.sync_request.connect(self._on_sync_request)

        # 设置选中状态
        if camera.id == self.selected_camera_id:
            camera_widget.set_selected(True)

        return camera_widget

    def _on_camera_widget_selected(self, camera_id: str) -> None:
        """摄像机组件选中事件"""
        self.selected_camera_id = camera_id

        # 更新其他组件的选中状态
        for i in range(self.camera_grid_layout.count()):
            widget = self.camera_grid_layout.itemAt(i).widget()
            if isinstance(widget, CameraWidget):
                widget.set_selected(widget.camera_source.id == camera_id)

        # 更新下拉框
        camera = self.multicam_engine.camera_sources.get(camera_id)
        if camera:
            index = self.camera_combo.findText(f"{camera.name} ({camera.camera_angle.value})")
            if index >= 0:
                self.camera_combo.setCurrentIndex(index)

    def _on_camera_widget_double_clicked(self, camera_id: str) -> None:
        """摄像机组件双击事件"""
        # 切换到单视图模式
        self._set_display_mode(MultiCamDisplayMode.SINGLE)

    def _on_sync_request(self, camera_id: str, offset: float) -> None:
        """同步请求事件"""
        # 这里可以添加更复杂的同步逻辑
        self.logger.debug(f"同步请求: {camera_id} -> {offset}s")

    def _on_camera_selected(self, text: str) -> None:
        """摄像机下拉框选择事件"""
        # 查找对应的摄像机ID
        for camera in self.multicam_engine.camera_sources.values():
            if f"{camera.name} ({camera.camera_angle.value})" == text:
                self._on_camera_widget_selected(camera.id)
                break

    def _on_switch_mode_changed(self, text: str) -> None:
        """切换模式改变事件"""
        try:
            mode = SwitchMode(text)
            # 这里可以添加切换模式改变的处理逻辑
        except ValueError:
            pass

    def _switch_camera(self) -> None:
        """切换摄像机"""
        if not self.selected_camera_id:
            QMessageBox.warning(self, "警告", "请先选择摄像机")
            return

        success = self.multicam_engine.switch_camera(
            self.current_time, self.selected_camera_id
        )

        if success:
            self.switch_performed.emit(self.selected_camera_id, self.current_time)

    def _on_project_created(self, data: Any) -> None:
        """项目创建事件"""
        project_id = data.get('project_id')
        project_name = data.get('name')
        self.project_label.setText(f"项目: {project_name}")

    def _on_camera_added(self, data: Any) -> None:
        """摄像机添加事件"""
        camera_id = data.get('camera_id')
        camera_name = data.get('name')
        camera_angle = data.get('camera_angle')

        # 更新摄像机下拉框
        self.camera_combo.addItem(f"{camera_name} ({camera_angle})", camera_id)

        # 更新摄像机网格
        self._update_camera_grid_layout()

        # 更新状态栏
        camera_count = len(self.multicam_engine.camera_sources)
        self.camera_count_label.setText(f"摄像机: {camera_count}")

    def _on_sync_completed(self, data: Any) -> None:
        """同步完成事件"""
        method = data.get('method')
        sync_results = data.get('sync_results', {})

        self.sync_status_label.setText(f"同步完成 ({method})")
        sync_details = []
        for camera_id, offset in sync_results.items():
            camera = self.multicam_engine.camera_sources.get(camera_id)
            if camera:
                sync_details.append(f"{camera.name}: {offset:.2f}s")

        self.sync_details_label.setText("\n".join(sync_details))

    def _on_switch_performed(self, data: Any) -> None:
        """切换执行事件"""
        target_camera = data.get('target_camera')
        timeline_time = data.get('timeline_time')

        camera = self.multicam_engine.camera_sources.get(target_camera)
        if camera:
            self.logger.info(f"切换到摄像机: {camera.name} @ {timeline_time:.2f}s")

    def seek_to_time(self, time: float) -> None:
        """跳转到指定时间"""
        self.current_time = max(0.0, time)
        self._update_time_display()
        self.timeline_widget.set_current_time(self.current_time)
        self._update_previews()

    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return self.multicam_engine.get_engine_status()

    def cleanup(self) -> None:
        """清理资源"""
        if hasattr(self, 'playback_timer'):
            self.playback_timer.stop()
        if hasattr(self, 'preview_timer'):
            self.preview_timer.stop()


class AutoSwitchSettingsDialog(QDialog):
    """自动切换设置对话框"""

    def __init__(self, mode: SwitchMode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.settings = {}

        self.setWindowTitle("自动切换设置")
        self.setModal(True)
        self.resize(400, 300)

        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 设置表单
        form_layout = QFormLayout()

        if self.mode == SwitchMode.AUTO_CUT:
            self.confidence_spin = QDoubleSpinBox()
            self.confidence_spin.setRange(0.0, 1.0)
            self.confidence_spin.setSingleStep(0.1)
            self.confidence_spin.setValue(0.7)
            form_layout.addRow("置信度阈值:", self.confidence_spin)

            self.interval_spin = QDoubleSpinBox()
            self.interval_spin.setRange(0.5, 10.0)
            self.interval_spin.setSingleStep(0.5)
            self.interval_spin.setValue(2.0)
            self.interval_spin.setSuffix("s")
            form_layout.addRow("分析间隔:", self.interval_spin)

        elif self.mode == SwitchMode.AUTO_MIX:
            self.mix_interval_spin = QDoubleSpinBox()
            self.mix_interval_spin.setRange(1.0, 30.0)
            self.mix_interval_spin.setSingleStep(1.0)
            self.mix_interval_spin.setValue(5.0)
            self.mix_interval_spin.setSuffix("s")
            form_layout.addRow("切换间隔:", self.mix_interval_spin)

            self.fade_duration_spin = QDoubleSpinBox()
            self.fade_duration_spin.setRange(0.0, 5.0)
            self.fade_duration_spin.setSingleStep(0.1)
            self.fade_duration_spin.setValue(1.0)
            self.fade_duration_spin.setSuffix("s")
            form_layout.addRow("淡入淡出时长:", self.fade_duration_spin)

        elif self.mode == SwitchMode.FOLLOW_AUDIO:
            self.audio_threshold_spin = QDoubleSpinBox()
            self.audio_threshold_spin.setRange(0.0, 1.0)
            self.audio_threshold_spin.setSingleStep(0.1)
            self.audio_threshold_spin.setValue(0.5)
            form_layout.addRow("音频阈值:", self.audio_threshold_spin)

            self.check_interval_spin = QDoubleSpinBox()
            self.check_interval_spin.setRange(0.1, 2.0)
            self.check_interval_spin.setSingleStep(0.1)
            self.check_interval_spin.setValue(0.5)
            self.check_interval_spin.setSuffix("s")
            form_layout.addRow("检查间隔:", self.check_interval_spin)

        layout.addLayout(form_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_settings(self) -> Dict[str, Any]:
        """获取设置"""
        if self.mode == SwitchMode.AUTO_CUT:
            return {
                'confidence_threshold': self.confidence_spin.value(),
                'analysis_interval': self.interval_spin.value()
            }
        elif self.mode == SwitchMode.AUTO_MIX:
            return {
                'mix_interval': self.mix_interval_spin.value(),
                'fade_duration': self.fade_duration_spin.value()
            }
        elif self.mode == SwitchMode.FOLLOW_AUDIO:
            return {
                'audio_threshold': self.audio_threshold_spin.value(),
                'check_interval': self.check_interval_spin.value()
            }
        else:
            return {}


class ExportSettingsDialog(QDialog):
    """导出设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = {}

        self.setWindowTitle("导出设置")
        self.setModal(True)
        self.resize(400, 300)

        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 设置表单
        form_layout = QFormLayout()

        # 视频编解码器
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["H.264", "H.265", "ProRes", "DNxHD"])
        form_layout.addRow("视频编解码器:", self.codec_combo)

        # 质量
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["高质量", "中等质量", "低质量"])
        form_layout.addRow("质量:", self.quality_combo)

        # 分辨率
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["原始分辨率", "1920x1080", "1280x720", "854x480"])
        form_layout.addRow("分辨率:", self.resolution_combo)

        # 帧率
        self.framerate_spin = QSpinBox()
        self.framerate_spin.setRange(24, 60)
        self.framerate_spin.setValue(30)
        form_layout.addRow("帧率:", self.framerate_spin)

        # 比特率
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(1000, 50000)
        self.bitrate_spin.setValue(8000)
        self.bitrate_spin.setSuffix(" kbps")
        form_layout.addRow("视频比特率:", self.bitrate_spin)

        layout.addLayout(form_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_settings(self) -> Dict[str, Any]:
        """获取设置"""
        return {
            'video_codec': self.codec_combo.currentText(),
            'quality': self.quality_combo.currentText(),
            'resolution': self.resolution_combo.currentText(),
            'framerate': self.framerate_spin.value(),
            'bitrate': self.bitrate_spin.value()
        }


class ExportProgressDialog(QDialog):
    """导出进度对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出进度")
        self.setModal(True)
        self.resize(400, 200)

        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 标签
        self.status_label = QLabel("正在导出...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

    def set_progress(self, value: int) -> None:
        """设置进度"""
        self.progress_bar.setValue(value)

    def set_status(self, text: str) -> None:
        """设置状态文本"""
        self.status_label.setText(text)


# 自定义事件类
class AnalysisCompletedEvent(QEvent):
    """分析完成事件"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, results: Dict[str, Any]):
        super().__init__(AnalysisCompletedEvent.EVENT_TYPE)
        self.results = results


class ExportCompletedEvent(QEvent):
    """导出完成事件"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, success: bool, output_path: str):
        super().__init__(ExportCompletedEvent.EVENT_TYPE)
        self.success = success
        self.output_path = output_path


# 事件处理方法需要添加到MultiCamEditorComponent类中
def event(self, event: QEvent) -> bool:
    """事件处理"""
    if event.type() == AnalysisCompletedEvent.EVENT_TYPE:
        analysis_event = event
        QMessageBox.information(self, "分析完成", f"分析了 {len(analysis_event.results)} 个摄像机")
        return True
    elif event.type() == ExportCompletedEvent.EVENT_TYPE:
        export_event = event
        if export_event.success:
            QMessageBox.information(self, "导出完成", f"文件已保存到: {export_event.output_path}")
        else:
            QMessageBox.warning(self, "导出失败", "导出过程中出现错误")
        return True

    return super().event(event)


# 将事件处理方法添加到类中
MultiCamEditorComponent.event = event