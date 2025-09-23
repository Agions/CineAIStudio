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
from ...core.event_bus import EventBus


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

        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("快速开始")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 快速操作按钮网格
        button_layout = QGridLayout()
        button_layout.setSpacing(15)

        # 创建项目按钮
        create_project_btn = self._create_action_button(
            "创建新项目",
            "开始一个新的视频编辑项目",
            self._on_create_project
        )
        button_layout.addWidget(create_project_btn, 0, 0)

        # 打开项目按钮
        open_project_btn = self._create_action_button(
            "打开项目",
            "打开已有的视频编辑项目",
            self._on_open_project
        )
        button_layout.addWidget(open_project_btn, 0, 1)

        # 导入媒体按钮
        import_media_btn = self._create_action_button(
            "导入媒体",
            "导入视频、音频或图片文件",
            self._on_import_media
        )
        button_layout.addWidget(import_media_btn, 1, 0)

        # AI工具按钮
        ai_tools_btn = self._create_action_button(
            "AI工具",
            "使用AI功能处理视频",
            self._on_ai_tools
        )
        button_layout.addWidget(ai_tools_btn, 1, 1)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _create_action_button(self, title: str, description: str, callback) -> QWidget:
        """创建操作按钮"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 按钮样式
        button = QPushButton(title)
        button.setFixedSize(160, 80)
        button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #404040;
                border-color: #1890ff;
            }
            QPushButton:pressed {
                background-color: #1890ff;
                border-color: #1890ff;
            }
        """)
        button.clicked.connect(callback)

        # 描述标签
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 12px;
                text-align: center;
            }
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(button)
        layout.addWidget(desc_label)

        return container

    def _on_create_project(self):
        """创建新项目"""
        try:
            from PyQt6.QtWidgets import QFileDialog

            # 选择项目保存位置
            project_dir = QFileDialog.getExistingDirectory(
                self,
                "选择项目保存位置",
                os.path.expanduser("~")
            )

            if project_dir:
                # 创建项目
                project_name = f"项目_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                project_path = os.path.join(project_dir, project_name)

                # 创建项目目录
                os.makedirs(project_path, exist_ok=True)

                # 创建项目信息
                project_info = ProjectInfo(
                    id=f"project_{datetime.now().timestamp()}",
                    name=project_name,
                    path=project_path,
                    description="新建项目",
                    last_modified=datetime.now()
                )

                self.project_created.emit(project_info)
                self.logger.info(f"创建新项目: {project_name}")

        except Exception as e:
            self.logger.error(f"创建项目失败: {e}")

    def _on_open_project(self):
        """打开项目"""
        try:
            from PyQt6.QtWidgets import QFileDialog

            # 选择项目文件
            project_file, _ = QFileDialog.getOpenFileName(
                self,
                "打开项目",
                os.path.expanduser("~"),
                "CineAIStudio项目 (*.cineaiproj);;所有文件 (*)"
            )

            if project_file:
                self.logger.info(f"打开项目: {project_file}")

        except Exception as e:
            self.logger.error(f"打开项目失败: {e}")

    def _on_import_media(self):
        """导入媒体"""
        try:
            from PyQt6.QtWidgets import QFileDialog

            # 选择媒体文件
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "导入媒体文件",
                os.path.expanduser("~"),
                "媒体文件 (*.mp4 *.avi *.mov *.mkv *.mp3 *.wav *.jpg *.png *.bmp);;所有文件 (*)"
            )

            if files:
                self.logger.info(f"导入媒体文件: {len(files)} 个")

        except Exception as e:
            self.logger.error(f"导入媒体失败: {e}")

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

        self.recent_projects: List[ProjectInfo] = []

        self._init_ui()
        self._load_recent_projects()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题和刷新按钮
        header_layout = QHBoxLayout()

        title_label = QLabel("最近项目")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedSize(60, 30)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #404040;
                border-color: #1890ff;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_projects)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # 项目列表
        self.projects_scroll = QScrollArea()
        self.projects_scroll.setWidgetResizable(True)
        self.projects_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.projects_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.projects_widget = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_widget)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(10)

        self.projects_scroll.setWidget(self.projects_widget)
        layout.addWidget(self.projects_scroll)

    def _load_recent_projects(self):
        """加载最近项目"""
        try:
            # 从配置管理器加载最近项目
            settings = self.config_manager.get_settings()
            recent_projects_data = settings.get("recent_projects", [])

            self.recent_projects = []
            for project_data in recent_projects_data:
                if os.path.exists(project_data.get("path", "")):
                    project_info = ProjectInfo(
                        id=project_data["id"],
                        name=project_data["name"],
                        path=project_data["path"],
                        description=project_data.get("description", ""),
                        last_modified=datetime.fromisoformat(project_data["last_modified"]),
                        thumbnail=project_data.get("thumbnail"),
                        duration=project_data.get("duration", 0),
                        file_count=project_data.get("file_count", 0)
                    )
                    self.recent_projects.append(project_info)

            self._update_projects_display()

        except Exception as e:
            self.logger.error(f"加载最近项目失败: {e}")

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
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #1890ff;
            }
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)

        # 项目信息
        info_layout = QVBoxLayout()

        name_label = QLabel(project.name)
        name_font = QFont("Arial", 14, QFont.Weight.Bold)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(name_label)

        desc_label = QLabel(project.description)
        desc_label.setStyleSheet("color: #b0b0b0; font-size: 12px;")
        info_layout.addWidget(desc_label)

        # 项目统计
        stats_label = QLabel(f"时长: {project.duration}s | 文件: {project.file_count} | 更新: {project.last_modified.strftime('%Y-%m-%d')}")
        stats_label.setStyleSheet("color: #808080; font-size: 11px;")
        info_layout.addWidget(stats_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # 打开按钮
        open_btn = QPushButton("打开")
        open_btn.setFixedSize(60, 30)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        open_btn.clicked.connect(lambda: self.project_opened.emit(project))
        layout.addWidget(open_btn)

        return card

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

        self._init_ui()
        self._setup_timer()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("系统状态")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(title_label)

        # 状态信息
        self.status_widget = QWidget()
        status_layout = QGridLayout(self.status_widget)
        status_layout.setSpacing(15)

        # 应用程序状态
        self.app_status_label = QLabel("应用程序状态: 就绪")
        self.app_status_label.setStyleSheet("color: #4caf50; font-size: 12px;")
        status_layout.addWidget(self.app_status_label, 0, 0)

        # 内存使用
        self.memory_label = QLabel("内存使用: 计算中...")
        self.memory_label.setStyleSheet("color: #ff9800; font-size: 12px;")
        status_layout.addWidget(self.memory_label, 0, 1)

        # CPU使用率
        self.cpu_label = QLabel("CPU使用率: 计算中...")
        self.cpu_label.setStyleSheet("color: #2196f3; font-size: 12px;")
        status_layout.addWidget(self.cpu_label, 1, 0)

        # 磁盘空间
        self.disk_label = QLabel("磁盘空间: 计算中...")
        self.disk_label.setStyleSheet("color: #9c27b0; font-size: 12px;")
        status_layout.addWidget(self.disk_label, 1, 1)

        layout.addWidget(self.status_widget)

        # 系统信息
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout(info_group)

        info_text = f"""
        <table style='color: #b0b0b0; font-size: 12px;'>
            <tr><td>版本:</td><td>{self.application.get_config().version}</td></tr>
            <tr><td>Python:</td><td>{sys.version.split()[0]}</td></tr>
            <tr><td>Qt版本:</td><td>{self.application.get_config().qt_version}</td></tr>
            <tr><td>工作目录:</td><td>{os.getcwd()}</td></tr>
        </table>
        """

        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_layout.addWidget(info_label)

        layout.addWidget(info_group)
        layout.addStretch()

    def _setup_timer(self):
        """设置定时器"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(2000)  # 每2秒更新一次

    def _update_status(self):
        """更新状态信息"""
        try:
            # 更新应用程序状态
            app_state = self.application.get_state()
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

            self.app_status_label.setText(f"应用程序状态: {state_text.get(app_state, '未知')}")
            self.app_status_label.setStyleSheet(f"color: {state_color.get(app_state, '#808080')}; font-size: 12px;")

            # 更新系统资源使用情况
            self._update_system_resources()

        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")

    def _update_system_resources(self):
        """更新系统资源使用情况"""
        try:
            import psutil

            # 内存使用
            memory = psutil.virtual_memory()
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"内存使用: {memory_mb:.1f}MB / {memory.total / 1024 / 1024 / 1024:.1f}GB")

            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_label.setText(f"CPU使用率: {cpu_percent:.1f}%")

            # 磁盘空间
            disk = psutil.disk_usage('/')
            self.disk_label.setText(f"磁盘空间: {disk.free / 1024 / 1024 / 1024:.1f}GB / {disk.total / 1024 / 1024 / 1024:.1f}GB")

        except ImportError:
            self.memory_label.setText("内存使用: psutil未安装")
            self.cpu_label.setText("CPU使用率: psutil未安装")
            self.disk_label.setText("磁盘空间: psutil未安装")
        except Exception as e:
            self.logger.error(f"更新系统资源失败: {e}")


class HomePage(QWidget):
    """CineAIStudio v2.0 首页"""

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service(ConfigManager)
        self.event_bus = application.get_service(EventBus)

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # 快速开始面板
        self.quick_start_panel = QuickStartPanel(self.application)
        left_layout.addWidget(self.quick_start_panel)

        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 最近项目面板
        self.recent_projects_panel = RecentProjectsPanel(self.application)
        right_layout.addWidget(self.recent_projects_panel)

        # 系统状态面板
        self.system_status_panel = SystemStatusPanel(self.application)
        right_layout.addWidget(self.system_status_panel)

        # 设置分割器比例
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)

    def _setup_connections(self):
        """设置信号连接"""
        # 快速开始面板信号
        self.quick_start_panel.project_created.connect(self._on_project_created)

        # 最近项目面板信号
        self.recent_projects_panel.project_opened.connect(self._on_project_opened)

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

    def refresh(self):
        """刷新首页"""
        try:
            self.recent_projects_panel._refresh_projects()
            self.system_status_panel._update_status()
            self.logger.info("首页刷新完成")

        except Exception as e:
            self.logger.error(f"刷新首页失败: {e}")

    def get_application(self) -> Application:
        """获取应用程序实例"""
        return self.application

    def get_config(self) -> Any:
        """获取配置"""
        return self.application.get_config()