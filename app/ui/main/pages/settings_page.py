#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 设置页面
提供AI配置、路径配置、项目管理、主题管理和系统设置
"""

import os
import sys
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QPushButton, QLabel, QFrame, QProgressBar, QSpacerItem,
    QSizePolicy, QGroupBox, QStackedWidget, QSplitter,
    QTabWidget, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QRadioButton, QButtonGroup,
    QFileDialog, QColorDialog, QFontDialog, QMessageBox,
    QSlider, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, pyqtSignal, QPoint, QRect, QSettings,
    QMimeData, QUrl, QEvent, QRectF
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QFont, QPalette, QColor, QCursor,
    QPainter, QPen, QBrush, QPainterPath, QFontDatabase
)

from app.core.config_manager import ConfigManager
from app.core.logger import Logger
from app.core.icon_manager import get_icon
from app.core.application import Application
from app.utils.error_handler import handle_exception
from .base_page import BasePage
# from ..ai_config_page import AIConfigPage  # TODO: Create this file


class SettingsType(Enum):
    """设置类型"""
    AI_CONFIG = "ai_config"
    CHINESE_AI_CONFIG = "chinese_ai_config"
    PATH_CONFIG = "path_config"
    PROJECT_MANAGEMENT = "project_management"
    THEME_MANAGEMENT = "theme_management"
    SYSTEM_SETTINGS = "system_settings"


class AIConfigPanel(QWidget):
    """AI配置面板"""

    config_changed = pyqtSignal(str, object)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("AI配置")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(title_label)

        # AI模型配置
        model_group = QGroupBox("AI模型配置")
        model_layout = QGridLayout(model_group)

        # 模型类型
        model_layout.addWidget(QLabel("模型类型:"), 0, 0)
        self.model_type_combo = QComboBox()
        self.model_type_combo.addItems([
            "GPT-4",
            "GPT-3.5",
            "Claude",
            "Gemini",
            "本地模型"
        ])
        model_layout.addWidget(self.model_type_combo, 0, 1)

        # API密钥
        model_layout.addWidget(QLabel("API密钥:"), 1, 0)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        model_layout.addWidget(self.api_key_edit, 1, 1)

        # 模型路径
        model_layout.addWidget(QLabel("模型路径:"), 2, 0)
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("本地模型路径")
        model_layout.addWidget(self.model_path_edit, 2, 1)

        # 浏览按钮
        browse_btn = QPushButton(get_icon("folder", 16), "浏览...")
        browse_btn.clicked.connect(self._browse_model_path)
        model_layout.addWidget(browse_btn, 2, 2)

        layout.addWidget(model_group)

        # AI功能配置
        feature_group = QGroupBox("AI功能配置")
        feature_layout = QGridLayout(feature_group)

        # 启用AI功能
        self.ai_enabled_check = QCheckBox("启用AI功能")
        feature_layout.addWidget(self.ai_enabled_check, 0, 0)

        # 自动字幕
        self.auto_subtitle_check = QCheckBox("自动字幕")
        feature_layout.addWidget(self.auto_subtitle_check, 0, 1)

        # 智能剪辑
        self.smart_editing_check = QCheckBox("智能剪辑")
        feature_layout.addWidget(self.smart_editing_check, 1, 0)

        # 场景检测
        self.scene_detection_check = QCheckBox("场景检测")
        feature_layout.addWidget(self.scene_detection_check, 1, 1)

        # 语音转文字
        self.speech_to_text_check = QCheckBox("语音转文字")
        feature_layout.addWidget(self.speech_to_text_check, 2, 0)

        # 文字转语音
        self.text_to_speech_check = QCheckBox("文字转语音")
        feature_layout.addWidget(self.text_to_speech_check, 2, 1)

        layout.addWidget(feature_group)

        # AI性能配置
        perf_group = QGroupBox("AI性能配置")
        perf_layout = QGridLayout(perf_group)

        # 批处理大小
        perf_layout.addWidget(QLabel("批处理大小:"), 0, 0)
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 32)
        self.batch_size_spin.setValue(8)
        perf_layout.addWidget(self.batch_size_spin, 0, 1)

        # 推理精度
        perf_layout.addWidget(QLabel("推理精度:"), 1, 0)
        self.precision_combo = QComboBox()
        self.precision_combo.addItems(["FP32", "FP16", "INT8"])
        perf_layout.addWidget(self.precision_combo, 1, 1)

        # GPU内存限制
        perf_layout.addWidget(QLabel("GPU内存限制(GB):"), 2, 0)
        self.gpu_memory_spin = QSpinBox()
        self.gpu_memory_spin.setRange(1, 32)
        self.gpu_memory_spin.setValue(8)
        perf_layout.addWidget(self.gpu_memory_spin, 2, 1)

        layout.addWidget(perf_group)

        # 应用按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QPushButton("应用")
        apply_btn.setFixedSize(80, 30)
        apply_btn.setStyleSheet("""
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
        apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(apply_btn)

        reset_btn = QPushButton("重置")
        reset_btn.setFixedSize(80, 30)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4f;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff7875;
            }
        """)
        reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(reset_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _browse_model_path(self):
        """浏览模型路径"""
        try:
            model_path = QFileDialog.getExistingDirectory(
                self,
                "选择模型路径",
                os.path.expanduser("~")
            )

            if model_path:
                self.model_path_edit.setText(model_path)

        except Exception as e:
            self.logger.error(f"浏览模型路径失败: {e}")

    def _load_settings(self):
        """加载设置"""
        try:
            settings = self.config_manager.get_settings()
            ai_config = settings.get("ai_config", {})

            # 加载模型配置
            self.model_type_combo.setCurrentText(ai_config.get("model_type", "GPT-4"))
            self.api_key_edit.setText(ai_config.get("api_key", ""))
            self.model_path_edit.setText(ai_config.get("model_path", ""))

            # 加载功能配置
            self.ai_enabled_check.setChecked(ai_config.get("enabled", True))
            self.auto_subtitle_check.setChecked(ai_config.get("auto_subtitle", True))
            self.smart_editing_check.setChecked(ai_config.get("smart_editing", True))
            self.scene_detection_check.setChecked(ai_config.get("scene_detection", True))
            self.speech_to_text_check.setChecked(ai_config.get("speech_to_text", True))
            self.text_to_speech_check.setChecked(ai_config.get("text_to_speech", True))

            # 加载性能配置
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

            # 保存模型配置
            ai_config.update({
                "model_type": self.model_type_combo.currentText(),
                "api_key": self.api_key_edit.text(),
                "model_path": self.model_path_edit.text()
            })

            # 保存功能配置
            ai_config.update({
                "enabled": self.ai_enabled_check.isChecked(),
                "auto_subtitle": self.auto_subtitle_check.isChecked(),
                "smart_editing": self.smart_editing_check.isChecked(),
                "scene_detection": self.scene_detection_check.isChecked(),
                "speech_to_text": self.speech_to_text_check.isChecked(),
                "text_to_speech": self.text_to_speech_check.isChecked()
            })

            # 保存性能配置
            ai_config["performance"] = {
                "batch_size": self.batch_size_spin.value(),
                "precision": self.precision_combo.currentText(),
                "gpu_memory_limit": self.gpu_memory_spin.value()
            }

            settings["ai_config"] = ai_config
            self.config_manager.update_settings(settings)

            # 发送配置变更信号
            self.config_changed.emit("ai_config", ai_config)

            QMessageBox.information(self, "成功", "AI配置已保存")

        except Exception as e:
            self.logger.error(f"应用AI配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")

    def _reset_settings(self):
        """重置设置"""
        try:
            reply = QMessageBox.question(
                self,
                "确认重置",
                "确定要重置AI配置为默认值吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 重置为默认值
                self.model_type_combo.setCurrentText("GPT-4")
                self.api_key_edit.setText("")
                self.model_path_edit.setText("")
                self.ai_enabled_check.setChecked(True)
                self.auto_subtitle_check.setChecked(True)
                self.smart_editing_check.setChecked(True)
                self.scene_detection_check.setChecked(True)
                self.speech_to_text_check.setChecked(True)
                self.text_to_speech_check.setChecked(True)
                self.batch_size_spin.setValue(8)
                self.precision_combo.setCurrentText("FP16")
                self.gpu_memory_spin.setValue(8)

                self._apply_settings()

        except Exception as e:
            self.logger.error(f"重置AI配置失败: {e}")


class PathConfigPanel(QWidget):
    """路径配置面板"""

    config_changed = pyqtSignal(str, object)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("路径配置")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(title_label)

        # 工作路径配置
        work_group = QGroupBox("工作路径")
        work_layout = QGridLayout(work_group)

        # 项目默认路径
        work_layout.addWidget(QLabel("项目默认路径:"), 0, 0)
        self.project_path_edit = QLineEdit()
        work_layout.addWidget(self.project_path_edit, 0, 1)

        project_browse_btn = QPushButton("浏览...")
        project_browse_btn.clicked.connect(lambda: self._browse_path(self.project_path_edit))
        work_layout.addWidget(project_browse_btn, 0, 2)

        # 媒体文件路径
        work_layout.addWidget(QLabel("媒体文件路径:"), 1, 0)
        self.media_path_edit = QLineEdit()
        work_layout.addWidget(self.media_path_edit, 1, 1)

        media_browse_btn = QPushButton("浏览...")
        media_browse_btn.clicked.connect(lambda: self._browse_path(self.media_path_edit))
        work_layout.addWidget(media_browse_btn, 1, 2)

        # 临时文件路径
        work_layout.addWidget(QLabel("临时文件路径:"), 2, 0)
        self.temp_path_edit = QLineEdit()
        work_layout.addWidget(self.temp_path_edit, 2, 1)

        temp_browse_btn = QPushButton("浏览...")
        temp_browse_btn.clicked.connect(lambda: self._browse_path(self.temp_path_edit))
        work_layout.addWidget(temp_browse_btn, 2, 2)

        # 导出路径
        work_layout.addWidget(QLabel("导出路径:"), 3, 0)
        self.export_path_edit = QLineEdit()
        work_layout.addWidget(self.export_path_edit, 3, 1)

        export_browse_btn = QPushButton("浏览...")
        export_browse_btn.clicked.connect(lambda: self._browse_path(self.export_path_edit))
        work_layout.addWidget(export_browse_btn, 3, 2)

        layout.addWidget(work_group)

        # AI模型路径配置
        ai_group = QGroupBox("AI模型路径")
        ai_layout = QGridLayout(ai_group)

        # 模型存储路径
        ai_layout.addWidget(QLabel("模型存储路径:"), 0, 0)
        self.ai_model_path_edit = QLineEdit()
        ai_layout.addWidget(self.ai_model_path_edit, 0, 1)

        ai_model_browse_btn = QPushButton("浏览...")
        ai_model_browse_btn.clicked.connect(lambda: self._browse_path(self.ai_model_path_edit))
        ai_layout.addWidget(ai_model_browse_btn, 0, 2)

        # 缓存路径
        ai_layout.addWidget(QLabel("缓存路径:"), 1, 0)
        self.ai_cache_path_edit = QLineEdit()
        ai_layout.addWidget(self.ai_cache_path_edit, 1, 1)

        ai_cache_browse_btn = QPushButton("浏览...")
        ai_cache_browse_btn.clicked.connect(lambda: self._browse_path(self.ai_cache_path_edit))
        ai_layout.addWidget(ai_cache_browse_btn, 1, 2)

        layout.addWidget(ai_group)

        # 路径验证
        verify_btn = QPushButton("验证路径")
        verify_btn.setFixedSize(100, 30)
        verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #52c41a;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #73d13d;
            }
        """)
        verify_btn.clicked.connect(self._verify_paths)
        layout.addWidget(verify_btn)

        # 验证结果显示
        self.verify_result = QTextEdit()
        self.verify_result.setReadOnly(True)
        self.verify_result.setMaximumHeight(100)
        layout.addWidget(self.verify_result)

        # 应用按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QPushButton("应用")
        apply_btn.setFixedSize(80, 30)
        apply_btn.setStyleSheet("""
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
        apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _browse_path(self, line_edit: QLineEdit):
        """浏览路径"""
        try:
            path = QFileDialog.getExistingDirectory(
                self,
                "选择路径",
                line_edit.text() or os.path.expanduser("~")
            )

            if path:
                line_edit.setText(path)

        except Exception as e:
            self.logger.error(f"浏览路径失败: {e}")

    def _verify_paths(self):
        """验证路径"""
        try:
            results = []
            paths = {
                "项目默认路径": self.project_path_edit.text(),
                "媒体文件路径": self.media_path_edit.text(),
                "临时文件路径": self.temp_path_edit.text(),
                "导出路径": self.export_path_edit.text(),
                "模型存储路径": self.ai_model_path_edit.text(),
                "缓存路径": self.ai_cache_path_edit.text()
            }

            for name, path in paths.items():
                if not path:
                    results.append(f"❌ {name}: 未设置")
                elif not os.path.exists(path):
                    results.append(f"❌ {name}: 路径不存在 ({path})")
                elif not os.path.isdir(path):
                    results.append(f"❌ {name}: 不是目录 ({path})")
                else:
                    # 检查读写权限
                    readable = os.access(path, os.R_OK)
                    writable = os.access(path, os.W_OK)
                    if readable and writable:
                        results.append(f"✅ {name}: 正常 ({path})")
                    else:
                        results.append(f"⚠️ {name}: 权限不足 ({path})")

            self.verify_result.setText("\\n".join(results))

        except Exception as e:
            self.logger.error(f"验证路径失败: {e}")

    def _load_settings(self):
        """加载设置"""
        try:
            settings = self.config_manager.get_settings()
            path_config = settings.get("path_config", {})

            self.project_path_edit.setText(path_config.get("project_path", ""))
            self.media_path_edit.setText(path_config.get("media_path", ""))
            self.temp_path_edit.setText(path_config.get("temp_path", ""))
            self.export_path_edit.setText(path_config.get("export_path", ""))
            self.ai_model_path_edit.setText(path_config.get("ai_model_path", ""))
            self.ai_cache_path_edit.setText(path_config.get("ai_cache_path", ""))

        except Exception as e:
            self.logger.error(f"加载路径配置失败: {e}")

    def _apply_settings(self):
        """应用设置"""
        try:
            settings = self.config_manager.get_settings()
            path_config = settings.get("path_config", {})

            path_config.update({
                "project_path": self.project_path_edit.text(),
                "media_path": self.media_path_edit.text(),
                "temp_path": self.temp_path_edit.text(),
                "export_path": self.export_path_edit.text(),
                "ai_model_path": self.ai_model_path_edit.text(),
                "ai_cache_path": self.ai_cache_path_edit.text()
            })

            settings["path_config"] = path_config
            self.config_manager.update_settings(settings)

            # 发送配置变更信号
            self.config_changed.emit("path_config", path_config)

            QMessageBox.information(self, "成功", "路径配置已保存")

        except Exception as e:
            self.logger.error(f"应用路径配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")


class ThemeManagementPanel(QWidget):
    """主题管理面板"""

    config_changed = pyqtSignal(str, object)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("主题管理")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(title_label)

        # 主题选择
        theme_group = QGroupBox("主题选择")
        theme_layout = QGridLayout(theme_group)

        # 预设主题
        theme_layout.addWidget(QLabel("预设主题:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "深色主题",
            "浅色主题",
            "蓝色主题",
            "绿色主题",
            "紫色主题"
        ])
        theme_layout.addWidget(self.theme_combo, 0, 1)

        # 自定义主题
        theme_layout.addWidget(QLabel("自定义主题:"), 1, 0)
        custom_theme_layout = QHBoxLayout()

        self.primary_color_btn = QPushButton()
        self.primary_color_btn.setFixedSize(50, 30)
        self.primary_color_btn.clicked.connect(lambda: self._choose_color(self.primary_color_btn))
        custom_theme_layout.addWidget(self.primary_color_btn)

        self.secondary_color_btn = QPushButton()
        self.secondary_color_btn.setFixedSize(50, 30)
        self.secondary_color_btn.clicked.connect(lambda: self._choose_color(self.secondary_color_btn))
        custom_theme_layout.addWidget(self.secondary_color_btn)

        self.accent_color_btn = QPushButton()
        self.accent_color_btn.setFixedSize(50, 30)
        self.accent_color_btn.clicked.connect(lambda: self._choose_color(self.accent_color_btn))
        custom_theme_layout.addWidget(self.accent_color_btn)

        theme_layout.addLayout(custom_theme_layout, 1, 1)

        layout.addWidget(theme_group)

        # 界面配置
        ui_group = QGroupBox("界面配置")
        ui_layout = QGridLayout(ui_group)

        # 字体配置
        ui_layout.addWidget(QLabel("字体:"), 0, 0)
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Microsoft YaHei", "SimSun", "Times New Roman"])
        ui_layout.addWidget(self.font_combo, 0, 1)

        font_btn = QPushButton("选择字体")
        font_btn.clicked.connect(self._choose_font)
        ui_layout.addWidget(font_btn, 0, 2)

        # 字体大小
        ui_layout.addWidget(QLabel("字体大小:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        ui_layout.addWidget(self.font_size_spin, 1, 1)

        # 界面缩放
        ui_layout.addWidget(QLabel("界面缩放:"), 2, 0)
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(50, 200)
        self.scale_slider.setValue(100)
        self.scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.scale_slider.setTickInterval(25)
        ui_layout.addWidget(self.scale_slider, 2, 1)

        self.scale_label = QLabel("100%")
        ui_layout.addWidget(self.scale_label, 2, 2)

        self.scale_slider.valueChanged.connect(
            lambda value: self.scale_label.setText(f"{value}%")
        )

        layout.addWidget(ui_group)

        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QGridLayout(advanced_group)

        # 启用动画
        self.animation_check = QCheckBox("启用界面动画")
        advanced_layout.addWidget(self.animation_check, 0, 0)

        # 启用透明效果
        self.transparency_check = QCheckBox("启用透明效果")
        advanced_layout.addWidget(self.transparency_check, 0, 1)

        # 启用毛玻璃效果
        self.glass_check = QCheckBox("启用毛玻璃效果")
        advanced_layout.addWidget(self.glass_check, 1, 0)

        # 启用圆角
        self.rounded_check = QCheckBox("启用圆角")
        advanced_layout.addWidget(self.rounded_check, 1, 1)

        layout.addWidget(advanced_group)

        # 应用按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QPushButton("应用")
        apply_btn.setFixedSize(80, 30)
        apply_btn.setStyleSheet("""
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
        apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _choose_color(self, button: QPushButton):
        """选择颜色"""
        try:
            current_color = button.palette().color(QPalette.ColorRole.Button)
            color = QColorDialog.getColor(current_color, self)

            if color.isValid():
                button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #404040;")

        except Exception as e:
            self.logger.error(f"选择颜色失败: {e}")

    def _choose_font(self):
        """选择字体"""
        try:
            font, ok = QFontDialog.getFont()

            if ok:
                self.font_combo.setCurrentText(font.family())
                self.font_size_spin.setValue(font.pointSize())

        except Exception as e:
            self.logger.error(f"选择字体失败: {e}")

    def _load_settings(self):
        """加载设置"""
        try:
            settings = self.config_manager.get_settings()
            theme_config = settings.get("theme_config", {})

            # 加载主题设置
            self.theme_combo.setCurrentText(theme_config.get("theme", "深色主题"))

            # 加载颜色设置
            colors = theme_config.get("colors", {})
            self._set_button_color(self.primary_color_btn, colors.get("primary_color", "#1890ff"))
            self._set_button_color(self.secondary_color_btn, colors.get("secondary_color", "#2d2d2d"))
            self._set_button_color(self.accent_color_btn, colors.get("accent_color", "#404040"))

            # 加载界面设置
            ui_settings = theme_config.get("ui_settings", {})
            self.font_combo.setCurrentText(ui_settings.get("font", "Arial"))
            self.font_size_spin.setValue(ui_settings.get("font_size", 12))
            self.scale_slider.setValue(ui_settings.get("scale", 100))

            # 加载高级设置
            advanced_settings = theme_config.get("advanced_settings", {})
            self.animation_check.setChecked(advanced_settings.get("animation", True))
            self.transparency_check.setChecked(advanced_settings.get("transparency", False))
            self.glass_check.setChecked(advanced_settings.get("glass", False))
            self.rounded_check.setChecked(advanced_settings.get("rounded", True))

        except Exception as e:
            self.logger.error(f"加载主题配置失败: {e}")

    def _set_button_color(self, button: QPushButton, color: str):
        """设置按钮颜色"""
        button.setStyleSheet(f"background-color: {color}; border: 1px solid #404040;")

    def _apply_settings(self):
        """应用设置"""
        try:
            settings = self.config_manager.get_settings()
            theme_config = settings.get("theme_config", {})

            # 保存主题设置
            theme_config.update({
                "theme": self.theme_combo.currentText()
            })

            # 保存颜色设置
            theme_config["colors"] = {
                "primary_color": self.primary_color_btn.palette().color(QPalette.ColorRole.Button).name(),
                "secondary_color": self.secondary_color_btn.palette().color(QPalette.ColorRole.Button).name(),
                "accent_color": self.accent_color_btn.palette().color(QPalette.ColorRole.Button).name()
            }

            # 保存界面设置
            theme_config["ui_settings"] = {
                "font": self.font_combo.currentText(),
                "font_size": self.font_size_spin.value(),
                "scale": self.scale_slider.value()
            }

            # 保存高级设置
            theme_config["advanced_settings"] = {
                "animation": self.animation_check.isChecked(),
                "transparency": self.transparency_check.isChecked(),
                "glass": self.glass_check.isChecked(),
                "rounded": self.rounded_check.isChecked()
            }

            settings["theme_config"] = theme_config
            self.config_manager.update_settings(settings)

            # 发送配置变更信号
            self.config_changed.emit("theme_config", theme_config)

            QMessageBox.information(self, "成功", "主题配置已保存")

        except Exception as e:
            self.logger.error(f"应用主题配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")


class SettingsPage(BasePage):
    """CineAIStudio v2.0 设置页面"""

    def __init__(self, application: Application):
        super().__init__("settings", "设置", application)
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")
        self.event_bus = application.get_service_by_name("event_bus")

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """初始化用户界面"""
        # 使用BasePage的main_layout而不是创建新的layout
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1890ff;
                border-color: #1890ff;
            }
            QTabBar::tab:hover {
                background-color: #404040;
            }
        """)

        # 创建各个设置面板
        self.ai_config_panel = AIConfigPanel(self.application)
        # self.chinese_ai_config_panel = AIConfigPage(self.application)  # TODO: Uncomment when AIConfigPage is created
        # Create a placeholder panel that has the model_config_changed signal
        self.chinese_ai_config_panel = QWidget()
        layout = QVBoxLayout(self.chinese_ai_config_panel)
        label = QLabel("AI配置页面正在开发中...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #ffffff; font-size: 16px;")
        layout.addWidget(label)

        # Add the required signal
        class PlaceholderPanel(QWidget):
            model_config_changed = pyqtSignal()
        self.chinese_ai_config_panel = PlaceholderPanel()
        self.path_config_panel = PathConfigPanel(self.application)
        self.theme_panel = ThemeManagementPanel(self.application)

        # 添加标签页
        self.tab_widget.addTab(self.ai_config_panel, "AI配置")
        self.tab_widget.addTab(self.chinese_ai_config_panel, "国产AI")
        self.tab_widget.addTab(self.path_config_panel, "路径配置")
        self.tab_widget.addTab(self.theme_panel, "主题管理")

        self.main_layout.addWidget(self.tab_widget)

    def _setup_connections(self):
        """设置信号连接"""
        # 设置面板信号
        self.ai_config_panel.config_changed.connect(self._on_config_changed)
        self.chinese_ai_config_panel.model_config_changed.connect(self._on_config_changed)
        self.path_config_panel.config_changed.connect(self._on_config_changed)
        self.theme_panel.config_changed.connect(self._on_config_changed)

        # 事件总线订阅
        self.event_bus.subscribe("settings.changed", self._on_settings_changed)

    def _on_config_changed(self, config_type: str, config_data: Any):
        """处理配置变更"""
        self.logger.info(f"配置变更: {config_type}")

        # 发送事件
        self.event_bus.emit("settings.changed", {
            "type": config_type,
            "data": config_data
        })

    def _on_settings_changed(self, event_data: Dict[str, Any]):
        """处理设置变更事件"""
        config_type = event_data.get("type")
        config_data = event_data.get("data")

        if config_type == "theme_config":
            # 应用主题变更
            self._apply_theme_changes(config_data)
        elif config_type == "path_config":
            # 验证路径
            self._validate_paths(config_data)

    def _apply_theme_changes(self, theme_config: Dict[str, Any]):
        """应用主题变更"""
        try:
            # 这里可以实现主题变更的逻辑
            self.logger.info("应用主题变更")

        except Exception as e:
            self.logger.error(f"应用主题变更失败: {e}")

    def _validate_paths(self, path_config: Dict[str, Any]):
        """验证路径"""
        try:
            # 这里可以实现路径验证的逻辑
            self.logger.info("验证路径配置")

        except Exception as e:
            self.logger.error(f"验证路径失败: {e}")

    def refresh(self):
        """刷新设置页面"""
        try:
            self.ai_config_panel._load_settings()
            self.chinese_ai_config_panel.refresh()
            self.path_config_panel._load_settings()
            self.theme_panel._load_settings()
            self.logger.info("设置页面刷新完成")

        except Exception as e:
            self.logger.error(f"刷新设置页面失败: {e}")

    def get_application(self) -> Application:
        """获取应用程序实例"""
        return self.application

    def get_config(self) -> Any:
        """获取配置"""
        return self.application.get_config()