"""
视频编辑页面 - macOS 设计系统优化版
重构为使用标准化组件，零内联样式
"""

import os
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QFrame, QScrollArea, QStackedWidget, QProgressBar,
    QComboBox, QSlider, QTabWidget, QListWidget, QListWidgetItem,
    QLineEdit, QMessageBox, QFileDialog, QApplication,
    QToolBox, QSizePolicy, QFormLayout, QPushButton
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QUrl, QMimeData
from PyQt6.QtGui import QIcon, QAction, QDragEnterEvent, QDropEvent

from .base_page import BasePage
from app.services.ai_service.mock_ai_service import MockAIService
from app.core.icon_manager import get_icon

# 导入标准化 macOS 组件
from app.ui.components import (
    MacCard, MacElevatedCard, MacPrimaryButton, MacSecondaryButton,
    MacDangerButton, MacIconButton, MacTitleLabel, MacLabel, MacBadge,
    MacPageToolbar, MacGrid, MacScrollArea, MacEmptyState,
    MacSearchBox, MacButtonGroup
)


class MediaLibraryPanel(QWidget):
    """媒体库面板 - macOS 设计系统"""

    video_selected = pyqtSignal(str)
    audio_selected = pyqtSignal(str)
    image_selected = pyqtSignal(str)
    project_opened = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "panel")
        self._setup_ui()
        self._setup_drag_drop()

    def _setup_ui(self):
        """设置UI - 使用标准化组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. 标题区域
        title_row = create_icon_text_row("📦", "媒体库", "title-lg")
        layout.addWidget(title_row)

        # 2. 标签页容器（使用 MacElevatedCard）
        self.tab_container = MacElevatedCard()
        self.tab_container.setProperty("class", "card elevated")
        self.tab_container_layout = QVBoxLayout(self.tab_container)
        self.tab_container_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_container_layout.setSpacing(0)

        # 3. 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setProperty("class", "library-tabs")
        self.tab_container_layout.addWidget(self.tab_widget)

        # 创建各个标签页
        self._create_media_tabs()

        layout.addWidget(self.tab_container)

        # 4. 导入按钮区域
        import_row = QWidget()
        import_row.setProperty("class", "button-group")
        import_layout = QHBoxLayout(import_row)
        import_layout.setContentsMargins(0, 0, 0, 0)
        import_layout.setSpacing(6)

        import_btn = MacSecondaryButton("📥 导入文件")
        import_btn.setProperty("class", "button secondary")
        import_btn.clicked.connect(self._import_files)
        import_layout.addWidget(import_btn)

        layout.addWidget(import_row)

    def _create_media_tabs(self):
        """创建媒体标签页"""
        # 视频素材
        self.video_tab = QWidget()
        video_layout = QVBoxLayout(self.video_tab)
        video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_list = self._create_file_list()
        video_layout.addWidget(self.video_list)
        self.tab_widget.addTab(self.video_tab, "视频")

        # 音频素材
        self.audio_tab = QWidget()
        audio_layout = QVBoxLayout(self.audio_tab)
        audio_layout.setContentsMargins(0, 0, 0, 0)
        self.audio_list = self._create_file_list()
        audio_layout.addWidget(self.audio_list)
        self.tab_widget.addTab(self.audio_tab, "音频")

        # 图片素材
        self.image_tab = QWidget()
        image_layout = QVBoxLayout(self.image_tab)
        image_layout.setContentsMargins(0, 0, 0, 0)
        self.image_list = self._create_file_list(False)  # 图片使用图标模式
        image_layout.addWidget(self.image_list)
        self.tab_widget.addTab(self.image_tab, "图片")

        # 导出文件
        self.export_tab = QWidget()
        export_layout = QVBoxLayout(self.export_tab)
        export_layout.setContentsMargins(0, 0, 0, 0)
        self.export_list = self._create_file_list()
        self.export_list.setAlternatingRowColors(True)
        export_layout.addWidget(self.export_list)
        self.tab_widget.addTab(self.export_tab, "导出")

    def _create_file_list(self, icon_mode=True):
        """创建文件列表"""
        file_list = QListWidget()
        file_list.setProperty("class", "file-list")
        file_list.setAlternatingRowColors(True)
        file_list.setViewMode(QListWidget.ViewMode.IconMode if icon_mode else QListWidget.ViewMode.ListMode)
        file_list.setIconSize(QSize(64, 48))
        file_list.setGridSize(QSize(80, 70)) if icon_mode else None

        # 连接双击事件
        file_list.itemDoubleClicked.connect(self._on_file_double_clicked)

        return file_list

    def _setup_drag_drop(self):
        """设置拖放功能"""
        self.setAcceptDrops(True)
        self.video_list.setAcceptDrops(True)
        self.audio_list.setAcceptDrops(True)
        self.image_list.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]

        if file_paths:
            self.add_media_files(file_paths)

    def add_media_files(self, file_paths: List[str]):
        """添加媒体文件"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
        audio_extensions = {'.mp3', '.wav', '.flac'}
        image_extensions = {'.jpg', '.png', '.jpeg'}

        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue

            file_ext = os.path.splitext(file_path)[1].lower()
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setData(Qt.ItemDataRole.UserRole, file_path)

            # 设置图标
            if file_ext in video_extensions:
                item.setIcon(get_icon("video", 32))
                item.setToolTip(f"视频: {file_name}")
                self.video_list.addItem(item)
                self._extract_video_metadata(item, file_path)
            elif file_ext in audio_extensions:
                item.setIcon(get_icon("audio", 32))
                item.setToolTip(f"音频: {file_name}")
                self.audio_list.addItem(item)
            elif file_ext in image_extensions:
                item.setIcon(get_icon("image", 32))
                item.setToolTip(f"图片: {file_name}")
                self.image_list.addItem(item)

    def _extract_video_metadata(self, item, file_path):
        """提取视频元数据（简化版）"""
        try:
            import subprocess
            import json

            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)

            duration = float(metadata['format'].get('duration', 0))
            hours, remainder = divmod(duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

            for stream in metadata['streams']:
                if stream['codec_type'] == 'video':
                    width = stream.get('width', 0)
                    height = stream.get('height', 0)
                    item.setToolTip(f"时长: {duration_str}\n分辨率: {width}x{height}\n{os.path.basename(file_path)}")
                    break
        except Exception:
            pass

    def _on_file_double_clicked(self, item):
        """文件双击事件"""
        if not item:
            return

        file_path = item.data(Qt.ItemDataRole.UserRole)

        # 获取当前标签页
        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:  # 视频
            self.video_selected.emit(file_path)
        elif current_tab == 1:  # 音频
            self.audio_selected.emit(file_path)
        elif current_tab == 2:  # 图片
            self.image_selected.emit(file_path)
        elif current_tab == 3:  # 导出
            self.video_selected.emit(file_path)  # 作为视频播放

    def _import_files(self):
        """导入文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择媒体文件", "",
            "所有支持文件 (*.mp4 *.avi *.mov *.mkv *.mp3 *.wav *.flac *.jpg *.png *.jpeg);;"
            "视频文件 (*.mp4 *.avi *.mov *.mkv);;"
            "音频文件 (*.mp3 *.wav *.flac);;"
            "图片文件 (*.jpg *.png *.jpeg)"
        )
        if files:
            self.add_media_files(files)

    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)


class PreviewPanel(QWidget):
    """预览面板 - macOS 设计系统"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "panel preview-panel")
        self.media_player = None
        self.video_widget = None
        self.audio_output = None
        self.current_video_path = None
        self.is_playing = False
        self.logger = None
        self._setup_ui()
        self._setup_media_player()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. 标题
        title_row = create_icon_text_row("🎬", "预览面板", "title-lg")
        layout.addWidget(title_row)

        # 2. 预览区域
        self.preview_container = MacCard()
        self.preview_container.setProperty("class", "card preview-area")
        self.preview_container.setMinimumHeight(300)

        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # 占位符
        self.placeholder = MacEmptyState(
            icon="🎥",
            title="未加载视频",
            description="从媒体库选择或拖拽视频文件到此处"
        )
        preview_layout.addWidget(self.placeholder)

        # 视频播放器（初始隐藏）
        self.video_widget = QVideoWidget()
        self.video_widget.setProperty("class", "video-widget")
        self.video_widget.hide()
        preview_layout.addWidget(self.video_widget)

        layout.addWidget(self.preview_container)

        # 3. 控制栏
        control_card = MacCard()
        control_card.setProperty("class", "card control-bar")
        control_layout = QHBoxLayout(control_card)
        control_layout.setContentsMargins(12, 8, 12, 8)
        control_layout.setSpacing(12)

        # 播放按钮
        self.play_btn = MacIconButton("▶️", 28)
        self.play_btn.setToolTip("播放/暂停")
        self.play_btn.clicked.connect(self._toggle_playback)
        control_layout.addWidget(self.play_btn)

        # 时间显示
        self.time_label = MacLabel("00:00:00 / 00:00:00", "text-sm")
        control_layout.addWidget(self.time_label)

        # 进度条
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setProperty("class", "slider")
        self.progress_slider.setRange(0, 0)
        self.progress_slider.setToolTip("播放进度")
        self.progress_slider.valueChanged.connect(self._on_slider_changed)
        control_layout.addWidget(self.progress_slider, 1)

        # 音量
        self.volume_btn = MacIconButton("🔊", 24)
        self.volume_btn.setToolTip("静音/取消")
        self.volume_btn.clicked.connect(self._toggle_mute)
        control_layout.addWidget(self.volume_btn)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setProperty("class", "slider volume")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(80)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        control_layout.addWidget(self.volume_slider)

        # 全屏
        self.fullscreen_btn = MacIconButton("⛶", 24)
        self.fullscreen_btn.setToolTip("全屏 (F键)")
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        control_layout.addWidget(self.fullscreen_btn)

        layout.addWidget(control_card)

    def _setup_media_player(self):
        """设置媒体播放器"""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)

    def load_video(self, video_path: str) -> bool:
        """加载视频"""
        try:
            if not os.path.exists(video_path):
                return False

            self.current_video_path = video_path
            self.media_player.setSource(QUrl.fromLocalFile(video_path))

            # 切换到视频播放器
            self.placeholder.hide()
            self.video_widget.show()
            self.audio_output.setVolume(self.volume_slider.value() / 100.0)

            return True
        except Exception:
            return False

    def _toggle_playback(self):
        """切换播放/暂停"""
        if self.current_video_path is None:
            return

        if self.is_playing:
            self.media_player.pause()
        else:
            self.media_player.play()

    def _toggle_mute(self):
        """切换静音"""
        if self.audio_output.volume() == 0:
            self.audio_output.setVolume(self.volume_slider.value() / 100.0)
            self.volume_btn.setText("🔊")
        else:
            self.audio_output.setVolume(0)
            self.volume_btn.setText("🔇")

    def _toggle_fullscreen(self):
        """切换全屏"""
        if self.video_widget.isFullScreen():
            self.video_widget.showNormal()
        else:
            self.video_widget.showFullScreen()

    def _on_position_changed(self, position: int):
        """播放位置变化"""
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)

        current = self._format_time(position)
        duration = self._format_time(self.media_player.duration())
        self.time_label.setText(f"{current} / {duration}")

    def _on_duration_changed(self, duration: int):
        """时长变化"""
        self.progress_slider.setRange(0, duration)

    def _on_playback_state_changed(self, state):
        """播放状态变化"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.is_playing = True
            self.play_btn.setText("⏸️")
        else:
            self.is_playing = False
            self.play_btn.setText("▶️")

    def _on_slider_changed(self, value: int):
        """进度条变化"""
        if self.media_player:
            self.media_player.setPosition(value)

    def _on_volume_changed(self, value: int):
        """音量变化"""
        if self.audio_output:
            self.audio_output.setVolume(value / 100.0)

    def _format_time(self, milliseconds: int) -> str:
        """格式化时间"""
        if milliseconds < 0:
            return "00:00:00"
        seconds = milliseconds // 1000
        minutes = seconds // 60
        hours = minutes // 60
        seconds = seconds % 60
        minutes = minutes % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class PropertiesPanel(QWidget):
    """属性面板 - macOS 设计系统"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "panel properties-panel")
        self._setup_ui()
        self._connect_ai_signals()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. 标题
        title_row = create_icon_text_row("⚙️", "属性面板", "title-lg")
        layout.addWidget(title_row)

        # 2. 属性标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setProperty("class", "properties-tabs")

        # 视频属性
        self.video_tab = self._create_video_tab()
        self.tab_widget.addTab(self.video_tab, "视频")

        # AI增强
        self.ai_enhance_tab = self._create_ai_enhance_tab()
        self.tab_widget.addTab(self.ai_enhance_tab, "AI增强")

        # AI字幕
        self.ai_subtitle_tab = self._create_ai_subtitle_tab()
        self.tab_widget.addTab(self.ai_subtitle_tab, "AI字幕")

        layout.addWidget(self.tab_widget)

    def _create_video_tab(self):
        """创建视频属性标签页"""
        container = MacScrollArea()
        container.setProperty("class", "scroll-area")

        content = QWidget()
        content.setProperty("class", "section-content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 基本信息卡片
        info_card = MacCard()
        info_card.setProperty("class", "card")
        info_layout = QVBoxLayout(info_card.layout())
        info_layout.setSpacing(8)

        info_title = MacTitleLabel("基本信息", 6)
        info_layout.addWidget(info_title)

        # 分辨率
        self.resolution_label = MacLabel("1920x1080", "text-sm")
        info_layout.addWidget(self._create_info_row("分辨率:", self.resolution_label))

        # 时长
        self.duration_label = MacLabel("00:05:30", "text-sm")
        info_layout.addWidget(self._create_info_row("时长:", self.duration_label))

        # 帧率
        self.fps_label = MacLabel("30 fps", "text-sm")
        info_layout.addWidget(self._create_info_row("帧率:", self.fps_label))

        layout.addWidget(info_card)

        # 调整参数
        adjust_card = MacCard()
        adjust_card.setProperty("class", "card")
        adjust_layout = QVBoxLayout(adjust_card.layout())
        adjust_layout.setSpacing(8)

        adjust_title = MacTitleLabel("调整参数", 6)
        adjust_layout.addWidget(adjust_title)

        # 亮度、对比度、饱和度滑块
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.setProperty("class", "slider")
        adjust_layout.addWidget(self._create_slider_row("亮度", self.brightness_slider))

        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.setProperty("class", "slider")
        adjust_layout.addWidget(self._create_slider_row("对比度", self.contrast_slider))

        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)
        self.saturation_slider.setProperty("class", "slider")
        adjust_layout.addWidget(self._create_slider_row("饱和度", self.saturation_slider))

        layout.addWidget(adjust_card)
        layout.addStretch()

        container.setWidget(content)
        return container

    def _create_ai_enhance_tab(self):
        """创建AI增强标签页"""
        container = MacScrollArea()
        container.setProperty("class", "scroll-area")

        content = QWidget()
        content.setProperty("class", "section-content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # AI功能按钮组
        ai_card = MacCard()
        ai_card.setProperty("class", "card")
        ai_layout = QVBoxLayout(ai_card.layout())
        ai_layout.setSpacing(8)

        ai_title = MacTitleLabel("AI增强功能", 6)
        ai_layout.addWidget(ai_title)

        # 功能按钮
        actions = [
            ("智能剪辑", "AI自动识别精彩片段", "scissors"),
            ("AI降噪", "智能去除背景噪音", "audio"),
            ("自动字幕", "AI生成字幕文件", "subtitle"),
            ("画质增强", "AI提升视频清晰度", "enhance")
        ]

        for text, tooltip, icon_name in actions:
            btn = MacSecondaryButton(f"🛠️ {text}", get_icon(icon_name, 16))
            btn.setMinimumHeight(36)
            btn.setToolTip(tooltip)
            btn.setProperty("class", "button secondary action-btn")
            ai_layout.addWidget(btn)

        layout.addWidget(ai_card)
        layout.addStretch()

        container.setWidget(content)
        return container

    def _create_ai_subtitle_tab(self):
        """创建AI字幕标签页"""
        container = MacScrollArea()
        container.setProperty("class", "scroll-area")

        content = QWidget()
        content.setProperty("class", "section-content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 字幕设置卡片
        subtitle_card = MacCard()
        subtitle_card.setProperty("class", "card")
        subtitle_layout = QVBoxLayout(subtitle_card.layout())
        subtitle_layout.setSpacing(8)

        subtitle_title = MacTitleLabel("字幕设置", 6)
        subtitle_layout.addWidget(subtitle_title)

        # 样式选择
        self.style_combo = QComboBox()
        self.style_combo.setProperty("class", "input")
        self.style_combo.addItems(["默认", "科技", "文艺", "复古"])
        subtitle_layout.addWidget(self._create_form_row("字幕样式:", self.style_combo))

        # 字幕大小
        self.size_spin = QSpinBox()
        self.size_spin.setProperty("class", "input")
        self.size_spin.setRange(12, 48)
        self.size_spin.setValue(24)
        subtitle_layout.addWidget(self._create_form_row("字幕大小:", self.size_spin))

        # 字幕颜色
        self.color_combo = QComboBox()
        self.color_combo.setProperty("class", "input")
        self.color_combo.addItems(["白色", "黄色", "黑色"])
        subtitle_layout.addWidget(self._create_form_row("字幕颜色:", self.color_combo))

        layout.addWidget(subtitle_card)

        # 生成按钮
        self.generate_btn = MacPrimaryButton("🤖 生成AI字幕")
        self.generate_btn.setMinimumHeight(40)
        layout.addWidget(self.generate_btn)

        layout.addStretch()

        container.setWidget(content)
        return container

    def _create_info_row(self, label: str, value_widget):
        """创建信息行"""
        row = QWidget()
        row.setProperty("class", "info-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        label_widget = MacLabel(label, "text-secondary text-bold")
        row_layout.addWidget(label_widget)
        row_layout.addWidget(value_widget)
        row_layout.addStretch()

        return row

    def _create_slider_row(self, label: str, slider):
        """创建滑块行"""
        row = QWidget()
        row.setProperty("class", "control-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        label_widget = MacLabel(label, "text-sm text-bold")
        row_layout.addWidget(label_widget)
        row_layout.addWidget(slider, 1)

        value_label = MacLabel("0", "text-sm text-muted")
        slider.valueChanged.connect(lambda v: value_label.setNum(v))
        row_layout.addWidget(value_label)

        return row

    def _create_form_row(self, label: str, input_widget):
        """创建表单行"""
        row = QWidget()
        row.setProperty("class", "form-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        label_widget = MacLabel(label, "text-sm text-bold")
        row_layout.addWidget(label_widget)
        row_layout.addWidget(input_widget, 1)

        return row

    def _connect_ai_signals(self):
        """连接AI信号"""
        # 连接 AI 分析完成信号
        if hasattr(self, 'ai_analyzer'):
            self.ai_analyzer.analysis_completed.connect(self._on_ai_analysis_completed)
            self.ai_analyzer.analysis_failed.connect(self._on_ai_analysis_failed)


class TimelinePanel(QWidget):
    """时间线面板 - macOS 设计系统"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "panel timeline-panel")
        self.logger = None
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. 标题
        title_row = create_icon_text_row("⏱️", "时间线", "title-lg")
        layout.addWidget(title_row)

        # 2. AI工具栏
        ai_toolbar = self._create_ai_toolbar()
        layout.addWidget(ai_toolbar)

        # 3. 时间线轨道容器
        timeline_card = MacCard()
        timeline_card.setProperty("class", "card timeline-container")
        timeline_card.setMinimumHeight(180)

        timeline_layout = QVBoxLayout(timeline_card)
        timeline_layout.setContentsMargins(0, 0, 0, 0)

        # 时间标尺
        self._add_time_ruler(timeline_layout)

        # 轨道
        self._add_tracks(timeline_layout)

        layout.addWidget(timeline_card)

    def _create_ai_toolbar(self):
        """创建AI工具栏"""
        toolbar = QWidget()
        toolbar.setProperty("class", "ai-toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(6)

        ai_tools = [
            ("短剧解说", "AI生成短剧解说", "💬"),
            ("高能混剪", "智能混剪精彩片段", "✂️"),
            ("第三人称解说", "生成第三人称解说", "🎤")
        ]

        for name, tooltip, icon in ai_tools:
            btn = MacSecondaryButton(f"{icon} {name}")
            btn.setProperty("class", "button secondary ai-tool")
            btn.setMinimumWidth(110)
            btn.setToolTip(tooltip)
            toolbar_layout.addWidget(btn)

        toolbar_layout.addStretch()
        return toolbar

    def _add_time_ruler(self, layout):
        """添加时间标尺"""
        ruler = QFrame()
        ruler.setProperty("class", "time-ruler")
        ruler.setFixedHeight(28)

        ruler_layout = QHBoxLayout(ruler)
        ruler_layout.setContentsMargins(12, 4, 12, 4)
        ruler_layout.setSpacing(0)

        # 添加时间刻度
        for i in range(0, 61, 10):
            time_label = QLabel(f"{i:02d}:00")
            time_label.setProperty("class", "ruler-tick")
            ruler_layout.addWidget(time_label)
            if i < 60:
                ruler_layout.addStretch()

        layout.addWidget(ruler)

    def _add_tracks(self, layout):
        """添加轨道"""
        # 视频轨道
        video_track = QFrame()
        video_track.setProperty("class", "track video-track")
        video_track.setFixedHeight(50)

        track_layout = QHBoxLayout(video_track)
        track_layout.setContentsMargins(12, 8, 12, 8)

        label = MacLabel("视频轨道", "text-sm text-bold")
        track_layout.addWidget(label)
        track_layout.addStretch()

        layout.addWidget(video_track)

        # 音频轨道
        audio_track = QFrame()
        audio_track.setProperty("class", "track audio-track")
        audio_track.setFixedHeight(40)

        track_layout = QHBoxLayout(audio_track)
        track_layout.setContentsMargins(12, 8, 12, 8)

        label = MacLabel("音频轨道", "text-sm text-bold")
        track_layout.addWidget(label)
        track_layout.addStretch()

        layout.addWidget(audio_track)

        layout.addStretch()


class VideoEditorPage(BasePage):
    """视频编辑器页面 - macOS 设计系统"""

    def __init__(self, application):
        self.media_panel = None
        self.preview_panel = None
        self.properties_panel = None
        self.timeline_panel = None
        self.main_splitter = None
        self.center_splitter = None
        self.ai_service = MockAIService()
        self.current_video = None
        
        super().__init__("video_editor", "视频编辑器", application)

    def initialize(self) -> bool:
        """初始化页面"""
        try:
            self.log_info("Initializing video editor page")
            return True
        except Exception as e:
            self.handle_error(e, "initialize")
            return False

    def create_content(self) -> None:
        """创建页面内容"""
        # 主分割器
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setProperty("class", "splitter horizontal")
        self.add_widget_to_main_layout(self.main_splitter)

        # 左侧：媒体库
        self.media_panel = MediaLibraryPanel()
        self.media_panel.setMinimumWidth(220)
        self.media_panel.setMaximumWidth(280)
        self.main_splitter.addWidget(self.media_panel)

        # 中央：预览和时间线
        self.center_splitter = QSplitter(Qt.Orientation.Vertical)
        self.center_splitter.setProperty("class", "splitter vertical")
        self.main_splitter.addWidget(self.center_splitter)

        self.preview_panel = PreviewPanel()
        self.preview_panel.logger = self.logger
        self.preview_panel.setMinimumHeight(300)
        self.center_splitter.addWidget(self.preview_panel)

        self.timeline_panel = TimelinePanel()
        self.timeline_panel.logger = self.logger
        self.timeline_panel.setMinimumHeight(180)
        self.center_splitter.addWidget(self.timeline_panel)

        # 右侧：属性面板
        self.properties_panel = PropertiesPanel()
        self.properties_panel.setMinimumWidth(250)
        self.properties_panel.setMaximumWidth(300)
        self.main_splitter.addWidget(self.properties_panel)

        # 设置分割器比例
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setStretchFactor(2, 1)
        self.center_splitter.setStretchFactor(0, 3)
        self.center_splitter.setStretchFactor(1, 1)

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接信号"""
        if self.media_panel:
            self.media_panel.video_selected.connect(self._on_video_selected)

    def _on_video_selected(self, video_path: str):
        """视频选中处理"""
        self.current_video = video_path
        self.update_status(f"已选择视频: {os.path.basename(video_path)}")

        if self.preview_panel:
            success = self.preview_panel.load_video(video_path)
            if not success:
                self.show_error("视频加载失败")
