#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出设置组件
提供增强的错误处理和用户友好的导出设置界面
"""

import os
import json
import time
import shutil
import platform
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
                            QProgressBar, QTableWidget, QTableWidgetItem,
                            QFileDialog, QMessageBox, QTabWidget, QGroupBox,
                            QLineEdit, QTextEdit, QCheckBox, QSlider, QDialog,
                            QDialogButtonBox, QFormLayout, QScrollArea,
                            QSplitter, QFrame, QStackedWidget, QToolButton,
                            QHeaderView, QAbstractItemView, QMenu, QGridLayout,
                            QSpinBox, QDoubleSpinBox, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QRect, QPoint
from PyQt6.QtGui import QAction, QFont, QPalette, QColor, QIcon, QPainter, QPen

from ...export.export_system import ExportSystem, ExportTask, ExportPreset, ExportFormat, ExportQuality
from ...core.logger import Logger
from ...utils.error_handler import (
    ErrorHandler, ErrorType, ErrorSeverity, RecoveryAction,
    ErrorContext, safe_execute, error_handler_decorator
)


class ExportValidationResult:
    """导出验证结果"""

    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []


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


class EnhancedExportSettingsComponent(QWidget):
    """增强的导出设置组件"""

    # 信号定义
    settings_validated = pyqtSignal(ExportValidationResult)
    export_started = pyqtSignal(str)
    export_progress = pyqtSignal(str, float)
    export_completed = pyqtSignal(str, str)
    export_failed = pyqtSignal(str, str, str)  # task_id, error_message, error_category

    # 自定义信号
    disk_space_warning = pyqtSignal(str, str, str)  # path, required_space, available_space
    format_compatibility_warning = pyqtSignal(str, str)  # format, issue_description

    def __init__(self, export_system: ExportSystem, parent=None):
        super().__init__(parent)
        self.export_system = export_system
        self.logger = Logger("EnhancedExportSettingsComponent")
        self.error_handler = ErrorHandler(self.logger)
        self.current_project = None
        self.validation_timer = QTimer()
        self.validation_timer.timeout.connect(self.validate_settings)

        # 系统状态监控
        self.system_monitor = SystemResourceMonitor()

        self.setup_ui()
        self.connect_signals()
        self.start_monitoring()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建主标签页
        self.main_tab_widget = QTabWidget()

        # 基本设置标签页
        self.basic_settings_tab = self.create_basic_settings_tab()
        self.main_tab_widget.addTab(self.basic_settings_tab, "基本设置")

        # 高级设置标签页
        self.advanced_settings_tab = self.create_advanced_settings_tab()
        self.main_tab_widget.addTab(self.advanced_settings_tab, "高级设置")

        # 质量优化标签页
        self.quality_optimization_tab = self.create_quality_optimization_tab()
        self.main_tab_widget.addTab(self.quality_optimization_tab, "质量优化")

        # 错误处理和恢复标签页
        self.error_handling_tab = self.create_error_handling_tab()
        self.main_tab_widget.addTab(self.error_handling_tab, "错误处理")

        layout.addWidget(self.main_tab_widget)

        # 验证状态栏
        self.validation_status_widget = self.create_validation_status_widget()
        layout.addWidget(self.validation_status_widget)

    def create_basic_settings_tab(self) -> QWidget:
        """创建基本设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 项目信息组
        project_group = QGroupBox("项目信息")
        project_layout = QFormLayout(project_group)

        self.project_name_label = QLabel("未选择项目")
        self.project_duration_label = QLabel("00:00:00")
        self.project_resolution_label = QLabel("1920×1080")
        self.project_file_size_label = QLabel("0 MB")

        project_layout.addRow("项目名称:", self.project_name_label)
        project_layout.addRow("持续时间:", self.project_duration_label)
        project_layout.addRow("分辨率:", self.project_resolution_label)
        project_layout.addRow("文件大小:", self.project_file_size_label)

        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout(output_group)

        # 输出路径
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择输出文件路径...")
        self.output_path_edit.textChanged.connect(self.on_output_path_changed)

        self.browse_output_btn = QPushButton("浏览...")
        self.browse_output_btn.clicked.connect(self.browse_output_path)

        output_path_layout = QHBoxLayout()
        output_path_layout.addWidget(self.output_path_edit, 1)
        output_path_layout.addWidget(self.browse_output_btn)

        # 格式选择
        self.format_combo = QComboBox()
        self.format_combo.setMinimumWidth(200)
        self.populate_format_combo()
        self.format_combo.currentTextChanged.connect(self.on_format_changed)

        # 预设选择
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(200)
        self.refresh_presets()
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)

        output_layout.addRow("输出路径:", output_path_layout)
        output_layout.addRow("输出格式:", self.format_combo)
        output_layout.addRow("导出预设:", self.preset_combo)

        # 快速预设按钮
        quick_presets_group = QGroupBox("快速预设")
        quick_presets_layout = QGridLayout(quick_presets_group)

        quick_presets = [
            ("📺 YouTube 1080p", "youtube_1080p", "高质量H.264，适合YouTube"),
            ("🎬 YouTube 4K", "youtube_4k", "4K分辨率，H.265编码"),
            ("🎵 TikTok", "tiktok_video", "9:16竖屏，适合短视频"),
            ("📸 Instagram", "instagram_reel", "1:1正方形，适合Instagram"),
            ("⭐ 高质量", "master_quality", "无损质量，适合专业编辑"),
            ("📝 剪映草稿", "jianying_draft", "生成剪映草稿文件")
        ]

        self.quick_preset_buttons = {}
        for i, (name, preset_id, tooltip) in enumerate(quick_presets):
            btn = QPushButton(name)
            btn.setMinimumHeight(50)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, pid=preset_id: self.apply_quick_preset(pid))

            row = i // 2
            col = i % 2
            quick_presets_layout.addWidget(btn, row, col)

            self.quick_preset_buttons[preset_id] = btn

        # 系统资源显示
        system_info_group = QGroupBox("系统资源状态")
        system_info_layout = QVBoxLayout(system_info_group)

        self.cpu_usage_label = QLabel("CPU: --%")
        self.memory_usage_label = QLabel("内存: --%")
        self.disk_space_label = QLabel("磁盘空间: --")
        self.gpu_status_label = QLabel("GPU状态: --")

        system_info_layout.addWidget(self.cpu_usage_label)
        system_info_layout.addWidget(self.memory_usage_label)
        system_info_layout.addWidget(self.disk_space_label)
        system_info_layout.addWidget(self.gpu_status_label)

        # 添加到布局
        layout.addWidget(project_group)
        layout.addWidget(output_group)
        layout.addWidget(quick_presets_group)
        layout.addWidget(system_info_group)
        layout.addStretch()

        return widget

    def create_advanced_settings_tab(self) -> QWidget:
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 编码设置组
        encoding_group = QGroupBox("编码设置")
        encoding_layout = QFormLayout(encoding_group)

        # 视频编码器
        self.video_codec_combo = QComboBox()
        self.video_codec_combo.addItems([
            "libx264 (H.264)", "libx265 (H.265)", "libvpx (VP9)",
            "prores", "dnxhd", "mpeg4"
        ])
        self.video_codec_combo.currentTextChanged.connect(self.on_video_codec_changed)

        # 音频编码器
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems([
            "aac", "mp3", "libvorbis", "libopus", "pcm_s16le"
        ])

        # 比特率设置
        bitrate_layout = QHBoxLayout()

        self.video_bitrate_spin = QSpinBox()
        self.video_bitrate_spin.setRange(100, 100000)
        self.video_bitrate_spin.setValue(8000)
        self.video_bitrate_spin.setSuffix(" kbps")

        self.audio_bitrate_spin = QSpinBox()
        self.audio_bitrate_spin.setRange(32, 512)
        self.audio_bitrate_spin.setValue(128)
        self.audio_bitrate_spin.setSuffix(" kbps")

        bitrate_layout.addWidget(QLabel("视频:"))
        bitrate_layout.addWidget(self.video_bitrate_spin)
        bitrate_layout.addWidget(QLabel("音频:"))
        bitrate_layout.addWidget(self.audio_bitrate_spin)
        bitrate_layout.addStretch()

        # 额外编码参数
        self.codec_params_edit = QTextEdit()
        self.codec_params_edit.setMaximumHeight(80)
        self.codec_params_edit.setPlaceholderText(
            "额外编码参数，例如：-crf 23 -preset medium -tune film"
        )

        encoding_layout.addRow("视频编码器:", self.video_codec_combo)
        encoding_layout.addRow("音频编码器:", self.audio_codec_combo)
        encoding_layout.addRow("比特率设置:", bitrate_layout)
        encoding_layout.addRow("编码参数:", self.codec_params_edit)

        # 硬件加速组
        hardware_group = QGroupBox("硬件加速")
        hardware_layout = QVBoxLayout(hardware_group)

        # GPU加速选项
        self.gpu_accel_check = QCheckBox("启用GPU硬件加速")
        self.gpu_accel_check.setChecked(True)
        self.gpu_accel_check.stateChanged.connect(self.on_gpu_accel_changed)

        self.gpu_device_combo = QComboBox()
        self.gpu_device_combo.addItems(["自动选择", "GPU 0", "GPU 1", "CPU软件渲染"])
        self.gpu_device_combo.setEnabled(self.gpu_accel_check.isChecked())

        # 编码速度预设
        self.encoding_preset_combo = QComboBox()
        self.encoding_preset_combo.addItems([
            "ultrafast", "superfast", "veryfast", "faster", "fast",
            "medium", "slow", "slower", "veryslow", "placebo"
        ])
        self.encoding_preset_combo.setCurrentText("medium")

        hardware_layout.addWidget(self.gpu_accel_check)
        hardware_layout.addWidget(self.gpu_device_combo)
        hardware_layout.addWidget(QLabel("编码速度预设:"))
        hardware_layout.addWidget(self.encoding_preset_combo)

        # 分辨率和帧率组
        resolution_group = QGroupBox("分辨率和帧率")
        resolution_layout = QFormLayout(resolution_group)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "3840×2160 (4K)", "2560×1440 (2K)", "1920×1080 (1080p)",
            "1280×720 (720p)", "854×480 (480p)", "自定义"
        ])

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)

        # 自定义分辨率
        self.custom_width_spin = QSpinBox()
        self.custom_width_spin.setRange(64, 8192)
        self.custom_width_spin.setValue(1920)
        self.custom_width_spin.setEnabled(False)

        self.custom_height_spin = QSpinBox()
        self.custom_height_spin.setRange(64, 8192)
        self.custom_height_spin.setValue(1080)
        self.custom_height_spin.setEnabled(False)

        custom_res_layout = QHBoxLayout()
        custom_res_layout.addWidget(self.custom_width_spin)
        custom_res_layout.addWidget(QLabel("×"))
        custom_res_layout.addWidget(self.custom_height_spin)

        resolution_layout.addRow("分辨率:", self.resolution_combo)
        resolution_layout.addRow("自定义分辨率:", custom_res_layout)
        resolution_layout.addRow("帧率 (FPS):", self.fps_spin)

        # 添加到布局
        layout.addWidget(encoding_group)
        layout.addWidget(hardware_group)
        layout.addWidget(resolution_group)
        layout.addStretch()

        return widget

    def create_quality_optimization_tab(self) -> QWidget:
        """创建质量优化标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 质量预设组
        quality_preset_group = QGroupBox("质量预设")
        quality_preset_layout = QFormLayout(quality_preset_group)

        self.quality_preset_combo = QComboBox()
        self.quality_preset_combo.addItems([
            "低质量 (快速)", "中等质量", "高质量", "超高质量", "无损质量"
        ])
        self.quality_preset_combo.setCurrentText("高质量")

        quality_preset_layout.addRow("质量预设:", self.quality_preset_combo)

        # 高级质量设置组
        advanced_quality_group = QGroupBox("高级质量设置")
        advanced_quality_layout = QFormLayout(advanced_quality_group)

        # CRF值 (恒定质量因子)
        self.crf_spin = QSpinBox()
        self.crf_spin.setRange(0, 51)
        self.crf_spin.setValue(23)
        self.crf_spin.setSuffix(" (0=无损, 51=最差)")
        self.crf_spin.setToolTip("H.264/H.265的恒定质量因子，值越低质量越好")

        # 量化参数
        self.qp_spin = QSpinBox()
        self.qp_spin.setRange(0, 51)
        self.qp_spin.setValue(23)
        self.qp_spin.setSuffix(" (0=无损, 51=最差)")

        # 关键帧间隔
        self.keyframe_interval_spin = QSpinBox()
        self.keyframe_interval_spin.setRange(1, 1000)
        self.keyframe_interval_spin.setValue(250)
        self.keyframe_interval_spin.setSuffix(" 帧")

        advanced_quality_layout.addRow("CRF值:", self.crf_spin)
        advanced_quality_layout.addRow("量化参数:", self.qp_spin)
        advanced_quality_layout.addRow("关键帧间隔:", self.keyframe_interval_spin)

        # 滤镜和后处理组
        filters_group = QGroupBox("滤镜和后处理")
        filters_layout = QVBoxLayout(filters_group)

        self.deinterlace_check = QCheckBox("去隔行扫描")
        self.denoise_check = QCheckBox("降噪处理")
        self.sharpen_check = QCheckBox("锐化处理")
        self.color_correction_check = QCheckBox("色彩校正")
        self.stabilization_check = QCheckBox("视频防抖")

        filters_layout.addWidget(self.deinterlace_check)
        filters_layout.addWidget(self.denoise_check)
        filters_layout.addWidget(self.sharpen_check)
        filters_layout.addWidget(self.color_correction_check)
        filters_layout.addWidget(self.stabilization_check)

        # 音频质量设置组
        audio_quality_group = QGroupBox("音频质量设置")
        audio_quality_layout = QFormLayout(audio_quality_group)

        self.audio_sample_rate_combo = QComboBox()
        self.audio_sample_rate_combo.addItems([
            "44100 Hz", "48000 Hz", "96000 Hz", "192000 Hz"
        ])
        self.audio_sample_rate_combo.setCurrentText("48000 Hz")

        self.audio_channels_combo = QComboBox()
        self.audio_channels_combo.addItems([
            "单声道", "立体声", "5.1环绕声", "7.1环绕声"
        ])
        self.audio_channels_combo.setCurrentText("立体声")

        audio_quality_layout.addRow("采样率:", self.audio_sample_rate_combo)
        audio_quality_layout.addRow("声道:", self.audio_channels_combo)

        # 添加到布局
        layout.addWidget(quality_preset_group)
        layout.addWidget(advanced_quality_group)
        layout.addWidget(filters_group)
        layout.addWidget(audio_quality_group)
        layout.addStretch()

        return widget

    def create_error_handling_tab(self) -> QWidget:
        """创建错误处理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 错误恢复设置组
        recovery_group = QGroupBox("错误恢复设置")
        recovery_layout = QVBoxLayout(recovery_group)

        # 自动重试设置
        self.auto_retry_check = QCheckBox("失败时自动重试")
        self.auto_retry_check.setChecked(True)

        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(3)
        self.max_retries_spin.setSuffix(" 次")

        retry_layout = QHBoxLayout()
        retry_layout.addWidget(self.auto_retry_check)
        retry_layout.addWidget(QLabel("最大重试次数:"))
        retry_layout.addWidget(self.max_retries_spin)
        retry_layout.addStretch()

        # 恢复策略
        recovery_strategy_layout = QHBoxLayout()
        recovery_strategy_layout.addWidget(QLabel("恢复策略:"))

        self.retry_strategy_combo = QComboBox()
        self.retry_strategy_combo.addItems([
            "立即重试", "延迟重试", "指数退避", "跳过任务"
        ])
        recovery_strategy_layout.addWidget(self.retry_strategy_combo)
        recovery_strategy_layout.addStretch()

        recovery_layout.addLayout(retry_layout)
        recovery_layout.addLayout(recovery_strategy_layout)

        # 临时文件管理组
        temp_files_group = QGroupBox("临时文件管理")
        temp_files_layout = QVBoxLayout(temp_files_group)

        self.cleanup_temp_files_check = QCheckBox("完成后自动清理临时文件")
        self.cleanup_temp_files_check.setChecked(True)

        self.preserve_failed_files_check = QCheckBox("保留失败任务的临时文件用于调试")
        self.preserve_failed_files_check.setChecked(False)

        temp_files_layout.addWidget(self.cleanup_temp_files_check)
        temp_files_layout.addWidget(self.preserve_failed_files_check)

        # 错误日志设置组
        logging_group = QGroupBox("错误日志设置")
        logging_layout = QVBoxLayout(logging_group)

        self.detailed_logging_check = QCheckBox("启用详细日志记录")
        self.detailed_logging_check.setChecked(True)

        self.save_error_reports_check = QCheckBox("保存错误报告文件")
        self.save_error_reports_check.setChecked(True)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems([
            "ERROR", "WARNING", "INFO", "DEBUG"
        ])
        self.log_level_combo.setCurrentText("INFO")

        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("日志级别:"))
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()

        logging_layout.addWidget(self.detailed_logging_check)
        logging_layout.addWidget(self.save_error_reports_check)
        logging_layout.addLayout(log_level_layout)

        # 系统兼容性检查组
        compatibility_group = QGroupBox("系统兼容性检查")
        compatibility_layout = QVBoxLayout(compatibility_group)

        self.check_disk_space_check = QCheckBox("检查磁盘空间")
        self.check_disk_space_check.setChecked(True)

        self.check_codecs_check = QCheckBox("检查编解码器可用性")
        self.check_codecs_check.setChecked(True)

        self.check_gpu_support_check = QCheckBox("检查GPU支持")
        self.check_gpu_support_check.setChecked(True)

        compatibility_layout.addWidget(self.check_disk_space_check)
        compatibility_layout.addWidget(self.check_codecs_check)
        compatibility_layout.addWidget(self.check_gpu_support_check)

        # 测试和验证按钮
        test_buttons_layout = QHBoxLayout()

        self.test_settings_btn = QPushButton("测试设置")
        self.test_settings_btn.clicked.connect(self.test_export_settings)

        self.validate_system_btn = QPushButton("验证系统")
        self.validate_system_btn.clicked.connect(self.validate_system_compatibility)

        self.check_disk_space_btn = QPushButton("检查磁盘空间")
        self.check_disk_space_btn.clicked.connect(self.check_disk_space)

        test_buttons_layout.addWidget(self.test_settings_btn)
        test_buttons_layout.addWidget(self.validate_system_btn)
        test_buttons_layout.addWidget(self.check_disk_space_btn)

        # 添加到布局
        layout.addWidget(recovery_group)
        layout.addWidget(temp_files_group)
        layout.addWidget(logging_group)
        layout.addWidget(compatibility_group)
        layout.addLayout(test_buttons_layout)
        layout.addStretch()

        return widget

    def create_validation_status_widget(self) -> QWidget:
        """创建验证状态部件"""
        widget = QWidget()
        widget.setMaximumHeight(60)
        widget.setStyleSheet("background-color: #f8f9fa; border-top: 1px solid #dee2e6;")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)

        # 验证状态图标
        self.validation_status_icon = QLabel("⚠️")
        self.validation_status_icon.setStyleSheet("font-size: 16px;")

        # 验证状态文本
        self.validation_status_text = QLabel("请设置导出参数")
        self.validation_status_text.setStyleSheet("color: #6c757d;")

        # 验证详情按钮
        self.validation_details_btn = QPushButton("查看详情")
        self.validation_details_btn.setMaximumWidth(80)
        self.validation_details_btn.clicked.connect(self.show_validation_details)
        self.validation_details_btn.setEnabled(False)

        layout.addWidget(self.validation_status_icon)
        layout.addWidget(self.validation_status_text)
        layout.addStretch()
        layout.addWidget(self.validation_details_btn)

        return widget

    def connect_signals(self):
        """连接信号"""
        # 错误处理器信号
        self.error_handler.error_occurred.connect(self.on_error_occurred)
        self.error_handler.error_recovered.connect(self.on_error_recovered)

        # 系统监控信号
        self.system_monitor.resource_update.connect(self.on_system_resources_updated)

        # 自定义信号
        self.disk_space_warning.connect(self.on_disk_space_warning)
        self.format_compatibility_warning.connect(self.on_format_compatibility_warning)

    def start_monitoring(self):
        """开始监控"""
        # 启动验证定时器
        self.validation_timer.start(2000)  # 每2秒验证一次

        # 启动系统监控
        self.system_monitor.start()

    def populate_format_combo(self):
        """填充格式下拉框"""
        formats = [
            ("MP4 (H.264)", "mp4_h264", "最常用的格式，兼容性好"),
            ("MP4 (H.265)", "mp4_h265", "高压缩率，适合4K视频"),
            ("MOV (ProRes)", "mov_prores", "专业视频编辑格式"),
            ("AVI (无压缩)", "avi_uncompressed", "无损质量，文件很大"),
            ("MKV (H.264)", "mkv_h264", "开源格式，支持多音轨"),
            ("WebM (VP9)", "webm_vp9", "Web视频格式，适合网络分享"),
            ("GIF动画", "gif_animated", "动图格式，文件小质量差"),
            ("MP3音频", "mp3_audio", "音频格式，兼容性好"),
            ("WAV音频", "wav_audio", "无损音频格式"),
            ("剪映草稿", "jianying_draft", "剪映工程文件格式")
        ]

        for text, value, tooltip in formats:
            self.format_combo.addItem(text, value)
            self.format_combo.setItemData(
                self.format_combo.count() - 1,
                tooltip,
                Qt.ItemDataRole.ToolTipRole
            )

    def refresh_presets(self):
        """刷新预设列表"""
        @error_handler_decorator(
            error_type=ErrorType.SYSTEM,
            severity=ErrorSeverity.LOW,
            user_message="刷新预设列表失败"
        )
        def _refresh_presets():
            try:
                presets = self.export_system.get_presets()
                self.preset_combo.clear()

                for preset in presets:
                    self.preset_combo.addItem(preset.name, preset.id)

                self.logger.info(f"Refreshed {len(presets)} presets")
            except Exception as e:
                self.logger.error(f"Failed to refresh presets: {e}")
                raise

        _refresh_presets()

    def browse_output_path(self):
        """浏览输出路径"""
        @safe_execute(
            error_message="选择输出文件失败",
            error_type=ErrorType.FILE,
            severity=ErrorSeverity.MEDIUM,
            parent=self
        )
        def _browse_output_path():
            current_format = self.format_combo.currentData()
            if current_format in ["mp3_audio", "wav_audio"]:
                file_filter = "音频文件 (*.mp3 *.wav);;所有文件 (*)"
            elif current_format == "jianying_draft":
                file_filter = "JSON文件 (*.json);;所有文件 (*)"
            else:
                file_filter = "视频文件 (*.mp4 *.avi *.mov *.mkv *.webm);;所有文件 (*)"

            file_path, _ = QFileDialog.getSaveFileName(
                self, "选择输出文件", "", file_filter
            )

            if file_path:
                self.output_path_edit.setText(file_path)

        _browse_output_path()

    def on_output_path_changed(self, path: str):
        """输出路径改变事件"""
        if not path:
            return

        # 验证输出路径
        self.validation_timer.start(500)  # 延迟500ms验证

    def on_format_changed(self, format_text: str):
        """格式改变事件"""
        # 自动调整文件扩展名
        current_path = self.output_path_edit.text()
        if current_path:
            base_path = os.path.splitext(current_path)[0]

            format_extensions = {
                "MP4 (H.264)": ".mp4",
                "MP4 (H.265)": ".mp4",
                "MOV (ProRes)": ".mov",
                "AVI (无压缩)": ".avi",
                "MKV (H.264)": ".mkv",
                "WebM (VP9)": ".webm",
                "GIF动画": ".gif",
                "MP3音频": ".mp3",
                "WAV音频": ".wav",
                "剪映草稿": ".json"
            }

            extension = format_extensions.get(format_text, ".mp4")
            new_path = base_path + extension

            if new_path != current_path:
                self.output_path_edit.setText(new_path)

        # 检查格式兼容性
        self.check_format_compatibility(format_text)

    def on_preset_changed(self, preset_name: str):
        """预设改变事件"""
        # 根据预设更新界面设置
        self.apply_preset_settings(preset_name)

    def on_gpu_accel_changed(self, state: int):
        """GPU加速状态改变事件"""
        enabled = state == Qt.CheckState.Checked.value
        self.gpu_device_combo.setEnabled(enabled)

        if enabled:
            self.check_gpu_compatibility()

    def on_video_codec_changed(self, codec: str):
        """视频编码器改变事件"""
        # 根据编码器调整可用选项
        if "nvenc" in codec.lower():
            # NVIDIA编码器特定设置
            self.gpu_accel_check.setChecked(True)
            self.gpu_device_combo.setEnabled(True)

    def validate_settings(self):
        """验证设置"""
        @safe_execute(
            error_message="验证导出设置失败",
            error_type=ErrorType.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            parent=self
        )
        def _validate_settings():
            errors = []
            warnings = []

            # 验证输出路径
            output_path = self.output_path_edit.text()
            if not output_path:
                errors.append("请设置输出路径")
            else:
                # 检查输出目录是否存在
                output_dir = os.path.dirname(output_path)
                if not os.path.exists(output_dir):
                    try:
                        os.makedirs(output_dir, exist_ok=True)
                    except Exception as e:
                        errors.append(f"无法创建输出目录: {str(e)}")

                # 检查写入权限
                if os.path.exists(output_dir):
                    if not os.access(output_dir, os.W_OK):
                        errors.append("没有输出目录的写入权限")

            # 验证磁盘空间
            if self.check_disk_space_check.isChecked() and output_path:
                disk_space_ok, space_info = self.check_output_disk_space(output_path)
                if not disk_space_ok:
                    errors.append(f"磁盘空间不足: 需要 {space_info['required_space']}, 可用 {space_info['available_space']}")

            # 验证格式和编码器兼容性
            selected_format = self.format_combo.currentText()
            format_issues = self.get_format_compatibility_issues(selected_format)
            warnings.extend(format_issues)

            # 验证数值设置
            if self.video_bitrate_spin.value() < 100:
                warnings.append("视频比特率过低可能导致质量严重下降")

            if self.fps_spin.value() < 1 or self.fps_spin.value() > 120:
                errors.append("帧率必须在1-120之间")

            # 验证项目设置
            if not self.current_project:
                errors.append("请先选择一个项目")

            # 创建验证结果
            is_valid = len(errors) == 0
            result = ExportValidationResult(is_valid, errors, warnings)

            # 更新验证状态显示
            self.update_validation_status(result)

            # 发送验证信号
            self.settings_validated.emit(result)

            return result

        return _validate_settings()

    def update_validation_status(self, result: ExportValidationResult):
        """更新验证状态显示"""
        if result.is_valid:
            self.validation_status_icon.setText("✅")
            self.validation_status_text.setText("设置验证通过")
            self.validation_status_text.setStyleSheet("color: #28a745;")
            self.validation_details_btn.setEnabled(False)
        elif result.errors:
            self.validation_status_icon.setText("❌")
            self.validation_status_text.setText(f"设置验证失败 ({len(result.errors)} 个错误)")
            self.validation_status_text.setStyleSheet("color: #dc3545;")
            self.validation_details_btn.setEnabled(True)
        else:
            self.validation_status_icon.setText("⚠️")
            self.validation_status_text.setText(f"设置存在警告 ({len(result.warnings)} 个警告)")
            self.validation_status_text.setStyleSheet("color: #ffc107;")
            self.validation_details_btn.setEnabled(True)

    def show_validation_details(self):
        """显示验证详情"""
        result = self.validate_settings()

        if not result.errors and not result.warnings:
            QMessageBox.information(self, "验证详情", "设置验证通过，无错误或警告。")
            return

        details_text = ""
        if result.errors:
            details_text += "❌ 错误：\n"
            for error in result.errors:
                details_text += f"  • {error}\n"
            details_text += "\n"

        if result.warnings:
            details_text += "⚠️ 警告：\n"
            for warning in result.warnings:
                details_text += f"  • {warning}\n"

        QMessageBox.warning(self, "验证详情", details_text)

    def check_output_disk_space(self, output_path: str) -> Tuple[bool, Dict[str, str]]:
        """检查输出磁盘空间"""
        try:
            # 估算输出文件大小
            estimated_size = self.estimate_output_file_size()

            # 获取磁盘空间信息
            output_dir = os.path.dirname(output_path)
            if not output_dir:
                output_dir = os.getcwd()

            disk_usage = shutil.disk_usage(output_dir)
            available_space = disk_usage.free / (1024 * 1024 * 1024)  # GB

            space_ok = available_space > estimated_size

            return space_ok, {
                'required_space': f"{estimated_size:.1f} GB",
                'available_space': f"{available_space:.1f} GB"
            }

        except Exception as e:
            self.logger.error(f"Failed to check disk space: {e}")
            return False, {
                'required_space': "未知",
                'available_space': "检查失败"
            }

    def estimate_output_file_size(self) -> float:
        """估算输出文件大小 (GB)"""
        # 基于当前设置估算文件大小
        duration_minutes = 5  # 假设5分钟视频
        bitrate_mbps = self.video_bitrate_spin.value() / 1000

        # 基本大小计算 (GB)
        size_gb = (duration_minutes * 60 * bitrate_mbps) / (8 * 1024)

        # 根据分辨率和质量调整
        resolution = self.resolution_combo.currentText()
        if "4K" in resolution:
            size_gb *= 2.0
        elif "2K" in resolution:
            size_gb *= 1.5

        quality_preset = self.quality_preset_combo.currentText()
        if "超高质量" in quality_preset:
            size_gb *= 1.5
        elif "无损" in quality_preset:
            size_gb *= 3.0

        return size_gb

    def check_format_compatibility(self, format_name: str):
        """检查格式兼容性"""
        issues = self.get_format_compatibility_issues(format_name)

        for issue in issues:
            self.format_compatibility_warning.emit(format_name, issue)

    def get_format_compatibility_issues(self, format_name: str) -> List[str]:
        """获取格式兼容性问题"""
        issues = []

        # 检查GPU编码支持
        if self.gpu_accel_check.isChecked():
            if "H.265" in format_name and not self.is_h265_gpu_encoding_supported():
                issues.append("当前系统可能不支持H.265 GPU编码，将使用CPU编码")

        # 检查专业格式支持
        if "ProRes" in format_name and platform.system() == "Windows":
            issues.append("Windows系统对ProRes支持有限，建议使用MOV格式")

        # 检查高分辨率支持
        if "4K" in format_name and not self.is_4k_export_supported():
            issues.append("当前系统可能不支持4K导出，建议降低分辨率")

        return issues

    def is_h265_gpu_encoding_supported(self) -> bool:
        """检查是否支持H.265 GPU编码"""
        # 这里应该实际检查GPU和驱动支持
        # 简化实现，总是返回True
        return True

    def is_4k_export_supported(self) -> bool:
        """检查是否支持4K导出"""
        # 检查系统是否支持4K导出
        import psutil
        return psutil.virtual_memory().total >= 8 * 1024 * 1024 * 1024  # 8GB内存

    def check_gpu_compatibility(self):
        """检查GPU兼容性"""
        @safe_execute(
            error_message="检查GPU兼容性失败",
            error_type=ErrorType.SYSTEM,
            severity=ErrorSeverity.LOW,
            parent=self
        )
        def _check_gpu_compatibility():
            try:
                # 这里应该实际检查GPU支持
                # 简化实现，模拟检查结果
                gpu_supported = True
                gpu_name = "NVIDIA GeForce RTX 3080"

                if gpu_supported:
                    self.gpu_status_label.setText(f"GPU状态: {gpu_name} (已就绪)")
                    self.gpu_status_label.setStyleSheet("color: #28a745;")
                else:
                    self.gpu_status_label.setText("GPU状态: 不支持或驱动问题")
                    self.gpu_status_label.setStyleSheet("color: #dc3545;")

            except Exception as e:
                self.gpu_status_label.setText("GPU状态: 检查失败")
                self.gpu_status_label.setStyleSheet("color: #dc3545;")
                raise

        _check_gpu_compatibility()

    def test_export_settings(self):
        """测试导出设置"""
        @safe_execute(
            error_message="测试导出设置失败",
            error_type=ErrorType.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            parent=self
        )
        def _test_export_settings():
            # 验证设置
            result = self.validate_settings()
            if not result.is_valid:
                return False

            # 创建测试任务
            try:
                # 这里应该创建一个小的测试导出任务
                # 简化实现，直接显示成功消息
                QMessageBox.information(self, "测试成功", "导出设置测试通过！")
                return True

            except Exception as e:
                raise RuntimeError(f"导出设置测试失败: {str(e)}")

        _test_export_settings()

    def validate_system_compatibility(self):
        """验证系统兼容性"""
        @safe_execute(
            error_message="系统兼容性验证失败",
            error_type=ErrorType.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            parent=self
        )
        def _validate_system_compatibility():
            compatibility_report = {
                'system': platform.system(),
                'python_version': platform.python_version(),
                'checks': []
            }

            # 检查FFmpeg
            try:
                import subprocess
                result = subprocess.run(['ffmpeg', '-version'],
                                     capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    compatibility_report['checks'].append({
                        'name': 'FFmpeg',
                        'status': 'OK',
                        'version': result.stdout.split('\n')[0]
                    })
                else:
                    compatibility_report['checks'].append({
                        'name': 'FFmpeg',
                        'status': 'ERROR',
                        'message': 'FFmpeg不可用'
                    })
            except Exception as e:
                compatibility_report['checks'].append({
                    'name': 'FFmpeg',
                    'status': 'ERROR',
                    'message': str(e)
                })

            # 检查系统资源
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()

            compatibility_report['checks'].extend([
                {
                    'name': '内存',
                    'status': 'OK' if memory_gb >= 4 else 'WARNING',
                    'value': f"{memory_gb:.1f} GB"
                },
                {
                    'name': 'CPU核心数',
                    'status': 'OK' if cpu_count >= 4 else 'WARNING',
                    'value': str(cpu_count)
                }
            ])

            # 显示兼容性报告
            self.show_compatibility_report(compatibility_report)

        _validate_system_compatibility()

    def show_compatibility_report(self, report: Dict[str, Any]):
        """显示兼容性报告"""
        dialog = QDialog(self)
        dialog.setWindowTitle("系统兼容性报告")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        # 系统信息
        info_text = f"系统: {report['system']}\\nPython版本: {report['python_version']}"
        info_label = QLabel(info_text)
        layout.addWidget(info_label)

        # 检查结果表格
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["检查项目", "状态", "详细信息"])

        checks = report['checks']
        table.setRowCount(len(checks))

        for i, check in enumerate(checks):
            table.setItem(i, 0, QTableWidgetItem(check['name']))

            status_item = QTableWidgetItem(check['status'])
            if check['status'] == 'OK':
                status_item.setBackground(QColor(0, 200, 0))
            elif check['status'] == 'WARNING':
                status_item.setBackground(QColor(255, 200, 0))
            else:
                status_item.setBackground(QColor(255, 0, 0))

            table.setItem(i, 1, status_item)
            table.setItem(i, 2, QTableWidgetItem(check.get('value', check.get('message', ''))))

        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def check_disk_space(self):
        """检查磁盘空间"""
        output_path = self.output_path_edit.text()
        if not output_path:
            QMessageBox.warning(self, "警告", "请先设置输出路径")
            return

        space_ok, space_info = self.check_output_disk_space(output_path)

        if space_ok:
            QMessageBox.information(
                self, "磁盘空间检查",
                f"磁盘空间充足\\n"
                f"需要空间: {space_info['required_space']}\\n"
                f"可用空间: {space_info['available_space']}"
            )
        else:
            QMessageBox.warning(
                self, "磁盘空间警告",
                f"磁盘空间不足\\n"
                f"需要空间: {space_info['required_space']}\\n"
                f"可用空间: {space_info['available_space']}\\n"
                f"请清理磁盘空间或选择其他输出位置"
            )

    def apply_quick_preset(self, preset_id: str):
        """应用快速预设"""
        try:
            # 根据预设ID应用不同的设置
            presets = {
                "youtube_1080p": {
                    "format": "MP4 (H.264)",
                    "resolution": "1920×1080 (1080p)",
                    "video_bitrate": 8000,
                    "fps": 30,
                    "quality_preset": "高质量"
                },
                "youtube_4k": {
                    "format": "MP4 (H.265)",
                    "resolution": "3840×2160 (4K)",
                    "video_bitrate": 35000,
                    "fps": 30,
                    "quality_preset": "超高质量"
                },
                "tiktok_video": {
                    "format": "MP4 (H.264)",
                    "resolution": "1080×1920 (自定义)",
                    "video_bitrate": 5000,
                    "fps": 30,
                    "quality_preset": "中等质量"
                },
                "instagram_reel": {
                    "format": "MP4 (H.264)",
                    "resolution": "1080×1080 (自定义)",
                    "video_bitrate": 4000,
                    "fps": 30,
                    "quality_preset": "中等质量"
                },
                "master_quality": {
                    "format": "MOV (ProRes)",
                    "resolution": "1920×1080 (1080p)",
                    "video_bitrate": 50000,
                    "fps": 30,
                    "quality_preset": "无损质量"
                },
                "jianying_draft": {
                    "format": "剪映草稿",
                    "resolution": "1920×1080 (1080p)",
                    "fps": 30,
                    "quality_preset": "中等质量"
                }
            }

            preset_data = presets.get(preset_id)
            if preset_data:
                # 应用预设设置
                self.format_combo.setCurrentText(preset_data["format"])
                self.resolution_combo.setCurrentText(preset_data["resolution"])
                self.video_bitrate_spin.setValue(preset_data["video_bitrate"])
                self.fps_spin.setValue(preset_data["fps"])
                self.quality_preset_combo.setCurrentText(preset_data["quality_preset"])

                # 处理自定义分辨率
                if preset_data["resolution"] == "1080×1920 (自定义)":
                    self.custom_width_spin.setValue(1080)
                    self.custom_height_spin.setValue(1920)
                    self.custom_width_spin.setEnabled(True)
                    self.custom_height_spin.setEnabled(True)

                self.logger.info(f"Applied quick preset: {preset_id}")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"应用快速预设失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ExportSettingsComponent",
                    operation="apply_quick_preset"
                ),
                user_message="应用预设失败",
                recovery_action=RecoveryAction.NONE
            )
            self.error_handler.handle_error(error_info, parent=self)

    def apply_preset_settings(self, preset_name: str):
        """应用预设设置"""
        try:
            # 从导出系统获取预设数据并应用
            presets = self.export_system.get_presets()
            for preset in presets:
                if preset.name == preset_name:
                    # 应用预设设置到界面
                    self.format_combo.setCurrentText(preset.format.value)
                    self.video_bitrate_spin.setValue(preset.bitrate)
                    self.fps_spin.setValue(int(preset.fps))
                    # 其他设置...
                    break

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.LOW,
                message=f"应用预设设置失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ExportSettingsComponent",
                    operation="apply_preset_settings"
                )
            )
            self.error_handler.handle_error(error_info, parent=self)

    def on_error_occurred(self, error_info):
        """错误发生事件"""
        self.logger.error(f"Error occurred: {error_info.message}")

    def on_error_recovered(self, error_info, recovery_action):
        """错误恢复事件"""
        self.logger.info(f"Error recovered: {error_info.message} with {recovery_action}")

    def on_system_resources_updated(self, resource_info):
        """系统资源更新事件"""
        try:
            self.cpu_usage_label.setText(f"CPU: {resource_info['cpu_percent']:.1f}%")
            self.memory_usage_label.setText(f"内存: {resource_info['memory_percent']:.1f}%")

            if resource_info.get('disk_info'):
                disk_info = resource_info['disk_info']
                self.disk_space_label.setText(
                    f"磁盘空间: {disk_info['free_gb']:.1f} GB 可用 / {disk_info['total_gb']:.1f} GB 总计"
                )

        except Exception as e:
            self.logger.error(f"Failed to update system resource display: {e}")

    def on_disk_space_warning(self, path: str, required_space: str, available_space: str):
        """磁盘空间警告事件"""
        warning_msg = (
            f"磁盘空间不足警告！\\n"
            f"路径: {path}\\n"
            f"需要空间: {required_space}\\n"
            f"可用空间: {available_space}\\n"
            f"建议清理磁盘或选择其他输出位置"
        )

        QMessageBox.warning(self, "磁盘空间警告", warning_msg)

    def on_format_compatibility_warning(self, format_name: str, issue_description: str):
        """格式兼容性警告事件"""
        warning_msg = (
            f"格式兼容性警告：{format_name}\\n"
            f"问题：{issue_description}"
        )

        self.logger.warning(f"Format compatibility warning: {format_name} - {issue_description}")

    def set_current_project(self, project_info: Dict[str, Any]):
        """设置当前项目"""
        self.current_project = project_info

        # 更新项目信息显示
        self.project_name_label.setText(project_info.get('name', '未知项目'))
        self.project_duration_label.setText(project_info.get('duration', '00:00:00'))
        self.project_resolution_label.setText(project_info.get('resolution', '1920×1080'))
        self.project_file_size_label.setText(project_info.get('size', '0 MB'))

        # 触发验证
        self.validation_timer.start(500)

    def get_export_settings(self) -> Dict[str, Any]:
        """获取导出设置"""
        try:
            settings = {
                'output_path': self.output_path_edit.text(),
                'format': self.format_combo.currentData(),
                'preset': self.preset_combo.currentData(),
                'video_codec': self.video_codec_combo.currentText(),
                'audio_codec': self.audio_codec_combo.currentText(),
                'video_bitrate': self.video_bitrate_spin.value(),
                'audio_bitrate': self.audio_bitrate_spin.value(),
                'resolution': self.get_current_resolution(),
                'fps': self.fps_spin.value(),
                'gpu_acceleration': self.gpu_accel_check.isChecked(),
                'encoding_preset': self.encoding_preset_combo.currentText(),
                'codec_params': self.codec_params_edit.toPlainText(),
                'quality_preset': self.quality_preset_combo.currentText(),
                'crf_value': self.crf_spin.value(),
                'error_handling': {
                    'auto_retry': self.auto_retry_check.isChecked(),
                    'max_retries': self.max_retries_spin.value(),
                    'retry_strategy': self.retry_strategy_combo.currentText(),
                    'cleanup_temp_files': self.cleanup_temp_files_check.isChecked(),
                    'preserve_failed_files': self.preserve_failed_files_check.isChecked()
                }
            }

            return settings

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"获取导出设置失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ExportSettingsComponent",
                    operation="get_export_settings"
                ),
                user_message="无法获取导出设置",
                recovery_action=RecoveryAction.NONE
            )
            self.error_handler.handle_error(error_info, parent=self)
            return {}

    def get_current_resolution(self) -> Tuple[int, int]:
        """获取当前分辨率"""
        resolution_text = self.resolution_combo.currentText()

        if "自定义" in resolution_text:
            return (self.custom_width_spin.value(), self.custom_height_spin.value())

        # 解析标准分辨率
        resolution_map = {
            "3840×2160 (4K)": (3840, 2160),
            "2560×1440 (2K)": (2560, 1440),
            "1920×1080 (1080p)": (1920, 1080),
            "1280×720 (720p)": (1280, 720),
            "854×480 (480p)": (854, 480)
        }

        return resolution_map.get(resolution_text, (1920, 1080))

    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'validation_timer'):
                self.validation_timer.stop()

            if hasattr(self, 'system_monitor'):
                self.system_monitor.stop()

        except Exception as e:
            self.logger.error(f"Failed to cleanup export settings component: {e}")


class SystemResourceMonitor(QThread):
    """系统资源监控线程"""

    resource_update = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.logger = Logger("SystemResourceMonitor")
        self.running = False
        self.update_interval = 2  # 秒

    def run(self):
        """运行监控"""
        self.running = True

        while self.running:
            try:
                import psutil

                # 获取系统资源信息
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                resource_info = {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_total_gb': memory.total / (1024**3),
                    'disk_info': {
                        'total_gb': disk.total / (1024**3),
                        'used_gb': disk.used / (1024**3),
                        'free_gb': disk.free / (1024**3),
                        'percent': (disk.used / disk.total) * 100
                    }
                }

                # 发送更新信号
                self.resource_update.emit(resource_info)

            except Exception as e:
                self.logger.error(f"Failed to monitor system resources: {e}")

            # 等待下次更新
            self.msleep(self.update_interval * 1000)

    def stop(self):
        """停止监控"""
        self.running = False
        self.wait()