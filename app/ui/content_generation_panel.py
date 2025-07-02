#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFormLayout, QComboBox, QSlider, QTextEdit,
    QProgressBar, QTabWidget, QSpinBox, QDoubleSpinBox,
    QCheckBox, QListWidget, QListWidgetItem, QMessageBox,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from app.core.video_manager import VideoClip
from app.ai.content_generator import ContentGenerator, GeneratedContent, ContentSegment
from app.ai import AIManager


class ContentSegmentWidget(QWidget):
    """内容片段控件"""
    
    def __init__(self, segment: ContentSegment, parent=None):
        super().__init__(parent)
        
        self.segment = segment
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 时间信息
        time_label = QLabel(f"{self._format_time(self.segment.start_time)} - {self._format_time(self.segment.end_time)}")
        time_label.setFont(QFont("Arial", 9))
        time_label.setStyleSheet("color: #666;")
        layout.addWidget(time_label)
        
        # 内容类型
        type_label = QLabel(f"类型: {self.segment.content_type}")
        type_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout.addWidget(type_label)
        
        # 文本内容
        text_edit = QTextEdit()
        text_edit.setPlainText(self.segment.text)
        text_edit.setMaximumHeight(80)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


class ContentGenerationPanel(QWidget):
    """内容生成面板"""
    
    content_generated = pyqtSignal(GeneratedContent)
    
    def __init__(self, ai_manager: AIManager, parent=None):
        super().__init__(parent)
        
        self.ai_manager = ai_manager
        self.content_generator = ContentGenerator(ai_manager)
        self.current_video = None
        self.generated_content = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("AI内容生成")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 解说生成选项卡
        self.commentary_tab = self._create_commentary_tab()
        self.tab_widget.addTab(self.commentary_tab, "解说生成")
        
        # 混剪生成选项卡
        self.compilation_tab = self._create_compilation_tab()
        self.tab_widget.addTab(self.compilation_tab, "混剪生成")
        
        # 独白生成选项卡
        self.monologue_tab = self._create_monologue_tab()
        self.tab_widget.addTab(self.monologue_tab, "独白生成")
        
        # 结果显示选项卡
        self.results_tab = self._create_results_tab()
        self.tab_widget.addTab(self.results_tab, "生成结果")
    
    def _create_commentary_tab(self) -> QWidget:
        """创建解说生成选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 视频信息
        video_group = QGroupBox("视频信息")
        video_layout = QVBoxLayout(video_group)
        self.commentary_video_label = QLabel("未选择视频")
        self.commentary_video_label.setStyleSheet("color: #666;")
        video_layout.addWidget(self.commentary_video_label)
        layout.addWidget(video_group)
        
        # 生成设置
        settings_group = QGroupBox("生成设置")
        settings_layout = QFormLayout(settings_group)
        
        # 解说风格
        self.commentary_style_combo = QComboBox()
        self.commentary_style_combo.addItems(["幽默风趣", "专业分析", "情感解读"])
        settings_layout.addRow("解说风格:", self.commentary_style_combo)
        
        # 场景分析
        self.scene_analysis_check = QCheckBox("启用场景分析")
        self.scene_analysis_check.setChecked(True)
        settings_layout.addRow("", self.scene_analysis_check)
        
        # AI模型选择
        self.commentary_model_combo = QComboBox()
        self._update_model_list(self.commentary_model_combo)
        settings_layout.addRow("AI模型:", self.commentary_model_combo)
        
        layout.addWidget(settings_group)
        
        # 生成按钮
        self.generate_commentary_btn = QPushButton("生成解说")
        self.generate_commentary_btn.clicked.connect(self._generate_commentary)
        layout.addWidget(self.generate_commentary_btn)
        
        # 进度条
        self.commentary_progress = QProgressBar()
        self.commentary_progress.setVisible(False)
        layout.addWidget(self.commentary_progress)
        
        layout.addStretch()
        return tab
    
    def _create_compilation_tab(self) -> QWidget:
        """创建混剪生成选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 视频信息
        video_group = QGroupBox("视频信息")
        video_layout = QVBoxLayout(video_group)
        self.compilation_video_label = QLabel("未选择视频")
        self.compilation_video_label.setStyleSheet("color: #666;")
        video_layout.addWidget(self.compilation_video_label)
        layout.addWidget(video_group)
        
        # 生成设置
        settings_group = QGroupBox("生成设置")
        settings_layout = QFormLayout(settings_group)
        
        # 混剪风格
        self.compilation_style_combo = QComboBox()
        self.compilation_style_combo.addItems(["高能燃向", "节奏紧凑", "情感起伏"])
        settings_layout.addRow("混剪风格:", self.compilation_style_combo)
        
        # 精彩片段比例
        self.highlight_ratio_slider = QSlider(Qt.Orientation.Horizontal)
        self.highlight_ratio_slider.setRange(10, 80)
        self.highlight_ratio_slider.setValue(30)
        self.highlight_ratio_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.highlight_ratio_slider.setTickInterval(10)
        self.highlight_ratio_label = QLabel("30%")
        self.highlight_ratio_slider.valueChanged.connect(
            lambda v: self.highlight_ratio_label.setText(f"{v}%")
        )
        
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(self.highlight_ratio_slider)
        ratio_layout.addWidget(self.highlight_ratio_label)
        settings_layout.addRow("精彩片段比例:", ratio_layout)
        
        # AI模型选择
        self.compilation_model_combo = QComboBox()
        self._update_model_list(self.compilation_model_combo)
        settings_layout.addRow("AI模型:", self.compilation_model_combo)
        
        layout.addWidget(settings_group)
        
        # 生成按钮
        self.generate_compilation_btn = QPushButton("生成混剪")
        self.generate_compilation_btn.clicked.connect(self._generate_compilation)
        layout.addWidget(self.generate_compilation_btn)
        
        # 进度条
        self.compilation_progress = QProgressBar()
        self.compilation_progress.setVisible(False)
        layout.addWidget(self.compilation_progress)
        
        layout.addStretch()
        return tab
    
    def _create_monologue_tab(self) -> QWidget:
        """创建独白生成选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 视频信息
        video_group = QGroupBox("视频信息")
        video_layout = QVBoxLayout(video_group)
        self.monologue_video_label = QLabel("未选择视频")
        self.monologue_video_label.setStyleSheet("color: #666;")
        video_layout.addWidget(self.monologue_video_label)
        layout.addWidget(video_group)
        
        # 生成设置
        settings_group = QGroupBox("生成设置")
        settings_layout = QFormLayout(settings_group)
        
        # 角色视角
        self.character_combo = QComboBox()
        self.character_combo.addItems(["主角", "配角", "旁观者"])
        settings_layout.addRow("角色视角:", self.character_combo)
        
        # 情感基调
        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems(["平静叙述", "激动兴奋", "忧伤沉重", "愤怒不满", "温暖感动"])
        settings_layout.addRow("情感基调:", self.emotion_combo)
        
        # AI模型选择
        self.monologue_model_combo = QComboBox()
        self._update_model_list(self.monologue_model_combo)
        settings_layout.addRow("AI模型:", self.monologue_model_combo)
        
        layout.addWidget(settings_group)
        
        # 生成按钮
        self.generate_monologue_btn = QPushButton("生成独白")
        self.generate_monologue_btn.clicked.connect(self._generate_monologue)
        layout.addWidget(self.generate_monologue_btn)
        
        # 进度条
        self.monologue_progress = QProgressBar()
        self.monologue_progress.setVisible(False)
        layout.addWidget(self.monologue_progress)
        
        layout.addStretch()
        return tab
    
    def _create_results_tab(self) -> QWidget:
        """创建结果显示选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 结果信息
        info_group = QGroupBox("生成信息")
        info_layout = QFormLayout(info_group)
        
        self.result_mode_label = QLabel("无")
        info_layout.addRow("生成模式:", self.result_mode_label)
        
        self.result_duration_label = QLabel("无")
        info_layout.addRow("总时长:", self.result_duration_label)
        
        self.result_segments_label = QLabel("无")
        info_layout.addRow("片段数量:", self.result_segments_label)
        
        layout.addWidget(info_group)
        
        # 片段列表
        segments_group = QGroupBox("内容片段")
        segments_layout = QVBoxLayout(segments_group)
        
        # 滚动区域
        scroll_area = QScrollArea()
        self.segments_widget = QWidget()
        self.segments_layout = QVBoxLayout(self.segments_widget)
        self.segments_layout.addStretch()
        scroll_area.setWidget(self.segments_widget)
        scroll_area.setWidgetResizable(True)
        segments_layout.addWidget(scroll_area)
        
        layout.addWidget(segments_group)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("导出内容")
        self.export_btn.clicked.connect(self._export_content)
        self.export_btn.setEnabled(False)
        action_layout.addWidget(self.export_btn)
        
        self.clear_results_btn = QPushButton("清空结果")
        self.clear_results_btn.clicked.connect(self._clear_results)
        action_layout.addWidget(self.clear_results_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        return tab
    
    def _connect_signals(self):
        """连接信号"""
        self.content_generator.generation_progress.connect(self._on_generation_progress)
        self.content_generator.segment_generated.connect(self._on_segment_generated)
        self.content_generator.generation_completed.connect(self._on_generation_completed)
    
    def set_video(self, video: VideoClip):
        """设置当前视频"""
        self.current_video = video
        
        if video:
            video_info = f"{video.name} ({self._format_duration(video.duration)})"
            self.commentary_video_label.setText(video_info)
            self.compilation_video_label.setText(video_info)
            self.monologue_video_label.setText(video_info)
            
            # 重置样式
            for label in [self.commentary_video_label, self.compilation_video_label, self.monologue_video_label]:
                label.setStyleSheet("color: black;")
        else:
            for label in [self.commentary_video_label, self.compilation_video_label, self.monologue_video_label]:
                label.setText("未选择视频")
                label.setStyleSheet("color: #666;")
    
    def _update_model_list(self, combo: QComboBox):
        """更新模型列表"""
        combo.clear()
        available_models = self.ai_manager.get_available_models()
        
        if available_models:
            for model in available_models:
                combo.addItem(model)
        else:
            combo.addItem("无可用模型")
    
    def _format_duration(self, duration: float) -> str:
        """格式化时长"""
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _generate_commentary(self):
        """生成解说"""
        if not self.current_video:
            QMessageBox.warning(self, "警告", "请先选择一个视频文件")
            return
        
        # 禁用按钮
        self.generate_commentary_btn.setEnabled(False)
        self.commentary_progress.setVisible(True)
        self.commentary_progress.setValue(0)
        
        # 获取设置
        style = self.commentary_style_combo.currentText()
        scene_analysis = self.scene_analysis_check.isChecked()
        
        # 异步生成
        asyncio.create_task(
            self.content_generator.generate_commentary(
                self.current_video, style, scene_analysis
            )
        )
    
    def _generate_compilation(self):
        """生成混剪"""
        if not self.current_video:
            QMessageBox.warning(self, "警告", "请先选择一个视频文件")
            return
        
        # 禁用按钮
        self.generate_compilation_btn.setEnabled(False)
        self.compilation_progress.setVisible(True)
        self.compilation_progress.setValue(0)
        
        # 获取设置
        style = self.compilation_style_combo.currentText()
        ratio = self.highlight_ratio_slider.value() / 100.0
        
        # 异步生成
        asyncio.create_task(
            self.content_generator.generate_compilation(
                self.current_video, style, ratio
            )
        )
    
    def _generate_monologue(self):
        """生成独白"""
        if not self.current_video:
            QMessageBox.warning(self, "警告", "请先选择一个视频文件")
            return
        
        # 禁用按钮
        self.generate_monologue_btn.setEnabled(False)
        self.monologue_progress.setVisible(True)
        self.monologue_progress.setValue(0)
        
        # 获取设置
        character = self.character_combo.currentText()
        emotion = self.emotion_combo.currentText()
        
        # 异步生成
        asyncio.create_task(
            self.content_generator.generate_monologue(
                self.current_video, character, emotion
            )
        )
    
    def _on_generation_progress(self, progress: int):
        """生成进度回调"""
        # 更新当前活动选项卡的进度条
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:  # 解说
            self.commentary_progress.setValue(progress)
        elif current_index == 1:  # 混剪
            self.compilation_progress.setValue(progress)
        elif current_index == 2:  # 独白
            self.monologue_progress.setValue(progress)
    
    def _on_segment_generated(self, segment: ContentSegment):
        """片段生成回调"""
        # 可以在这里实时显示生成的片段
        pass
    
    def _on_generation_completed(self, content: GeneratedContent):
        """生成完成回调"""
        # 恢复按钮
        self.generate_commentary_btn.setEnabled(True)
        self.generate_compilation_btn.setEnabled(True)
        self.generate_monologue_btn.setEnabled(True)
        
        # 隐藏进度条
        self.commentary_progress.setVisible(False)
        self.compilation_progress.setVisible(False)
        self.monologue_progress.setVisible(False)
        
        # 保存结果
        self.generated_content = content
        
        # 显示结果
        self._display_results(content)
        
        # 切换到结果选项卡
        self.tab_widget.setCurrentIndex(3)
        
        # 发射信号
        self.content_generated.emit(content)
        
        QMessageBox.information(self, "完成", f"内容生成完成！共生成 {len(content.segments)} 个片段")
    
    def _display_results(self, content: GeneratedContent):
        """显示结果"""
        # 更新信息
        self.result_mode_label.setText(content.editing_mode)
        self.result_duration_label.setText(self._format_duration(content.total_duration))
        self.result_segments_label.setText(str(len(content.segments)))
        
        # 清空之前的片段
        for i in reversed(range(self.segments_layout.count() - 1)):  # 保留stretch
            child = self.segments_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # 添加新片段
        for segment in content.segments:
            segment_widget = ContentSegmentWidget(segment)
            self.segments_layout.insertWidget(self.segments_layout.count() - 1, segment_widget)
        
        # 启用导出按钮
        self.export_btn.setEnabled(True)
    
    def _export_content(self):
        """导出内容"""
        if not self.generated_content:
            return
        
        # 这里可以实现导出功能
        QMessageBox.information(self, "导出", "内容导出功能正在开发中...")
    
    def _clear_results(self):
        """清空结果"""
        self.generated_content = None
        
        # 清空信息
        self.result_mode_label.setText("无")
        self.result_duration_label.setText("无")
        self.result_segments_label.setText("无")
        
        # 清空片段
        for i in reversed(range(self.segments_layout.count() - 1)):
            child = self.segments_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # 禁用导出按钮
        self.export_btn.setEnabled(False)
