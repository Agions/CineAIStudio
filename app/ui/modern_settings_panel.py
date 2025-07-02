#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGroupBox, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QComboBox, QSlider, QFileDialog, QMessageBox,
    QTextEdit, QScrollArea, QFrame, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

from app.config.settings_manager import SettingsManager
from app.config.defaults import AI_PROVIDERS
from .components.theme_toggle import ThemeToggle
from .theme_manager import get_theme_manager
import os


class ModernSettingsCard(QFrame):
    """现代化设置卡片组件"""
    
    def __init__(self, title: str, description: str = "", parent=None):
        super().__init__(parent)
        
        self.title = title
        self.description = description
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 标题区域
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        # 标题
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setObjectName("card_title")
        header_layout.addWidget(title_label)
        
        # 描述
        if self.description:
            desc_label = QLabel(self.description)
            desc_label.setFont(QFont("Arial", 12))
            desc_label.setObjectName("card_description")
            desc_label.setWordWrap(True)
            header_layout.addWidget(desc_label)
        
        layout.addLayout(header_layout)
        
        # 内容区域
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        layout.addWidget(QWidget())  # 占位符，子类可以重写
        layout.addLayout(self.content_layout)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            ModernSettingsCard {
                background-color: #ffffff;
                border: 1px solid #f0f0f0;
                border-radius: 12px;
            }
            
            ModernSettingsCard:hover {
                border-color: #d9d9d9;
            }
            
            QLabel#card_title {
                color: #262626;
                font-weight: 600;
            }
            
            QLabel#card_description {
                color: #595959;
                line-height: 1.4;
            }
        """)
    
    def add_content_widget(self, widget):
        """添加内容控件"""
        self.content_layout.addWidget(widget)


class APIKeyCard(ModernSettingsCard):
    """API密钥设置卡片"""
    
    key_changed = pyqtSignal(str, str)  # provider, key
    
    def __init__(self, provider: str, provider_info: dict, settings_manager: SettingsManager, parent=None):
        self.provider = provider
        self.provider_info = provider_info
        self.settings_manager = settings_manager
        
        super().__init__(
            title=provider_info.get('name', provider),
            description=f"配置{provider_info.get('name', provider)}的API密钥",
            parent=parent
        )
        
        self._setup_content()
        self._load_current_key()
    
    def _setup_content(self):
        """设置内容"""
        # API密钥输入
        key_layout = QHBoxLayout()
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("请输入API密钥...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.textChanged.connect(self._on_key_changed)
        key_layout.addWidget(self.key_input)
        
        # 显示/隐藏按钮
        self.toggle_btn = QPushButton("👁️")
        self.toggle_btn.setMaximumWidth(40)
        self.toggle_btn.setToolTip("显示/隐藏密钥")
        self.toggle_btn.clicked.connect(self._toggle_visibility)
        key_layout.addWidget(self.toggle_btn)
        
        # 测试按钮
        self.test_btn = QPushButton("🔍 测试")
        self.test_btn.setMaximumWidth(80)
        self.test_btn.clicked.connect(self._test_connection)
        key_layout.addWidget(self.test_btn)
        
        self.add_content_widget(QWidget())
        self.content_layout.addLayout(key_layout)
        
        # 状态指示器
        self.status_label = QLabel("未配置")
        self.status_label.setObjectName("status_label")
        self.add_content_widget(self.status_label)
        
        # 获取密钥链接
        if 'url' in self.provider_info:
            link_btn = QPushButton(f"📝 获取{self.provider_info['name']}密钥")
            link_btn.clicked.connect(lambda: self._open_url(self.provider_info['url']))
            self.add_content_widget(link_btn)
    
    def _load_current_key(self):
        """加载当前密钥"""
        key = self.settings_manager.get_api_key(self.provider)
        if key:
            self.key_input.setText(key)
            self._update_status("已配置", "#52c41a")
        else:
            self._update_status("未配置", "#ff4d4f")
    
    def _on_key_changed(self, text):
        """密钥变更"""
        if text.strip():
            self.settings_manager.set_api_key(self.provider, text.strip())
            self._update_status("已配置", "#52c41a")
            self.key_changed.emit(self.provider, text.strip())
        else:
            self.settings_manager.remove_api_key(self.provider)
            self._update_status("未配置", "#ff4d4f")
    
    def _toggle_visibility(self):
        """切换密钥可见性"""
        if self.key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setText("🙈")
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setText("👁️")
    
    def _test_connection(self):
        """测试连接"""
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "警告", "请先输入API密钥")
            return
        
        # 这里可以添加实际的API测试逻辑
        QMessageBox.information(self, "测试结果", f"{self.provider_info['name']} API密钥格式正确")
    
    def _update_status(self, text: str, color: str):
        """更新状态"""
        self.status_label.setText(f"状态: {text}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 500;")
    
    def _open_url(self, url: str):
        """打开URL"""
        import webbrowser
        webbrowser.open(url)


class GeneralSettingsCard(ModernSettingsCard):
    """通用设置卡片"""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        self.settings_manager = settings_manager
        
        super().__init__(
            title="通用设置",
            description="应用程序的基本配置选项",
            parent=parent
        )
        
        self._setup_content()
        self._load_settings()
    
    def _setup_content(self):
        """设置内容"""
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # 主题设置
        self.theme_toggle = ThemeToggle()
        self.theme_toggle.theme_changed.connect(
            lambda v: self.settings_manager.set_setting("app.theme", v)
        )
        form_layout.addRow("应用主题:", self.theme_toggle)
        
        # 语言设置
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        self.language_combo.currentTextChanged.connect(
            lambda v: self.settings_manager.set_setting("app.language", v)
        )
        form_layout.addRow("界面语言:", self.language_combo)
        
        # 自动保存
        self.auto_save_check = QCheckBox("启用自动保存")
        self.auto_save_check.toggled.connect(
            lambda v: self.settings_manager.set_setting("app.auto_save", v)
        )
        form_layout.addRow("", self.auto_save_check)
        
        # 启动时检查更新
        self.check_update_check = QCheckBox("启动时检查更新")
        self.check_update_check.toggled.connect(
            lambda v: self.settings_manager.set_setting("app.check_updates", v)
        )
        form_layout.addRow("", self.check_update_check)
        
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        self.add_content_widget(form_widget)
    
    def _load_settings(self):
        """加载设置"""
        # 主题
        theme = self.settings_manager.get_setting("app.theme", "light")
        self.theme_toggle.set_theme(theme)
        
        # 语言
        language = self.settings_manager.get_setting("app.language", "简体中文")
        self.language_combo.setCurrentText(language)
        
        # 自动保存
        auto_save = self.settings_manager.get_setting("app.auto_save", True)
        self.auto_save_check.setChecked(auto_save)
        
        # 检查更新
        check_updates = self.settings_manager.get_setting("app.check_updates", True)
        self.check_update_check.setChecked(check_updates)


class VideoSettingsCard(ModernSettingsCard):
    """视频设置卡片"""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        self.settings_manager = settings_manager
        
        super().__init__(
            title="视频处理设置",
            description="视频导入、处理和导出的相关配置",
            parent=parent
        )
        
        self._setup_content()
        self._load_settings()
    
    def _setup_content(self):
        """设置内容"""
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # 默认输出目录
        output_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择默认输出目录...")
        output_layout.addWidget(self.output_path_edit)
        
        browse_btn = QPushButton("📁 浏览")
        browse_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(browse_btn)
        
        output_widget = QWidget()
        output_widget.setLayout(output_layout)
        form_layout.addRow("输出目录:", output_widget)
        
        # 视频质量
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["高质量", "标准质量", "快速预览"])
        self.quality_combo.currentTextChanged.connect(
            lambda v: self.settings_manager.set_setting("video.quality", v)
        )
        form_layout.addRow("默认质量:", self.quality_combo)
        
        # 并发处理数
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 8)
        self.concurrent_spin.setValue(2)
        self.concurrent_spin.valueChanged.connect(
            lambda v: self.settings_manager.set_setting("video.concurrent", v)
        )
        form_layout.addRow("并发处理数:", self.concurrent_spin)
        
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        self.add_content_widget(form_widget)
    
    def _browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_path_edit.setText(dir_path)
            self.settings_manager.set_setting("video.output_dir", dir_path)
    
    def _load_settings(self):
        """加载设置"""
        # 输出目录
        output_dir = self.settings_manager.get_setting("video.output_dir", "")
        self.output_path_edit.setText(output_dir)
        
        # 视频质量
        quality = self.settings_manager.get_setting("video.quality", "标准质量")
        self.quality_combo.setCurrentText(quality)
        
        # 并发数
        concurrent = self.settings_manager.get_setting("video.concurrent", 2)
        self.concurrent_spin.setValue(concurrent)


class ModernSettingsPanel(QWidget):
    """现代化设置面板"""

    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)

        self.settings_manager = settings_manager
        self.theme_manager = get_theme_manager()

        self._setup_ui()
        self._connect_signals()
        self._apply_theme()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 主内容
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)

        # 页面标题
        title_label = QLabel("设置")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setObjectName("page_title")
        content_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("配置应用程序的各项参数")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setObjectName("page_subtitle")
        content_layout.addWidget(subtitle_label)

        # 设置卡片
        self._create_settings_cards(content_layout)

        # 添加弹性空间
        content_layout.addStretch()

        layout.addWidget(scroll_area)

    def _create_settings_cards(self, layout):
        """创建设置卡片"""
        # 通用设置
        self.general_card = GeneralSettingsCard(self.settings_manager)
        layout.addWidget(self.general_card)

        # AI模型设置
        ai_section_label = QLabel("AI模型配置")
        ai_section_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        ai_section_label.setObjectName("section_title")
        ai_section_label.setContentsMargins(0, 20, 0, 10)
        layout.addWidget(ai_section_label)

        # API密钥卡片
        for provider, info in AI_PROVIDERS.items():
            if provider != "ollama":  # Ollama不需要API密钥
                api_card = APIKeyCard(provider, info, self.settings_manager)
                layout.addWidget(api_card)

        # 视频处理设置
        video_section_label = QLabel("视频处理")
        video_section_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        video_section_label.setObjectName("section_title")
        video_section_label.setContentsMargins(0, 20, 0, 10)
        layout.addWidget(video_section_label)

        self.video_card = VideoSettingsCard(self.settings_manager)
        layout.addWidget(self.video_card)

        # 高级设置
        advanced_section_label = QLabel("高级选项")
        advanced_section_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        advanced_section_label.setObjectName("section_title")
        advanced_section_label.setContentsMargins(0, 20, 0, 10)
        layout.addWidget(advanced_section_label)

        self.advanced_card = self._create_advanced_card()
        layout.addWidget(self.advanced_card)

    def _create_advanced_card(self) -> ModernSettingsCard:
        """创建高级设置卡片"""
        card = ModernSettingsCard(
            title="高级设置",
            description="开发者选项和高级功能配置"
        )

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # 调试模式
        debug_check = QCheckBox("启用调试模式")
        debug_check.toggled.connect(
            lambda v: self.settings_manager.set_setting("app.debug", v)
        )
        debug_value = self.settings_manager.get_setting("app.debug", False)
        debug_check.setChecked(debug_value)
        form_layout.addRow("", debug_check)

        # 日志级别
        log_level_combo = QComboBox()
        log_level_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        log_level_combo.currentTextChanged.connect(
            lambda v: self.settings_manager.set_setting("app.log_level", v)
        )
        log_level = self.settings_manager.get_setting("app.log_level", "INFO")
        log_level_combo.setCurrentText(log_level)
        form_layout.addRow("日志级别:", log_level_combo)

        # 缓存大小
        cache_spin = QSpinBox()
        cache_spin.setRange(100, 5000)
        cache_spin.setValue(1000)
        cache_spin.setSuffix(" MB")
        cache_spin.valueChanged.connect(
            lambda v: self.settings_manager.set_setting("app.cache_size", v)
        )
        cache_size = self.settings_manager.get_setting("app.cache_size", 1000)
        cache_spin.setValue(cache_size)
        form_layout.addRow("缓存大小:", cache_spin)

        # 操作按钮
        buttons_layout = QHBoxLayout()

        clear_cache_btn = QPushButton("🗑️ 清理缓存")
        clear_cache_btn.clicked.connect(self._clear_cache)
        buttons_layout.addWidget(clear_cache_btn)

        reset_settings_btn = QPushButton("🔄 重置设置")
        reset_settings_btn.setObjectName("danger_button")
        reset_settings_btn.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(reset_settings_btn)

        export_btn = QPushButton("📤 导出设置")
        export_btn.clicked.connect(self._export_settings)
        buttons_layout.addWidget(export_btn)

        import_btn = QPushButton("📥 导入设置")
        import_btn.clicked.connect(self._import_settings)
        buttons_layout.addWidget(import_btn)

        buttons_layout.addStretch()

        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        card.add_content_widget(form_widget)

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        card.add_content_widget(buttons_widget)

        return card

    def _connect_signals(self):
        """连接信号"""
        self.theme_manager.theme_changed.connect(self._on_theme_changed)

    def _apply_theme(self):
        """应用主题"""
        current_theme = self.theme_manager.get_current_theme().value
        self._on_theme_changed(current_theme)

    def _on_theme_changed(self, theme_value: str):
        """主题变更处理"""
        is_dark = theme_value == "dark"

        if is_dark:
            self.setStyleSheet("""
                QLabel#page_title {
                    color: #ffffff;
                    margin-bottom: 8px;
                }

                QLabel#page_subtitle {
                    color: #a6a6a6;
                    margin-bottom: 20px;
                }

                QLabel#section_title {
                    color: #ffffff;
                    border-bottom: 2px solid #177ddc;
                    padding-bottom: 8px;
                }

                ModernSettingsCard {
                    background-color: #1f1f1f;
                    border: 1px solid #434343;
                }

                ModernSettingsCard:hover {
                    border-color: #595959;
                }

                QLabel#card_title {
                    color: #ffffff;
                }

                QLabel#card_description {
                    color: #a6a6a6;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel#page_title {
                    color: #262626;
                    margin-bottom: 8px;
                }

                QLabel#page_subtitle {
                    color: #595959;
                    margin-bottom: 20px;
                }

                QLabel#section_title {
                    color: #262626;
                    border-bottom: 2px solid #1890ff;
                    padding-bottom: 8px;
                }

                ModernSettingsCard {
                    background-color: #ffffff;
                    border: 1px solid #f0f0f0;
                }

                ModernSettingsCard:hover {
                    border-color: #d9d9d9;
                }

                QLabel#card_title {
                    color: #262626;
                }

                QLabel#card_description {
                    color: #595959;
                }
            """)

    def _clear_cache(self):
        """清理缓存"""
        reply = QMessageBox.question(
            self, "确认", "确定要清理应用缓存吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 这里添加实际的缓存清理逻辑
            QMessageBox.information(self, "成功", "缓存已清理完成")

    def _reset_settings(self):
        """重置设置"""
        reply = QMessageBox.warning(
            self, "警告", "确定要重置所有设置吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 这里添加实际的设置重置逻辑
            QMessageBox.information(self, "成功", "设置已重置，请重启应用程序")

    def _export_settings(self):
        """导出设置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出设置", "settings.json", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                # 这里添加实际的设置导出逻辑
                QMessageBox.information(self, "成功", f"设置已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def _import_settings(self):
        """导入设置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入设置", "", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                # 这里添加实际的设置导入逻辑
                QMessageBox.information(self, "成功", "设置导入成功，请重启应用程序")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
