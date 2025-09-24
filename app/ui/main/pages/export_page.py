#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出页面
提供完整的视频导出功能界面
"""

import os
import json
import time
import shutil
import platform
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QFileDialog, QMessageBox, QSplitter,
                            QFrame, QStackedWidget, QFormLayout, QProgressBar,
                            QTextEdit, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QRect
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QPen

from ...components.base_component import BaseComponent
from ..components.complete_export_manager import CompleteExportManager
from ....core.logger import Logger
from ....core.event_system import EventBus
from ....utils.error_handler import (
    ErrorHandler, ErrorType, ErrorSeverity, RecoveryAction,
    ErrorContext, safe_execute, error_handler_decorator
)


class ExportPage(BaseComponent):
    """导出页面"""

    # 信号定义
    export_started = pyqtSignal(str)
    export_progress = pyqtSignal(str, float)
    export_completed = pyqtSignal(str, str)
    export_failed = pyqtSignal(str, str)

    def __init__(self, application, parent=None):
        super().__init__(parent)
        self.application = application
        self.logger = Logger("ExportPage")
        self.current_project = None
        self.error_handler = ErrorHandler(self.logger)
        self.export_error_history = []
        self.setup_ui()
        self.connect_signals()
        self.setup_timer()
        self.setup_error_handling()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 页面标题
        title_widget = self.create_title_widget()
        layout.addWidget(title_widget)

        # 主要内容区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：导出管理器
        self.export_manager = CompleteExportManager(self.application, self)
        content_splitter.addWidget(self.export_manager)

        # 右侧：项目信息和快速操作
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)

        # 设置分割器比例
        content_splitter.setSizes([700, 300])

        layout.addWidget(content_splitter)

        # 底部状态栏
        status_widget = self.create_status_widget()
        layout.addWidget(status_widget)

    def create_title_widget(self) -> QWidget:
        """创建标题部件"""
        widget = QWidget()
        widget.setMaximumHeight(80)
        widget.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)

        # 标题
        title_label = QLabel("🎬 视频导出")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)

        # 副标题
        subtitle_label = QLabel("专业的视频导出和剪映Draft生成工具")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #6c757d;")

        # 快速统计
        self.quick_stats_label = QLabel("队列状态: 就绪")
        self.quick_stats_label.setStyleSheet("color: #28a745; font-weight: bold;")

        # 布局
        left_layout = QVBoxLayout()
        left_layout.addWidget(title_label)
        left_layout.addWidget(subtitle_label)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.quick_stats_label)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        layout.addLayout(left_layout)
        layout.addStretch()
        layout.addLayout(right_layout)

        return widget

    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        widget = QWidget()
        widget.setMaximumWidth(350)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)

        # 项目信息卡片
        project_card = self.create_project_card()
        layout.addWidget(project_card)

        # 快速操作卡片
        quick_actions_card = self.create_quick_actions_card()
        layout.addWidget(quick_actions_card)

        # 最近导出卡片
        recent_exports_card = self.create_recent_exports_card()
        layout.addWidget(recent_exports_card)

        # 系统状态卡片
        system_status_card = self.create_system_status_card()
        layout.addWidget(system_status_card)

        layout.addStretch()

        return widget

    def create_project_card(self) -> QWidget:
        """创建项目信息卡片"""
        card = self.create_card("当前项目")

        layout = QVBoxLayout(card)

        # 项目名称
        self.project_name_label = QLabel("未选择项目")
        project_name_font = QFont()
        project_name_font.setBold(True)
        project_name_font.setPointSize(14)
        self.project_name_label.setFont(project_name_font)

        # 项目详细信息
        details_layout = QFormLayout()
        details_layout.setSpacing(8)

        self.project_duration_label = QLabel("--:--:--")
        self.project_resolution_label = QLabel("--×--")
        self.project_size_label = QLabel("-- MB")
        self.project_modified_label = QLabel("--")

        details_layout.addRow("时长:", self.project_duration_label)
        details_layout.addRow("分辨率:", self.project_resolution_label)
        details_layout.addRow("大小:", self.project_size_label)
        details_layout.addRow("修改时间:", self.project_modified_label)

        # 项目操作按钮
        project_actions_layout = QHBoxLayout()

        self.open_project_btn = QPushButton("打开项目")
        self.open_project_btn.clicked.connect(self.open_project)

        self.project_settings_btn = QPushButton("项目设置")
        self.project_settings_btn.clicked.connect(self.open_project_settings)

        project_actions_layout.addWidget(self.open_project_btn)
        project_actions_layout.addWidget(self.project_settings_btn)

        layout.addWidget(self.project_name_label)
        layout.addLayout(details_layout)
        layout.addLayout(project_actions_layout)

        return card

    def create_quick_actions_card(self) -> QWidget:
        """创建快速操作卡片"""
        card = self.create_card("快速操作")

        layout = QVBoxLayout(card)

        # 快速导出按钮
        quick_actions = [
            ("🚀 YouTube 1080p", lambda: self.quick_export("youtube_1080p")),
            ("📱 TikTok", lambda: self.quick_export("tiktok_video")),
            ("📸 Instagram", lambda: self.quick_export("instagram_reel")),
            ("📝 剪映Draft", lambda: self.quick_export("jianying_draft")),
            ("⭐ 高质量", lambda: self.quick_export("master_quality")),
            ("🎬 批量导出", self.open_batch_export)
        ]

        for text, action in quick_actions:
            btn = QPushButton(text)
            btn.setMinimumHeight(35)
            btn.clicked.connect(action)
            layout.addWidget(btn)

        return card

    def create_recent_exports_card(self) -> QWidget:
        """创建最近导出卡片"""
        card = self.create_card("最近导出")

        layout = QVBoxLayout(card)

        self.recent_exports_list = self.create_recent_exports_list()
        layout.addWidget(self.recent_exports_list)

        # 查看历史按钮
        self.view_history_btn = QPushButton("查看完整历史")
        self.view_history_btn.clicked.connect(self.view_export_history)
        layout.addWidget(self.view_history_btn)

        return card

    def create_recent_exports_list(self) -> QWidget:
        """创建最近导出列表"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 这里应该显示最近5个导出记录
        self.recent_exports_labels = []

        for i in range(5):
            label = QLabel(f"{i+1}. 暂无导出记录")
            label.setStyleSheet("color: #6c757d; font-size: 12px; padding: 2px;")
            label.setWordWrap(True)
            layout.addWidget(label)
            self.recent_exports_labels.append(label)

        layout.addStretch()
        return widget

    def create_system_status_card(self) -> QWidget:
        """创建系统状态卡片"""
        card = self.create_card("系统状态")

        layout = QVBoxLayout(card)

        # 系统状态指示器
        status_items = [
            ("导出引擎", "engine_status_label"),
            ("性能优化", "performance_status_label"),
            ("队列管理", "queue_status_label"),
            ("GPU加速", "gpu_status_label")
        ]

        self.status_labels = {}

        for name, attr_name in status_items:
            # 创建水平布局
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(0, 2, 0, 2)

            name_label = QLabel(name + ":")
            name_label.setMinimumWidth(80)

            status_label = QLabel("正常")
            status_label.setStyleSheet("color: #28a745;")
            self.status_labels[name] = status_label
            # 保存属性引用
            setattr(self, attr_name, status_label)

            item_layout.addWidget(name_label)
            item_layout.addWidget(status_label)
            item_layout.addStretch()

            layout.addLayout(item_layout)

        # 系统信息按钮
        self.system_info_btn = QPushButton("详细系统信息")
        self.system_info_btn.clicked.connect(self.show_system_info)
        layout.addWidget(self.system_info_btn)

        return card

    def create_status_widget(self) -> QWidget:
        """创建状态栏部件"""
        widget = QWidget()
        widget.setMaximumHeight(30)
        widget.setStyleSheet("background-color: #e9ecef; border-top: 1px solid #dee2e6;")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 2, 10, 2)

        # 状态信息
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #495057;")

        # 队列信息
        self.queue_info_label = QLabel("队列: 0 个任务")
        self.queue_info_label.setStyleSheet("color: #495057;")

        # 性能信息
        self.performance_info_label = QLabel("CPU: --%, 内存: --%")
        self.performance_info_label.setStyleSheet("color: #495057;")

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.queue_info_label)
        layout.addWidget(self.performance_info_label)

        return widget

    def create_card(self, title: str) -> QWidget:
        """创建卡片样式部件"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)

        # 卡片标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #495057; padding-bottom: 5px; border-bottom: 1px solid #e9ecef; margin-bottom: 10px;")

        layout.addWidget(title_label)

        return widget

    def connect_signals(self):
        """连接信号"""
        # 导出管理器信号
        self.export_manager.export_started.connect(self.on_export_started)
        self.export_manager.export_progress.connect(self.on_export_progress)
        self.export_manager.export_completed.connect(self.on_export_completed)
        self.export_manager.export_failed.connect(self.on_export_failed)

    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(2000)  # 每2秒更新一次

    def setup_error_handling(self):
        """设置错误处理"""
        # 连接错误处理器信号
        self.error_handler.error_occurred.connect(self.on_error_occurred)
        self.error_handler.error_recovered.connect(self.on_error_recovered)

        # 设置全局错误处理器
        from ....utils.error_handler import set_global_error_handler
        set_global_error_handler(self.error_handler)

    def set_current_project(self, project_info: Dict[str, Any]):
        """设置当前项目"""
        self.current_project = project_info

        # 更新项目信息显示
        self.project_name_label.setText(project_info.get('name', '未知项目'))
        self.project_duration_label.setText(project_info.get('duration', '00:00:00'))
        self.project_resolution_label.setText(project_info.get('resolution', '1920×1080'))
        self.project_size_label.setText(project_info.get('size', '0 MB'))

        # 更新修改时间
        modified_time = project_info.get('modified_time')
        if modified_time:
            import time
            self.project_modified_label.setText(time.strftime("%Y-%m-%d %H:%M", time.localtime(modified_time)))
        else:
            self.project_modified_label.setText("--")

        # 传递给导出管理器
        self.export_manager.set_current_project(project_info)

        # 更新状态
        self.status_label.setText(f"当前项目: {project_info.get('name', '未知项目')}")

    def quick_export(self, preset_id: str):
        """快速导出"""
        @safe_execute(
            error_message="快速导出操作失败",
            error_type=ErrorType.EXPORT,
            severity=ErrorSeverity.HIGH,
            recovery_action=RecoveryAction.RETRY,
            parent=self
        )
        def _quick_export():
            # 验证项目选择
            if not self.current_project:
                error_info = ErrorInfo(
                    error_type=ErrorType.VALIDATION,
                    severity=ErrorSeverity.MEDIUM,
                    message="未选择项目进行导出",
                    context=ErrorContext(
                        component="ExportPage",
                        operation="quick_export",
                        user_action="快速导出"
                    ),
                    user_message="请先选择一个项目",
                    recovery_action=RecoveryAction.NONE
                )
                self.error_handler.handle_error(error_info, parent=self)
                return

            # 验证系统资源
            if not self.validate_system_resources_for_export():
                error_info = ErrorInfo(
                    error_type=ErrorType.SYSTEM,
                    severity=ErrorSeverity.HIGH,
                    message="系统资源不足以进行导出",
                    context=ErrorContext(
                        component="ExportPage",
                        operation="quick_export"
                    ),
                    user_message="系统资源不足，无法开始导出。建议关闭其他程序或降低导出质量。",
                    recovery_action=RecoveryAction.RESET
                )
                self.error_handler.handle_error(error_info, parent=self)
                return

            # 验证输出路径
            output_path = self.generate_output_path(preset_id)
            if not self.validate_output_path(output_path):
                error_info = ErrorInfo(
                    error_type=ErrorType.FILE,
                    severity=ErrorSeverity.HIGH,
                    message=f"输出路径无效或无权限: {output_path}",
                    context=ErrorContext(
                        component="ExportPage",
                        operation="quick_export"
                    ),
                    user_message="无法访问输出路径，请检查路径和权限设置。",
                    recovery_action=RecoveryAction.SKIP
                )
                self.error_handler.handle_error(error_info, parent=self)
                return

            # 开始导出
            try:
                self.logger.info(f"Starting quick export: {preset_id}")
                self.status_label.setText(f"正在快速导出: {preset_id}")

                # 调用导出管理器的快速导出功能
                task_id = self.export_manager.quick_export(preset_id)

                # 记录导出开始
                self.record_export_operation(
                    operation_type="quick_export",
                    preset_id=preset_id,
                    status="started",
                    task_id=task_id
                )

                # 显示进度对话框
                self.show_progress_dialog()

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
                        component="ExportPage",
                        operation="quick_export",
                        user_action="快速导出"
                    ),
                    user_message=self.get_user_friendly_export_error(export_error),
                    recovery_action=self.get_recovery_action_for_error(error_category),
                    technical_details={
                        "preset_id": preset_id,
                        "error_category": error_category,
                        "timestamp": time.time()
                    }
                )
                self.error_handler.handle_error(error_info, parent=self)
                raise

        _quick_export()

    def validate_system_resources_for_export(self) -> bool:
        """验证系统资源是否足以进行导出"""
        try:
            import psutil

            # 检查内存
            memory = psutil.virtual_memory()
            if memory.available < 2 * 1024 * 1024 * 1024:  # 2GB可用内存
                self.logger.warning("Insufficient memory for export")
                return False

            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:  # CPU使用率超过90%
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
                return False

            # 检查磁盘空间
            if hasattr(self, 'current_project') and self.current_project:
                output_path = self.generate_output_path("temp")
                disk_ok, _ = self.check_output_disk_space(output_path)
                if not disk_ok:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate system resources: {e}")
            return False

    def generate_output_path(self, preset_id: str) -> str:
        """生成输出路径"""
        if not self.current_project:
            project_name = "unknown_project"
        else:
            project_name = self.current_project.get('name', 'unknown_project')

        # 清理项目名称
        project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()

        # 生成文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        extension = "mp4" if preset_id != "jianying_draft" else "json"

        return f"{project_name}_{preset_id}_{timestamp}.{extension}"

    def validate_output_path(self, output_path: str) -> bool:
        """验证输出路径"""
        try:
            # 检查路径格式
            if not output_path or len(output_path) > 260:  # Windows路径长度限制
                return False

            # 检查输出目录
            output_dir = os.path.dirname(output_path)
            if not output_dir:
                output_dir = os.getcwd()

            # 检查目录是否存在
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception:
                    return False

            # 检查写入权限
            test_file = os.path.join(output_dir, ".write_test")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate output path: {e}")
            return False

    def check_output_disk_space(self, output_path: str) -> tuple[bool, dict]:
        """检查输出磁盘空间"""
        try:
            # 估算文件大小 (简化计算)
            estimated_size_mb = 500  # 默认500MB

            if hasattr(self, 'current_project') and self.current_project:
                # 根据项目信息估算
                duration_str = self.current_project.get('duration', '00:00:00')
                if duration_str != '00:00:00':
                    # 解析时长
                    parts = duration_str.split(':')
                    if len(parts) == 3:
                        hours, minutes, seconds = map(int, parts)
                        duration_minutes = hours * 60 + minutes + seconds / 60
                        estimated_size_mb = int(duration_minutes * 100)  # 每分钟约100MB

            output_dir = os.path.dirname(output_path)
            if not output_dir:
                output_dir = os.getcwd()

            disk_usage = shutil.disk_usage(output_dir)
            available_mb = disk_usage.free / (1024 * 1024)

            space_ok = available_mb > estimated_size_mb * 1.2  # 预留20%缓冲

            return space_ok, {
                'required_mb': estimated_size_mb,
                'available_mb': available_mb,
                'required_gb': estimated_size_mb / 1024,
                'available_gb': available_mb / 1024
            }

        except Exception as e:
            self.logger.error(f"Failed to check disk space: {e}")
            return False, {'error': str(e)}

    def record_export_operation(self, operation_type: str, preset_id: str,
                             status: str, task_id: str = None, error_message: str = None):
        """记录导出操作"""
        try:
            operation_record = {
                'timestamp': time.time(),
                'operation_type': operation_type,
                'preset_id': preset_id,
                'status': status,
                'task_id': task_id,
                'error_message': error_message,
                'project_id': self.current_project.get('id') if self.current_project else None,
                'project_name': self.current_project.get('name') if self.current_project else None
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
            return ExportErrorCategories.PERMISSION_DENIED
        elif any(keyword in error_str for keyword in ['disk space', 'no space', 'disk full']):
            return ExportErrorCategories.DISK_SPACE_INSUFFICIENT
        elif any(keyword in error_str for keyword in ['file not found', 'no such file']):
            return ExportErrorCategories.FILE_NOT_FOUND
        elif any(keyword in error_str for keyword in ['format', 'codec', 'encoder']):
            return ExportErrorCategories.CODEC_ERROR
        elif any(keyword in error_str for keyword in ['gpu', 'cuda', 'opencl']):
            return ExportErrorCategories.GPU_ACCELERATION_FAILED
        elif 'cancel' in error_str or 'abort' in error_str:
            return ExportErrorCategories.CANCELLED_BY_USER
        else:
            return ExportErrorCategories.SYSTEM_ERROR

    def get_user_friendly_export_error(self, error: Exception) -> str:
        """获取用户友好的导出错误消息"""
        error_category = self.categorize_export_error(error)

        error_messages = {
            ExportErrorCategories.PERMISSION_DENIED: "没有文件写入权限，请检查输出目录的权限设置。",
            ExportErrorCategories.DISK_SPACE_INSUFFICIENT: "磁盘空间不足，请清理磁盘或选择其他输出位置。",
            ExportErrorCategories.FILE_NOT_FOUND: "源文件不存在或已损坏，请检查项目文件。",
            ExportErrorCategories.CODEC_ERROR: "视频编码器错误，请尝试更改导出格式或编码设置。",
            ExportErrorCategories.GPU_ACCELERATION_FAILED: "GPU加速失败，请尝试禁用GPU加速或更新显卡驱动。",
            ExportErrorCategories.CANCELLED_BY_USER: "导出操作已被用户取消。",
            ExportErrorCategories.SYSTEM_ERROR: "系统错误导致导出失败，请重启应用程序后重试。",
            ExportErrorCategories.VALIDATION_ERROR: "导出参数验证失败，请检查导出设置。"
        }

        return error_messages.get(error_category, f"导出失败: {str(error)}")

    def get_recovery_action_for_error(self, error_category: str) -> RecoveryAction:
        """根据错误类别获取恢复动作"""
        recovery_actions = {
            ExportErrorCategories.PERMISSION_DENIED: RecoveryAction.RESET,
            ExportErrorCategories.DISK_SPACE_INSUFFICIENT: RecoveryAction.SKIP,
            ExportErrorCategories.FILE_NOT_FOUND: RecoveryAction.ROLLBACK,
            ExportErrorCategories.CODEC_ERROR: RecoveryAction.RETRY,
            ExportErrorCategories.GPU_ACCELERATION_FAILED: RecoveryAction.RESET,
            ExportErrorCategories.CANCELLED_BY_USER: RecoveryAction.NONE,
            ExportErrorCategories.SYSTEM_ERROR: RecoveryAction.CONTACT_SUPPORT,
            ExportErrorCategories.VALIDATION_ERROR: RecoveryAction.RESET
        }

        return recovery_actions.get(error_category, RecoveryAction.NONE)

    def on_error_occurred(self, error_info):
        """错误发生事件处理"""
        self.logger.error(f"Error occurred in export page: {error_info.message}")

        # 更新状态显示
        self.status_label.setText(f"错误: {error_info.user_message}")
        self.status_label.setStyleSheet("color: #dc3545;")

    def on_error_recovered(self, error_info, recovery_action):
        """错误恢复事件处理"""
        self.logger.info(f"Error recovered: {error_info.message} with {recovery_action}")

        # 更新状态显示
        self.status_label.setText("错误已恢复")
        self.status_label.setStyleSheet("color: #28a745;")

    def show_progress_dialog(self):
        """显示进度对话框"""
        if hasattr(self, 'export_manager') and hasattr(self.export_manager, 'show_progress_dialog'):
            self.export_manager.show_progress_dialog()

    def open_project(self):
        """打开项目"""
        # 这里需要实现项目打开逻辑
        QMessageBox.information(self, "提示", "打开项目功能正在开发中...")

    def open_project_settings(self):
        """打开项目设置"""
        # 这里需要实现项目设置逻辑
        QMessageBox.information(self, "提示", "项目设置功能正在开发中...")

    def open_batch_export(self):
        """打开批量导出"""
        # 切换到批量导出标签页
        self.export_manager.main_tab_widget.setCurrentIndex(2)  # 批量导出标签页索引

    def view_export_history(self):
        """查看导出历史"""
        # 这里需要实现导出历史查看功能
        QMessageBox.information(self, "提示", "导出历史功能正在开发中...")

    def show_system_info(self):
        """显示系统信息"""
        try:
            # 获取系统信息
            import psutil
            import platform

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            info_text = f"""系统信息：

操作系统: {platform.system()} {platform.release()}
CPU使用率: {cpu_percent}%
内存使用: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
磁盘空间: {disk.percent}% ({disk.free // (1024**3)}GB 可用)

Python版本: {platform.python_version()}
"""

            QMessageBox.information(self, "系统信息", info_text)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取系统信息失败: {str(e)}")

    def update_status(self):
        """更新状态信息"""
        try:
            # 更新队列信息
            if hasattr(self.application, 'export_system'):
                queue_status = self.application.export_system.get_queue_status()
                queue_text = (f"队列: {queue_status['queue_size']} 待处理, "
                             f"{queue_status['active_tasks']} 处理中")
                self.queue_info_label.setText(queue_text)
                self.quick_stats_label.setText(f"队列状态: {queue_status['active_tasks']} 活动任务")

            # 更新性能信息
            import psutil
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()

                perf_text = f"CPU: {cpu_percent:.1f}%, 内存: {memory.percent:.1f}%"
                self.performance_info_label.setText(perf_text)
            except:
                self.performance_info_label.setText("CPU: --%, 内存: --%")

            # 更新系统状态
            self.update_system_status()

            # 更新最近导出记录
            self.update_recent_exports()

        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")

    def update_system_status(self):
        """更新系统状态"""
        try:
            # 检查导出引擎状态
            engine_status = "正常"
            if hasattr(self.application, 'export_system'):
                # 这里可以添加更多检查
                pass

            # 检查性能优化状态
            perf_status = "正常"
            if hasattr(self.application, 'performance_optimizer'):
                # 这里可以添加更多检查
                pass

            # 检查队列管理状态
            queue_status = "正常"
            if hasattr(self.application, 'export_system'):
                queue_status_info = self.application.export_system.get_queue_status()
                if queue_status_info['active_tasks'] > 0:
                    queue_status = "运行中"

            # 检查GPU状态
            gpu_status = "正常"
            # 这里可以添加GPU检测逻辑

            # 更新状态标签
            if "导出引擎" in self.status_labels:
                self.status_labels["导出引擎"].setText(engine_status)
                self.status_labels["导出引擎"].setStyleSheet("color: #28a745;")

            if "性能优化" in self.status_labels:
                self.status_labels["性能优化"].setText(perf_status)
                self.status_labels["性能优化"].setStyleSheet("color: #28a745;")

            if "队列管理" in self.status_labels:
                self.status_labels["队列管理"].setText(queue_status)
                color = "#ffc107" if queue_status == "运行中" else "#28a745"
                self.status_labels["队列管理"].setStyleSheet(f"color: {color};")

            if "GPU加速" in self.status_labels:
                self.status_labels["GPU加速"].setText(gpu_status)
                self.status_labels["GPU加速"].setStyleSheet("color: #28a745;")

        except Exception as e:
            self.logger.error(f"Failed to update system status: {e}")

    def update_recent_exports(self):
        """更新最近导出记录"""
        try:
            if hasattr(self.application, 'export_system'):
                tasks = self.application.export_system.get_task_history()

                # 获取最近5个完成的导出
                completed_tasks = [t for t in tasks if t.status.value == "completed"][:5]

                for i, task in enumerate(completed_tasks):
                    if i < len(self.recent_exports_labels):
                        project_name = task.metadata.get("project_name", "未知项目")
                        preset_name = task.preset.name if task.preset else "未知预设"
                        output_path = os.path.basename(task.output_path) if task.output_path else "未知路径"

                        text = f"{i+1}. {project_name} - {preset_name}"
                        if len(text) > 40:
                            text = text[:37] + "..."

                        self.recent_exports_labels[i].setText(text)
                        self.recent_exports_labels[i].setStyleSheet("color: #495057; font-size: 12px; padding: 2px;")

                # 清空多余的标签
                for i in range(len(completed_tasks), len(self.recent_exports_labels)):
                    self.recent_exports_labels[i].setText(f"{i+1}. 暂无更多记录")
                    self.recent_exports_labels[i].setStyleSheet("color: #6c757d; font-size: 12px; padding: 2px;")

        except Exception as e:
            self.logger.error(f"Failed to update recent exports: {e}")

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

    def on_export_failed(self, task_id: str, error_message: str):
        """导出失败事件"""
        self.logger.error(f"Export failed: {task_id} - {error_message}")
        self.export_failed.emit(task_id, error_message)

    def get_page_name(self) -> str:
        """获取页面名称"""
        return "视频导出"

    def get_page_icon(self) -> str:
        """获取页面图标"""
        return "🎬"

    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()

            if hasattr(self, 'export_manager'):
                self.export_manager.cleanup()

        except Exception as e:
            self.logger.error(f"Failed to cleanup export page: {e}")

    def update_theme(self, is_dark: bool = True):
        """更新主题"""
        # 这里可以实现主题更新逻辑
        pass