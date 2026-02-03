#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio - AI 视频创作页面
提供三大核心功能的图形界面:
- AI 视频解说
- AI 视频混剪
- AI 第一人称独白
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar, QComboBox, QSpinBox,
    QTabWidget, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QSlider, QCheckBox, QFrame, QScrollArea,
    QMessageBox, QStackedWidget, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QUrl
from PyQt6.QtGui import QFont, QIcon, QPixmap, QDragEnterEvent, QDropEvent
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from .base_page import BasePage
from app.ui.common.macOS_components import (
    MacCard, MacTitleLabel, MacPrimaryButton, MacSecondaryButton, MacLabel,
    MacGrid, MacScrollArea
)
from app.services.video.commentary_maker import CommentaryMaker, CommentaryStyle
from app.services.video.mashup_maker import MashupMaker, MashupStyle
from app.services.video.monologue_maker import MonologueMaker, MonologueStyle
from app.services.ai.voice_generator import VoiceConfig
from app.services.viral_video.caption_generator import CaptionStyle


class CreationType(Enum):
    """创作类型"""
    COMMENTARY = "解说视频"
    MASHUP = "混剪视频"
    MONOLOGUE = "独白视频"


class WorkerThread(QThread):
    """后台工作线程"""
    progress = pyqtSignal(str, float)  # stage, progress
    finished = pyqtSignal(str)         # result path
    error = pyqtSignal(str)            # error message
    
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
    
    files_dropped = pyqtSignal(list)
    
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
    
    creation_started = pyqtSignal(str)    # creation type
    creation_finished = pyqtSignal(str)   # output path
    creation_error = pyqtSignal(str)      # error message
    
    def __init__(self, application):
        super().__init__("ai_video_creator", "AI 视频创作", application)
        self.current_project = None
        self.worker_thread = None
        
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
        self.tabs.addTab(self._create_commentary_tab(), "🎙️ AI 解说")
        self.tabs.addTab(self._create_mashup_tab(), "🎵 AI 混剪")
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

    def _create_commentary_tab(self) -> QWidget:
        """创建解说功能页面 (macOS 风格 - 优化版)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        
        # === 左侧：资源与设置 ===
        left_scroll = MacScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 16, 0)
        left_layout.setSpacing(20)
        
        # 1. 视频选择卡片
        video_card = MacCard()
        video_title = MacTitleLabel("源视频", 4)
        video_card.layout().addWidget(video_title)
        
        self.commentary_video_drop = VideoDropZone()
        video_card.layout().addWidget(self.commentary_video_drop)
        
        # 视频预览 (默认隐藏应用最小高度防止堆叠)
        self.commentary_preview = VideoPreviewWidget()
        self.commentary_preview.setMinimumHeight(200) 
        self.commentary_preview.hide()
        video_card.layout().addWidget(self.commentary_preview)
        
        # 连接信号
        self.commentary_video_drop.files_dropped.connect(
            lambda files: self._show_video_preview(self.commentary_preview, files[0])
        )
        
        left_layout.addWidget(video_card)
        
        # 2. 设置卡片
        settings_card = MacCard()
        settings_title = MacTitleLabel("解说设置", 4)
        settings_card.layout().addWidget(settings_title)
        
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(16)
        
        # 主题
        self.commentary_topic = QLineEdit()
        self.commentary_topic.setPlaceholderText("例如：这只猫咪太可爱了")
        self.commentary_topic.setProperty("class", "input")
        settings_layout.addWidget(self._create_form_group("解说主题", self.commentary_topic))
        
        # 风格
        self.commentary_style = QComboBox()
        self.commentary_style.setProperty("class", "input")
        self.commentary_style.addItems([
            "说明型 - 客观解说",
            "故事型 - 叙事风格",
            "评论型 - 点评分析",
            "测评型 - 产品评测",
            "教程型 - 教学指导",
        ])
        settings_layout.addWidget(self._create_form_group("解说风格", self.commentary_style))
        
        # 声音
        self.commentary_voice = QComboBox()
        self.commentary_voice.setProperty("class", "input")
        self.commentary_voice.addItems([
            "晓晓 (女声，温柔)",
            "云扬 (男声，大气)",
            "晓墨 (女声，知性)",
            "云希 (男声，年轻)",
        ])
        settings_layout.addWidget(self._create_form_group("配音声音", self.commentary_voice))
        
        # 语速
        self.commentary_rate = QSlider(Qt.Orientation.Horizontal)
        self.commentary_rate.setProperty("class", "slider")
        self.commentary_rate.setRange(50, 150)
        self.commentary_rate.setValue(100)
        settings_layout.addWidget(self._create_form_group("语速调节", self.commentary_rate))

        # 字幕
        self.commentary_subtitle_style = QComboBox()
        self.commentary_subtitle_style.setProperty("class", "input")
        self.commentary_subtitle_style.addItems(["默认 (白色)", "电影感 (黄色)", "综艺 (花字)", "极简 (黑底)"])
        settings_layout.addWidget(self._create_form_group("字幕样式", self.commentary_subtitle_style))
        
        settings_card.layout().addLayout(settings_layout)
        left_layout.addWidget(settings_card)
        left_layout.addStretch()
        
        left_scroll.setWidget(left_panel)
        splitter.addWidget(left_scroll)
        
        # === 右侧：文案预览 ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        script_card = MacCard()
        script_title = MacTitleLabel("解说文案", 4)
        script_card.layout().addWidget(script_title)
        
        # 分析按钮
        analyze_btn = MacPrimaryButton("🔍 分析视频画面")
        analyze_btn.clicked.connect(self._analyze_commentary_video)
        script_card.layout().addWidget(analyze_btn)
        
        # 文案编辑区
        self.commentary_script = QTextEdit()
        self.commentary_script.setProperty("class", "input")
        self.commentary_script.setPlaceholderText(
            "点击上方分析按钮，AI 将自动生成解说文案...\n\n"
            "您也可以直接在此处编写。"
        )
        self.commentary_script.setMinimumHeight(400)
        script_card.layout().addWidget(self.commentary_script)
        
        right_layout.addWidget(script_card)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 550])
        
        layout.addWidget(splitter)
        
        return widget
    
    def _create_mashup_tab(self) -> QWidget:
        """创建混剪功能页面 (macOS 风格 - 优化版)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        
        # === 左侧：素材管理 ===
        left_scroll = MacScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 16, 0)
        left_layout.setSpacing(20)
        
        # 1. 视频素材卡片
        video_card = MacCard()
        video_card.layout().addWidget(MacTitleLabel("视频素材", 4))
        
        self.mashup_video_drop = VideoDropZone(multiple=True)
        video_card.layout().addWidget(self.mashup_video_drop)
        
        # 素材列表
        self.mashup_video_list = QListWidget()
        self.mashup_video_list.setMaximumHeight(200)
        self.mashup_video_list.setProperty("class", "input")
        video_card.layout().addWidget(self.mashup_video_list)
        
        self.mashup_video_drop.files_dropped.connect(self._update_mashup_video_list)
        left_layout.addWidget(video_card)
        
        # 2. 背景音乐卡片
        music_card = MacCard()
        music_card.layout().addWidget(MacTitleLabel("背景音乐", 4))
        
        music_row = QHBoxLayout()
        self.mashup_music_path = QLineEdit()
        self.mashup_music_path.setPlaceholderText("选择背景音乐（可选）")
        self.mashup_music_path.setReadOnly(True)
        self.mashup_music_path.setProperty("class", "input")
        music_row.addWidget(self.mashup_music_path)
        
        music_btn = MacSecondaryButton("选择")
        music_btn.clicked.connect(self._select_mashup_music)
        music_row.addWidget(music_btn)
        
        music_card.layout().addLayout(music_row)
        left_layout.addWidget(music_card)
        left_layout.addStretch()
        
        left_scroll.setWidget(left_panel)
        splitter.addWidget(left_scroll)
        
        # === 右侧：混剪设置 ===
        right_scroll = MacScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(20)
        
        # 3. 设置卡片
        settings_card = MacCard()
        settings_card.layout().addWidget(MacTitleLabel("混剪设置", 4))
        
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(16)
        
        self.mashup_style = QComboBox()
        self.mashup_style.setProperty("class", "input")
        self.mashup_style.addItems([
            "快节奏 - 动感剪辑",
            "电影感 - 大气沉稳",
            "Vlog 风格 - 自然过渡",
            "高光集锦 - 精彩瞬间",
            "蒙太奇 - 情感叙事",
        ])
        settings_layout.addWidget(self._create_form_group("混剪风格", self.mashup_style))
        
        self.mashup_duration = QSpinBox()
        self.mashup_duration.setRange(10, 300)
        self.mashup_duration.setValue(30)
        self.mashup_duration.setSuffix(" 秒")
        self.mashup_duration.setProperty("class", "input")
        settings_layout.addWidget(self._create_form_group("目标时长", self.mashup_duration))
        
        self.mashup_transition = QComboBox()
        self.mashup_transition.setProperty("class", "input")
        self.mashup_transition.addItems([
            "淡入淡出",
            "交叉溶解",
            "向左擦除",
            "向右滑动",
            "缩放",
            "随机",
        ])
        settings_layout.addWidget(self._create_form_group("转场效果", self.mashup_transition))
        
        self.mashup_beat_sync = QCheckBox(" 启用节拍同步 (自动踩点)")
        self.mashup_beat_sync.setChecked(True)
        settings_layout.addWidget(self.mashup_beat_sync)
        
        settings_card.layout().addLayout(settings_layout)
        right_layout.addWidget(settings_card)
        
        # 4. 预览占位卡片
        preview_card = MacCard()
        preview_card.layout().addWidget(MacTitleLabel("剪辑预览", 4))
        
        self.mashup_preview = QLabel("选择素材后预览剪辑点")
        self.mashup_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mashup_preview.setProperty("class", "text-muted")
        self.mashup_preview.setMinimumHeight(200)
        preview_card.layout().addWidget(self.mashup_preview)
        
        right_layout.addWidget(preview_card)
        right_layout.addStretch()
        
        right_scroll.setWidget(right_panel)
        splitter.addWidget(right_scroll)
        
        splitter.setSizes([450, 550])
        
        layout.addWidget(splitter)
        
        return widget
    
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
        
        # 1. 视频卡片
        video_card = MacCard()
        video_card.layout().addWidget(MacTitleLabel("源视频", 4))
        
        self.monologue_video_drop = VideoDropZone()
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
        self.output_dir.setText(str(Path.home() / "Documents" / "CineAIStudio"))
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
    
    def _update_mashup_video_list(self, files: List[str]):
        """更新混剪视频列表"""
        self.mashup_video_list.clear()
        for f in files:
            item = QListWidgetItem(Path(f).name)
            item.setData(Qt.ItemDataRole.UserRole, f)
            self.mashup_video_list.addItem(item)
    
    def _select_mashup_music(self):
        """选择混剪背景音乐"""
        try:
            file, _ = QFileDialog.getOpenFileName(
                self, "选择背景音乐", "",
                "音频文件 (*.mp3 *.wav *.m4a);;所有文件 (*)"
            )
            if file:
                self.mashup_music_path.setText(file)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件选择框: {e}")

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
    
    def _analyze_commentary_video(self):
        """分析解说视频"""
        if not self.commentary_video_drop.files:
            QMessageBox.warning(self, "提示", "请先选择视频文件")
            return
            
        # 检查 API Key
        api_key = self.get_config_value("ai_config.api_key", "")
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY") # Fallback to env var
            
        if not api_key:
            reply = QMessageBox.question(
                self, "缺少 API Key",
                "未配置 AI 服务 API Key（需在设置中配置）。\n\n是否使用模拟数据进行功能演示？\n(将返回固定的测试结果)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                # 引导去设置页面 (可选)
                return
            # 标记使用模拟模式
            self._use_mock_analysis = True
        else:
            self._use_mock_analysis = False
        
        self._start_video_analysis(
            self.commentary_video_drop.files[0],
            self.commentary_script,
            "commentary"
        )
    
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
                    # 使用占位文案
                    if mode == "commentary":
                        output_widget.setText(self._generate_sample_commentary())
                    else:
                        output_widget.setText(self._generate_sample_monologue())
                    
            except Exception as e:
                    # 使用占位文案
                    if mode == "commentary":
                        output_widget.setText(self._generate_sample_commentary())
                    else:
                        output_widget.setText(self._generate_sample_monologue())
                    
            except Exception as e:
                if mode == "commentary":
                    output_widget.setText(self._generate_sample_commentary())
                else:
                    output_widget.setText(self._generate_sample_monologue())
        
        def on_error(error: str):
            self.progress_bar.setVisible(False)
            self.status_label.setText("分析失败")
            
            # 使用占位文案
            if mode == "commentary":
                output_widget.setText(self._generate_sample_commentary())
            else:
                output_widget.setText(self._generate_sample_monologue())
            
            QMessageBox.warning(self, "分析失败", f"视频分析失败: {error}\n\n已填充示例文案，您可以编辑后使用。")
        
        # 启动线程
        self.worker_thread = WorkerThread(analyze)
        self.worker_thread.finished.connect(on_finished)
        self.worker_thread.error.connect(on_error)
        self.worker_thread.start()
    
    def _generate_sample_commentary(self) -> str:
        """生成示例解说文案"""
        return """【解说文案】

欢迎观看今天的视频。

这段画面为我们展示了一个精彩的场景。
让我们来仔细分析一下其中的细节。

首先，我们可以看到...

接下来，值得注意的是...

最后，让我们总结一下今天内容的要点。
感谢观看，别忘了点赞关注！

---
提示：您可以基于视频内容修改上面的文案"""
    
    def _generate_sample_monologue(self) -> str:
        """生成示例独白文案"""
        return """【独白文案】

有时候，我会停下脚步，看看身边的世界。

那些匆匆而过的身影，
那些转瞬即逝的瞬间，
都在诉说着各自的故事。

我常常想，
生活的意义是什么？

也许，
答案就藏在每一个平凡的日子里。

---
提示：您可以基于视频情感修改上面的独白"""
    
    def _start_creation(self):
        """开始创作"""
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:
            self._start_commentary_creation()
        elif current_tab == 1:
            self._start_mashup_creation()
        else:
            self._start_monologue_creation()
    
    def _start_commentary_creation(self):
        """开始解说视频创作"""
        if not self.commentary_video_drop.files:
            QMessageBox.warning(self, "提示", "请先选择视频文件")
            return
        
        if not self.commentary_script.toPlainText().strip():
            QMessageBox.warning(self, "提示", "请先生成或输入解说文案")
            return
        
        self._run_creation_task("commentary", self._create_commentary)
    
    def _start_mashup_creation(self):
        """开始混剪视频创作"""
        if not self.mashup_video_drop.files or len(self.mashup_video_drop.files) < 2:
            QMessageBox.warning(self, "提示", "请至少选择 2 个视频素材")
            return
        
        self._run_creation_task("mashup", self._create_mashup)
    
    def _start_monologue_creation(self):
        """开始独白视频创作"""
        if not self.monologue_video_drop.files:
            QMessageBox.warning(self, "提示", "请先选择视频文件")
            return
        
        if not self.monologue_script.toPlainText().strip():
            QMessageBox.warning(self, "提示", "请先生成或输入独白文案")
            return
        
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
    
    def _create_commentary(self) -> str:
        """创建解说视频"""
        # 使用绝对导入
        from app.services.video.commentary_maker import CommentaryMaker, CommentaryStyle
        from app.services.ai.voice_generator import VoiceConfig
        
        # 1. 参数映射
        # 风格映射
        style_map = {
            "说明型": CommentaryStyle.EXPLAINER,
            "故事型": CommentaryStyle.STORYTELLING,
            "评论型": CommentaryStyle.NEWS,
            "测评型": CommentaryStyle.REVIEW,
            "教程型": CommentaryStyle.EDUCATIONAL
        }
        current_style_text = self.commentary_style.currentText()
        style = next((v for k, v in style_map.items() if k in current_style_text), CommentaryStyle.EXPLAINER)
        
        # 声音映射
        voice_map = {
            "晓晓": "zh-CN-XiaoxiaoNeural",
            "云扬": "zh-CN-YunyangNeural", 
            "晓墨": "zh-CN-XiaomoNeural",
            "云希": "zh-CN-YunxiNeural" 
        }
        current_voice_text = self.commentary_voice.currentText()
        voice_id = next((v for k, v in voice_map.items() if k in current_voice_text), "zh-CN-XiaoxiaoNeural")
        
        # 语速
        rate = self.commentary_rate.value() / 100.0
        voice_config = VoiceConfig(voice_id=voice_id, rate=rate)
        
        # 2. 初始化服务
        maker = CommentaryMaker(voice_provider="edge")
        maker.set_progress_callback(lambda stage, p: self.worker_thread.progress.emit(stage, p))
        
        # 3. 获取设置
        video_path = self.commentary_video_drop.files[0]
        topic = self.commentary_topic.text() or "视频解说"
        script = self.commentary_script.toPlainText()
        output_dir = self.output_dir.text()
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                raise Exception(f"无法创建输出目录: {e}")

        # 4. 创建项目
        project = maker.create_project(
            source_video=video_path,
            topic=topic,
            style=style,
            voice_config=voice_config,
            output_dir=os.path.join(output_dir, "commentary"),
        )
        
        # 5. 生成内容
        maker.generate_script(project, custom_script=script)
        maker.generate_voice(project)
        maker.generate_captions(project)
        
        # 6. 导出
        draft_path = maker.export_to_jianying(project, output_dir + "/jianying_drafts")
        
        return draft_path
    
    def _create_mashup(self) -> str:
        """创建混剪视频"""
        from app.services.video.mashup_maker import MashupMaker, MashupStyle
        
        maker = MashupMaker()
        maker.set_progress_callback(lambda stage, p: self.worker_thread.progress.emit(stage, p))
        
        # 获取设置
        videos = self.mashup_video_drop.files
        music = self.mashup_music_path.text() or None
        duration = self.mashup_duration.value()
        output_dir = self.output_dir.text()
        
        # 风格映射
        style_map = {
            "快节奏": MashupStyle.FAST_PACED,
            "电影感": MashupStyle.CINEMATIC,
            "Vlog": MashupStyle.VLOG,
            "高光": MashupStyle.HIGHLIGHT,
            "蒙太奇": MashupStyle.MONTAGE
        }
        current_style = self.mashup_style.currentText()
        style = next((v for k, v in style_map.items() if k in current_style), MashupStyle.FAST_PACED)
        
        # 创建项目
        project = maker.create_project(
            source_videos=videos,
            background_music=music,
            target_duration=float(duration),
            # style=style, # MashupMaker create_project signature might not take style directly yet
            # 暂时通过 project.style 手动设置（如果 create_project 不支持）
            output_dir=os.path.join(output_dir, "mashup"),
        )
        # 手动设置风格（因为 create_project 可能还没更新签名）
        if hasattr(project, 'style'):
            project.style = style
        
        # 自动混剪
        if hasattr(maker, 'auto_mashup'):
            maker.auto_mashup(project)
        else:
             # 如果 MashupMaker 还没实现 auto_mashup，这里作为未实现功能的占位
             pass
        
        # 导出
        draft_path = maker.export_to_jianying(project, output_dir + "/jianying_drafts")
        
        return draft_path
    
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
🎬 CineAIStudio 使用帮助

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
