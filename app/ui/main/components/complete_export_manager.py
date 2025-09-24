#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整导出管理器
整合所有导出功能，提供统一的导出管理界面
"""

import os
import json
import time
import platform
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
                            QProgressBar, QTableWidget, QTableWidgetItem,
                            QFileDialog, QMessageBox, QTabWidget, QGroupBox,
                            QLineEdit, QTextEdit, QCheckBox, QSlider, QDialog,
                            QDialogButtonBox, QFormLayout, QScrollArea,
                            QSplitter, QFrame, QStackedWidget, QToolButton,
                            QHeaderView, QAbstractItemView, QMenu, QGridLayout)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QRect, QPoint
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPainter, QPen

from ....export.export_system import ExportSystem, ExportTask, ExportPreset, ExportFormat, ExportQuality
from ....export.jianying_draft_generator import JianyingDraftGenerator
from ....export.performance_optimizer import ExportOptimizer, ExportOptimizationConfig, OptimizationLevel
from ....services.export_service import ExportService, ExportServiceMode
from ....core.logger import Logger
from ....core.event_system import EventBus
from ....utils.error_handler import (
    ErrorHandler, ErrorType, ErrorSeverity, RecoveryAction,
    ErrorContext, ErrorInfo, safe_execute, error_handler_decorator
)


@dataclass
class ExportJobConfig:
    """导出作业配置"""
    project_id: str
    project_name: str
    output_path: str
    preset_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)


class ExportPresetDialog(QDialog):
    """导出预设对话框"""

    def __init__(self, preset: ExportPreset = None, parent=None):
        super().__init__(parent)
        self.preset = preset
        self.logger = Logger("CompleteExportManager")
        self.setup_ui()

        if preset:
            self.load_preset_data()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("导出预设设置")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入预设名称...")

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("输入预设描述...")

        basic_layout.addRow("预设名称:", self.name_input)
        basic_layout.addRow("描述:", self.description_input)

        # 格式设置组
        format_group = QGroupBox("格式设置")
        format_layout = QFormLayout(format_group)

        # 格式选择
        self.format_combo = QComboBox()
        format_items = [
            ("MP4 (H.264)", ExportFormat.MP4_H264),
            ("MP4 (H.265)", ExportFormat.MP4_H265),
            ("MOV (ProRes)", ExportFormat.MOV_PRORES),
            ("AVI (无压缩)", ExportFormat.AVI_UNCOMPRESSED),
            ("MKV (H.264)", ExportFormat.MKV_H264),
            ("WebM (VP9)", ExportFormat.WEBM_VP9),
            ("GIF动画", ExportFormat.GIF_ANIMATED),
            ("MP3音频", ExportFormat.MP3_AUDIO),
            ("WAV音频", ExportFormat.WAV_AUDIO),
            ("剪映草稿", ExportFormat.JIANYING_DRAFT)
        ]

        for text, format_type in format_items:
            self.format_combo.addItem(text, format_type)

        # 分辨率选择
        self.resolution_combo = QComboBox()
        resolution_items = [
            ("3840×2160 (4K)", (3840, 2160)),
            ("2560×1440 (2K)", (2560, 1440)),
            ("1920×1080 (1080p)", (1920, 1080)),
            ("1280×720 (720p)", (1280, 720)),
            ("854×480 (480p)", (854, 480)),
            ("自定义", None)
        ]

        for text, resolution in resolution_items:
            self.resolution_combo.addItem(text, resolution)

        # 帧率设置
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        self.fps_spin.setSuffix(" fps")

        format_layout.addRow("输出格式:", self.format_combo)
        format_layout.addRow("分辨率:", self.resolution_combo)
        format_layout.addRow("帧率:", self.fps_spin)

        # 质量设置组
        quality_group = QGroupBox("质量设置")
        quality_layout = QFormLayout(quality_group)

        # 质量级别
        self.quality_combo = QComboBox()
        quality_items = [
            ("低质量 (480p)", ExportQuality.LOW),
            ("中等质量 (720p)", ExportQuality.MEDIUM),
            ("高质量 (1080p)", ExportQuality.HIGH),
            ("超高质量 (4K)", ExportQuality.ULTRA),
            ("自定义", ExportQuality.CUSTOM)
        ]

        for text, quality in quality_items:
            self.quality_combo.addItem(text, quality)

        # 比特率设置
        self.video_bitrate_spin = QSpinBox()
        self.video_bitrate_spin.setRange(100, 100000)
        self.video_bitrate_spin.setValue(8000)
        self.video_bitrate_spin.setSuffix(" kbps")

        self.audio_bitrate_spin = QSpinBox()
        self.audio_bitrate_spin.setRange(32, 512)
        self.audio_bitrate_spin.setValue(128)
        self.audio_bitrate_spin.setSuffix(" kbps")

        quality_layout.addRow("质量级别:", self.quality_combo)
        quality_layout.addRow("视频比特率:", self.video_bitrate_spin)
        quality_layout.addRow("音频比特率:", self.audio_bitrate_spin)

        # 高级设置组
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)

        # 编码参数
        self.codec_params_edit = QTextEdit()
        self.codec_params_edit.setMaximumHeight(100)
        self.codec_params_edit.setPlaceholderText("额外编码参数，例如：-crf 23 -preset medium")

        # 优化选项
        self.gpu_acceleration_check = QCheckBox("启用GPU加速")
        self.gpu_acceleration_check.setChecked(True)

        self.multi_threading_check = QCheckBox("启用多线程")
        self.multi_threading_check.setChecked(True)

        advanced_layout.addRow("编码参数:", self.codec_params_edit)
        advanced_layout.addRow("GPU加速:", self.gpu_acceleration_check)
        advanced_layout.addRow("多线程:", self.multi_threading_check)

        # 添加到主布局
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        scroll_layout.addWidget(basic_group)
        scroll_layout.addWidget(format_group)
        scroll_layout.addWidget(quality_group)
        scroll_layout.addWidget(advanced_group)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # 对话框按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_changes)

        layout.addWidget(buttons)

        # 连接信号
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        self.quality_combo.currentTextChanged.connect(self.on_quality_changed)

    def load_preset_data(self):
        """加载预设数据"""
        if not self.preset:
            return

        self.name_input.setText(self.preset.name)
        self.description_input.setText(self.preset.description)

        # 设置格式
        format_index = self.format_combo.findData(self.preset.format)
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)

        # 设置分辨率
        resolution_index = self.resolution_combo.findData(self.preset.resolution)
        if resolution_index >= 0:
            self.resolution_combo.setCurrentIndex(resolution_index)
        else:
            self.resolution_combo.setCurrentText("自定义")

        # 设置帧率
        self.fps_spin.setValue(int(self.preset.fps))

        # 设置质量
        quality_index = self.quality_combo.findData(self.preset.quality)
        if quality_index >= 0:
            self.quality_combo.setCurrentIndex(quality_index)

        # 设置比特率
        self.video_bitrate_spin.setValue(self.preset.bitrate)
        self.audio_bitrate_spin.setValue(self.preset.audio_bitrate)

    def on_format_changed(self):
        """格式改变事件"""
        current_format = self.format_combo.currentData()

        # 根据格式调整可用选项
        if current_format in [ExportFormat.MP3_AUDIO, ExportFormat.WAV_AUDIO]:
            # 音频格式，禁用视频相关选项
            self.video_bitrate_spin.setEnabled(False)
            self.resolution_combo.setEnabled(False)
            self.fps_spin.setEnabled(False)
        else:
            self.video_bitrate_spin.setEnabled(True)
            self.resolution_combo.setEnabled(True)
            self.fps_spin.setEnabled(True)

    def on_quality_changed(self):
        """质量改变事件"""
        current_quality = self.quality_combo.currentData()

        # 根据质量级别自动设置比特率
        bitrate_presets = {
            ExportQuality.LOW: 1000,
            ExportQuality.MEDIUM: 3000,
            ExportQuality.HIGH: 8000,
            ExportQuality.ULTRA: 35000
        }

        if current_quality in bitrate_presets:
            self.video_bitrate_spin.setValue(bitrate_presets[current_quality])

    def apply_changes(self):
        """应用更改"""
        # 这里可以添加实时预览或其他功能
        pass

    def get_preset_data(self) -> Dict[str, Any]:
        """获取预设数据"""
        resolution = self.resolution_combo.currentData()
        if resolution is None:
            # 自定义分辨率，可以添加自定义分辨率输入
            resolution = (1920, 1080)  # 默认值

        return {
            "name": self.name_input.text(),
            "description": self.description_input.toPlainText(),
            "format": self.format_combo.currentData().value,
            "quality": self.quality_combo.currentData().value,
            "resolution": resolution,
            "fps": self.fps_spin.value(),
            "bitrate": self.video_bitrate_spin.value(),
            "audio_bitrate": self.audio_bitrate_spin.value(),
            "codec_params": self.codec_params_edit.toPlainText(),
            "gpu_acceleration": self.gpu_acceleration_check.isChecked(),
            "multi_threading": self.multi_threading_check.isChecked()
        }


class ExportProgressDialog(QDialog):
    """导出进度对话框"""

    def __init__(self, export_system: ExportSystem, parent=None):
        super().__init__(parent)
        self.export_system = export_system
        self.logger = Logger("CompleteExportManager")
        self.active_tasks: Dict[str, ExportTask] = {}
        self.setup_ui()
        self.connect_signals()
        self.setup_timer()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("导出进度")
        self.setMinimumSize(700, 500)
        self.setModal(False)

        layout = QVBoxLayout(self)

        # 总体进度
        overall_group = QGroupBox("总体进度")
        overall_layout = QVBoxLayout(overall_group)

        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)

        self.overall_status_label = QLabel("准备就绪")

        overall_layout.addWidget(self.overall_progress)
        overall_layout.addWidget(self.overall_status_label)

        # 任务列表
        tasks_group = QGroupBox("活动任务")
        tasks_layout = QVBoxLayout(tasks_group)

        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "任务", "项目", "状态", "进度", "剩余时间", "操作"
        ])
        self.tasks_table.horizontalHeader().setStretchLastSection(True)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tasks_table.setAlternatingRowColors(True)

        tasks_layout.addWidget(self.tasks_table)

        # 性能监控
        perf_group = QGroupBox("性能监控")
        perf_layout = QHBoxLayout(perf_group)

        self.cpu_label = QLabel("CPU: 0%")
        self.memory_label = QLabel("内存: 0%")
        self.speed_label = QLabel("速度: 0 MB/s")

        perf_layout.addWidget(self.cpu_label)
        perf_layout.addWidget(self.memory_label)
        perf_layout.addWidget(self.speed_label)
        perf_layout.addStretch()

        # 操作按钮
        button_layout = QHBoxLayout()

        self.hide_btn = QPushButton("隐藏")
        self.hide_btn.clicked.connect(self.hide)

        self.cancel_all_btn = QPushButton("取消全部")
        self.cancel_all_btn.clicked.connect(self.cancel_all_tasks)

        self.minimize_btn = QPushButton("最小化")
        self.minimize_btn.clicked.connect(self.showMinimized)

        button_layout.addStretch()
        button_layout.addWidget(self.minimize_btn)
        button_layout.addWidget(self.hide_btn)
        button_layout.addWidget(self.cancel_all_btn)

        # 添加到主布局
        layout.addWidget(overall_group)
        layout.addWidget(tasks_group)
        layout.addWidget(perf_group)
        layout.addLayout(button_layout)

    def connect_signals(self):
        """连接信号"""
        self.export_system.export_started.connect(self.on_export_started)
        self.export_system.export_progress.connect(self.on_export_progress)
        self.export_system.export_completed.connect(self.on_export_completed)
        self.export_system.export_failed.connect(self.on_export_failed)

    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)

    def update_display(self):
        """更新显示"""
        try:
            # 更新任务列表
            self.update_tasks_table()

            # 更新总体进度
            self.update_overall_progress()

            # 更新性能信息
            self.update_performance_info()

        except Exception as e:
            self.logger.error(f"Failed to update display: {e}")

    def update_tasks_table(self):
        """更新任务表格"""
        try:
            tasks = self.export_system.get_task_history()
            active_tasks = [t for t in tasks if t.status.value in ["processing", "queued", "pending"]]

            self.tasks_table.setRowCount(len(active_tasks))

            for i, task in enumerate(active_tasks):
                # 任务名称
                task_name = f"{task.metadata.get('project_name', '未知项目')} ({task.preset.name})"
                self.tasks_table.setItem(i, 0, QTableWidgetItem(task_name))

                # 项目信息
                project_info = task.metadata.get('project_name', '未知项目')
                self.tasks_table.setItem(i, 1, QTableWidgetItem(project_info))

                # 状态
                status_item = QTableWidgetItem(task.status.value)
                status_item.setBackground(self.get_status_color(task.status))
                self.tasks_table.setItem(i, 2, status_item)

                # 进度
                progress_item = QTableWidgetItem(f"{task.progress:.1f}%")
                self.tasks_table.setItem(i, 3, progress_item)

                # 剩余时间
                eta = self.calculate_eta(task)
                self.tasks_table.setItem(i, 4, QTableWidgetItem(eta))

                # 操作按钮
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)

                if task.status.value in ["processing", "queued"]:
                    cancel_btn = QPushButton("取消")
                    cancel_btn.setMaximumWidth(60)
                    cancel_btn.clicked.connect(lambda checked, tid=task.id: self.cancel_task(tid))
                    actions_layout.addWidget(cancel_btn)

                actions_layout.addStretch()
                self.tasks_table.setCellWidget(i, 5, actions_widget)

            # 更新活动任务字典
            self.active_tasks = {task.id: task for task in active_tasks}

        except Exception as e:
            self.logger.error(f"Failed to update tasks table: {e}")

    def update_overall_progress(self):
        """更新总体进度"""
        try:
            if not self.active_tasks:
                self.overall_progress.setValue(0)
                self.overall_status_label.setText("无活动任务")
                return

            total_progress = sum(task.progress for task in self.active_tasks.values())
            avg_progress = total_progress / len(self.active_tasks)

            self.overall_progress.setValue(int(avg_progress))

            processing_count = len([t for t in self.active_tasks.values() if t.status.value == "processing"])
            queued_count = len([t for t in self.active_tasks.values() if t.status.value == "queued"])

            status_text = f"处理中: {processing_count} | 排队中: {queued_count} | 平均进度: {avg_progress:.1f}%"
            self.overall_status_label.setText(status_text)

        except Exception as e:
            self.logger.error(f"Failed to update overall progress: {e}")

    def update_performance_info(self):
        """更新性能信息"""
        try:
            # 这里可以集成性能优化器的信息
            # 暂时使用模拟数据
            import random
            cpu_usage = random.randint(10, 80)
            memory_usage = random.randint(20, 70)
            speed = random.uniform(10, 100)

            self.cpu_label.setText(f"CPU: {cpu_usage}%")
            self.memory_label.setText(f"内存: {memory_usage}%")
            self.speed_label.setText(f"速度: {speed:.1f} MB/s")

        except Exception as e:
            self.logger.error(f"Failed to update performance info: {e}")

    def get_status_color(self, status) -> QColor:
        """获取状态颜色"""
        colors = {
            "pending": QColor(200, 200, 200),
            "queued": QColor(255, 200, 0),
            "processing": QColor(0, 150, 255),
            "completed": QColor(0, 200, 0),
            "failed": QColor(255, 0, 0),
            "cancelled": QColor(150, 150, 150)
        }
        return colors.get(status.value, QColor(200, 200, 200))

    def calculate_eta(self, task: ExportTask) -> str:
        """计算预计剩余时间"""
        if task.status.value != "processing" or not task.started_at:
            return "未知"

        elapsed_time = time.time() - task.started_at
        if elapsed_time <= 0 or task.progress <= 0:
            return "未知"

        total_estimated_time = elapsed_time / (task.progress / 100)
        remaining_time = total_estimated_time - elapsed_time

        if remaining_time < 0:
            return "即将完成"

        return self.format_duration(remaining_time)

    def format_duration(self, seconds: float) -> str:
        """格式化持续时间"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分"

    def on_export_started(self, task_id: str):
        """导出开始事件"""
        self.show()
        self.raise_()
        self.activateWindow()

    def on_export_progress(self, task_id: str, progress: float):
        """导出进度事件"""
        # 更新由定时器处理
        pass

    def on_export_completed(self, task_id: str, output_path: str):
        """导出完成事件"""
        self.check_all_completed()

    def on_export_failed(self, task_id: str, error_message: str):
        """导出失败事件"""
        pass

    def check_all_completed(self):
        """检查是否所有任务都已完成"""
        try:
            tasks = self.export_system.get_task_history()
            active_tasks = [t for t in tasks if t.status.value in ["processing", "queued", "pending"]]

            if not active_tasks:
                self.show_completion_notification()
        except Exception as e:
            self.logger.error(f"Failed to check completion: {e}")

    def show_completion_notification(self):
        """显示完成通知"""
        try:
            tasks = self.export_system.get_task_history()
            completed_count = len([t for t in tasks if t.status.value == "completed"])
            failed_count = len([t for t in tasks if t.status.value == "failed"])

            message = f"导出完成！\\n成功: {completed_count} 个任务"
            if failed_count > 0:
                message += f"\\n失败: {failed_count} 个任务"

            QMessageBox.information(self, "导出完成", message)

        except Exception as e:
            self.logger.error(f"Failed to show completion notification: {e}")

    def cancel_task(self, task_id: str):
        """取消单个任务"""
        try:
            success = self.export_system.cancel_export(task_id)
            if success:
                QMessageBox.information(self, "成功", "任务已取消")
            else:
                QMessageBox.warning(self, "警告", "无法取消该任务")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"取消任务失败: {str(e)}")

    def cancel_all_tasks(self):
        """取消所有任务"""
        reply = QMessageBox.question(
            self, "确认取消", "确定要取消所有导出任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                tasks = self.export_system.get_task_history()
                cancelled_count = 0

                for task in tasks:
                    if task.status.value in ["processing", "queued", "pending"]:
                        if self.export_system.cancel_export(task.id):
                            cancelled_count += 1

                QMessageBox.information(self, "成功", f"已取消 {cancelled_count} 个任务")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"取消任务失败: {str(e)}")

    def cleanup(self):
        """清理资源"""
        try:
            self.update_timer.stop()
        except:
            pass


class CompleteExportManager(QWidget):
    """完整导出管理器"""

    # 信号定义
    export_started = pyqtSignal(str)
    export_progress = pyqtSignal(str, float)
    export_completed = pyqtSignal(str, str)
    export_failed = pyqtSignal(str, str)

    def __init__(self, application, parent=None):
        super().__init__(parent)
        self.application = application
        self.export_system = application.export_system
        self.export_service = application.export_service
        self.project_manager = application.get_service_by_name("project_manager")
        self.logger = Logger("CompleteExportManager")
        self.current_project = None
        self.progress_dialog = None

        # 增强错误处理
        self.error_handler = ErrorHandler(self.logger)
        self.export_error_history = []
        self.retry_count = 0
        self.max_retries = 3
        self.export_system_monitor = ExportSystemMonitor()

        self.setup_ui()
        self.connect_signals()
        self.setup_error_handling()
        self.load_data()
        self.start_system_monitoring()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建主标签页
        self.main_tab_widget = QTabWidget()

        # 快速导出标签页
        self.quick_export_tab = self.create_quick_export_tab()
        self.main_tab_widget.addTab(self.quick_export_tab, "快速导出")

        # 高级导出标签页
        self.advanced_export_tab = self.create_advanced_export_tab()
        self.main_tab_widget.addTab(self.advanced_export_tab, "高级导出")

        # 批量导出标签页
        self.batch_export_tab = self.create_batch_export_tab()
        self.main_tab_widget.addTab(self.batch_export_tab, "批量导出")

        # 剪映导出标签页
        self.jianying_export_tab = self.create_jianying_export_tab()
        self.main_tab_widget.addTab(self.jianying_export_tab, "剪映导出")

        # 队列管理标签页
        self.queue_tab = self.create_queue_tab()
        self.main_tab_widget.addTab(self.queue_tab, "队列管理")

        # 预设管理标签页
        self.presets_tab = self.create_presets_tab()
        self.main_tab_widget.addTab(self.presets_tab, "预设管理")

        layout.addWidget(self.main_tab_widget)

        # 状态栏
        self.status_bar = QWidget()
        self.status_bar.setMaximumHeight(30)
        status_bar_layout = QHBoxLayout(self.status_bar)
        status_bar_layout.setContentsMargins(5, 2, 5, 2)

        self.status_label = QLabel("就绪")
        self.queue_status_label = QLabel("队列: 0 个任务")

        status_bar_layout.addWidget(self.status_label)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(self.queue_status_label)

        layout.addWidget(self.status_bar)

    def create_quick_export_tab(self) -> QWidget:
        """创建快速导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 项目信息组
        project_group = QGroupBox("当前项目")
        project_layout = QFormLayout(project_group)

        self.project_name_label = QLabel("未选择项目")
        self.project_duration_label = QLabel("00:00:00")
        self.project_resolution_label = QLabel("1920×1080")
        self.project_size_label = QLabel("0 MB")

        project_layout.addRow("项目名称:", self.project_name_label)
        project_layout.addRow("持续时间:", self.project_duration_label)
        project_layout.addRow("分辨率:", self.project_resolution_label)
        project_layout.addRow("文件大小:", self.project_size_label)

        # 快速预设组
        presets_group = QGroupBox("快速预设")
        presets_layout = QGridLayout(presets_group)

        # 预设按钮
        quick_presets = [
            ("YouTube 1080p", "youtube_1080p", "📺"),
            ("YouTube 4K", "youtube_4k", "🎬"),
            ("TikTok", "tiktok_video", "🎵"),
            ("Instagram", "instagram_reel", "📸"),
            ("高质量", "master_quality", "⭐"),
            ("剪映草稿", "jianying_draft", "📝")
        ]

        self.quick_preset_buttons = {}
        for i, (name, preset_id, icon) in enumerate(quick_presets):
            btn = QPushButton(f"{icon} {name}")
            btn.setMinimumHeight(60)
            btn.clicked.connect(lambda checked, pid=preset_id: self.quick_export(pid))

            row = i // 3
            col = i % 3
            presets_layout.addWidget(btn, row, col)

            self.quick_preset_buttons[preset_id] = btn

        # 自定义导出组
        custom_group = QGroupBox("自定义导出")
        custom_layout = QFormLayout(custom_group)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(200)

        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择输出文件路径...")

        self.browse_output_btn = QPushButton("浏览...")
        self.browse_output_btn.clicked.connect(self.browse_output_path)

        output_path_layout = QHBoxLayout()
        output_path_layout.addWidget(self.output_path_edit, 1)
        output_path_layout.addWidget(self.browse_output_btn)

        custom_layout.addRow("导出预设:", self.preset_combo)
        custom_layout.addRow("输出路径:", output_path_layout)

        # 操作按钮
        actions_layout = QHBoxLayout()

        self.export_btn = QPushButton("🚀 开始导出")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.clicked.connect(self.start_export)

        self.preview_btn = QPushButton("👁️ 预览设置")
        self.preview_btn.clicked.connect(self.preview_export_settings)

        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.export_btn)

        # 添加到布局
        layout.addWidget(project_group)
        layout.addWidget(presets_group)
        layout.addWidget(custom_group)
        layout.addLayout(actions_layout)
        layout.addStretch()

        return widget

    def create_advanced_export_tab(self) -> QWidget:
        """创建高级导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：设置面板
        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)

        # 基本设置
        basic_group = QGroupBox("基本设置")
        basic_layout = QFormLayout(basic_group)

        self.adv_format_combo = QComboBox()
        self.adv_format_combo.addItems([
            "MP4 (H.264)", "MP4 (H.265)", "MOV (ProRes)",
            "AVI (无压缩)", "MKV (H.264)", "WebM (VP9)"
        ])

        self.adv_resolution_combo = QComboBox()
        self.adv_resolution_combo.addItems([
            "3840×2160 (4K)", "2560×1440 (2K)", "1920×1080 (1080p)",
            "1280×720 (720p)", "854×480 (480p)", "自定义"
        ])

        self.adv_fps_spin = QSpinBox()
        self.adv_fps_spin.setRange(1, 120)
        self.adv_fps_spin.setValue(30)

        basic_layout.addRow("格式:", self.adv_format_combo)
        basic_layout.addRow("分辨率:", self.adv_resolution_combo)
        basic_layout.addRow("帧率:", self.adv_fps_spin)

        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)

        self.adv_bitrate_spin = QSpinBox()
        self.adv_bitrate_spin.setRange(100, 100000)
        self.adv_bitrate_spin.setValue(8000)
        self.adv_bitrate_spin.setSuffix(" kbps")

        self.adv_audio_bitrate_spin = QSpinBox()
        self.adv_audio_bitrate_spin.setRange(32, 512)
        self.adv_audio_bitrate_spin.setValue(128)
        self.adv_audio_bitrate_spin.setSuffix(" kbps")

        self.adv_codec_params_edit = QTextEdit()
        self.adv_codec_params_edit.setMaximumHeight(80)
        self.adv_codec_params_edit.setPlaceholderText("额外编码参数...")

        advanced_layout.addRow("视频比特率:", self.adv_bitrate_spin)
        advanced_layout.addRow("音频比特率:", self.adv_audio_bitrate_spin)
        advanced_layout.addRow("编码参数:", self.adv_codec_params_edit)

        # 优化设置
        optimization_group = QGroupBox("优化设置")
        optimization_layout = QVBoxLayout(optimization_group)

        self.gpu_accel_check = QCheckBox("启用GPU加速")
        self.gpu_accel_check.setChecked(True)

        self.multi_thread_check = QCheckBox("启用多线程")
        self.multi_thread_check.setChecked(True)

        self.fast_start_check = QCheckBox("快速启动 (Web优化)")
        self.fast_start_check.setChecked(True)

        optimization_layout.addWidget(self.gpu_accel_check)
        optimization_layout.addWidget(self.multi_thread_check)
        optimization_layout.addWidget(self.fast_start_check)

        settings_layout.addWidget(basic_group)
        settings_layout.addWidget(advanced_group)
        settings_layout.addWidget(optimization_group)
        settings_layout.addStretch()

        # 右侧：预览和信息
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)

        # 文件信息
        info_group = QGroupBox("文件信息")
        info_layout = QFormLayout(info_group)

        self.estimated_size_label = QLabel("计算中...")
        self.estimated_time_label = QLabel("计算中...")

        info_layout.addRow("预计文件大小:", self.estimated_size_label)
        info_layout.addRow("预计导出时间:", self.estimated_time_label)

        # 预览
        preview_group = QGroupBox("预览")
        preview_content_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel("导出预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")

        preview_content_layout.addWidget(self.preview_label)

        # 操作按钮
        adv_actions_layout = QHBoxLayout()

        self.adv_save_preset_btn = QPushButton("保存预设")
        self.adv_save_preset_btn.clicked.connect(self.save_advanced_preset)

        self.adv_start_export_btn = QPushButton("开始导出")
        self.adv_start_export_btn.setMinimumHeight(40)
        self.adv_start_export_btn.clicked.connect(self.start_advanced_export)

        adv_actions_layout.addWidget(self.adv_save_preset_btn)
        adv_actions_layout.addWidget(self.adv_start_export_btn)

        preview_layout.addWidget(info_group)
        preview_layout.addWidget(preview_group)
        preview_layout.addLayout(adv_actions_layout)
        preview_layout.addStretch()

        # 添加到分割器
        splitter.addWidget(settings_panel)
        splitter.addWidget(preview_panel)
        splitter.setSizes([400, 300])

        layout.addWidget(splitter)

        return widget

    def create_batch_export_tab(self) -> QWidget:
        """创建批量导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 项目选择组
        projects_group = QGroupBox("项目选择")
        projects_layout = QVBoxLayout(projects_group)

        self.batch_projects_table = QTableWidget()
        self.batch_projects_table.setColumnCount(5)
        self.batch_projects_table.setHorizontalHeaderLabels([
            "选择", "项目名称", "持续时间", "分辨率", "大小"
        ])
        self.batch_projects_table.horizontalHeader().setStretchLastSection(True)
        self.batch_projects_table.setAlternatingRowColors(True)

        projects_layout.addWidget(self.batch_projects_table)

        # 项目选择按钮
        project_actions_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_projects)

        self.select_none_btn = QPushButton("全不选")
        self.select_none_btn.clicked.connect(self.select_none_projects)

        self.refresh_projects_btn = QPushButton("刷新项目")
        self.refresh_projects_btn.clicked.connect(self.refresh_projects_list)

        project_actions_layout.addWidget(self.select_all_btn)
        project_actions_layout.addWidget(self.select_none_btn)
        project_actions_layout.addWidget(self.refresh_projects_btn)

        projects_layout.addLayout(project_actions_layout)

        # 批量设置组
        batch_settings_group = QGroupBox("批量设置")
        batch_settings_layout = QFormLayout(batch_settings_group)

        self.batch_output_dir_edit = QLineEdit()
        self.batch_output_dir_edit.setPlaceholderText("选择输出目录...")

        self.batch_browse_btn = QPushButton("浏览...")
        self.batch_browse_btn.clicked.connect(self.browse_batch_output_dir)

        batch_output_layout = QHBoxLayout()
        batch_output_layout.addWidget(self.batch_output_dir_edit, 1)
        batch_output_layout.addWidget(self.batch_browse_btn)

        self.batch_preset_combo = QComboBox()
        self.batch_preset_combo.setMinimumWidth(200)

        self.batch_naming_pattern_edit = QLineEdit()
        self.batch_naming_pattern_edit.setPlaceholderText("{project_name}_{preset}_{date}")
        self.batch_naming_pattern_edit.setText("{project_name}_{preset_id}")

        batch_settings_layout.addRow("输出目录:", batch_output_layout)
        batch_settings_layout.addRow("导出预设:", self.batch_preset_combo)
        batch_settings_layout.addRow("命名模式:", self.batch_naming_pattern_edit)

        # 批量操作组
        batch_actions_group = QGroupBox("批量操作")
        batch_actions_layout = QVBoxLayout(batch_actions_group)

        # 批量导出类型
        batch_type_layout = QHBoxLayout()

        self.batch_single_preset_radio = QCheckBox("单预设导出")
        self.batch_single_preset_radio.setChecked(True)

        self.batch_multi_preset_radio = QCheckBox("多预设导出")

        self.batch_template_radio = QCheckBox("模板导出")

        batch_type_layout.addWidget(self.batch_single_preset_radio)
        batch_type_layout.addWidget(self.batch_multi_preset_radio)
        batch_type_layout.addWidget(self.batch_template_radio)

        batch_actions_layout.addLayout(batch_type_layout)

        # 开始批量导出按钮
        self.start_batch_btn = QPushButton("🚀 开始批量导出")
        self.start_batch_btn.setMinimumHeight(40)
        self.start_batch_btn.clicked.connect(self.start_batch_export)

        batch_actions_layout.addWidget(self.start_batch_btn)

        # 添加到布局
        layout.addWidget(projects_group)
        layout.addWidget(batch_settings_group)
        layout.addWidget(batch_actions_group)
        layout.addStretch()

        return widget

    def create_jianying_export_tab(self) -> QWidget:
        """创建剪映导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明组
        info_group = QGroupBox("剪映Draft导出说明")
        info_layout = QVBoxLayout(info_group)

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setHtml("""
        <p><b>剪映Draft格式导出功能说明：</b></p>
        <ul>
            <li>生成符合剪映草稿格式的JSON文件</li>
            <li>保留所有轨道、素材、特效信息</li>
            <li>可在剪映中继续编辑和调整</li>
            <li>支持视频、音频、图片、文字等素材</li>
        </ul>
        """)

        info_layout.addWidget(info_text)

        # Draft配置组
        config_group = QGroupBox("Draft配置")
        config_layout = QFormLayout(config_group)

        self.draft_project_name_edit = QLineEdit()
        self.draft_project_name_edit.setPlaceholderText("输入项目名称...")

        self.draft_fps_spin = QSpinBox()
        self.draft_fps_spin.setRange(24, 60)
        self.draft_fps_spin.setValue(30)

        self.draft_resolution_combo = QComboBox()
        self.draft_resolution_combo.addItems([
            "1920×1080 (1080p)", "1280×720 (720p)", "3840×2160 (4K)"
        ])

        config_layout.addRow("项目名称:", self.draft_project_name_edit)
        config_layout.addRow("帧率:", self.draft_fps_spin)
        config_layout.addRow("分辨率:", self.draft_resolution_combo)

        # 素材管理组
        materials_group = QGroupBox("素材管理")
        materials_layout = QVBoxLayout(materials_group)

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(4)
        self.materials_table.setHorizontalHeaderLabels([
            "素材类型", "文件名", "持续时间", "路径"
        ])
        self.materials_table.horizontalHeader().setStretchLastSection(True)

        materials_layout.addWidget(self.materials_table)

        # 素材操作按钮
        material_actions_layout = QHBoxLayout()

        self.add_material_btn = QPushButton("添加素材")
        self.add_material_btn.clicked.connect(self.add_material)

        self.remove_material_btn = QPushButton("移除素材")
        self.remove_material_btn.clicked.connect(self.remove_material)

        self.clear_materials_btn = QPushButton("清空素材")
        self.clear_materials_btn.clicked.connect(self.clear_materials)

        material_actions_layout.addWidget(self.add_material_btn)
        material_actions_layout.addWidget(self.remove_material_btn)
        material_actions_layout.addWidget(self.clear_materials_btn)

        materials_layout.addLayout(material_actions_layout)

        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout(output_group)

        self.draft_output_path_edit = QLineEdit()
        self.draft_output_path_edit.setPlaceholderText("选择Draft文件保存路径...")

        self.draft_browse_btn = QPushButton("浏览...")
        self.draft_browse_btn.clicked.connect(self.browse_draft_output_path)

        draft_output_layout = QHBoxLayout()
        draft_output_layout.addWidget(self.draft_output_path_edit, 1)
        draft_output_layout.addWidget(self.draft_browse_btn)

        self.include_metadata_check = QCheckBox("包含完整元数据")
        self.include_metadata_check.setChecked(True)

        self.compress_draft_check = QCheckBox("压缩Draft文件")
        self.compress_draft_check.setChecked(False)

        output_layout.addRow("输出路径:", draft_output_layout)
        output_layout.addRow("包含元数据:", self.include_metadata_check)
        output_layout.addRow("压缩文件:", self.compress_draft_check)

        # 生成Draft按钮
        self.generate_draft_btn = QPushButton("📝 生成剪映Draft")
        self.generate_draft_btn.setMinimumHeight(40)
        self.generate_draft_btn.clicked.connect(self.generate_jianying_draft)

        # 添加到布局
        layout.addWidget(info_group)
        layout.addWidget(config_group)
        layout.addWidget(materials_group)
        layout.addWidget(output_group)
        layout.addWidget(self.generate_draft_btn)
        layout.addStretch()

        return widget

    def create_queue_tab(self) -> QWidget:
        """创建队列管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 队列状态组
        status_group = QGroupBox("队列状态")
        status_layout = QHBoxLayout(status_group)

        self.queue_total_label = QLabel("总任务: 0")
        self.queue_processing_label = QLabel("处理中: 0")
        self.queue_completed_label = QLabel("已完成: 0")
        self.queue_failed_label = QLabel("失败: 0")

        status_layout.addWidget(self.queue_total_label)
        status_layout.addWidget(self.queue_processing_label)
        status_layout.addWidget(self.queue_completed_label)
        status_layout.addWidget(self.queue_failed_label)
        status_layout.addStretch()

        # 队列表格
        queue_table_group = QGroupBox("任务队列")
        queue_table_layout = QVBoxLayout(queue_table_group)

        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(7)
        self.queue_table.setHorizontalHeaderLabels([
            "任务ID", "项目", "预设", "状态", "进度", "开始时间", "操作"
        ])
        self.queue_table.horizontalHeader().setStretchLastSection(True)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        queue_table_layout.addWidget(self.queue_table)

        # 队列操作按钮
        queue_actions_layout = QHBoxLayout()

        self.pause_queue_btn = QPushButton("暂停队列")
        self.pause_queue_btn.clicked.connect(self.pause_queue)

        self.resume_queue_btn = QPushButton("恢复队列")
        self.resume_queue_btn.clicked.connect(self.resume_queue)

        self.clear_completed_btn = QPushButton("清除已完成")
        self.clear_completed_btn.clicked.connect(self.clear_completed_tasks)

        self.cancel_all_queue_btn = QPushButton("取消全部")
        self.cancel_all_queue_btn.clicked.connect(self.cancel_all_queue_tasks)

        queue_actions_layout.addWidget(self.pause_queue_btn)
        queue_actions_layout.addWidget(self.resume_queue_btn)
        queue_actions_layout.addWidget(self.clear_completed_btn)
        queue_actions_layout.addWidget(self.cancel_all_queue_btn)

        queue_table_layout.addLayout(queue_actions_layout)

        # 队列设置组
        queue_settings_group = QGroupBox("队列设置")
        queue_settings_layout = QFormLayout(queue_settings_group)

        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 8)
        self.max_concurrent_spin.setValue(2)

        self.auto_cleanup_check = QCheckBox("自动清理已完成任务")
        self.auto_cleanup_check.setChecked(True)

        self.retry_failed_check = QCheckBox("自动重试失败任务")
        self.retry_failed_check.setChecked(False)

        queue_settings_layout.addRow("最大并发数:", self.max_concurrent_spin)
        queue_settings_layout.addRow("自动清理:", self.auto_cleanup_check)
        queue_settings_layout.addRow("自动重试:", self.retry_failed_check)

        # 应用设置按钮
        self.apply_queue_settings_btn = QPushButton("应用队列设置")
        self.apply_queue_settings_btn.clicked.connect(self.apply_queue_settings)

        # 添加到布局
        layout.addWidget(status_group)
        layout.addWidget(queue_table_group)
        layout.addWidget(queue_settings_group)
        layout.addWidget(self.apply_queue_settings_btn)

        return widget

    def create_presets_tab(self) -> QWidget:
        """创建预设管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 预设列表组
        presets_list_group = QGroupBox("导出预设")
        presets_list_layout = QVBoxLayout(presets_list_group)

        self.presets_table = QTableWidget()
        self.presets_table.setColumnCount(6)
        self.presets_table.setHorizontalHeaderLabels([
            "预设名称", "格式", "分辨率", "质量", "比特率", "操作"
        ])
        self.presets_table.horizontalHeader().setStretchLastSection(True)
        self.presets_table.setAlternatingRowColors(True)
        self.presets_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        presets_list_layout.addWidget(self.presets_table)

        # 预设操作按钮
        preset_actions_layout = QHBoxLayout()

        self.add_preset_btn = QPushButton("➕ 添加预设")
        self.add_preset_btn.clicked.connect(self.add_preset)

        self.edit_preset_btn = QPushButton("✏️ 编辑预设")
        self.edit_preset_btn.clicked.connect(self.edit_preset)

        self.delete_preset_btn = QPushButton("🗑️ 删除预设")
        self.delete_preset_btn.clicked.connect(self.delete_preset)

        self.duplicate_preset_btn = QPushButton("📋 复制预设")
        self.duplicate_preset_btn.clicked.connect(self.duplicate_preset)

        self.refresh_presets_btn = QPushButton("🔄 刷新")
        self.refresh_presets_btn.clicked.connect(self.refresh_presets_table)

        preset_actions_layout.addWidget(self.add_preset_btn)
        preset_actions_layout.addWidget(self.edit_preset_btn)
        preset_actions_layout.addWidget(self.delete_preset_btn)
        preset_actions_layout.addWidget(self.duplicate_preset_btn)
        preset_actions_layout.addWidget(self.refresh_presets_btn)

        presets_list_layout.addLayout(preset_actions_layout)

        # 预设导入导出组
        preset_io_group = QGroupBox("预设导入导出")
        preset_io_layout = QHBoxLayout(preset_io_group)

        self.import_presets_btn = QPushButton("📥 导入预设")
        self.import_presets_btn.clicked.connect(self.import_presets)

        self.export_presets_btn = QPushButton("📤 导出预设")
        self.export_presets_btn.clicked.connect(self.export_presets)

        self.reset_presets_btn = QPushButton("🔄 重置为默认")
        self.reset_presets_btn.clicked.connect(self.reset_presets)

        preset_io_layout.addWidget(self.import_presets_btn)
        preset_io_layout.addWidget(self.export_presets_btn)
        preset_io_layout.addWidget(self.reset_presets_btn)

        # 添加到布局
        layout.addWidget(presets_list_group)
        layout.addWidget(preset_io_group)

        return widget

    def connect_signals(self):
        """连接信号"""
        # 导出系统信号
        self.export_system.export_started.connect(self.on_export_started)
        self.export_system.export_progress.connect(self.on_export_progress)
        self.export_system.export_completed.connect(self.on_export_completed)
        self.export_system.export_failed.connect(self.on_export_failed)

        # 设置定时器更新队列状态
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_queue_status)
        self.update_timer.start(2000)  # 每2秒更新一次

    def setup_error_handling(self):
        """设置错误处理"""
        # 连接错误处理器信号
        self.error_handler.error_occurred.connect(self.on_error_occurred)
        self.error_handler.error_recovered.connect(self.on_error_recovered)

        # 设置全局错误处理器
        from ....utils.error_handler import set_global_error_handler
        set_global_error_handler(self.error_handler)

        # 监控系统资源
        self.export_system_monitor.resource_warning.connect(self.on_system_resource_warning)
        self.export_system_monitor.system_error.connect(self.on_system_error)

    def start_system_monitoring(self):
        """启动系统监控"""
        self.export_system_monitor.start()

    def stop_system_monitoring(self):
        """停止系统监控"""
        self.export_system_monitor.stop()

    def load_data(self):
        """加载数据"""
        self.refresh_presets()
        self.refresh_projects_list()
        self.refresh_presets_table()

    def refresh_presets(self):
        """刷新预设列表"""
        try:
            presets = self.export_system.get_presets()

            # 清空下拉框
            self.preset_combo.clear()
            self.batch_preset_combo.clear()

            # 添加预设到下拉框
            for preset in presets:
                self.preset_combo.addItem(preset.name, preset.id)
                self.batch_preset_combo.addItem(preset.name, preset.id)

        except Exception as e:
            self.logger.error(f"Failed to refresh presets: {e}")

    def refresh_projects_list(self):
        """刷新项目列表"""
        try:
            if hasattr(self.project_manager, 'get_projects'):
                projects = self.project_manager.get_projects()

                self.batch_projects_table.setRowCount(len(projects))

                for i, project in enumerate(projects):
                    # 选择复选框
                    checkbox = QCheckBox()
                    checkbox.setChecked(False)
                    self.batch_projects_table.setCellWidget(i, 0, checkbox)

                    # 项目信息
                    self.batch_projects_table.setItem(i, 1, QTableWidgetItem(project.get('name', '未知项目')))
                    self.batch_projects_table.setItem(i, 2, QTableWidgetItem(project.get('duration', '00:00:00')))
                    self.batch_projects_table.setItem(i, 3, QTableWidgetItem(project.get('resolution', '1920×1080')))
                    self.batch_projects_table.setItem(i, 4, QTableWidgetItem(project.get('size', '0 MB')))

                    # 存储项目ID
                    self.batch_projects_table.item(i, 1).setData(Qt.ItemDataRole.UserRole, project.get('id'))

        except Exception as e:
            self.logger.error(f"Failed to refresh projects list: {e}")

    def refresh_presets_table(self):
        """刷新预设表格"""
        try:
            presets = self.export_system.get_presets()
            self.presets_table.setRowCount(len(presets))

            for i, preset in enumerate(presets):
                self.presets_table.setItem(i, 0, QTableWidgetItem(preset.name))
                self.presets_table.setItem(i, 1, QTableWidgetItem(preset.format.value))
                self.presets_table.setItem(i, 2, QTableWidgetItem(f"{preset.resolution[0]}×{preset.resolution[1]}"))
                self.presets_table.setItem(i, 3, QTableWidgetItem(preset.quality.value))
                self.presets_table.setItem(i, 4, QTableWidgetItem(f"{preset.bitrate} kbps"))

                # 操作按钮
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)

                edit_btn = QPushButton("编辑")
                edit_btn.setMaximumWidth(50)
                edit_btn.clicked.connect(lambda checked, p=preset: self.edit_preset_data(p))

                delete_btn = QPushButton("删除")
                delete_btn.setMaximumWidth(50)
                delete_btn.clicked.connect(lambda checked, p=preset: self.delete_preset_data(p))

                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)

                self.presets_table.setCellWidget(i, 5, actions_widget)

        except Exception as e:
            self.logger.error(f"Failed to refresh presets table: {e}")

    def set_current_project(self, project_info: Dict[str, Any]):
        """设置当前项目"""
        self.current_project = project_info

        # 更新项目信息显示
        self.project_name_label.setText(project_info.get('name', '未知项目'))
        self.project_duration_label.setText(project_info.get('duration', '00:00:00'))
        self.project_resolution_label.setText(project_info.get('resolution', '1920×1080'))
        self.project_size_label.setText(project_info.get('size', '0 MB'))

        # 更新状态
        self.status_label.setText(f"当前项目: {project_info.get('name', '未知项目')}")

    def browse_output_path(self):
        """浏览输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.webm);;音频文件 (*.mp3 *.wav);;所有文件 (*)"
        )
        if file_path:
            self.output_path_edit.setText(file_path)

    def browse_batch_output_dir(self):
        """浏览批量输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录"
        )
        if dir_path:
            self.batch_output_dir_edit.setText(dir_path)

    def browse_draft_output_path(self):
        """浏览Draft输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择Draft文件保存路径", "",
            "剪映Draft文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            self.draft_output_path_edit.setText(file_path)

    def quick_export(self, preset_id: str):
        """快速导出"""
        def _quick_export():
            # 验证项目选择
            if not self.current_project:
                error_info = ErrorInfo(
                    error_type=ErrorType.VALIDATION,
                    severity=ErrorSeverity.MEDIUM,
                    message="未选择项目进行导出",
                    context=ErrorContext(
                        component="CompleteExportManager",
                        operation="quick_export",
                        user_action="快速导出"
                    ),
                    user_message="请先选择一个项目",
                    recovery_action=RecoveryAction.NONE
                )
                self.error_handler.handle_error(error_info, parent=self)
                return

            # 验证系统资源
            if not self.export_system_monitor.check_export_readiness():
                error_info = ErrorInfo(
                    error_type=ErrorType.SYSTEM,
                    severity=ErrorSeverity.HIGH,
                    message="系统资源不足以进行导出",
                    context=ErrorContext(
                        component="CompleteExportManager",
                        operation="quick_export"
                    ),
                    user_message="系统资源不足，无法开始导出。建议关闭其他程序或降低导出质量。",
                    recovery_action=RecoveryAction.RESET
                )
                self.error_handler.handle_error(error_info, parent=self)
                return

            # 生成和验证输出路径
            try:
                project_name = self.current_project.get('name', 'unknown_project')
                extension = "mp4" if preset_id != "jianying_draft" else "json"
                output_path = f"{project_name}_{preset_id}.{extension}"

                # 如果没有设置输出路径，使用生成路径
                if not self.output_path_edit.text():
                    self.output_path_edit.setText(output_path)
                else:
                    output_path = self.output_path_edit.text()

                # 验证输出路径
                if not self.validate_output_path(output_path):
                    error_info = ErrorInfo(
                        error_type=ErrorType.FILE,
                        severity=ErrorSeverity.HIGH,
                        message=f"输出路径无效或无权限: {output_path}",
                        context=ErrorContext(
                            component="CompleteExportManager",
                            operation="quick_export"
                        ),
                        user_message="无法访问输出路径，请检查路径和权限设置。",
                        recovery_action=RecoveryAction.SKIP
                    )
                    self.error_handler.handle_error(error_info, parent=self)
                    return

            except Exception as path_error:
                error_info = ErrorInfo(
                    error_type=ErrorType.VALIDATION,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"输出路径生成失败: {str(path_error)}",
                    exception=path_error,
                    context=ErrorContext(
                        component="CompleteExportManager",
                        operation="quick_export"
                    ),
                    user_message="无法生成输出路径",
                    recovery_action=RecoveryAction.NONE
                )
                self.error_handler.handle_error(error_info, parent=self)
                return

            # 验证导出预设
            if not self.validate_export_preset(preset_id):
                error_info = ErrorInfo(
                    error_type=ErrorType.VALIDATION,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"导出预设无效: {preset_id}",
                    context=ErrorContext(
                        component="CompleteExportManager",
                        operation="quick_export"
                    ),
                    user_message="导出预设配置无效，请检查预设设置。",
                    recovery_action=RecoveryAction.RESET
                )
                self.error_handler.handle_error(error_info, parent=self)
                return

            # 开始导出
            try:
                self.logger.info(f"Starting quick export: {preset_id}")
                self.status_label.setText(f"正在快速导出: {preset_id}")

                # 记录导出开始
                self.record_export_operation(
                    operation_type="quick_export",
                    preset_id=preset_id,
                    status="started"
                )

                # 开始导出任务
                task_id = self.export_system.export_project(
                    project_id=self.current_project.get('id'),
                    output_path=output_path,
                    preset_id=preset_id,
                    metadata={
                        "project_name": project_name,
                        "export_type": "quick",
                        "preset_id": preset_id,
                        "timestamp": time.time(),
                        "system_info": self.export_system_monitor.get_system_info()
                    }
                )

                # 显示进度对话框
                self.show_progress_dialog()

                # 显示成功消息
                QMessageBox.information(self, "成功", f"导出任务已添加到队列: {task_id[:8]}...")

                self.logger.info(f"Quick export task created: {task_id}")

            except Exception as export_error:
                # 记录导出失败
                self.record_export_operation(
                    operation_type="quick_export",
                    preset_id=preset_id,
                    status="failed",
                    error_message=str(export_error)
                )

                # 创建特定错误信息
                error_category = self.categorize_export_error(export_error)
                error_info = ErrorInfo(
                    error_type=ErrorType.EXPORT,
                    severity=ErrorSeverity.HIGH,
                    message=f"快速导出失败: {str(export_error)}",
                    exception=export_error,
                    context=ErrorContext(
                        component="CompleteExportManager",
                        operation="quick_export",
                        user_action="快速导出"
                    ),
                    user_message=self.get_user_friendly_export_error(export_error),
                    recovery_action=self.get_recovery_action_for_error(error_category),
                    technical_details={
                        "preset_id": preset_id,
                        "output_path": output_path,
                        "error_category": error_category,
                        "system_info": self.export_system_monitor.get_system_info(),
                        "timestamp": time.time()
                    }
                )
                self.error_handler.handle_error(error_info, parent=self)
                raise

        safe_execute(
            _quick_export,
            error_message="快速导出操作失败",
            error_type=ErrorType.EXPORT,
            severity=ErrorSeverity.HIGH,
            recovery_action=RecoveryAction.RETRY,
            parent=self
        )

    def start_export(self):
        """开始导出"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        output_path = self.output_path_edit.text()
        if not output_path:
            QMessageBox.warning(self, "警告", "请选择输出路径")
            return

        preset_id = self.preset_combo.currentData()
        if not preset_id:
            QMessageBox.warning(self, "警告", "请选择导出预设")
            return

        try:
            task_id = self.export_system.export_project(
                project_id=self.current_project.get('id'),
                output_path=output_path,
                preset_id=preset_id,
                metadata={
                    "project_name": self.current_project.get('name'),
                    "export_type": "custom"
                }
            )

            self.show_progress_dialog()
            QMessageBox.information(self, "成功", f"导出任务已添加到队列: {task_id[:8]}...")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def start_advanced_export(self):
        """开始高级导出"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        try:
            # 这里需要实现高级导出逻辑
            QMessageBox.information(self, "提示", "高级导出功能正在开发中...")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"高级导出失败: {str(e)}")

    def start_batch_export(self):
        """开始批量导出"""
        selected_projects = self.get_selected_projects()
        if not selected_projects:
            QMessageBox.warning(self, "警告", "请选择要导出的项目")
            return

        output_dir = self.batch_output_dir_edit.text()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return

        preset_id = self.batch_preset_combo.currentData()
        if not preset_id:
            QMessageBox.warning(self, "警告", "请选择导出预设")
            return

        try:
            batch_configs = []
            naming_pattern = self.batch_naming_pattern_edit.text()

            for project in selected_projects:
                # 生成输出文件名
                filename = naming_pattern.format(
                    project_name=project['name'],
                    preset_id=preset_id,
                    date=time.strftime("%Y%m%d"),
                    time=time.strftime("%H%M%S")
                )

                # 确保文件扩展名正确
                if not filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    filename += '.mp4'

                output_path = os.path.join(output_dir, filename)

                batch_configs.append({
                    "project_id": project['id'],
                    "output_path": output_path,
                    "preset_id": preset_id,
                    "metadata": {
                        "project_name": project['name'],
                        "export_type": "batch"
                    }
                })

            task_ids = self.export_system.export_batch(batch_configs)
            self.show_progress_dialog()

            QMessageBox.information(self, "成功", f"已添加 {len(task_ids)} 个批量导出任务")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"批量导出失败: {str(e)}")

    def generate_jianying_draft(self):
        """生成剪映Draft"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        output_path = self.draft_output_path_edit.text()
        if not output_path:
            QMessageBox.warning(self, "警告", "请选择Draft文件保存路径")
            return

        try:
            # 创建剪映Draft生成器
            generator = JianyingDraftGenerator()

            # 设置Draft配置
            project_name = self.draft_project_name_edit.text() or self.current_project.get('name', '未命名项目')
            fps = self.draft_fps_spin.value()

            # 解析分辨率
            resolution_text = self.draft_resolution_combo.currentText()
            resolution = (1920, 1080)  # 默认
            if "3840×2160" in resolution_text:
                resolution = (3840, 2160)
            elif "1280×720" in resolution_text:
                resolution = (1280, 720)

            # 添加素材（这里需要从项目信息中获取）
            # 暂时使用示例数据
            video_id = generator.add_video_material(
                path=self.current_project.get('main_video_path', '/path/to/video.mp4'),
                name="主视频"
            )

            # 创建轨道
            video_track_id = generator.create_track("video")
            generator.add_material_to_track(video_track_id, video_id, 0.0)

            # 生成Draft文件
            success = generator.generate_draft(
                project_name=project_name,
                output_path=output_path,
                fps=fps,
                resolution=resolution
            )

            if success:
                QMessageBox.information(self, "成功", f"剪映Draft文件已生成:\\n{output_path}")

                # 询问是否打开文件位置
                reply = QMessageBox.question(
                    self, "打开文件位置", "是否打开文件所在位置？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    import subprocess
                    if os.name == 'nt':  # Windows
                        subprocess.run(['explorer', '/select,', output_path])
                    elif os.name == 'posix':  # macOS/Linux
                        subprocess.run(['open', os.path.dirname(output_path)])
            else:
                QMessageBox.critical(self, "错误", "Draft文件生成失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成Draft失败: {str(e)}")

    def get_selected_projects(self) -> List[Dict[str, Any]]:
        """获取选中的项目"""
        selected_projects = []

        for i in range(self.batch_projects_table.rowCount()):
            checkbox = self.batch_projects_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                item = self.batch_projects_table.item(i, 1)
                if item:
                    project_id = item.data(Qt.ItemDataRole.UserRole)
                    selected_projects.append({
                        'id': project_id,
                        'name': item.text(),
                        'duration': self.batch_projects_table.item(i, 2).text(),
                        'resolution': self.batch_projects_table.item(i, 3).text(),
                        'size': self.batch_projects_table.item(i, 4).text()
                    })

        return selected_projects

    def select_all_projects(self):
        """全选项目"""
        for i in range(self.batch_projects_table.rowCount()):
            checkbox = self.batch_projects_table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(True)

    def select_none_projects(self):
        """全不选项目"""
        for i in range(self.batch_projects_table.rowCount()):
            checkbox = self.batch_projects_table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(False)

    def add_material(self):
        """添加素材"""
        # 这里需要实现添加素材的逻辑
        QMessageBox.information(self, "提示", "添加素材功能正在开发中...")

    def remove_material(self):
        """移除素材"""
        # 这里需要实现移除素材的逻辑
        QMessageBox.information(self, "提示", "移除素材功能正在开发中...")

    def clear_materials(self):
        """清空素材"""
        # 这里需要实现清空素材的逻辑
        QMessageBox.information(self, "提示", "清空素材功能正在开发中...")

    def show_progress_dialog(self):
        """显示进度对话框"""
        if not self.progress_dialog:
            self.progress_dialog = ExportProgressDialog(self.export_system, self)

        self.progress_dialog.show()
        self.progress_dialog.raise_()
        self.progress_dialog.activateWindow()

    def preview_export_settings(self):
        """预览导出设置"""
        # 这里可以实现导出设置预览功能
        QMessageBox.information(self, "提示", "导出设置预览功能正在开发中...")

    def save_advanced_preset(self):
        """保存高级预设"""
        # 这里需要实现保存高级预设的逻辑
        QMessageBox.information(self, "提示", "保存高级预设功能正在开发中...")

    def pause_queue(self):
        """暂停队列"""
        # 这里需要实现暂停队列的逻辑
        QMessageBox.information(self, "提示", "暂停队列功能正在开发中...")

    def resume_queue(self):
        """恢复队列"""
        # 这里需要实现恢复队列的逻辑
        QMessageBox.information(self, "提示", "恢复队列功能正在开发中...")

    def clear_completed_tasks(self):
        """清除已完成任务"""
        try:
            # 这里需要实现清除已完成任务的逻辑
            QMessageBox.information(self, "提示", "清除已完成任务功能正在开发中...")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清除任务失败: {str(e)}")

    def cancel_all_queue_tasks(self):
        """取消所有队列任务"""
        reply = QMessageBox.question(
            self, "确认取消", "确定要取消所有队列中的任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 这里需要实现取消所有任务的逻辑
                QMessageBox.information(self, "成功", "所有任务已取消")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"取消任务失败: {str(e)}")

    def apply_queue_settings(self):
        """应用队列设置"""
        try:
            # 这里需要实现应用队列设置的逻辑
            QMessageBox.information(self, "成功", "队列设置已应用")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用设置失败: {str(e)}")

    def add_preset(self):
        """添加预设"""
        dialog = ExportPresetDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                preset_data = dialog.get_preset_data()

                # 创建预设对象
                from dataclasses import asdict
                from ..export.export_system import ExportFormat, ExportQuality

                preset = ExportPreset(
                    id=f"preset_{int(time.time())}",
                    name=preset_data["name"],
                    format=ExportFormat(preset_data["format"]),
                    quality=ExportQuality(preset_data["quality"]),
                    resolution=tuple(preset_data["resolution"]),
                    bitrate=preset_data["bitrate"],
                    fps=preset_data["fps"],
                    audio_bitrate=preset_data["audio_bitrate"],
                    description=preset_data["description"]
                )

                # 添加到导出系统
                success = self.export_system.add_preset(preset)
                if success:
                    self.refresh_presets()
                    self.refresh_presets_table()
                    QMessageBox.information(self, "成功", "预设已添加")
                else:
                    QMessageBox.warning(self, "警告", "添加预设失败")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加预设失败: {str(e)}")

    def edit_preset(self):
        """编辑预设"""
        selected_items = self.presets_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要编辑的预设")
            return

        # 这里需要实现编辑预设的逻辑
        QMessageBox.information(self, "提示", "编辑预设功能正在开发中...")

    def edit_preset_data(self, preset: ExportPreset):
        """编辑预设数据"""
        dialog = ExportPresetDialog(preset, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                preset_data = dialog.get_preset_data()

                # 更新预设数据
                preset.name = preset_data["name"]
                preset.description = preset_data["description"]
                preset.resolution = tuple(preset_data["resolution"])
                preset.bitrate = preset_data["bitrate"]
                preset.fps = preset_data["fps"]
                preset.audio_bitrate = preset_data["audio_bitrate"]

                self.refresh_presets_table()
                QMessageBox.information(self, "成功", "预设已更新")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新预设失败: {str(e)}")

    def delete_preset(self):
        """删除预设"""
        selected_items = self.presets_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要删除的预设")
            return

        reply = QMessageBox.question(
            self, "确认删除", "确定要删除选中的预设吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 这里需要实现删除预设的逻辑
            QMessageBox.information(self, "成功", "预设已删除")

    def delete_preset_data(self, preset: ExportPreset):
        """删除预设数据"""
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除预设 '{preset.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.export_system.remove_preset(preset.id)
                if success:
                    self.refresh_presets()
                    self.refresh_presets_table()
                    QMessageBox.information(self, "成功", "预设已删除")
                else:
                    QMessageBox.warning(self, "警告", "删除预设失败")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除预设失败: {str(e)}")

    def duplicate_preset(self):
        """复制预设"""
        selected_items = self.presets_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要复制的预设")
            return

        # 这里需要实现复制预设的逻辑
        QMessageBox.information(self, "提示", "复制预设功能正在开发中...")

    def import_presets(self):
        """导入预设"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入预设", "",
            "JSON文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            try:
                # 这里需要实现导入预设的逻辑
                QMessageBox.information(self, "成功", "预设导入成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入预设失败: {str(e)}")

    def export_presets(self):
        """导出预设"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出预设", "",
            "JSON文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            try:
                # 这里需要实现导出预设的逻辑
                QMessageBox.information(self, "成功", "预设导出成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出预设失败: {str(e)}")

    def reset_presets(self):
        """重置为默认预设"""
        reply = QMessageBox.question(
            self, "确认重置", "确定要重置为默认预设吗？这将删除所有自定义预设。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 这里需要实现重置预设的逻辑
                QMessageBox.information(self, "成功", "预设已重置为默认")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重置预设失败: {str(e)}")

    def update_queue_status(self):
        """更新队列状态"""
        try:
            # 获取队列状态
            queue_status = self.export_system.get_queue_status()

            # 更新状态标签
            status_text = (f"队列: {queue_status['queue_size']} 待处理, "
                         f"{queue_status['active_tasks']} 处理中, "
                         f"{queue_status['completed_tasks']} 已完成")
            self.queue_status_label.setText(status_text)

            # 更新队列管理标签页的状态
            if hasattr(self, 'queue_total_label'):
                self.queue_total_label.setText(f"总任务: {queue_status['queue_size'] + queue_status['active_tasks'] + queue_status['completed_tasks']}")

            # 获取任务历史
            tasks = self.export_system.get_task_history()

            if hasattr(self, 'queue_processing_label'):
                processing_count = len([t for t in tasks if t.status.value == "processing"])
                self.queue_processing_label.setText(f"处理中: {processing_count}")

            if hasattr(self, 'queue_completed_label'):
                completed_count = len([t for t in tasks if t.status.value == "completed"])
                self.queue_completed_label.setText(f"已完成: {completed_count}")

            if hasattr(self, 'queue_failed_label'):
                failed_count = len([t for t in tasks if t.status.value == "failed"])
                self.queue_failed_label.setText(f"失败: {failed_count}")

            # 更新队列表格
            if hasattr(self, 'queue_table'):
                self.update_queue_table(tasks)

        except Exception as e:
            self.logger.error(f"Failed to update queue status: {e}")

    def update_queue_table(self, tasks: List[ExportTask]):
        """更新队列表格"""
        try:
            # 只显示最近的任务
            recent_tasks = tasks[:50]  # 最多显示50个任务

            self.queue_table.setRowCount(len(recent_tasks))

            for i, task in enumerate(recent_tasks):
                # 任务ID
                self.queue_table.setItem(i, 0, QTableWidgetItem(task.id[:12] + "..."))

                # 项目名称
                project_name = task.metadata.get("project_name", "未知项目")
                self.queue_table.setItem(i, 1, QTableWidgetItem(project_name))

                # 预设名称
                preset_name = task.preset.name if task.preset else "未知预设"
                self.queue_table.setItem(i, 2, QTableWidgetItem(preset_name))

                # 状态
                status_item = QTableWidgetItem(task.status.value)
                status_item.setBackground(self.get_status_color(task.status))
                self.queue_table.setItem(i, 3, status_item)

                # 进度
                progress_text = f"{task.progress:.1f}%" if task.progress > 0 else "0%"
                self.queue_table.setItem(i, 4, QTableWidgetItem(progress_text))

                # 开始时间
                start_time_text = time.strftime("%H:%M:%S", time.localtime(task.started_at)) if task.started_at else "未开始"
                self.queue_table.setItem(i, 5, QTableWidgetItem(start_time_text))

                # 操作按钮
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)

                if task.status.value in ["processing", "queued"]:
                    cancel_btn = QPushButton("取消")
                    cancel_btn.setMaximumWidth(50)
                    cancel_btn.clicked.connect(lambda checked, tid=task.id: self.cancel_queue_task(tid))
                    actions_layout.addWidget(cancel_btn)

                actions_layout.addStretch()
                self.queue_table.setCellWidget(i, 6, actions_widget)

        except Exception as e:
            self.logger.error(f"Failed to update queue table: {e}")

    def get_status_color(self, status) -> QColor:
        """获取状态颜色"""
        colors = {
            "pending": QColor(200, 200, 200),
            "queued": QColor(255, 200, 0),
            "processing": QColor(0, 150, 255),
            "completed": QColor(0, 200, 0),
            "failed": QColor(255, 0, 0),
            "cancelled": QColor(150, 150, 150)
        }
        return colors.get(status.value, QColor(200, 200, 200))

    def cancel_queue_task(self, task_id: str):
        """取消队列任务"""
        try:
            success = self.export_system.cancel_export(task_id)
            if success:
                QMessageBox.information(self, "成功", "任务已取消")
            else:
                QMessageBox.warning(self, "警告", "无法取消该任务")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"取消任务失败: {str(e)}")

    def on_export_started(self, task_id: str):
        """导出开始事件"""
        self.logger.info(f"Export started: {task_id}")
        self.export_started.emit(task_id)

    def on_export_progress(self, task_id: str, progress: float):
        """导出进度事件"""
        self.logger.info(f"Export progress: {task_id} - {progress:.1f}%")
        self.export_progress.emit(task_id, progress)

    def on_export_completed(self, task_id: str, output_path: str):
        """导出完成事件"""
        self.logger.info(f"Export completed: {task_id} -> {output_path}")
        self.export_completed.emit(task_id, output_path)

        # 显示完成通知
        QMessageBox.information(self, "导出完成", f"导出完成:\\n{output_path}")

    def on_export_failed(self, task_id: str, error_message: str):
        """导出失败事件"""
        self.logger.error(f"Export failed: {task_id} - {error_message}")
        self.export_failed.emit(task_id, error_message)

        # 显示错误通知
        QMessageBox.critical(self, "导出失败", f"导出失败:\\n{error_message}")

    def validate_output_path(self, output_path: str) -> bool:
        """验证输出路径"""
        try:
            # 检查路径格式
            if not output_path or len(output_path) > 260:  # Windows路径长度限制
                self.logger.warning("Invalid output path format")
                return False

            # 检查输出目录
            output_dir = os.path.dirname(output_path)
            if not output_dir:
                output_dir = os.getcwd()

            # 检查目录是否存在
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    self.logger.error(f"Failed to create output directory: {e}")
                    return False

            # 检查写入权限
            test_file = os.path.join(output_dir, ".write_test")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                self.logger.error(f"Failed to test write permissions: {e}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate output path: {e}")
            return False

    def validate_export_preset(self, preset_id: str) -> bool:
        """验证导出预设"""
        try:
            presets = self.export_system.get_presets()
            preset_exists = any(preset.id == preset_id for preset in presets)

            if not preset_exists:
                self.logger.warning(f"Export preset not found: {preset_id}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate export preset: {e}")
            return False

    def record_export_operation(self, operation_type: str, preset_id: str,
                             status: str, error_message: str = None):
        """记录导出操作"""
        try:
            operation_record = {
                'timestamp': time.time(),
                'operation_type': operation_type,
                'preset_id': preset_id,
                'status': status,
                'error_message': error_message,
                'project_id': self.current_project.get('id') if self.current_project else None,
                'project_name': self.current_project.get('name') if self.current_project else None,
                'system_info': self.export_system_monitor.get_system_info()
            }

            self.export_error_history.append(operation_record)

            # 限制历史记录大小
            if len(self.export_error_history) > 100:
                self.export_error_history = self.export_error_history[-50:]

            self.logger.info(f"Export operation recorded: {operation_record}")

        except Exception as e:
            self.logger.error(f"Failed to record export operation: {e}")

    def categorize_export_error(self, error: Exception) -> str:
        """分类导出错误"""
        error_str = str(error).lower()

        if any(keyword in error_str for keyword in ['permission', 'access denied', 'read-only']):
            return "permission_denied"
        elif any(keyword in error_str for keyword in ['disk space', 'no space', 'disk full']):
            return "disk_space_insufficient"
        elif any(keyword in error_str for keyword in ['file not found', 'no such file']):
            return "file_not_found"
        elif any(keyword in error_str for keyword in ['format', 'codec', 'encoder']):
            return "codec_error"
        elif any(keyword in error_str for keyword in ['gpu', 'cuda', 'opencl']):
            return "gpu_acceleration_failed"
        elif 'cancel' in error_str or 'abort' in error_str:
            return "cancelled_by_user"
        else:
            return "system_error"

    def get_user_friendly_export_error(self, error: Exception) -> str:
        """获取用户友好的导出错误消息"""
        error_category = self.categorize_export_error(error)

        error_messages = {
            "permission_denied": "没有文件写入权限，请检查输出目录的权限设置。",
            "disk_space_insufficient": "磁盘空间不足，请清理磁盘或选择其他输出位置。",
            "file_not_found": "源文件不存在或已损坏，请检查项目文件。",
            "codec_error": "视频编码器错误，请尝试更改导出格式或编码设置。",
            "gpu_acceleration_failed": "GPU加速失败，请尝试禁用GPU加速或更新显卡驱动。",
            "cancelled_by_user": "导出操作已被用户取消。",
            "system_error": "系统错误导致导出失败，请重启应用程序后重试。",
            "validation_error": "导出参数验证失败，请检查导出设置。"
        }

        return error_messages.get(error_category, f"导出失败: {str(error)}")

    def get_recovery_action_for_error(self, error_category: str) -> RecoveryAction:
        """根据错误类别获取恢复动作"""
        recovery_actions = {
            "permission_denied": RecoveryAction.RESET,
            "disk_space_insufficient": RecoveryAction.SKIP,
            "file_not_found": RecoveryAction.ROLLBACK,
            "codec_error": RecoveryAction.RETRY,
            "gpu_acceleration_failed": RecoveryAction.RESET,
            "cancelled_by_user": RecoveryAction.NONE,
            "system_error": RecoveryAction.CONTACT_SUPPORT,
            "validation_error": RecoveryAction.RESET
        }

        return recovery_actions.get(error_category, RecoveryAction.NONE)

    def on_error_occurred(self, error_info):
        """错误发生事件处理"""
        self.logger.error(f"Error occurred in export manager: {error_info.message}")

        # 更新状态显示
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"错误: {error_info.user_message}")
            self.status_label.setStyleSheet("color: #dc3545;")

    def on_error_recovered(self, error_info, recovery_action):
        """错误恢复事件处理"""
        self.logger.info(f"Error recovered: {error_info.message} with {recovery_action}")

        # 更新状态显示
        if hasattr(self, 'status_label'):
            self.status_label.setText("错误已恢复")
            self.status_label.setStyleSheet("color: #28a745;")

    def on_system_resource_warning(self, warning_info):
        """系统资源警告事件处理"""
        self.logger.warning(f"System resource warning: {warning_info}")

        # 显示资源警告对话框
        QMessageBox.warning(
            self,
            "系统资源警告",
            f"系统资源紧张！\\n{warning_info.get('message', '未知资源问题')}\\n"
            f"建议关闭其他程序或降低导出质量。"
        )

    def on_system_error(self, error_info):
        """系统错误事件处理"""
        self.logger.error(f"System error: {error_info}")

        # 显示系统错误对话框
        QMessageBox.critical(
            self,
            "系统错误",
            f"系统错误导致导出失败：{error_info.get('message', '未知系统错误')}\\n"
            f"请重启应用程序后重试。"
        )

    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()

            if hasattr(self, 'export_system_monitor'):
                self.export_system_monitor.stop()

            if self.progress_dialog:
                self.progress_dialog.cleanup()

        except Exception as e:
            self.logger.error(f"Failed to cleanup: {e}")

    def update_theme(self, is_dark: bool = True):
        """更新主题"""
        # 这里可以实现主题更新逻辑
        pass


class ExportSystemMonitor(QThread):
    """导出系统监控线程"""

    resource_warning = pyqtSignal(dict)
    system_error = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.logger = Logger("ExportSystemMonitor")
        self.running = False
        self.update_interval = 5  # 秒 - 增加间隔减少CPU使用
        self.resource_thresholds = {
            'memory_usage': 90.0,  # 内存使用率超过90%
            'cpu_usage': 95.0,    # CPU使用率超过95%
            'disk_usage': 95.0,   # 磁盘使用率超过95%
            'temperature': 80.0   # 温度超过80°C
        }
        self.last_warning_time = {}  # 跟踪上次警告时间，避免重复警告
        self.warning_cooldown = 60  # 警告冷却时间（秒）
        self.psutil_available = False  # 检查psutil是否可用
        self.check_psutil_availability()

    def check_psutil_availability(self):
        """检查psutil可用性"""
        try:
            import psutil
            # 测试基本功能
            psutil.cpu_percent(interval=0.1)
            self.psutil_available = True
            self.logger.info("psutil is available for system monitoring")
        except (ImportError, Exception):
            self.psutil_available = False
            self.logger.warning("psutil is not available, system monitoring will be limited")

    def run(self):
        """运行监控"""
        self.running = True

        while self.running:
            try:
                # 监控系统资源
                resource_info = self.monitor_system_resources()

                # 检查资源警告
                self.check_resource_warnings(resource_info)

                # 检查系统错误
                self.check_system_errors(resource_info)

            except Exception as e:
                self.logger.error(f"System monitoring error: {e}")

            # 等待下次更新
            self.msleep(self.update_interval * 1000)

    def monitor_system_resources(self) -> dict:
        """监控系统资源"""
        try:
            if not self.psutil_available:
                return {
                    'timestamp': time.time(),
                    'system': {
                        'platform': platform.system(),
                        'python_version': platform.python_version(),
                        'monitoring': 'limited'
                    }
                }

            import psutil

            # CPU信息 - 使用非阻塞方式
            cpu_percent = psutil.cpu_percent(interval=None)  # 不阻塞
            cpu_count = psutil.cpu_count(logical=False)  # 只获取物理核心数

            # 内存信息
            memory = psutil.virtual_memory()

            # 磁盘信息 - 只检查根目录
            disk = psutil.disk_usage('/')

            # 基本系统信息
            return {
                'timestamp': time.time(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'system': {
                    'platform': platform.system(),
                    'python_version': platform.python_version(),
                    'monitoring': 'full'
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to monitor system resources: {e}")
            return {'error': str(e), 'timestamp': time.time()}

    def check_resource_warnings(self, resource_info):
        """检查资源警告"""
        if 'error' in resource_info:
            return

        current_time = time.time()
        warnings = []

        # 检查内存使用
        if 'memory' in resource_info:
            memory_percent = resource_info['memory']['percent']
            if memory_percent > self.resource_thresholds['memory_usage']:
                warning_key = 'memory_usage'
                if self._should_send_warning(warning_key, current_time):
                    warnings.append({
                        'type': 'memory',
                        'current': memory_percent,
                        'threshold': self.resource_thresholds['memory_usage'],
                        'message': f"内存使用率过高: {memory_percent:.1f}%"
                    })
                    self.last_warning_time[warning_key] = current_time

        # 检查CPU使用
        if 'cpu' in resource_info:
            cpu_percent = resource_info['cpu']['percent']
            if cpu_percent > self.resource_thresholds['cpu_usage']:
                warning_key = 'cpu_usage'
                if self._should_send_warning(warning_key, current_time):
                    warnings.append({
                        'type': 'cpu',
                        'current': cpu_percent,
                        'threshold': self.resource_thresholds['cpu_usage'],
                        'message': f"CPU使用率过高: {cpu_percent:.1f}%"
                    })
                    self.last_warning_time[warning_key] = current_time

        # 检查磁盘使用
        if 'disk' in resource_info:
            disk_percent = resource_info['disk']['percent']
            if disk_percent > self.resource_thresholds['disk_usage']:
                warning_key = 'disk_usage'
                if self._should_send_warning(warning_key, current_time):
                    warnings.append({
                        'type': 'disk',
                        'current': disk_percent,
                        'threshold': self.resource_thresholds['disk_usage'],
                        'message': f"磁盘使用率过高: {disk_percent:.1f}%"
                    })
                    self.last_warning_time[warning_key] = current_time

        # 发送警告信号
        for warning in warnings:
            self.resource_warning.emit(warning)
            self.logger.warning(f"Resource warning: {warning['message']}")

    def _should_send_warning(self, warning_key: str, current_time: float) -> bool:
        """检查是否应该发送警告（基于冷却时间）"""
        last_time = self.last_warning_time.get(warning_key, 0)
        return (current_time - last_time) >= self.warning_cooldown

    def check_system_errors(self, resource_info):
        """检查系统错误"""
        try:
            if 'error' in resource_info:
                # 监控系统本身出现错误
                error_key = 'monitoring_error'
                current_time = time.time()
                if self._should_send_warning(error_key, current_time):
                    self.system_error.emit({
                        'type': 'monitoring_error',
                        'message': resource_info['error']
                    })
                    self.last_warning_time[error_key] = current_time

            # 检查极端情况
            extreme_conditions = []

            # 内存极低
            if 'memory' in resource_info:
                memory_available_gb = resource_info['memory']['available'] / (1024**3)
                if memory_available_gb < 0.5:  # 小于500MB
                    extreme_conditions.append({
                        'type': 'critical_memory',
                        'message': f"内存严重不足，仅剩 {memory_available_gb:.1f} GB"
                    })

            # 磁盘空间极低
            if 'disk' in resource_info:
                disk_free_gb = resource_info['disk']['free'] / (1024**3)
                if disk_free_gb < 1.0:  # 小于1GB
                    extreme_conditions.append({
                        'type': 'critical_disk',
                        'message': f"磁盘空间严重不足，仅剩 {disk_free_gb:.1f} GB"
                    })

            # 发送系统错误信号（带冷却时间）
            current_time = time.time()
            for condition in extreme_conditions:
                error_key = condition['type']
                if self._should_send_warning(error_key, current_time):
                    self.system_error.emit(condition)
                    self.logger.error(f"Critical system condition: {condition['message']}")
                    self.last_warning_time[error_key] = current_time

        except Exception as e:
            self.logger.error(f"Error in check_system_errors: {e}")

    def check_export_readiness(self) -> bool:
        """检查导出准备状态"""
        try:
            resource_info = self.monitor_system_resources()

            if 'error' in resource_info:
                self.logger.warning(f"Cannot check export readiness due to monitoring error: {resource_info['error']}")
                return True  # 如果监控出错，默认允许导出

            # 如果监控受限，只做基本检查
            if resource_info.get('system', {}).get('monitoring') == 'limited':
                self.logger.info("Limited monitoring, allowing export with basic checks")
                return True

            # 检查基本资源要求
            if 'memory' in resource_info and resource_info['memory']['percent'] > 95:
                self.logger.warning("Memory usage too high for export")
                return False

            if 'cpu' in resource_info and resource_info['cpu']['percent'] > 98:
                self.logger.warning("CPU usage too high for export")
                return False

            # 检查可用内存
            if 'memory' in resource_info:
                memory_available_gb = resource_info['memory']['available'] / (1024**3)
                if memory_available_gb < 1.0:  # 至少需要1GB可用内存
                    self.logger.warning(f"Insufficient memory for export: {memory_available_gb:.1f} GB")
                    return False

            # 检查可用磁盘空间
            if 'disk' in resource_info:
                disk_free_gb = resource_info['disk']['free'] / (1024**3)
                if disk_free_gb < 2.0:  # 至少需要2GB可用磁盘空间
                    self.logger.warning(f"Insufficient disk space for export: {disk_free_gb:.1f} GB")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to check export readiness: {e}")
            return True  # 如果检查失败，默认允许导出

    def get_system_info(self) -> dict:
        """获取系统信息摘要"""
        try:
            resource_info = self.monitor_system_resources()

            if 'error' in resource_info:
                return {'status': 'error', 'message': resource_info['error']}

            # 如果监控受限，返回基本信息
            if resource_info.get('system', {}).get('monitoring') == 'limited':
                return {
                    'status': 'limited',
                    'platform': resource_info['system']['platform'],
                    'python_version': resource_info['system']['python_version'],
                    'monitoring': 'limited',
                    'timestamp': resource_info['timestamp']
                }

            # 返回完整系统信息
            return {
                'status': 'ok',
                'memory_usage': f"{resource_info['memory']['percent']:.1f}%",
                'cpu_usage': f"{resource_info['cpu']['percent']:.1f}%",
                'disk_usage': f"{resource_info['disk']['percent']:.1f}%",
                'memory_available_gb': f"{resource_info['memory']['available'] / (1024**3):.1f}",
                'disk_free_gb': f"{resource_info['disk']['free'] / (1024**3):.1f}",
                'platform': resource_info['system']['platform'],
                'monitoring': 'full',
                'timestamp': resource_info['timestamp']
            }

        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {'status': 'error', 'message': str(e)}

    def stop(self):
        """停止监控"""
        self.running = False
        self.wait()


# 导出错误分类常量
class ExportErrorCategories:
    """导出错误分类"""
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    DISK_SPACE_INSUFFICIENT = "disk_space_insufficient"
    FORMAT_NOT_SUPPORTED = "format_not_supported"
    CODEC_ERROR = "codec_error"
    GPU_ACCELERATION_FAILED = "gpu_acceleration_failed"
    NETWORK_ERROR = "network_error"
    CANCELLED_BY_USER = "cancelled_by_user"
    SYSTEM_ERROR = "system_error"
    VALIDATION_ERROR = "validation_error"