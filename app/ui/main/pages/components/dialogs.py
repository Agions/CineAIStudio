#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目管理对话框组件
包含 CreateProjectDialog 和 ProjectSettingsDialog
"""


from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QDialog, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QCheckBox, QTabWidget, QSlider, QMessageBox
)
from PySide6.QtCore import Qt

from app.ui.components import (
    MacCard, MacElevatedCard, MacPrimaryButton, MacSecondaryButton,
    MacIconButton, MacTitleLabel, MacLabel, MacScrollArea, MacSearchBox,
)
from app.core.project_template_manager import ProjectTemplateManager
from app.core.project_settings_manager import ProjectSettingsManager
from app.core.project_manager import Project, ProjectType

from .project_cards import TemplateCard


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
        # 显示用户友好的名称
        self.type_combo.addItems([pt.display_name for pt in ProjectType])
        type_layout.addWidget(self.type_combo)
        content_layout.addWidget(type_card)

        # 类型说明标签
        self.type_desc_label = MacLabel(ProjectType.VIDEO_EDITING.description)
        self.type_desc_label.setProperty("class", "text-muted")
        type_layout.addWidget(self.type_desc_label)

        # 类型选择变化时更新说明
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
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

    def _on_type_changed(self, index: int):
        """类型选择变化时更新说明"""
        if 0 <= index < len(ProjectType):
            selected_type = list(ProjectType)[index]
            self.type_desc_label.setText(selected_type.description)

    def _create_project(self):
        """创建项目"""
        project_name = self.name_edit.text().strip()
        if not project_name:
            QMessageBox.warning(self, "警告", "请输入项目名称")
            return

        # 通过显示名称查找对应的 ProjectType
        display_name = self.type_combo.currentText()
        _project_type = next((pt for pt in ProjectType if pt.display_name == display_name), ProjectType.VIDEO_EDITING)
        _description = self.desc_edit.toPlainText().strip()

        self.accept()

    def get_project_info(self):
        """获取项目信息"""
        display_name = self.type_combo.currentText()
        project_type = next((pt for pt in ProjectType if pt.display_name == display_name), ProjectType.VIDEO_EDITING)
        return {
            'name': self.name_edit.text().strip(),
            'type': project_type,
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
        res_row_layout.addWidget(MacLabel("分辨率:", "text-secondary text-bold"))
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
        fps_row_layout.addWidget(MacLabel("帧率 (FPS):", "text-secondary text-bold"))
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
        bitrate_row_layout.addWidget(MacLabel("比特率:", "text-secondary text-bold"))
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
        codec_row_layout.addWidget(MacLabel("编码器:", "text-secondary text-bold"))
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
        rate_row_layout.addWidget(MacLabel("采样率 (Hz):", "text-secondary text-bold"))
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
        audio_rate_row_layout.addWidget(MacLabel("比特率:", "text-secondary text-bold"))
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
        channels_row_layout.addWidget(MacLabel("声道数:", "text-secondary text-bold"))
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
        interval_row_layout.addWidget(MacLabel("自动保存间隔:", "text-secondary text-bold"))
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
        backups_row_layout.addWidget(MacLabel("最大备份数:", "text-secondary text-bold"))
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
        model_row_layout.addWidget(MacLabel("默认模型:", "text-secondary text-bold"))
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
        tokens_row_layout.addWidget(MacLabel("最大令牌数:", "text-secondary text-bold"))
        tokens_row_layout.addWidget(self.max_tokens_spin, 1)
        form_layout.addWidget(tokens_row)

        # 创造性程度
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 200)
        self.temperature_slider.setValue(70)
        self.temperature_label = MacLabel("0.7", "text-bold")

        temp_row = QWidget()
        temp_row.setProperty("class", "stat-row")
        temp_row_layout = QHBoxLayout(temp_row)
        temp_row_layout.setContentsMargins(0, 0, 0, 0)
        temp_row_layout.setSpacing(8)
        temp_row_layout.addWidget(MacLabel("创造性程度:", "text-secondary text-bold"))
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


