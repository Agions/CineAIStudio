#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 2: Pipeline 执行 — REDESIGNED"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QCursor

from ...components import MacCard
from app.orchestration.pipeline_controller import PipelineStage


_STAGE_COLORS = {"idle": "#1E2D42", "running": "#0A84FF", "done": "#10B981", "error": "#F59E0B", "skip": "#4A5A70"}
_STAGE_ICONS  = {"idle": "⏸", "running": "⚡", "done": "✓", "error": "✗", "skip": "⊘"}


class StageCard(QFrame):
    """Pipeline 阶段卡片 — REDESIGNED: 圆角12px · 脉冲动画"""
    stage_clicked = Signal(PipelineStage)

    def __init__(self, stage: PipelineStage, label: str, parent=None):
        super().__init__(parent)
        self._stage = stage
        self._label = label
        self._state = "idle"
        self._anim_toggle = False
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(160, 100)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label = QLabel(_STAGE_ICONS["idle"])
        self.icon_label.setFont(QFont("", 20))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        self.name_label = QLabel(self._label)
        self.name_label.setFont(QFont("", 12, QFont.Weight.Bold))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("color: #8098B0;")
        layout.addWidget(self.name_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: #1E2D42; border: none; border-radius: 2px; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0A84FF,stop:1 #00C8FF); border-radius: 2px; }
        """)
        layout.addWidget(self.progress_bar)
        self.sub_label = QLabel("")
        self.sub_label.setFont(QFont("", 10))
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("color: #4A5A70;")
        layout.addWidget(self.sub_label)
        self.clicked.connect(lambda: self.stage_clicked.emit(self._stage))

    def _apply_style(self):
        color = _STAGE_COLORS.get(self._state, "#1E2D42")
        bg = "#0A1020" if self._state == "running" else "#0E1520"
        self.setStyleSheet(f"QFrame {{ background: {bg}; border: 1px solid {color}; border-radius: 12px; }}")

    def set_state(self, state: str, sub: str = ""):
        self._state = state
        self._apply_style()
        self.icon_label.setText(_STAGE_ICONS.get(state, "⏸"))
        self.sub_label.setText(sub)
        if state == "running":
            self._start_animation()
        else:
            self._stop_animation()

    def set_progress(self, value: float):
        self.progress_bar.setValue(int(value * 1000))
        self.sub_label.setText(f"{int(value * 100)}%")

    def _start_animation(self):
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._pulse_border)
        self._anim_timer.start(500)

    def _pulse_border(self):
        self._anim_toggle = not self._anim_toggle
        color = "#2196FF" if self._anim_toggle else "#0A84FF"
        self.setStyleSheet(f"QFrame {{ background: #0A1020; border: 2px solid {color}; border-radius: 12px; }}")

    def _stop_animation(self):
        if hasattr(self, "_anim_timer"):
            self._anim_timer.stop()


class ScriptEditor(QWidget):
    """解说词编辑器 — REDESIGNED"""
    script_changed = Signal(str)
    retry_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("解说词")
        title.setFont(QFont("", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #E2E8F0;")
        header.addWidget(title)
        self.word_count_label = QLabel("0 字")
        self.word_count_label.setStyleSheet("color: #4A5A70; font-size: 12px;")
        header.addWidget(self.word_count_label)
        header.addStretch()
        self.edit_btn = QPushButton("✏️ 编辑")
        self.edit_btn.setObjectName("secondary_btn")
        self.edit_btn.setFixedSize(56, 26)
        self.edit_btn.clicked.connect(self._toggle_edit)
        header.addWidget(self.edit_btn)
        self.retry_btn = QPushButton("🔄 重试")
        self.retry_btn.setObjectName("secondary_btn")
        self.retry_btn.setFixedSize(72, 26)
        self.retry_btn.hide()
        self.retry_btn.clicked.connect(self.retry_requested.emit)
        header.addWidget(self.retry_btn)
        layout.addLayout(header)
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setMinimumHeight(200)
        self.editor.setStyleSheet("""
            QTextEdit { background: #0A0E16; color: #D0E0F0; border: 1px solid #1A2332; border-radius: 8px; padding: 12px; font-size: 13px; line-height: 1.6; }
            QTextEdit:focus { border-color: #0A84FF; }
        """)
        self.editor.textChanged.connect(lambda: (
            self.word_count_label.setText(f"{len(self.editor.toPlainText())} 字"),
            self.script_changed.emit(self.editor.toPlainText())
        ))
        layout.addWidget(self.editor)

    def _toggle_edit(self):
        if self.editor.isReadOnly():
            self.editor.setReadOnly(False)
            self.editor.setFocus()
            self.edit_btn.setText("✓ 完成")
            self.retry_btn.show()
        else:
            self.editor.setReadOnly(True)
            self.edit_btn.setText("✏️ 编辑")
            self.retry_btn.hide()

    def set_segments(self, segments: list):
        lines = [f"[{i}] {s.get('script', '')}" for i, s in enumerate(segments, 1)]
        self.editor.setPlainText("\n\n".join(lines))

    def get_text(self) -> str:
        return self.editor.toPlainText()


class StepPipeline(QWidget):
    """Step 2 — REDESIGNED"""
    finished = Signal(str)

    _STAGES = [
        (PipelineStage.ANALYZE, "场景理解"),
        (PipelineStage.SCRIPT,  "解说生成"),
        (PipelineStage.VOICE,    "配音合成"),
        (PipelineStage.CAPTION,  "字幕制作"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._controller = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        title = QLabel("正在创作...")
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(title)

        stage_layout = QHBoxLayout()
        stage_layout.addStretch()
        self.stage_cards = {}
        for stage, label in self._STAGES:
            card = StageCard(stage, label)
            card.stage_clicked.connect(lambda s: None)
            self.stage_cards[stage.value] = card
            stage_layout.addWidget(card)
        stage_layout.addStretch()
        layout.addLayout(stage_layout)

        self.script_editor = ScriptEditor()
        self.script_editor.retry_requested.connect(self._on_retry)
        layout.addWidget(self.script_editor, 1)

        log_card = MacCard()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(12, 12, 12, 12)
        log_header = QLabel("处理日志")
        log_header.setStyleSheet("color: #4A5A70; font-size: 12px; font-weight: 600;")
        log_layout.addWidget(log_header)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(120)
        self.log_area.setStyleSheet("""
            QTextEdit { background: #0A0E16; color: #4A5A70; border: 1px solid #141E2E; border-radius: 8px; padding: 8px; font-size: 11px; }
        """)
        log_layout.addWidget(self.log_area)
        layout.addWidget(log_card)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.back_btn = QPushButton("← 上一步")
        self.back_btn.setObjectName("secondary_btn")
        self.back_btn.setFixedSize(120, 40)
        self.back_btn.clicked.connect(lambda: self.finished.emit("back"))
        btn_layout.addWidget(self.back_btn)
        self.next_btn = QPushButton("导出视频 →")
        self.next_btn.setObjectName("primary_btn")
        self.next_btn.setFixedSize(140, 44)
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(lambda: self.finished.emit("export"))
        btn_layout.addWidget(self.next_btn)
        layout.addLayout(btn_layout)

    def bind_controller(self, controller):
        self._controller = controller

    def _on_retry(self):
        if self._controller:
            self._controller.retry_stage(PipelineStage.SCRIPT)

    def append_log(self, text: str):
        self.log_area.append(text)

    def set_stage_state(self, stage_value: int, state: str, sub: str = ""):
        card = self.stage_cards.get(stage_value)
        if card:
            card.set_state(state, sub)

    def set_stage_progress(self, stage_value: int, value: float):
        card = self.stage_cards.get(stage_value)
        if card:
            card.set_progress(value)

    def enable_export(self):
        self.next_btn.setEnabled(True)
