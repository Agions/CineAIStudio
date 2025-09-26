#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio Color Grading Panel
专业色彩分级面板，提供实时色彩调整和预览功能
"""

import os
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
import threading
import time
from queue import Queue
import logging

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QSlider, QComboBox, QSpinBox, QDoubleSpinBox,
                           QTabWidget, QGroupBox, QGridLayout, QSplitter,
                           QScrollArea, QFrame, QColorDialog, QFileDialog,
                           QProgressBar, QCheckBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QRect, QSize
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QBrush, QFont

from ...core.color_grading_engine import (
    ColorGradingEngine, ColorGradingSettings, ColorSpace, HDRStandard,
    ColorGradingTool, ColorWheelAdjustment, ColorCurve, LUTInfo,
    ColorGradePreset, ColorGradingOperation
)
from ...core.color_science import ColorScienceEngine, TransferFunction, ColorProfile
from ...core.logger import get_logger
from ...utils.error_handler import get_global_error_handler


class ScopeType(Enum):
    """示波器类型枚举"""
    WAVEFORM = "waveform"
    VECTORSCOPE = "vectorscope"
    HISTOGRAM = "histogram"
    PARADE = "parade"


class ColorScopeWidget(QWidget):
    """色彩示波器组件"""
    scope_updated = pyqtSignal(np.ndarray)

    def __init__(self, scope_type: ScopeType, parent=None):
        super().__init__(parent)
        self.scope_type = scope_type
        self.logger = get_logger("ColorScopeWidget")
        self.color_engine = get_color_grading_engine()
        self.scope_image = None

        self.setMinimumSize(256, 256)
        self.setMaximumSize(512, 512)

        # 设置背景
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(palette)

        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_scope)
        self.update_timer.start(100)  # 10fps更新

    def update_scope(self):
        """更新示波器显示"""
        try:
            # 获取当前帧（从父组件或其他地方）
            current_frame = self._get_current_frame()
            if current_frame is None:
                return

            # 根据示波器类型生成图像
            if self.scope_type == ScopeType.WAVEFORM:
                self.scope_image = self.color_engine.generate_waveform(current_frame, 256, 256)
            elif self.scope_type == ScopeType.VECTORSCOPE:
                self.scope_image = self.color_engine.generate_vectorscope(current_frame, 256, 256)
            elif self.scope_type == ScopeType.HISTOGRAM:
                self.scope_image = self.color_engine.generate_histogram(current_frame, 256, 100)
            elif self.scope_type == ScopeType.PARADE:
                self.scope_image = self._generate_parade(current_frame, 256, 256)

            # 触发重绘
            self.update()

        except Exception as e:
            self.logger.error(f"示波器更新失败: {str(e)}")

    def _get_current_frame(self) -> Optional[np.ndarray]:
        """获取当前帧"""
        # 这个方法应该从父组件或视频引擎获取当前帧
        # 这里返回一个测试帧
        return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

    def _generate_parade(self, frame: np.ndarray, width: int, height: int) -> np.ndarray:
        """生成RGB示波器"""
        try:
            channels = cv2.split(frame)
            colors = ['red', 'green', 'blue']

            # 创建示波器图像
            parade = np.zeros((height, width, 3), dtype=np.uint8)

            # 为每个通道创建波形
            channel_width = width // 3
            for i, (channel, color) in enumerate(zip(channels, colors)):
                x_offset = i * channel_width
                channel_image = np.zeros((height, channel_width), dtype=np.uint8)

                # 计算通道波形
                for x in range(channel_width):
                    col_idx = int(x * frame.shape[1] / width)
                    col_pixels = channel[:, col_idx]

                    hist = np.histogram(col_pixels, bins=height, range=(0, 256))[0]
                    if hist.max() > 0:
                        hist_normalized = (hist / hist.max() * height).astype(int)
                        for y, intensity in enumerate(hist_normalized):
                            if intensity > 0:
                                channel_image[height-intensity:height, x] = 255

                # 添加到示波器
                color_val = QColor(color).rgb()
                for y in range(height):
                    for x in range(channel_width):
                        if channel_image[y, x] > 0:
                            parade[y, x_offset + x] = [
                                (color_val >> 16) & 0xFF,
                                (color_val >> 8) & 0xFF,
                                color_val & 0xFF
                            ]

            return parade

        except Exception as e:
            self.logger.error(f"RGB示波器生成失败: {str(e)}")
            return np.zeros((height, width, 3), dtype=np.uint8)

    def paintEvent(self, event):
        """绘制示波器"""
        if self.scope_image is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 缩放图像以适应组件
        scaled_image = self.scale_image_to_widget(self.scope_image)
        painter.drawImage(0, 0, scaled_image)

        # 绘制网格
        self.draw_grid(painter)

    def scale_image_to_widget(self, image: np.ndarray) -> QImage:
        """缩放图像以适应组件"""
        h, w = image.shape[:2]
        widget_size = self.size()
        aspect_ratio = w / h
        widget_aspect = widget_size.width() / widget_size.height()

        if aspect_ratio > widget_aspect:
            # 按宽度缩放
            new_w = widget_size.width()
            new_h = int(new_w / aspect_ratio)
        else:
            # 按高度缩放
            new_h = widget_size.height()
            new_w = int(new_h * aspect_ratio)

        if len(image.shape) == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            q_image = QImage(rgb_image.data, w, h, w * 3, QImage.Format_RGB888)
        else:
            q_image = QImage(image.data, w, h, w, QImage.Format_Grayscale8)

        return q_image.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def draw_grid(self, painter: QPainter):
        """绘制网格"""
        pen = QPen(QColor(100, 100, 100, 128))
        pen.setWidth(1)
        painter.setPen(pen)

        widget_size = self.size()
        # 绘制网格线
        for i in range(0, widget_size.width(), 50):
            painter.drawLine(i, 0, i, widget_size.height())
        for i in range(0, widget_size.height(), 50):
            painter.drawLine(0, i, widget_size.width(), i)

        # 绘制边框
        pen.setColor(QColor(200, 200, 200, 255))
        painter.setPen(pen)
        painter.drawRect(0, 0, widget_size.width() - 1, widget_size.height() - 1)


class ColorWheelWidget(QWidget):
    """色轮调整组件"""
    wheel_changed = pyqtSignal(ColorWheelAdjustment)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("ColorWheelWidget")
        self.wheel_type = "shadows"  # shadows, midtones, highlights
        self.adjustment = ColorWheelAdjustment()
        self.dragging = False
        self.center_point = None
        self.radius = 0

        self.setMinimumSize(200, 200)
        self.setMaximumSize(300, 300)

        # 设置背景
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.darkGray)
        self.setPalette(palette)

    def set_wheel_type(self, wheel_type: str):
        """设置色轮类型"""
        self.wheel_type = wheel_type
        self.update()

    def set_adjustment(self, adjustment: ColorWheelAdjustment):
        """设置调整参数"""
        self.adjustment = adjustment
        self.update()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.update_wheel_position(event.pos())

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging:
            self.update_wheel_position(event.pos())

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.wheel_changed.emit(self.adjustment)

    def update_wheel_position(self, pos):
        """更新色轮位置"""
        if self.center_point is None:
            return

        # 计算相对于中心点的位置
        dx = pos.x() - self.center_point.x()
        dy = pos.y() - self.center_point.y()

        # 计算极坐标
        distance = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)

        # 限制在半径内
        if distance > self.radius:
            distance = self.radius

        # 计算调整值
        hue_shift = angle / (2 * np.pi)  # -0.5 to 0.5
        saturation = distance / self.radius  # 0 to 1
        lift_gamma_gain = (self.radius - distance) / self.radius  # 1 to 0

        # 更新调整参数
        if self.wheel_type == "shadows":
            self.adjustment.shadows = (hue_shift, saturation, lift_gamma_gain - 0.5)
        elif self.wheel_type == "midtones":
            self.adjustment.midtones = (hue_shift, saturation, lift_gamma_gain - 0.5)
        elif self.wheel_type == "highlights":
            self.adjustment.highlights = (hue_shift, saturation, lift_gamma_gain - 0.5)

        self.update()

    def resizeEvent(self, event):
        """调整大小事件"""
        super().resizeEvent(event)
        self.center_point = QPoint(self.width() // 2, self.height() // 2)
        self.radius = min(self.width(), self.height()) // 2 - 10

    def paintEvent(self, event):
        """绘制色轮"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制色轮背景
        self.draw_color_wheel(painter)

        # 绘制控制点
        self.draw_control_points(painter)

        # 绘制标签
        self.draw_labels(painter)

    def draw_color_wheel(self, painter: QPainter):
        """绘制色轮"""
        # 创建径向渐变
        gradient = QRadialGradient(self.center_point, self.radius)

        # 添加色轮颜色
        for i in range(360):
            angle = i * np.pi / 180
            color = QColor.fromHsv(i, 255, 255)
            gradient.setColorAt(i / 360.0, color)

        # 绘制色轮
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.center_point, self.radius, self.radius)

        # 绘制中心圆
        painter.setBrush(QBrush(Qt.darkGray))
        painter.drawEllipse(self.center_point, self.radius // 2, self.radius // 2)

    def draw_control_points(self, painter: QPainter):
        """绘制控制点"""
        # 根据当前色轮类型绘制控制点
        if self.wheel_type == "shadows":
            values = self.adjustment.shadows
        elif self.wheel_type == "midtones":
            values = self.adjustment.midtones
        elif self.wheel_type == "highlights":
            values = self.adjustment.highlights
        else:
            return

        # 计算控制点位置
        hue_shift, saturation, lift_gamma_gain = values
        angle = hue_shift * 2 * np.pi
        distance = saturation * self.radius

        control_x = self.center_point.x() + distance * np.cos(angle)
        control_y = self.center_point.y() + distance * np.sin(angle)

        # 绘制控制点
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(QPoint(int(control_x), int(control_y)), 8, 8)

    def draw_labels(self, painter: QPainter):
        """绘制标签"""
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(QFont("Arial", 10))

        # 绘制色轮类型标签
        label_text = self.wheel_type.capitalize()
        text_rect = painter.fontMetrics().boundingRect(label_text)
        text_x = self.center_point.x() - text_rect.width() // 2
        text_y = self.center_point.y() + text_rect.height() // 2
        painter.drawText(text_x, text_y, label_text)


class CurveEditorWidget(QWidget):
    """曲线编辑器组件"""
    curve_changed = pyqtSignal(ColorCurve)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("CurveEditorWidget")
        self.curve = ColorCurve(curve_type="luma")
        self.points = []
        self.dragging_point = None
        self.grid_size = 10

        self.setMinimumSize(300, 300)
        self.setMaximumSize(400, 400)

        # 设置背景
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(palette)

        # 初始化曲线点
        self.init_default_points()

    def init_default_points(self):
        """初始化默认曲线点"""
        self.points = [
            QPoint(0, 255),    # 左下角
            QPoint(255, 0)     # 右上角
        ]

    def set_curve(self, curve: ColorCurve):
        """设置曲线"""
        self.curve = curve
        # 从曲线数据中加载点
        self.points = []
        for curve_point in curve.points:
            x = int(curve_point.x * 255)
            y = int((1 - curve_point.y) * 255)  # 反转Y坐标
            self.points.append(QPoint(x, y))
        self.update()

    def get_curve(self) -> ColorCurve:
        """获取当前曲线"""
        # 将点转换为曲线数据
        curve_points = []
        for point in self.points:
            curve_point = CurvePoint(
                x=point.x() / 255.0,
                y=1 - point.y() / 255.0  # 反转Y坐标
            )
            curve_points.append(curve_point)

        return ColorCurve(
            curve_type=self.curve.curve_type,
            points=curve_points,
            spline_degree=self.curve.spline_degree
        )

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击了现有点
            for i, point in enumerate(self.points):
                if (event.pos() - point).manhattanLength() < 10:
                    self.dragging_point = i
                    return

            # 添加新点
            self.points.append(event.pos())
            self.dragging_point = len(self.points) - 1
            self.update_curve()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging_point is not None:
            # 限制点在画布内
            x = max(0, min(255, event.pos().x()))
            y = max(0, min(255, event.pos().y()))
            self.points[self.dragging_point] = QPoint(x, y)
            self.update()
            self.update_curve()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging_point = None

    def mouseDoubleClickEvent(self, event):
        """双击删除点"""
        if event.button() == Qt.LeftButton:
            # 检查是否双击了现有点
            for i, point in enumerate(self.points):
                if (event.pos() - point).manhattanLength() < 10:
                    if len(self.points) > 2:  # 至少保留两个点
                        self.points.pop(i)
                        self.update_curve()
                    break

    def update_curve(self):
        """更新曲线并发出信号"""
        self.curve_changed.emit(self.get_curve())

    def paintEvent(self, event):
        """绘制曲线编辑器"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制网格
        self.draw_grid(painter)

        # 绘制曲线
        self.draw_curve(painter)

        # 绘制控制点
        self.draw_points(painter)

        # 绘制坐标轴
        self.draw_axes(painter)

    def draw_grid(self, painter: QPainter):
        """绘制网格"""
        painter.setPen(QPen(QColor(50, 50, 50), 1))

        # 绘制垂直线
        for i in range(0, 256, self.grid_size):
            x = self.scale_x(i)
            painter.drawLine(x, 0, x, self.height())

        # 绘制水平线
        for i in range(0, 256, self.grid_size):
            y = self.scale_y(i)
            painter.drawLine(0, y, self.width(), y)

    def draw_curve(self, painter: QPainter):
        """绘制曲线"""
        if len(self.points) < 2:
            return

        painter.setPen(QPen(QColor(255, 255, 255), 2))

        # 按X坐标排序点
        sorted_points = sorted(self.points, key=lambda p: p.x())

        # 绘制曲线
        path = QPainterPath()
        path.moveTo(self.scale_x(sorted_points[0].x()), self.scale_y(sorted_points[0].y()))

        for i in range(1, len(sorted_points)):
            point = sorted_points[i]
            path.lineTo(self.scale_x(point.x()), self.scale_y(point.y()))

        painter.drawPath(path)

    def draw_points(self, painter: QPainter):
        """绘制控制点"""
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(QPen(Qt.black, 2))

        for point in self.points:
            x = self.scale_x(point.x())
            y = self.scale_y(point.y())
            painter.drawEllipse(QPoint(x, y), 6, 6)

    def draw_axes(self, painter: QPainter):
        """绘制坐标轴"""
        painter.setPen(QPen(QColor(200, 200, 200), 1))

        # X轴
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

        # Y轴
        painter.drawLine(0, 0, 0, self.height())

        # 绘制标签
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(QFont("Arial", 8))

        # X轴标签
        for i in range(0, 256, 64):
            x = self.scale_x(i)
            painter.drawText(x - 10, self.height() - 5, str(i))

        # Y轴标签
        for i in range(0, 256, 64):
            y = self.scale_y(i)
            painter.drawText(5, y + 5, str(255 - i))

    def scale_x(self, x: int) -> int:
        """缩放X坐标"""
        margin = 30
        return margin + int(x * (self.width() - 2 * margin) / 255)

    def scale_y(self, y: int) -> int:
        """缩放Y坐标"""
        margin = 30
        return margin + int((255 - y) * (self.height() - 2 * margin) / 255)


class ColorGradingPanel(QWidget):
    """色彩分级面板主组件"""
    grade_applied = pyqtSignal()
    preview_updated = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("ColorGradingPanel")
        self.error_handler = get_global_error_handler()
        self.color_engine = get_color_grading_engine()
        self.color_science = get_color_science_engine()

        # 当前设置
        self.current_frame = None
        self.preview_enabled = True
        self.real_time_update = True

        # 初始化UI
        self.init_ui()

        # 连接信号
        self.connect_signals()

        # 启动预览定时器
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_timer.start(50)  # 20fps更新

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)

        # 左侧控制面板
        left_panel = self.create_control_panel()
        main_splitter.addWidget(left_panel)

        # 右侧预览和示波器面板
        right_panel = self.create_preview_panel()
        main_splitter.addWidget(right_panel)

        # 设置分割器比例
        main_splitter.setSizes([400, 600])

        # 底部按钮
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 创建标签页
        tab_widget = QTabWidget()

        # 基础调整标签页
        basic_tab = self.create_basic_adjustments_tab()
        tab_widget.addTab(basic_tab, "基础调整")

        # 色轮标签页
        wheel_tab = self.create_wheel_tab()
        tab_widget.addTab(wheel_tab, "色轮")

        # 曲线标签页
        curve_tab = self.create_curve_tab()
        tab_widget.addTab(curve_tab, "曲线")

        # LUT标签页
        lut_tab = self.create_lut_tab()
        tab_widget.addTab(lut_tab, "LUT")

        # 色彩科学标签页
        science_tab = self.create_science_tab()
        tab_widget.addTab(science_tab, "色彩科学")

        layout.addWidget(tab_widget)

        return panel

    def create_basic_adjustments_tab(self) -> QWidget:
        """创建基础调整标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 曝光调整
        exposure_group = QGroupBox("曝光")
        exposure_layout = QGridLayout(exposure_group)

        self.exposure_slider = self.create_slider("曝光", -2.0, 2.0, 0.0, 0.1)
        exposure_layout.addWidget(self.exposure_slider['label'], 0, 0)
        exposure_layout.addWidget(self.exposure_slider['slider'], 0, 1)
        exposure_layout.addWidget(self.exposure_slider['value'], 0, 2)

        self.contrast_slider = self.create_slider("对比度", 0.0, 2.0, 1.0, 0.1)
        exposure_layout.addWidget(self.contrast_slider['label'], 1, 0)
        exposure_layout.addWidget(self.contrast_slider['slider'], 1, 1)
        exposure_layout.addWidget(self.contrast_slider['value'], 1, 2)

        self.brightness_slider = self.create_slider("亮度", -1.0, 1.0, 0.0, 0.1)
        exposure_layout.addWidget(self.brightness_slider['label'], 2, 0)
        exposure_layout.addWidget(self.brightness_slider['slider'], 2, 1)
        exposure_layout.addWidget(self.brightness_slider['value'], 2, 2)

        layout.addWidget(exposure_group)

        # 色彩调整
        color_group = QGroupBox("色彩")
        color_layout = QGridLayout(color_group)

        self.saturation_slider = self.create_slider("饱和度", 0.0, 2.0, 1.0, 0.1)
        color_layout.addWidget(self.saturation_slider['label'], 0, 0)
        color_layout.addWidget(self.saturation_slider['slider'], 0, 1)
        color_layout.addWidget(self.saturation_slider['value'], 0, 2)

        self.vibrance_slider = self.create_slider("鲜艳度", 0.0, 2.0, 1.0, 0.1)
        color_layout.addWidget(self.vibrance_slider['label'], 1, 0)
        color_layout.addWidget(self.vibrance_slider['slider'], 1, 1)
        color_layout.addWidget(self.vibrance_slider['value'], 1, 2)

        self.hue_slider = self.create_slider("色相", -180.0, 180.0, 0.0, 1.0)
        color_layout.addWidget(self.hue_slider['label'], 2, 0)
        color_layout.addWidget(self.hue_slider['slider'], 2, 1)
        color_layout.addWidget(self.hue_slider['value'], 2, 2)

        layout.addWidget(color_group)

        # 阴影高光
        shadow_group = QGroupBox("阴影/高光")
        shadow_layout = QGridLayout(shadow_group)

        self.shadows_slider = self.create_slider("阴影", -1.0, 1.0, 0.0, 0.1)
        shadow_layout.addWidget(self.shadows_slider['label'], 0, 0)
        shadow_layout.addWidget(self.shadows_slider['slider'], 0, 1)
        shadow_layout.addWidget(self.shadows_slider['value'], 0, 2)

        self.highlights_slider = self.create_slider("高光", -1.0, 1.0, 0.0, 0.1)
        shadow_layout.addWidget(self.highlights_slider['label'], 1, 0)
        shadow_layout.addWidget(self.highlights_slider['slider'], 1, 1)
        shadow_layout.addWidget(self.highlights_slider['value'], 1, 2)

        layout.addWidget(shadow_group)

        layout.addStretch()

        return tab

    def create_wheel_tab(self) -> QWidget:
        """创建色轮标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 色轮类型选择
        wheel_type_group = QGroupBox("色轮类型")
        wheel_type_layout = QHBoxLayout(wheel_type_group)

        self.wheel_type_buttons = []
        wheel_types = ["shadows", "midtones", "highlights"]
        wheel_labels = ["阴影", "中间调", "高光"]

        for wheel_type, label in zip(wheel_types, wheel_labels):
            radio = QRadioButton(label)
            radio.wheel_type = wheel_type
            if wheel_type == "midtones":
                radio.setChecked(True)
            radio.toggled.connect(self.on_wheel_type_changed)
            wheel_type_layout.addWidget(radio)
            self.wheel_type_buttons.append(radio)

        layout.addWidget(wheel_type_group)

        # 色轮组件
        self.color_wheel = ColorWheelWidget()
        self.color_wheel.wheel_changed.connect(self.on_wheel_changed)
        layout.addWidget(self.color_wheel)

        # 色轮参数
        wheel_params_group = QGroupBox("参数")
        wheel_params_layout = QGridLayout(wheel_params_group)

        self.wheel_hue_spin = QDoubleSpinBox()
        self.wheel_hue_spin.setRange(-0.5, 0.5)
        self.wheel_hue_spin.setSingleStep(0.01)
        self.wheel_hue_spin.setDecimals(3)
        wheel_params_layout.addWidget(QLabel("色相偏移:"), 0, 0)
        wheel_params_layout.addWidget(self.wheel_hue_spin, 0, 1)

        self.wheel_sat_spin = QDoubleSpinBox()
        self.wheel_sat_spin.setRange(0.0, 1.0)
        self.wheel_sat_spin.setSingleStep(0.01)
        self.wheel_sat_spin.setDecimals(3)
        wheel_params_layout.addWidget(QLabel("饱和度:"), 1, 0)
        wheel_params_layout.addWidget(self.wheel_sat_spin, 1, 1)

        self.wheel_lift_spin = QDoubleSpinBox()
        self.wheel_lift_spin.setRange(-0.5, 0.5)
        self.wheel_lift_spin.setSingleStep(0.01)
        self.wheel_lift_spin.setDecimals(3)
        wheel_params_layout.addWidget(QLabel("亮度:"), 2, 0)
        wheel_params_layout.addWidget(self.wheel_lift_spin, 2, 1)

        layout.addWidget(wheel_params_group)

        layout.addStretch()

        return tab

    def create_curve_tab(self) -> QWidget:
        """创建曲线标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 曲线类型选择
        curve_type_group = QGroupBox("曲线类型")
        curve_type_layout = QHBoxLayout(curve_type_group)

        self.curve_type_combo = QComboBox()
        self.curve_type_combo.addItems(["亮度", "红色", "绿色", "蓝色", "RGB"])
        self.curve_type_combo.currentTextChanged.connect(self.on_curve_type_changed)
        curve_type_layout.addWidget(QLabel("类型:"))
        curve_type_layout.addWidget(self.curve_type_combo)

        layout.addWidget(curve_type_group)

        # 曲线编辑器
        self.curve_editor = CurveEditorWidget()
        self.curve_editor.curve_changed.connect(self.on_curve_changed)
        layout.addWidget(self.curve_editor)

        # 曲线参数
        curve_params_group = QGroupBox("参数")
        curve_params_layout = QGridLayout(curve_params_group)

        self.curve_spline_spin = QSpinBox()
        self.curve_spline_spin.setRange(1, 5)
        self.curve_spline_spin.setValue(3)
        curve_params_layout.addWidget(QLabel("样条度数:"), 0, 0)
        curve_params_layout.addWidget(self.curve_spline_spin, 0, 1)

        layout.addWidget(curve_params_group)

        layout.addStretch()

        return tab

    def create_lut_tab(self) -> QWidget:
        """创建LUT标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # LUT文件选择
        lut_file_group = QGroupBox("LUT文件")
        lut_file_layout = QHBoxLayout(lut_file_group)

        self.lut_path_edit = QLineEdit()
        self.lut_path_edit.setReadOnly(True)
        lut_file_layout.addWidget(self.lut_path_edit)

        self.load_lut_button = QPushButton("加载LUT")
        self.load_lut_button.clicked.connect(self.on_load_lut)
        lut_file_layout.addWidget(self.load_lut_button)

        layout.addWidget(lut_file_group)

        # LUT参数
        lut_params_group = QGroupBox("LUT参数")
        lut_params_layout = QGridLayout(lut_params_group)

        self.lut_size_combo = QComboBox()
        self.lut_size_combo.addItems(["17", "33", "65"])
        self.lut_size_combo.setCurrentText("33")
        lut_params_layout.addWidget(QLabel("尺寸:"), 0, 0)
        lut_params_layout.addWidget(self.lut_size_combo, 0, 1)

        self.lut_format_combo = QComboBox()
        self.lut_format_combo.addItems(["CUBE", "3DL"])
        lut_params_layout.addWidget(QLabel("格式:"), 1, 0)
        lut_params_layout.addWidget(self.lut_format_combo, 1, 1)

        layout.addWidget(lut_params_group)

        # LUT强度
        lut_intensity_group = QGroupBox("LUT强度")
        lut_intensity_layout = QHBoxLayout(lut_intensity_group)

        self.lut_intensity_slider = self.create_slider("强度", 0.0, 1.0, 1.0, 0.01)
        lut_intensity_layout.addWidget(self.lut_intensity_slider['label'])
        lut_intensity_layout.addWidget(self.lut_intensity_slider['slider'])
        lut_intensity_layout.addWidget(self.lut_intensity_slider['value'])

        layout.addWidget(lut_intensity_group)

        # 内置LUT
        builtin_lut_group = QGroupBox("内置LUT")
        builtin_lut_layout = QVBoxLayout(builtin_lut_group)

        self.builtin_lut_list = QComboBox()
        self.builtin_lut_list.addItems([
            "电影风格", "复古风格", "鲜艳风格",
            "黑白风格", "暖色调", "冷色调"
        ])
        builtin_lut_layout.addWidget(self.builtin_lut_list)

        self.apply_builtin_lut_button = QPushButton("应用内置LUT")
        self.apply_builtin_lut_button.clicked.connect(self.on_apply_builtin_lut)
        builtin_lut_layout.addWidget(self.apply_builtin_lut_button)

        layout.addWidget(builtin_lut_group)

        layout.addStretch()

        return tab

    def create_science_tab(self) -> QWidget:
        """创建色彩科学标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 色彩空间
        color_space_group = QGroupBox("色彩空间")
        color_space_layout = QGridLayout(color_space_group)

        self.input_space_combo = QComboBox()
        self.input_space_combo.addItems([space.value for space in ColorSpace])
        color_space_layout.addWidget(QLabel("输入空间:"), 0, 0)
        color_space_layout.addWidget(self.input_space_combo, 0, 1)

        self.output_space_combo = QComboBox()
        self.output_space_combo.addItems([space.value for space in ColorSpace])
        self.output_space_combo.setCurrentText("rec709")
        color_space_layout.addWidget(QLabel("输出空间:"), 1, 0)
        color_space_layout.addWidget(self.output_space_combo, 1, 1)

        layout.addWidget(color_space_group)

        # HDR设置
        hdr_group = QGroupBox("HDR设置")
        hdr_layout = QGridLayout(hdr_group)

        self.hdr_standard_combo = QComboBox()
        self.hdr_standard_combo.addItems([standard.value for standard in HDRStandard])
        self.hdr_standard_combo.setCurrentText("none")
        hdr_layout.addWidget(QLabel("HDR标准:"), 0, 0)
        hdr_layout.addWidget(self.hdr_standard_combo, 0, 1)

        self.hdr_to_sdr_button = QPushButton("HDR转SDR")
        self.hdr_to_sdr_button.clicked.connect(self.on_hdr_to_sdr)
        hdr_layout.addWidget(self.hdr_to_sdr_button, 1, 0, 1, 2)

        layout.addWidget(hdr_group)

        # 色彩匹配
        match_group = QGroupBox("色彩匹配")
        match_layout = QGridLayout(match_group)

        self.match_method_combo = QComboBox()
        self.match_method_combo.addItems([
            "直方图匹配", "颜色传递", "Reinhard匹配"
        ])
        match_layout.addWidget(QLabel("匹配方法:"), 0, 0)
        match_layout.addWidget(self.match_method_combo, 0, 1)

        self.color_match_button = QPushButton("应用色彩匹配")
        self.color_match_button.clicked.connect(self.on_color_match)
        match_layout.addWidget(self.color_match_button, 1, 0, 1, 2)

        layout.addWidget(match_group)

        # 色彩分析
        analysis_group = QGroupBox("色彩分析")
        analysis_layout = QVBoxLayout(analysis_group)

        self.analyze_color_button = QPushButton("分析色彩")
        self.analyze_color_button.clicked.connect(self.on_analyze_color)
        analysis_layout.addWidget(self.analyze_color_button)

        self.color_analysis_text = QTextEdit()
        self.color_analysis_text.setReadOnly(True)
        self.color_analysis_text.setMaximumHeight(150)
        analysis_layout.addWidget(self.color_analysis_text)

        layout.addWidget(analysis_group)

        layout.addStretch()

        return tab

    def create_preview_panel(self) -> QWidget:
        """创建预览面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 预览控制
        preview_control_group = QGroupBox("预览控制")
        preview_control_layout = QHBoxLayout(preview_control_group)

        self.preview_checkbox = QCheckBox("实时预览")
        self.preview_checkbox.setChecked(True)
        self.preview_checkbox.toggled.connect(self.on_preview_toggled)
        preview_control_layout.addWidget(self.preview_checkbox)

        self.split_view_checkbox = QCheckBox("分割视图")
        preview_control_layout.addWidget(self.split_view_checkbox)

        self.before_after_button = QPushButton("前后对比")
        preview_control_layout.addWidget(self.before_after_button)

        layout.addWidget(preview_control_group)

        # 预览区域
        preview_splitter = QSplitter(Qt.Vertical)
        layout.addWidget(preview_splitter)

        # 视频预览
        self.preview_label = QLabel("视频预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("background-color: #1a1a1a; color: white;")
        preview_splitter.addWidget(self.preview_label)

        # 示波器区域
        scope_widget = QWidget()
        scope_layout = QVBoxLayout(scope_widget)

        # 示波器标签页
        scope_tab_widget = QTabWidget()

        # 波形图
        self.waveform_widget = ColorScopeWidget(ScopeType.WAVEFORM)
        scope_tab_widget.addTab(self.waveform_widget, "波形图")

        # 矢量图
        self.vectorscope_widget = ColorScopeWidget(ScopeType.VECTORSCOPE)
        scope_tab_widget.addTab(self.vectorscope_widget, "矢量图")

        # 直方图
        self.histogram_widget = ColorScopeWidget(ScopeType.HISTOGRAM)
        scope_tab_widget.addTab(self.histogram_widget, "直方图")

        # RGB示波器
        self.parade_widget = ColorScopeWidget(ScopeType.PARADE)
        scope_tab_widget.addTab(self.parade_widget, "RGB")

        scope_layout.addWidget(scope_tab_widget)
        preview_splitter.addWidget(scope_widget)

        # 设置分割器比例
        preview_splitter.setSizes([400, 200])

        return panel

    def create_bottom_panel(self) -> QWidget:
        """创建底部面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # 预设管理
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["选择预设...", "电影风格", "复古风格", "鲜艳风格"])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        layout.addWidget(self.preset_combo)

        self.save_preset_button = QPushButton("保存预设")
        self.save_preset_button.clicked.connect(self.on_save_preset)
        layout.addWidget(self.save_preset_button)

        layout.addStretch()

        # 操作按钮
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.on_reset)
        layout.addWidget(self.reset_button)

        self.apply_button = QPushButton("应用")
        self.apply_button.clicked.connect(self.on_apply)
        layout.addWidget(self.apply_button)

        self.export_button = QPushButton("导出LUT")
        self.export_button.clicked.connect(self.on_export_lut)
        layout.addWidget(self.export_button)

        return panel

    def create_slider(self, label: str, min_val: float, max_val: float,
                      default_val: float, step: float) -> Dict[str, QWidget]:
        """创建滑块组件"""
        widget = {}

        widget['label'] = QLabel(f"{label}:")

        widget['slider'] = QSlider(Qt.Horizontal)
        widget['slider'].setMinimum(int(min_val * 100))
        widget['slider'].setMaximum(int(max_val * 100))
        widget['slider'].setValue(int(default_val * 100))
        widget['slider'].setSingleStep(int(step * 100))

        widget['value'] = QLabel(f"{default_val:.2f}")

        # 连接信号
        widget['slider'].valueChanged.connect(
            lambda value: widget['value'].setText(f"{value / 100:.2f}")
        )

        return widget

    def connect_signals(self):
        """连接信号"""
        # 基础调整滑块
        self.exposure_slider['slider'].valueChanged.connect(self.on_basic_adjustment_changed)
        self.contrast_slider['slider'].valueChanged.connect(self.on_basic_adjustment_changed)
        self.brightness_slider['slider'].valueChanged.connect(self.on_basic_adjustment_changed)
        self.saturation_slider['slider'].valueChanged.connect(self.on_basic_adjustment_changed)
        self.vibrance_slider['slider'].valueChanged.connect(self.on_basic_adjustment_changed)
        self.hue_slider['slider'].valueChanged.connect(self.on_basic_adjustment_changed)
        self.shadows_slider['slider'].valueChanged.connect(self.on_basic_adjustment_changed)
        self.highlights_slider['slider'].valueChanged.connect(self.on_basic_adjustment_changed)

        # LUT强度滑块
        self.lut_intensity_slider['slider'].valueChanged.connect(self.on_basic_adjustment_changed)

        # 色轮参数
        self.wheel_hue_spin.valueChanged.connect(self.on_wheel_param_changed)
        self.wheel_sat_spin.valueChanged.connect(self.on_wheel_param_changed)
        self.wheel_lift_spin.valueChanged.connect(self.on_wheel_param_changed)

    def on_basic_adjustment_changed(self):
        """基础调整改变"""
        if not self.real_time_update:
            return

        self.update_preview()

    def on_wheel_type_changed(self, checked):
        """色轮类型改变"""
        if not checked:
            return

        sender = self.sender()
        if hasattr(sender, 'wheel_type'):
            self.color_wheel.set_wheel_type(sender.wheel_type)
            self.update_wheel_params()

    def on_wheel_changed(self, adjustment: ColorWheelAdjustment):
        """色轮改变"""
        self.update_wheel_params()
        if self.real_time_update:
            self.update_preview()

    def on_wheel_param_changed(self):
        """色轮参数改变"""
        # 更新色轮调整
        current_adjustment = self.color_wheel.adjustment

        if self.color_wheel.wheel_type == "shadows":
            current_adjustment.shadows = (
                self.wheel_hue_spin.value(),
                self.wheel_sat_spin.value(),
                self.wheel_lift_spin.value()
            )
        elif self.color_wheel.wheel_type == "midtones":
            current_adjustment.midtones = (
                self.wheel_hue_spin.value(),
                self.wheel_sat_spin.value(),
                self.wheel_lift_spin.value()
            )
        elif self.color_wheel.wheel_type == "highlights":
            current_adjustment.highlights = (
                self.wheel_hue_spin.value(),
                self.wheel_sat_spin.value(),
                self.wheel_lift_spin.value()
            )

        self.color_wheel.set_adjustment(current_adjustment)
        self.color_wheel.update()

        if self.real_time_update:
            self.update_preview()

    def update_wheel_params(self):
        """更新色轮参数显示"""
        adjustment = self.color_wheel.adjustment

        if self.color_wheel.wheel_type == "shadows":
            hue, sat, lift = adjustment.shadows
        elif self.color_wheel.wheel_type == "midtones":
            hue, sat, gamma = adjustment.midtones
        elif self.color_wheel.wheel_type == "highlights":
            hue, sat, gain = adjustment.highlights
        else:
            return

        # 更新显示值
        self.wheel_hue_spin.setValue(hue)
        self.wheel_sat_spin.setValue(sat)
        self.wheel_lift_spin.setValue(lift if self.color_wheel.wheel_type == "shadows" else gamma if self.color_wheel.wheel_type == "midtones" else gain)

    def on_curve_type_changed(self, curve_type: str):
        """曲线类型改变"""
        curve_type_map = {
            "亮度": "luma",
            "红色": "red",
            "绿色": "green",
            "蓝色": "blue",
            "RGB": "rgb"
        }

        curve = self.curve_editor.get_curve()
        curve.curve_type = curve_type_map.get(curve_type, "luma")
        self.curve_editor.set_curve(curve)

    def on_curve_changed(self, curve: ColorCurve):
        """曲线改变"""
        if self.real_time_update:
            self.update_preview()

    def on_load_lut(self):
        """加载LUT"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择LUT文件", "", "LUT Files (*.cube *.3dl *.dat)"
        )

        if file_path:
            self.lut_path_edit.setText(file_path)
            if self.real_time_update:
                self.update_preview()

    def on_apply_builtin_lut(self):
        """应用内置LUT"""
        preset_name = self.builtin_lut_list.currentText()
        if preset_name and self.real_time_update:
            self.update_preview()

    def on_hdr_to_sdr(self):
        """HDR转SDR"""
        if self.real_time_update:
            self.update_preview()

    def on_color_match(self):
        """色彩匹配"""
        if self.real_time_update:
            self.update_preview()

    def on_analyze_color(self):
        """分析色彩"""
        if self.current_frame is None:
            return

        try:
            # 获取输入色彩空间
            input_space = ColorSpace(self.input_space_combo.currentText())

            # 分析色彩
            analysis = self.color_science.analyze_color_accuracy(self.current_frame, input_space.value)

            # 显示分析结果
            analysis_text = f"""色彩分析结果:
平均RGB: {analysis.get('mean_rgb', [])}
标准差RGB: {analysis.get('std_rgb', [])}
最小RGB: {analysis.get('min_rgb', [])}
最大RGB: {analysis.get('max_rgb', [])}
色域覆盖率: {analysis.get('gamut_coverage', 0.0):.2%}
色温: {analysis.get('color_temperature', 6500.0):.0f}K
动态范围: {analysis.get('dynamic_range', 0.0):.1f}dB"""

            self.color_analysis_text.setText(analysis_text)

        except Exception as e:
            self.logger.error(f"色彩分析失败: {str(e)}")
            self.color_analysis_text.setText(f"分析失败: {str(e)}")

    def on_preview_toggled(self, checked: bool):
        """预览开关"""
        self.preview_enabled = checked
        if checked:
            self.update_preview()

    def on_preset_changed(self, preset_name: str):
        """预设改变"""
        if preset_name == "选择预设...":
            return

        # 应用预设
        if self.color_engine.load_preset(preset_name):
            self.logger.info(f"预设已应用: {preset_name}")

    def on_save_preset(self):
        """保存预设"""
        preset_name, ok = QInputDialog.getText(self, "保存预设", "预设名称:")
        if ok and preset_name:
            if self.color_engine.save_preset(preset_name, "用户预设"):
                self.logger.info(f"预设已保存: {preset_name}")
                # 添加到下拉框
                self.preset_combo.addItem(preset_name)

    def on_reset(self):
        """重置所有调整"""
        self.color_engine.clear_operations()
        self.reset_all_controls()
        self.update_preview()

    def on_apply(self):
        """应用调整"""
        self.update_preview()
        self.grade_applied.emit()

    def on_export_lut(self):
        """导出LUT"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出LUT", "", "CUBE Files (*.cube)"
        )

        if file_path:
            try:
                # 生成LUT
                operations = self.color_engine.get_operations()
                lut_data = self.color_engine.generate_lut_from_operations(
                    [op.to_dict() for op in operations],
                    lut_size=33
                )

                # 保存LUT文件
                self.save_lut_file(file_path, lut_data)
                self.logger.info(f"LUT已导出: {file_path}")

            except Exception as e:
                self.logger.error(f"LUT导出失败: {str(e)}")

    def save_lut_file(self, file_path: str, lut_data: np.ndarray):
        """保存LUT文件"""
        size = lut_data.shape[0]
        with open(file_path, 'w') as f:
            f.write('TITLE "Generated by CineAIStudio"\n')
            f.write(f'LUT_3D_SIZE {size}\n')

            for r in range(size):
                for g in range(size):
                    for b in range(size):
                        values = lut_data[r, g, b]
                        f.write(f'{values[0]:.6f} {values[1]:.6f} {values[2]:.6f}\n')

    def reset_all_controls(self):
        """重置所有控制器"""
        # 重置基础调整滑块
        self.exposure_slider['slider'].setValue(0)
        self.contrast_slider['slider'].setValue(100)
        self.brightness_slider['slider'].setValue(0)
        self.saturation_slider['slider'].setValue(100)
        self.vibrance_slider['slider'].setValue(100)
        self.hue_slider['slider'].setValue(0)
        self.shadows_slider['slider'].setValue(0)
        self.highlights_slider['slider'].setValue(0)

        # 重置色轮
        self.color_wheel.set_adjustment(ColorWheelAdjustment())

        # 重置曲线
        self.curve_editor.set_curve(ColorCurve(curve_type="luma"))

        # 重置其他控制器
        self.lut_path_edit.clear()
        self.lut_intensity_slider['slider'].setValue(100)

    def update_preview(self):
        """更新预览"""
        if not self.preview_enabled or self.current_frame is None:
            return

        try:
            # 获取当前调整参数
            operations = self.build_operations_from_ui()

            # 处理帧
            processed_frame = self.color_engine.process_frame(
                self.current_frame,
                operations,
                frame_id="preview"
            )

            # 更新预览显示
            self.update_preview_display(processed_frame)

            # 发出预览更新信号
            self.preview_updated.emit(processed_frame)

        except Exception as e:
            self.logger.error(f"预览更新失败: {str(e)}")

    def build_operations_from_ui(self) -> List[ColorGradingOperation]:
        """从UI构建操作列表"""
        operations = []

        # 基础调整
        exposure_val = self.exposure_slider['slider'].value() / 100.0
        contrast_val = self.contrast_slider['slider'].value() / 100.0
        brightness_val = self.brightness_slider['slider'].value() / 100.0

        if exposure_val != 0.0 or contrast_val != 1.0 or brightness_val != 0.0:
            operations.append(ColorGradingOperation(
                id=f"exposure_{int(time.time() * 1000)}",
                operation_type=ColorGradingTool.CONTRAST,
                parameters={
                    'contrast': contrast_val,
                    'brightness': brightness_val
                }
            ))

        # 色彩调整
        saturation_val = self.saturation_slider['slider'].value() / 100.0
        vibrance_val = self.vibrance_slider['slider'].value() / 100.0
        hue_val = self.hue_slider['slider'].value() / 100.0

        if saturation_val != 1.0 or vibrance_val != 1.0 or hue_val != 0.0:
            operations.append(ColorGradingOperation(
                id=f"hsl_{int(time.time() * 1000)}",
                operation_type=ColorGradingTool.HSL,
                parameters={
                    'hue_shift': hue_val,
                    'saturation': saturation_val,
                    'lightness': 1.0
                }
            ))

        # 阴影高光
        shadows_val = self.shadows_slider['slider'].value() / 100.0
        highlights_val = self.highlights_slider['slider'].value() / 100.0

        if shadows_val != 0.0 or highlights_val != 0.0:
            operations.append(ColorGradingOperation(
                id=f"shadows_highlights_{int(time.time() * 1000)}",
                operation_type=ColorGradingTool.SHADOWS_HIGHLIGHTS,
                parameters={
                    'shadows_amount': shadows_val,
                    'highlights_amount': highlights_val
                }
            ))

        # 色轮调整
        wheel_adjustment = self.color_wheel.adjustment
        if (wheel_adjustment.shadows != (0.0, 0.0, 0.0) or
            wheel_adjustment.midtones != (0.0, 0.0, 0.0) or
            wheel_adjustment.highlights != (0.0, 0.0, 0.0)):
            operations.append(ColorGradingOperation(
                id=f"wheel_{int(time.time() * 1000)}",
                operation_type=ColorGradingTool.WHEEL,
                parameters=wheel_adjustment.to_dict()
            ))

        # 曲线调整
        curve = self.curve_editor.get_curve()
        if curve.points:
            operations.append(ColorGradingOperation(
                id=f"curve_{int(time.time() * 1000)}",
                operation_type=ColorGradingTool.CURVE,
                parameters=curve.to_dict()
            ))

        # LUT调整
        lut_path = self.lut_path_edit.text()
        if lut_path:
            operations.append(ColorGradingOperation(
                id=f"lut_{int(time.time() * 1000)}",
                operation_type=ColorGradingTool.LUT,
                parameters={
                    'lut_path': lut_path,
                    'lut_intensity': self.lut_intensity_slider['slider'].value() / 100.0
                }
            ))

        return operations

    def update_preview_display(self, frame: np.ndarray):
        """更新预览显示"""
        try:
            # 转换为QImage
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

            # 缩放以适应预览区域
            preview_size = self.preview_label.size()
            scaled_image = q_image.scaled(
                preview_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            # 更新显示
            self.preview_label.setPixmap(QPixmap.fromImage(scaled_image))

        except Exception as e:
            self.logger.error(f"预览显示更新失败: {str(e)}")

    def set_current_frame(self, frame: np.ndarray):
        """设置当前帧"""
        if frame is not None:
            self.current_frame = frame.copy()
            if self.preview_enabled:
                self.update_preview()

    def get_current_operations(self) -> List[ColorGradingOperation]:
        """获取当前操作"""
        return self.build_operations_from_ui()

    def apply_operations_to_frame(self, frame: np.ndarray) -> np.ndarray:
        """将操作应用到帧"""
        operations = self.build_operations_from_ui()
        return self.color_engine.process_frame(frame, operations)

    def export_settings(self, file_path: str) -> bool:
        """导出设置"""
        return self.color_engine.export_settings(file_path)

    def import_settings(self, file_path: str) -> bool:
        """导入设置"""
        if self.color_engine.import_settings(file_path):
            # 更新UI以反映导入的设置
            self.reset_all_controls()
            return True
        return False


# 导入缺失的模块
from PyQt5.QtWidgets import QLineEdit, QTabWidget, QCheckBox, QRadioButton, QButtonGroup
from PyQt5.QtCore import QPoint, QRect, QLineF, QPointF
from PyQt5.QtGui import QRadialGradient, QLinearGradient, QPainterPath, QTransform
from PyQt5.QtWidgets import QInputDialog, QTextEdit, QSpinBox, QLabel

# 需要添加的导入
from ...core.color_grading_engine import get_color_grading_engine
from ...core.color_science import get_color_science_engine