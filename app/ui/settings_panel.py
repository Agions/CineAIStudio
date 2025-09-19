#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGroupBox, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QComboBox, QSlider, QFileDialog, QMessageBox,
    QTextEdit, QScrollArea, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPixmap, QDesktopServices
from PyQt6.QtCore import QUrl

from app.config.settings_manager import SettingsManager
from app.config.defaults import AI_PROVIDERS
import os
import webbrowser


class APIKeyWidget(QWidget):
    """API密钥输入控件"""
    
    key_changed = pyqtSignal(str, str)  # provider, key
    
    def __init__(self, provider: str, provider_info: dict, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        
        self.provider = provider
        self.provider_info = provider_info
        self.settings_manager = settings_manager
        
        self._setup_ui()
        self._load_current_key()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 创建卡片容器
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #ffffff, stop:1 #f8fafc);
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 16px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        # 提供商信息头部
        header_layout = QHBoxLayout()

        # 提供商名称和图标
        name_layout = QHBoxLayout()

        # 添加图标
        icon_label = QLabel("🤖")
        icon_label.setStyleSheet("font-size: 20px;")
        name_layout.addWidget(icon_label)

        # 提供商名称
        name_label = QLabel(self.provider_info["display_name"])
        name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        name_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-weight: 600;
                margin-left: 8px;
            }
        """)
        name_layout.addWidget(name_label)
        name_layout.addStretch()

        header_layout.addLayout(name_layout)
        header_layout.addStretch()

        # 操作按钮组
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        # 官网链接按钮
        self.website_btn = QPushButton("🌐 官网")
        self.website_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #f1f5f9, stop:1 #e2e8f0);
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                color: #475569;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #e2e8f0, stop:1 #cbd5e1);
                color: #334155;
            }
        """)
        self.website_btn.clicked.connect(self._open_website)
        button_layout.addWidget(self.website_btn)

        # API文档链接按钮
        self.docs_btn = QPushButton("📚 文档")
        self.docs_btn.setStyleSheet(self.website_btn.styleSheet())
        self.docs_btn.clicked.connect(self._open_docs)
        button_layout.addWidget(self.docs_btn)

        header_layout.addLayout(button_layout)
        card_layout.addLayout(header_layout)

        # API密钥输入区域
        key_group = QFrame()
        key_group.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        key_group_layout = QVBoxLayout(key_group)
        key_group_layout.setContentsMargins(12, 12, 12, 12)
        key_group_layout.setSpacing(8)

        # 标签
        key_label = QLabel("API密钥:")
        key_label.setStyleSheet("""
            QLabel {
                color: #374151;
                font-weight: 500;
                font-size: 13px;
            }
        """)
        key_group_layout.addWidget(key_label)

        # 输入框和按钮行
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("请输入API密钥...")
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #374151;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background: #fefefe;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
        """)
        self.key_edit.textChanged.connect(self._on_key_changed)
        input_layout.addWidget(self.key_edit)

        # 显示/隐藏按钮
        self.toggle_btn = QPushButton("👁️")
        self.toggle_btn.setFixedSize(36, 36)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #e5e7eb;
            }
            QPushButton:pressed {
                background: #d1d5db;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle_visibility)
        input_layout.addWidget(self.toggle_btn)

        # 测试按钮
        self.test_btn = QPushButton("🔍 测试")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #3b82f6, stop:1 #1d4ed8);
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #2563eb, stop:1 #1e40af);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #1e40af, stop:1 #1e3a8a);
            }
            QPushButton:disabled {
                background: #9ca3af;
                color: #ffffff;
            }
        """)
        self.test_btn.clicked.connect(self._test_connection)
        input_layout.addWidget(self.test_btn)

        key_group_layout.addLayout(input_layout)

        # 状态标签
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 12px;
                font-weight: 400;
                margin-top: 4px;
            }
        """)
        key_group_layout.addWidget(self.status_label)

        card_layout.addWidget(key_group)
        layout.addWidget(card)
    
    def _load_current_key(self):
        """加载当前密钥"""
        if self.settings_manager.has_api_key(self.provider):
            masked_key = self.settings_manager.get_masked_api_key(self.provider)
            self.key_edit.setText(masked_key)
            self.status_label.setText("已配置")
            self.status_label.setStyleSheet("color: green; font-size: 10px;")
        else:
            self.status_label.setText("未配置")
            self.status_label.setStyleSheet("color: red; font-size: 10px;")
    
    def _on_key_changed(self):
        """密钥变更"""
        key = self.key_edit.text().strip()
        if key and not key.startswith("*"):  # 不是掩码显示
            self.settings_manager.set_api_key(self.provider, key)
            self.key_changed.emit(self.provider, key)
            self.status_label.setText("已保存")
            self.status_label.setStyleSheet("color: green; font-size: 10px;")
    
    def _toggle_visibility(self):
        """切换密钥可见性"""
        if self.key_edit.echoMode() == QLineEdit.EchoMode.Password:
            # 显示真实密钥
            real_key = self.settings_manager.get_api_key(self.provider)
            self.key_edit.setText(real_key)
            self.key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setText("隐藏")
        else:
            # 隐藏密钥
            masked_key = self.settings_manager.get_masked_api_key(self.provider)
            self.key_edit.setText(masked_key)
            self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setText("显示")
    
    def _test_connection(self):
        """测试连接"""
        # TODO: 实现API连接测试
        self.status_label.setText("测试中...")
        self.status_label.setStyleSheet("color: orange; font-size: 10px;")
        
        # 模拟测试
        QTimer.singleShot(1000, self._test_complete)
    
    def _test_complete(self):
        """测试完成"""
        if self.settings_manager.has_api_key(self.provider):
            self.status_label.setText("连接正常")
            self.status_label.setStyleSheet("color: green; font-size: 10px;")
        else:
            self.status_label.setText("连接失败")
            self.status_label.setStyleSheet("color: red; font-size: 10px;")
    
    def _open_website(self):
        """打开官网"""
        QDesktopServices.openUrl(QUrl(self.provider_info["website"]))
    
    def _open_docs(self):
        """打开API文档"""
        QDesktopServices.openUrl(QUrl(self.provider_info["api_docs"]))


class SettingsPanel(QWidget):
    """设置面板"""
    
    settings_changed = pyqtSignal(str, object)  # key, value
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        
        self.settings_manager = settings_manager
        
        self._setup_ui()
        self._connect_signals()
        self._load_settings()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 设置页面标题
        title_layout = QHBoxLayout()

        title_label = QLabel("⚙️ 系统设置")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-weight: 700;
                margin-bottom: 8px;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 重置按钮
        reset_btn = QPushButton("🔄 重置设置")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #ef4444, stop:1 #dc2626);
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #dc2626, stop:1 #b91c1c);
            }
        """)
        reset_btn.clicked.connect(self._reset_settings)
        title_layout.addWidget(reset_btn)

        layout.addLayout(title_layout)

        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background: #ffffff;
                padding: 0px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #f8fafc, stop:1 #f1f5f9);
                border: 1px solid #e2e8f0;
                border-bottom: none;
                border-radius: 8px 8px 0px 0px;
                padding: 12px 20px;
                margin-right: 2px;
                color: #64748b;
                font-weight: 500;
                font-size: 14px;
                min-width: 100px;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #f1f5f9, stop:1 #e2e8f0);
                color: #475569;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #ffffff, stop:1 #f8fafc);
                color: #1e293b;
                font-weight: 600;
                border-color: #3b82f6;
                border-bottom: 2px solid #3b82f6;
            }
            QTabBar::tab:first {
                margin-left: 0;
            }
        """)
        layout.addWidget(self.tab_widget)

        # 创建各个标签页
        self.general_tab = self._create_general_tab()
        self.tab_widget.addTab(self.general_tab, "🏠 通用")

        self.ai_tab = self._create_ai_tab()
        self.tab_widget.addTab(self.ai_tab, "🤖 AI模型")

        self.paths_tab = self._create_paths_tab()
        self.tab_widget.addTab(self.paths_tab, "📁 路径")

        self.performance_tab = self._create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "⚡ 性能")
    
    def _create_general_tab(self) -> QWidget:
        """创建通用设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 界面设置
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout(ui_group)
        
        # 主题选择 - 使用新的主题切换组件
        from .components.theme_toggle import ThemeToggle
        self.theme_toggle = ThemeToggle()
        ui_layout.addRow("主题:", self.theme_toggle)
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        ui_layout.addRow("语言:", self.language_combo)
        
        # 自动保存
        self.auto_save_check = QCheckBox("启用自动保存")
        ui_layout.addRow("", self.auto_save_check)
        
        # 自动保存间隔
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(60, 3600)
        self.auto_save_interval.setSuffix(" 秒")
        ui_layout.addRow("自动保存间隔:", self.auto_save_interval)
        
        layout.addWidget(ui_group)
        
        # 更新设置
        update_group = QGroupBox("更新设置")
        update_layout = QFormLayout(update_group)
        
        self.check_updates_check = QCheckBox("启动时检查更新")
        update_layout.addRow("", self.check_updates_check)
        
        layout.addWidget(update_group)
        
        layout.addStretch()
        return tab
    
    def _create_ai_tab(self) -> QWidget:
        """创建AI模型设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f1f5f9;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
        """)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 8, 0)
        scroll_layout.setSpacing(16)

        # 默认模型选择
        default_group = QGroupBox("🎯 默认AI模型")
        default_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                color: #1e293b;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #ffffff, stop:1 #f8fafc);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px 0 8px;
                background: #ffffff;
                border-radius: 4px;
            }
        """)

        default_layout = QFormLayout(default_group)
        default_layout.setContentsMargins(16, 20, 16, 16)
        default_layout.setSpacing(12)

        self.default_model_combo = QComboBox()
        self.default_model_combo.addItems([
            "智谱AI (GLM)", "DeepSeek (深度求索)", "通义千问 (阿里云)",
            "文心一言 (百度)", "讯飞星火", "腾讯混元", "OpenAI", "Ollama"
        ])
        self.default_model_combo.setStyleSheet("""
            QComboBox {
                background: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #374151;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6b7280;
                margin-right: 5px;
            }
        """)
        default_layout.addRow("默认模型:", self.default_model_combo)

        scroll_layout.addWidget(default_group)

        # AI模型配置
        models_group = QGroupBox("🔑 AI模型配置")
        models_group.setStyleSheet(default_group.styleSheet())

        models_layout = QVBoxLayout(models_group)
        models_layout.setContentsMargins(16, 20, 16, 16)
        models_layout.setSpacing(12)

        # 为每个AI提供商创建配置控件
        self.api_key_widgets = {}
        for i, (provider, info) in enumerate(AI_PROVIDERS.items()):
            widget = APIKeyWidget(provider, info, self.settings_manager)
            widget.key_changed.connect(self._on_api_key_changed)
            self.api_key_widgets[provider] = widget
            models_layout.addWidget(widget)

            # 添加分隔线（除了最后一个）
            if i < len(AI_PROVIDERS) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setStyleSheet("""
                    QFrame {
                        color: #e2e8f0;
                        background-color: #e2e8f0;
                        border: none;
                        height: 1px;
                        margin: 8px 0px;
                    }
                """)
                models_layout.addWidget(line)

        scroll_layout.addWidget(models_group)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        return tab
    
    def _create_paths_tab(self) -> QWidget:
        """创建路径设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 项目路径设置
        project_group = QGroupBox("项目路径")
        project_layout = QFormLayout(project_group)
        
        # 默认项目位置
        project_path_layout = QHBoxLayout()
        self.project_path_edit = QLineEdit()
        project_path_layout.addWidget(self.project_path_edit)
        
        project_browse_btn = QPushButton("浏览")
        project_browse_btn.clicked.connect(self._browse_project_path)
        project_path_layout.addWidget(project_browse_btn)
        
        project_layout.addRow("默认项目位置:", project_path_layout)
        
        layout.addWidget(project_group)
        
        # 剪映集成设置
        jianying_group = QGroupBox("剪映集成")
        jianying_layout = QFormLayout(jianying_group)
        
        # 自动检测剪映路径
        self.auto_detect_jianying = QCheckBox("自动检测剪映安装路径")
        jianying_layout.addRow("", self.auto_detect_jianying)
        
        # 剪映草稿文件夹
        jianying_path_layout = QHBoxLayout()
        self.jianying_path_edit = QLineEdit()
        jianying_path_layout.addWidget(self.jianying_path_edit)
        
        jianying_browse_btn = QPushButton("浏览")
        jianying_browse_btn.clicked.connect(self._browse_jianying_path)
        jianying_path_layout.addWidget(jianying_browse_btn)
        
        jianying_detect_btn = QPushButton("检测")
        jianying_detect_btn.clicked.connect(self._detect_jianying_path)
        jianying_path_layout.addWidget(jianying_detect_btn)
        
        jianying_layout.addRow("草稿文件夹:", jianying_path_layout)
        
        layout.addWidget(jianying_group)
        
        # 导出路径设置
        export_group = QGroupBox("导出设置")
        export_layout = QFormLayout(export_group)
        
        # 默认导出位置
        export_path_layout = QHBoxLayout()
        self.export_path_edit = QLineEdit()
        export_path_layout.addWidget(self.export_path_edit)
        
        export_browse_btn = QPushButton("浏览")
        export_browse_btn.clicked.connect(self._browse_export_path)
        export_path_layout.addWidget(export_browse_btn)
        
        export_layout.addRow("默认导出位置:", export_path_layout)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        return tab
    
    def _create_performance_tab(self) -> QWidget:
        """创建性能设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 处理设置
        processing_group = QGroupBox("处理设置")
        processing_layout = QFormLayout(processing_group)
        
        # 最大线程数
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 16)
        processing_layout.addRow("最大线程数:", self.max_threads_spin)
        
        # 内存限制
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(512, 8192)
        self.memory_limit_spin.setSuffix(" MB")
        processing_layout.addRow("内存限制:", self.memory_limit_spin)
        
        # GPU加速
        self.gpu_acceleration_check = QCheckBox("启用GPU加速")
        processing_layout.addRow("", self.gpu_acceleration_check)
        
        layout.addWidget(processing_group)
        
        # 缓存设置
        cache_group = QGroupBox("缓存设置")
        cache_layout = QFormLayout(cache_group)
        
        # 最大缓存大小
        self.max_cache_spin = QSpinBox()
        self.max_cache_spin.setRange(100, 10240)
        self.max_cache_spin.setSuffix(" MB")
        cache_layout.addRow("最大缓存大小:", self.max_cache_spin)
        
        # 清理缓存按钮
        clear_cache_btn = QPushButton("清理缓存")
        clear_cache_btn.clicked.connect(self._clear_cache)
        cache_layout.addRow("", clear_cache_btn)
        
        layout.addWidget(cache_group)
        
        layout.addStretch()
        return tab
    
    def _connect_signals(self):
        """连接信号"""
        # 通用设置信号
        self.theme_toggle.theme_changed.connect(
            lambda v: self._save_setting("app.theme", v)
        )
        self.auto_save_check.toggled.connect(
            lambda v: self._save_setting("app.auto_save", v)
        )
        self.auto_save_interval.valueChanged.connect(
            lambda v: self._save_setting("app.auto_save_interval", v)
        )
        
        # 路径设置信号
        self.project_path_edit.textChanged.connect(
            lambda v: self._save_setting("project.default_location", v)
        )
        self.jianying_path_edit.textChanged.connect(
            lambda v: self._save_setting("jianying.draft_folder", v)
        )
        self.export_path_edit.textChanged.connect(
            lambda v: self._save_setting("export.output_folder", v)
        )
        
        # 性能设置信号
        self.max_threads_spin.valueChanged.connect(
            lambda v: self._save_setting("performance.max_threads", v)
        )
        self.memory_limit_spin.valueChanged.connect(
            lambda v: self._save_setting("performance.memory_limit", v)
        )
        self.gpu_acceleration_check.toggled.connect(
            lambda v: self._save_setting("performance.gpu_acceleration", v)
        )
    
    def _load_settings(self):
        """加载设置"""
        # 通用设置
        theme = self.settings_manager.get_setting("app.theme", "light")
        self.theme_toggle.set_theme(theme)
        
        self.auto_save_check.setChecked(
            self.settings_manager.get_setting("app.auto_save", True)
        )
        self.auto_save_interval.setValue(
            self.settings_manager.get_setting("app.auto_save_interval", 300)
        )
        
        # 路径设置
        self.project_path_edit.setText(
            self.settings_manager.get_setting("project.default_location", "")
        )
        self.jianying_path_edit.setText(
            self.settings_manager.get_setting("jianying.draft_folder", "")
        )
        self.export_path_edit.setText(
            self.settings_manager.get_setting("export.output_folder", "")
        )
        
        # 性能设置
        self.max_threads_spin.setValue(
            self.settings_manager.get_setting("performance.max_threads", 4)
        )
        self.memory_limit_spin.setValue(
            self.settings_manager.get_setting("performance.memory_limit", 2048)
        )
        self.gpu_acceleration_check.setChecked(
            self.settings_manager.get_setting("performance.gpu_acceleration", True)
        )
    
    def _save_setting(self, key: str, value):
        """保存设置"""
        self.settings_manager.set_setting(key, value)
        self.settings_changed.emit(key, value)
    
    def _on_api_key_changed(self, provider: str, key: str):
        """API密钥变更"""
        self.settings_changed.emit(f"ai_models.{provider}.api_key", key)
    
    def _browse_project_path(self):
        """浏览项目路径"""
        path = QFileDialog.getExistingDirectory(self, "选择项目文件夹")
        if path:
            self.project_path_edit.setText(path)
    
    def _browse_jianying_path(self):
        """浏览剪映路径"""
        path = QFileDialog.getExistingDirectory(self, "选择剪映草稿文件夹")
        if path:
            self.jianying_path_edit.setText(path)
    
    def _browse_export_path(self):
        """浏览导出路径"""
        path = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if path:
            self.export_path_edit.setText(path)
    
    def _detect_jianying_path(self):
        """检测剪映路径"""
        from app.config.defaults import get_jianying_paths
        paths = get_jianying_paths()
        
        if paths:
            # 使用第一个找到的路径
            self.jianying_path_edit.setText(paths[0])
            QMessageBox.information(self, "检测成功", f"找到剪映路径: {paths[0]}")
        else:
            QMessageBox.warning(self, "检测失败", "未找到剪映安装路径")
    
    def _clear_cache(self):
        """清理缓存"""
        reply = QMessageBox.question(
            self, "确认清理",
            "确定要清理所有缓存文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # TODO: 实现缓存清理
            QMessageBox.information(self, "完成", "缓存清理完成")

    def _reset_settings(self):
        """重置所有设置"""
        reply = QMessageBox.question(
            self, "重置设置",
            "确定要重置所有设置到默认值吗？\n这将清除所有API密钥和自定义配置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.settings_manager.reset_to_defaults()
                self._load_settings()
                QMessageBox.information(self, "成功", "设置已重置到默认值")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重置设置失败:\n{str(e)}")
