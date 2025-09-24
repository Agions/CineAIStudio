#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 首页
提供快速开始、最近项目、系统状态和AI工具入口
"""

import os
import sys
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QPushButton, QLabel, QFrame, QGroupBox, QSplitter
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal
)
from PyQt6.QtGui import QFont

from ...core.application import Application, ApplicationState
from ...core.config_manager import ConfigManager
from ...core.logger import Logger
# 事件总线由应用程序内部创建
from ...core.project_manager import ProjectManager
from ...ui.components.project_manager_component import ProjectManagerWidget, CreateProjectDialog
from ...utils.error_handler import (
    get_global_error_handler, ErrorInfo, ErrorType, ErrorSeverity,
    ErrorContext, RecoveryAction, safe_execute, error_handler_decorator
)
from ...utils.ui_error_handler import get_ui_error_handler, UIErrorType, UIErrorSeverity, UIErrorInfo
from ...utils.file_error_handler import get_file_error_handler


@dataclass
class ProjectInfo:
    """项目信息"""
    id: str
    name: str
    path: str
    description: str
    last_modified: datetime
    thumbnail: Optional[str] = None
    duration: int = 0  # 视频时长（秒）
    file_count: int = 0  # 文件数量


class QuickStartPanel(QWidget):
    """快速开始面板"""

    project_created = pyqtSignal(ProjectInfo)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service(ConfigManager)
        self.error_handler = get_global_error_handler()
        self.ui_error_handler = get_ui_error_handler()
        self.file_error_handler = get_file_error_handler()

        # 获取项目管理器
        self.project_manager = application.get_service_by_name("project_manager")
        if not self.project_manager:
            from ...core.project_manager import ProjectManager
            self.project_manager = ProjectManager(self.config_manager)

        try:
            self._init_ui()
            self._setup_animations()
        except Exception as e:
            self._handle_component_error(e, "__init__", UIErrorSeverity.CRITICAL)

    def _handle_component_error(self, exception: Exception, operation: str, severity: UIErrorSeverity = UIErrorSeverity.MAJOR):
        """处理组件错误"""
        error_info = ErrorInfo(
            error_type=ErrorType.UI,
            severity=ErrorSeverity.HIGH if severity == UIErrorSeverity.CRITICAL else ErrorSeverity.MEDIUM,
            message=f"QuickStartPanel {operation} 失败: {str(exception)}",
            exception=exception,
            context=ErrorContext(
                component="QuickStartPanel",
                operation=operation,
                system_state={
                    "application": str(self.application),
                    "config_manager": str(self.config_manager)
                }
            ),
            recovery_action=RecoveryAction.RETRY,
            user_message="快速开始面板初始化失败，正在尝试恢复..."
        )

        self.error_handler.handle_error(error_info, show_dialog=True, parent=self)

        # 对于关键错误，禁用组件
        if severity == UIErrorSeverity.CRITICAL:
            self.setEnabled(False)
            self.setVisible(False)

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 欢迎标题区域
        welcome_widget = self._create_welcome_section()
        layout.addWidget(welcome_widget)

        # 主要操作按钮区域
        primary_actions_widget = self._create_primary_actions_section()
        layout.addWidget(primary_actions_widget)

        # AI功能快捷入口
        ai_actions_widget = self._create_ai_actions_section()
        layout.addWidget(ai_actions_widget)

        layout.addStretch()

    def _create_welcome_section(self) -> QWidget:
        """创建欢迎区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 主标题
        title_label = QLabel("欢迎使用 CineAIStudio")
        title_font = QFont("Arial", 20, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("AI驱动的智能视频创作平台")
        subtitle_font = QFont("Arial", 12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("""
            color: #b0b0b0;
            font-size: 12px;
        """)
        layout.addWidget(subtitle_label)

        return widget

    def _create_primary_actions_section(self) -> QWidget:
        """创建主要操作区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("快速开始")
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        layout.addWidget(title_label)

        # 按钮网格
        button_layout = QGridLayout()
        button_layout.setSpacing(12)

        # 创建项目按钮（主要操作）
        create_project_btn = self._create_enhanced_button(
            "创建新项目",
            "开始一个新的视频编辑项目",
            "plus",
            "#1890ff",
            self._on_create_project,
            is_primary=True
        )
        button_layout.addWidget(create_project_btn, 0, 0)

        # 打开项目按钮
        open_project_btn = self._create_enhanced_button(
            "打开项目",
            "打开已有的视频编辑项目",
            "folder",
            "#52c41a",
            self._on_open_project
        )
        button_layout.addWidget(open_project_btn, 0, 1)

        # 导入媒体按钮
        import_media_btn = self._create_enhanced_button(
            "导入媒体",
            "导入视频、音频或图片文件",
            "upload",
            "#fa8c16",
            self._on_import_media
        )
        button_layout.addWidget(import_media_btn, 1, 0)

        # 模板项目按钮
        template_btn = self._create_enhanced_button(
            "使用模板",
            "从模板快速创建项目",
            "template",
            "#722ed1",
            self._on_use_template
        )
        button_layout.addWidget(template_btn, 1, 1)

        layout.addLayout(button_layout)
        return widget

    def _create_ai_actions_section(self) -> QWidget:
        """创建AI功能区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("AI 功能")
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        layout.addWidget(title_label)

        # AI功能按钮网格
        ai_button_layout = QGridLayout()
        ai_button_layout.setSpacing(10)

        ai_features = [
            ("AI剪辑", "智能剪辑视频内容", "cut", "#1890ff", self._on_ai_editing),
            ("AI解说", "自动生成视频解说", "voice", "#52c41a", self._on_ai_commentary),
            ("AI配乐", "智能匹配背景音乐", "music", "#fa8c16", self._on_ai_music),
            ("AI字幕", "自动生成字幕", "subtitle", "#722ed1", self._on_ai_subtitle)
        ]

        for i, (title, desc, icon, color, callback) in enumerate(ai_features):
            btn = self._create_compact_button(title, desc, icon, color, callback)
            row = i // 2
            col = i % 2
            ai_button_layout.addWidget(btn, row, col)

        layout.addLayout(ai_button_layout)
        return widget

    def _create_enhanced_button(self, title: str, description: str, icon_name: str,
                              color: str, callback, is_primary: bool = False) -> QWidget:
        """创建增强按钮"""
        container = QFrame()
        container.setObjectName(f"enhancedButton_{title}")
        container.setFrameStyle(QFrame.Shape.Box)

        # 根据是否为主要操作设置不同的样式
        if is_primary:
            container.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border: 2px solid {color};
                    border-radius: 12px;
                    padding: 15px;
                }}
                QFrame:hover {{
                    background-color: {self._adjust_color(color, 1.2)};
                    border-color: {self._adjust_color(color, 1.2)};
                }}
            """)
            container.setFixedSize(180, 100)
        else:
            container.setStyleSheet(f"""
                QFrame {{
                    background-color: #2d2d2d;
                    border: 2px solid #404040;
                    border-radius: 12px;
                    padding: 15px;
                }}
                QFrame:hover {{
                    background-color: #404040;
                    border-color: {color};
                }}
            """)
            container.setFixedSize(180, 100)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 图标和标题
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # 图标
        try:
            from ...core.icon_manager import get_icon
            icon_label = QLabel()
            icon_label.setPixmap(get_icon(icon_name, 24).pixmap(24, 24))
            header_layout.addWidget(icon_label)
        except:
            header_layout.addSpacing(24)

        # 标题
        title_label = QLabel(title)
        title_color = "#ffffff" if is_primary else "#ffffff"
        title_label.setStyleSheet(f"""
            color: {title_color};
            font-size: 14px;
            font-weight: bold;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 描述
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            color: {'#ffffff' if is_primary else '#b0b0b0'};
            font-size: 11px;
            text-align: center;
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        container.mousePressEvent = lambda event: callback()

        return container

    def _create_compact_button(self, title: str, description: str, icon_name: str,
                              color: str, callback) -> QWidget:
        """创建紧凑按钮"""
        container = QFrame()
        container.setObjectName(f"compactButton_{title}")
        container.setFrameStyle(QFrame.Shape.Box)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                background-color: #404040;
                border-color: {color};
            }}
        """)
        container.setFixedSize(85, 70)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 图标
        try:
            from ...core.icon_manager import get_icon
            icon_label = QLabel()
            icon_label.setPixmap(get_icon(icon_name, 20).pixmap(20, 20))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        except:
            layout.addSpacing(20)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 11px;
            font-weight: bold;
            text-align: center;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        container.mousePressEvent = lambda event: callback()

        return container

    def _adjust_color(self, hex_color: str, factor: float) -> str:
        """调整颜色亮度"""
        try:
            # 移除#号
            hex_color = hex_color.lstrip('#')
            # 转换为RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # 调整亮度
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))

            # 转换回十六进制
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color

    def _setup_animations(self):
        """设置动画效果"""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        self.animations = {}

    def _on_use_template(self):
        """使用模板"""
        try:
            self.logger.info("打开项目模板")
            # 这里可以跳转到模板选择页面
        except Exception as e:
            self.logger.error(f"打开模板失败: {e}")

    def _on_ai_editing(self):
        """AI剪辑"""
        try:
            self.logger.info("打开AI剪辑功能")
            # 跳转到AI剪辑页面
        except Exception as e:
            self.logger.error(f"打开AI剪辑失败: {e}")

    def _on_ai_commentary(self):
        """AI解说"""
        try:
            self.logger.info("打开AI解说功能")
            # 跳转到AI解说页面
        except Exception as e:
            self.logger.error(f"打开AI解说失败: {e}")

    def _on_ai_music(self):
        """AI配乐"""
        try:
            self.logger.info("打开AI配乐功能")
            # 跳转到AI配乐页面
        except Exception as e:
            self.logger.error(f"打开AI配乐失败: {e}")

    def _on_ai_subtitle(self):
        """AI字幕"""
        try:
            self.logger.info("打开AI字幕功能")
            # 跳转到AI字幕页面
        except Exception as e:
            self.logger.error(f"打开AI字幕失败: {e}")

    @error_handler_decorator(
        error_type=ErrorType.UI,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.RETRY,
        user_message="创建项目失败，正在重试..."
    )
    def _on_create_project(self):
        """创建新项目"""
        try:
            # 显示创建项目对话框
            dialog = CreateProjectDialog(self.project_manager, self)
            dialog.project_created.connect(self._on_project_dialog_created)
            dialog.exec()

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.UI,
                severity=ErrorSeverity.MEDIUM,
                message=f"创建项目对话框失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="QuickStartPanel",
                    operation="_on_create_project",
                    system_state={"project_manager": str(self.project_manager)}
                ),
                recovery_action=RecoveryAction.SHOW_DIALOG,
                user_message="无法创建项目，请检查项目管理系统是否正常"
            )
            self.ui_error_handler.handle_ui_error(
                UIErrorInfo(
                    ui_error_type=UIErrorType.DIALOG_ERROR,
                    severity=UIErrorSeverity.MAJOR,
                    message="创建项目对话框初始化失败",
                    exception=e,
                    component="QuickStartPanel",
                    operation="_on_create_project",
                    user_message="无法打开创建项目对话框，请稍后重试"
                ),
                show_dialog=True,
                parent=self
            )

    @error_handler_decorator(
        error_type=ErrorType.UI,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.SHOW_DIALOG,
        user_message="项目创建处理失败"
    )
    def _on_project_dialog_created(self, project_data: dict):
        """处理项目对话框创建"""
        try:
            # 验证输入数据
            if not project_data or 'id' not in project_data:
                raise ValueError("无效的项目数据")

            # 获取创建的项目
            project = self.project_manager.get_project(project_data['id'])
            if project:
                project_info = ProjectInfo(
                    id=project.id,
                    name=project.metadata.name,
                    path=project.path,
                    description=project.metadata.description,
                    last_modified=project.metadata.modified_at
                )
                self.project_created.emit(project_info)
                self.logger.info(f"创建新项目: {project.metadata.name}")
            else:
                raise ValueError(f"无法找到项目: {project_data['id']}")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.VALIDATION,
                severity=ErrorSeverity.MEDIUM,
                message=f"处理项目创建失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="QuickStartPanel",
                    operation="_on_project_dialog_created",
                    system_state={"project_data": project_data}
                ),
                recovery_action=RecoveryAction.SHOW_DIALOG,
                user_message="项目创建失败，请检查项目数据是否正确"
            )
            self.ui_error_handler.handle_ui_error(
                UIErrorInfo(
                    ui_error_type=UIErrorType.VALIDATION_ERROR,
                    severity=UIErrorSeverity.MAJOR,
                    message="项目数据处理失败",
                    exception=e,
                    component="QuickStartPanel",
                    operation="_on_project_dialog_created",
                    user_message="无法完成项目创建，请检查输入数据"
                ),
                show_dialog=True,
                parent=self
            )

    @error_handler_decorator(
        error_type=ErrorType.FILE,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.SHOW_DIALOG,
        user_message="打开项目失败，正在重试..."
    )
    def _on_open_project(self):
        """打开项目"""
        try:
            from PyQt6.QtWidgets import QFileDialog

            # 使用文件错误处理器安全地选择项目目录
            def safe_select_project():
                project_dir = QFileDialog.getExistingDirectory(
                    self,
                    "打开项目",
                    os.path.expanduser("~"),
                    QFileDialog.Option.ShowDirsOnly
                )
                return project_dir

            project_dir = safe_execute(safe_select_project)

            if project_dir:
                # 使用文件错误处理器检查项目文件
                project_file = os.path.join(project_dir, 'project.json')
                if self.file_error_handler.safe_file_exists(project_file, component="OpenProject"):
                    # 安全地打开项目
                    project_id = self.project_manager.open_project(project_dir)
                    if project_id:
                        project = self.project_manager.get_project(project_id)
                        if project:
                            project_info = ProjectInfo(
                                id=project.id,
                                name=project.metadata.name,
                                path=project.path,
                                description=project.metadata.description,
                                last_modified=project.metadata.modified_at
                            )
                            self.project_created.emit(project_info)
                            self.logger.info(f"打开项目: {project.metadata.name}")
                        else:
                            raise ValueError(f"无法获取项目数据: {project_id}")
                    else:
                        raise ValueError(f"项目管理器无法打开项目: {project_dir}")
                else:
                    raise FileNotFoundError(f"无效的项目目录，缺少project.json文件: {project_dir}")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.MEDIUM,
                message=f"打开项目失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="QuickStartPanel",
                    operation="_on_open_project",
                    system_state={"project_dir": project_dir if 'project_dir' in locals() else None}
                ),
                recovery_action=RecoveryAction.SHOW_DIALOG,
                user_message="无法打开项目，请检查项目文件是否存在"
            )
            self.ui_error_handler.handle_ui_error(
                UIErrorInfo(
                    ui_error_type=UIErrorType.FILE_OPERATION_ERROR,
                    severity=UIErrorSeverity.MAJOR,
                    message="项目文件操作失败",
                    exception=e,
                    component="QuickStartPanel",
                    operation="_on_open_project",
                    user_message="无法打开项目文件，请检查项目路径和文件完整性"
                ),
                show_dialog=True,
                parent=self
            )

    @error_handler_decorator(
        error_type=ErrorType.FILE,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.SHOW_DIALOG,
        user_message="导入媒体失败，正在重试..."
    )
    def _on_import_media(self):
        """导入媒体"""
        try:
            from PyQt6.QtWidgets import QFileDialog

            # 使用文件错误处理器安全地选择媒体文件
            def safe_select_media():
                files, _ = QFileDialog.getOpenFileNames(
                    self,
                    "导入媒体文件",
                    os.path.expanduser("~"),
                    "媒体文件 (*.mp4 *.avi *.mov *.mkv *.mp3 *.wav *.jpg *.png *.bmp);;所有文件 (*)"
                )
                return files

            files = safe_execute(safe_select_media)

            if files:
                # 验证文件存在性和可读性
                valid_files = []
                for file_path in files:
                    if self.file_error_handler.safe_file_exists(file_path, component="ImportMedia"):
                        # 检查文件是否可读
                        if self.file_error_handler.safe_check_file_readable(file_path, component="ImportMedia"):
                            valid_files.append(file_path)
                        else:
                            self.logger.warning(f"文件不可读: {file_path}")
                    else:
                        self.logger.warning(f"文件不存在: {file_path}")

                if valid_files:
                    self.logger.info(f"导入媒体文件: {len(valid_files)} 个")
                    # 这里可以添加实际导入逻辑
                else:
                    raise ValueError("没有有效的媒体文件可供导入")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.MEDIUM,
                message=f"导入媒体失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="QuickStartPanel",
                    operation="_on_import_media",
                    system_state={"files_count": len(files) if 'files' in locals() else 0}
                ),
                recovery_action=RecoveryAction.SHOW_DIALOG,
                user_message="无法导入媒体文件，请检查文件是否存在且可读"
            )
            self.ui_error_handler.handle_ui_error(
                UIErrorInfo(
                    ui_error_type=UIErrorType.FILE_OPERATION_ERROR,
                    severity=UIErrorSeverity.MAJOR,
                    message="媒体文件导入失败",
                    exception=e,
                    component="QuickStartPanel",
                    operation="_on_import_media",
                    user_message="无法导入媒体文件，请检查文件权限和完整性"
                ),
                show_dialog=True,
                parent=self
            )

    def _on_ai_tools(self):
        """AI工具"""
        try:
            self.logger.info("打开AI工具")
            # 这里可以跳转到AI工具页面或显示AI工具面板

        except Exception as e:
            self.logger.error(f"打开AI工具失败: {e}")


class RecentProjectsPanel(QWidget):
    """最近项目面板"""

    project_opened = pyqtSignal(ProjectInfo)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service(ConfigManager)
        self.error_handler = get_global_error_handler()
        self.ui_error_handler = get_ui_error_handler()
        self.file_error_handler = get_file_error_handler()

        self.recent_projects: List[ProjectInfo] = []

        try:
            self._init_ui()
            self._load_recent_projects()
        except Exception as e:
            self._handle_component_error(e, "__init__", UIErrorSeverity.CRITICAL)

    def _handle_component_error(self, exception: Exception, operation: str, severity: UIErrorSeverity = UIErrorSeverity.MAJOR):
        """处理组件错误"""
        error_info = ErrorInfo(
            error_type=ErrorType.UI,
            severity=ErrorSeverity.HIGH if severity == UIErrorSeverity.CRITICAL else ErrorSeverity.MEDIUM,
            message=f"RecentProjectsPanel {operation} 失败: {str(exception)}",
            exception=exception,
            context=ErrorContext(
                component="RecentProjectsPanel",
                operation=operation,
                system_state={
                    "application": str(self.application),
                    "config_manager": str(self.config_manager),
                    "recent_projects_count": len(self.recent_projects)
                }
            ),
            recovery_action=RecoveryAction.RETRY,
            user_message="最近项目面板初始化失败，正在尝试恢复..."
        )

        self.error_handler.handle_error(error_info, show_dialog=True, parent=self)

        # 对于关键错误，禁用组件
        if severity == UIErrorSeverity.CRITICAL:
            self.setEnabled(False)
            self.setVisible(False)

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题和操作按钮
        header_layout = QHBoxLayout()

        title_label = QLabel("最近项目")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 查看全部按钮
        view_all_btn = QPushButton("查看全部")
        view_all_btn.setFixedSize(80, 28)
        view_all_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1890ff;
                border: 1px solid #1890ff;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1890ff;
                color: white;
            }
        """)
        view_all_btn.clicked.connect(self._on_view_all_projects)
        header_layout.addWidget(view_all_btn)

        layout.addLayout(header_layout)

        # 项目列表
        self.projects_scroll = QScrollArea()
        self.projects_scroll.setWidgetResizable(True)
        self.projects_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.projects_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.projects_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        self.projects_widget = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_widget)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(12)

        self.projects_scroll.setWidget(self.projects_widget)
        layout.addWidget(self.projects_scroll)

    @error_handler_decorator(
        error_type=ErrorType.CONFIG,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.USE_DEFAULT,
        user_message="加载最近项目失败，正在重试..."
    )
    def _load_recent_projects(self):
        """加载最近项目"""
        try:
            # 使用文件错误处理器安全地加载配置
            def safe_load_config():
                settings = self.config_manager.get_settings()
                return settings.get("recent_projects", [])

            recent_projects_data = safe_execute(safe_load_config)

            self.recent_projects = []
            for project_data in recent_projects_data:
                # 验证项目数据完整性
                if not isinstance(project_data, dict):
                    self.logger.warning(f"无效的项目数据格式: {project_data}")
                    continue

                # 检查必需字段
                required_fields = ["id", "name", "path", "last_modified"]
                if not all(field in project_data for field in required_fields):
                    self.logger.warning(f"项目数据缺少必需字段: {project_data}")
                    continue

                # 检查项目路径是否存在
                project_path = project_data.get("path", "")
                if self.file_error_handler.safe_file_exists(os.path.join(project_path, 'project.json'), component="RecentProjects"):
                    try:
                        project_info = ProjectInfo(
                            id=project_data["id"],
                            name=project_data["name"],
                            path=project_path,
                            description=project_data.get("description", ""),
                            last_modified=datetime.fromisoformat(project_data["last_modified"]),
                            thumbnail=project_data.get("thumbnail"),
                            duration=project_data.get("duration", 0),
                            file_count=project_data.get("file_count", 0)
                        )
                        self.recent_projects.append(project_info)
                    except ValueError as e:
                        self.logger.warning(f"日期格式错误，跳过项目: {project_data['name']} - {e}")
                        continue
                else:
                    self.logger.info(f"项目不存在，从最近列表中移除: {project_path}")

            self._update_projects_display()

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.CONFIG,
                severity=ErrorSeverity.MEDIUM,
                message=f"加载最近项目失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="RecentProjectsPanel",
                    operation="_load_recent_projects",
                    system_state={
                        "config_manager": str(self.config_manager),
                        "recent_projects_count": len(self.recent_projects)
                    }
                ),
                recovery_action=RecoveryAction.USE_DEFAULT,
                user_message="无法加载最近项目列表，将显示空列表"
            )
            self.ui_error_handler.handle_ui_error(
                UIErrorInfo(
                    ui_error_type=UIErrorType.CONFIG_ERROR,
                    severity=UIErrorSeverity.MAJOR,
                    message="最近项目配置加载失败",
                    exception=e,
                    component="RecentProjectsPanel",
                    operation="_load_recent_projects",
                    user_message="无法加载最近项目，可能是配置文件损坏"
                ),
                show_dialog=False,  # 不显示对话框，只是记录错误
                parent=self
            )

    def _refresh_projects(self):
        """刷新项目列表"""
        self._load_recent_projects()

    def _update_projects_display(self):
        """更新项目显示"""
        # 清空现有项目
        for i in reversed(range(self.projects_layout.count())):
            item = self.projects_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # 添加项目卡片
        for project in self.recent_projects[:5]:  # 只显示最近5个项目
            project_card = self._create_project_card(project)
            self.projects_layout.addWidget(project_card)

        self.projects_layout.addStretch()

    def _create_project_card(self, project: ProjectInfo) -> QWidget:
        """创建项目卡片"""
        card = QFrame()
        card.setObjectName(f"projectCard_{project.id}")
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 15px;
            }
            QFrame:hover {
                background-color: #3a3a3a;
                border-color: #1890ff;
            }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 项目头部信息
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # 项目图标
        try:
            from ...core.icon_manager import get_icon
            icon_label = QLabel()
            icon_label.setPixmap(get_icon("project", 32).pixmap(32, 32))
            header_layout.addWidget(icon_label)
        except:
            header_layout.addSpacing(32)

        # 项目名称和描述
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(project.name)
        name_font = QFont("Arial", 14, QFont.Weight.Bold)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(name_label)

        # 简短描述（如果太长则截断）
        desc_text = project.description
        if len(desc_text) > 50:
            desc_text = desc_text[:47] + "..."
        desc_label = QLabel(desc_text)
        desc_label.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        info_layout.addWidget(desc_label)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 项目统计信息
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(15)

        # 时长
        if project.duration > 0:
            duration_text = self._format_duration(project.duration)
            duration_widget = self._create_stat_item("时长", duration_text, "time")
            stats_layout.addWidget(duration_widget)

        # 文件数量
        if project.file_count > 0:
            files_widget = self._create_stat_item("文件", str(project.file_count), "file")
            stats_layout.addWidget(files_widget)

        # 修改时间
        time_text = project.last_modified.strftime('%m-%d')
        time_widget = self._create_stat_item("更新", time_text, "update")
        stats_layout.addWidget(time_widget)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # 底部操作栏
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)

        action_layout.addStretch()

        # 打开按钮
        open_btn = QPushButton("打开项目")
        open_btn.setFixedSize(80, 28)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        open_btn.clicked.connect(lambda: self.project_opened.emit(project))
        action_layout.addWidget(open_btn)

        layout.addLayout(action_layout)

        # 点击卡片也可以打开项目
        card.mousePressEvent = lambda event: self.project_opened.emit(project)

        return card

    def _create_stat_item(self, label: str, value: str, icon_name: str) -> QWidget:
        """创建统计项"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 图标
        try:
            from ...core.icon_manager import get_icon
            icon_label = QLabel()
            icon_label.setPixmap(get_icon(icon_name, 14).pixmap(14, 14))
            layout.addWidget(icon_label)
        except:
            layout.addSpacing(14)

        # 标签
        label_widget = QLabel(f"{label}: {value}")
        label_widget.setStyleSheet("color: #808080; font-size: 10px;")
        layout.addWidget(label_widget)

        return widget

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    def _on_view_all_projects(self):
        """查看全部项目"""
        try:
            self.logger.info("查看全部项目")
            # 这里可以跳转到项目管理器页面
        except Exception as e:
            self.logger.error(f"查看全部项目失败: {e}")

    def add_project(self, project: ProjectInfo):
        """添加项目到最近列表"""
        try:
            # 检查是否已存在
            for i, existing_project in enumerate(self.recent_projects):
                if existing_project.id == project.id:
                    # 移动到顶部
                    self.recent_projects.pop(i)
                    break

            # 添加到顶部
            self.recent_projects.insert(0, project)

            # 只保留最近10个项目
            self.recent_projects = self.recent_projects[:10]

            # 保存到配置
            self._save_recent_projects()

            # 更新显示
            self._update_projects_display()

        except Exception as e:
            self.logger.error(f"添加项目失败: {e}")

    def _save_recent_projects(self):
        """保存最近项目到配置"""
        try:
            recent_projects_data = []
            for project in self.recent_projects:
                recent_projects_data.append({
                    "id": project.id,
                    "name": project.name,
                    "path": project.path,
                    "description": project.description,
                    "last_modified": project.last_modified.isoformat(),
                    "thumbnail": project.thumbnail,
                    "duration": project.duration,
                    "file_count": project.file_count
                })

            settings = self.config_manager.get_settings()
            settings["recent_projects"] = recent_projects_data
            self.config_manager.update_settings(settings)

        except Exception as e:
            self.logger.error(f"保存最近项目失败: {e}")


class SystemStatusPanel(QWidget):
    """系统状态面板"""

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service(ConfigManager)
        self.error_handler = get_global_error_handler()
        self.ui_error_handler = get_ui_error_handler()

        try:
            self._init_ui()
            self._setup_timer()
        except Exception as e:
            self._handle_component_error(e, "__init__", UIErrorSeverity.CRITICAL)

    def _handle_component_error(self, exception: Exception, operation: str, severity: UIErrorSeverity = UIErrorSeverity.MAJOR):
        """处理组件错误"""
        error_info = ErrorInfo(
            error_type=ErrorType.UI,
            severity=ErrorSeverity.HIGH if severity == UIErrorSeverity.CRITICAL else ErrorSeverity.MEDIUM,
            message=f"SystemStatusPanel {operation} 失败: {str(exception)}",
            exception=exception,
            context=ErrorContext(
                component="SystemStatusPanel",
                operation=operation,
                system_state={
                    "application": str(self.application),
                    "config_manager": str(self.config_manager)
                }
            ),
            recovery_action=RecoveryAction.RETRY,
            user_message="系统状态面板初始化失败，正在尝试恢复..."
        )

        self.error_handler.handle_error(error_info, show_dialog=True, parent=self)

        # 对于关键错误，禁用组件
        if severity == UIErrorSeverity.CRITICAL:
            self.setEnabled(False)
            self.setVisible(False)

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 系统概览
        overview_widget = self._create_system_overview()
        layout.addWidget(overview_widget)

        # 资源监控
        resources_widget = self._create_resources_monitor()
        layout.addWidget(resources_widget)

        # 快速操作
        quick_actions_widget = self._create_quick_actions()
        layout.addWidget(quick_actions_widget)

        layout.addStretch()

    def _create_system_overview(self) -> QWidget:
        """创建系统概览"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("系统概览")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(title_label)

        # 应用状态
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)

        # 状态图标
        try:
            from ...core.icon_manager import get_icon
            status_icon = QLabel()
            status_icon.setPixmap(get_icon("status", 16).pixmap(16, 16))
            status_layout.addWidget(status_icon)
        except:
            status_layout.addSpacing(16)

        self.app_status_label = QLabel("应用程序状态: 就绪")
        self.app_status_label.setStyleSheet("color: #4caf50; font-size: 12px;")
        status_layout.addWidget(self.app_status_label)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # 版本信息
        version_layout = QHBoxLayout()
        version_layout.setContentsMargins(0, 0, 0, 0)

        try:
            from ...core.icon_manager import get_icon
            version_icon = QLabel()
            version_icon.setPixmap(get_icon("version", 16).pixmap(16, 16))
            version_layout.addWidget(version_icon)
        except:
            version_layout.addSpacing(16)

        version_text = f"版本: {self.application.get_config().version}"
        version_label = QLabel(version_text)
        version_label.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        version_layout.addWidget(version_label)
        version_layout.addStretch()

        layout.addLayout(version_layout)

        return widget

    def _create_resources_monitor(self) -> QWidget:
        """创建资源监控"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("资源监控")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(title_label)

        # 资源项
        resources_layout = QGridLayout()
        resources_layout.setSpacing(10)

        # CPU
        cpu_widget = self._create_resource_item("CPU", "计算中...", "#2196f3", "cpu")
        resources_layout.addWidget(cpu_widget, 0, 0)

        # 内存
        memory_widget = self._create_resource_item("内存", "计算中...", "#ff9800", "memory")
        resources_layout.addWidget(memory_widget, 0, 1)

        # 磁盘
        disk_widget = self._create_resource_item("磁盘", "计算中...", "#9c27b0", "disk")
        resources_layout.addWidget(disk_widget, 1, 0)

        layout.addLayout(resources_layout)

        return widget

    def _create_resource_item(self, label: str, value: str, color: str, icon_name: str) -> QWidget:
        """创建资源项"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 图标
        try:
            from ...core.icon_manager import get_icon
            icon_label = QLabel()
            icon_label.setPixmap(get_icon(icon_name, 16).pixmap(16, 16))
            layout.addWidget(icon_label)
        except:
            layout.addSpacing(16)

        # 标签
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        layout.addWidget(label_widget)

        # 值
        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        layout.addWidget(value_widget)

        layout.addStretch()

        return container

    def _create_quick_actions(self) -> QWidget:
        """创建快速操作"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("快速操作")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(title_label)

        # 操作按钮
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        # 清理缓存
        clean_btn = self._create_action_button("清理缓存", self._on_clean_cache, "#ff9800")
        actions_layout.addWidget(clean_btn)

        # 重启应用
        restart_btn = self._create_action_button("重启应用", self._on_restart_app, "#f44336")
        actions_layout.addWidget(restart_btn)

        # 查看日志
        log_btn = self._create_action_button("查看日志", self._on_view_logs, "#4caf50")
        actions_layout.addWidget(log_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        return widget

    def _create_action_button(self, text: str, callback, color: str) -> QPushButton:
        """创建操作按钮"""
        btn = QPushButton(text)
        btn.setFixedSize(70, 25)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {color};
                border: 1px solid {color};
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: white;
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _on_clean_cache(self):
        """清理缓存"""
        try:
            self.logger.info("清理缓存")
            # 实现缓存清理逻辑
        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")

    def _on_restart_app(self):
        """重启应用"""
        try:
            reply = QMessageBox.question(
                self,
                "确认重启",
                "确定要重启应用程序吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.logger.info("重启应用")
                # 实现重启逻辑
        except Exception as e:
            self.logger.error(f"重启应用失败: {e}")

    def _on_view_logs(self):
        """查看日志"""
        try:
            self.logger.info("查看日志")
            # 实现查看日志逻辑
        except Exception as e:
            self.logger.error(f"查看日志失败: {e}")

    def _setup_timer(self):
        """设置定时器"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(2000)  # 每2秒更新一次

    @error_handler_decorator(
        error_type=ErrorType.SYSTEM,
        severity=ErrorSeverity.LOW,
        recovery_action=RecoveryAction.CONTINUE,
        user_message="状态更新失败"
    )
    def _update_status(self):
        """更新状态信息"""
        try:
            # 安全地获取应用程序状态
            def safe_get_state():
                return self.application.get_state()

            app_state = safe_execute(safe_get_state)

            state_text = {
                ApplicationState.INITIALIZING: "初始化中",
                ApplicationState.STARTING: "启动中",
                ApplicationState.READY: "就绪",
                ApplicationState.RUNNING: "运行中",
                ApplicationState.PAUSING: "暂停中",
                ApplicationState.SHUTTING_DOWN: "关闭中",
                ApplicationState.ERROR: "错误"
            }

            state_color = {
                ApplicationState.INITIALIZING: "#ff9800",
                ApplicationState.STARTING: "#2196f3",
                ApplicationState.READY: "#4caf50",
                ApplicationState.RUNNING: "#4caf50",
                ApplicationState.PAUSING: "#ff9800",
                ApplicationState.SHUTTING_DOWN: "#f44336",
                ApplicationState.ERROR: "#f44336"
            }

            # 安全地更新UI状态
            if hasattr(self, 'app_status_label') and self.app_status_label:
                self.app_status_label.setText(f"应用程序状态: {state_text.get(app_state, '未知')}")
                self.app_status_label.setStyleSheet(f"color: {state_color.get(app_state, '#808080')}; font-size: 12px;")

            # 更新系统资源使用情况
            self._update_system_resources()

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.LOW,
                message=f"更新状态失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="SystemStatusPanel",
                    operation="_update_status",
                    system_state={
                        "application": str(self.application),
                        "app_state": app_state if 'app_state' in locals() else None
                    }
                ),
                recovery_action=RecoveryAction.CONTINUE,
                user_message="状态更新失败，将继续运行"
            )

            # 对于状态更新错误，只记录日志不显示对话框
            self.error_handler.handle_error(error_info, show_dialog=False)

    def _update_system_resources(self):
        """更新系统资源使用情况"""
        try:
            import psutil

            # 内存使用
            memory = psutil.virtual_memory()
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            if hasattr(self, 'memory_label') and self.memory_label:
                self.memory_label.setText(f"内存使用: {memory_mb:.1f}MB / {memory.total / 1024 / 1024 / 1024:.1f}GB")

            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)  # 减少等待时间
            if hasattr(self, 'cpu_label') and self.cpu_label:
                self.cpu_label.setText(f"CPU使用率: {cpu_percent:.1f}%")

            # 磁盘空间
            disk = psutil.disk_usage('/')
            if hasattr(self, 'disk_label') and self.disk_label:
                self.disk_label.setText(f"磁盘空间: {disk.free / 1024 / 1024 / 1024:.1f}GB / {disk.total / 1024 / 1024 / 1024:.1f}GB")

        except ImportError:
            # psutil未安装，显示默认消息
            if hasattr(self, 'memory_label') and self.memory_label:
                self.memory_label.setText("内存使用: 监控组件未安装")
            if hasattr(self, 'cpu_label') and self.cpu_label:
                self.cpu_label.setText("CPU使用率: 监控组件未安装")
            if hasattr(self, 'disk_label') and self.disk_label:
                self.disk_label.setText("磁盘空间: 监控组件未安装")
        except Exception as e:
            # 对于资源监控错误，只记录日志不显示对话框
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.LOW,
                message=f"更新系统资源失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="SystemStatusPanel",
                    operation="_update_system_resources",
                    system_state={}
                ),
                recovery_action=RecoveryAction.CONTINUE,
                user_message="系统资源监控失败"
            )
            self.error_handler.handle_error(error_info, show_dialog=False)

            # 设置错误状态显示
            if hasattr(self, 'memory_label') and self.memory_label:
                self.memory_label.setText("内存使用: 监控失败")
            if hasattr(self, 'cpu_label') and self.cpu_label:
                self.cpu_label.setText("CPU使用率: 监控失败")
            if hasattr(self, 'disk_label') and self.disk_label:
                self.disk_label.setText("磁盘空间: 监控失败")


class HomePage(QWidget):
    """CineAIStudio v2.0 首页"""

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service(ConfigManager)
        self.event_bus = application.get_service_by_name("event_bus")
        self.error_handler = get_global_error_handler()
        self.ui_error_handler = get_ui_error_handler()

        # 获取项目管理器
        self.project_manager = application.get_service_by_name("project_manager")
        if not self.project_manager:
            self.project_manager = ProjectManager(self.config_manager)

        try:
            self._init_ui()
            self._setup_connections()
            self._setup_shortcuts()
        except Exception as e:
            self._handle_component_error(e, "__init__", UIErrorSeverity.CRITICAL)

    def _handle_component_error(self, exception: Exception, operation: str, severity: UIErrorSeverity = UIErrorSeverity.MAJOR):
        """处理组件错误"""
        error_info = ErrorInfo(
            error_type=ErrorType.UI,
            severity=ErrorSeverity.CRITICAL if severity == UIErrorSeverity.CRITICAL else ErrorSeverity.HIGH,
            message=f"HomePage {operation} 失败: {str(exception)}",
            exception=exception,
            context=ErrorContext(
                component="HomePage",
                operation=operation,
                system_state={
                    "application": str(self.application),
                    "config_manager": str(self.config_manager),
                    "event_bus": str(self.event_bus)
                }
            ),
            recovery_action=RecoveryAction.CONTACT_SUPPORT,
            user_message="首页初始化失败，请联系技术支持"
        )

        self.error_handler.handle_error(error_info, show_dialog=True)

        # 对于关键错误，禁用整个首页
        if severity == UIErrorSeverity.CRITICAL:
            self.setEnabled(False)
            # 显示错误占位符
            error_layout = QVBoxLayout(self)
            error_label = QLabel("首页加载失败\n请检查系统配置或联系技术支持")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #f44336; font-size: 16px; font-weight: bold;")
            error_layout.addWidget(error_label)

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建主分割器
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(2)

        # 顶部主要区域
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        # 创建顶部分割器
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setChildrenCollapsible(False)
        top_splitter.setHandleWidth(2)

        # 左侧面板 - 快速开始和AI功能
        left_panel = self._create_left_panel()
        top_splitter.addWidget(left_panel)

        # 右侧面板 - 项目和状态
        right_panel = self._create_right_panel()
        top_splitter.addWidget(right_panel)

        # 设置顶部分割器比例（左40%，右60%）
        top_splitter.setSizes([480, 720])
        top_layout.addWidget(top_splitter)

        # 底部项目管理和AI配置区域
        bottom_widget = self._create_bottom_panel()
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(bottom_widget)

        # 设置主分割器比例（上70%，下30%）
        main_splitter.setSizes([700, 300])

        layout.addWidget(main_splitter)

        # 设置样式
        self._setup_styles()

    def _create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 快速开始面板
        self.quick_start_panel = QuickStartPanel(self.application)
        layout.addWidget(self.quick_start_panel)

        return panel

    def _create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建右侧分割器
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setChildrenCollapsible(False)
        right_splitter.setHandleWidth(2)

        # 最近项目面板
        self.recent_projects_panel = RecentProjectsPanel(self.application)
        right_splitter.addWidget(self.recent_projects_panel)

        # 系统状态面板
        self.system_status_panel = SystemStatusPanel(self.application)
        right_splitter.addWidget(self.system_status_panel)

        # 设置右侧分割器比例（上70%，下30%）
        right_splitter.setSizes([400, 200])
        layout.addWidget(right_splitter)

        return panel

    def _create_bottom_panel(self) -> QWidget:
        """创建底部面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Box)
        panel.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-top: 1px solid #404040;
                border-radius: 0px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #b0b0b0;
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid transparent;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #ffffff;
                border-bottom-color: #1890ff;
            }
            QTabBar::tab:hover {
                background-color: #3a3a3a;
                color: #ffffff;
            }
        """)

        # 项目管理器选项卡
        self.project_manager_widget = ProjectManagerWidget(self.application)
        tab_widget.addTab(self.project_manager_widget, "项目管理")

        # AI配置选项卡
        try:
            from app.ui.components.quick_ai_config import QuickAIConfigWidget
            self.ai_config_widget = QuickAIConfigWidget()
            tab_widget.addTab(self.ai_config_widget, "AI配置")
        except ImportError:
            # 如果AI配置组件不存在，创建一个简单的占位符
            placeholder = QLabel("AI配置功能正在开发中...")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #b0b0b0; font-size: 14px;")
            tab_widget.addTab(placeholder, "AI配置")

        layout.addWidget(tab_widget)
        return panel

    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QSplitter::handle {
                background-color: #404040;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
            QSplitter::handle:hover {
                background-color: #1890ff;
            }
        """)

    def _setup_shortcuts(self):
        """设置快捷键"""
        from PyQt6.QtGui import QShortcut
        from PyQt6.QtCore import Qt

        # F5 - 刷新
        refresh_shortcut = QShortcut(Qt.Key.Key_F5, self)
        refresh_shortcut.activated.connect(self.refresh)

        # Ctrl+N - 新建项目
        new_project_shortcut = QShortcut(
            Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_N, self
        )
        new_project_shortcut.activated.connect(
            lambda: self.quick_start_panel._on_create_project()
        )

        # Ctrl+O - 打开项目
        open_project_shortcut = QShortcut(
            Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_O, self
        )
        open_project_shortcut.activated.connect(
            lambda: self.quick_start_panel._on_open_project()
        )

    def _setup_connections(self):
        """设置信号连接"""
        # 快速开始面板信号
        self.quick_start_panel.project_created.connect(self._on_project_created)

        # 最近项目面板信号
        self.recent_projects_panel.project_opened.connect(self._on_project_opened)

        # 项目管理器信号
        self.project_manager_widget.project_created.connect(self._on_project_created)
        self.project_manager_widget.project_opened.connect(self._on_project_opened)
        self.project_manager_widget.project_imported.connect(self._on_project_opened)
        self.project_manager_widget.project_exported.connect(self._on_project_exported)

        # 事件总线订阅
        self.event_bus.subscribe("project.created", self._on_project_created_event)
        self.event_bus.subscribe("project.opened", self._on_project_opened_event)

    def _on_project_created(self, project: ProjectInfo):
        """处理项目创建"""
        self.logger.info(f"项目创建: {project.name}")
        self.recent_projects_panel.add_project(project)

        # 发送事件
        self.event_bus.emit("project.created", project)

    def _on_project_opened(self, project: ProjectInfo):
        """处理项目打开"""
        self.logger.info(f"项目打开: {project.name}")
        self.recent_projects_panel.add_project(project)

        # 发送事件
        self.event_bus.emit("project.opened", project)

    def _on_project_created_event(self, project: ProjectInfo):
        """处理项目创建事件"""
        self.recent_projects_panel.add_project(project)

    def _on_project_opened_event(self, project: ProjectInfo):
        """处理项目打开事件"""
        self.recent_projects_panel.add_project(project)

    def _on_project_exported(self, project: dict):
        """处理项目导出"""
        self.logger.info(f"项目导出: {project.get('name', 'Unknown')}")

    @error_handler_decorator(
        error_type=ErrorType.UI,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.RETRY,
        user_message="刷新首页失败，正在重试..."
    )
    def refresh(self):
        """刷新首页"""
        try:
            # 安全地刷新各个组件
            def safe_refresh_components():
                # 刷新最近项目面板
                if hasattr(self, 'recent_projects_panel') and self.recent_projects_panel:
                    self.recent_projects_panel._refresh_projects()

                # 刷新系统状态面板
                if hasattr(self, 'system_status_panel') and self.system_status_panel:
                    self.system_status_panel._update_status()

                # 刷新项目管理器
                if hasattr(self, 'project_manager_widget') and self.project_manager_widget:
                    self.project_manager_widget.refresh()

                return True

            result = safe_execute(safe_refresh_components)

            if result:
                self.logger.info("首页刷新完成")
            else:
                raise RuntimeError("组件刷新失败")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.UI,
                severity=ErrorSeverity.MEDIUM,
                message=f"刷新首页失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="HomePage",
                    operation="refresh",
                    system_state={
                        "recent_projects_panel": str(getattr(self, 'recent_projects_panel', None)),
                        "system_status_panel": str(getattr(self, 'system_status_panel', None)),
                        "project_manager_widget": str(getattr(self, 'project_manager_widget', None))
                    }
                ),
                recovery_action=RecoveryAction.SHOW_DIALOG,
                user_message="无法刷新首页，请检查各个组件状态"
            )

            self.ui_error_handler.handle_ui_error(
                UIErrorInfo(
                    ui_error_type=UIErrorType.REFRESH_ERROR,
                    severity=UIErrorSeverity.MAJOR,
                    message="首页刷新失败",
                    exception=e,
                    component="HomePage",
                    operation="refresh",
                    user_message="刷新操作失败，部分组件可能无法正常显示"
                ),
                show_dialog=True,
                parent=self
            )

    def get_application(self) -> Application:
        """获取应用程序实例"""
        return self.application

    def get_config(self) -> Any:
        """获取配置"""
        return self.application.get_config()