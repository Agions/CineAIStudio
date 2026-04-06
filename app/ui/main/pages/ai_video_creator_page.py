#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Narrafiilm - AI 视频创作页面
提供三大核心功能的图形界面:
- AI 视频解说
- AI 视频混剪
- AI 第一人称独白
"""

import os
from pathlib import Path
from typing import List, Callable
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar, QComboBox, QSpinBox,
    QTabWidget, QListWidget, QListWidgetItem, QSplitter,
    QSlider, QCheckBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from .base_page import BasePage
from app.ui.components import (
    MacCard, MacTitleLabel, MacPrimaryButton, MacSecondaryButton, MacLabel,
    MacScrollArea
)


class CreationType(Enum):
    """创作类型"""
    COMMENTARY = "解说视频"
    MASHUP = "混剪视频"
    MONOLOGUE = "独白视频"


class WorkerThread(QThread):
    """后台工作线程"""
    progress = Signal(str, float)  # stage, progress
    finished = Signal(str)         # result path
    error = Signal(str)            # error message
    
    def __init__(self, task_func: Callable, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.task_func(*self.args, **self.kwargs)
            self.finished.emit(str(result) if result else "完成")
        except Exception as e:
            self.error.emit(str(e))


class VideoPreviewWidget(QWidget):
    """视频预览组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_player()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频容器
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(200)
        # 样式移至 modern.qss
        layout.addWidget(self.video_widget)
        
        # 控制栏
        controls = QHBoxLayout()
        controls.setContentsMargins(5, 5, 5, 5)
        
        self.play_btn = QPushButton("▶") 
        self.play_btn.setFixedSize(32, 32)
        self.play_btn.clicked.connect(self._toggle_playback)
        controls.addWidget(self.play_btn)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.sliderMoved.connect(self._set_position)
        controls.addWidget(self.slider)
        
        layout.addLayout(controls)
        
    def _setup_player(self):
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)
        
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        
    def load_video(self, path: str):
        self.player.setSource(QUrl.fromLocalFile(path))
        self.play_btn.setText("▶")
        
    def _toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()
            
    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")
            
    def _on_position_changed(self, position):
        if not self.slider.isSliderDown():
            self.slider.setValue(position)
            
    def _on_duration_changed(self, duration):
        self.slider.setRange(0, duration)
        
    def _set_position(self, position):
        self.player.setPosition(position)


class VideoDropZone(QFrame):
    """视频拖放区域"""
    
    files_dropped = Signal(list)
    
    def __init__(self, parent=None, multiple=False):
        super().__init__(parent)
        self.multiple = multiple
        self.files = []
        self._setup_ui()
        self.setAcceptDrops(True)
    
    def _setup_ui(self):
        self.setMinimumHeight(120)
        # 样式已移至 modern.qss (VideoDropZone)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图标
        icon_label = QLabel("📹")
        icon_label.setFont(QFont("", 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # 文字
        text = "拖放视频到这里" if not self.multiple else "拖放多个视频到这里"
        self.label = QLabel(text)
        self.label.setStyleSheet("color: #888; font-size: 14px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        # 按钮
        btn = QPushButton("选择文件")
        btn.clicked.connect(self._select_files)
        btn.setObjectName("primary_button")
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def _select_files(self):
        try:
            if self.multiple:
                files, _ = QFileDialog.getOpenFileNames(
                    self, "选择视频文件", "",
                    "视频文件 (*.mp4 *.mov *.avi *.mkv);;所有文件 (*)"
                )
            else:
                file, _ = QFileDialog.getOpenFileName(
                    self, "选择视频文件", "",
                    "视频文件 (*.mp4 *.mov *.avi *.mkv);;所有文件 (*)"
                )
                files = [file] if file else []
            
            if files:
                self.files = files
                self._update_display()
                self.files_dropped.emit(files)
        except Exception as e:
            print(f"Error opening file dialog: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "错误", f"无法打开文件选择对话框: {e}")
    
    def _update_display(self):
        if self.files:
            if len(self.files) == 1:
                name = Path(self.files[0]).name
                self.label.setText(f"✅ {name}")
            else:
                self.label.setText(f"✅ 已选择 {len(self.files)} 个视频")
            self.setStyleSheet(self.styleSheet().replace("dashed", "solid"))
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet().replace("#555", "#007AFF"))
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("#007AFF", "#555"))
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                files.append(path)
        
        if files:
            if not self.multiple:
                files = files[:1]
            self.files = files
            self._update_display()
            self.files_dropped.emit(files)
        
        self.setStyleSheet(self.styleSheet().replace("#007AFF", "#555"))


class AIVideoCreatorPage(BasePage):
    """
    AI 视频创作页面
    
    集成三大核心功能的图形界面
    """
    
    creation_started = Signal(str)    # creation type
    creation_finished = Signal(str)   # output path
    creation_error = Signal(str)      # error message
    
    def __init__(self, application):
        super().__init__("ai_video_creator", "AI 视频创作", application)
        self.current_project = None
        self.worker_thread = None
        self._imported_voice_path = None  # 外部导入的配音路径
        
    def initialize(self) -> bool:
        """初始化页面"""
        return True

    def create_content(self) -> None:
        """创建页面内容"""
        # 使用 BasePage 的 main_layout
        layout = self.main_layout
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("🎬 AI 视频创作")
        title.setFont(QFont("", 24, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 帮助按钮
        help_btn = QPushButton("使用帮助")
        help_btn.clicked.connect(self._show_help)
        title_layout.addWidget(help_btn)
        
        layout.addLayout(title_layout)
        
        # 功能选项卡
        self.tabs = QTabWidget()
        # 样式已移至 modern.qss
        
        # 添加三个功能页面
        self.tabs.addTab(self._create_monologue_tab(), "🎭 AI 独白")
        
        layout.addWidget(self.tabs)
        
        # 底部操作栏
        layout.addWidget(self._create_action_bar())
    
    def _create_form_group(self, label_text: str, input_widget: QWidget) -> QWidget:
        """创建垂直排列的表单组 (标签在上，输入框在下)"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        label = MacLabel(label_text, "text-secondary text-bold")
        layout.addWidget(label)
        layout.addWidget(input_widget)
        
        return container

    def _create_monologue_tab(self) -> QWidget:
        """创建独白功能页面 (macOS 风格 - 优化版)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        
        # === 左侧 ===
        left_scroll = MacScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 16, 0)
        left_layout.setSpacing(20)
        
        # 1. 视频卡片（支持多集素材）
        video_card = MacCard()
        video_card.layout().addWidget(MacTitleLabel("素材导入", 4))

        multi_hint = QLabel("支持拖入多集素材")
        multi_hint.setStyleSheet("color: #888; font-size: 12px;")
        video_card.layout().addWidget(multi_hint)

        self.monologue_video_drop = VideoDropZone(multiple=True)
        video_card.layout().addWidget(self.monologue_video_drop)
        
        # 视频预览 (独立实例)
        self.monologue_preview = VideoPreviewWidget()
        self.monologue_preview.setMinimumHeight(200)
        self.monologue_preview.hide()
        video_card.layout().addWidget(self.monologue_preview)
        
        self.monologue_video_drop.files_dropped.connect(
            lambda files: self._show_video_preview(self.monologue_preview, files[0])
        )
        
        left_layout.addWidget(video_card)
        
        # 2. 情感设置
        emotion_card = MacCard()
        emotion_card.layout().addWidget(MacTitleLabel("情感设置", 4))
        
        emotion_layout = QVBoxLayout()
        emotion_layout.setSpacing(16)
        
        self.monologue_context = QLineEdit()
        self.monologue_context.setPlaceholderText("例如：深夜独自走在城市街头，思绪万千")
        self.monologue_context.setProperty("class", "input")
        emotion_layout.addWidget(self._create_form_group("场景描述", self.monologue_context))
        
        self.monologue_emotion = QComboBox()
        self.monologue_emotion.setProperty("class", "input")
        self.monologue_emotion.addItems([
            "惆怅 - 淡淡忧伤",
            "励志 - 积极向上",
            "治愈 - 温暖人心",
            "思念 - 深情款款",
            "平静 - 岁月静好",
            "神秘 - 引人入胜",
        ])
        emotion_layout.addWidget(self._create_form_group("情感基调", self.monologue_emotion))
        
        self.monologue_style = QComboBox()
        self.monologue_style.setProperty("class", "input")
        self.monologue_style.addItems([
            "抒情散文 - 优美文艺",
            "内心独白 - 真实自然",
            "诗意表达 - 意境深远",
            "故事旁白 - 娓娓道来",
        ])
        emotion_layout.addWidget(self._create_form_group("独白风格", self.monologue_style))

        # 字幕
        self.monologue_subtitle_style = QComboBox()
        self.monologue_subtitle_style.setProperty("class", "input")
        self.monologue_subtitle_style.addItems(["电影感 (黄金)", "文艺 (宋体)", "极简 (白/黑)"])
        emotion_layout.addWidget(self._create_form_group("字幕样式", self.monologue_subtitle_style))
        
        emotion_card.layout().addLayout(emotion_layout)
        left_layout.addWidget(emotion_card)
        left_layout.addStretch()
        
        left_scroll.setWidget(left_panel)
        splitter.addWidget(left_scroll)
        
        # === 右侧：独白文案 ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        script_card = MacCard()
        script_card.layout().addWidget(MacTitleLabel("独白文案", 4))
        
        analyze_btn = MacPrimaryButton("🎭 分析画面情感")
        analyze_btn.clicked.connect(self._analyze_monologue_video)
        script_card.layout().addWidget(analyze_btn)
        
        self.monologue_script = QTextEdit()
        self.monologue_script.setProperty("class", "input")
        self.monologue_script.setPlaceholderText(
            "AI 将基于视频画面情感分析生成第一人称独白\n\n"
            "独白将以沉浸式风格呈现，与画面情感同步"
        )
        self.monologue_script.setMinimumHeight(400)
        script_card.layout().addWidget(self.monologue_script)
        
        right_layout.addWidget(script_card)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 550])
        
        layout.addWidget(splitter)
        
        return widget
    
    def _create_action_bar(self) -> QWidget:
        """创建底部操作栏"""
        widget = QFrame()
        widget.setObjectName("action_bar")  # 使用 QSS 样式
        
        layout = QHBoxLayout(widget)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v")
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumWidth(300)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 输出目录
        layout.addWidget(QLabel("输出目录:"))
        self.output_dir = QLineEdit()
        self.output_dir.setText(str(Path.home() / "Documents" / "Narrafiilm"))
        self.output_dir.setMinimumWidth(200)
        layout.addWidget(self.output_dir)
        
        output_btn = QPushButton("📁")
        output_btn.clicked.connect(self._select_output_dir)
        layout.addWidget(output_btn)
        
        # 开始按钮
        self.start_btn = QPushButton("🚀 开始创作")
        self.start_btn.clicked.connect(self._start_creation)
        self.start_btn.setObjectName("primary_button")
        self.start_btn.setMinimumHeight(36)
        layout.addWidget(self.start_btn)
        
        return widget
    
    # === 事件处理 ===
    

    def _select_output_dir(self):
        """选择输出目录"""
        try:
            dir_path = QFileDialog.getExistingDirectory(
                self, "选择输出目录",
                self.output_dir.text()
            )
            if dir_path:
                self.output_dir.setText(dir_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开目录选择框: {e}")
    

    def _analyze_monologue_video(self):
        """分析独白视频"""
        if not self.monologue_video_drop.files:
            QMessageBox.warning(self, "提示", "请先选择视频文件")
            return
            
        # 检查 API Key
        api_key = self.get_config_value("ai_config.api_key", "")
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY") # Fallback
            
        if not api_key:
            reply = QMessageBox.question(
                self, "缺少 API Key",
                "未配置 AI 服务 API Key（需在设置中配置）。\n\n是否使用模拟数据进行功能演示？\n(将返回固定的测试结果)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            self._use_mock_analysis = True
        else:
            self._use_mock_analysis = False
        
        self._start_video_analysis(
            self.monologue_video_drop.files[0],
            self.monologue_script,
            "monologue"
        )
    
    def _start_video_analysis(self, video_path: str, output_widget: QTextEdit, mode: str):
        """开始视频分析"""
        self.status_label.setText("正在分析视频画面...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 获取 API Key (优先从配置)
        config_api_key = self.get_config_value("ai_config.api_key", "")
        # 如果配置为空，尝试环境变量
        if not config_api_key:
            config_api_key = os.getenv("OPENAI_API_KEY")

        def analyze():
            # 使用绝对导入
            from app.services.ai.video_content_analyzer import VideoContentAnalyzer
            
            # 如果是模拟模式，直接返回模拟结果
            if getattr(self, '_use_mock_analysis', False):
                import time
                time.sleep(1.5) # 模拟耗时
                return None # 返回 None 触发后续的模拟文案生成
            
            # 使用外部获取的 key
            api_key = config_api_key
            
            analyzer = VideoContentAnalyzer(vision_api_key=api_key)
            result = analyzer.analyze(video_path)
            
            return result
        
        def on_finished(result):
            self.progress_bar.setVisible(False)
            self.status_label.setText("分析完成")
            
            # 显示结果
            try:
                if result and hasattr(result, 'script_suggestion') and result.script_suggestion:
                    output_widget.setText(result.script_suggestion)
                else:
                    # 提示用户手动输入
                    placeholder = "AI 分析未返回结果，请手动输入文案。\n\n" if mode == "commentary" else "AI 分析未返回结果，请手动输入独白。\n\n"
                    output_widget.setPlaceholderText(placeholder + output_widget.placeholderText())
                    QMessageBox.information(self, "提示", "AI 分析完成，但未生成文案。请手动输入或调整设置后重试。")
            except Exception as e:
                placeholder = "分析出错，请手动输入文案。\n\n" if mode == "commentary" else "分析出错，请手动输入独白。\n\n"
                output_widget.setPlaceholderText(placeholder + output_widget.placeholderText())
                QMessageBox.warning(self, "错误", f"处理分析结果时出错: {e}\n\n请手动输入文案。")
        
        def on_error(error: str):
            self.progress_bar.setVisible(False)
            self.status_label.setText("分析失败")
            
            # 提示用户手动输入
            QMessageBox.warning(self, "分析失败", f"视频分析失败: {error}\n\n请手动输入文案或检查 API 配置。")
        
        # 启动线程
        self.worker_thread = WorkerThread(analyze)
        self.worker_thread.finished.connect(on_finished)
        self.worker_thread.error.connect(on_error)
        self.worker_thread.start()
    

    
    def _start_creation(self):
        """开始创作（仅第一人称解说模式）"""
        self._start_monologue_creation()
    
    def _start_monologue_creation(self):
        """开始独白视频创作"""
        if not self.monologue_video_drop.files:
            QMessageBox.warning(self, "提示", "请先选择视频文件")
            return
        
        if not self.monologue_script.toPlainText().strip():
            QMessageBox.warning(self, "提示", "请先生成或输入独白文案")
            return
        
    def _on_import_voice(self):
        """导入外部配音文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配音文件", "",
            "音频文件 (*.mp3 *.wav *.m4a *.flac *.ogg *.aac);;所有文件 (*)"
        )
        if file_path:
            self._imported_voice_path = file_path
            name = Path(file_path).name
            # Voice file imported (path stored in self._imported_voice_path)

    def _show_video_preview(self, preview_widget: VideoPreviewWidget, file_path: str):
        """显示视频预览"""
        preview_widget.show()
        preview_widget.load_video(file_path)

    def _run_creation_task(self, task_type: str, task_func: Callable):
        """运行创作任务"""
        self.start_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在创作中...")
        
        def on_progress(stage: str, progress: float):
            self.progress_bar.setValue(int(progress * 100))
            self.status_label.setText(stage)
        
        self.worker_thread = WorkerThread(task_func)
        self.worker_thread.progress.connect(on_progress)
        self.worker_thread.finished.connect(self._on_creation_finished)
        self.worker_thread.error.connect(self._on_creation_error)
        self.worker_thread.start()
    
    def _create_monologue(self) -> str:
        """创建独白视频"""
        from app.services.video.monologue_maker import MonologueMaker, MonologueStyle
        
        maker = MonologueMaker(voice_provider="edge")
        maker.set_progress_callback(lambda stage, p: self.worker_thread.progress.emit(stage, p))
        
        # 获取设置
        video_path = self.monologue_video_drop.files[0]
        context = self.monologue_context.text() or "深夜独自一人"
        script = self.monologue_script.toPlainText()
        output_dir = self.output_dir.text()
        
        # 情感解析
        emotion_text = self.monologue_emotion.currentText().split(" - ")[0]
        
        # 风格映射
        style_map = {
            "抒情": MonologueStyle.MELANCHOLIC,
            "内心": MonologueStyle.NOSTALGIC,
            "诗意": MonologueStyle.PHILOSOPHICAL,
            "故事": MonologueStyle.ROMANTIC
        }
        current_style = self.monologue_style.currentText()
        style = next((v for k, v in style_map.items() if k in current_style), MonologueStyle.MELANCHOLIC)
        
        # 字幕样式映射
        sub_style_map = {
            "电影": "cinematic",
            "文艺": "minimal",
            "极简": "minimal",
        }
        current_sub = self.monologue_subtitle_style.currentText()
        sub_style = next((v for k, v in sub_style_map.items() if k in current_sub), "cinematic")
        
        # 创建项目
        project = maker.create_project(
            source_video=video_path,
            context=context,
            emotion=emotion_text,
            style=style,
            output_dir=os.path.join(output_dir, "monologue"),
        )
        
        # 生成内容
        maker.generate_script(project, custom_script=script if script else None)
        maker.generate_voice(project)
        maker.generate_captions(project, style=sub_style)
        
        # 导出
        draft_path = maker.export_to_jianying(project, output_dir + "/jianying_drafts")
        
        return draft_path
    
    def _on_creation_finished(self, result: str):
        """创作完成"""
        self.start_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText("创作完成！")
        
        QMessageBox.information(
            self, "创作完成",
            f"视频项目已成功创建！\n\n"
            f"剪映草稿已导出至:\n{result}\n\n"
            f"您可以在剪映中打开继续编辑"
        )
        
        self.creation_finished.emit(result)
    
    def _on_creation_error(self, error: str):
        """创作失败"""
        self.start_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("创作失败")
        
        QMessageBox.critical(self, "创作失败", f"视频创作过程中发生错误:\n\n{error}")
        
        self.creation_error.emit(error)
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
🎬 Narrafiilm 使用帮助

【AI 视频解说】
1. 选择源视频文件
2. 输入解说主题
3. 点击"分析视频画面"自动生成文案
4. 调整文案后点击"开始创作"
5. 导出的剪映草稿可在剪映中打开

【AI 视频混剪】
1. 选择多个视频素材（至少 2 个）
2. 可选择背景音乐
3. 设置目标时长和混剪风格
4. 点击"开始创作"自动智能混剪
5. 会自动匹配音乐节拍

【AI 第一人称独白】
1. 选择源视频文件
2. 描述场景和情感
3. 点击"分析画面情感"生成独白
4. 调整独白后点击"开始创作"
5. 会生成电影级字幕效果

【提示】
• 配音使用免费的 Edge TTS，无需 API
• 画面分析需要 OPENAI_API_KEY
• 没有 API 也可以手动输入文案
        """
        
        try:
            QMessageBox.information(self, "使用帮助", help_text)
        except Exception as e:
            print(f"Error showing help: {e}")
    
    def get_page_name(self) -> str:
        return "AI 视频创作"
    
    def get_page_icon(self) -> str:
        return "🎬"
