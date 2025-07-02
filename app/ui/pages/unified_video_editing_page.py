#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一视频编辑页面
整合所有AI功能到一个页面中，提供流畅的用户体验
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSplitter, QGroupBox, QButtonGroup,
    QRadioButton, QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from app.ui.professional_ui_system import ProfessionalButton, ProfessionalCard, ProfessionalTheme
from app.ui.components.subtitle_extraction_widget import SubtitleExtractionWidget


class AIFeatureSelector(QWidget):
    """AI功能选择器"""
    
    feature_selected = pyqtSignal(str)  # 功能选择信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark_theme = False
        self.selected_feature = None
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("选择AI处理功能")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 功能选择区域
        features_layout = QHBoxLayout()
        features_layout.setSpacing(20)
        
        # 创建按钮组确保单选
        self.feature_group = QButtonGroup(self)
        
        # AI短剧解说
        self.commentary_card = self._create_feature_card(
            "🎬", "AI短剧解说", 
            "智能分析视频内容，生成专业的短剧解说文案，适合抖音、快手等短视频平台",
            "commentary"
        )
        features_layout.addWidget(self.commentary_card)
        
        # AI高能混剪
        self.compilation_card = self._create_feature_card(
            "⚡", "AI高能混剪", 
            "自动检测视频中的精彩片段，智能剪辑生成高能混剪视频",
            "compilation"
        )
        features_layout.addWidget(self.compilation_card)
        
        # AI第一人称独白
        self.monologue_card = self._create_feature_card(
            "🎭", "AI第一人称独白", 
            "基于视频内容生成第一人称视角的独白文案，增强观众代入感",
            "monologue"
        )
        features_layout.addWidget(self.monologue_card)
        
        features_widget = QWidget()
        features_widget.setLayout(features_layout)
        layout.addWidget(features_widget)
        
        # 功能说明
        self.description_label = QLabel("请选择一个AI处理功能开始视频编辑")
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.description_label)
    
    def _create_feature_card(self, icon, title, description, feature_id):
        """创建功能卡片"""
        card = ProfessionalCard("")
        card.setMinimumHeight(180)
        card.setMaximumHeight(200)
        
        # 卡片内容
        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图标
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 28))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setMinimumHeight(40)
        content_layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(title)
        title_font = QFont("Arial", 13, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setMinimumHeight(24)
        title_label.setContentsMargins(4, 4, 4, 4)
        content_layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_font = QFont("Arial", 10)
        desc_label.setFont(desc_font)
        desc_label.setMinimumHeight(40)
        desc_label.setMaximumHeight(80)
        desc_label.setContentsMargins(6, 4, 6, 4)
        content_layout.addWidget(desc_label)
        
        # 选择按钮
        select_btn = ProfessionalButton("选择此功能", "primary")
        select_btn.setCheckable(True)
        select_btn.setProperty('feature_id', feature_id)
        select_btn.clicked.connect(lambda: self._select_feature(feature_id, title, description))

        # 添加到按钮组
        self.feature_group.addButton(select_btn)

        content_layout.addWidget(select_btn)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        card.add_content(content_widget)
        
        return card
    
    def _select_feature(self, feature_id, title, description):
        """选择功能"""
        self.selected_feature = feature_id
        self.description_label.setText(f"已选择：{title}\n{description}")
        self.feature_selected.emit(feature_id)
    
    def _apply_styles(self):
        """应用样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        
        self.setStyleSheet(f"""
            AIFeatureSelector {{
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_primary']};
                font-family: Arial, sans-serif;
            }}
        """)
    
    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()
        
        # 更新子组件主题
        for card in self.findChildren(ProfessionalCard):
            card.set_theme(is_dark)
        for button in self.findChildren(ProfessionalButton):
            button.set_theme(is_dark)

    def select_feature(self, feature_id):
        """程序化选择功能"""
        feature_mapping = {
            'ai_commentary': 'commentary',
            'ai_compilation': 'compilation',
            'ai_monologue': 'monologue'
        }

        # 转换功能ID
        actual_feature = feature_mapping.get(feature_id, feature_id)

        # 查找对应的按钮并选中
        for button in self.feature_group.buttons():
            if button.property('feature_id') == actual_feature:
                button.setChecked(True)
                self.selected_feature = actual_feature
                self.feature_selected.emit(actual_feature)
                break


class ProcessingControlPanel(QWidget):
    """处理控制面板"""
    
    processing_started = pyqtSignal(str, dict)  # 开始处理信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark_theme = False
        self.current_feature = None
        self.current_video = None
        self.current_subtitles = None
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 状态显示
        status_card = ProfessionalCard("处理状态")
        
        status_layout = QVBoxLayout()
        
        # 各项状态
        self.video_status = QLabel("📹 视频文件: 未选择")
        self.video_status.setFont(QFont("Arial", 12))
        status_layout.addWidget(self.video_status)
        
        self.subtitle_status = QLabel("📝 字幕提取: 未完成")
        self.subtitle_status.setFont(QFont("Arial", 12))
        status_layout.addWidget(self.subtitle_status)
        
        self.feature_status = QLabel("🤖 AI功能: 未选择")
        self.feature_status.setFont(QFont("Arial", 12))
        status_layout.addWidget(self.feature_status)
        
        # 整体状态
        self.overall_status = QLabel("⏳ 请完成上述步骤后开始处理")
        self.overall_status.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.overall_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.overall_status)
        
        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        status_card.add_content(status_widget)
        
        layout.addWidget(status_card)
        
        # 处理控制
        control_card = ProfessionalCard("处理控制")
        
        control_layout = QVBoxLayout()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # 状态消息
        self.status_message = QLabel("准备就绪")
        self.status_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(self.status_message)
        
        # 控制按钮
        buttons_layout = QHBoxLayout()
        
        self.start_btn = ProfessionalButton("🚀 开始AI处理", "primary")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_processing)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = ProfessionalButton("⏹️ 停止处理", "danger")
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        buttons_layout.addStretch()
        
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        control_layout.addWidget(buttons_widget)
        
        control_widget = QWidget()
        control_widget.setLayout(control_layout)
        control_card.add_content(control_widget)
        
        layout.addWidget(control_card)
    
    def update_video_status(self, video_path):
        """更新视频状态"""
        self.current_video = video_path
        if video_path:
            filename = os.path.basename(video_path)
            self.video_status.setText(f"📹 视频文件: {filename}")
        else:
            self.video_status.setText("📹 视频文件: 未选择")
        self._check_ready_status()
    
    def update_subtitle_status(self, subtitles_result):
        """更新字幕状态"""
        self.current_subtitles = subtitles_result
        if subtitles_result and subtitles_result.success:
            track_count = len(subtitles_result.tracks)
            self.subtitle_status.setText(f"📝 字幕提取: 已完成 ({track_count}个轨道)")
        else:
            self.subtitle_status.setText("📝 字幕提取: 未完成")
        self._check_ready_status()
    
    def update_feature_status(self, feature_id):
        """更新功能状态"""
        self.current_feature = feature_id
        feature_names = {
            "commentary": "AI短剧解说",
            "compilation": "AI高能混剪",
            "monologue": "AI第一人称独白"
        }
        
        if feature_id:
            feature_name = feature_names.get(feature_id, "未知功能")
            self.feature_status.setText(f"🤖 AI功能: {feature_name}")
        else:
            self.feature_status.setText("🤖 AI功能: 未选择")
        self._check_ready_status()
    
    def _check_ready_status(self):
        """检查准备状态"""
        ready = (self.current_video and 
                self.current_subtitles and 
                self.current_subtitles.success and 
                self.current_feature)
        
        self.start_btn.setEnabled(ready)
        
        if ready:
            self.overall_status.setText("✅ 准备就绪，可以开始AI处理")
        else:
            missing = []
            if not self.current_video:
                missing.append("视频文件")
            if not self.current_subtitles or not self.current_subtitles.success:
                missing.append("字幕提取")
            if not self.current_feature:
                missing.append("AI功能选择")
            
            self.overall_status.setText(f"⏳ 等待: {', '.join(missing)}")
    
    def _start_processing(self):
        """开始处理"""
        if not (self.current_video and self.current_subtitles and self.current_feature):
            return
        
        # 准备处理参数
        params = {
            "video_path": self.current_video,
            "subtitles": self.current_subtitles,
            "feature": self.current_feature
        }
        
        # 发射开始处理信号
        self.processing_started.emit(self.current_feature, params)
        
        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.status_message.setText("正在进行AI处理...")
    
    def _apply_styles(self):
        """应用样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        
        self.setStyleSheet(f"""
            ProcessingControlPanel {{
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
            QProgressBar {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                text-align: center;
                color: {colors['text_primary']};
                font-weight: 500;
                min-height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {colors['primary']};
                border-radius: 5px;
            }}
        """)
    
    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()
        
        # 更新子组件主题
        for card in self.findChildren(ProfessionalCard):
            card.set_theme(is_dark)
        for button in self.findChildren(ProfessionalButton):
            button.set_theme(is_dark)


class UnifiedVideoEditingPage(QWidget):
    """统一视频编辑页面 - 整合所有AI功能"""

    def __init__(self, ai_manager, parent=None):
        super().__init__(parent)
        self.ai_manager = ai_manager
        self.is_dark_theme = False
        self.current_project_data = None  # 当前项目数据
        self.project_manager = None  # 项目管理器引用

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

    def _setup_ui(self):
        """设置UI"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 主内容
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(24)

        # 页面标题
        self.title_label = QLabel("视频编辑")
        self.title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # 使用说明
        instruction_card = ProfessionalCard("使用说明")
        instruction_text = QLabel(
            "📋 完整的AI视频编辑流程：\n"
            "1️⃣ 选择AI处理功能（短剧解说、高能混剪、第一人称独白）\n"
            "2️⃣ 导入视频文件并提取字幕内容\n"
            "3️⃣ 配置处理参数并开始AI处理\n"
            "4️⃣ 预览结果并导出成品视频"
        )
        instruction_text.setWordWrap(True)
        instruction_text.setFont(QFont("Arial", 12))
        instruction_card.add_content(instruction_text)
        layout.addWidget(instruction_card)

        # 主要工作区域 - 使用分割器
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # 上半部分：AI功能选择
        self.feature_selector = AIFeatureSelector()
        main_splitter.addWidget(self.feature_selector)

        # 下半部分：字幕提取和处理控制
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：字幕提取
        self.subtitle_widget = SubtitleExtractionWidget()
        bottom_splitter.addWidget(self.subtitle_widget)

        # 右侧：处理控制
        self.control_panel = ProcessingControlPanel()
        bottom_splitter.addWidget(self.control_panel)

        # 设置分割比例
        bottom_splitter.setStretchFactor(0, 2)  # 字幕提取占2/3
        bottom_splitter.setStretchFactor(1, 1)  # 控制面板占1/3

        main_splitter.addWidget(bottom_splitter)

        # 设置主分割器比例
        main_splitter.setStretchFactor(0, 1)  # 功能选择
        main_splitter.setStretchFactor(1, 2)  # 字幕提取和控制

        layout.addWidget(main_splitter)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _connect_signals(self):
        """连接信号"""
        # AI功能选择信号
        self.feature_selector.feature_selected.connect(self._on_feature_selected)

        # 字幕提取完成信号
        self.subtitle_widget.extraction_completed.connect(self._on_subtitle_extraction_completed)

        # 处理开始信号
        self.control_panel.processing_started.connect(self._on_processing_started)

    def _on_feature_selected(self, feature_id):
        """AI功能选择处理"""
        self.control_panel.update_feature_status(feature_id)

        # 显示功能相关提示
        feature_tips = {
            "commentary": "💡 提示：AI短剧解说适合有对话和情节的视频，建议先提取字幕获得更好的解说效果。",
            "compilation": "💡 提示：AI高能混剪会自动检测视频中的精彩片段，适合游戏、体育等动作丰富的视频。",
            "monologue": "💡 提示：AI第一人称独白会基于视频内容生成角色视角的文案，适合故事性强的视频。"
        }

        tip_text = feature_tips.get(feature_id, "")
        if tip_text:
            QMessageBox.information(self, "功能提示", tip_text)

        # 更新编辑进度
        self._update_editing_progress(feature_id, 0.2)  # 选择功能算20%进度

    def _on_subtitle_extraction_completed(self, result):
        """字幕提取完成处理"""
        self.control_panel.update_subtitle_status(result)

        # 更新视频文件状态
        if result.video_path:
            self.control_panel.update_video_status(result.video_path)

        if result.success:
            # 显示提取成功消息
            track_count = len(result.tracks)
            QMessageBox.information(
                self, "字幕提取完成",
                f"字幕提取成功！\n"
                f"提取到 {track_count} 个字幕轨道\n"
                f"处理时间: {result.processing_time:.1f}秒\n\n"
                f"现在可以选择AI功能并开始处理。"
            )
        else:
            # 显示提取失败消息
            QMessageBox.warning(
                self, "字幕提取失败",
                f"字幕提取失败：{result.error_message}\n\n"
                f"请检查视频文件格式或网络连接后重试。"
            )

    def _on_processing_started(self, feature_id, params):
        """AI处理开始"""
        feature_names = {
            "commentary": "AI短剧解说",
            "compilation": "AI高能混剪",
            "monologue": "AI第一人称独白"
        }

        feature_name = feature_names.get(feature_id, "未知功能")

        # 获取字幕文本
        subtitle_text = params["subtitles"].get_combined_text()

        # 显示处理开始消息
        QMessageBox.information(
            self, "开始AI处理",
            f"开始 {feature_name} 处理\n\n"
            f"视频文件: {os.path.basename(params['video_path'])}\n"
            f"字幕内容: {len(subtitle_text)} 字符\n"
            f"处理功能: {feature_name}\n\n"
            f"AI处理功能正在开发中，敬请期待完整版本！\n"
            f"当前版本已完成字幕提取和界面整合。"
        )

        # 更新编辑进度
        self._update_editing_progress(feature_id, 0.5)  # 开始处理算50%进度

    def _apply_styles(self):
        """应用样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)

        self.setStyleSheet(f"""
            UnifiedVideoEditingPage {{
                background-color: {colors['background']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
            QScrollArea {{
                background-color: {colors['background']};
                border: none;
            }}
            QSplitter::handle {{
                background-color: {colors['border']};
            }}
            QSplitter::handle:horizontal {{
                width: 2px;
            }}
            QSplitter::handle:vertical {{
                height: 2px;
            }}
        """)

    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()

        # 更新所有子组件主题
        self.feature_selector.set_theme(is_dark)
        self.subtitle_widget.set_theme(is_dark)
        self.control_panel.set_theme(is_dark)

        # 更新专业组件主题
        for card in self.findChildren(ProfessionalCard):
            card.set_theme(is_dark)

    def load_project_data(self, project_data, project_manager=None):
        """加载项目数据"""
        self.current_project_data = project_data
        self.project_manager = project_manager

        # 更新页面标题显示项目信息
        if hasattr(self, 'title_label'):
            project_name = project_data.get('name', '未知项目')
            self.title_label.setText(f"视频编辑 - {project_name}")

        # 根据项目的编辑模式预选AI功能
        editing_mode = project_data.get('editing_mode', 'commentary')
        mode_mapping = {
            'commentary': 'ai_commentary',
            'compilation': 'ai_compilation',
            'monologue': 'ai_monologue'
        }

        if editing_mode in mode_mapping:
            feature_id = mode_mapping[editing_mode]
            if hasattr(self, 'feature_selector'):
                self.feature_selector.select_feature(feature_id)

        # 更新项目状态为编辑中
        if self.project_manager and project_data:
            self.project_manager.update_project_status(
                project_data.get('id'),
                'editing',
                project_data.get('progress', 0.1)
            )

        print(f"已加载项目: {project_name}, 编辑模式: {editing_mode}")

    def _update_editing_progress(self, feature_id, progress):
        """更新编辑进度"""
        if self.project_manager and self.current_project_data:
            self.project_manager.update_editing_progress(
                self.current_project_data.get('id'),
                feature_id,
                progress
            )

    def _on_processing_completed(self, feature_id, result):
        """处理完成回调 - 添加进度更新"""
        # 更新编辑进度
        self._update_editing_progress(feature_id, 1.0)  # 完成处理算100%进度

    def get_project_data(self):
        """获取当前项目数据"""
        return self.current_project_data
