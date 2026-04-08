"""
Step 3: 预览导出页
视频预览 + 字幕样式选择 + 导出格式
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame, QProgressBar,
    QFileDialog, QSizePolicy, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from app.ui.components import MacCard, MacTitleLabel, MacPrimaryButton


class SubtitleStyleCard(QFrame):
    """字幕样式选择卡片"""

    selected = Signal(str)

    _STYLES = {
        "cinematic": ("电影字幕", "黑底白字，居中，适合故事叙述"),
        "minimal": ("简约白字", "无背景白色文字，适合教程"),
        "dynamic": ("动感字幕", "打字机效果，适合短内容"),
    }

    def __init__(self, style_id: str, parent=None):
        super().__init__(parent)
        self._style_id = style_id
        self._is_selected = False
        self._setup_ui()

    def _setup_ui(self):
        name, desc = self._STYLES.get(self._style_id, (self._style_id, ""))
        icon = {"cinematic": "🎬", "minimal": "✦", "dynamic": "⚡"}.get(
            self._style_id, "□"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("", 24))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        name_label = QLabel(name)
        name_label.setFont(QFont("", 13, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #E6EDF3;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        desc_label = QLabel(desc)
        desc_label.setFont(QFont("", 11))
        desc_label.setStyleSheet("color: #8B949E; line-height: 1.4;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        self.setMinimumSize(140, 140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def select(self):
        self._is_selected = True
        self._apply_style()

    def deselect(self):
        self._is_selected = False
        self._apply_style()

    def _apply_style(self):
        if self._is_selected:
            border = "2px solid #388BFD"
            bg = "#1C2128"
        else:
            border = "1px solid #30363D"
            bg = "#161B22"
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: {border};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: #388BFD;
            }}
        """)

    def mousePressEvent(self, event):
        self.selected.emit(self._style_id)


class StepExport(QWidget):
    """
    向导 Step 3：预览与导出

    Signals:
        restart_requested()
    """

    restart_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project = None
        self._export_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # 标题
        title = MacTitleLabel("预览与导出")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #E6EDF3;")
        layout.addWidget(title)

        # 预览区
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(20)

        # 视频预览
        video_card = MacCard()
        video_layout = QVBoxLayout(video_card)
        video_layout.setContentsMargins(12, 12, 12, 12)

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(280)
        self.video_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        video_layout.addWidget(self.video_widget)

        # 播放控制栏
        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #21262D;
                border: none;
                border-radius: 18px;
                color: #E6EDF3;
                font-size: 14px;
            }
            QPushButton:hover { background: #30363D; }
        """)
        self.play_btn.clicked.connect(self._toggle_playback)
        controls.addWidget(self.play_btn)

        self.progress_slider = QProgressBar()
        self.progress_slider.setFixedHeight(4)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        self.progress_slider.setTextVisible(False)
        self.progress_slider.setStyleSheet("""
            QProgressBar {
                background: #21262D;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk { background: #388BFD; }
        """)
        controls.addWidget(self.progress_slider, 1)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("color: #8B949E; font-size: 11px;")
        controls.addWidget(self.time_label)

        video_layout.addLayout(controls)
        preview_layout.addWidget(video_card, stretch=2)

        # 右侧配置
        config_card = MacCard()
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(20, 20, 20, 20)
        config_layout.setSpacing(16)

        # 字幕样式
        sub_title = QLabel("字幕样式")
        sub_title.setStyleSheet("color: #C9D1D9; font-size: 13px; font-weight: 600;")
        config_layout.addWidget(sub_title)

        sub_style_layout = QHBoxLayout()
        sub_style_layout.setSpacing(8)
        self.sub_style_cards: dict = {}
        self.sub_style_group = QButtonGroup()
        for style_id in ["cinematic", "minimal", "dynamic"]:
            card = SubtitleStyleCard(style_id)
            card.selected.connect(self._on_sub_style_selected)
            self.sub_style_cards[style_id] = card
            sub_style_layout.addWidget(card)
        # 默认选中 cinematic
        self._on_sub_style_selected("cinematic")
        config_layout.addLayout(sub_style_layout)

        # 导出格式
        fmt_title = QLabel("导出格式")
        fmt_title.setStyleSheet("color: #C9D1D9; font-size: 13px; font-weight: 600;")
        config_layout.addWidget(fmt_title)

        self.fmt_group = QButtonGroup()
        fmt_layout = QVBoxLayout()
        fmt_layout.setSpacing(8)
        for fmt_id, fmt_name in [
            ("mp4", "MP4 视频（推荐）"),
            ("jianying", "剪映草稿（可继续编辑）"),
        ]:
            radio = QRadioButton(fmt_name)
            radio.setStyleSheet("""
                QRadioButton {
                    color: #C9D1D9;
                    font-size: 13px;
                    spacing: 8px;
                }
                QRadioButton::indicator {
                    width: 16px; height: 16px;
                    border: 1px solid #30363D;
                    border-radius: 8px;
                }
                QRadioButton::indicator:checked {
                    background: #388BFD;
                    border-color: #388BFD;
                }
            """)
            radio.setChecked(fmt_id == "mp4")
            self.fmt_group.addButton(radio, fmt_id)
            fmt_layout.addWidget(radio)
        config_layout.addLayout(fmt_layout)

        config_layout.addStretch()

        # 导出路径
        out_layout = QHBoxLayout()
        out_layout.setSpacing(8)
        out_label = QLabel("保存至")
        out_label.setStyleSheet("color: #C9D1D9; font-size: 13px;")
        out_layout.addWidget(out_label)
        out_layout.addStretch()

        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondary_button")
        browse_btn.setFixedSize(64, 28)
        browse_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(browse_btn)
        config_layout.addLayout(out_layout)

        self.out_path_label = QLabel("默认保存至项目目录")
        self.out_path_label.setStyleSheet("color: #8B949E; font-size: 12px;")
        self.out_path_label.setWordWrap(True)
        config_layout.addWidget(self.out_path_label)

        # 导出按钮
        self.export_btn = MacPrimaryButton("导出视频")
        self.export_btn.setFixedHeight(44)
        self.export_btn.clicked.connect(self._do_export)
        config_layout.addWidget(self.export_btn)

        preview_layout.addWidget(config_card, stretch=1)
        layout.addLayout(preview_layout, stretch=1)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.back_btn = QPushButton("← 上一步")
        self.back_btn.setObjectName("secondary_button")
        self.back_btn.setFixedSize(120, 40)
        self.back_btn.clicked.connect(lambda: self.restart_requested.emit())
        btn_layout.addWidget(self.back_btn)

        layout.addLayout(btn_layout)

    def _toggle_playback(self):
        if not self._project:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶")
        else:
            self.player.play()
            self.play_btn.setText("⏸")

    def _on_sub_style_selected(self, style_id: str):
        for sid, card in self.sub_style_cards.items():
            if sid == style_id:
                card.select()
            else:
                card.deselect()

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存位置", "")
        if path:
            self.out_path_label.setText(path)

    def _do_export(self):
        self.export_btn.setEnabled(False)
        self.export_btn.setText("导出中...")

    def set_project(self, project):
        """接收 Pipeline 完成后的 Project"""
        self._project = project
        # 设置视频路径到播放器
        if hasattr(project, "source_video") and project.source_video:
            self.player = QMediaPlayer()
            self.audio = QAudioOutput()
            self.player.setAudioOutput(self.audio)
            self.player.setVideoOutput(self.video_widget)
            self.player.setSource(QUrl.fromLocalFile(project.source_video))
            self.play_btn.setText("▶")
