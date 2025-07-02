#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QLineEdit, QPushButton, QComboBox,
    QCheckBox, QLabel, QTextEdit, QProgressBar, QListWidget,
    QListWidgetItem, QMessageBox, QFrame, QScrollArea,
    QDialogButtonBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from app.config.settings_manager import SettingsManager
from app.ai import AIManager
from app.ai.ollama_manager import OllamaManager
from app.config.defaults import AI_PROVIDERS


class OllamaModelWidget(QWidget):
    """Ollama模型管理控件"""
    
    def __init__(self, model_info: dict, is_installed: bool = False):
        super().__init__()
        
        self.model_info = model_info
        self.is_installed = is_installed
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 模型信息
        info_layout = QVBoxLayout()
        
        # 模型名称
        name_label = QLabel(self.model_info["display_name"])
        name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        info_layout.addWidget(name_label)
        
        # 模型描述
        desc_label = QLabel(self.model_info["description"])
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        # 模型大小
        size_label = QLabel(f"大小: {self.model_info['size']}")
        size_label.setStyleSheet("color: #666;")
        info_layout.addWidget(size_label)
        
        layout.addLayout(info_layout, 1)
        
        # 操作按钮
        if self.is_installed:
            self.action_btn = QPushButton("删除")
            self.action_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; }")
        else:
            self.action_btn = QPushButton("安装")
            self.action_btn.setStyleSheet("QPushButton { background-color: #51cf66; }")
        
        layout.addWidget(self.action_btn)
    
    def set_installed(self, installed: bool):
        """设置安装状态"""
        self.is_installed = installed
        if installed:
            self.action_btn.setText("删除")
            self.action_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; }")
        else:
            self.action_btn.setText("安装")
            self.action_btn.setStyleSheet("QPushButton { background-color: #51cf66; }")


class AIProviderWidget(QWidget):
    """AI提供商配置控件"""
    
    settings_changed = pyqtSignal(str, dict)  # provider, settings
    
    def __init__(self, provider: str, provider_info: dict, settings_manager: SettingsManager):
        super().__init__()
        
        self.provider = provider
        self.provider_info = provider_info
        self.settings_manager = settings_manager
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 提供商标题
        title_label = QLabel(self.provider_info["display_name"])
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 配置表单
        form_group = QGroupBox("配置")
        form_layout = QFormLayout(form_group)
        
        # 启用开关
        self.enabled_check = QCheckBox("启用此模型")
        form_layout.addRow("", self.enabled_check)
        
        # API密钥
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("输入API密钥")
        form_layout.addRow("API密钥:", self.api_key_edit)
        
        # API地址
        self.api_url_edit = QLineEdit()
        self.api_url_edit.setPlaceholderText("API服务地址")
        form_layout.addRow("API地址:", self.api_url_edit)
        
        # 模型选择
        self.model_combo = QComboBox()
        if "models" in self.provider_info:
            self.model_combo.addItems(self.provider_info["models"])
        form_layout.addRow("模型:", self.model_combo)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)
        
        # 最大令牌数
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 32000)
        self.max_tokens_spin.setValue(4096)
        advanced_layout.addRow("最大令牌数:", self.max_tokens_spin)
        
        # 温度
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.7)
        advanced_layout.addRow("温度:", self.temperature_spin)
        
        # Top-p
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.1)
        self.top_p_spin.setValue(0.9)
        advanced_layout.addRow("Top-p:", self.top_p_spin)
        
        layout.addWidget(form_group)
        layout.addWidget(advanced_group)
        
        # 连接信号
        self.enabled_check.toggled.connect(self._on_settings_changed)
        self.api_key_edit.textChanged.connect(self._on_settings_changed)
        self.api_url_edit.textChanged.connect(self._on_settings_changed)
        self.model_combo.currentTextChanged.connect(self._on_settings_changed)
        self.max_tokens_spin.valueChanged.connect(self._on_settings_changed)
        self.temperature_spin.valueChanged.connect(self._on_settings_changed)
        self.top_p_spin.valueChanged.connect(self._on_settings_changed)
    
    def _load_settings(self):
        """加载设置"""
        config = self.settings_manager.get_setting(f"ai_models.{self.provider}", {})
        
        self.enabled_check.setChecked(config.get("enabled", False))
        self.api_url_edit.setText(config.get("api_url", ""))
        self.max_tokens_spin.setValue(config.get("max_tokens", 4096))
        self.temperature_spin.setValue(config.get("temperature", 0.7))
        self.top_p_spin.setValue(config.get("top_p", 0.9))
        
        # 加载API密钥
        api_key = self.settings_manager.get_api_key(self.provider)
        if api_key:
            self.api_key_edit.setText(api_key)
        
        # 设置默认模型
        model = config.get("model", "")
        if model and self.model_combo.findText(model) >= 0:
            self.model_combo.setCurrentText(model)
    
    def _on_settings_changed(self):
        """设置变更处理"""
        settings = {
            "enabled": self.enabled_check.isChecked(),
            "api_url": self.api_url_edit.text().strip(),
            "model": self.model_combo.currentText(),
            "max_tokens": self.max_tokens_spin.value(),
            "temperature": self.temperature_spin.value(),
            "top_p": self.top_p_spin.value()
        }
        
        # 保存API密钥
        api_key = self.api_key_edit.text().strip()
        if api_key:
            self.settings_manager.set_api_key(self.provider, api_key)
        
        self.settings_changed.emit(self.provider, settings)


class AISettingsDialog(QDialog):
    """AI设置对话框"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_manager: SettingsManager, ai_manager: AIManager, parent=None):
        super().__init__(parent)
        
        self.settings_manager = settings_manager
        self.ai_manager = ai_manager
        self.ollama_manager = OllamaManager()
        
        self.setWindowTitle("AI模型设置")
        self.setModal(True)
        self.resize(800, 600)
        
        self._setup_ui()
        self._connect_signals()
        
        # 初始化Ollama管理器
        asyncio.create_task(self.ollama_manager.initialize())
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 云端模型选项卡
        self.cloud_tab = self._create_cloud_models_tab()
        self.tab_widget.addTab(self.cloud_tab, "云端模型")
        
        # 本地模型选项卡
        self.local_tab = self._create_local_models_tab()
        self.tab_widget.addTab(self.local_tab, "本地模型")
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_cloud_models_tab(self) -> QWidget:
        """创建云端模型选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 为每个AI提供商创建配置控件
        self.provider_widgets = {}
        for provider, info in AI_PROVIDERS.items():
            if provider != "ollama":  # Ollama在本地模型选项卡中处理
                widget = AIProviderWidget(provider, info, self.settings_manager)
                widget.settings_changed.connect(self._on_provider_settings_changed)
                self.provider_widgets[provider] = widget
                scroll_layout.addWidget(widget)
                
                # 添加分隔线
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                scroll_layout.addWidget(line)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_local_models_tab(self) -> QWidget:
        """创建本地模型选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Ollama状态
        status_group = QGroupBox("Ollama状态")
        status_layout = QVBoxLayout(status_group)
        
        self.ollama_status_label = QLabel("检查中...")
        status_layout.addWidget(self.ollama_status_label)
        
        # 启动按钮
        button_layout = QHBoxLayout()
        self.start_ollama_btn = QPushButton("启动Ollama")
        self.start_ollama_btn.clicked.connect(self._start_ollama)
        button_layout.addWidget(self.start_ollama_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._refresh_ollama_status)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        status_layout.addLayout(button_layout)
        
        layout.addWidget(status_group)
        
        # 模型管理
        models_group = QGroupBox("模型管理")
        models_layout = QVBoxLayout(models_group)
        
        # 模型列表
        self.model_list_widget = QListWidget()
        models_layout.addWidget(self.model_list_widget)
        
        layout.addWidget(models_group)
        
        return tab
    
    def _connect_signals(self):
        """连接信号"""
        self.ollama_manager.service_status_changed.connect(self._on_ollama_status_changed)
        self.ollama_manager.model_list_updated.connect(self._on_model_list_updated)
        self.ollama_manager.model_pulled.connect(self._on_model_pulled)
        self.ollama_manager.model_deleted.connect(self._on_model_deleted)
    
    def _on_provider_settings_changed(self, provider: str, settings: dict):
        """提供商设置变更"""
        # 保存设置
        for key, value in settings.items():
            self.settings_manager.set_setting(f"ai_models.{provider}.{key}", value)
        
        # 通知AI管理器更新配置
        self.ai_manager.update_model_config(provider, settings)
    
    def _on_ollama_status_changed(self, is_running: bool):
        """Ollama状态变更"""
        if is_running:
            self.ollama_status_label.setText("✅ Ollama服务正在运行")
            self.start_ollama_btn.setText("重启Ollama")
        else:
            self.ollama_status_label.setText("❌ Ollama服务未运行")
            self.start_ollama_btn.setText("启动Ollama")
    
    def _on_model_list_updated(self, models: list):
        """模型列表更新"""
        self.model_list_widget.clear()
        
        # 添加推荐模型
        recommended = self.ollama_manager.get_recommended_models()
        for model_info in recommended:
            is_installed = model_info["name"] in models
            widget = OllamaModelWidget(model_info, is_installed)
            
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.model_list_widget.addItem(item)
            self.model_list_widget.setItemWidget(item, widget)
            
            # 连接按钮信号
            if is_installed:
                widget.action_btn.clicked.connect(
                    lambda checked, name=model_info["name"]: self._delete_model(name)
                )
            else:
                widget.action_btn.clicked.connect(
                    lambda checked, name=model_info["name"]: self._pull_model(name)
                )
    
    def _start_ollama(self):
        """启动Ollama"""
        if self.ollama_manager.start_ollama_service():
            QMessageBox.information(self, "启动成功", "Ollama服务启动中，请稍等...")
            QTimer.singleShot(3000, self._refresh_ollama_status)
        else:
            QMessageBox.warning(self, "启动失败", "无法启动Ollama服务，请检查安装")
    
    def _refresh_ollama_status(self):
        """刷新Ollama状态"""
        asyncio.create_task(self.ollama_manager.check_service_status())
    
    def _pull_model(self, model_name: str):
        """拉取模型"""
        reply = QMessageBox.question(
            self, "确认下载",
            f"确定要下载模型 {model_name} 吗？这可能需要一些时间。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            asyncio.create_task(self.ollama_manager.pull_model(model_name))
    
    def _delete_model(self, model_name: str):
        """删除模型"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模型 {model_name} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            asyncio.create_task(self.ollama_manager.delete_model(model_name))
    
    def _on_model_pulled(self, model_name: str, success: bool):
        """模型拉取完成"""
        if success:
            QMessageBox.information(self, "下载完成", f"模型 {model_name} 下载完成")
        else:
            QMessageBox.warning(self, "下载失败", f"模型 {model_name} 下载失败")
        
        # 刷新模型列表
        asyncio.create_task(self.ollama_manager.refresh_model_list())
    
    def _on_model_deleted(self, model_name: str, success: bool):
        """模型删除完成"""
        if success:
            QMessageBox.information(self, "删除完成", f"模型 {model_name} 删除完成")
        else:
            QMessageBox.warning(self, "删除失败", f"模型 {model_name} 删除失败")
        
        # 刷新模型列表
        asyncio.create_task(self.ollama_manager.refresh_model_list())
    
    def accept(self):
        """确认设置"""
        self.settings_changed.emit()
        super().accept()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 关闭Ollama管理器
        asyncio.create_task(self.ollama_manager.close())
        super().closeEvent(event)
