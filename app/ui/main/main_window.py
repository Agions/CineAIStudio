#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 主窗口 - 设置版本
实现双页面架构：首页 + 设置页面
"""

import os
import sys
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QToolBar, QStatusBar, QMenuBar, QSplitter, QFrame, QLabel,
    QSizePolicy, QApplication, QMessageBox, QPushButton
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, pyqtSignal, QPoint, QRect, QSettings,
    QMimeData, QUrl, QEvent
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QFont, QPalette, QColor, QCursor,
    QAction, QFontDatabase, QCloseEvent, QKeySequence, QShortcut
)


from ...core.config_manager import ConfigManager
from ...core.logger import Logger
from ...core.icon_manager import get_icon_manager, get_icon
from ...core.macOS_theme_manager import get_theme_manager, apply_macos_theme
from ...core.event_bus import EventBus
from ...core.application import Application, ApplicationState, ErrorInfo, ErrorType, ErrorSeverity
from ...utils.error_handler import ErrorHandler
from ...utils.error_handler import handle_exception, show_error_dialog


class PageType(Enum):
    """页面类型"""
    HOME = "home"
    SETTINGS = "settings"
    VIDEO_EDITOR = "video_editor"
    PROJECTS = "projects"
    AI_CHAT = "ai_chat"
    AI_VIDEO_CREATOR = "ai_video_creator"  # AI 视频创作


@dataclass
class WindowConfig:
    """窗口配置"""
    title: str = "CineAIStudio"
    width: int = 1200
    height: int = 800
    min_width: int = 800
    min_height: int = 600
    icon_path: Optional[str] = None
    style: str = "Fusion"


class MainWindow(QMainWindow):
    """CineAIStudio 主窗口 - 设置版本"""

    # 信号定义
    page_changed = pyqtSignal(PageType)           # 页面切换信号
    theme_changed = pyqtSignal(str)              # 主题变更信号
    layout_changed = pyqtSignal(str)             # 布局变更信号
    error_occurred = pyqtSignal(str, str)        # 错误信号
    status_updated = pyqtSignal(str)             # 状态更新信号

    def __init__(self, application: Application):
        super().__init__()

        self.application = application
        self.config = application.get_config()
        self.logger = application.get_service_by_name("logger")
        self.config_manager = application.get_service_by_name("config_manager")
        self.event_bus = application.get_service_by_name("event_bus")
        self.error_handler = application.get_service_by_name("error_handler")

        # 获取图标管理器
        self.icon_manager = application.get_service_by_name("icon_manager")

        # 安全地处理可能为None的服务
        if self.logger is None:
            self.logger = Logger("MainWindow")
        if self.config_manager is None:
            self.config_manager = ConfigManager()
        if self.event_bus is None:
            self.event_bus = EventBus()  # Fallback
        if self.error_handler is None:
            self.error_handler = ErrorHandler(self.logger)

        # 状态管理
        self.current_page = PageType.HOME
        self.is_dark_theme = True
        self.is_fullscreen = False

        # 窗口配置
        self.window_config = WindowConfig()

        # 组件初始化
        self.central_widget: Optional[QWidget] = None
        self.page_stack: Optional[QStackedWidget] = None
        self.status_bar: Optional[QStatusBar] = None

        # 页面组件
        self.home_page: Optional[QWidget] = None
        self.settings_page: Optional[QWidget] = None
        self.video_editor_page: Optional[QWidget] = None

        # 初始化UI
        self._init_ui()
        self._setup_connections()
        self._load_settings()
        self._apply_theme()

        self.logger.info("主窗口初始化完成")

    def _init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle(self.window_config.title)
        self.resize(self.window_config.width, self.window_config.height)
        self.setMinimumSize(self.window_config.min_width, self.window_config.min_height)

        # 设置窗口图标
        try:
            icon_manager = get_icon_manager()
            app_icon = icon_manager.get_app_icon()
            if not app_icon.isNull():
                self.setWindowIcon(app_icon)
        except Exception as e:
            self.logger.warning(f"设置窗口图标失败: {e}")

        # 创建中央控件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 创建主布局：左侧导航 + 右侧内容
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建左侧导航面板
        self.left_panel = QFrame()
        self.left_panel.setObjectName("left_panel")
        self.left_panel.setFixedWidth(200)
        
        # 左侧面板布局
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # 应用标题
        self.app_title = QLabel("CineAIStudio")
        self.app_title.setObjectName("app_title")
        left_layout.addWidget(self.app_title)

        # 导航按钮容器
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(4)

        # 导航按钮 - 安全地获取图标
        try:
            home_icon = get_icon("home", 20)
            settings_icon = get_icon("settings", 20)
            video_icon = get_icon("video", 20)
            ai_chat_icon = get_icon("chat", 20)
            projects_icon = get_icon("projects", 20)
        except Exception:
            # 如果图标获取失败，使用空图标
            home_icon = QIcon()
            settings_icon = QIcon()
            video_icon = QIcon()
            ai_chat_icon = QIcon()
            projects_icon = QIcon()

        # 创建导航按钮
        self.home_btn = QPushButton(home_icon, "首页")
        self.projects_btn = QPushButton(projects_icon, "项目")
        self.editor_btn = QPushButton(video_icon, "视频编辑器")
        self.ai_video_btn = QPushButton(video_icon, "🎬 AI创作")  # AI 视频创作
        self.ai_chat_btn = QPushButton(ai_chat_icon, "AI聊天")
        self.settings_btn = QPushButton(settings_icon, "设置")

        # 设置按钮通用样式和属性
        self.nav_buttons = [self.home_btn, self.projects_btn, self.editor_btn, self.ai_video_btn, self.ai_chat_btn, self.settings_btn]
        for btn in self.nav_buttons:
            btn.setObjectName("nav_button")
            btn.setCheckable(True)
            btn.setIconSize(QSize(20, 20))
            btn.setContentsMargins(8, 4, 8, 4)

        # 连接按钮信号
        self.home_btn.clicked.connect(lambda: self.switch_to_page(PageType.HOME))
        self.projects_btn.clicked.connect(lambda: self.switch_to_page(PageType.PROJECTS))
        self.editor_btn.clicked.connect(lambda: self.switch_to_page(PageType.VIDEO_EDITOR))
        self.ai_video_btn.clicked.connect(lambda: self.switch_to_page(PageType.AI_VIDEO_CREATOR))
        self.ai_chat_btn.clicked.connect(lambda: self.switch_to_page(PageType.AI_CHAT))
        self.settings_btn.clicked.connect(lambda: self.switch_to_page(PageType.SETTINGS))

        # 添加分隔线
        from ..common.widgets.separator import HSeparator
        
        # 添加按钮到导航布局，分组排列
        # 主要功能
        nav_layout.addWidget(QLabel("主要功能"))
        nav_layout.addWidget(self.home_btn)
        nav_layout.addWidget(self.projects_btn)
        nav_layout.addWidget(self.editor_btn)
        
        # 添加分隔线
        nav_layout.addWidget(HSeparator())
        
        # AI功能
        nav_layout.addWidget(QLabel("AI功能"))
        nav_layout.addWidget(self.ai_video_btn)  # AI 视频创作
        nav_layout.addWidget(self.ai_chat_btn)
        
        # 添加分隔线
        nav_layout.addWidget(HSeparator())
        
        # 设置
        nav_layout.addWidget(self.settings_btn)
        
        nav_layout.addStretch()

        left_layout.addWidget(nav_container)

        # 右侧主内容区域
        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 创建页面标题栏
        self.page_header = QWidget()
        self.page_header.setObjectName("page_header")
        self.page_header.setMinimumHeight(56)
        header_layout = QHBoxLayout(self.page_header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(16)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 页面标题
        self.page_title = QLabel("首页")
        self.page_title.setObjectName("page_title")
        page_font = QFont()
        page_font.setBold(True)
        page_font.setPointSize(18)
        self.page_title.setFont(page_font)
        header_layout.addWidget(self.page_title)
        
        # 右侧操作按钮区域
        header_actions = QWidget()
        actions_layout = QHBoxLayout(header_actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        
        # 创建常用操作按钮
        self.new_project_btn = QPushButton(get_icon("new", 16), "新建项目")
        self.new_project_btn.setObjectName("primary_button")
        self.new_project_btn.setFixedHeight(32)
        self.new_project_btn.hide()  # 默认隐藏，根据页面显示
        
        self.import_btn = QPushButton(get_icon("import", 16), "导入")
        self.import_btn.setObjectName("secondary_button")
        self.import_btn.setFixedHeight(32)
        self.import_btn.hide()  # 默认隐藏，根据页面显示
        
        self.export_btn = QPushButton(get_icon("export", 16), "导出")
        self.export_btn.setObjectName("secondary_button")
        self.export_btn.setFixedHeight(32)
        self.export_btn.hide()  # 默认隐藏，根据页面显示
        
        # 添加按钮到布局
        actions_layout.addWidget(self.new_project_btn)
        actions_layout.addWidget(self.import_btn)
        actions_layout.addWidget(self.export_btn)
        
        header_layout.addStretch()
        header_layout.addWidget(header_actions)
        
        right_layout.addWidget(self.page_header)

        # 添加分隔线
        header_separator = QFrame()
        header_separator.setFrameShape(QFrame.Shape.HLine)
        header_separator.setFrameShadow(QFrame.Shadow.Sunken)
        header_separator.setObjectName("header_separator")
        right_layout.addWidget(header_separator)

        # 创建页面堆栈
        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("page_stack")
        right_layout.addWidget(self.page_stack, 1)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 添加状态栏组件
        # 左侧：应用状态
        self.app_status = QLabel("就绪")
        self.app_status.setObjectName("status_app_status")
        self.status_bar.addWidget(self.app_status)
        
        # 分隔线
        self.status_bar.addPermanentWidget(QLabel(" | "))
        
        # 右侧：AI服务状态
        self.ai_status = QLabel("AI: 可用")
        self.ai_status.setObjectName("status_ai_status")
        self.status_bar.addPermanentWidget(self.ai_status)
        
        # 分隔线
        self.status_bar.addPermanentWidget(QLabel(" | "))
        
        # 右侧：当前时间
        self.current_time = QLabel()
        self.current_time.setObjectName("status_time")
        self.status_bar.addPermanentWidget(self.current_time)
        
        # 启动时间更新定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_current_time)
        self.time_timer.start(1000)  # 每秒更新一次
        self._update_current_time()

        # 将左侧面板和右侧内容添加到主布局
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(right_content, 1)

        # 初始化页面
        self._init_pages()

        # 设置默认页面
        self.switch_to_page(PageType.HOME)

        # 应用 macOS 设计系统
        self._apply_theme()

    def _init_pages(self):
        """初始化页面，采用异步方式加载"""
        try:
            # 页面加载状态管理
            self.pages_loading_status = {
                "home": False,
                "projects": False,
                "video_editor": False,
                "ai_video_creator": False,
                "ai_chat": False,
                "settings": False
            }
            
            # 先加载首页，保证主窗口能快速显示
            from .pages.home_page import HomePage
            self.logger.info("开始加载首页...")
            self.home_page = HomePage(self.application)
            self.page_stack.addWidget(self.home_page)
            self.pages_loading_status["home"] = True
            self.logger.info("首页初始化完成")
            
            # 更新状态栏
            self.show_status_message("正在加载其他页面...")
            
            # 使用QTimer异步加载其他页面，避免阻塞主线程
            from PyQt6.QtCore import QTimer
            
            # 延迟加载其他页面，给予主窗口更多初始化时间
            QTimer.singleShot(500, self._load_remaining_pages)
            
        except Exception as e:
            self.logger.error(f"首页初始化失败: {e}")
            if self.error_handler:
                error_info = ErrorInfo(
                    error_type=ErrorType.UI,
                    severity=ErrorSeverity.HIGH,
                    message=f"首页初始化失败: {e}",
                    exception=e
                )
                self.error_handler.handle_error(error_info)
            else:
                self.logger.error(f"错误处理器未初始化: {e}")
    
    def _load_remaining_pages(self):
        """异步加载剩余页面"""
        try:
            # 延迟导入以避免循环依赖
            self.logger.info("开始异步加载剩余页面...")
            
            # 页面加载顺序：项目页面 → 视频编辑器页面 → AI视频创作页面 → AI聊天页面 → 设置页面
            pages_to_load = [
                {"id": "projects", "name": "项目页面", "class": "ProjectsPage", "attribute": "projects_page"},
                {"id": "video_editor", "name": "视频编辑器页面", "class": "VideoEditorPage", "attribute": "video_editor_page"},
                {"id": "ai_video_creator", "name": "AI视频创作页面", "class": "AIVideoCreatorPage", "attribute": "ai_video_creator_page"},
                {"id": "ai_chat", "name": "AI聊天页面", "class": "AIChatPage", "attribute": "ai_chat_page"},
                {"id": "settings", "name": "设置页面", "class": "SettingsPage", "attribute": "settings_page"}
            ]
            
            for page_info in pages_to_load:
                try:
                    page_id = page_info["id"]
                    page_name = page_info["name"]
                    page_class = page_info["class"]
                    attribute_name = page_info["attribute"]
                    
                    self.logger.info(f"正在加载{page_name}...")
                    self.show_status_message(f"正在加载{page_name}...")
                    
                    # 动态导入页面类
                    if page_class == "ProjectsPage":
                        from .pages.projects_page import ProjectsPage as PageClass
                    elif page_class == "VideoEditorPage":
                        from .pages.video_editor_page import VideoEditorPage as PageClass
                    elif page_class == "AIVideoCreatorPage":
                        from .pages.ai_video_creator_page import AIVideoCreatorPage as PageClass
                    elif page_class == "AIChatPage":
                        from .pages.ai_chat_page import AIChatPage as PageClass
                    elif page_class == "SettingsPage":
                        from .pages.settings_page import SettingsPage as PageClass
                    else:
                        raise ImportError(f"未知的页面类: {page_class}")
                    
                    # 创建页面实例
                    page_instance = PageClass(self.application)
                    self.page_stack.addWidget(page_instance)
                    
                    # 保存页面实例到属性
                    setattr(self, attribute_name, page_instance)
                    
                    # 更新加载状态
                    self.pages_loading_status[page_id] = True
                    
                    self.logger.info(f"{page_name}初始化完成")
                    self.show_status_message(f"{page_name}加载完成")
                    
                except Exception as e:
                    # 确保page_name和page_id有默认值
                    error_page_name = page_name if 'page_name' in locals() else '未知页面'
                    error_page_id = page_id if 'page_id' in locals() else 'unknown'
                    self.logger.error(f"加载{error_page_name}失败: {e}")
                    self.pages_loading_status[error_page_id] = False
                    
                    # 单个页面加载失败不影响其他页面
                    if self.error_handler:
                        from PyQt6.QtWidgets import QApplication
                        import time
                        error_info = ErrorInfo(
                            error_type=ErrorType.UI,
                            severity=ErrorSeverity.LOW,
                            message=f"加载{error_page_name}失败: {e}",
                            exception=e,
                            timestamp=time.time()
                        )
                        self.error_handler.handle_error(error_info)
            
            # 检查所有页面加载状态
            all_pages_loaded = all(self.pages_loading_status.values())
            if all_pages_loaded:
                self.logger.info("所有页面初始化完成")
                self.show_status_message("所有页面加载完成", 3000)
            else:
                # 收集加载失败的页面
                failed_pages = []
                for page_info in pages_to_load:
                    page_id = page_info["id"]
                    page_name = page_info["name"]
                    if not self.pages_loading_status.get(page_id, False):
                        failed_pages.append(page_name)
                
                if failed_pages:
                    self.logger.warning(f"部分页面加载失败: {failed_pages}")
                    self.show_status_message(f"部分页面加载失败: {', '.join(failed_pages)}", 5000)
                else:
                    self.logger.info("所有页面初始化完成")
                    self.show_status_message("所有页面加载完成", 3000)
            
        except Exception as e:
            self.logger.error(f"异步加载页面失败: {e}")
            if self.error_handler:
                error_info = ErrorInfo(
                    error_type=ErrorType.UI,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"异步加载页面失败: {e}",
                    exception=e
                )
                self.error_handler.handle_error(error_info)
            else:
                self.logger.error(f"错误处理器未初始化: {e}")

    def _setup_connections(self):
        """设置信号连接"""
        # 应用程序状态变化
        self.application.state_changed.connect(self._on_application_state_changed)

        # 错误处理
        self.application.error_occurred.connect(self._on_application_error)

        # 事件总线订阅
        self.event_bus.subscribe("theme.changed", self._on_theme_changed)
        self.event_bus.subscribe("layout.changed", self._on_layout_changed)

    def _load_settings(self):
        """加载设置，添加验证和默认值处理"""
        try:
            # 加载窗口设置
            settings = QSettings("CineAIStudio", "MainWindow")
            settings.setFallbacksEnabled(True)

            # 恢复窗口位置和大小
            geometry = settings.value("geometry")
            if geometry:
                try:
                    self.restoreGeometry(geometry)
                except Exception as e:
                    self.logger.warning(f"恢复窗口几何形状失败: {e}")
                    # 使用默认尺寸
                    self.resize(self.window_config.width, self.window_config.height)

            # 恢复窗口状态
            state = settings.value("windowState")
            if state:
                try:
                    self.restoreState(state)
                except Exception as e:
                    self.logger.warning(f"恢复窗口状态失败: {e}")

            # 加载主题设置
            theme = settings.value("theme", "dark")
            self.is_dark_theme = theme == "dark"
            
            # 加载窗口尺寸
            width = settings.value("width", self.window_config.width)
            height = settings.value("height", self.window_config.height)
            try:
                self.resize(int(width), int(height))
            except (TypeError, ValueError):
                self.logger.warning("恢复窗口尺寸失败，使用默认尺寸")
                self.resize(self.window_config.width, self.window_config.height)

            self.logger.info("窗口设置加载完成")

        except Exception as e:
            self.logger.warning(f"加载窗口设置失败: {e}")
            # 使用默认设置
            self._load_default_settings()
            
    def _load_default_settings(self):
        """加载默认设置"""
        self.logger.info("加载默认设置")
        self.is_dark_theme = True
        self.resize(self.window_config.width, self.window_config.height)

    def _save_settings(self):
        """保存设置，添加验证和异常处理"""
        try:
            settings = QSettings("CineAIStudio", "MainWindow")
            settings.setFallbacksEnabled(True)

            # 保存窗口位置和大小
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            
            # 保存当前尺寸（用于快速恢复）
            settings.setValue("width", self.width())
            settings.setValue("height", self.height())

            # 保存主题设置
            theme = "dark" if self.is_dark_theme else "light"
            settings.setValue("theme", theme)
            
            # 保存最近使用的页面
            settings.setValue("last_page", self.current_page.value)
            
            # 同步设置到磁盘
            settings.sync()

            self.logger.info("窗口设置保存完成")

        except Exception as e:
            self.logger.warning(f"保存窗口设置失败: {e}")

    def _apply_style(self):
        """应用现代样式表"""
        try:
            # 1. 设置应用程序基本样式
            QApplication.setStyle("Fusion")
            
            # 2. 加载 QSS 文件
            style_path = os.path.join(os.path.dirname(__file__), "../theme/modern.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    qss = f.read()
                    # 可以在这里做一些动态替换，比如基于配置的颜色
                    self.setStyleSheet(qss)
                self.logger.info(f"已加载样式表: {style_path}")
            else:
                self.logger.warning(f"样式表文件未找到: {style_path}")
                
        except Exception as e:
            self.logger.error(f"应用样式失败: {e}")
            
    def _apply_theme(self):
        """应用主题设置"""
        # 调用 _apply_style 加载 QSS
        self._apply_style()
        # 发送信号通知子组件更新
        theme_name = "dark" if self.is_dark_theme else "light"
        self.theme_changed.emit(theme_name)

    def switch_to_page(self, page_type: PageType):
        """切换到指定页面"""
        try:
            # 检查页面是否存在
            target_page = None
            
            # 安全地检查页面属性是否存在
            if page_type == PageType.HOME and hasattr(self, 'home_page') and self.home_page:
                target_page = self.home_page
            elif page_type == PageType.PROJECTS and hasattr(self, 'projects_page') and self.projects_page:
                target_page = self.projects_page
            elif page_type == PageType.VIDEO_EDITOR and hasattr(self, 'video_editor_page') and self.video_editor_page:
                target_page = self.video_editor_page
            elif page_type == PageType.AI_VIDEO_CREATOR and hasattr(self, 'ai_video_creator_page') and self.ai_video_creator_page:
                target_page = self.ai_video_creator_page
            elif page_type == PageType.AI_CHAT and hasattr(self, 'ai_chat_page') and self.ai_chat_page:
                target_page = self.ai_chat_page
            elif page_type == PageType.SETTINGS and hasattr(self, 'settings_page') and self.settings_page:
                target_page = self.settings_page
            else:
                self.logger.warning(f"页面不存在或未初始化: {page_type}")
                return
                
            # 如果目标页面仍为None，尝试动态创建页面
            if not target_page:
                self.logger.info(f"页面 {page_type} 未初始化，尝试动态创建...")
                
                # 根据页面类型动态创建页面
                if page_type == PageType.PROJECTS:
                    from .pages.projects_page import ProjectsPage
                    target_page = ProjectsPage(self.application)
                    self.projects_page = target_page
                    self.page_stack.addWidget(target_page)
                elif page_type == PageType.AI_VIDEO_CREATOR:
                    from .pages.ai_video_creator_page import AIVideoCreatorPage
                    target_page = AIVideoCreatorPage(self.application)
                    self.ai_video_creator_page = target_page
                    self.page_stack.addWidget(target_page)
                elif page_type == PageType.AI_CHAT:
                    from .pages.ai_chat_page import AIChatPage
                    target_page = AIChatPage(self.application)
                    self.ai_chat_page = target_page
                    self.page_stack.addWidget(target_page)
                
                if target_page:
                    self.logger.info(f"成功动态创建页面: {page_type}")
                else:
                    self.logger.error(f"无法动态创建页面: {page_type}")
                    return

            # 获取当前页面和目标页面索引
            current_page_widget = self.page_stack.currentWidget()
            current_index = self.page_stack.currentIndex()
            target_index = self.page_stack.indexOf(target_page)
            
            # 激活目标页面（加载内容）
            if hasattr(target_page, 'activate'):
                target_page.activate()
            
            # 使用更丰富的页面切换动画
            from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
            
            animation_group = QParallelAnimationGroup()
            
            # 淡出当前页面（如果存在）
            if current_page_widget and current_page_widget != target_page:
                fade_out = QPropertyAnimation(current_page_widget, b"windowOpacity")
                fade_out.setDuration(200)
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.setEasingCurve(QEasingCurve.Type.InOutCubic)
                animation_group.addAnimation(fade_out)
            
            # 设置目标页面初始透明度
            target_page.setWindowOpacity(0.0)
            
            # 切换到目标页面
            self.page_stack.setCurrentWidget(target_page)
            
            # 淡入目标页面
            fade_in = QPropertyAnimation(target_page, b"windowOpacity")
            fade_in.setDuration(300)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.Type.InOutCubic)
            animation_group.addAnimation(fade_in)
            
            # 启动动画组
            animation_group.start()

            self.current_page = page_type
            self.page_changed.emit(page_type)

            # 更新页面标题
            page_names = {
                PageType.HOME: "首页",
                PageType.PROJECTS: "项目",
                PageType.VIDEO_EDITOR: "视频编辑器",
                PageType.AI_VIDEO_CREATOR: "AI 视频创作",
                PageType.AI_CHAT: "AI聊天",
                PageType.SETTINGS: "设置"
            }
            page_name = page_names.get(page_type, "未知")
            self.page_title.setText(page_name)

            # 更新导航按钮状态
            self._update_navigation_buttons()

            # 更新操作按钮显示
            self._update_page_actions(page_type)

            # 更新状态栏
            self.status_updated.emit(f"当前页面: {page_name}")

            self.logger.info(f"切换到页面: {page_type.value}")

        except Exception as e:
            self.logger.error(f"切换页面失败: {e}")
            if self.error_handler:
                # 创建一个简单的ErrorInfo对象
                class ErrorInfo:
                    def __init__(self, error_type, message):
                        self.error_type = error_type
                        self.message = message
                        self.exception = e
                self.error_handler.handle_error(ErrorInfo("UI", f"切换页面失败: {e}"))
            # 确保页面切换成功，即使动画失败
            self.logger.warning("页面切换动画失败，已跳过动画")

    def _update_navigation_buttons(self):
        """更新导航按钮状态"""
        # 重置所有按钮状态
        for btn in self.nav_buttons:
            btn.setChecked(False)

        # 高亮当前页面按钮
        if self.current_page == PageType.HOME:
            self.home_btn.setChecked(True)
        elif self.current_page == PageType.PROJECTS:
            self.projects_btn.setChecked(True)
        elif self.current_page == PageType.VIDEO_EDITOR:
            self.editor_btn.setChecked(True)
        elif self.current_page == PageType.AI_VIDEO_CREATOR:
            self.ai_video_btn.setChecked(True)
        elif self.current_page == PageType.AI_CHAT:
            self.ai_chat_btn.setChecked(True)
        elif self.current_page == PageType.SETTINGS:
            self.settings_btn.setChecked(True)

    def _update_page_actions(self, page_type: PageType):
        """根据页面类型更新操作按钮显示"""
        # 隐藏所有操作按钮
        self.new_project_btn.hide()
        self.import_btn.hide()
        self.export_btn.hide()
        
        # 根据页面类型显示相应的按钮
        if page_type == PageType.HOME:
            self.new_project_btn.show()
        elif page_type == PageType.PROJECTS:
            self.new_project_btn.show()
            self.import_btn.show()
        elif page_type == PageType.VIDEO_EDITOR:
            self.export_btn.show()
            self.import_btn.show()

    def _on_theme_changed(self, theme_name: str):
        """处理主题变更事件"""
        self.is_dark_theme = theme_name == "dark"
        self._apply_theme()
        self._apply_style()
    
    def _update_current_time(self):
        """更新当前时间"""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.current_time.setText(current_time)
        except KeyboardInterrupt:
            # 捕获KeyboardInterrupt异常，避免程序崩溃
            pass
        except Exception as e:
            # 捕获其他异常，记录日志
            self.logger.error(f"更新时间失败: {e}")

    def _on_layout_changed(self, layout_name: str):
        """处理布局变更事件"""
        self.layout_changed.emit(layout_name)
        self.logger.info(f"布局变更为: {layout_name}")

    def _on_application_state_changed(self, state: ApplicationState):
        """处理应用程序状态变化"""
        status_messages = {
            ApplicationState.INITIALIZING: "正在初始化...",
            ApplicationState.STARTING: "正在启动...",
            ApplicationState.READY: "就绪",
            ApplicationState.RUNNING: "运行中",
            ApplicationState.PAUSED: "已暂停",
            ApplicationState.SHUTTING_DOWN: "正在关闭...",
            ApplicationState.ERROR: "错误"
        }

        message = status_messages.get(state, "未知状态")
        self.status_updated.emit(f"应用程序状态: {message}")

    def _on_application_error(self, error_type: str, error_message: str):
        """处理应用程序错误"""
        self.error_occurred.emit(error_type, error_message)

        # 显示错误对话框
        QMessageBox.critical(
            self,
            "错误",
            f"{error_type}: {error_message}",
            QMessageBox.StandardButton.Ok
        )

    def toggle_theme(self):
        """切换主题"""
        self.is_dark_theme = not self.is_dark_theme
        self._apply_theme()
        self._apply_style()

    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.is_fullscreen:
            self.showNormal()
        else:
            self.showFullScreen()
        self.is_fullscreen = not self.is_fullscreen

    def refresh_ui(self):
        """刷新用户界面"""
        try:
            # 刷新当前页面
            if self.current_page == PageType.HOME and self.home_page:
                if hasattr(self.home_page, 'refresh'):
                    self.home_page.refresh()
            elif self.current_page == PageType.SETTINGS and self.settings_page:
                if hasattr(self.settings_page, 'refresh'):
                    self.settings_page.refresh()

            # 刷新主题
            self._apply_theme()
            self._apply_style()

            self.logger.info("用户界面刷新完成")

        except Exception as e:
            self.logger.error(f"刷新用户界面失败: {e}")

    def closeEvent(self, event: QCloseEvent):
        """处理窗口关闭事件"""
        try:
            # 保存设置
            self._save_settings()

            # 询问确认
            reply = QMessageBox.question(
                self,
                "确认退出",
                "确定要退出 CineAIStudio 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 通知应用程序关闭
                self.application.shutdown()
                event.accept()
            else:
                event.ignore()

        except Exception as e:
            self.logger.error(f"处理关闭事件失败: {e}")
            event.accept()

    def keyPressEvent(self, event):
        """处理键盘事件"""
        try:
            # Ctrl+Q: 退出
            if event.key() == Qt.Key.Key_Q and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.close()
            # F11: 全屏切换
            elif event.key() == Qt.Key.Key_F11:
                self.toggle_fullscreen()
            # Ctrl+T: 主题切换
            elif event.key() == Qt.Key.Key_T and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.toggle_theme()
            # F5: 刷新
            elif event.key() == Qt.Key.Key_F5:
                self.refresh_ui()
            else:
                super().keyPressEvent(event)

        except Exception as e:
            self.logger.error(f"处理键盘事件失败: {e}")
            super().keyPressEvent(event)

    def get_current_page(self) -> PageType:
        """获取当前页面类型"""
        return self.current_page

    def get_application(self) -> Application:
        """获取应用程序实例"""
        return self.application

    def get_config(self) -> Any:
        """获取配置"""
        return self.config

    def show_status_message(self, message: str, timeout: int = 3000):
        """显示状态消息"""
        if self.status_bar:
            self.status_bar.showMessage(message, timeout)

    def show_error_message(self, title: str, message: str):
        """显示错误消息"""
        QMessageBox.critical(self, title, message)

    def show_info_message(self, title: str, message: str):
        """显示信息消息"""
        QMessageBox.information(self, title, message)

    def show_warning_message(self, title: str, message: str):
        """显示警告消息"""
        QMessageBox.warning(self, title, message)