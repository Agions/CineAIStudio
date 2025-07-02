#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QApplication,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QFormLayout, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QProgressBar, QTabWidget, QScrollArea, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont, QPixmap

from app.config.settings_manager import SettingsManager
from app.core.project_manager import ProjectManager, ProjectInfo
from app.core.video_manager import VideoClip
from app.ai import AIManager
from .video_management_panel import VideoManagementPanel
from .settings_panel import SettingsPanel
from .video_editing_window import VideoEditingWindow


class NewMainWindow(QMainWindow):
    """重新设计的主窗口 - 符合新的UI布局要求"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化管理器
        self.settings_manager = SettingsManager()
        self.project_manager = ProjectManager(self.settings_manager)
        self.ai_manager = AIManager(self.settings_manager)

        # 当前打开的编辑窗口
        self.editing_window = None
        
        # 设置窗口属性
        self.setWindowTitle("VideoEpicCreator - AI短剧视频编辑器")
        self.setGeometry(100, 100, 1400, 800)
        
        # 创建UI组件
        self._create_central_widget()
        self._create_statusbar()
        
        # 连接信号
        self._connect_signals()
        
        # 设置样式
        self._setup_styles()
        
        # 加载设置
        self._load_settings()

        # 初始化延迟的AI模型
        QTimer.singleShot(1000, self.ai_manager.initialize_delayed_models)

    def _switch_panel(self, panel_type: str):
        """切换右侧面板"""
        if panel_type == "core":
            # 切换到核心功能页面
            self.stacked_widget.setCurrentIndex(0)
            self.core_features_btn.setChecked(True)
            self.settings_btn.setChecked(False)
            self.page_title.setText("AI视频创作")
            self.quick_action_btn.setText("开始创作")
        elif panel_type == "settings":
            # 切换到设置页面
            self.stacked_widget.setCurrentIndex(1)
            self.core_features_btn.setChecked(False)
            self.settings_btn.setChecked(True)
            self.page_title.setText("系统设置")
            self.quick_action_btn.setText("保存设置")
    

    
    def _create_central_widget(self):
        """创建中央窗口部件"""
        # 创建主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建左右分隔面板
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # 左侧面板 - 项目管理和设置
        self.left_panel = self._create_left_panel()
        self.main_splitter.addWidget(self.left_panel)
        
        # 右侧面板 - 项目列表和编辑控制
        self.right_panel = self._create_right_panel()
        self.main_splitter.addWidget(self.right_panel)
        
        # 设置初始大小比例 - 进一步缩短左侧导航，增加右侧空间
        self.main_splitter.setSizes([200, 1200])
    
    def _create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        panel.setObjectName("left_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 应用标题
        title_label = QLabel("VideoEpicCreator")
        title_label.setObjectName("app_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 导航菜单 - 紧凑型设计
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        # 核心功能按钮
        self.core_features_btn = QPushButton("AI创作")
        self.core_features_btn.setObjectName("nav_button")
        self.core_features_btn.setCheckable(True)
        self.core_features_btn.setChecked(True)  # 默认选中
        self.core_features_btn.clicked.connect(lambda: self._switch_panel("core"))
        nav_layout.addWidget(self.core_features_btn)

        # 设置按钮
        self.settings_btn = QPushButton("设置")
        self.settings_btn.setObjectName("nav_button")
        self.settings_btn.setCheckable(True)
        self.settings_btn.clicked.connect(lambda: self._switch_panel("settings"))
        nav_layout.addWidget(self.settings_btn)

        layout.addWidget(nav_container)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { color: #f0f0f0; }")
        layout.addWidget(separator)

        # AI状态显示
        ai_status_container = QWidget()
        ai_status_layout = QVBoxLayout(ai_status_container)
        ai_status_layout.setContentsMargins(0, 0, 0, 0)
        ai_status_layout.setSpacing(4)

        ai_status_title = QLabel("AI模型状态")
        ai_status_title.setStyleSheet("color: #595959; font-size: 12px; font-weight: 600;")
        ai_status_layout.addWidget(ai_status_title)

        self.ai_status_label = QLabel("正在初始化...")
        self.ai_status_label.setStyleSheet("color: #8c8c8c; font-size: 11px;")
        self.ai_status_label.setWordWrap(True)
        ai_status_layout.addWidget(self.ai_status_label)

        layout.addWidget(ai_status_container)
        layout.addStretch()

        return panel
    
    def _create_right_panel(self) -> QWidget:
        """创建现代化右侧面板"""
        panel = QWidget()
        panel.setObjectName("right_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 顶部标题栏
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # 当前页面标题
        self.page_title = QLabel("项目管理")
        self.page_title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #1e40af;
                padding: 8px 0px;
            }
        """)
        header_layout.addWidget(self.page_title)

        header_layout.addStretch()

        # 快捷操作按钮
        self.quick_action_btn = QPushButton("新建项目")
        self.quick_action_btn.setObjectName("primary_button")
        header_layout.addWidget(self.quick_action_btn)

        layout.addWidget(header_container)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("QFrame { background-color: #e5e7eb; height: 1px; }")
        layout.addWidget(separator)

        # 主内容区域 - 使用卡片式设计
        content_container = QWidget()
        content_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #ffffff, stop:1 #f9fafb);
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                padding: 16px;
            }
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        # 使用QStackedWidget来切换不同的页面
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        # 创建核心功能页面
        self.core_features_panel = self._create_core_features_panel()
        self.stacked_widget.addWidget(self.core_features_panel)

        # 创建设置页面
        self.settings_panel = SettingsPanel(self.settings_manager)
        self.stacked_widget.addWidget(self.settings_panel)

        # 默认显示核心功能页面
        self.stacked_widget.setCurrentIndex(0)

        layout.addWidget(content_container)

        return panel

    def _create_core_features_panel(self) -> QWidget:
        """创建核心功能面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #f3f4f6, stop:1 #e5e7eb);
                border: 1px solid #d1d5db;
                border-bottom: none;
                border-radius: 8px 8px 0px 0px;
                padding: 12px 20px;
                margin-right: 4px;
                color: #6b7280;
                font-weight: 500;
                min-width: 120px;
                font-size: 14px;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #eff6ff, stop:1 #dbeafe);
                color: #1e40af;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #ffffff, stop:1 #f8fafc);
                color: #1e40af;
                font-weight: 600;
                border-color: #3b82f6;
            }
        """)

        # AI短剧解说标签页
        try:
            from .core_features.commentary_panel import CommentaryPanel
            commentary_panel = CommentaryPanel(self.ai_manager)
            tab_widget.addTab(commentary_panel, "🎬 AI短剧解说")
        except ImportError as e:
            # 如果导入失败，创建占位符
            placeholder = self._create_feature_placeholder("AI短剧解说", "智能生成解说内容并同步到视频")
            tab_widget.addTab(placeholder, "🎬 AI短剧解说")

        # AI高能混剪标签页
        try:
            from .core_features.compilation_panel import CompilationPanel
            compilation_panel = CompilationPanel(self.ai_manager)
            tab_widget.addTab(compilation_panel, "⚡ AI高能混剪")
        except ImportError as e:
            placeholder = self._create_feature_placeholder("AI高能混剪", "自动检测精彩片段并生成混剪")
            tab_widget.addTab(placeholder, "⚡ AI高能混剪")

        # AI第一人称独白标签页
        try:
            from .core_features.monologue_panel import MonologuePanel
            monologue_panel = MonologuePanel(self.ai_manager)
            tab_widget.addTab(monologue_panel, "💭 AI第一人称独白")
        except ImportError as e:
            placeholder = self._create_feature_placeholder("AI第一人称独白", "生成角色独白并匹配场景")
            tab_widget.addTab(placeholder, "💭 AI第一人称独白")

        layout.addWidget(tab_widget)
        return panel

    def _create_feature_placeholder(self, feature_name: str, description: str) -> QWidget:
        """创建功能占位符"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        # 图标
        icon_label = QLabel("🚧")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(feature_name)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #1e40af; margin: 8px 0px;")
        layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("font-size: 16px; color: #6b7280; margin-bottom: 16px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 状态
        status_label = QLabel("功能开发中，敬请期待...")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("font-size: 14px; color: #f59e0b; font-weight: 500;")
        layout.addWidget(status_label)

        return widget
    
    def _create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)
        
        # AI模型状态
        self.ai_status_label = QLabel("AI: 未配置")
        self.statusbar.addPermanentWidget(self.ai_status_label)
    
    def _connect_signals(self):
        """连接信号"""
        # 设置面板信号
        try:
            self.settings_panel.settings_changed.connect(self._on_settings_changed)
        except AttributeError:
            pass

        # AI管理器信号
        try:
            self.ai_manager.model_initialized.connect(self._on_ai_model_initialized)
            self.ai_manager.model_response_ready.connect(self._on_ai_response_ready)
        except AttributeError:
            pass
    
    def _setup_styles(self):
        """设置现代化样式"""
        # 优先加载最新的现代化样式
        style_files = [
            "resources/styles/modern_style.qss",  # 最新现代化样式
            "resources/styles/antd_style.qss",    # Ant Design样式
            "resources/styles/style.qss"          # 原始样式
        ]

        for style_path in style_files:
            try:
                if os.path.exists(style_path):
                    with open(style_path, "r", encoding="utf-8") as f:
                        self.setStyleSheet(f.read())
                    print(f"✅ 成功加载样式: {style_path}")
                    break
            except Exception as e:
                print(f"❌ 加载样式失败 {style_path}: {e}")
                continue
        else:
            print("⚠️ 所有样式文件加载失败，使用默认样式")
    
    def _load_settings(self):
        """加载设置"""
        # 加载窗口设置
        window_size = self.settings_manager.get_setting("ui.window_size", [1400, 800])
        self.resize(window_size[0], window_size[1])
        
        if self.settings_manager.get_setting("ui.window_maximized", False):
            self.showMaximized()
        
        # 加载面板宽度
        left_width = self.settings_manager.get_setting("ui.left_panel_width", 300)
        right_width = self.settings_manager.get_setting("ui.right_panel_width", 1100)
        self.main_splitter.setSizes([left_width, right_width])
        
        # 更新AI状态
        self._update_ai_status()
    
    def _save_settings(self):
        """保存设置"""
        # 保存窗口设置
        self.settings_manager.set_setting("ui.window_size", [self.width(), self.height()])
        self.settings_manager.set_setting("ui.window_maximized", self.isMaximized())
        
        # 保存面板宽度
        sizes = self.main_splitter.sizes()
        if len(sizes) >= 2:
            self.settings_manager.set_setting("ui.left_panel_width", sizes[0])
            self.settings_manager.set_setting("ui.right_panel_width", sizes[1])
    
    def _update_ai_status(self):
        """更新AI状态显示"""
        # 获取可用的AI模型
        available_models = self.ai_manager.get_available_models()

        if available_models:
            # 显示可用模型
            model_names = []
            for provider in available_models:
                if provider == "openai":
                    model_names.append("OpenAI")
                elif provider == "qianwen":
                    model_names.append("通义千问")
                elif provider == "wenxin":
                    model_names.append("文心一言")
                elif provider == "zhipu":
                    model_names.append("智谱AI")
                elif provider == "xunfei":
                    model_names.append("讯飞星火")
                elif provider == "hunyuan":
                    model_names.append("腾讯混元")
                elif provider == "deepseek":
                    model_names.append("DeepSeek")
                elif provider == "ollama":
                    model_names.append("Ollama")
                else:
                    model_names.append(provider.title())

            status_text = f"AI: {', '.join(model_names)}"
        else:
            status_text = "AI: 未配置"

        self.ai_status_label.setText(status_text)
    
    # 事件处理方法
    def _on_new_project(self):
        """新建项目"""
        self.editing_panel.show_new_project_dialog()
    
    def _on_new_project_from_panel(self, project_info):
        """从面板新建项目"""
        project = self.project_manager.create_project(
            project_info['name'],
            project_info['description'],
            project_info['editing_mode']
        )
        self.status_label.setText(f"已创建项目: {project.name}")
    
    def _on_open_project(self):
        """打开项目"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("VideoEpicCreator项目文件 (*.vecp)")
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if self.project_manager.load_project(file_path):
                self.status_label.setText(f"已打开项目: {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "打开失败", f"无法打开项目文件: {file_path}")
    
    def _on_save_project(self):
        """保存项目"""
        if self.project_manager.current_project:
            if self.project_manager.save_project():
                self.status_label.setText("项目已保存")
            else:
                QMessageBox.warning(self, "保存失败", "无法保存项目")
        else:
            QMessageBox.information(self, "提示", "没有打开的项目")
    
    def _on_settings(self):
        """打开设置"""
        # 切换到设置选项卡
        left_tab_widget = self.left_panel.findChild(QTabWidget)
        if left_tab_widget:
            left_tab_widget.setCurrentIndex(1)  # 设置选项卡
    
    def _on_ai_settings(self):
        """打开AI设置"""
        self._on_settings()
        # 可以进一步切换到AI设置子选项卡
    

    
    def _on_edit_video(self, video: VideoClip):
        """编辑视频"""
        # 打开视频编辑窗口
        if self.editing_window:
            self.editing_window.close()

        self.editing_window = VideoEditingWindow(video, self.settings_manager, self.ai_manager)
        self.editing_window.show()
    
    def _on_settings_changed(self, key: str, value):
        """设置变更回调"""
        if key.startswith("ai_models"):
            # 重新加载AI模型
            self.ai_manager.reload_models()
            self._update_ai_status()

    def _on_ai_model_initialized(self, provider: str, success: bool):
        """AI模型初始化回调"""
        if success:
            print(f"AI模型 {provider} 初始化成功")
        else:
            print(f"AI模型 {provider} 初始化失败")

        # 更新状态显示
        self._update_ai_status()

    def _on_ai_response_ready(self, provider: str, response):
        """AI响应就绪回调"""
        if response.success:
            print(f"AI模型 {provider} 响应成功: {response.content[:100]}...")
        else:
            print(f"AI模型 {provider} 响应失败: {response.error_message}")
    
    def closeEvent(self, event):
        """关闭事件"""
        # 保存设置
        self._save_settings()
        
        # 检查是否有未保存的项目
        if self.project_manager.is_project_modified():
            reply = QMessageBox.question(
                self, "确认退出",
                "当前项目有未保存的更改，是否保存？",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if not self.project_manager.save_project():
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        
        # 关闭编辑窗口
        if self.editing_window:
            self.editing_window.close()
        
        event.accept()
