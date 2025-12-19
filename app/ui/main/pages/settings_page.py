#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设置页面 - macOS 设计系统优化版
重构为使用标准化组件，零内联样式
"""

import os
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QLabel,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.core.application import Application
from app.core.logger import Logger
from app.core.icon_manager import get_icon
from .base_page import BasePage

# 导入标准化 macOS 组件
from app.ui.common.macOS_components import (
    MacCard, MacPrimaryButton, MacSecondaryButton, MacDangerButton,
    MacIconButton, MacTitleLabel, MacLabel, MacBadge,
    MacPageToolbar, MacScrollArea, MacEmptyState
)


class ConfigRow(QWidget):
    """配置行组件 - 带标签和输入控件"""

    def __init__(self, label: str, input_widget, parent=None):
        super().__init__(parent)
        self.setProperty("class", "config-row")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # 标签
        label_widget = MacLabel(label, "text-sm text-bold")
        layout.addWidget(label_widget)

        # 输入控件
        layout.addWidget(input_widget, 1)

        # 如果是 Combo 或 SpinBox，设置样式
        if isinstance(input_widget, (QComboBox, QSpinBox)):
            input_widget.setProperty("class", "input config-input")


class GroupCard(MacCard):
    """分组卡片容器"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card group-card")

        self.title = MacTitleLabel(title, 6)
        self.layout().addWidget(self.title)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        self.layout().addLayout(self.content_layout)

    def add_row(self, label: str, widget):
        """添加配置行"""
        row = ConfigRow(label, widget)
        self.content_layout.addWidget(row)


class AIConfigPanel(QWidget):
    """AI配置面板 - macOS 设计系统"""

    config_changed = pyqtSignal(str, object)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")

        self.setProperty("class", "panel config-panel")
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 滚动区域
        scroll = MacScrollArea()
        scroll.setProperty("class", "scroll-area config-scroll")

        content = QWidget()
        content.setProperty("class", "section-content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # 模型配置
        model_group = GroupCard("模型配置")

        self.model_type_combo = QComboBox()
        self.model_type_combo.addItems(["GPT-4", "GPT-3.5", "Claude", "Gemini", "本地模型"])
        model_group.add_row("模型类型:", self.model_type_combo)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("输入API密钥")
        model_group.add_row("API密钥:", self.api_key_edit)

        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("本地模型路径")
        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_path_edit, 1)
        browse_btn = MacSecondaryButton("浏览")
        browse_btn.clicked.connect(self._browse_model_path)
        model_layout.addWidget(browse_btn)

        # 手动添加为内嵌布局
        row = QWidget()
        row.setProperty("class", "config-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 8, 12, 8)
        row_layout.setSpacing(8)
        row_layout.addWidget(MacLabel("模型路径:", "text-sm text-bold"))
        row_layout.addLayout(model_layout)
        model_group.content_layout.addWidget(row)

        content_layout.addWidget(model_group)

        # 功能配置
        feature_group = GroupCard("功能配置")

        self.ai_enabled_check = QCheckBox("启用AI功能")
        feature_group.content_layout.addWidget(self._create_checkbox(self.ai_enabled_check))

        self.auto_subtitle_check = QCheckBox("自动字幕")
        feature_group.content_layout.addWidget(self._create_checkbox(self.auto_subtitle_check))

        self.smart_editing_check = QCheckBox("智能剪辑")
        feature_group.content_layout.addWidget(self._create_checkbox(self.smart_editing_check))

        self.scene_detection_check = QCheckBox("场景检测")
        feature_group.content_layout.addWidget(self._create_checkbox(self.scene_detection_check))

        content_layout.addWidget(feature_group)

        # 性能配置
        perf_group = GroupCard("性能配置")

        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 32)
        self.batch_size_spin.setValue(8)
        perf_group.add_row("批处理大小:", self.batch_size_spin)

        self.precision_combo = QComboBox()
        self.precision_combo.addItems(["FP32", "FP16", "INT8"])
        self.precision_combo.setCurrentText("FP16")
        perf_group.add_row("推理精度:", self.precision_combo)

        self.gpu_memory_spin = QSpinBox()
        self.gpu_memory_spin.setRange(1, 32)
        self.gpu_memory_spin.setValue(8)
        perf_group.add_row("GPU内存(GB):", self.gpu_memory_spin)

        content_layout.addWidget(perf_group)

        # 按钮区域
        btn_group = MacCard()
        btn_group.setProperty("class", "card action-group")
        btn_layout = QHBoxLayout(btn_group.layout())
        btn_layout.setContentsMargins(12, 12, 12, 12)

        btn_layout.addStretch()

        apply_btn = MacPrimaryButton("应用")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)

        reset_btn = MacSecondaryButton("重置")
        reset_btn.clicked.connect(self._reset_settings)
        btn_layout.addWidget(reset_btn)

        content_layout.addWidget(btn_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_checkbox(self, checkbox):
        """创建带样式的复选框容器"""
        container = QWidget()
        container.setProperty("class", "checkbox-row")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 8, 12, 8)

        checkbox.setProperty("class", "checkbox")
        layout.addWidget(checkbox)

        return container

    def _browse_model_path(self):
        """浏览模型路径"""
        path = QFileDialog.getExistingDirectory(self, "选择模型路径", os.path.expanduser("~"))
        if path:
            self.model_path_edit.setText(path)

    def _load_settings(self):
        """加载设置"""
        try:
            settings = self.config_manager.get_settings()
            ai_config = settings.get("ai_config", {})

            self.model_type_combo.setCurrentText(ai_config.get("model_type", "GPT-4"))
            self.api_key_edit.setText(ai_config.get("api_key", ""))
            self.model_path_edit.setText(ai_config.get("model_path", ""))

            self.ai_enabled_check.setChecked(ai_config.get("enabled", True))
            self.auto_subtitle_check.setChecked(ai_config.get("auto_subtitle", True))
            self.smart_editing_check.setChecked(ai_config.get("smart_editing", True))
            self.scene_detection_check.setChecked(ai_config.get("scene_detection", True))

            perf_config = ai_config.get("performance", {})
            self.batch_size_spin.setValue(perf_config.get("batch_size", 8))
            self.precision_combo.setCurrentText(perf_config.get("precision", "FP16"))
            self.gpu_memory_spin.setValue(perf_config.get("gpu_memory_limit", 8))

        except Exception as e:
            self.logger.error(f"加载AI配置失败: {e}")

    def _apply_settings(self):
        """应用设置"""
        try:
            settings = self.config_manager.get_settings()
            ai_config = settings.get("ai_config", {})

            ai_config.update({
                "model_type": self.model_type_combo.currentText(),
                "api_key": self.api_key_edit.text(),
                "model_path": self.model_path_edit.text(),
                "enabled": self.ai_enabled_check.isChecked(),
                "auto_subtitle": self.auto_subtitle_check.isChecked(),
                "smart_editing": self.smart_editing_check.isChecked(),
                "scene_detection": self.scene_detection_check.isChecked(),
                "performance": {
                    "batch_size": self.batch_size_spin.value(),
                    "precision": self.precision_combo.currentText(),
                    "gpu_memory_limit": self.gpu_memory_spin.value()
                }
            })

            settings["ai_config"] = ai_config
            self.config_manager.update_settings(settings)

            self.config_changed.emit("ai_config", ai_config)
            QMessageBox.information(self, "成功", "AI配置已保存")

        except Exception as e:
            self.logger.error(f"应用AI配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")

    def _reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self, "确认重置", "确定要重置AI配置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.model_type_combo.setCurrentText("GPT-4")
            self.api_key_edit.setText("")
            self.model_path_edit.setText("")
            self.ai_enabled_check.setChecked(True)
            self.auto_subtitle_check.setChecked(True)
            self.smart_editing_check.setChecked(True)
            self.scene_detection_check.setChecked(True)
            self.batch_size_spin.setValue(8)
            self.precision_combo.setCurrentText("FP16")
            self.gpu_memory_spin.setValue(8)
            self._apply_settings()


class ChineseAIConfigPanel(QWidget):
    """国产AI配置面板 - macOS 设计系统"""

    config_changed = pyqtSignal(str, object)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")

        self.setProperty("class", "panel config-panel")
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = MacScrollArea()
        scroll.setProperty("class", "scroll-area config-scroll")

        content = QWidget()
        content.setProperty("class", "section-content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # 模型选择
        model_group = GroupCard("国产AI模型")

        self.model_type_combo = QComboBox()
        self.model_type_combo.addItems([
            "文心一言(ERNIE)", "通义千问(Qwen)", "智谱清言(ChatGLM)",
            "讯飞星火", "百川大模型", "月之暗面(LLaMA)", "其他国产模型"
        ])
        model_group.add_row("模型类型:", self.model_type_combo)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("输入API密钥")
        model_group.add_row("API密钥:", self.api_key_edit)

        self.api_endpoint_edit = QLineEdit()
        self.api_endpoint_edit.setPlaceholderText("https://api.example.com/v1/chat/completions")
        model_group.add_row("API端点:", self.api_endpoint_edit)

        content_layout.addWidget(model_group)

        # 功能开关
        feature_group = GroupCard("功能开关")

        self.ernie_enabled_check = QCheckBox("启用文心一言")
        feature_group.content_layout.addWidget(self._create_checkbox(self.ernie_enabled_check))

        self.qwen_enabled_check = QCheckBox("启用通义千问")
        feature_group.content_layout.addWidget(self._create_checkbox(self.qwen_enabled_check))

        self.chatglm_enabled_check = QCheckBox("启用智谱清言")
        feature_group.content_layout.addWidget(self._create_checkbox(self.chatglm_enabled_check))

        self.xunfei_enabled_check = QCheckBox("启用讯飞星火")
        feature_group.content_layout.addWidget(self._create_checkbox(self.xunfei_enabled_check))

        self.baichuan_enabled_check = QCheckBox("启用百川大模型")
        feature_group.content_layout.addWidget(self._create_checkbox(self.baichuan_enabled_check))

        self.llama_enabled_check = QCheckBox("启用月之暗面")
        feature_group.content_layout.addWidget(self._create_checkbox(self.llama_enabled_check))

        content_layout.addWidget(feature_group)

        # 性能配置
        perf_group = GroupCard("性能配置")

        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 32)
        self.batch_size_spin.setValue(4)
        perf_group.add_row("批处理大小:", self.batch_size_spin)

        self.precision_combo = QComboBox()
        self.precision_combo.addItems(["FP32", "FP16", "INT8"])
        self.precision_combo.setCurrentText("FP16")
        perf_group.add_row("推理精度:", self.precision_combo)

        self.gpu_memory_spin = QSpinBox()
        self.gpu_memory_spin.setRange(1, 32)
        self.gpu_memory_spin.setValue(4)
        perf_group.add_row("GPU内存(GB):", self.gpu_memory_spin)

        content_layout.addWidget(perf_group)

        # 按钮
        btn_group = MacCard()
        btn_group.setProperty("class", "card action-group")
        btn_layout = QHBoxLayout(btn_group.layout())
        btn_layout.setContentsMargins(12, 12, 12, 12)

        test_btn = MacSecondaryButton("测试连接")
        btn_layout.addWidget(test_btn)
        btn_layout.addStretch()

        apply_btn = MacPrimaryButton("应用")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)

        reset_btn = MacSecondaryButton("重置")
        reset_btn.clicked.connect(self._reset_settings)
        btn_layout.addWidget(reset_btn)

        content_layout.addWidget(btn_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_checkbox(self, checkbox):
        widget = QWidget()
        widget.setProperty("class", "checkbox-row")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        checkbox.setProperty("class", "checkbox")
        layout.addWidget(checkbox)
        return widget

    def _load_settings(self):
        try:
            settings = self.config_manager.get_settings()
            config = settings.get("chinese_ai_config", {})

            self.model_type_combo.setCurrentText(config.get("model_type", "文心一言(ERNIE)"))
            self.api_key_edit.setText(config.get("api_key", ""))
            self.api_endpoint_edit.setText(config.get("api_endpoint", ""))

            enabled = config.get("enabled_models", [])
            self.ernie_enabled_check.setChecked("ernie" in enabled)
            self.qwen_enabled_check.setChecked("qwen" in enabled)
            self.chatglm_enabled_check.setChecked("chatglm" in enabled)
            self.xunfei_enabled_check.setChecked("xunfei" in enabled)
            self.baichuan_enabled_check.setChecked("baichuan" in enabled)
            self.llama_enabled_check.setChecked("llama" in enabled)

            perf = config.get("performance", {})
            self.batch_size_spin.setValue(perf.get("batch_size", 4))
            self.precision_combo.setCurrentText(perf.get("precision", "FP16"))
            self.gpu_memory_spin.setValue(perf.get("gpu_memory_limit", 4))

        except Exception as e:
            self.logger.error(f"加载国产AI配置失败: {e}")

    def _apply_settings(self):
        try:
            settings = self.config_manager.get_settings()
            config = settings.get("chinese_ai_config", {})

            enabled_models = []
            if self.ernie_enabled_check.isChecked(): enabled_models.append("ernie")
            if self.qwen_enabled_check.isChecked(): enabled_models.append("qwen")
            if self.chatglm_enabled_check.isChecked(): enabled_models.append("chatglm")
            if self.xunfei_enabled_check.isChecked(): enabled_models.append("xunfei")
            if self.baichuan_enabled_check.isChecked(): enabled_models.append("baichuan")
            if self.llama_enabled_check.isChecked(): enabled_models.append("llama")

            config.update({
                "model_type": self.model_type_combo.currentText(),
                "api_key": self.api_key_edit.text(),
                "api_endpoint": self.api_endpoint_edit.text(),
                "enabled_models": enabled_models,
                "performance": {
                    "batch_size": self.batch_size_spin.value(),
                    "precision": self.precision_combo.currentText(),
                    "gpu_memory_limit": self.gpu_memory_spin.value()
                }
            })

            settings["chinese_ai_config"] = config
            self.config_manager.update_settings(settings)

            self.config_changed.emit("chinese_ai_config", config)
            QMessageBox.information(self, "成功", "国产AI配置已保存")

        except Exception as e:
            self.logger.error(f"应用国产AI配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")

    def _reset_settings(self):
        reply = QMessageBox.question(
            self, "确认重置", "确定要重置国产AI配置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.model_type_combo.setCurrentText("文心一言(ERNIE)")
            self.api_key_edit.setText("")
            self.api_endpoint_edit.setText("")
            self.ernie_enabled_check.setChecked(True)
            self.qwen_enabled_check.setChecked(False)
            self.chatglm_enabled_check.setChecked(False)
            self.xunfei_enabled_check.setChecked(False)
            self.baichuan_enabled_check.setChecked(False)
            self.llama_enabled_check.setChecked(False)
            self.batch_size_spin.setValue(4)
            self.precision_combo.setCurrentText("FP16")
            self.gpu_memory_spin.setValue(4)
            self._apply_settings()

    def refresh(self):
        self._load_settings()


class PathConfigPanel(QWidget):
    """路径配置面板 - macOS 设计系统"""

    config_changed = pyqtSignal(str, object)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")

        self.setProperty("class", "panel config-panel")
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = MacScrollArea()
        scroll.setProperty("class", "scroll-area config-scroll")

        content = QWidget()
        content.setProperty("class", "section-content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # 工作路径
        work_group = GroupCard("工作路径")

        self.project_path_edit = self._create_path_input(work_group, "项目默认路径:")
        self.media_path_edit = self._create_path_input(work_group, "媒体文件路径:")
        self.temp_path_edit = self._create_path_input(work_group, "临时文件路径:")
        self.export_path_edit = self._create_path_input(work_group, "导出路径:")

        content_layout.addWidget(work_group)

        # AI模型路径
        ai_group = GroupCard("AI模型路径")

        self.ai_model_path_edit = self._create_path_input(ai_group, "模型存储路径:")
        self.ai_cache_path_edit = self._create_path_input(ai_group, "缓存路径:")

        content_layout.addWidget(ai_group)

        # 按钮
        btn_group = MacCard()
        btn_group.setProperty("class", "card action-group")
        btn_layout = QHBoxLayout(btn_group.layout())
        btn_layout.setContentsMargins(12, 12, 12, 12)

        verify_btn = MacSecondaryButton("验证路径")
        verify_btn.clicked.connect(self._verify_paths)
        btn_layout.addWidget(verify_btn)

        apply_btn = MacPrimaryButton("应用")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addStretch()
        btn_layout.addWidget(apply_btn)

        content_layout.addWidget(btn_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_path_input(self, group, label):
        """创建路径输入行"""
        edit = QLineEdit()
        edit.setPlaceholderText("请选择路径...")

        row = QWidget()
        row.setProperty("class", "config-row")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        layout.addWidget(MacLabel(label, "text-sm text-bold"))
        layout.addWidget(edit, 1)

        browse_btn = MacSecondaryButton("浏览")
        browse_btn.clicked.connect(lambda: self._browse_path(edit))
        layout.addWidget(browse_btn)

        group.content_layout.addWidget(row)
        return edit

    def _browse_path(self, edit):
        path = QFileDialog.getExistingDirectory(self, "选择路径", edit.text() or os.path.expanduser("~"))
        if path:
            edit.setText(path)

    def _verify_paths(self):
        """验证路径"""
        try:
            paths = {
                "项目路径": self.project_path_edit.text(),
                "媒体路径": self.media_path_edit.text(),
                "临时路径": self.temp_path_edit.text(),
                "导出路径": self.export_path_edit.text(),
                "模型路径": self.ai_model_path_edit.text(),
                "缓存路径": self.ai_cache_path_edit.text()
            }

            results = ["验证结果:"]
            for name, path in paths.items():
                if not path:
                    results.append(f"❌ {name}: 未设置")
                elif not os.path.exists(path):
                    results.append(f"❌ {name}: 不存在")
                else:
                    results.append(f"✅ {name}: 正常")

            QMessageBox.information(self, "路径验证", "\n".join(results))

        except Exception as e:
            self.logger.error(f"验证路径失败: {e}")

    def _load_settings(self):
        try:
            settings = self.config_manager.get_settings()
            config = settings.get("path_config", {})

            self.project_path_edit.setText(config.get("project_path", ""))
            self.media_path_edit.setText(config.get("media_path", ""))
            self.temp_path_edit.setText(config.get("temp_path", ""))
            self.export_path_edit.setText(config.get("export_path", ""))
            self.ai_model_path_edit.setText(config.get("ai_model_path", ""))
            self.ai_cache_path_edit.setText(config.get("ai_cache_path", ""))

        except Exception as e:
            self.logger.error(f"加载路径配置失败: {e}")

    def _apply_settings(self):
        try:
            settings = self.config_manager.get_settings()
            config = settings.get("path_config", {})

            config.update({
                "project_path": self.project_path_edit.text(),
                "media_path": self.media_path_edit.text(),
                "temp_path": self.temp_path_edit.text(),
                "export_path": self.export_path_edit.text(),
                "ai_model_path": self.ai_model_path_edit.text(),
                "ai_cache_path": self.ai_cache_path_edit.text()
            })

            settings["path_config"] = config
            self.config_manager.update_settings(settings)

            self.config_changed.emit("path_config", config)
            QMessageBox.information(self, "成功", "路径配置已保存")

        except Exception as e:
            self.logger.error(f"应用路径配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")


class ThemeConfigPanel(QWidget):
    """主题配置面板 - macOS 设计系统"""

    config_changed = pyqtSignal(str, object)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")

        self.setProperty("class", "panel config-panel")
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = MacScrollArea()
        scroll.setProperty("class", "scroll-area config-scroll")

        content = QWidget()
        content.setProperty("class", "section-content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # 主题选择
        theme_group = GroupCard("主题选择")

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["深色主题", "浅色主题", "蓝色主题", "绿色主题", "紫色主题"])
        self.theme_combo.setCurrentText("深色主题")
        theme_group.add_row("预设主题:", self.theme_combo)

        content_layout.addWidget(theme_group)

        # 界面配置
        ui_group = GroupCard("界面配置")

        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Microsoft YaHei", "SimSun", "Times New Roman"])
        self.font_combo.setCurrentText("Arial")
        ui_group.add_row("字体:", self.font_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        ui_group.add_row("字体大小:", self.font_size_spin)

        self.scale_slider = QSpinBox()
        self.scale_slider.setRange(50, 200)
        self.scale_slider.setSuffix("%")
        self.scale_slider.setValue(100)
        ui_group.add_row("界面缩放:", self.scale_slider)

        content_layout.addWidget(ui_group)

        # 高级设置
        advanced_group = GroupCard("高级设置")

        self.animation_check = QCheckBox("启用界面动画")
        advanced_group.content_layout.addWidget(self._create_checkbox(self.animation_check))

        self.transparency_check = QCheckBox("启用透明效果")
        advanced_group.content_layout.addWidget(self._create_checkbox(self.transparency_check))

        self.glass_check = QCheckBox("启用毛玻璃效果")
        advanced_group.content_layout.addWidget(self._create_checkbox(self.glass_check))

        self.rounded_check = QCheckBox("启用圆角")
        advanced_group.content_layout.addWidget(self._create_checkbox(self.rounded_check))

        content_layout.addWidget(advanced_group)

        # 按钮
        btn_group = MacCard()
        btn_group.setProperty("class", "card action-group")
        btn_layout = QHBoxLayout(btn_group.layout())
        btn_layout.setContentsMargins(12, 12, 12, 12)

        apply_btn = MacPrimaryButton("应用")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addStretch()
        btn_layout.addWidget(apply_btn)

        content_layout.addWidget(btn_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_checkbox(self, checkbox):
        widget = QWidget()
        widget.setProperty("class", "checkbox-row")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        checkbox.setProperty("class", "checkbox")
        layout.addWidget(checkbox)
        return widget

    def _load_settings(self):
        try:
            settings = self.config_manager.get_settings()
            config = settings.get("theme_config", {})

            self.theme_combo.setCurrentText(config.get("theme", "深色主题"))

            ui = config.get("ui_settings", {})
            self.font_combo.setCurrentText(ui.get("font", "Arial"))
            self.font_size_spin.setValue(ui.get("font_size", 12))
            self.scale_slider.setValue(ui.get("scale", 100))

            advanced = config.get("advanced_settings", {})
            self.animation_check.setChecked(advanced.get("animation", True))
            self.transparency_check.setChecked(advanced.get("transparency", False))
            self.glass_check.setChecked(advanced.get("glass", False))
            self.rounded_check.setChecked(advanced.get("rounded", True))

        except Exception as e:
            self.logger.error(f"加载主题配置失败: {e}")

    def _apply_settings(self):
        try:
            settings = self.config_manager.get_settings()
            config = settings.get("theme_config", {})

            config.update({
                "theme": self.theme_combo.currentText(),
                "ui_settings": {
                    "font": self.font_combo.currentText(),
                    "font_size": self.font_size_spin.value(),
                    "scale": self.scale_slider.value()
                },
                "advanced_settings": {
                    "animation": self.animation_check.isChecked(),
                    "transparency": self.transparency_check.isChecked(),
                    "glass": self.glass_check.isChecked(),
                    "rounded": self.rounded_check.isChecked()
                }
            })

            settings["theme_config"] = config
            self.config_manager.update_settings(settings)

            self.config_changed.emit("theme_config", config)
            QMessageBox.information(self, "成功", "主题配置已保存")

        except Exception as e:
            self.logger.error(f"应用主题配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")


class SettingsPage(BasePage):
    """设置页面 - macOS 设计系统"""

    def __init__(self, application: Application):
        super().__init__("settings", "设置", application)
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")
        self.event_bus = application.get_service_by_name("event_bus")

    def initialize(self) -> bool:
        try:
            self.log_info("Initializing settings page")
            return True
        except Exception as e:
            self.handle_error(e, "initialize")
            return False

    def create_content(self) -> None:
        """创建页面内容"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        header = MacPageToolbar("⚙️ 设置", [
            ("🔄", "刷新", self.refresh),
            ("💾", "保存所有", self._save_all),
        ])
        layout.addWidget(header)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setProperty("class", "settings-tabs")

        # 创建面板
        self.ai_panel = AIConfigPanel(self.application)
        self.chinese_ai_panel = ChineseAIConfigPanel(self.application)
        self.path_panel = PathConfigPanel(self.application)
        self.theme_panel = ThemeConfigPanel(self.application)

        # 连接信号
        self._connect_signals()

        # 添加标签页
        self.tab_widget.addTab(self.ai_panel, "AI配置")
        self.tab_widget.addTab(self.chinese_ai_panel, "国产AI")
        self.tab_widget.addTab(self.path_panel, "路径配置")
        self.tab_widget.addTab(self.theme_panel, "主题管理")

        layout.addWidget(self.tab_widget)

    def _connect_signals(self):
        """连接信号"""
        self.ai_panel.config_changed.connect(self._on_config_changed)
        self.chinese_ai_panel.config_changed.connect(self._on_config_changed)
        self.path_panel.config_changed.connect(self._on_config_changed)
        self.theme_panel.config_changed.connect(self._on_config_changed)

    def _on_config_changed(self, config_type: str, config_data: Any):
        """配置变更处理"""
        self.logger.info(f"配置变更: {config_type}")
        self.event_bus.emit("settings.changed", {"type": config_type, "data": config_data})

    def _save_all(self):
        """保存所有配置"""
        try:
            self.ai_panel._apply_settings()
            self.chinese_ai_panel._apply_settings()
            self.path_panel._apply_settings()
            self.theme_panel._apply_settings()
            QMessageBox.information(self, "成功", "所有配置已保存")
        except Exception as e:
            self.logger.error(f"保存所有配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def refresh(self):
        """刷新配置"""
        try:
            self.ai_panel._load_settings()
            self.chinese_ai_panel.refresh()
            self.path_panel._load_settings()
            self.theme_panel._load_settings()
            self.update_status("配置已刷新")
        except Exception as e:
            self.logger.error(f"刷新配置失败: {e}")
