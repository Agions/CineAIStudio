#!#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlowCut 项目管理页面 - macOS 设计系统优化版
使用标准化组件，零内联样式
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
    QMenu, QDialogButtonBox, QFormLayout, QSlider, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QBrush

from .base_page import BasePage
from app.core.icon_manager import get_icon
from app.utils.error_handler import handle_exception

# 导入辅助函数
from app.ui.common.macOS_components import create_icon_text_row
from app.core.project_manager import ProjectManager, Project, ProjectType, ProjectStatus
from app.core.project_template_manager import ProjectTemplateManager, TemplateInfo
from app.core.project_settings_manager import ProjectSettingsManager

# 导入标准化组件
from app.ui.components import (
    MacCard, MacElevatedCard, MacPrimaryButton, MacSecondaryButton,
    MacDangerButton, MacIconButton, MacTitleLabel, MacLabel, MacBadge,
    MacPageToolbar, MacGrid, MacScrollArea, MacEmptyState,
    MacSearchBox, MacButtonGroup,
)


class ProjectCard(MacCard):
    """项目卡片组件 - 使用标准化 macOS 组件"""

    clicked = pyqtSignal(str)  # 项目点击信号
    edit_clicked = pyqtSignal(str)  # 编辑点击信号
    delete_clicked = pyqtSignal(str)  # 删除点击信号
    export_clicked = pyqtSignal(str)  # 导出点击信号

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setProperty("class", "card project-card")
        self.set_interactive(True)  # 设置为可交互卡片
        self.setFixedSize(300, 200)

        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        """设置UI - 使用 QSS 类名，无内联样式"""
        layout = self.layout()

        # 项目名称 (大标题)
        self.name_label = MacLabel("", None, "card-title")
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        # 项目描述 (副标题)
        self.desc_label = MacLabel("", None, "card-subtitle")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        # 项目信息行
        info_row = QWidget()
        info_row.setProperty("class", "stat-row")
        info_layout = QHBoxLayout(info_row)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)

        # 类型徽章
        self.type_badge = MacBadge("", "neutral")
        info_layout.addWidget(self.type_badge)

        info_layout.addStretch()

        # 日期标签
        self.date_label = MacLabel("", None, "text-sm text-muted")
        info_layout.addWidget(self.date_label)

        layout.addWidget(info_row)

        # 操作按钮行
        button_row = QWidget()
        button_row.setProperty("class", "icon-text-row")
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(6)

        # 编辑按钮
        self.edit_btn = MacIconButton("✏️", 28)
        self.edit_btn.setToolTip("编辑项目")
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.project.id))
        button_layout.addWidget(self.edit_btn)

        # 导出按钮
        self.export_btn = MacIconButton("📤", 28)
        self.export_btn.setToolTip("导出项目")
        self.export_btn.clicked.connect(lambda: self.export_clicked.emit(self.project.id))
        button_layout.addWidget(self.export_btn)

        # 删除按钮（使用危险样式）
        self.delete_btn = MacIconButton("🗑️", 28)
        self.delete_btn.setProperty("class", "button icon-only danger")
        self.delete_btn.setToolTip("删除项目")
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.project.id))
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()
        layout.addWidget(button_row)

    def _update_display(self):
        """更新显示"""
        self.name_label.setText(self.project.metadata.name)
        self.desc_label.setText(self.project.metadata.description or "无描述")
        self.type_badge.setText(self.project.metadata.project_type.value)
        self.date_label.setText(self.project.metadata.modified_at.strftime("%m-%d"))

    def mousePressEvent(self, event):
        """鼠标点击事件 - 点击卡片本身触发"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查点击位置是否在操作按钮区域外
            # 简单处理：点击卡片即触发
            self.clicked.emit(self.project.id)
        super().mousePressEvent(event)


class TemplateCard(MacCard):
    """模板卡片组件 - 使用标准化 macOS 组件"""

    selected = pyqtSignal(str)  # 模板选择信号
    preview_clicked = pyqtSignal(str)  # 预览点击信号

    def __init__(self, template: TemplateInfo, parent=None):
        super().__init__(parent)
        self.template = template
        self.is_selected = False
        self.setProperty("class", "card template-card")
        self.setFixedSize(220, 180)
        self.set_interactive(True)

        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        """设置UI - 使用 QSS 类名，无内联样式"""
        self.layout().setSpacing(8)
        self.layout().setContentsMargins(12, 12, 12, 12)

        # 模板名称
        self.name_label = MacLabel("", None, "text-lg text-bold")
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.name_label)

        # 模板预览图容器
        preview_container = QWidget()
        preview_container.setProperty("class", "template-preview-container")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(160, 90)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setProperty("class", "template-preview")
        preview_layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.layout().addWidget(preview_container)

        # 模板类别徽章
        self.category_badge = MacBadge("", "primary")
        self.category_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(self.category_badge, alignment=Qt.AlignmentFlag.AlignCenter)

    def _update_display(self):
        """更新显示"""
        self.name_label.setText(self.template.name)
        self.category_badge.setText(self.template.category)

        # 加载预览图
        if self.template.preview_image and os.path.exists(self.template.preview_image):
            pixmap = QPixmap(self.template.preview_image)
            scaled_pixmap = pixmap.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
        else:
            self.preview_label.setText("🖼️")

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        if selected:
            self.setProperty("class", "card template-card template-selected")
        else:
            self.setProperty("class", "card template-card")

        # 刷新样式
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(True)
            self.selected.emit(self.template.id)
        super().mousePressEvent(event)


class CreateProjectDialog(QDialog):
    """创建项目对话框 - macOS 风格"""

    def __init__(self, template_manager: ProjectTemplateManager, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.selected_template = None
        self.templates = []  # 添加默认空列表
        self.setProperty("class", "modal-container")
        self._setup_ui()
        if template_manager is not None:
            self._load_templates()

    def _setup_ui(self):
        """设置UI - 使用标准化组件和 QSS 类"""
        self.setWindowTitle("创建新项目")
        self.setModal(True)
        self.setFixedSize(640, 560)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 模态头部
        header = QWidget()
        header.setProperty("class", "modal-header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)

        title = MacTitleLabel("✨ 创建新项目")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # 关闭按钮
        close_btn = MacIconButton("✖️", 28)
        close_btn.setProperty("class", "modal-close")
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)

        main_layout.addWidget(header)

        # 模态主体（带滚动）
        scroll = MacScrollArea()
        scroll.setProperty("class", "modal-body")
        content = QWidget()
        content.setProperty("class", "section-content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # 项目名称输入
        name_card = MacCard()
        name_card.setProperty("class", "card")
        name_layout = name_card.layout()
        name_layout.setSpacing(8)

        name_label = MacTitleLabel("项目名称")
        name_layout.addWidget(name_label)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入项目名称...")
        self.name_edit.setProperty("class", "input")
        self.name_edit.setMinimumHeight(32)
        name_layout.addWidget(self.name_edit)
        content_layout.addWidget(name_card)

        # 项目类型选择
        type_card = MacCard()
        type_card.setProperty("class", "card")
        type_layout = type_card.layout()
        type_layout.setSpacing(8)

        type_label = MacTitleLabel("项目类型")
        type_layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.setProperty("class", "input")
        self.type_combo.addItems([pt.value for pt in ProjectType])
        type_layout.addWidget(self.type_combo)
        content_layout.addWidget(type_card)

        # 项目描述
        desc_card = MacCard()
        desc_card.setProperty("class", "card")
        desc_layout = desc_card.layout()
        desc_layout.setSpacing(8)

        desc_label = MacTitleLabel("项目描述")
        desc_layout.addWidget(desc_label)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("输入项目描述...")
        self.desc_edit.setProperty("class", "input")
        self.desc_edit.setMinimumHeight(80)
        desc_layout.addWidget(self.desc_edit)
        content_layout.addWidget(desc_card)

        # 模板选择区域
        template_card = MacElevatedCard()
        template_card.setProperty("class", "card card-elevated")
        template_layout = template_card.layout()
        template_layout.setSpacing(12)

        template_header = QWidget()
        template_header.setProperty("class", "icon-text-row")
        header_row = QHBoxLayout(template_header)
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        template_title = MacTitleLabel("选择模板")
        header_row.addWidget(template_title)
        header_row.addStretch()

        template_layout.addWidget(template_header)

        # 搜索框（使用 MacSearchBox）
        self.search_box = MacSearchBox("搜索模板...")
        self.search_box.searchRequested.connect(self._filter_templates)
        template_layout.addWidget(self.search_box)

        # 模板滚动区域
        self.scroll_area = MacScrollArea()
        self.scroll_area.setFixedHeight(220)
        self.scroll_widget = QWidget()
        self.scroll_widget.setProperty("class", "section-content")
        self.templates_layout = QGridLayout(self.scroll_widget)
        self.templates_layout.setSpacing(8)
        self.templates_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_area.setWidget(self.scroll_widget)
        template_layout.addWidget(self.scroll_area)

        content_layout.addWidget(template_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)

        # 底部按钮区域
        footer = QWidget()
        footer.setProperty("class", "modal-footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 16, 20, 16)
        footer_layout.setSpacing(8)

        # 取消按钮
        self.cancel_btn = MacSecondaryButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(self.cancel_btn)

        footer_layout.addStretch()

        # 创建按钮
        self.create_btn = MacPrimaryButton("✨ 创建项目")
        self.create_btn.clicked.connect(self._create_project)
        footer_layout.addWidget(self.create_btn)

        main_layout.addWidget(footer)

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
            if col >= 2:  # 两列布局更合适
                col = 0
                row += 1

    def _filter_templates(self, search_query: str):
        """过滤模板"""
        search_text = search_query.lower()
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
    """项目设置对话框 - macOS 风格"""

    def __init__(self, project: Project, settings_manager: ProjectSettingsManager, parent=None):
        super().__init__(parent)
        self.project = project
        self.settings_manager = settings_manager
        self.setProperty("class", "modal-container")
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """设置UI - 使用标准化组件"""
        self.setWindowTitle("项目设置")
        self.setModal(True)
        self.setFixedSize(840, 640)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 模态头部
        header = QWidget()
        header.setProperty("class", "modal-header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)

        title = MacTitleLabel("⚙️ 项目设置")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = MacIconButton("✖️", 28)
        close_btn.setProperty("class", "modal-close")
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)

        main_layout.addWidget(header)

        # 模态主体
        content = QWidget()
        content.setProperty("class", "modal-body")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 设置标签页（使用 QTabWidget，但添加类名）
        self.tab_widget = QTabWidget()
        self.tab_widget.setProperty("class", "settings-tabs")

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

        content_layout.addWidget(self.tab_widget)
        main_layout.addWidget(content, 1)

        # 底部按钮区域
        footer = QWidget()
        footer.setProperty("class", "modal-footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 16, 20, 16)
        footer_layout.setSpacing(8)

        # 重置按钮
        self.reset_btn = MacSecondaryButton("🔄 重置")
        self.reset_btn.clicked.connect(self._reset_settings)
        footer_layout.addWidget(self.reset_btn)

        footer_layout.addStretch()

        # 取消按钮
        self.cancel_btn = MacSecondaryButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(self.cancel_btn)

        # 保存按钮
        self.save_btn = MacPrimaryButton("💾 保存")
        self.save_btn.clicked.connect(self._save_settings)
        footer_layout.addWidget(self.save_btn)

        main_layout.addWidget(footer)

    def _create_video_tab(self):
        """创建视频设置标签页"""
        widget = MacScrollArea()
        widget.setProperty("class", "scroll-area")
        content = QWidget()
        content.setProperty("class", "section-content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 表单内容
        form_card = MacCard()
        form_layout = form_card.layout()
        form_layout.setSpacing(12)

        # 分辨率
        self.resolution_combo = QComboBox()
        self.resolution_combo.setProperty("class", "input")
        self.resolution_combo.addItems(['3840x2160', '2560x1440', '1920x1080', '1280x720', '854x480'])

        res_row = QWidget()
        res_row.setProperty("class", "stat-row")
        res_row_layout = QHBoxLayout(res_row)
        res_row_layout.setContentsMargins(0, 0, 0, 0)
        res_row_layout.setSpacing(8)
        res_row_layout.addWidget(MacLabel("分辨率:", None, "text-secondary text-bold"))
        res_row_layout.addWidget(self.resolution_combo, 1)
        form_layout.addWidget(res_row)

        # 帧率
        self.fps_spin = QSpinBox()
        self.fps_spin.setProperty("class", "input")
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)

        fps_row = QWidget()
        fps_row.setProperty("class", "stat-row")
        fps_row_layout = QHBoxLayout(fps_row)
        fps_row_layout.setContentsMargins(0, 0, 0, 0)
        fps_row_layout.setSpacing(8)
        fps_row_layout.addWidget(MacLabel("帧率 (FPS):", None, "text-secondary text-bold"))
        fps_row_layout.addWidget(self.fps_spin, 1)
        form_layout.addWidget(fps_row)

        # 比特率
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.setProperty("class", "input")
        self.bitrate_combo.addItems(['4000k', '6000k', '8000k', '12000k', '16000k', '20000k'])

        bitrate_row = QWidget()
        bitrate_row.setProperty("class", "stat-row")
        bitrate_row_layout = QHBoxLayout(bitrate_row)
        bitrate_row_layout.setContentsMargins(0, 0, 0, 0)
        bitrate_row_layout.setSpacing(8)
        bitrate_row_layout.addWidget(MacLabel("比特率:", None, "text-secondary text-bold"))
        bitrate_row_layout.addWidget(self.bitrate_combo, 1)
        form_layout.addWidget(bitrate_row)

        # 编码器
        self.codec_combo = QComboBox()
        self.codec_combo.setProperty("class", "input")
        self.codec_combo.addItems(['h264', 'h265', 'vp9', 'av1'])

        codec_row = QWidget()
        codec_row.setProperty("class", "stat-row")
        codec_row_layout = QHBoxLayout(codec_row)
        codec_row_layout.setContentsMargins(0, 0, 0, 0)
        codec_row_layout.setSpacing(8)
        codec_row_layout.addWidget(MacLabel("编码器:", None, "text-secondary text-bold"))
        codec_row_layout.addWidget(self.codec_combo, 1)
        form_layout.addWidget(codec_row)

        layout.addWidget(form_card)
        layout.addStretch()

        widget.setWidget(content)
        return widget

    def _create_audio_tab(self):
        """创建音频设置标签页"""
        widget = MacScrollArea()
        widget.setProperty("class", "scroll-area")
        content = QWidget()
        content.setProperty("class", "section-content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form_card = MacCard()
        form_layout = form_card.layout()
        form_layout.setSpacing(12)

        # 采样率
        self.samplerate_combo = QComboBox()
        self.samplerate_combo.setProperty("class", "input")
        self.samplerate_combo.addItems(['22050', '44100', '48000', '96000'])

        rate_row = QWidget()
        rate_row.setProperty("class", "stat-row")
        rate_row_layout = QHBoxLayout(rate_row)
        rate_row_layout.setContentsMargins(0, 0, 0, 0)
        rate_row_layout.setSpacing(8)
        rate_row_layout.addWidget(MacLabel("采样率 (Hz):", None, "text-secondary text-bold"))
        rate_row_layout.addWidget(self.samplerate_combo, 1)
        form_layout.addWidget(rate_row)

        # 比特率
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.setProperty("class", "input")
        self.audio_bitrate_combo.addItems(['128k', '192k', '256k', '320k'])

        audio_rate_row = QWidget()
        audio_rate_row.setProperty("class", "stat-row")
        audio_rate_row_layout = QHBoxLayout(audio_rate_row)
        audio_rate_row_layout.setContentsMargins(0, 0, 0, 0)
        audio_rate_row_layout.setSpacing(8)
        audio_rate_row_layout.addWidget(MacLabel("比特率:", None, "text-secondary text-bold"))
        audio_rate_row_layout.addWidget(self.audio_bitrate_combo, 1)
        form_layout.addWidget(audio_rate_row)

        # 声道数
        self.channels_spin = QSpinBox()
        self.channels_spin.setProperty("class", "input")
        self.channels_spin.setRange(1, 8)
        self.channels_spin.setValue(2)

        channels_row = QWidget()
        channels_row.setProperty("class", "stat-row")
        channels_row_layout = QHBoxLayout(channels_row)
        channels_row_layout.setContentsMargins(0, 0, 0, 0)
        channels_row_layout.setSpacing(8)
        channels_row_layout.addWidget(MacLabel("声道数:", None, "text-secondary text-bold"))
        channels_row_layout.addWidget(self.channels_spin, 1)
        form_layout.addWidget(channels_row)

        layout.addWidget(form_card)
        layout.addStretch()

        widget.setWidget(content)
        return widget

    def _create_autosave_tab(self):
        """创建自动保存设置标签页"""
        widget = MacScrollArea()
        widget.setProperty("class", "scroll-area")
        content = QWidget()
        content.setProperty("class", "section-content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form_card = MacCard()
        form_layout = form_card.layout()
        form_layout.setSpacing(12)

        # 启用自动保存
        self.autosave_check = QCheckBox("启用自动保存")
        self.autosave_check.setProperty("class", "input")
        form_layout.addWidget(self.autosave_check)

        # 自动保存间隔
        self.interval_spin = QSpinBox()
        self.interval_spin.setProperty("class", "input")
        self.interval_spin.setRange(60, 3600)
        self.interval_spin.setValue(300)
        self.interval_spin.setSuffix(" 秒")

        interval_row = QWidget()
        interval_row.setProperty("class", "stat-row")
        interval_row_layout = QHBoxLayout(interval_row)
        interval_row_layout.setContentsMargins(0, 0, 0, 0)
        interval_row_layout.setSpacing(8)
        interval_row_layout.addWidget(MacLabel("自动保存间隔:", None, "text-secondary text-bold"))
        interval_row_layout.addWidget(self.interval_spin, 1)
        form_layout.addWidget(interval_row)

        # 最大备份数
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setProperty("class", "input")
        self.max_backups_spin.setRange(1, 50)
        self.max_backups_spin.setValue(10)

        backups_row = QWidget()
        backups_row.setProperty("class", "stat-row")
        backups_row_layout = QHBoxLayout(backups_row)
        backups_row_layout.setContentsMargins(0, 0, 0, 0)
        backups_row_layout.setSpacing(8)
        backups_row_layout.addWidget(MacLabel("最大备份数:", None, "text-secondary text-bold"))
        backups_row_layout.addWidget(self.max_backups_spin, 1)
        form_layout.addWidget(backups_row)

        layout.addWidget(form_card)
        layout.addStretch()

        widget.setWidget(content)
        return widget

    def _create_ai_tab(self):
        """创建AI设置标签页"""
        widget = MacScrollArea()
        widget.setProperty("class", "scroll-area")
        content = QWidget()
        content.setProperty("class", "section-content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form_card = MacCard()
        form_layout = form_card.layout()
        form_layout.setSpacing(12)

        # 默认模型
        self.model_combo = QComboBox()
        self.model_combo.setProperty("class", "input")
        self.model_combo.addItems(['gpt-5', 'gpt-5-mini', 'claude-opus-4-6', 'gemini-3-pro'])

        model_row = QWidget()
        model_row.setProperty("class", "stat-row")
        model_row_layout = QHBoxLayout(model_row)
        model_row_layout.setContentsMargins(0, 0, 0, 0)
        model_row_layout.setSpacing(8)
        model_row_layout.addWidget(MacLabel("默认模型:", None, "text-secondary text-bold"))
        model_row_layout.addWidget(self.model_combo, 1)
        form_layout.addWidget(model_row)

        # 最大令牌数
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setProperty("class", "input")
        self.max_tokens_spin.setRange(100, 8000)
        self.max_tokens_spin.setValue(2000)

        tokens_row = QWidget()
        tokens_row.setProperty("class", "stat-row")
        tokens_row_layout = QHBoxLayout(tokens_row)
        tokens_row_layout.setContentsMargins(0, 0, 0, 0)
        tokens_row_layout.setSpacing(8)
        tokens_row_layout.addWidget(MacLabel("最大令牌数:", None, "text-secondary text-bold"))
        tokens_row_layout.addWidget(self.max_tokens_spin, 1)
        form_layout.addWidget(tokens_row)

        # 创造性程度
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 200)
        self.temperature_slider.setValue(70)
        self.temperature_label = MacLabel("0.7", None, "text-bold")

        temp_row = QWidget()
        temp_row.setProperty("class", "stat-row")
        temp_row_layout = QHBoxLayout(temp_row)
        temp_row_layout.setContentsMargins(0, 0, 0, 0)
        temp_row_layout.setSpacing(8)
        temp_row_layout.addWidget(MacLabel("创造性程度:", None, "text-secondary text-bold"))
        temp_row_layout.addWidget(self.temperature_slider, 1)
        temp_row_layout.addWidget(self.temperature_label)

        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v/100:.1f}")
        )
        form_layout.addWidget(temp_row)

        layout.addWidget(form_card)
        layout.addStretch()

        widget.setWidget(content)
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
        self.project_manager: Optional[ProjectManager] = application.get_service_by_name("project_manager")
        self.template_manager: Optional[ProjectTemplateManager] = application.get_service_by_name("template_manager")
        self.settings_manager: Optional[ProjectSettingsManager] = application.get_service_by_name("settings_manager")

        # 当前选中的项目
        self.selected_project_id: Optional[str] = None

        # 检查服务状态
        self._check_services()

    def initialize(self) -> bool:
        """初始化页面"""
        try:
            self.logger.info("Initializing projects page")

            # 初始化UI
            self._init_ui()

            # 加载项目数据（添加检查，避免NoneType错误）
            self._load_projects()

            # 定时刷新
            self._setup_refresh_timer()

            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize projects page: {e}")
            return False

    def create_content(self) -> None:
        """创建页面内容"""
        # 内容创建已在 _init_ui 中完成
        # 刷新项目列表
        self._refresh_project_list()

    def _check_services(self):
        """检查服务状态"""
        if not self.project_manager:
            self.logger.warning("项目管理器服务未找到")
        if not self.template_manager:
            self.logger.warning("模板管理器服务未找到")
        if not self.settings_manager:
            self.logger.warning("设置管理器服务未找到")

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
        """创建标题区域 - 使用 MacPageToolbar"""
        toolbar = MacPageToolbar("📁 项目管理")

        # 操作按钮
        self.new_project_btn = MacPrimaryButton("✨ 新建项目")
        self.new_project_btn.clicked.connect(self._on_new_project)
        toolbar.add_action(self.new_project_btn)

        self.open_project_btn = MacSecondaryButton("📂 打开项目")
        self.open_project_btn.clicked.connect(self._on_open_project)
        toolbar.add_action(self.open_project_btn)

        self.import_project_btn = MacSecondaryButton("📥 导入项目")
        self.import_project_btn.clicked.connect(self._on_import_project)
        toolbar.add_action(self.import_project_btn)

        self.refresh_btn = MacIconButton("🔄", 32)
        self.refresh_btn.setToolTip("刷新")
        self.refresh_btn.clicked.connect(self._refresh_projects)
        toolbar.add_action(self.refresh_btn)

        return toolbar

    def _create_projects_section(self) -> QWidget:
        """创建项目列表区域 - 使用标准化卡片布局"""
        widget = MacElevatedCard()
        widget.setProperty("class", "card section-card")
        widget.layout().setSpacing(12)

        # 搜索和过滤区域
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        # 搜索框（使用 MacSearchBox）
        self.search_box = MacSearchBox("🔍 搜索项目...")
        # MacSearchBox 的 searchRequested 信号会传回 query
        # 但我们还有下拉过滤，所以统一用 _filter_projects
        self.search_box.searchRequested.connect(lambda: self._filter_projects())
        filter_layout.addWidget(self.search_box, 1)

        # 按钮组用于类型和状态过滤
        self.type_filter = QComboBox()
        self.type_filter.setProperty("class", "input")
        self.type_filter.setMinimumWidth(120)
        self.type_filter.addItem("全部类型")
        for project_type in ProjectType:
            self.type_filter.addItem(project_type.value)
        self.type_filter.currentTextChanged.connect(self._filter_projects)
        filter_layout.addWidget(self.type_filter)

        self.status_filter = QComboBox()
        self.status_filter.setProperty("class", "input")
        self.status_filter.setMinimumWidth(120)
        self.status_filter.addItem("全部状态")
        for status in ProjectStatus:
            self.status_filter.addItem(status.value)
        self.status_filter.currentTextChanged.connect(self._filter_projects)
        filter_layout.addWidget(self.status_filter)

        filter_container = QWidget()
        filter_container.setLayout(filter_layout)
        widget.layout().addWidget(filter_container)

        # 项目网格（使用 MacScrollArea）
        self.projects_scroll = MacScrollArea()
        self.projects_widget = QWidget()
        self.projects_widget.setProperty("class", "grid")
        self.projects_layout = QGridLayout(self.projects_widget)
        self.projects_layout.setSpacing(12)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_scroll.setWidget(self.projects_widget)
        widget.layout().addWidget(self.projects_scroll, 1)

        return widget

    def _filter_projects(self):
        """过滤项目 - 响应搜索框和下拉框"""
        # 获取搜索文本
        search_text = ""
        if hasattr(self, 'search_box') and self.search_box:
            search_text = self.search_box.input.text().lower()

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

    def _create_project_details_section(self) -> QWidget:
        """创建项目详情区域 - 重新设计的现代化布局"""
        widget = MacElevatedCard()
        widget.setProperty("class", "card section-card")
        widget.layout().setSpacing(16)

        # 详情标题
        title_row = create_icon_text_row("📋", "项目详情")
        widget.layout().addWidget(title_row)

        # 详情内容 - 使用 StackedWidget
        self.details_stack = QStackedWidget()

        # 空状态页面
        empty_widget = MacEmptyState(
            icon="📭",
            title="未选择项目",
            description="请在左侧选择一个项目查看详情"
        )
        self.details_stack.addWidget(empty_widget)

        # 项目详情页面（使用 MacScrollArea）
        self.details_scroll = MacScrollArea()
        self.details_widget = self._create_project_details_content()
        self.details_scroll.setWidget(self.details_widget)
        self.details_stack.addWidget(self.details_scroll)

        widget.layout().addWidget(self.details_stack, 1)

        # 操作按钮
        self.details_buttons = self._create_details_buttons()
        widget.layout().addWidget(self.details_buttons)

        # 初始禁用按钮
        self._set_details_buttons_enabled(False)

        return widget

    def _set_details_buttons_enabled(self, enabled: bool):
        """设置详情按钮启用状态"""
        if hasattr(self, 'edit_project_btn'):
            self.edit_project_btn.setEnabled(enabled)
        if hasattr(self, 'settings_project_btn'):
            self.settings_project_btn.setEnabled(enabled)
        if hasattr(self, 'export_project_btn'):
            self.export_project_btn.setEnabled(enabled)
        if hasattr(self, 'delete_project_btn'):
            self.delete_project_btn.setEnabled(enabled)
        if hasattr(self, 'open_project_btn'):
            self.open_project_btn.setEnabled(enabled)

    def _create_project_details_content(self) -> QWidget:
        """创建项目详情内容 - 现代化卡片布局"""
        content = QWidget()
        content.setProperty("class", "section-content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ===== 1. 项目预览卡片 =====
        preview_card = MacCard()
        preview_card.setProperty("class", "card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setSpacing(12)

        # 项目图标/预览区域
        self.detail_icon_label = QLabel()
        self.detail_icon_label.setFixedSize(80, 80)
        self.detail_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_icon_label.setStyleSheet("font-size: 48px;")
        preview_layout.addWidget(self.detail_icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 项目名称（大标题）
        self.detail_name = MacTitleLabel("")
        self.detail_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        preview_layout.addWidget(self.detail_name, alignment=Qt.AlignmentFlag.AlignCenter)

        # 项目类型徽章
        self.detail_type_badge = MacBadge("", "primary")
        self.detail_type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.detail_type_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(preview_card)

        # ===== 2. 统计信息卡片（网格布局）=====
        stats_card = MacCard()
        stats_card.setProperty("class", "card")
        stats_layout = QGridLayout(stats_card)
        stats_layout.setSpacing(12)

        # 媒体文件数
        self.stat_media_container = self._create_stat_item("🎬", "媒体文件", "0")
        stats_layout.addWidget(self.stat_media_container, 0, 0)

        # 总时长
        self.stat_duration_container = self._create_stat_item("⏱️", "总时长", "0:00")
        stats_layout.addWidget(self.stat_duration_container, 0, 1)

        # 项目大小
        self.stat_size_container = self._create_stat_item("💾", "项目大小", "0 MB")
        stats_layout.addWidget(self.stat_size_container, 1, 0)

        # 项目状态
        self.stat_status_container = self._create_stat_item("📊", "状态", "未设置")
        stats_layout.addWidget(self.stat_status_container, 1, 1)

        layout.addWidget(stats_card)

        # ===== 3. 基本信息卡片 =====
        info_card = MacCard()
        info_card.setProperty("class", "card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(8)

        info_title = MacTitleLabel("时间信息")
        info_layout.addWidget(info_title)

        self.detail_created = MacLabel("", None, "text-base")
        info_layout.addWidget(self._create_detail_row("🗓️ 创建时间:", self.detail_created))

        self.detail_modified = MacLabel("", None, "text-base")
        info_layout.addWidget(self._create_detail_row("🔄 修改时间:", self.detail_modified))

        layout.addWidget(info_card)

        # ===== 4. 描述卡片 =====
        desc_card = MacCard()
        desc_card.setProperty("class", "card")
        desc_layout = QVBoxLayout(desc_card)
        desc_layout.setSpacing(8)

        desc_title = MacTitleLabel("项目描述")
        desc_layout.addWidget(desc_title)

        self.detail_description = MacLabel("暂无描述", None, "text-secondary")
        self.detail_description.setWordWrap(True)
        desc_layout.addWidget(self.detail_description)

        layout.addWidget(desc_card)

        layout.addStretch()

        return content

    def _create_stat_item(self, icon: str, label: str, value: str) -> QWidget:
        """创建统计项组件"""
        container = QWidget()
        container.setProperty("class", "stat-item")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(icon_label)

        # 数值
        value_label = MacLabel(value, "text-lg text-bold")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setObjectName("stat_value")
        layout.addWidget(value_label)

        # 标签
        label_widget = MacLabel(label, "text-sm text-muted")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_widget)

        # 保存引用以便后续更新
        container.stat_value_label = value_label

        return container

    def _create_detail_row(self, label: str, value_label: MacLabel) -> QWidget:
        """创建详情行"""
        row = QWidget()
        row.setProperty("class", "stat-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        label_widget = MacLabel(label, "text-secondary text-bold")
        row_layout.addWidget(label_widget)
        row_layout.addWidget(value_label, 1)

        return row

    def _create_details_buttons(self) -> QWidget:
        """创建详情区域按钮 - 现代化布局"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 打开项目按钮（主要操作）
        self.open_project_btn = MacPrimaryButton("🚀 打开项目")
        self.open_project_btn.clicked.connect(self._on_edit_project)
        layout.addWidget(self.open_project_btn)

        # 编辑按钮
        self.edit_project_btn = MacSecondaryButton("✏️ 编辑")
        self.edit_project_btn.clicked.connect(self._on_edit_project)
        layout.addWidget(self.edit_project_btn)

        # 设置按钮
        self.settings_project_btn = MacSecondaryButton("⚙️ 设置")
        self.settings_project_btn.clicked.connect(self._on_project_settings)
        layout.addWidget(self.settings_project_btn)

        # 导出按钮
        self.export_project_btn = MacSecondaryButton("📤 导出")
        self.export_project_btn.clicked.connect(self._on_export_project)
        layout.addWidget(self.export_project_btn)

        # 删除按钮
        self.delete_project_btn = MacDangerButton("🗑️ 删除")
        self.delete_project_btn.clicked.connect(self._on_delete_project)
        layout.addWidget(self.delete_project_btn)

        layout.addStretch()

        return widget

    def _load_projects(self):
        """加载项目列表"""
        self.project_cards = {}

        # 检查项目管理器是否可用
        if not self.project_manager:
            self.logger.warning("项目管理器不可用，无法加载项目")

            # 显示空状态
            self.projects_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding), 0, 0)
            return

        try:
            projects = self.project_manager.get_all_projects()
        except Exception as e:
            self.logger.error(f"获取项目列表失败: {e}")
            return

        # 清空现有卡片
        for i in reversed(range(self.projects_layout.count())):
            child = self.projects_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
            else:
                # 移除非widget项（如QSpacerItem）
                item = self.projects_layout.takeAt(i)
                if item and hasattr(item, 'deleteLater'):
                    item.deleteLater()

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

    # _filter_projects 已在前面定义，支持 MacSearchBox

    def _on_project_selected(self, project_id: str):
        """项目选择"""
        self.selected_project_id = project_id
        project = self.project_manager.get_project(project_id)

        if project:
            # 更新详情显示
            self._update_project_details(project)
            self.details_stack.setCurrentWidget(self.details_widget)

            # 更新按钮状态 - 使用新方法启用按钮
            self._set_details_buttons_enabled(True)

    def _update_project_details(self, project: Project):
        """更新项目详情 - 适配新的UI组件"""
        # 项目图标（根据类型显示不同图标）
        project_type = project.metadata.project_type.value
        icon_map = {
            "视频剪辑": "🎬",
            "视频合成": "🎨",
            "音频处理": "🎵",
            "字幕制作": "📝",
            "格式转换": "🔄"
        }
        self.detail_icon_label.setText(icon_map.get(project_type, "📁"))

        # 项目名称
        self.detail_name.setText(project.metadata.name)

        # 项目类型徽章
        self.detail_type_badge.setText(project_type)

        # 统计信息（更新容器内的值标签）
        media_count = len(project.media_files)
        if hasattr(self, 'stat_media_container') and hasattr(self.stat_media_container, 'stat_value_label'):
            self.stat_media_container.stat_value_label.setText(str(media_count))

        duration = project.timeline.duration
        duration_str = self._format_duration(duration)
        if hasattr(self, 'stat_duration_container') and hasattr(self.stat_duration_container, 'stat_value_label'):
            self.stat_duration_container.stat_value_label.setText(duration_str)

        project_size = self._calculate_project_size(project)
        size_str = self._format_file_size(project_size)
        if hasattr(self, 'stat_size_container') and hasattr(self.stat_size_container, 'stat_value_label'):
            self.stat_size_container.stat_value_label.setText(size_str)

        status = project.metadata.status.value
        if hasattr(self, 'stat_status_container') and hasattr(self.stat_status_container, 'stat_value_label'):
            self.stat_status_container.stat_value_label.setText(status)

        # 时间信息
        self.detail_created.setText(project.metadata.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        self.detail_modified.setText(project.metadata.modified_at.strftime("%Y-%m-%d %H:%M:%S"))

        # 描述
        self.detail_description.setText(project.metadata.description or "暂无描述")

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

    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}:{minutes:02d}:{secs:02d}"

    def _on_new_project(self):
        """新建项目"""
        print(f"[DEBUG] _on_new_project called")
        print(f"[DEBUG] template_manager: {self.template_manager}")
        print(f"[DEBUG] project_manager: {self.project_manager}")
        # 检查模板管理器是否可用
        if not self.template_manager:
            print("[DEBUG] template_manager is None, showing warning")
            QMessageBox.warning(self, "错误", "模板管理器不可用，无法创建项目")
            return

        # 检查项目管理器是否可用
        if not self.project_manager:
            print("[DEBUG] project_manager is None, showing warning")
            QMessageBox.warning(self, "错误", "项目管理器不可用，无法创建项目")
            return

        try:
            print("[DEBUG] Creating CreateProjectDialog")
            dialog = CreateProjectDialog(self.template_manager, self)
            print(f"[DEBUG] Dialog created, showing dialog")
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
                else:
                    QMessageBox.warning(self, "失败", "无法创建项目")
        except Exception as e:
            print(f"[DEBUG] Exception: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"创建项目时发生错误: {str(e)}")

    def _on_open_project(self):
        """打开项目"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", "", "ClipFlowCut项目 (*.json)"
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
            self, "导入项目", "", "ClipFlowCut项目包 (*.zip)"
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
                self, "导出项目", "", "ClipFlowCut项目包 (*.zip)"
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
                        # 禁用按钮
                        self._set_details_buttons_enabled(False)
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
