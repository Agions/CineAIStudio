#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QSplitter, QStatusBar, QMessageBox, QApplication, QLabel
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from app.config.settings_manager import SettingsManager
from app.core.project_manager import ProjectManager
from app.ai import AIManager
from .components.modern_navigation import ModernNavigation
from .components.theme_toggle import ThemeToggle
from .theme_manager import get_theme_manager
from .modern_settings_panel import ModernSettingsPanel
from .modern_video_management import ModernVideoManagement


class EnhancedMainWindow(QMainWindow):
    """增强版主窗口 - 现代化UI设计"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化管理器
        self.settings_manager = SettingsManager()
        self.project_manager = ProjectManager(self.settings_manager)
        self.ai_manager = AIManager(self.settings_manager)
        self.theme_manager = get_theme_manager()
        
        # 当前打开的编辑窗口
        self.editing_window = None
        
        # 设置窗口属性
        self.setWindowTitle("VideoEpicCreator - AI短剧视频编辑器")
        self.setGeometry(100, 100, 1400, 800)
        self.setMinimumSize(1200, 700)
        
        # 创建UI组件
        self._create_ui()
        self._connect_signals()
        self._setup_theme()
        self._load_settings()
        
        # 延迟初始化AI模型
        QTimer.singleShot(1000, self.ai_manager.initialize_delayed_models)
    
    def _create_ui(self):
        """创建用户界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航
        self.navigation = ModernNavigation()
        main_layout.addWidget(self.navigation)
        
        # 右侧内容区域
        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area)
        
        # 创建状态栏
        self._create_statusbar()
    
    def _create_content_area(self) -> QWidget:
        """创建内容区域"""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 顶部工具栏
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)
        
        # 主内容区域
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # 创建各个页面
        self._create_pages()
        
        return content_widget
    
    def _create_toolbar(self) -> QWidget:
        """创建顶部工具栏"""
        toolbar = QWidget()
        toolbar.setObjectName("main_toolbar")
        toolbar.setFixedHeight(60)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(16)
        
        # 页面标题
        self.page_title = QLabel("首页")
        self.page_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.page_title.setObjectName("page_title")
        layout.addWidget(self.page_title)
        
        # 弹性空间
        layout.addStretch()
        
        # 主题切换
        self.theme_toggle = ThemeToggle()
        layout.addWidget(self.theme_toggle)
        
        # 应用工具栏样式
        toolbar.setStyleSheet("""
            QWidget#main_toolbar {
                background-color: #ffffff;
                border-bottom: 1px solid #f0f0f0;
            }
            
            QLabel#page_title {
                color: #262626;
                font-weight: 600;
            }
        """)
        
        return toolbar
    
    def _create_pages(self):
        """创建各个页面"""
        # 首页
        self.home_page = self._create_home_page()
        self.stacked_widget.addWidget(self.home_page)
        
        # 项目管理页面
        self.projects_page = self._create_projects_page()
        self.stacked_widget.addWidget(self.projects_page)
        
        # AI功能页面
        self.ai_features_page = self._create_ai_features_page()
        self.stacked_widget.addWidget(self.ai_features_page)
        
        # 设置页面
        self.settings_page = ModernSettingsPanel(self.settings_manager)
        self.stacked_widget.addWidget(self.settings_page)
        
        # 默认显示首页
        self.stacked_widget.setCurrentIndex(0)
    
    def _create_home_page(self) -> QWidget:
        """创建首页"""
        from .pages.home_page import HomePage
        try:
            return HomePage(self.project_manager, self.ai_manager)
        except ImportError:
            # 如果首页组件不存在，创建简单的占位符
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(24, 24, 24, 24)
            
            from PyQt6.QtWidgets import QLabel
            welcome_label = QLabel("欢迎使用 VideoEpicCreator")
            welcome_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
            welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            welcome_label.setStyleSheet("color: #1890ff; margin: 40px;")
            
            desc_label = QLabel("AI驱动的短剧视频编辑器\n\n请从左侧导航选择功能模块")
            desc_label.setFont(QFont("Arial", 14))
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setStyleSheet("color: #595959; line-height: 1.6;")
            
            layout.addStretch()
            layout.addWidget(welcome_label)
            layout.addWidget(desc_label)
            layout.addStretch()
            
            return page
    
    def _create_projects_page(self) -> QWidget:
        """创建项目管理页面"""
        try:
            return ModernVideoManagement()
        except Exception as e:
            print(f"创建项目页面失败: {e}")
            # 创建占位符
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(24, 24, 24, 24)

            from PyQt6.QtWidgets import QLabel
            label = QLabel("项目管理功能正在开发中...")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #595959; font-size: 16px;")
            layout.addWidget(label)

            return page
    
    def _create_ai_features_page(self) -> QWidget:
        """创建AI功能页面"""
        from .pages.ai_features_page import AIFeaturesPage
        try:
            return AIFeaturesPage(self.ai_manager)
        except ImportError:
            # 创建占位符
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(24, 24, 24, 24)
            
            from PyQt6.QtWidgets import QLabel, QTabWidget
            
            # 创建选项卡
            tab_widget = QTabWidget()
            
            # AI短剧解说
            commentary_tab = QWidget()
            commentary_layout = QVBoxLayout(commentary_tab)
            commentary_label = QLabel("🎬 AI短剧解说功能")
            commentary_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            commentary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            commentary_layout.addWidget(commentary_label)
            tab_widget.addTab(commentary_tab, "AI短剧解说")
            
            # AI高能混剪
            compilation_tab = QWidget()
            compilation_layout = QVBoxLayout(compilation_tab)
            compilation_label = QLabel("⚡ AI高能混剪功能")
            compilation_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            compilation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            compilation_layout.addWidget(compilation_label)
            tab_widget.addTab(compilation_tab, "AI高能混剪")
            
            # AI第一人称独白
            monologue_tab = QWidget()
            monologue_layout = QVBoxLayout(monologue_tab)
            monologue_label = QLabel("🎭 AI第一人称独白功能")
            monologue_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            monologue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            monologue_layout.addWidget(monologue_label)
            tab_widget.addTab(monologue_tab, "AI第一人称独白")
            
            layout.addWidget(tab_widget)
            return page
    
    def _create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")
        
        # 状态栏样式
        self.statusbar.setStyleSheet("""
            QStatusBar {
                background-color: #fafafa;
                border-top: 1px solid #f0f0f0;
                color: #595959;
                font-size: 12px;
            }
        """)
    
    def _connect_signals(self):
        """连接信号"""
        # 导航信号
        self.navigation.navigation_changed.connect(self._on_navigation_changed)
        
        # 主题变更信号
        self.theme_toggle.theme_changed.connect(self._on_theme_changed)
        self.theme_manager.theme_changed.connect(self._on_theme_manager_changed)
        
        # 设置变更信号
        self.settings_manager.settings_changed.connect(self._on_settings_changed)
    
    def _setup_theme(self):
        """设置主题"""
        # 从设置中加载主题
        saved_theme = self.settings_manager.get_setting("app.theme", "light")
        self.theme_manager.set_theme(saved_theme)
        
        # 更新主题切换控件
        self.theme_toggle.set_theme(saved_theme)
    
    def _load_settings(self):
        """加载设置"""
        # 恢复窗口几何
        geometry = self.settings_manager.get_setting("window.geometry")
        if geometry:
            try:
                self.restoreGeometry(geometry)
            except:
                pass
        
        # 恢复窗口状态
        state = self.settings_manager.get_setting("window.state")
        if state:
            try:
                self.restoreState(state)
            except:
                pass
    
    def _save_settings(self):
        """保存设置"""
        # 保存窗口几何和状态
        self.settings_manager.set_setting("window.geometry", self.saveGeometry())
        self.settings_manager.set_setting("window.state", self.saveState())
    
    def _on_navigation_changed(self, page_id: str):
        """导航变更处理"""
        page_map = {
            "home": (0, "首页"),
            "projects": (1, "项目管理"),
            "ai_features": (2, "AI功能"),
            "settings": (3, "设置")
        }
        
        if page_id in page_map:
            index, title = page_map[page_id]
            self.stacked_widget.setCurrentIndex(index)
            self.page_title.setText(title)
            self.statusbar.showMessage(f"已切换到: {title}")
    
    def _on_theme_changed(self, theme_value: str):
        """主题变更处理"""
        # 保存主题设置
        self.settings_manager.set_setting("app.theme", theme_value)
        
        # 应用主题
        self.theme_manager.set_theme(theme_value)
    
    def _on_theme_manager_changed(self, theme_value: str):
        """主题管理器变更处理"""
        is_dark = theme_value == "dark"
        
        # 更新导航样式
        self.navigation.update_theme_styles(is_dark)
        
        # 更新工具栏样式
        if is_dark:
            self.toolbar.setStyleSheet("""
                QWidget#main_toolbar {
                    background-color: #1f1f1f;
                    border-bottom: 1px solid #434343;
                }
                
                QLabel#page_title {
                    color: #ffffff;
                    font-weight: 600;
                }
            """)
            
            self.statusbar.setStyleSheet("""
                QStatusBar {
                    background-color: #262626;
                    border-top: 1px solid #434343;
                    color: #a6a6a6;
                    font-size: 12px;
                }
            """)
        else:
            self.toolbar.setStyleSheet("""
                QWidget#main_toolbar {
                    background-color: #ffffff;
                    border-bottom: 1px solid #f0f0f0;
                }
                
                QLabel#page_title {
                    color: #262626;
                    font-weight: 600;
                }
            """)
            
            self.statusbar.setStyleSheet("""
                QStatusBar {
                    background-color: #fafafa;
                    border-top: 1px solid #f0f0f0;
                    color: #595959;
                    font-size: 12px;
                }
            """)
    
    def _on_settings_changed(self, key: str, value):
        """设置变更处理"""
        if key == "app.theme":
            self.theme_toggle.set_theme(value)
    
    def closeEvent(self, event):
        """关闭事件"""
        # 保存设置
        self._save_settings()
        
        # 关闭编辑窗口
        if self.editing_window:
            self.editing_window.close()
        
        event.accept()
