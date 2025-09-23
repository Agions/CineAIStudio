#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 项目管理页面
提供完整的项目管理功能界面
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSplitter, QStackedWidget, QProgressBar,
    QMessageBox, QDialog, QFileDialog, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QInputDialog, QListWidget, QListWidgetItem, QToolButton,
    QMenu, QAction, QDialogButtonBox, QFormLayout, QSlider
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QBrush

from .base_page import BasePage
from app.core.icon_manager import get_icon
from app.utils.error_handler import handle_exception
from app.core.project_manager import ProjectManager, Project, ProjectType, ProjectStatus
from app.core.project_template_manager import ProjectTemplateManager, TemplateInfo
from app.core.project_settings_manager import ProjectSettingsManager
from app.core.project_version_manager import ProjectVersionManager


class ProjectCard(QFrame):
    """项目卡片组件"""

    clicked = pyqtSignal(str)  # 项目点击信号
    edit_clicked = pyqtSignal(str)  # 编辑点击信号
    delete_clicked = pyqtSignal(str)  # 删除点击信号
    export_clicked = pyqtSignal(str)  # 导出点击信号

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        """设置UI"""
        self.setObjectName("projectCard")
        self.setFixedSize(300, 200)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 项目名称
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(self.name_label)

        # 项目描述
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(self.desc_label)

        # 项目信息
        info_layout = QHBoxLayout()
        self.type_label = QLabel()
        self.type_label.setStyleSheet("font-size: 10px; color: #999; padding: 2px 6px; background: #f0f0f0; border-radius: 3px;")
        info_layout.addWidget(self.type_label)

        info_layout.addStretch()

        self.date_label = QLabel()
        self.date_label.setStyleSheet("font-size: 10px; color: #999;")
        info_layout.addWidget(self.date_label)

        layout.addLayout(info_layout)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.edit_btn = QToolButton()
        self.edit_btn.setIcon(get_icon("edit", 20))
        self.edit_btn.setToolTip("编辑项目")
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.project.id))
        button_layout.addWidget(self.edit_btn)

        self.export_btn = QToolButton()
        self.export_btn.setIcon(get_icon("export", 20))
        self.export_btn.setToolTip("导出项目")
        self.export_btn.clicked.connect(lambda: self.export_clicked.emit(self.project.id))
        button_layout.addWidget(self.export_btn)

        self.delete_btn = QToolButton()
        self.delete_btn.setIcon(get_icon("delete", 20))
        self.delete_btn.setToolTip("删除项目")
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.project.id))
        button_layout.addWidget(self.delete_btn)

        layout.addLayout(button_layout)

        # 设置样式
        self.setStyleSheet("""
            QFrame#projectCard {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QFrame#projectCard:hover {
                border-color: #2196F3;
                background-color: #f8f9fa;
            }
            QToolButton {
                border: none;
                background: transparent;
                padding: 5px;
                border-radius: 4px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
        """)

    def _update_display(self):
        """更新显示"""
        self.name_label.setText(self.project.metadata.name)
        self.desc_label.setText(self.project.metadata.description or "无描述")
        self.type_label.setText(self.project.metadata.project_type.value)
        self.date_label.setText(self.project.metadata.modified_at.strftime("%Y-%m-%d"))

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project.id)
        super().mousePressEvent(event)


class TemplateCard(QFrame):
    """模板卡片组件"""

    selected = pyqtSignal(str)  # 模板选择信号
    preview_clicked = pyqtSignal(str)  # 预览点击信号

    def __init__(self, template: TemplateInfo, parent=None):
        super().__init__(parent)
        self.template = template
        self.is_selected = False
        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        """设置UI"""
        self.setObjectName("templateCard")
        self.setFixedSize(200, 150)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 模板名称
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(self.name_label)

        # 模板预览图
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(120, 80)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 4px;")
        layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 模板类别
        self.category_label = QLabel()
        self.category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.category_label.setStyleSheet("font-size: 10px; color: #666; padding: 2px 6px; background: #e3f2fd; border-radius: 3px;")
        layout.addWidget(self.category_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 设置样式
        self.setStyleSheet("""
            QFrame#templateCard {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
            }
            QFrame#templateCard:hover {
                border-color: #2196F3;
            }
            QFrame#templateCard[selected=true] {
                border-color: #4CAF50;
                background-color: #f1f8e9;
            }
        """)

    def _update_display(self):
        """更新显示"""
        self.name_label.setText(self.template.name)
        self.category_label.setText(self.template.category)

        # 加载预览图
        if self.template.preview_image and os.path.exists(self.template.preview_image):
            pixmap = QPixmap(self.template.preview_image)
            scaled_pixmap = pixmap.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(True)
            self.selected.emit(self.template.id)
        super().mousePressEvent(event)


class CreateProjectDialog(QDialog):
    """创建项目对话框"""

    def __init__(self, template_manager: ProjectTemplateManager, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.selected_template = None
        self._setup_ui()
        self._load_templates()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("创建新项目")
        self.setModal(True)
        self.setFixedSize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 项目名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("项目名称:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入项目名称...")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 项目类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("项目类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([pt.value for pt in ProjectType])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # 项目描述
        desc_label = QLabel("项目描述:")
        layout.addWidget(desc_label)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("输入项目描述...")
        self.desc_edit.setMaximumHeight(100)
        layout.addWidget(self.desc_edit)

        # 模板选择
        template_group = QGroupBox("选择模板")
        template_layout = QVBoxLayout(template_group)

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索模板...")
        self.search_edit.textChanged.connect(self._filter_templates)
        search_layout.addWidget(self.search_edit)
        template_layout.addLayout(search_layout)

        # 模板滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.templates_layout = QGridLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        template_layout.addWidget(self.scroll_area)

        layout.addWidget(template_group)

        # 按钮
        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.create_btn = QPushButton("创建")
        self.create_btn.clicked.connect(self._create_project)
        self.create_btn.setDefault(True)
        button_layout.addWidget(self.create_btn)

        layout.addLayout(button_layout)

    def _load_templates(self):
        """加载模板"""
        self.template_cards = {}
        templates = self.template_manager.get_all_templates()

        row, col = 0, 0
        for template in templates:
            card = TemplateCard(template)
            card.selected.connect(self._on_template_selected)
            self.templates_layout.addWidget(card, row, col)
            self.template_cards[template.id] = card

            col += 1
            if col >= 3:
                col = 0
                row += 1

    def _filter_templates(self):
        """过滤模板"""
        search_text = self.search_edit.text().lower()
        for template_id, card in self.template_cards.items():
            template = card.template
            matches = (search_text in template.name.lower() or
                      search_text in template.description.lower() or
                      search_text in template.category.lower())
            card.setVisible(matches)

    def _on_template_selected(self, template_id: str):
        """模板选择"""
        # 取消其他选中
        for card in self.template_cards.values():
            card.set_selected(False)

        # 选中当前模板
        if template_id in self.template_cards:
            self.template_cards[template_id].set_selected(True)
            self.selected_template = template_id

    def _create_project(self):
        """创建项目"""
        project_name = self.name_edit.text().strip()
        if not project_name:
            QMessageBox.warning(self, "警告", "请输入项目名称")
            return

        project_type = ProjectType(self.type_combo.currentText())
        description = self.desc_edit.toPlainText().strip()

        self.accept()

    def get_project_info(self):
        """获取项目信息"""
        return {
            'name': self.name_edit.text().strip(),
            'type': ProjectType(self.type_combo.currentText()),
            'description': self.desc_edit.toPlainText().strip(),
            'template_id': self.selected_template
        }


class ProjectSettingsDialog(QDialog):
    """项目设置对话框"""

    def __init__(self, project: Project, settings_manager: ProjectSettingsManager, parent=None):
        super().__init__(parent)
        self.project = project
        self.settings_manager = settings_manager
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("项目设置")
        self.setModal(True)
        self.setFixedSize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 设置标签页
        self.tab_widget = QTabWidget()

        # 视频设置
        self.video_tab = self._create_video_tab()
        self.tab_widget.addTab(self.video_tab, "视频")

        # 音频设置
        self.audio_tab = self._create_audio_tab()
        self.tab_widget.addTab(self.audio_tab, "音频")

        # 自动保存设置
        self.autosave_tab = self._create_autosave_tab()
        self.tab_widget.addTab(self.autosave_tab, "自动保存")

        # AI设置
        self.ai_tab = self._create_ai_tab()
        self.tab_widget.addTab(self.ai_tab, "AI设置")

        layout.addWidget(self.tab_widget)

        # 按钮
        button_layout = QHBoxLayout()
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(self.reset_btn)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _create_video_tab(self):
        """创建视频设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 分辨率
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['3840x2160', '2560x1440', '1920x1080', '1280x720', '854x480'])
        layout.addRow("分辨率:", self.resolution_combo)

        # 帧率
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        layout.addRow("帧率 (FPS):", self.fps_spin)

        # 比特率
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(['4000k', '6000k', '8000k', '12000k', '16000k', '20000k'])
        layout.addRow("比特率:", self.bitrate_combo)

        # 编码器
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(['h264', 'h265', 'vp9', 'av1'])
        layout.addRow("编码器:", self.codec_combo)

        return widget

    def _create_audio_tab(self):
        """创建音频设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 采样率
        self.samplerate_combo = QComboBox()
        self.samplerate_combo.addItems(['22050', '44100', '48000', '96000'])
        layout.addRow("采样率 (Hz):", self.samplerate_combo)

        # 比特率
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItems(['128k', '192k', '256k', '320k'])
        layout.addRow("比特率:", self.audio_bitrate_combo)

        # 声道数
        self.channels_spin = QSpinBox()
        self.channels_spin.setRange(1, 8)
        self.channels_spin.setValue(2)
        layout.addRow("声道数:", self.channels_spin)

        return widget

    def _create_autosave_tab(self):
        """创建自动保存设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 启用自动保存
        self.autosave_check = QCheckBox("启用自动保存")
        layout.addRow("", self.autosave_check)

        # 自动保存间隔
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(60, 3600)
        self.interval_spin.setValue(300)
        self.interval_spin.setSuffix(" 秒")
        layout.addRow("自动保存间隔:", self.interval_spin)

        # 最大备份数
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setRange(1, 50)
        self.max_backups_spin.setValue(10)
        layout.addRow("最大备份数:", self.max_backups_spin)

        return widget

    def _create_ai_tab(self):
        """创建AI设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 默认模型
        self.model_combo = QComboBox()
        self.model_combo.addItems(['gpt-3.5-turbo', 'gpt-4', 'claude-3', 'gemini-pro'])
        layout.addRow("默认模型:", self.model_combo)

        # 最大令牌数
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 8000)
        self.max_tokens_spin.setValue(2000)
        layout.addRow("最大令牌数:", self.max_tokens_spin)

        # 创造性程度
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 200)
        self.temperature_slider.setValue(70)
        self.temperature_label = QLabel("0.7")
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v/100:.1f}")
        )
        layout.addRow("创造性程度:", temp_layout)

        return widget

    def _load_settings(self):
        """加载设置"""
        # 加载视频设置
        resolution = self.project.settings.video_resolution
        self.resolution_combo.setCurrentText(resolution)

        self.fps_spin.setValue(self.project.settings.video_fps)
        self.bitrate_combo.setCurrentText(self.project.settings.video_bitrate)

        # 加载音频设置
        self.samplerate_combo.setCurrentText(str(self.project.settings.audio_sample_rate))
        self.audio_bitrate_combo.setCurrentText(self.project.settings.audio_bitrate)
        self.channels_spin.setValue(self.project.settings.audio_channels)

        # 加载自动保存设置
        self.autosave_check.setChecked(self.project.settings.auto_save_enabled)
        self.interval_spin.setValue(self.project.settings.auto_save_interval)
        self.max_backups_spin.setValue(self.project.settings.backup_count)

        # 加载AI设置
        ai_settings = self.project.settings.ai_settings
        self.model_combo.setCurrentText(ai_settings.get('default_model', 'gpt-3.5-turbo'))
        self.max_tokens_spin.setValue(ai_settings.get('max_tokens', 2000))
        temperature = ai_settings.get('temperature', 0.7)
        self.temperature_slider.setValue(int(temperature * 100))

    def _reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 重置为默认值
            self.resolution_combo.setCurrentText("1920x1080")
            self.fps_spin.setValue(30)
            self.bitrate_combo.setCurrentText("8000k")
            self.samplerate_combo.setCurrentText("44100")
            self.audio_bitrate_combo.setCurrentText("192k")
            self.channels_spin.setValue(2)
            self.autosave_check.setChecked(True)
            self.interval_spin.setValue(300)
            self.max_backups_spin.setValue(10)
            self.model_combo.setCurrentText("gpt-3.5-turbo")
            self.max_tokens_spin.setValue(2000)
            self.temperature_slider.setValue(70)

    def _save_settings(self):
        """保存设置"""
        # 更新项目设置
        self.project.settings.video_resolution = self.resolution_combo.currentText()
        self.project.settings.video_fps = self.fps_spin.value()
        self.project.settings.video_bitrate = self.bitrate_combo.currentText()
        self.project.settings.audio_sample_rate = int(self.samplerate_combo.currentText())
        self.project.settings.audio_bitrate = self.audio_bitrate_combo.currentText()
        self.project.settings.audio_channels = self.channels_spin.value()
        self.project.settings.auto_save_enabled = self.autosave_check.isChecked()
        self.project.settings.auto_save_interval = self.interval_spin.value()
        self.project.settings.backup_count = self.max_backups_spin.value()

        # 更新AI设置
        self.project.settings.ai_settings = {
            'default_model': self.model_combo.currentText(),
            'max_tokens': self.max_tokens_spin.value(),
            'temperature': self.temperature_slider.value() / 100
        }

        self.accept()


class ProjectsPage(BasePage):
    """项目管理页面"""

    def __init__(self, application):
        super().__init__("projects", "项目管理", application)

        # 初始化管理器
        self.project_manager: ProjectManager = application.get_service_by_name("project_manager")
        self.template_manager: ProjectTemplateManager = application.get_service_by_name("template_manager")
        self.settings_manager: ProjectSettingsManager = application.get_service_by_name("settings_manager")

        # 当前选中的项目
        self.selected_project_id: Optional[str] = None

        # 初始化UI
        self._init_ui()

        # 加载项目数据
        self._load_projects()

        # 定时刷新
        self._setup_refresh_timer()

    def _init_ui(self):
        """初始化UI"""
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # 标题和操作栏
        header_widget = self._create_header_section()
        self.main_layout.addWidget(header_widget)

        # 主内容区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：项目列表
        left_widget = self._create_projects_section()
        content_splitter.addWidget(left_widget)

        # 右侧：项目详情
        right_widget = self._create_project_details_section()
        content_splitter.addWidget(right_widget)

        # 设置分割器比例
        content_splitter.setSizes([400, 400])
        content_splitter.setCollapsible(0, False)
        content_splitter.setCollapsible(1, True)

        self.main_layout.addWidget(content_splitter, 1)

    def _create_header_section(self) -> QWidget:
        """创建标题区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QLabel("项目管理")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        layout.addStretch()

        # 操作按钮
        self.new_project_btn = QPushButton(get_icon("add", 20), "新建项目")
        self.new_project_btn.clicked.connect(self._on_new_project)
        layout.addWidget(self.new_project_btn)

        self.open_project_btn = QPushButton(get_icon("open", 20), "打开项目")
        self.open_project_btn.clicked.connect(self._on_open_project)
        layout.addWidget(self.open_project_btn)

        self.import_project_btn = QPushButton(get_icon("import", 20), "导入项目")
        self.import_project_btn.clicked.connect(self._on_import_project)
        layout.addWidget(self.import_project_btn)

        self.refresh_btn = QPushButton(get_icon("refresh", 20), "刷新")
        self.refresh_btn.clicked.connect(self._refresh_projects)
        layout.addWidget(self.refresh_btn)

        return widget

    def _create_projects_section(self) -> QWidget:
        """创建项目列表区域"""
        widget = QFrame()
        widget.setObjectName("projectsSection")
        widget.setStyleSheet("""
            QFrame#projectsSection {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 搜索和过滤
        filter_widget = self._create_filter_section()
        layout.addWidget(filter_widget)

        # 项目网格
        self.projects_scroll = QScrollArea()
        self.projects_scroll.setWidgetResizable(True)
        self.projects_widget = QWidget()
        self.projects_layout = QGridLayout(self.projects_widget)
        self.projects_scroll.setWidget(self.projects_widget)
        layout.addWidget(self.projects_scroll, 1)

        return widget

    def _create_filter_section(self) -> QWidget:
        """创建过滤区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索项目...")
        self.search_edit.textChanged.connect(self._filter_projects)
        layout.addWidget(self.search_edit, 1)

        # 类型过滤
        self.type_filter = QComboBox()
        self.type_filter.addItem("全部类型")
        for project_type in ProjectType:
            self.type_filter.addItem(project_type.value)
        self.type_filter.currentTextChanged.connect(self._filter_projects)
        layout.addWidget(self.type_filter)

        # 状态过滤
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部状态")
        for status in ProjectStatus:
            self.status_filter.addItem(status.value)
        self.status_filter.currentTextChanged.connect(self._filter_projects)
        layout.addWidget(self.status_filter)

        return widget

    def _create_project_details_section(self) -> QWidget:
        """创建项目详情区域"""
        widget = QFrame()
        widget.setObjectName("detailsSection")
        widget.setStyleSheet("""
            QFrame#detailsSection {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 详情标题
        self.details_title = QLabel("项目详情")
        self.details_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(self.details_title)

        # 详情内容
        self.details_stack = QStackedWidget()

        # 空状态页面
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.addStretch()
        empty_label = QLabel("选择一个项目查看详情")
        empty_label.setStyleSheet("font-size: 16px; color: #999; text-align: center;")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_label)
        empty_layout.addStretch()
        self.details_stack.addWidget(empty_widget)

        # 项目详情页面
        self.details_widget = self._create_project_details_content()
        self.details_stack.addWidget(self.details_widget)

        layout.addWidget(self.details_stack, 1)

        # 操作按钮
        self.details_buttons = self._create_details_buttons()
        layout.addWidget(self.details_buttons)

        return widget

    def _create_project_details_content(self) -> QWidget:
        """创建项目详情内容"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 基本信息
        info_group = QGroupBox("基本信息")
        info_layout = QFormLayout(info_group)

        self.detail_name = QLabel()
        info_layout.addRow("项目名称:", self.detail_name)

        self.detail_type = QLabel()
        info_layout.addRow("项目类型:", self.detail_type)

        self.detail_created = QLabel()
        info_layout.addRow("创建时间:", self.detail_created)

        self.detail_modified = QLabel()
        info_layout.addRow("修改时间:", self.detail_modified)

        self.detail_status = QLabel()
        info_layout.addRow("状态:", self.detail_status)

        layout.addWidget(info_group)

        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QFormLayout(stats_group)

        self.detail_media_count = QLabel()
        stats_layout.addRow("媒体文件数:", self.detail_media_count)

        self.detail_duration = QLabel()
        stats_layout.addRow("总时长:", self.detail_duration)

        self.detail_size = QLabel()
        stats_layout.addRow("项目大小:", self.detail_size)

        layout.addWidget(stats_group)

        # 描述
        desc_group = QGroupBox("描述")
        desc_layout = QVBoxLayout(desc_group)

        self.detail_description = QLabel()
        self.detail_description.setWordWrap(True)
        self.detail_description.setStyleSheet("color: #666;")
        desc_layout.addWidget(self.detail_description)

        layout.addWidget(desc_group)

        layout.addStretch()

        return widget

    def _create_details_buttons(self) -> QWidget:
        """创建详情区域按钮"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.edit_project_btn = QPushButton(get_icon("edit", 16), "编辑")
        self.edit_project_btn.clicked.connect(self._on_edit_project)
        layout.addWidget(self.edit_project_btn)

        self.settings_project_btn = QPushButton(get_icon("settings", 16), "设置")
        self.settings_project_btn.clicked.connect(self._on_project_settings)
        layout.addWidget(self.settings_project_btn)

        self.export_project_btn = QPushButton(get_icon("export", 16), "导出")
        self.export_project_btn.clicked.connect(self._on_export_project)
        layout.addWidget(self.export_project_btn)

        self.delete_project_btn = QPushButton(get_icon("delete", 16), "删除")
        self.delete_project_btn.clicked.connect(self._on_delete_project)
        self.delete_project_btn.setStyleSheet("background-color: #f44336; color: white;")
        layout.addWidget(self.delete_project_btn)

        return widget

    def _load_projects(self):
        """加载项目列表"""
        self.project_cards = {}
        projects = self.project_manager.get_all_projects()

        # 清空现有卡片
        for i in reversed(range(self.projects_layout.count())):
            child = self.projects_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        # 添加项目卡片
        row, col = 0, 0
        for project in projects:
            card = ProjectCard(project)
            card.clicked.connect(self._on_project_selected)
            card.edit_clicked.connect(self._on_edit_project)
            card.export_clicked.connect(self._on_export_project)
            card.delete_clicked.connect(self._on_delete_project)

            self.projects_layout.addWidget(card, row, col)
            self.project_cards[project.id] = card

            col += 1
            if col >= 2:
                col = 0
                row += 1

        # 添加拉伸空间
        self.projects_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding), row, col)

    def _filter_projects(self):
        """过滤项目"""
        search_text = self.search_edit.text().lower()
        type_filter = self.type_filter.currentText()
        status_filter = self.status_filter.currentText()

        for project_id, card in self.project_cards.items():
            project = card.project
            matches = True

            # 搜索过滤
            if search_text:
                matches = (search_text in project.metadata.name.lower() or
                          search_text in project.metadata.description.lower())

            # 类型过滤
            if matches and type_filter != "全部类型":
                matches = project.metadata.project_type.value == type_filter

            # 状态过滤
            if matches and status_filter != "全部状态":
                matches = project.metadata.status.value == status_filter

            card.setVisible(matches)

    def _on_project_selected(self, project_id: str):
        """项目选择"""
        self.selected_project_id = project_id
        project = self.project_manager.get_project(project_id)

        if project:
            # 更新详情显示
            self._update_project_details(project)
            self.details_stack.setCurrentWidget(self.details_widget)

            # 更新按钮状态
            self.edit_project_btn.setEnabled(True)
            self.settings_project_btn.setEnabled(True)
            self.export_project_btn.setEnabled(True)
            self.delete_project_btn.setEnabled(True)

    def _update_project_details(self, project: Project):
        """更新项目详情"""
        self.detail_name.setText(project.metadata.name)
        self.detail_type.setText(project.metadata.project_type.value)
        self.detail_created.setText(project.metadata.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        self.detail_modified.setText(project.metadata.modified_at.strftime("%Y-%m-%d %H:%M:%S"))
        self.detail_status.setText(project.metadata.status.value)
        self.detail_media_count.setText(str(len(project.media_files)))
        self.detail_duration.setText(f"{project.timeline.duration:.2f} 秒")
        self.detail_size.setText(self._format_file_size(self._calculate_project_size(project)))
        self.detail_description.setText(project.metadata.description or "无描述")

    def _calculate_project_size(self, project: Project) -> int:
        """计算项目大小"""
        try:
            total_size = 0
            project_path = Path(project.path)
            for file_path in project_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception:
            return 0

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def _on_new_project(self):
        """新建项目"""
        dialog = CreateProjectDialog(self.template_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_info = dialog.get_project_info()

            project_id = self.project_manager.create_project(
                name=project_info['name'],
                project_type=project_info['type'],
                description=project_info['description'],
                template_id=project_info['template_id']
            )

            if project_id:
                QMessageBox.information(self, "成功", "项目创建成功！")
                self._load_projects()

                # 切换到项目详情页面
                self._on_project_selected(project_id)

    def _on_open_project(self):
        """打开项目"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", "", "CineAIStudio项目 (*.json)"
        )

        if file_path:
            project_dir = os.path.dirname(file_path)
            project_id = self.project_manager.open_project(project_dir)

            if project_id:
                QMessageBox.information(self, "成功", "项目打开成功！")
                self._load_projects()
                self._on_project_selected(project_id)
            else:
                QMessageBox.warning(self, "失败", "无法打开项目")

    def _on_import_project(self):
        """导入项目"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入项目", "", "CineAIStudio项目包 (*.zip)"
        )

        if file_path:
            project_id = self.project_manager.import_project(file_path)

            if project_id:
                QMessageBox.information(self, "成功", "项目导入成功！")
                self._load_projects()
                self._on_project_selected(project_id)
            else:
                QMessageBox.warning(self, "失败", "无法导入项目")

    def _on_edit_project(self, project_id: str = None):
        """编辑项目"""
        if project_id is None:
            project_id = self.selected_project_id

        if project_id:
            project = self.project_manager.get_project(project_id)
            if project:
                # 这里可以打开项目编辑器
                QMessageBox.information(self, "编辑项目", f"正在编辑项目: {project.metadata.name}")

    def _on_project_settings(self, project_id: str = None):
        """项目设置"""
        if project_id is None:
            project_id = self.selected_project_id

        if project_id:
            project = self.project_manager.get_project(project_id)
            if project:
                dialog = ProjectSettingsDialog(project, self.settings_manager, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    # 保存项目设置
                    self.project_manager.save_project(project_id)
                    QMessageBox.information(self, "成功", "项目设置已保存！")

    def _on_export_project(self, project_id: str = None):
        """导出项目"""
        if project_id is None:
            project_id = self.selected_project_id

        if project_id:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出项目", "", "CineAIStudio项目包 (*.zip)"
            )

            if file_path:
                include_media = QMessageBox.question(
                    self, "包含媒体文件",
                    "是否包含媒体文件一起导出？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes

                if self.project_manager.export_project(project_id, file_path, include_media):
                    QMessageBox.information(self, "成功", "项目导出成功！")
                else:
                    QMessageBox.warning(self, "失败", "无法导出项目")

    def _on_delete_project(self, project_id: str = None):
        """删除项目"""
        if project_id is None:
            project_id = self.selected_project_id

        if project_id:
            project = self.project_manager.get_project(project_id)
            if project:
                reply = QMessageBox.question(
                    self, "确认删除",
                    f"确定要删除项目 '{project.metadata.name}' 吗？\n此操作不可撤销！",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    if self.project_manager.delete_project(project_id):
                        QMessageBox.information(self, "成功", "项目删除成功！")
                        self._load_projects()
                        self.details_stack.setCurrentWidget(self.details_stack.widget(0))  # 显示空状态
                        self.selected_project_id = None
                    else:
                        QMessageBox.warning(self, "失败", "无法删除项目")

    def _refresh_projects(self):
        """刷新项目列表"""
        self._load_projects()
        QMessageBox.information(self, "刷新", "项目列表已刷新！")

    def _setup_refresh_timer(self):
        """设置定时刷新"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(60000)  # 每分钟刷新一次

    def _auto_refresh(self):
        """自动刷新"""
        if self.selected_project_id:
            project = self.project_manager.get_project(self.selected_project_id)
            if project:
                self._update_project_details(project)

    def refresh(self):
        """刷新页面"""
        self._load_projects()
        if self.selected_project_id:
            project = self.project_manager.get_project(self.selected_project_id)
            if project:
                self._update_project_details(project)

    def get_page_type(self) -> str:
        """获取页面类型"""
        return "projects"