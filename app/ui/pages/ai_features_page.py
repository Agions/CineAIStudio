#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy, QProgressBar,
    QComboBox, QTextEdit, QFileDialog, QGroupBox, QFormLayout,
    QSpinBox, QCheckBox, QSlider, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QMovie

from app.ai import AIManager


class AIFeaturePanel(QWidget):
    """AI功能面板基类"""
    
    def __init__(self, title: str, description: str, icon: str = "", parent=None):
        super().__init__(parent)
        
        self.title = title
        self.description = description
        self.icon = icon
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 标题区域
        header = self._create_header()
        layout.addWidget(header)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { color: #f0f0f0; }")
        layout.addWidget(separator)
        
        # 内容区域
        content = self._create_content()
        layout.addWidget(content)
    
    def _create_header(self) -> QWidget:
        """创建标题区域"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 图标和标题
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setFont(QFont("Arial", 32))
            layout.addWidget(icon_label)
        
        # 文本区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setObjectName("feature_title")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(self.description)
        desc_label.setFont(QFont("Arial", 14))
        desc_label.setObjectName("feature_description")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # 样式
        header.setStyleSheet("""
            QLabel#feature_title {
                color: #1890ff;
                font-weight: 600;
            }
            
            QLabel#feature_description {
                color: #595959;
            }
        """)
        
        return header
    
    def _create_content(self) -> QWidget:
        """创建内容区域 - 子类重写"""
        content = QWidget()
        layout = QVBoxLayout(content)
        
        placeholder = QLabel("功能开发中...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFont(QFont("Arial", 16))
        placeholder.setStyleSheet("color: #bfbfbf; margin: 40px;")
        layout.addWidget(placeholder)
        
        return content


class CommentaryPanel(AIFeaturePanel):
    """AI短剧解说面板"""

    # 信号
    generation_started = pyqtSignal()
    generation_progress = pyqtSignal(int)  # 进度百分比
    generation_completed = pyqtSignal(str)  # 生成结果
    generation_error = pyqtSignal(str)  # 错误信息

    def __init__(self, parent=None):
        super().__init__(
            title="AI短剧解说",
            description="智能生成适合短剧的解说内容，自动插入原始片段",
            icon="🎬",
            parent=parent
        )

        # 状态变量
        self.current_video_path = ""
        self.is_generating = False
        self.generated_content = ""
    
    def _create_content(self) -> QWidget:
        """创建解说功能内容"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        
        # 功能介绍
        intro_widget = self._create_intro_section()
        layout.addWidget(intro_widget)
        
        # 操作区域
        controls_widget = self._create_controls_section()
        layout.addWidget(controls_widget)
        
        # 预览区域
        preview_widget = self._create_preview_section()
        layout.addWidget(preview_widget)
        
        return content
    
    def _create_intro_section(self) -> QWidget:
        """创建介绍区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("功能特点")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        features = [
            "• 智能分析视频内容，生成符合短剧风格的解说",
            "• 支持多种解说风格：幽默风趣、专业分析、情感解读",
            "• 自动匹配解说内容与视频场景",
            "• 支持自定义解说模板和风格调整"
        ]
        
        for feature in features:
            label = QLabel(feature)
            label.setFont(QFont("Arial", 12))
            label.setStyleSheet("color: #595959; margin: 4px 0px;")
            layout.addWidget(label)
        
        return widget
    
    def _create_controls_section(self) -> QWidget:
        """创建控制区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        title = QLabel("操作控制")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 视频选择区域
        video_group = QGroupBox("视频文件")
        video_layout = QVBoxLayout(video_group)

        # 文件选择
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("color: #595959; padding: 8px; border: 1px dashed #d9d9d9; border-radius: 4px;")
        file_layout.addWidget(self.file_path_label)

        self.upload_btn = QPushButton("📁 选择视频")
        self.upload_btn.setObjectName("primary_button")
        self.upload_btn.setMinimumHeight(40)
        self.upload_btn.clicked.connect(self._select_video_file)
        file_layout.addWidget(self.upload_btn)

        video_layout.addLayout(file_layout)
        layout.addWidget(video_group)

        # 解说设置区域
        settings_group = QGroupBox("解说设置")
        settings_layout = QFormLayout(settings_group)

        # 解说风格
        self.style_combo = QComboBox()
        self.style_combo.addItems(["幽默风趣", "专业分析", "情感解读", "悬疑推理", "轻松娱乐"])
        settings_layout.addRow("解说风格:", self.style_combo)

        # 解说长度
        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(30, 300)
        self.length_slider.setValue(120)
        self.length_slider.valueChanged.connect(self._update_length_label)

        length_layout = QHBoxLayout()
        length_layout.addWidget(self.length_slider)
        self.length_label = QLabel("120秒")
        self.length_label.setMinimumWidth(50)
        length_layout.addWidget(self.length_label)

        length_widget = QWidget()
        length_widget.setLayout(length_layout)
        settings_layout.addRow("目标长度:", length_widget)

        # 高级选项
        self.auto_timing_check = QCheckBox("自动匹配时间点")
        self.auto_timing_check.setChecked(True)
        settings_layout.addRow("", self.auto_timing_check)

        self.include_bgm_check = QCheckBox("包含背景音乐建议")
        settings_layout.addRow("", self.include_bgm_check)

        layout.addWidget(settings_group)

        # 生成按钮和进度
        action_layout = QVBoxLayout()

        # 按钮区域
        buttons_layout = QHBoxLayout()

        self.generate_btn = QPushButton("🎬 生成解说")
        self.generate_btn.setObjectName("primary_button")
        self.generate_btn.setMinimumHeight(44)
        self.generate_btn.clicked.connect(self._start_generation)
        buttons_layout.addWidget(self.generate_btn)

        self.stop_btn = QPushButton("⏹️ 停止生成")
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_generation)
        buttons_layout.addWidget(self.stop_btn)

        buttons_layout.addStretch()

        action_layout.addLayout(buttons_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        action_layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #52c41a; font-weight: 500;")
        action_layout.addWidget(self.status_label)

        layout.addLayout(action_layout)

        return widget
    
    def _create_preview_section(self) -> QWidget:
        """创建预览区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        title = QLabel("预览与导出")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 预览选项卡
        preview_tabs = QTabWidget()

        # 文本预览
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)

        self.preview_text = QTextEdit()
        self.preview_text.setPlaceholderText("生成的解说内容将在这里显示...")
        self.preview_text.setMinimumHeight(200)
        self.preview_text.setReadOnly(True)
        text_layout.addWidget(self.preview_text)

        # 文本操作按钮
        text_actions = QHBoxLayout()

        copy_btn = QPushButton("📋 复制文本")
        copy_btn.clicked.connect(self._copy_text)
        text_actions.addWidget(copy_btn)

        edit_btn = QPushButton("✏️ 编辑文本")
        edit_btn.clicked.connect(self._edit_text)
        text_actions.addWidget(edit_btn)

        save_btn = QPushButton("💾 保存文本")
        save_btn.clicked.connect(self._save_text)
        text_actions.addWidget(save_btn)

        text_actions.addStretch()
        text_layout.addLayout(text_actions)

        preview_tabs.addTab(text_tab, "📝 文本预览")

        # 时间轴预览
        timeline_tab = QWidget()
        timeline_layout = QVBoxLayout(timeline_tab)

        self.timeline_preview = QLabel("时间轴预览")
        self.timeline_preview.setMinimumHeight(150)
        self.timeline_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timeline_preview.setStyleSheet("""
            QLabel {
                background-color: #fafafa;
                border: 2px dashed #d9d9d9;
                border-radius: 8px;
                color: #bfbfbf;
                font-size: 14px;
            }
        """)
        timeline_layout.addWidget(self.timeline_preview)

        # 时间轴操作
        timeline_actions = QHBoxLayout()

        adjust_btn = QPushButton("⏱️ 调整时间")
        timeline_actions.addWidget(adjust_btn)

        sync_btn = QPushButton("🔄 同步视频")
        timeline_actions.addWidget(sync_btn)

        timeline_actions.addStretch()
        timeline_layout.addLayout(timeline_actions)

        preview_tabs.addTab(timeline_tab, "⏱️ 时间轴")

        layout.addWidget(preview_tabs)

        # 导出区域
        export_group = QGroupBox("导出选项")
        export_layout = QVBoxLayout(export_group)

        # 导出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("导出格式:"))

        self.export_format = QComboBox()
        self.export_format.addItems(["SRT字幕文件", "TXT文本文件", "剪映草稿", "JSON数据"])
        format_layout.addWidget(self.export_format)

        format_layout.addStretch()
        export_layout.addLayout(format_layout)

        # 导出按钮
        export_actions = QHBoxLayout()

        self.export_btn = QPushButton("📤 导出文件")
        self.export_btn.setObjectName("primary_button")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_content)
        export_actions.addWidget(self.export_btn)

        self.preview_btn = QPushButton("👁️ 预览效果")
        self.preview_btn.setMinimumHeight(40)
        self.preview_btn.setEnabled(False)
        self.preview_btn.clicked.connect(self._preview_effect)
        export_actions.addWidget(self.preview_btn)

        export_actions.addStretch()
        export_layout.addLayout(export_actions)

        layout.addWidget(export_group)

        return widget

    def _select_video_file(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;所有文件 (*)"
        )

        if file_path:
            self.current_video_path = file_path
            import os
            filename = os.path.basename(file_path)
            self.file_path_label.setText(f"已选择: {filename}")
            self.file_path_label.setStyleSheet("color: #52c41a; padding: 8px; border: 1px solid #52c41a; border-radius: 4px; background-color: #f6ffed;")
            self.generate_btn.setEnabled(True)
            self.status_label.setText("视频已选择，可以开始生成")

    def _update_length_label(self, value):
        """更新长度标签"""
        self.length_label.setText(f"{value}秒")

    def _start_generation(self):
        """开始生成解说"""
        if not self.current_video_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return

        self.is_generating = True
        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在分析视频内容...")
        self.status_label.setStyleSheet("color: #1890ff; font-weight: 500;")

        # 模拟生成过程
        self._simulate_generation()

        self.generation_started.emit()

    def _stop_generation(self):
        """停止生成"""
        self.is_generating = False
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("生成已停止")
        self.status_label.setStyleSheet("color: #ff4d4f; font-weight: 500;")

    def _simulate_generation(self):
        """模拟生成过程"""
        self.progress_timer = QTimer()
        self.progress_value = 0

        def update_progress():
            self.progress_value += 5
            self.progress_bar.setValue(self.progress_value)

            if self.progress_value == 25:
                self.status_label.setText("正在提取关键场景...")
            elif self.progress_value == 50:
                self.status_label.setText("正在生成解说文本...")
            elif self.progress_value == 75:
                self.status_label.setText("正在优化时间匹配...")
            elif self.progress_value >= 100:
                self.progress_timer.stop()
                self._generation_completed()

        self.progress_timer.timeout.connect(update_progress)
        self.progress_timer.start(200)  # 每200ms更新一次

    def _generation_completed(self):
        """生成完成"""
        self.is_generating = False
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        # 模拟生成的解说内容
        sample_content = """【开场】
大家好，今天给大家带来一个超级精彩的短剧！

【00:05】
注意看这里，主角的表情变化，简直不要太到位！这种细节处理真的很用心。

【00:15】
然后呢，剧情发生了神转折...这个反转我是真的没想到！

【00:30】
接下来这个场景展现了情感的层次，看主角的眼神，满满的都是故事。

【结尾】
好了，今天的短剧就到这里，喜欢的话记得点赞关注哦！"""

        self.generated_content = sample_content
        self.preview_text.setText(sample_content)
        self.export_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)

        self.status_label.setText("解说生成完成！")
        self.status_label.setStyleSheet("color: #52c41a; font-weight: 500;")

        self.generation_completed.emit(sample_content)

    def _copy_text(self):
        """复制文本到剪贴板"""
        if self.generated_content:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self.generated_content)
            QMessageBox.information(self, "成功", "文本已复制到剪贴板")

    def _edit_text(self):
        """编辑文本"""
        self.preview_text.setReadOnly(False)
        self.preview_text.setStyleSheet("border: 2px solid #1890ff;")
        QMessageBox.information(self, "编辑模式", "现在可以编辑文本内容，编辑完成后点击其他区域保存")

    def _save_text(self):
        """保存文本"""
        self.generated_content = self.preview_text.toPlainText()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("")
        QMessageBox.information(self, "成功", "文本已保存")

    def _export_content(self):
        """导出内容"""
        if not self.generated_content:
            QMessageBox.warning(self, "警告", "没有可导出的内容")
            return

        format_type = self.export_format.currentText()

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"导出{format_type}",
            f"commentary.{self._get_file_extension(format_type)}",
            self._get_file_filter(format_type)
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if format_type == "JSON数据":
                        import json
                        data = {
                            "content": self.generated_content,
                            "style": self.style_combo.currentText(),
                            "length": self.length_slider.value(),
                            "video_path": self.current_video_path
                        }
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    else:
                        f.write(self.generated_content)

                QMessageBox.information(self, "成功", f"文件已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def _get_file_extension(self, format_type):
        """获取文件扩展名"""
        extensions = {
            "SRT字幕文件": "srt",
            "TXT文本文件": "txt",
            "剪映草稿": "json",
            "JSON数据": "json"
        }
        return extensions.get(format_type, "txt")

    def _get_file_filter(self, format_type):
        """获取文件过滤器"""
        filters = {
            "SRT字幕文件": "SRT文件 (*.srt)",
            "TXT文本文件": "文本文件 (*.txt)",
            "剪映草稿": "JSON文件 (*.json)",
            "JSON数据": "JSON文件 (*.json)"
        }
        return filters.get(format_type, "所有文件 (*)")

    def _preview_effect(self):
        """预览效果"""
        QMessageBox.information(
            self,
            "预览功能",
            "预览功能将在后续版本中实现\n\n当前可以：\n- 查看生成的文本内容\n- 编辑和保存文本\n- 导出为多种格式"
        )


class CompilationPanel(AIFeaturePanel):
    """AI高能混剪面板"""

    # 信号
    compilation_started = pyqtSignal()
    compilation_progress = pyqtSignal(int, str)  # 进度和状态
    compilation_completed = pyqtSignal(list)  # 检测到的片段列表

    def __init__(self, parent=None):
        super().__init__(
            title="AI高能混剪",
            description="自动检测视频中的高能/精彩场景，创建激动人心的混剪视频",
            icon="⚡",
            parent=parent
        )

        # 状态变量
        self.current_videos = []
        self.detected_clips = []
        self.is_processing = False

    def _create_content(self) -> QWidget:
        """创建混剪功能内容"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)

        # 视频输入区域
        input_section = self._create_input_section()
        layout.addWidget(input_section)

        # 检测设置区域
        settings_section = self._create_settings_section()
        layout.addWidget(settings_section)

        # 结果预览区域
        results_section = self._create_results_section()
        layout.addWidget(results_section)

        return content

    def _create_input_section(self) -> QWidget:
        """创建输入区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("视频输入")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 视频列表
        input_group = QGroupBox("视频文件列表")
        input_layout = QVBoxLayout(input_group)

        # 文件列表
        self.video_list = QTextEdit()
        self.video_list.setMaximumHeight(120)
        self.video_list.setPlaceholderText("拖拽视频文件到这里，或点击下方按钮添加...")
        self.video_list.setReadOnly(True)
        input_layout.addWidget(self.video_list)

        # 操作按钮
        buttons_layout = QHBoxLayout()

        add_files_btn = QPushButton("📁 添加文件")
        add_files_btn.setObjectName("primary_button")
        add_files_btn.clicked.connect(self._add_video_files)
        buttons_layout.addWidget(add_files_btn)

        add_folder_btn = QPushButton("📂 添加文件夹")
        add_folder_btn.clicked.connect(self._add_video_folder)
        buttons_layout.addWidget(add_folder_btn)

        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.clicked.connect(self._clear_video_list)
        buttons_layout.addWidget(clear_btn)

        buttons_layout.addStretch()
        input_layout.addLayout(buttons_layout)

        layout.addWidget(input_group)

        return widget

    def _create_settings_section(self) -> QWidget:
        """创建设置区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("检测设置")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        settings_group = QGroupBox("高能场景检测参数")
        settings_layout = QFormLayout(settings_group)

        # 检测类型
        self.detection_type = QComboBox()
        self.detection_type.addItems(["动作场景", "情感高潮", "对话精彩", "视觉冲击", "综合检测"])
        settings_layout.addRow("检测类型:", self.detection_type)

        # 敏感度
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(7)
        self.sensitivity_slider.valueChanged.connect(self._update_sensitivity_label)

        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(self.sensitivity_slider)
        self.sensitivity_label = QLabel("高")
        sensitivity_layout.addWidget(self.sensitivity_label)

        sensitivity_widget = QWidget()
        sensitivity_widget.setLayout(sensitivity_layout)
        settings_layout.addRow("检测敏感度:", sensitivity_widget)

        # 片段长度
        self.clip_length = QSpinBox()
        self.clip_length.setRange(3, 30)
        self.clip_length.setValue(8)
        self.clip_length.setSuffix(" 秒")
        settings_layout.addRow("片段长度:", self.clip_length)

        # 最大片段数
        self.max_clips = QSpinBox()
        self.max_clips.setRange(5, 50)
        self.max_clips.setValue(15)
        settings_layout.addRow("最大片段数:", self.max_clips)

        # 高级选项
        self.auto_transition = QCheckBox("自动添加转场效果")
        self.auto_transition.setChecked(True)
        settings_layout.addRow("", self.auto_transition)

        self.background_music = QCheckBox("添加背景音乐")
        settings_layout.addRow("", self.background_music)

        layout.addWidget(settings_group)

        # 开始检测按钮
        action_layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()

        self.start_btn = QPushButton("⚡ 开始检测")
        self.start_btn.setObjectName("primary_button")
        self.start_btn.setMinimumHeight(44)
        self.start_btn.clicked.connect(self._start_detection)
        buttons_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹️ 停止检测")
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_detection)
        buttons_layout.addWidget(self.stop_btn)

        buttons_layout.addStretch()
        action_layout.addLayout(buttons_layout)

        # 进度显示
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        action_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #52c41a; font-weight: 500;")
        action_layout.addWidget(self.status_label)

        layout.addLayout(action_layout)

        return widget

    def _create_results_section(self) -> QWidget:
        """创建结果区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("检测结果")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 结果选项卡
        results_tabs = QTabWidget()

        # 片段列表
        clips_tab = QWidget()
        clips_layout = QVBoxLayout(clips_tab)

        self.clips_list = QTextEdit()
        self.clips_list.setPlaceholderText("检测到的高能片段将在这里显示...")
        self.clips_list.setReadOnly(True)
        clips_layout.addWidget(self.clips_list)

        # 片段操作
        clips_actions = QHBoxLayout()

        select_all_btn = QPushButton("✅ 全选")
        clips_actions.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("❌ 全不选")
        clips_actions.addWidget(deselect_all_btn)

        preview_btn = QPushButton("👁️ 预览片段")
        clips_actions.addWidget(preview_btn)

        clips_actions.addStretch()
        clips_layout.addLayout(clips_actions)

        results_tabs.addTab(clips_tab, "🎬 片段列表")

        # 统计信息
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)

        self.stats_text = QTextEdit()
        self.stats_text.setPlaceholderText("检测统计信息将在这里显示...")
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)

        results_tabs.addTab(stats_tab, "📊 统计信息")

        layout.addWidget(results_tabs)

        # 导出区域
        export_group = QGroupBox("生成混剪")
        export_layout = QVBoxLayout(export_group)

        # 输出设置
        output_layout = QFormLayout()

        self.output_format = QComboBox()
        self.output_format.addItems(["MP4视频", "剪映草稿", "时间点列表"])
        output_layout.addRow("输出格式:", self.output_format)

        self.output_quality = QComboBox()
        self.output_quality.addItems(["高质量", "标准质量", "快速预览"])
        output_layout.addRow("输出质量:", self.output_quality)

        export_layout.addLayout(output_layout)

        # 生成按钮
        generate_layout = QHBoxLayout()

        self.generate_btn = QPushButton("🎬 生成混剪")
        self.generate_btn.setObjectName("primary_button")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self._generate_compilation)
        generate_layout.addWidget(self.generate_btn)

        self.export_btn = QPushButton("📤 导出结果")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_results)
        generate_layout.addWidget(self.export_btn)

        generate_layout.addStretch()
        export_layout.addLayout(generate_layout)

        layout.addWidget(export_group)

        return widget

    def _add_video_files(self):
        """添加视频文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;所有文件 (*)"
        )

        if files:
            self.current_videos.extend(files)
            self._update_video_list()

    def _add_video_folder(self):
        """添加视频文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择包含视频的文件夹")

        if folder:
            import os
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
            video_files = []

            for root, dirs, files in os.walk(folder):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in video_extensions):
                        video_files.append(os.path.join(root, file))

            if video_files:
                self.current_videos.extend(video_files)
                self._update_video_list()
                QMessageBox.information(self, "成功", f"添加了 {len(video_files)} 个视频文件")
            else:
                QMessageBox.information(self, "提示", "所选文件夹中没有找到视频文件")

    def _clear_video_list(self):
        """清空视频列表"""
        self.current_videos.clear()
        self._update_video_list()

    def _update_video_list(self):
        """更新视频列表显示"""
        if self.current_videos:
            import os
            file_list = "\n".join([f"• {os.path.basename(f)}" for f in self.current_videos])
            self.video_list.setText(f"已添加 {len(self.current_videos)} 个视频文件:\n\n{file_list}")
            self.start_btn.setEnabled(True)
        else:
            self.video_list.setText("")
            self.start_btn.setEnabled(False)

    def _update_sensitivity_label(self, value):
        """更新敏感度标签"""
        labels = ["极低", "很低", "低", "较低", "中等", "较高", "高", "很高", "极高", "最高"]
        if 1 <= value <= 10:
            self.sensitivity_label.setText(labels[value - 1])

    def _start_detection(self):
        """开始检测"""
        if not self.current_videos:
            QMessageBox.warning(self, "警告", "请先添加视频文件")
            return

        self.is_processing = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 模拟检测过程
        self._simulate_detection()

        self.compilation_started.emit()

    def _stop_detection(self):
        """停止检测"""
        self.is_processing = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("检测已停止")
        self.status_label.setStyleSheet("color: #ff4d4f; font-weight: 500;")

    def _simulate_detection(self):
        """模拟检测过程"""
        self.detection_timer = QTimer()
        self.detection_progress = 0

        def update_detection():
            self.detection_progress += 3
            self.progress_bar.setValue(self.detection_progress)

            if self.detection_progress == 15:
                self.status_label.setText("正在分析视频内容...")
            elif self.detection_progress == 30:
                self.status_label.setText("正在检测动作场景...")
            elif self.detection_progress == 50:
                self.status_label.setText("正在分析情感变化...")
            elif self.detection_progress == 70:
                self.status_label.setText("正在评估场景质量...")
            elif self.detection_progress == 90:
                self.status_label.setText("正在生成结果...")
            elif self.detection_progress >= 100:
                self.detection_timer.stop()
                self._detection_completed()

        self.detection_timer.timeout.connect(update_detection)
        self.detection_timer.start(150)

    def _detection_completed(self):
        """检测完成"""
        self.is_processing = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        # 模拟检测结果
        sample_clips = [
            "视频1 - 00:15-00:23: 动作场景 (评分: 9.2)",
            "视频1 - 01:45-01:53: 情感高潮 (评分: 8.8)",
            "视频2 - 00:32-00:40: 视觉冲击 (评分: 9.5)",
            "视频2 - 02:10-02:18: 对话精彩 (评分: 8.5)",
            "视频3 - 00:58-01:06: 动作场景 (评分: 9.0)"
        ]

        self.detected_clips = sample_clips
        clips_text = "\n".join([f"✅ {clip}" for clip in sample_clips])
        self.clips_list.setText(f"检测到 {len(sample_clips)} 个高能片段:\n\n{clips_text}")

        # 统计信息
        stats_text = f"""检测统计信息:

📊 总体统计:
• 处理视频数量: {len(self.current_videos)}
• 检测到片段: {len(sample_clips)}
• 平均评分: 9.0
• 总时长: {len(sample_clips) * 8} 秒

🎯 场景类型分布:
• 动作场景: 2 个
• 情感高潮: 1 个
• 视觉冲击: 1 个
• 对话精彩: 1 个

⚙️ 检测参数:
• 检测类型: {self.detection_type.currentText()}
• 敏感度: {self.sensitivity_label.text()}
• 片段长度: {self.clip_length.value()} 秒"""

        self.stats_text.setText(stats_text)

        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        self.status_label.setText("检测完成！")
        self.status_label.setStyleSheet("color: #52c41a; font-weight: 500;")

        self.compilation_completed.emit(sample_clips)

    def _generate_compilation(self):
        """生成混剪"""
        if not self.detected_clips:
            QMessageBox.warning(self, "警告", "没有检测到可用的片段")
            return

        QMessageBox.information(
            self,
            "生成混剪",
            f"将生成包含 {len(self.detected_clips)} 个片段的混剪视频\n\n"
            f"输出格式: {self.output_format.currentText()}\n"
            f"输出质量: {self.output_quality.currentText()}\n\n"
            "此功能将在后续版本中完整实现"
        )

    def _export_results(self):
        """导出结果"""
        if not self.detected_clips:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出检测结果",
            "compilation_results.txt",
            "文本文件 (*.txt);;JSON文件 (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("AI高能混剪检测结果\n")
                    f.write("=" * 30 + "\n\n")
                    for i, clip in enumerate(self.detected_clips, 1):
                        f.write(f"{i}. {clip}\n")

                QMessageBox.information(self, "成功", f"结果已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")


class MonologuePanel(AIFeaturePanel):
    """AI第一人称独白面板"""

    # 信号
    monologue_started = pyqtSignal()
    monologue_progress = pyqtSignal(int, str)
    monologue_completed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(
            title="AI第一人称独白",
            description="生成第一人称叙述内容，自动插入相关原始片段",
            icon="🎭",
            parent=parent
        )

        # 状态变量
        self.current_video_path = ""
        self.generated_monologue = ""
        self.is_generating = False

    def _create_content(self) -> QWidget:
        """创建独白功能内容"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)

        # 输入设置区域
        input_section = self._create_input_section()
        layout.addWidget(input_section)

        # 角色设置区域
        character_section = self._create_character_section()
        layout.addWidget(character_section)

        # 生成结果区域
        result_section = self._create_result_section()
        layout.addWidget(result_section)

        return content

    def _create_input_section(self) -> QWidget:
        """创建输入区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("视频输入")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 视频选择
        video_group = QGroupBox("选择视频文件")
        video_layout = QVBoxLayout(video_group)

        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("color: #595959; padding: 8px; border: 1px dashed #d9d9d9; border-radius: 4px;")
        file_layout.addWidget(self.file_path_label)

        select_btn = QPushButton("📁 选择视频")
        select_btn.setObjectName("primary_button")
        select_btn.clicked.connect(self._select_video)
        file_layout.addWidget(select_btn)

        video_layout.addLayout(file_layout)
        layout.addWidget(video_group)

        return widget

    def _create_character_section(self) -> QWidget:
        """创建角色设置区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("角色设置")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        character_group = QGroupBox("第一人称角色配置")
        character_layout = QFormLayout(character_group)

        # 角色类型
        self.character_type = QComboBox()
        self.character_type.addItems([
            "主角视角", "旁观者视角", "回忆者视角",
            "解说者视角", "参与者视角", "自定义角色"
        ])
        character_layout.addRow("角色类型:", self.character_type)

        # 情感基调
        self.emotion_tone = QComboBox()
        self.emotion_tone.addItems([
            "平静叙述", "激动兴奋", "深沉思考",
            "幽默轻松", "紧张悬疑", "感动温馨"
        ])
        character_layout.addRow("情感基调:", self.emotion_tone)

        # 叙述风格
        self.narrative_style = QComboBox()
        self.narrative_style.addItems([
            "现在时叙述", "过去时回忆", "未来时展望",
            "对话式叙述", "内心独白", "日记体"
        ])
        character_layout.addRow("叙述风格:", self.narrative_style)

        # 个性化设置
        self.personality_text = QTextEdit()
        self.personality_text.setPlaceholderText("描述角色的个性特点、说话习惯等（可选）...")
        self.personality_text.setMaximumHeight(80)
        character_layout.addRow("个性化描述:", self.personality_text)

        layout.addWidget(character_group)

        # 生成控制
        control_layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()

        self.generate_btn = QPushButton("🎭 生成独白")
        self.generate_btn.setObjectName("primary_button")
        self.generate_btn.setMinimumHeight(44)
        self.generate_btn.clicked.connect(self._start_generation)
        self.generate_btn.setEnabled(False)
        buttons_layout.addWidget(self.generate_btn)

        self.stop_btn = QPushButton("⏹️ 停止生成")
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_generation)
        buttons_layout.addWidget(self.stop_btn)

        buttons_layout.addStretch()
        control_layout.addLayout(buttons_layout)

        # 进度显示
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("请先选择视频文件")
        self.status_label.setStyleSheet("color: #595959; font-weight: 500;")
        control_layout.addWidget(self.status_label)

        layout.addLayout(control_layout)

        return widget

    def _create_result_section(self) -> QWidget:
        """创建结果区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("生成结果")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 结果显示
        result_group = QGroupBox("独白内容")
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setPlaceholderText("生成的第一人称独白将在这里显示...")
        self.result_text.setMinimumHeight(200)
        result_layout.addWidget(self.result_text)

        # 操作按钮
        actions_layout = QHBoxLayout()

        self.regenerate_btn = QPushButton("🔄 重新生成")
        self.regenerate_btn.setEnabled(False)
        self.regenerate_btn.clicked.connect(self._regenerate)
        actions_layout.addWidget(self.regenerate_btn)

        self.edit_btn = QPushButton("✏️ 编辑内容")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._edit_content)
        actions_layout.addWidget(self.edit_btn)

        self.save_btn = QPushButton("💾 保存内容")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_content)
        actions_layout.addWidget(self.save_btn)

        actions_layout.addStretch()
        result_layout.addLayout(actions_layout)

        layout.addWidget(result_group)

        # 导出选项
        export_group = QGroupBox("导出选项")
        export_layout = QVBoxLayout(export_group)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("导出格式:"))

        self.export_format = QComboBox()
        self.export_format.addItems(["文本文件", "SRT字幕", "剪映草稿", "语音合成脚本"])
        format_layout.addWidget(self.export_format)

        format_layout.addStretch()
        export_layout.addLayout(format_layout)

        export_actions = QHBoxLayout()

        self.export_btn = QPushButton("📤 导出文件")
        self.export_btn.setObjectName("primary_button")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_content)
        export_actions.addWidget(self.export_btn)

        self.preview_voice_btn = QPushButton("🔊 语音预览")
        self.preview_voice_btn.setMinimumHeight(40)
        self.preview_voice_btn.setEnabled(False)
        self.preview_voice_btn.clicked.connect(self._preview_voice)
        export_actions.addWidget(self.preview_voice_btn)

        export_actions.addStretch()
        export_layout.addLayout(export_actions)

        layout.addWidget(export_group)

        return widget

    def _select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;所有文件 (*)"
        )

        if file_path:
            self.current_video_path = file_path
            import os
            filename = os.path.basename(file_path)
            self.file_path_label.setText(f"已选择: {filename}")
            self.file_path_label.setStyleSheet("color: #52c41a; padding: 8px; border: 1px solid #52c41a; border-radius: 4px; background-color: #f6ffed;")
            self.generate_btn.setEnabled(True)
            self.status_label.setText("视频已选择，可以开始生成独白")
            self.status_label.setStyleSheet("color: #52c41a; font-weight: 500;")

    def _start_generation(self):
        """开始生成独白"""
        if not self.current_video_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return

        self.is_generating = True
        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 模拟生成过程
        self._simulate_generation()

        self.monologue_started.emit()

    def _stop_generation(self):
        """停止生成"""
        self.is_generating = False
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("生成已停止")
        self.status_label.setStyleSheet("color: #ff4d4f; font-weight: 500;")

    def _simulate_generation(self):
        """模拟生成过程"""
        self.generation_timer = QTimer()
        self.generation_progress = 0

        def update_progress():
            self.generation_progress += 4
            self.progress_bar.setValue(self.generation_progress)

            if self.generation_progress == 20:
                self.status_label.setText("正在分析视频内容...")
            elif self.generation_progress == 40:
                self.status_label.setText("正在构建角色视角...")
            elif self.generation_progress == 60:
                self.status_label.setText("正在生成独白文本...")
            elif self.generation_progress == 80:
                self.status_label.setText("正在优化语言风格...")
            elif self.generation_progress >= 100:
                self.generation_timer.stop()
                self._generation_completed()

        self.generation_timer.timeout.connect(update_progress)
        self.generation_timer.start(180)

    def _generation_completed(self):
        """生成完成"""
        self.is_generating = False
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        # 模拟生成的独白内容
        character_type = self.character_type.currentText()
        emotion_tone = self.emotion_tone.currentText()

        sample_monologue = f"""我是这个故事的{character_type.replace('视角', '')}，让我来告诉你我所经历的一切。

当我第一次看到这个场景时，我的心情是{emotion_tone.replace('叙述', '').replace('式', '')}的。那一刻，我意识到这不仅仅是一个普通的故事。

我记得那天的阳光特别明亮，就像现在你看到的画面一样。我站在那里，心中涌起了千万种情感。

这个经历改变了我对很多事情的看法。如果你也经历过类似的情况，你一定能理解我当时的感受。

现在回想起来，我觉得那是我人生中最重要的时刻之一。它让我明白了什么是真正重要的。

这就是我想要分享给你的故事，希望它也能给你带来一些启发。"""

        self.generated_monologue = sample_monologue
        self.result_text.setText(sample_monologue)

        # 启用相关按钮
        self.regenerate_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.preview_voice_btn.setEnabled(True)

        self.status_label.setText("独白生成完成！")
        self.status_label.setStyleSheet("color: #52c41a; font-weight: 500;")

        self.monologue_completed.emit(sample_monologue)

    def _regenerate(self):
        """重新生成"""
        reply = QMessageBox.question(
            self, "确认", "确定要重新生成独白吗？当前内容将被覆盖。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._start_generation()

    def _edit_content(self):
        """编辑内容"""
        self.result_text.setReadOnly(False)
        self.result_text.setStyleSheet("border: 2px solid #1890ff;")
        self.edit_btn.setText("✅ 完成编辑")
        self.edit_btn.clicked.disconnect()
        self.edit_btn.clicked.connect(self._finish_editing)

    def _finish_editing(self):
        """完成编辑"""
        self.generated_monologue = self.result_text.toPlainText()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("")
        self.edit_btn.setText("✏️ 编辑内容")
        self.edit_btn.clicked.disconnect()
        self.edit_btn.clicked.connect(self._edit_content)
        QMessageBox.information(self, "成功", "内容编辑完成")

    def _save_content(self):
        """保存内容"""
        if not self.generated_monologue:
            QMessageBox.warning(self, "警告", "没有可保存的内容")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存独白内容",
            "monologue.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.generated_monologue)
                QMessageBox.information(self, "成功", f"内容已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def _export_content(self):
        """导出内容"""
        if not self.generated_monologue:
            QMessageBox.warning(self, "警告", "没有可导出的内容")
            return

        format_type = self.export_format.currentText()

        extensions = {
            "文本文件": "txt",
            "SRT字幕": "srt",
            "剪映草稿": "json",
            "语音合成脚本": "txt"
        }

        ext = extensions.get(format_type, "txt")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"导出{format_type}",
            f"monologue.{ext}",
            f"{format_type} (*.{ext});;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if format_type == "SRT字幕":
                        # 简单的SRT格式转换
                        lines = self.generated_monologue.split('\n')
                        for i, line in enumerate(lines, 1):
                            if line.strip():
                                start_time = f"00:00:{(i-1)*3:02d},000"
                                end_time = f"00:00:{i*3:02d},000"
                                f.write(f"{i}\n{start_time} --> {end_time}\n{line.strip()}\n\n")
                    elif format_type == "剪映草稿":
                        import json
                        data = {
                            "monologue": self.generated_monologue,
                            "character_type": self.character_type.currentText(),
                            "emotion_tone": self.emotion_tone.currentText(),
                            "narrative_style": self.narrative_style.currentText()
                        }
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    else:
                        f.write(self.generated_monologue)

                QMessageBox.information(self, "成功", f"文件已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def _preview_voice(self):
        """语音预览"""
        QMessageBox.information(
            self,
            "语音预览",
            "语音合成预览功能将在后续版本中实现\n\n"
            "当前支持的功能：\n"
            "- 文本内容生成和编辑\n"
            "- 多种格式导出\n"
            "- 角色个性化设置"
        )


class AIFeaturesPage(QWidget):
    """AI功能页面"""
    
    def __init__(self, ai_manager: AIManager, parent=None):
        super().__init__(parent)
        
        self.ai_manager = ai_manager
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)
        
        # 添加功能面板
        self.commentary_panel = CommentaryPanel()
        self.tab_widget.addTab(self.commentary_panel, "🎬 AI短剧解说")
        
        self.compilation_panel = CompilationPanel()
        self.tab_widget.addTab(self.compilation_panel, "⚡ AI高能混剪")
        
        self.monologue_panel = MonologuePanel()
        self.tab_widget.addTab(self.monologue_panel, "🎭 AI第一人称独白")
        
        layout.addWidget(self.tab_widget)
        
        # 应用样式
        self._apply_styles()
    
    def _apply_styles(self):
        """应用样式"""
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #f0f0f0;
                background-color: #ffffff;
                border-radius: 6px;
            }
            
            QTabBar::tab {
                background-color: #fafafa;
                border: 1px solid #f0f0f0;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 12px 20px;
                margin-right: 2px;
                color: #595959;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1890ff;
                border-color: #1890ff;
                border-bottom: 2px solid #1890ff;
                font-weight: 600;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #f5f5f5;
                color: #262626;
            }
        """)
