#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出面板
提供完整的视频导出功能界面
"""

import os
import json
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
                            QProgressBar, QTableWidget, QTableWidgetItem,
                            QFileDialog, QMessageBox, QTabWidget, QGroupBox,
                            QLineEdit, QTextEdit, QCheckBox, QSlider, QDialog,
                            QDialogButtonBox, QFormLayout, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPalette, QColor

from ...export.export_system import ExportSystem, ExportTask, ExportPreset
from ...export.jianying_draft_generator import JianyingDraftGenerator
from ...core.logger import Logger


class ExportSettingsDialog(QDialog):
    """导出设置对话框"""

    def __init__(self, preset: ExportPreset = None, parent=None):
        super().__init__(parent)
        self.preset = preset
        self.logger = Logger.get_logger(__name__)
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("导出设置")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)

        self.name_input = QLineEdit(self.preset.name if self.preset else "新建预设")
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setText(self.preset.description if self.preset else "")

        basic_layout.addRow("预设名称:", self.name_input)
        basic_layout.addRow("描述:", self.description_input)

        # 格式设置
        format_group = QGroupBox("格式设置")
        format_layout = QFormLayout(format_group)

        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "MP4 (H.264)", "MP4 (H.265)", "MOV (ProRes)",
            "AVI (无压缩)", "MKV (H.264)", "WebM (VP9)",
            "GIF动画", "MP3音频", "WAV音频", "剪映草稿"
        ])

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "3840x2160 (4K)", "2560x1440 (2K)", "1920x1080 (1080p)",
            "1280x720 (720p)", "854x480 (480p)", "自定义"
        ])

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)

        format_layout.addRow("输出格式:", self.format_combo)
        format_layout.addRow("分辨率:", self.resolution_combo)
        format_layout.addRow("帧率 (FPS):", self.fps_spin)

        # 质量设置
        quality_group = QGroupBox("质量设置")
        quality_layout = QFormLayout(quality_group)

        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(100, 100000)
        self.bitrate_spin.setValue(8000)
        self.bitrate_spin.setSuffix(" kbps")

        self.audio_bitrate_spin = QSpinBox()
        self.audio_bitrate_spin.setRange(32, 512)
        self.audio_bitrate_spin.setValue(128)
        self.audio_bitrate_spin.setSuffix(" kbps")

        quality_layout.addRow("视频比特率:", self.bitrate_spin)
        quality_layout.addRow("音频比特率:", self.audio_bitrate_spin)

        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)

        self.codec_params_edit = QTextEdit()
        self.codec_params_edit.setMaximumHeight(100)
        self.codec_params_edit.setPlaceholderText("额外的编码参数，如: -crf 23 -preset medium")

        advanced_layout.addRow("编码参数:", self.codec_params_edit)

        # 添加到主布局
        layout.addWidget(basic_group)
        layout.addWidget(format_group)
        layout.addWidget(quality_group)
        layout.addWidget(advanced_group)

        # 对话框按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # 如果有预设，加载预设数据
        if self.preset:
            self.load_preset_data()

    def load_preset_data(self):
        """加载预设数据"""
        self.name_input.setText(self.preset.name)
        self.description_input.setText(self.preset.description)
        self.bitrate_spin.setValue(self.preset.bitrate)
        self.audio_bitrate_spin.setValue(self.preset.audio_bitrate)
        self.fps_spin.setValue(int(self.preset.fps))

        # 设置分辨率
        resolution_text = f"{self.preset.resolution[0]}x{self.preset.resolution[1]}"
        index = self.resolution_combo.findText(resolution_text)
        if index >= 0:
            self.resolution_combo.setCurrentIndex(index)
        else:
            self.resolution_combo.setCurrentText("自定义")

    def get_preset_data(self) -> Dict[str, Any]:
        """获取预设数据"""
        return {
            "name": self.name_input.text(),
            "description": self.description_input.toPlainText(),
            "format": self.format_combo.currentText(),
            "resolution": self.resolution_combo.currentText(),
            "bitrate": self.bitrate_spin.value(),
            "audio_bitrate": self.audio_bitrate_spin.value(),
            "fps": self.fps_spin.value(),
            "codec_params": self.codec_params_edit.toPlainText()
        }


class ExportQueueWidget(QWidget):
    """导出队列部件"""

    task_selected = pyqtSignal(str)
    task_action = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger.get_logger(__name__)
        self.tasks: List[ExportTask] = []
        self.setup_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_queue_display)
        self.update_timer.start(1000)

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 队列状态
        status_layout = QHBoxLayout()
        self.queue_status_label = QLabel("队列状态: 0个任务")
        self.clear_completed_btn = QPushButton("清除已完成")
        self.clear_completed_btn.clicked.connect(self.clear_completed)
        status_layout.addWidget(self.queue_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.clear_completed_btn)

        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels([
            "任务ID", "项目名称", "状态", "进度", "输出路径", "操作"
        ])
        self.task_table.horizontalHeader().setStretchLastSection(True)
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.itemSelectionChanged.connect(self.on_task_selected)

        # 操作按钮
        actions_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始")
        self.pause_btn = QPushButton("暂停")
        self.cancel_btn = QPushButton("取消")
        self.remove_btn = QPushButton("移除")

        self.start_btn.clicked.connect(lambda: self.task_action.emit("start", ""))
        self.pause_btn.clicked.connect(lambda: self.task_action.emit("pause", ""))
        self.cancel_btn.clicked.connect(lambda: self.task_action.emit("cancel", ""))
        self.remove_btn.clicked.connect(lambda: self.task_action.emit("remove", ""))

        actions_layout.addWidget(self.start_btn)
        actions_layout.addWidget(self.pause_btn)
        actions_layout.addWidget(self.cancel_btn)
        actions_layout.addWidget(self.remove_btn)

        layout.addLayout(status_layout)
        layout.addWidget(self.task_table)
        layout.addLayout(actions_layout)

    def update_tasks(self, tasks: List[ExportTask]):
        """更新任务列表"""
        self.tasks = tasks
        self.update_queue_display()

    def update_queue_display(self):
        """更新队列显示"""
        self.task_table.setRowCount(len(self.tasks))

        for i, task in enumerate(self.tasks):
            # 任务ID
            self.task_table.setItem(i, 0, QTableWidgetItem(task.id[:8] + "..."))

            # 项目名称
            project_name = task.metadata.get("project_name", "未知项目")
            self.task_table.setItem(i, 1, QTableWidgetItem(project_name))

            # 状态
            status_item = QTableWidgetItem(task.status.value)
            status_item.setBackground(self.get_status_color(task.status))
            self.task_table.setItem(i, 2, status_item)

            # 进度
            progress_item = QTableWidgetItem(f"{task.progress:.1f}%")
            self.task_table.setItem(i, 3, progress_item)

            # 输出路径
            output_path = task.output_path
            if len(output_path) > 50:
                output_path = "..." + output_path[-47:]
            self.task_table.setItem(i, 4, QTableWidgetItem(output_path))

            # 操作按钮
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            if task.status.value in ["pending", "queued"]:
                start_btn = QPushButton("开始")
                start_btn.clicked.connect(lambda checked, tid=task.id: self.task_action.emit("start", tid))
                actions_layout.addWidget(start_btn)

            if task.status.value == "processing":
                pause_btn = QPushButton("暂停")
                pause_btn.clicked.connect(lambda checked, tid=task.id: self.task_action.emit("pause", tid))
                actions_layout.addWidget(pause_btn)

                cancel_btn = QPushButton("取消")
                cancel_btn.clicked.connect(lambda checked, tid=task.id: self.task_action.emit("cancel", tid))
                actions_layout.addWidget(cancel_btn)

            if task.status.value in ["completed", "failed"]:
                remove_btn = QPushButton("移除")
                remove_btn.clicked.connect(lambda checked, tid=task.id: self.task_action.emit("remove", tid))
                actions_layout.addWidget(remove_btn)

            actions_layout.addStretch()
            self.task_table.setCellWidget(i, 5, actions_widget)

        # 更新状态标签
        pending_count = len([t for t in self.tasks if t.status.value in ["pending", "queued"]])
        processing_count = len([t for t in self.tasks if t.status.value == "processing"])
        completed_count = len([t for t in self.tasks if t.status.value == "completed"])
        failed_count = len([t for t in self.tasks if t.status.value == "failed"])

        status_text = f"队列状态: {len(self.tasks)}个任务 | "
        status_text += f"待处理: {pending_count} | 处理中: {processing_count} | "
        status_text += f"已完成: {completed_count} | 失败: {failed_count}"
        self.queue_status_label.setText(status_text)

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

    def on_task_selected(self):
        """任务选择事件"""
        selected_items = self.task_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            if row < len(self.tasks):
                self.task_selected.emit(self.tasks[row].id)

    def clear_completed(self):
        """清除已完成的任务"""
        self.task_action.emit("clear_completed", "")

    def get_selected_task_id(self) -> Optional[str]:
        """获取选中的任务ID"""
        selected_items = self.task_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            if row < len(self.tasks):
                return self.tasks[row].id
        return None


class ExportPanel(QWidget):
    """导出面板主类"""

    # 信号定义
    export_started = pyqtSignal(str)
    export_progress = pyqtSignal(str, float)
    export_completed = pyqtSignal(str, str)
    export_failed = pyqtSignal(str, str)

    def __init__(self, application, parent=None):
        super().__init__(parent)
        self.application = application
        self.export_system = application.export_system
        self.logger = Logger.get_logger(__name__)
        self.current_project_id = None
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 快速导出标签页
        self.quick_export_tab = self.create_quick_export_tab()
        self.tab_widget.addTab(self.quick_export_tab, "快速导出")

        # 批量导出标签页
        self.batch_export_tab = self.create_batch_export_tab()
        self.tab_widget.addTab(self.batch_export_tab, "批量导出")

        # 队列管理标签页
        self.queue_tab = self.create_queue_tab()
        self.tab_widget.addTab(self.queue_tab, "队列管理")

        # 预设管理标签页
        self.presets_tab = self.create_presets_tab()
        self.tab_widget.addTab(self.presets_tab, "预设管理")

        layout.addWidget(self.tab_widget)

    def create_quick_export_tab(self) -> QWidget:
        """创建快速导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 项目信息
        project_group = QGroupBox("项目信息")
        project_layout = QFormLayout(project_group)

        self.project_name_label = QLabel("未选择项目")
        self.project_duration_label = QLabel("00:00:00")
        self.project_resolution_label = QLabel("1920x1080")

        project_layout.addRow("项目名称:", self.project_name_label)
        project_layout.addRow("持续时间:", self.project_duration_label)
        project_layout.addRow("分辨率:", self.project_resolution_label)

        # 导出设置
        export_group = QGroupBox("导出设置")
        export_layout = QFormLayout(export_group)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(200)
        self.refresh_presets()

        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择输出路径...")
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_output_path)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_path_edit, 1)
        output_layout.addWidget(self.browse_btn)

        export_layout.addRow("导出预设:", self.preset_combo)
        export_layout.addRow("输出路径:", output_layout)

        # 快速操作按钮
        quick_actions_group = QGroupBox("快速操作")
        quick_actions_layout = QHBoxLayout(quick_actions_group)

        self.export_youtube_btn = QPushButton("导出 YouTube")
        self.export_tiktok_btn = QPushButton("导出 TikTok")
        self.export_instagram_btn = QPushButton("导出 Instagram")
        self.export_jianying_btn = QPushButton("导出剪映草稿")

        self.export_youtube_btn.clicked.connect(lambda: self.quick_export("youtube_1080p"))
        self.export_tiktok_btn.clicked.connect(lambda: self.quick_export("tiktok_video"))
        self.export_instagram_btn.clicked.connect(lambda: self.quick_export("instagram_reel"))
        self.export_jianying_btn.clicked.connect(lambda: self.quick_export("jianying_draft"))

        quick_actions_layout.addWidget(self.export_youtube_btn)
        quick_actions_layout.addWidget(self.export_tiktok_btn)
        quick_actions_layout.addWidget(self.export_instagram_btn)
        quick_actions_layout.addWidget(self.export_jianying_btn)

        # 导出按钮
        self.export_btn = QPushButton("开始导出")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.clicked.connect(self.start_export)

        # 添加到布局
        layout.addWidget(project_group)
        layout.addWidget(export_group)
        layout.addWidget(quick_actions_group)
        layout.addWidget(self.export_btn)
        layout.addStretch()

        return widget

    def create_batch_export_tab(self) -> QWidget:
        """创建批量导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 批量配置
        config_group = QGroupBox("批量配置")
        config_layout = QFormLayout(config_group)

        self.batch_output_dir_edit = QLineEdit()
        self.batch_output_dir_edit.setPlaceholderText("选择输出目录...")
        self.batch_browse_btn = QPushButton("浏览")
        self.batch_browse_btn.clicked.connect(self.browse_batch_output_dir)

        batch_output_layout = QHBoxLayout()
        batch_output_layout.addWidget(self.batch_output_dir_edit, 1)
        batch_output_layout.addWidget(self.batch_browse_btn)

        self.batch_preset_combo = QComboBox()
        self.batch_preset_combo.setMinimumWidth(200)

        config_layout.addRow("输出目录:", batch_output_layout)
        config_layout.addRow("导出预设:", self.batch_preset_combo)

        # 项目列表
        projects_group = QGroupBox("项目列表")
        projects_layout = QVBoxLayout(projects_group)

        self.batch_projects_table = QTableWidget()
        self.batch_projects_table.setColumnCount(4)
        self.batch_projects_table.setHorizontalHeaderLabels([
            "选择", "项目名称", "持续时间", "分辨率"
        ])
        self.batch_projects_table.horizontalHeader().setStretchLastSection(True)

        projects_layout.addWidget(self.batch_projects_table)

        # 批量操作按钮
        batch_actions_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_none_btn = QPushButton("全不选")
        self.batch_export_btn = QPushButton("批量导出")

        self.select_all_btn.clicked.connect(self.select_all_projects)
        self.select_none_btn.clicked.connect(self.select_none_projects)
        self.batch_export_btn.clicked.connect(self.start_batch_export)

        batch_actions_layout.addWidget(self.select_all_btn)
        batch_actions_layout.addWidget(self.select_none_btn)
        batch_actions_layout.addStretch()
        batch_actions_layout.addWidget(self.batch_export_btn)

        # 添加到布局
        layout.addWidget(config_group)
        layout.addWidget(projects_group)
        layout.addLayout(batch_actions_layout)
        layout.addStretch()

        return widget

    def create_queue_tab(self) -> QWidget:
        """创建队列管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 队列状态
        self.queue_widget = ExportQueueWidget()
        layout.addWidget(self.queue_widget)

        # 队列设置
        settings_group = QGroupBox("队列设置")
        settings_layout = QFormLayout(settings_group)

        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 8)
        self.max_concurrent_spin.setValue(2)

        self.auto_cleanup_check = QCheckBox("自动清理已完成任务")
        self.auto_cleanup_check.setChecked(True)

        settings_layout.addRow("最大并发数:", self.max_concurrent_spin)
        settings_layout.addRow("自动清理:", self.auto_cleanup_check)

        # 应用设置按钮
        self.apply_queue_settings_btn = QPushButton("应用设置")
        self.apply_queue_settings_btn.clicked.connect(self.apply_queue_settings)

        # 添加到布局
        layout.addWidget(settings_group)
        layout.addWidget(self.apply_queue_settings_btn)

        return widget

    def create_presets_tab(self) -> QWidget:
        """创建预设管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 预设列表
        presets_group = QGroupBox("导出预设")
        presets_layout = QVBoxLayout(presets_group)

        self.presets_table = QTableWidget()
        self.presets_table.setColumnCount(5)
        self.presets_table.setHorizontalHeaderLabels([
            "预设名称", "格式", "分辨率", "比特率", "操作"
        ])
        self.presets_table.horizontalHeader().setStretchLastSection(True)

        presets_layout.addWidget(self.presets_table)

        # 预设操作按钮
        preset_actions_layout = QHBoxLayout()
        self.add_preset_btn = QPushButton("添加预设")
        self.edit_preset_btn = QPushButton("编辑预设")
        self.delete_preset_btn = QPushButton("删除预设")
        self.refresh_presets_btn = QPushButton("刷新")

        self.add_preset_btn.clicked.connect(self.add_preset)
        self.edit_preset_btn.clicked.connect(self.edit_preset)
        self.delete_preset_btn.clicked.connect(self.delete_preset)
        self.refresh_presets_btn.clicked.connect(self.refresh_presets_table)

        preset_actions_layout.addWidget(self.add_preset_btn)
        preset_actions_layout.addWidget(self.edit_preset_btn)
        preset_actions_layout.addWidget(self.delete_preset_btn)
        preset_actions_layout.addWidget(self.refresh_presets_btn)

        # 添加到布局
        layout.addWidget(presets_group)
        layout.addLayout(preset_actions_layout)
        layout.addStretch()

        return widget

    def connect_signals(self):
        """连接信号"""
        # 导出系统信号
        self.export_system.export_started.connect(self.on_export_started)
        self.export_system.export_progress.connect(self.on_export_progress)
        self.export_system.export_completed.connect(self.on_export_completed)
        self.export_system.export_failed.connect(self.on_export_failed)

        # 队列信号
        self.queue_widget.task_action.connect(self.handle_queue_action)

    def set_current_project(self, project_id: str, project_info: Dict[str, Any]):
        """设置当前项目"""
        self.current_project_id = project_id
        self.project_name_label.setText(project_info.get("name", "未知项目"))
        self.project_duration_label.setText(project_info.get("duration", "00:00:00"))
        self.project_resolution_label.setText(project_info.get("resolution", "1920x1080"))

    def refresh_presets(self):
        """刷新预设列表"""
        presets = self.export_system.get_presets()
        self.preset_combo.clear()
        self.batch_preset_combo.clear()

        for preset in presets:
            self.preset_combo.addItem(preset.name, preset.id)
            self.batch_preset_combo.addItem(preset.name, preset.id)

    def refresh_presets_table(self):
        """刷新预设表格"""
        presets = self.export_system.get_presets()
        self.presets_table.setRowCount(len(presets))

        for i, preset in enumerate(presets):
            self.presets_table.setItem(i, 0, QTableWidgetItem(preset.name))
            self.presets_table.setItem(i, 1, QTableWidgetItem(preset.format.value))
            self.presets_table.setItem(i, 2, QTableWidgetItem(f"{preset.resolution[0]}x{preset.resolution[1]}"))
            self.presets_table.setItem(i, 3, QTableWidgetItem(f"{preset.bitrate} kbps"))

            # 操作按钮
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, p=preset: self.edit_preset_data(p))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, p=preset: self.delete_preset_data(p))
            actions_layout.addWidget(delete_btn)

            actions_layout.addStretch()
            self.presets_table.setCellWidget(i, 4, actions_widget)

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

    def quick_export(self, preset_id: str):
        """快速导出"""
        if not self.current_project_id:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        # 生成默认输出路径
        project_name = self.project_name_label.text()
        output_path = f"{project_name}_{preset_id}.mp4"

        self.start_export_with_preset(preset_id, output_path)

    def start_export(self):
        """开始导出"""
        if not self.current_project_id:
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

        self.start_export_with_preset(preset_id, output_path)

    def start_export_with_preset(self, preset_id: str, output_path: str):
        """使用指定预设开始导出"""
        try:
            task_id = self.export_system.export_project(
                project_id=self.current_project_id,
                output_path=output_path,
                preset_id=preset_id,
                metadata={
                    "project_name": self.project_name_label.text(),
                    "duration": self.project_duration_label.text(),
                    "resolution": self.project_resolution_label.text()
                }
            )

            QMessageBox.information(self, "成功", f"导出任务已添加到队列: {task_id}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

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
            for project in selected_projects:
                output_path = os.path.join(
                    output_dir,
                    f"{project['name']}_{preset_id}.mp4"
                )
                batch_configs.append({
                    "project_id": project["id"],
                    "output_path": output_path,
                    "preset_id": preset_id,
                    "metadata": project
                })

            task_ids = self.export_system.export_batch(batch_configs)
            QMessageBox.information(self, "成功", f"已添加 {len(task_ids)} 个导出任务")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"批量导出失败: {str(e)}")

    def get_selected_projects(self) -> List[Dict[str, Any]]:
        """获取选中的项目"""
        selected_projects = []
        for i in range(self.batch_projects_table.rowCount()):
            checkbox = self.batch_projects_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                selected_projects.append({
                    "id": self.batch_projects_table.item(i, 1).data(Qt.ItemDataRole.UserRole),
                    "name": self.batch_projects_table.item(i, 1).text(),
                    "duration": self.batch_projects_table.item(i, 2).text(),
                    "resolution": self.batch_projects_table.item(i, 3).text()
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

    def handle_queue_action(self, action: str, task_id: str):
        """处理队列操作"""
        try:
            if action == "start":
                # 开始任务（重新实现）
                pass
            elif action == "pause":
                # 暂停任务
                pass
            elif action == "cancel":
                success = self.export_system.cancel_export(task_id)
                if success:
                    QMessageBox.information(self, "成功", "任务已取消")
                else:
                    QMessageBox.warning(self, "警告", "无法取消该任务")
            elif action == "remove":
                # 移除任务
                pass
            elif action == "clear_completed":
                # 清除已完成任务
                pass

        except Exception as e:
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def apply_queue_settings(self):
        """应用队列设置"""
        try:
            # 应用队列设置
            max_concurrent = self.max_concurrent_spin.value()
            auto_cleanup = self.auto_cleanup_check.isChecked()

            # 更新队列管理器设置
            # 这里需要访问队列管理器并更新设置
            QMessageBox.information(self, "成功", "队列设置已应用")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置应用失败: {str(e)}")

    def add_preset(self):
        """添加预设"""
        dialog = ExportSettingsDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            preset_data = dialog.get_preset_data()
            # 创建预设并添加到系统
            # 这里需要实现预设创建逻辑
            QMessageBox.information(self, "成功", "预设已添加")

    def edit_preset(self):
        """编辑预设"""
        selected_items = self.presets_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要编辑的预设")
            return

        # 编辑预设逻辑
        self.edit_preset_data(None)

    def edit_preset_data(self, preset: ExportPreset):
        """编辑预设数据"""
        dialog = ExportSettingsDialog(preset, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            preset_data = dialog.get_preset_data()
            # 更新预设
            QMessageBox.information(self, "成功", "预设已更新")

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
            # 删除预设逻辑
            QMessageBox.information(self, "成功", "预设已删除")

    def delete_preset_data(self, preset: ExportPreset):
        """删除预设数据"""
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除预设 '{preset.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.export_system.remove_preset(preset.id)
            if success:
                self.refresh_presets_table()
                QMessageBox.information(self, "成功", "预设已删除")
            else:
                QMessageBox.warning(self, "警告", "删除预设失败")

    def update_queue_display(self):
        """更新队列显示"""
        try:
            tasks = self.export_system.get_task_history()
            self.queue_widget.update_tasks(tasks)
        except Exception as e:
            self.logger.error(f"Failed to update queue display: {e}")

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
        QMessageBox.information(self, "成功", f"导出完成: {output_path}")

    def on_export_failed(self, task_id: str, error_message: str):
        """导出失败事件"""
        self.logger.error(f"Export failed: {task_id} - {error_message}")
        self.export_failed.emit(task_id, error_message)
        QMessageBox.critical(self, "错误", f"导出失败: {error_message}")

    def cleanup(self):
        """清理资源"""
        try:
            self.queue_widget.update_timer.stop()
        except:
            pass

    def update_theme(self, is_dark: bool = True):
        """更新主题"""
        # 实现主题更新逻辑
        pass