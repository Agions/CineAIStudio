#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 主窗口 - 设置版本
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
    QSizePolicy, QApplication, QMessageBox, QPushButton, QDialog
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
from ...core.event_system import EventBus
from ...core.application import Application, ApplicationState, ErrorInfo, ErrorType, ErrorSeverity
from ...utils.error_handler import ErrorHandler
from ...utils.error_handler import handle_exception, show_error_dialog
from ..components.enhanced_interactions import (
    EnhancedButton, LoadingIndicator, SmoothStackedWidget,
    ToastNotification, ProgressOverlay, InteractiveGuide
)
from ..components.help_system import HelpSystem


class PageType(Enum):
    """页面类型"""
    HOME = "home"
    SETTINGS = "settings"
    VIDEO_EDITOR = "video_editor"
    EXPORT = "export"


@dataclass
class WindowConfig:
    """窗口配置"""
    title: str = "CineAIStudio v2.0"
    width: int = 1200
    height: int = 800
    min_width: int = 800
    min_height: int = 600
    icon_path: Optional[str] = None
    style: str = "Fusion"


class MainWindow(QMainWindow):
    """CineAIStudio v2.0 主窗口 - 设置版本"""

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
        # 注册媒体服务
        from ...services.media_service import MediaService
        self.media_service = MediaService(self.logger)
        self.application.register_service("media_service", self.media_service)
        self.media_service.media_imported.connect(self._on_media_imported)

        # 组件初始化
        self.central_widget: Optional[QWidget] = None
        self.page_stack: Optional[SmoothStackedWidget] = None
        self.status_bar: Optional[QStatusBar] = None

        # 页面组件
        self.home_page: Optional[QWidget] = None
        self.settings_page: Optional[QWidget] = None
        self.video_editor_page: Optional[QWidget] = None
        self.export_page: Optional[QWidget] = None

        # 增强交互组件
        self.loading_indicator: Optional[LoadingIndicator] = None
        self.toast_notification: Optional[ToastNotification] = None
        self.progress_overlay: Optional[ProgressOverlay] = None
        self.interactive_guide: Optional[InteractiveGuide] = None
        self.help_system: Optional[HelpSystem] = None

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

        # 创建主布局
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建导航栏
        navigation_layout = QHBoxLayout()
        navigation_layout.setContentsMargins(10, 10, 10, 10)

        # 导航按钮 - 安全地获取图标
        try:
            home_icon = get_icon("home", 24)
            settings_icon = get_icon("settings", 24)
            video_icon = get_icon("video", 24)
            export_icon = get_icon("export", 24)
        except Exception:
            # 如果图标获取失败，使用空图标
            home_icon = QIcon()
            settings_icon = QIcon()
            video_icon = QIcon()
            export_icon = QIcon()

        self.home_btn = EnhancedButton(home_icon, "首页")
        self.settings_btn = EnhancedButton(settings_icon, "设置")
        self.editor_btn = EnhancedButton(video_icon, "视频编辑器")
        self.export_btn = EnhancedButton(export_icon, "视频导出")

        # 帮助按钮
        try:
            help_icon = get_icon("help", 24)
        except Exception:
            help_icon = QIcon()
        self.help_btn = EnhancedButton(help_icon, "帮助")

        self.home_btn.setFixedSize(120, 40)
        self.settings_btn.setFixedSize(120, 40)
        self.editor_btn.setFixedSize(140, 40)
        self.export_btn.setFixedSize(120, 40)
        self.help_btn.setFixedSize(120, 40)

        self.home_btn.clicked.connect(lambda: self.switch_to_page(PageType.HOME))
        self.settings_btn.clicked.connect(lambda: self.switch_to_page(PageType.SETTINGS))
        self.editor_btn.clicked.connect(lambda: self.switch_to_page(PageType.VIDEO_EDITOR))
        self.export_btn.clicked.connect(lambda: self.switch_to_page(PageType.EXPORT))
        self.help_btn.clicked.connect(self._show_help)

        navigation_layout.addWidget(self.home_btn)
        navigation_layout.addWidget(self.settings_btn)
        navigation_layout.addWidget(self.editor_btn)
        navigation_layout.addWidget(self.export_btn)
        navigation_layout.addWidget(self.help_btn)
        navigation_layout.addStretch()

        main_layout.addLayout(navigation_layout)

        # 创建页面堆栈 - 使用平滑切换
        self.page_stack = SmoothStackedWidget()
        main_layout.addWidget(self.page_stack, 1)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        # 添加媒体导入按钮到工具栏
        self._create_toolbar()

        # 创建工具栏
        self._create_toolbar()
        # 创建菜单栏
        self._create_menu_bar()

        # 初始化页面
        self._init_pages()

        # 设置默认页面
        self.switch_to_page(PageType.HOME)

        # 创建增强交互组件
        self._create_enhanced_components()

        # 应用样式
        self._apply_style()

    def _init_pages(self):
        """初始化页面"""
        try:
            # 延迟导入以避免循环依赖
            from .pages.home_page import HomePage
            from .pages.settings_page import SettingsPage

            # 创建首页
            self.home_page = HomePage(self.application)
            self.page_stack.addWidget(self.home_page)

            # 创建设置页面
            self.settings_page = SettingsPage(self.application)
            self.page_stack.addWidget(self.settings_page)

            # 创建视频编辑器页面
            from .pages.video_editor_page import VideoEditorPage
            self.video_editor_page = VideoEditorPage(self.application)
            self.page_stack.addWidget(self.video_editor_page)

            # 创建导出页面
            from .pages.export_page import ExportPage
            self.export_page = ExportPage(self.application)
            self.page_stack.addWidget(self.export_page)

            self.logger.info("页面初始化完成")

        except Exception as e:
            self.logger.error(f"页面初始化失败: {e}")
            if self.error_handler:
                error_info = ErrorInfo(
                    error_type=ErrorType.UI,
                    severity=ErrorSeverity.HIGH,
                    message=f"页面初始化失败: {e}",
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
        """加载设置"""
        try:
            # 加载窗口设置
            settings = QSettings("CineAIStudio", "MainWindow")

            # 恢复窗口位置和大小
            geometry = settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)

            # 恢复窗口状态
            state = settings.value("windowState")
            if state:
                self.restoreState(state)

            # 加载主题设置
            theme = settings.value("theme", "dark")
            self.is_dark_theme = theme == "dark"

            self.logger.info("窗口设置加载完成")

        except Exception as e:
            self.logger.warning(f"加载窗口设置失败: {e}")

    def _save_settings(self):
        """保存设置"""
        try:
            settings = QSettings("CineAIStudio", "MainWindow")

            # 保存窗口位置和大小
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())

            # 保存主题设置
            theme = "dark" if self.is_dark_theme else "light"
            settings.setValue("theme", theme)

            self.logger.info("窗口设置保存完成")

        except Exception as e:
            self.logger.warning(f"保存窗口设置失败: {e}")

    def _apply_theme(self):
        """应用主题"""
        try:
            # 应用主题样式
            if self.is_dark_theme:
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #1a1a1a;
                        color: #ffffff;
                    }
                    QPushButton {
                        background-color: #2d2d2d;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #404040;
                    }
                    QPushButton:pressed {
                        background-color: #1890ff;
                    }
                    QLabel {
                        color: #ffffff;
                    }
                    QStatusBar {
                        background-color: #2d2d2d;
                        color: #ffffff;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #ffffff;
                        color: #000000;
                    }
                    QPushButton {
                        background-color: #f0f0f0;
                        color: #000000;
                        border: 1px solid #d0d0d0;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                    QPushButton:pressed {
                        background-color: #1890ff;
                        color: white;
                    }
                    QLabel {
                        color: #000000;
                    }
                    QStatusBar {
                        background-color: #f0f0f0;
                        color: #000000;
                    }
                """)

            # 更新图标主题
            from ...core.icon_manager import set_icon_theme
            set_icon_theme("dark" if self.is_dark_theme else "light")

            self.theme_changed.emit("dark" if self.is_dark_theme else "light")

        except Exception as e:
            self.logger.error(f"应用主题失败: {e}")

    def _apply_style(self):
        """应用样式表"""
        try:
            # 设置应用程序样式
            QApplication.setStyle(self.window_config.style)

        except Exception as e:
            self.logger.error(f"应用样式失败: {e}")

    def switch_to_page(self, page_type: PageType):
        """切换到指定页面"""
        try:
            # 检查页面是否存在
            if page_type == PageType.HOME and self.home_page:
                self.page_stack.setCurrentWidget(self.home_page)
            elif page_type == PageType.SETTINGS and self.settings_page:
                self.page_stack.setCurrentWidget(self.settings_page)
            elif page_type == PageType.VIDEO_EDITOR and self.video_editor_page:
                self.page_stack.setCurrentWidget(self.video_editor_page)
            elif page_type == PageType.EXPORT and self.export_page:
                self.page_stack.setCurrentWidget(self.export_page)
            else:
                self.logger.warning(f"页面不存在或未初始化: {page_type}")
                return

            self.current_page = page_type
            self.page_changed.emit(page_type)

            # 更新按钮状态
            self._update_navigation_buttons()

            # 更新状态栏
            page_names = {
                PageType.HOME: "首页",
                PageType.SETTINGS: "设置",
                PageType.VIDEO_EDITOR: "视频编辑器",
                PageType.EXPORT: "视频导出"
            }
            page_name = page_names.get(page_type, "未知")
            self.status_updated.emit(f"当前页面: {page_name}")

            self.logger.info(f"切换到页面: {page_type.value}")

        except Exception as e:
            self.logger.error(f"切换页面失败: {e}")
            if self.error_handler:
                self.error_handler.handle_error(
                    ErrorType.UI,
                    f"切换页面失败: {e}",
                    ErrorSeverity.MEDIUM
                )

    def _create_enhanced_components(self):
        """创建增强交互组件"""
        try:
            # 创建加载指示器
            self.loading_indicator = LoadingIndicator(self)
            self.loading_indicator.hide()

            # 创建Toast通知
            self.toast_notification = ToastNotification(self)
            self.toast_notification.hide()

            # 创建进度覆盖层
            self.progress_overlay = ProgressOverlay(self)
            self.progress_overlay.hide()

            # 创建交互式引导
            self.interactive_guide = InteractiveGuide(self)
            self.interactive_guide.hide()

            # 创建帮助系统
            self.help_system = HelpSystem(self.application)
            self.help_system.hide()

            self.logger.info("增强交互组件创建完成")

        except Exception as e:
            self.logger.error(f"创建增强交互组件失败: {e}")

    def _update_navigation_buttons(self):
        """更新导航按钮状态"""
        # 重置所有按钮状态
        self.home_btn.set_active(False)
        self.settings_btn.set_active(False)
        self.editor_btn.set_active(False)
        self.export_btn.set_active(False)
        self.help_btn.set_active(False)

        # 设置当前页面按钮为激活状态
        if self.current_page == PageType.HOME:
            self.home_btn.set_active(True)
        elif self.current_page == PageType.SETTINGS:
            self.settings_btn.set_active(True)
        elif self.current_page == PageType.VIDEO_EDITOR:
            self.editor_btn.set_active(True)
        elif self.current_page == PageType.EXPORT:
            self.export_btn.set_active(True)

    def _on_theme_changed(self, theme_name: str):
        """处理主题变更事件"""
        self.is_dark_theme = theme_name == "dark"
        self._apply_theme()
        self._apply_style()

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
            # 确保可访问性焦点管理
            self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

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
        """处理键盘事件 - 增强可访问性"""
        try:
            # Tab导航
            if event.key() == Qt.Key.Key_Tab:
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                # 焦点移动到下一个控件
                current_focus = self.focusWidget()
                if current_focus:
                    # 简化焦点管理，实际可使用QAccessible
                    pass
            # Ctrl+Q: 退出
            elif event.key() == Qt.Key.Key_Q and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
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
            # F1: 帮助
            elif event.key() == Qt.Key.Key_F1:
                self._show_help()
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
        # 同时显示Toast通知
        if self.toast_notification:
            self.toast_notification.show_toast("error", message)

    def show_info_message(self, title: str, message: str):
        """显示信息消息"""
        QMessageBox.information(self, title, message)
        # 同时显示Toast通知
        if self.toast_notification:
            self.toast_notification.show_toast("info", message)

    def show_warning_message(self, title: str, message: str):
        """显示警告消息"""
        QMessageBox.warning(self, title, message)
        # 同时显示Toast通知
        if self.toast_notification:
            self.toast_notification.show_toast("warning", message)

    def show_loading(self, message: str = "加载中..."):
        """显示加载指示器"""
        if self.loading_indicator:
            self.loading_indicator.set_message(message)
            self.loading_indicator.show()

    def hide_loading(self):
        """隐藏加载指示器"""
        if self.loading_indicator:
            self.loading_indicator.hide()

    def show_progress(self, title: str, message: str = "", maximum: int = 100):
        """显示进度覆盖层"""
        if self.progress_overlay:
            self.progress_overlay.set_title(title)
            self.progress_overlay.set_message(message)
            self.progress_overlay.set_maximum(maximum)
            self.progress_overlay.set_value(0)
            self.progress_overlay.show()

    def update_progress(self, value: int, message: str = ""):
        """更新进度"""
        if self.progress_overlay:
            self.progress_overlay.set_value(value)
            if message:
                self.progress_overlay.set_message(message)

    def hide_progress(self):
        """隐藏进度覆盖层"""
        if self.progress_overlay:
            self.progress_overlay.hide()

    def show_toast(self, message_type: str, message: str, duration: int = 3000):
        """显示Toast通知"""
        if self.toast_notification:
            self.toast_notification.show_toast(message_type, message, duration)

    def show_guide(self, steps: list):
        """显示交互式引导"""
        if self.interactive_guide:
            self.interactive_guide.set_steps(steps)
            self.interactive_guide.show()

    def hide_guide(self):
        """隐藏交互式引导"""
        if self.interactive_guide:
            self.interactive_guide.hide()

    def _create_menu_bar(self):
        """创建菜单栏"""
        try:
            # 创建菜单栏
            menubar = self.menuBar()

            # 文件菜单
            file_menu = menubar.addMenu("文件(&F)")

            # 新建项目
            new_action = QAction("新建项目", self)
            new_action.setShortcut(QKeySequence.StandardKey.New)
            new_action.triggered.connect(self._on_new_project)
            file_menu.addAction(new_action)

            # 打开项目
            open_action = QAction("打开项目", self)
            open_action.setShortcut(QKeySequence.StandardKey.Open)
            open_action.triggered.connect(self._on_open_project)
            file_menu.addAction(open_action)

            file_menu.addSeparator()

            # 退出
            exit_action = QAction("退出", self)
            exit_action.setShortcut(QKeySequence.StandardKey.Quit)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            # 编辑菜单
            edit_menu = menubar.addMenu("编辑(&E)")

            # 设置
            settings_action = QAction("设置", self)
            settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
            settings_action.triggered.connect(lambda: self.switch_to_page(PageType.SETTINGS))
            edit_menu.addAction(settings_action)

            # 视图菜单
            view_menu = menubar.addMenu("视图(&V)")

            # 首页
            home_action = QAction("首页", self)
            home_action.setShortcut("Ctrl+1")
            home_action.triggered.connect(lambda: self.switch_to_page(PageType.HOME))
            view_menu.addAction(home_action)

            # 视频编辑器
            editor_action = QAction("视频编辑器", self)
            editor_action.setShortcut("Ctrl+2")
            editor_action.triggered.connect(lambda: self.switch_to_page(PageType.VIDEO_EDITOR))
            view_menu.addAction(editor_action)

            # 导出
            export_action = QAction("视频导出", self)
            export_action.setShortcut("Ctrl+3")
            export_action.triggered.connect(lambda: self.switch_to_page(PageType.EXPORT))
            view_menu.addAction(export_action)

            # 帮助菜单
            help_menu = menubar.addMenu("帮助(&H)")

            # 帮助文档
            help_action = QAction("帮助文档", self)
            help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
            help_action.triggered.connect(self._show_help)
            help_menu.addAction(help_action)

            # 快速入门
            quick_start_action = QAction("快速入门", self)
            quick_start_action.triggered.connect(self._show_quick_start)
            help_menu.addAction(quick_start_action)

            # 键盘快捷键
            shortcuts_action = QAction("键盘快捷键", self)
            shortcuts_action.setShortcut("Ctrl+?")
            shortcuts_action.triggered.connect(self._show_shortcuts)
            help_menu.addAction(shortcuts_action)

            help_menu.addSeparator()

            # 关于
            about_action = QAction("关于", self)
            about_action.triggered.connect(self._show_about)
            help_menu.addAction(about_action)

            self.logger.info("菜单栏创建完成")

        except Exception as e:
            self.logger.error(f"创建菜单栏失败: {e}")

    def _show_help(self):
        """显示帮助系统"""
        if self.help_system:
            self.help_system.show()
            self.help_system.raise_()
            self.help_system.activateWindow()

    def _show_quick_start(self):
        """显示快速入门引导"""
        if self.help_system:
            self.help_system.show()
            self.help_system.show_tutorial("quick_start")

    def _show_shortcuts(self):
        """显示键盘快捷键"""
        if self.help_system:
            self.help_system.show()
            self.help_system.navigate_to_topic("键盘快捷键")

    def _show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>CineAIStudio v2.0</h2>
        <p>专业AI视频编辑器</p>
        <p>基于人工智能的智能视频处理系统</p>
        <br>
        <p><b>特性：</b></p>
        <ul>
            <li>AI智能视频分析</li>
            <li>自动剪辑建议</li>
            <li>智能音频处理</li>
            <li>专业时间线编辑</li>
            <li>多种格式导出</li>
        </ul>
        <br>
        <p>© 2024 CineAIStudio Team</p>
        """

        QMessageBox.about(self, "关于 CineAIStudio", about_text)

    def _on_new_project(self):
        """处理新建项目"""
        self.show_info_message("新建项目", "新建项目功能正在开发中")

    def _on_open_project(self):
        """处理打开项目"""
        self.show_info_message("打开项目", "打开项目功能正在开发中")

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setStyleSheet("""
            QToolBar {
                background: #2A2A2A;
                border: none;
                spacing: 5px;
            }
            QToolButton {
                background: transparent;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
            QToolButton:hover {
                background: #3A3A3A;
            }
            QToolButton:pressed {
                background: #404040;
            }
        """)
        self.addToolBar(toolbar)

        # 导入媒体按钮
        import_action = QAction(get_icon("import", 24), "导入媒体", self)
        import_action.setToolTip("导入视频、音频或图片文件 (Ctrl+I)")
        import_action.setShortcut(QKeySequence.StandardKey.Open)
        import_action.triggered.connect(self._import_media)
        toolbar.addAction(import_action)

        # 新建项目按钮
        new_action = QAction(get_icon("new", 24), "新建项目", self)
        new_action.setToolTip("创建新项目 (Ctrl+N)")
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new_project)
        toolbar.addAction(new_action)

        # 保存项目按钮
        save_action = QAction(get_icon("save", 24), "保存项目", self)
        save_action.setToolTip("保存当前项目 (Ctrl+S)")
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save_project)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # AI助手按钮
        ai_action = QAction(get_icon("ai_magic", 24), "AI助手", self)
        ai_action.setToolTip("打开AI对话页面")
        ai_action.triggered.connect(lambda: self.switch_to_page(PageType.AI_DIALOG))
        toolbar.addAction(ai_action)

        # 多摄像头按钮
        multicam_action = QAction(get_icon("multicam", 24), "多摄像头", self)
        multicam_action.setToolTip("打开多摄像头编辑模式")
        multicam_action.triggered.connect(self._open_multicam_mode)
        toolbar.addAction(multicam_action)

    def _import_media(self):
        """导入媒体"""
        if self.media_service:
            imported = self.media_service.import_media(self)
            if imported:
                self.show_info_message("导入成功", f"成功导入 {len(imported)} 个媒体文件")
            else:
                self.show_warning_message("导入失败", "没有选择文件或导入失败")

    def _on_save_project(self):
        """保存项目"""
        self.show_info_message("保存项目", "保存项目功能正在开发中")

    def _open_multicam_mode(self):
        """打开多摄像头模式"""
        self.show_info_message("多摄像头", "多摄像头编辑功能正在开发中")

    def _on_media_imported(self, metadata):
        """媒体导入完成"""
        self.show_toast("info", f"导入媒体: {metadata.filename}")
        # 切换到视频编辑页面并刷新
        self.switch_to_page(PageType.VIDEO_EDITOR)
        if hasattr(self.video_editor_page, 'media_panel'):
            self.video_editor_page.media_panel.refresh_library()

    def setAccessibleName(self, name: str):
        """设置可访问名称"""
        super().setAccessibleName(name)
        # 确保所有子控件有可访问名称
        for child in self.findChildren(QWidget):
            if not child.accessibleName():
                child.setAccessibleName(child.objectName() or "控件")

    def setAccessibleDescription(self, description: str):
        """设置可访问描述"""
        super().setAccessibleDescription(description)