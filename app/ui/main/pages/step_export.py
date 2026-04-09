#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Step 3: 预览导出页 — REDESIGNED
frontend-design-pro: OKLCH · 圆形播放按钮 · 选中态卡片
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar,
    QFileDialog, QSizePolicy, QRadioButton, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, QUrl
from PySide6.QtGui import QFont, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from app.ui.components import MacCard, MacTitleLabel, MacPrimaryButton, MacSecondaryButton


# REDESIGN: OKLCH 调色板
_C = {
    "primary":    "#0A84FF",
    "primary_l": "#2196FF",
    "success":   "#10B981",
    "bg_card":   "#0E1520",
    "bg_input":  "#0A0E16",
    "border":    "#1A2332",
    "text":      "#E2E8F0",
    "text_sub":  "#8098B0",
    "text_muted":"#4A5A70",
}


class ExportWorker(QThread):
    """后台导出线程"""

    progress = Signal(str, int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, project, output_dir, fmt, subtitle_style, parent=None):
        super().__init__(parent)
        self._project = project
        self._output_dir = output_dir
        self._fmt = fmt
        self._subtitle_style = subtitle_style

    def run(self):
        try:
            from app.services.video.monologue_maker import MonologueMaker
            maker = MonologueMaker()
            maker.set_progress_callback(self._on_progress)

            self.progress.emit("准备导出", 10)

            if self._fmt == "jianying":
                output_path = maker.export_to_jianying(
                    self._project,
                    self._output_dir,
                )
            else:
                output_path = maker.export_to_mp4(
                    self._project,
                    self._output_dir,
                    subtitle_style=self._subtitle_style,
                )

            self.progress.emit("完成", 100)
            self.finished.emit(output_path)

        except AttributeError:
            try:
                output_path = maker.export_to_jianying(
                    self._project,
                    self._output_dir,
                )
                self.finished.emit(output_path)
            except Exception as e:
                self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, stage_label: str, progress: float):
        pct = int(progress * 80) + 10
        self.progress.emit(stage_label, pct)


class SubtitleStyleCard(QFrame):
    """
    字幕样式选择卡片 — REDESIGNED
    选中态: 主色边框发光 + 背景加深
    Hover: 边框微微亮起
    """

    selected = Signal(str)

    _STYLES = {
        "cinematic": ("电影字幕", "黑底白字，居中，适合故事叙述"),
        "minimal":   ("简约白字", "无背景白色文字，适合教程"),
        "dynamic":   ("动感字幕", "打字机效果，适合短内容"),
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
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("", 24))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        name_label = QLabel(name)
        name_label.setFont(QFont("", 13, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {_C['text']};")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        desc_label = QLabel(desc)
        desc_label.setFont(QFont("", 11))
        desc_label.setStyleSheet(f"color: {_C['text_sub']}; line-height: 1.4;")
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
            # REDESIGN: 主色发光边框 + 背景加深
            self.setStyleSheet(f"""
                QFrame {{
                    background: #0A1A3A;
                    border: 2px solid {_C['primary']};
                    border-radius: 14px;
                    box-shadow: 0 0 16px {_C['primary']}30;
                }}
            """)
        else:
            # REDESIGN: 默认边框
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_C['bg_card']};
                    border: 1px solid {_C['border']};
                    border-radius: 14px;
                }}
                QFrame:hover {{
                    border-color: {_C['primary']}80;
                }}
            """)

    def mousePressEvent(self, event):
        self.selected.emit(self._style_id)


class StepExport(QWidget):
    """
    向导 Step 3 — REDESIGNED
    播放按钮: 圆形 · 字幕卡片: 选中发光
    """

    restart_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project = None
        self._draft_path = ""
        self._source_video = ""
        self._player = None
        self._audio = None
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # 标题
        title = QLabel("预览与导出")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {_C['text']};")
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

        # 播放控制栏 — REDESIGN: 圆形播放按钮
        controls = QHBoxLayout()
        controls.setSpacing(12)

        # 圆形播放按钮
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['primary']};
                border: none;
                border-radius: 20px;
                color: #FFFFFF;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {_C['primary_l']};
            }}
            QPushButton:pressed {{
                background: #0070E0;
            }}
        """)
        self.play_btn.clicked.connect(self._toggle_playback)
        controls.addWidget(self.play_btn)

        # 进度条
        self.progress_slider = QProgressBar()
        self.progress_slider.setFixedHeight(4)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        self.progress_slider.setTextVisible(False)
        self.progress_slider.setStyleSheet(f"""
            QProgressBar {{
                background: {_C['bg_input']};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {_C['primary']},
                    stop:1 #00C8FF);
                border-radius: 2px;
            }}
        """)
        controls.addWidget(self.progress_slider, 1)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet(f"color: {_C['text_sub']}; font-size: 11px;")
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
        sub_title.setStyleSheet(f"color: {_C['text_sub']}; font-size: 13px; font-weight: 600;")
        config_layout.addWidget(sub_title)

        sub_style_layout = QHBoxLayout()
        sub_style_layout.setSpacing(10)
        self.sub_style_cards: dict = {}
        self.sub_style_group = QButtonGroup()
        for style_id in ["cinematic", "minimal", "dynamic"]:
            card = SubtitleStyleCard(style_id)
            card.selected.connect(self._on_sub_style_selected)
            self.sub_style_cards[style_id] = card
            sub_style_layout.addWidget(card)
        self._on_sub_style_selected("cinematic")
        config_layout.addLayout(sub_style_layout)

        # 导出格式
        fmt_title = QLabel("导出格式")
        fmt_title.setStyleSheet(f"color: {_C['text_sub']}; font-size: 13px; font-weight: 600;")
        config_layout.addWidget(fmt_title)

        self.fmt_group = QButtonGroup()
        fmt_layout = QVBoxLayout()
        fmt_layout.setSpacing(8)
        for fmt_id, fmt_name in [
            ("mp4",     "MP4 视频（推荐）"),
            ("jianying", "剪映草稿（可继续编辑）"),
        ]:
            radio = QRadioButton(fmt_name)
            radio.setStyleSheet(f"""
                QRadioButton {{
                    color: {_C['text']};
                    font-size: 13px;
                    spacing: 8px;
                }}
                QRadioButton::indicator {{
                    width: 16px; height: 16px;
                    border: 1px solid {_C['border']};
                    border-radius: 8px;
                }}
                QRadioButton::indicator:checked {{
                    background: {_C['primary']};
                    border-color: {_C['primary']};
                }}
            """)
            radio.setChecked(fmt_id == "jianying")
            self.fmt_group.addButton(radio, fmt_id)
            fmt_layout.addWidget(radio)
        config_layout.addLayout(fmt_layout)

        config_layout.addStretch()

        # 导出路径
        out_layout = QHBoxLayout()
        out_layout.setSpacing(8)
        out_label = QLabel("保存至")
        out_label.setStyleSheet(f"color: {_C['text']}; font-size: 13px;")
        out_layout.addWidget(out_label)
        out_layout.addStretch()

        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.setFixedSize(64, 28)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_C['text_sub']};
                border: 1px solid {_C['border']};
                border-radius: 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {_C['primary']};
                color: {_C['text']};
            }}
        """)
        browse_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(browse_btn)
        config_layout.addLayout(out_layout)

        self.out_path_label = QLabel("默认保存至项目目录")
        self.out_path_label.setStyleSheet(f"color: {_C['text_muted']}; font-size: 12px;")
        self.out_path_label.setWordWrap(True)
        config_layout.addWidget(self.out_path_label)

        # 导出进度条 — REDESIGN: 蓝色渐变
        self.export_progress = QProgressBar()
        self.export_progress.setFixedHeight(8)
        self.export_progress.setRange(0, 100)
        self.export_progress.setValue(0)
        self.export_progress.setVisible(False)
        self.export_progress.setStyleSheet(f"""
            QProgressBar {{
                background: {_C['bg_input']};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {_C['primary']},
                    stop:1 {_C['success']});
                border-radius: 4px;
            }}
        """)
        config_layout.addWidget(self.export_progress)

        self.export_status_label = QLabel("")
        self.export_status_label.setStyleSheet(f"color: {_C['text_muted']}; font-size: 11px;")
        self.export_status_label.setVisible(False)
        config_layout.addWidget(self.export_status_label)

        # 导出按钮 — REDESIGN: 主色渐变
        self.export_btn = QPushButton("导出视频")
        self.export_btn.setFixedHeight(44)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {_C['primary']},
                    stop:1 {_C['primary_l']});
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {_C['primary_l']},
                    stop:1 {_C['primary']});
            }}
            QPushButton:disabled {{
                background: #1A2740;
                color: #3A4A60;
            }}
        """)
        self.export_btn.clicked.connect(self._do_export)
        config_layout.addWidget(self.export_btn)

        preview_layout.addWidget(config_card, stretch=1)
        layout.addLayout(preview_layout, stretch=1)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.back_btn = QPushButton("← 上一步")
        self.back_btn.setFixedSize(120, 40)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_C['text_sub']};
                border: 1px solid {_C['border']};
                border-radius: 10px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {_C['primary']};
                color: {_C['text']};
            }}
        """)
        self.back_btn.clicked.connect(lambda: self.restart_requested.emit())
        btn_layout.addWidget(self.back_btn)

        layout.addLayout(btn_layout)

    def _toggle_playback(self):
        if not self._player:
            return
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self.play_btn.setText("▶")
        else:
            self._player.play()
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
        if not self._project:
            QMessageBox.warning(self, "未找到项目", "请先完成视频创作流程")
            return

        fmt = self.fmt_group.checkedButton()
        fmt = fmt if fmt else "jianying"

        output_dir = self.out_path_label.text()
        if output_dir == "默认保存至项目目录" or not output_dir:
            output_dir = self._draft_path if self._draft_path else os.path.expanduser("~/Narrafiilm/output")

        sub_style = next(
            (sid for sid, card in self.sub_style_cards.items() if card._is_selected),
            "cinematic"
        )

        self.export_btn.setEnabled(False)
        self.export_btn.setText("导出中...")
        self.export_progress.setVisible(True)
        self.export_progress.setValue(0)
        self.export_status_label.setVisible(True)
        self.export_status_label.setText("准备中...")

        self._worker = ExportWorker(
            self._project, output_dir, fmt, sub_style, self
        )
        self._worker.progress.connect(self._on_export_progress)
        self._worker.finished.connect(self._on_export_finished)
        self._worker.error.connect(self._on_export_error)
        self._worker.start()

    def _on_export_progress(self, stage: str, pct: int):
        self.export_progress.setValue(pct)
        self.export_status_label.setText(stage)

    def _on_export_finished(self, output_path: str):
        self.export_btn.setEnabled(True)
        self.export_btn.setText("✅ 导出完成")
        self.export_progress.setValue(100)
        self.export_status_label.setText(f"📁 {output_path}")
        self.out_path_label.setText(f"📁 {output_path}")

        QMessageBox.information(
            self, "导出完成",
            f"视频已导出至：\n{output_path}"
        )

    def _on_export_error(self, error: str):
        self.export_btn.setEnabled(True)
        self.export_btn.setText("导出失败，点击重试")
        self.export_progress.setVisible(False)
        self.export_status_label.setVisible(False)
        QMessageBox.critical(self, "导出失败", error)

    def set_project(self, project):
        self._project = project

    def set_draft_path(self, path: str):
        self._draft_path = path
        self.out_path_label.setText(f"📁 {path}")

    def set_source_video(self, video_path: str):
        if not video_path:
            return
        self._source_video = video_path
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self.video_widget)
        self._player.setSource(QUrl.fromLocalFile(video_path))
        self.play_btn.setText("▶")
