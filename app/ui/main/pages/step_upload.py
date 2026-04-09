#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 1: 上传配置 — REDESIGNED"""

import os, json, subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent

from ...components import MacCard, MacPrimaryButton, MacSecondaryButton, MacLabel


class VideoDropZone(QFrame):
    """REDESIGNED: 24px圆角 · active边框加粗"""
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_path = ""
        self._setup_ui()
        self.setAcceptDrops(True)
        self.setMinimumHeight(160)

    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame { border: 2px dashed #1E2D42; border-radius: 24px; background: #0A0E16; }
            QFrame:hover { border-color: #0A84FF; background: #0C1020; }
            QFrame[active="true"] { border-color: #0A84FF; border-width: 3px; background: #0A1028; }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        self.icon_label = QLabel("🎬")
        self.icon_label.setFont(QFont("", 48))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        self.text_label = QLabel("将视频文件拖放到此处，或点击选择")
        self.text_label.setFont(QFont("", 14))
        self.text_label.setStyleSheet("color: #4A5A70;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_label)
        self.select_btn = QPushButton("选择视频文件")
        self.select_btn.setObjectName("secondary_btn")
        self.select_btn.setFixedSize(120, 36)
        self.select_btn.clicked.connect(self._select_file)
        layout.addWidget(self.select_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(400)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.webm);;所有文件 (*)")
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self._file_path = path
        self.text_label.setText(f"📄 {Path(path).name}")
        self.text_label.setStyleSheet("color: #3FB950; font-weight: 600;")
        self.icon_label.setText("✅")
        self.file_selected.emit(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self._is_video(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self.setProperty("active", "true")
                self.style().unpolish(self); self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("active", "false")
        self.style().unpolish(self); self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("active", "false")
        self.style().unpolish(self); self.style().polish(self)
        urls = event.mimeData().urls()
        if urls and self._is_video(urls[0].toLocalFile()):
            self._set_file(urls[0].toLocalFile())

    def _is_video(self, path: str) -> bool:
        return Path(path).suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}


class VideoMetadataPanel(QFrame):
    """REDESIGNED: oklch色彩 · 12px圆角"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame { background: #0E1520; border-radius: 12px; border: 1px solid #1A2332; }
        """)
        layout = QGridLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setHorizontalSpacing(24)
        layout.setVerticalSpacing(8)
        self.labels = {}
        for i, (key, label_text) in enumerate([
            ("duration", "时长"), ("resolution", "分辨率"),
            ("size", "文件大小"), ("format", "格式"),
        ]):
            lbl_name = QLabel(label_text)
            lbl_name.setStyleSheet("color: #4A5A70; font-size: 12px;")
            layout.addWidget(lbl_name, i, 0)
            lbl_value = QLabel("—")
            lbl_value.setStyleSheet("color: #E2E8F0; font-size: 12px; font-weight: 600;")
            layout.addWidget(lbl_value, i, 1)
            self.labels[key] = lbl_value

    def set_metadata(self, path: str):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", path],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            fmt = data.get("format", {})
            dur = float(fmt.get("duration", 0))
            self.labels["duration"].setText(f"{int(dur//60):02d}:{int(dur%60):02d}")
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    self.labels["resolution"].setText(f"{s.get('width','?')}×{s.get('height','?')}")
                    break
            size = int(fmt.get("size", 0))
            if size > 1024**3: self.labels["size"].setText(f"{size/1024**3:.1f} GB")
            elif size > 1024**2: self.labels["size"].setText(f"{size/1024**2:.0f} MB")
            else: self.labels["size"].setText(f"{size/1024:.0f} KB")
            self.labels["format"].setText(fmt.get("format_name", "").split(",")[0])
        except: pass


class StepUpload(QWidget):
    """Step 1 — REDESIGNED"""
    config_ready = Signal(str, str, object, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        title = QLabel("创作新解说")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(title)

        hint = QLabel("上传视频后，AI 将代入主角视角生成解说词")
        hint.setStyleSheet("color: #4A5A70; font-size: 12px;")
        layout.addWidget(hint)

        self.drop_zone = VideoDropZone()
        self.drop_zone.file_selected.connect(self._on_video_selected)
        layout.addWidget(self.drop_zone)

        self.meta_panel = VideoMetadataPanel()
        self.meta_panel.setVisible(False)
        layout.addWidget(self.meta_panel)

        config_card = MacCard()
        gl = QGridLayout(config_card)
        gl.setContentsMargins(20, 20, 20, 20)
        gl.setSpacing(16)

        ctx_lbl = QLabel("解说场景")
        ctx_lbl.setStyleSheet("color: #8098B0; font-size: 13px;")
        gl.addWidget(ctx_lbl, 0, 0)
        self.ctx_input = QLineEdit()
        self.ctx_input.setPlaceholderText("例如：在咖啡馆独自工作，感受午后阳光...")
        self.ctx_input.setMinimumHeight(40)
        self.ctx_input.setStyleSheet("""
            QLineEdit { background: #0A0E16; color: #D0E0F0; border: 1px solid #1A2332; border-radius: 10px; padding: 0 12px; font-size: 13px; }
            QLineEdit:focus { border-color: #0A84FF; }
            QLineEdit::placeholder { color: #3A4A60; }
        """)
        gl.addWidget(self.ctx_input, 0, 1, 1, 2)

        emotion_lbl = QLabel("情感风格")
        emotion_lbl.setStyleSheet("color: #8098B0; font-size: 13px;")
        gl.addWidget(emotion_lbl, 1, 0)
        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems(["治愈", "悬疑", "励志", "怀旧", "浪漫"])
        self._style_combo(self.emotion_combo)
        gl.addWidget(self.emotion_combo, 1, 1, 1, 2)

        style_lbl = QLabel("解说长度")
        style_lbl.setStyleSheet("color: #8098B0; font-size: 13px;")
        gl.addWidget(style_lbl, 2, 0)
        self.style_combo = QComboBox()
        self.style_combo.addItems(["简洁版", "标准版", "详细版"])
        self._style_combo(self.style_combo)
        gl.addWidget(self.style_combo, 2, 1, 1, 2)

        layout.addWidget(config_card)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.next_btn = QPushButton("开始创作 →")
        self.next_btn.setObjectName("primary_btn")
        self.next_btn.setFixedSize(140, 44)
        self.next_btn.clicked.connect(self._on_next)
        self.next_btn.setEnabled(False)
        btn_layout.addWidget(self.next_btn)
        layout.addLayout(btn_layout)

    def _style_combo(self, combo: QComboBox):
        combo.setStyleSheet("""
            QComboBox { background-color: #0F1929; color: #C0D0E0; border: 1px solid #1E2D42; border-radius: 10px; padding: 10px 16px; font-size: 13px; }
            QComboBox:hover { border-color: #2A4060; }
            QComboBox:focus { border-color: #0A84FF; }
            QComboBox QAbstractItemView { background-color: #0F1929; border: 1px solid #1E2D42; border-radius: 10px; color: #C0D0E0; selection-background-color: #0F2640; padding: 4px; }
        """)

    def _on_video_selected(self, path: str):
        self._video_path = path
        self.meta_panel.set_metadata(path)
        self.meta_panel.setVisible(True)
        self.next_btn.setEnabled(True)

    def _on_next(self):
        emotion_map = {"治愈": "healing", "悬疑": "suspense", "励志": "inspiring", "怀旧": "nostalgic", "浪漫": "romantic"}
        style_map = {"简洁版": "concise", "标准版": "standard", "详细版": "detailed"}
        self.config_ready.emit(
            self._video_path,
            self.ctx_input.text().strip(),
            emotion_map.get(self.emotion_combo.currentText(), "healing"),
            style_map.get(self.style_combo.currentText(), "standard"),
            ""
        )
