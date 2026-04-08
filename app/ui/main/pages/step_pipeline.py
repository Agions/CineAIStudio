"""
Step 2: Pipeline 执行台
4 阶段横向进度卡 + ScriptEditor + 实时日志
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QTextEdit,
    QLineEdit, QListWidget, QListWidgetItem, QProgressBar,
    QSizePolicy, QSpacerItem, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QCursor

from app.ui.components import MacCard, MacTitleLabel
from app.orchestration.pipeline_controller import PipelineStage


class StageCard(QFrame):
    """
    Pipeline 阶段卡片

    状态：idle(灰) / running(蓝+动画) / done(绿✓) / error(红) / skipable(虚线)
    """

    stage_clicked = Signal(PipelineStage)

    _STATE_COLORS = {
        "idle": "#30363D",
        "running": "#388BFD",
        "done": "#238636",
        "error": "#DA3633",
        "skip": "#484F58",
    }

    _STATE_ICONS = {
        "idle": "⏸",
        "running": "⚡",
        "done": "✅",
        "error": "❌",
        "skip": "⏭",
    }

    def __init__(self, stage: PipelineStage, label: str, parent=None):
        super().__init__(parent)
        self._stage = stage
        self._label = label
        self._state = "idle"
        self._progress = 0.0
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(160, 100)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel(self._STATE_ICONS["idle"])
        self.icon_label.setFont(QFont("", 20))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        self.name_label = QLabel(self._label)
        self.name_label.setFont(QFont("", 12, QFont.Weight.Bold))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("color: #C9D1D9;")
        layout.addWidget(self.name_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #21262D;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk { background: #388BFD; border-radius: 2px; }
        """)
        layout.addWidget(self.progress_bar)

        self.sub_label = QLabel("")
        self.sub_label.setFont(QFont("", 10))
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("color: #8B949E;")
        layout.addWidget(self.sub_label)

        self.clicked.connect(lambda: self.stage_clicked.emit(self._stage))

    def _apply_style(self):
        color = self._STATE_COLORS.get(self._state, "#30363D")
        border = f"1px solid {color}"
        bg = "#161B22" if self._state != "running" else "#0D1117"
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: {border};
                border-radius: 12px;
            }}
        """)

    def set_state(self, state: str, sub: str = ""):
        """更新卡片状态"""
        self._state = state
        self._apply_style()
        self.icon_label.setText(self._STATE_ICONS.get(state, "⏸"))
        self.sub_label.setText(sub)
        if state == "running":
            self._start_animation()
        else:
            self._stop_animation()

    def set_progress(self, value: float):
        """更新进度 0.0~1.0"""
        self._progress = value
        self.progress_bar.setValue(int(value * 1000))
        pct = int(value * 100)
        self.sub_label.setText(f"{pct}%")

    def _start_animation(self):
        # 脉冲动画（透明度）
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(1000)
        self._anim.setStartValue(1.0)
        self._anim.setKeyValueAt(0.5, 0.7)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.setLoopCount(-1)  # 无限循环
        self._anim.start()

    def _stop_animation(self):
        if hasattr(self, "_anim"):
            self._anim.stop()
            self.setWindowOpacity(1.0)


class ScriptEditor(QWidget):
    """
    可编辑 AI 生成文案的面板
    生成后可修改，再触发后续 Pipeline
    """

    script_changed = Signal(str)  # 用户修改后的文案
    retry_requested = Signal()      # 请求重试

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._segments: list = []

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 标题栏
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("解说文案")
        title.setFont(QFont("", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #E6EDF3;")
        header.addWidget(title)

        self.word_count_label = QLabel("0 字")
        self.word_count_label.setStyleSheet("color: #8B949E; font-size: 12px;")
        header.addWidget(self.word_count_label)
        header.addStretch()

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.setObjectName("secondary_button")
        self.edit_btn.setFixedSize(56, 26)
        self.edit_btn.clicked.connect(self._toggle_edit)
        header.addWidget(self.edit_btn)

        self.retry_btn = QPushButton("🔄 重试")
        self.retry_btn.setObjectName("secondary_button")
        self.retry_btn.setFixedSize(72, 26)
        self.retry_btn.hide()
        self.retry_btn.clicked.connect(self.retry_requested.emit)
        header.addWidget(self.retry_btn)

        layout.addLayout(header)

        # 文案编辑器
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("AI 生成的解说文案将显示在这里...\n\n点击「编辑」可手动修改。")
        self.editor.setReadOnly(True)
        self.editor.setMinimumHeight(200)
        self.editor.setStyleSheet("""
            QTextEdit {
                background: #0D1117;
                border: 1px solid #21262D;
                border-radius: 8px;
                color: #E6EDF3;
                padding: 12px;
                font-size: 13px;
                line-height: 1.6;
                font-family: 'SF Pro Text', 'Segoe UI', sans-serif;
            }
        """)
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor)

    def set_read_only(self, readonly: bool):
        self.editor.setReadOnly(readonly)
        self.edit_btn.setText("编辑" if readonly else "完成")
        self.retry_btn.setVisible(not readonly)

    def _toggle_edit(self):
        if self.editor.isReadOnly():
            self.set_read_only(False)
            self.editor.setFocus()
        else:
            self.set_read_only(True)

    def set_segments(self, segments: list):
        """填充各片段的解说文案"""
        self._segments = segments
        lines = []
        for i, seg in enumerate(segments, 1):
            script = seg.get("script", "")
            lines.append(f"[{i}] {script}")
        self.editor.setPlainText("\n\n".join(lines))

    def set_full_text(self, text: str):
        self.editor.setPlainText(text)

    def get_text(self) -> str:
        return self.editor.toPlainText()

    def _on_text_changed(self):
        text = self.editor.toPlainText()
        self.word_count_label.setText(f"{len(text)} 字")
        self.script_changed.emit(text)


class StepPipeline(QWidget):
    """
    向导 Step 2：Pipeline 执行台

    Signals:
        finished(output_dir)
    """

    finished = Signal(str)

    _STAGES = [
        (PipelineStage.ANALYZING, "分析视频"),
        (PipelineStage.SCRIPT, "生成解说"),
        (PipelineStage.VOICE, "生成配音"),
        (PipelineStage.CAPTION, "生成字幕"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._controller = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # 标题
        title = MacTitleLabel("创作进度")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #E6EDF3;")
        layout.addWidget(title)

        # 阶段进度卡片（横向）
        stage_layout = QHBoxLayout()
        stage_layout.setSpacing(12)
        stage_layout.addStretch()

        self.stage_cards: dict = {}
        for stage, label in self._STAGES:
            card = StageCard(stage, label)
            card.stage_clicked.connect(self._on_stage_click)
            self.stage_cards[stage.value] = card
            stage_layout.addWidget(card)

        stage_layout.addStretch()
        layout.addLayout(stage_layout)

        # ScriptEditor
        self.script_editor = ScriptEditor()
        self.script_editor.retry_requested.connect(self._on_retry_script)
        layout.addWidget(self.script_editor, stretch=1)

        # 日志输出
        log_card = MacCard()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(12, 12, 12, 12)

        log_header = QLabel("执行日志")
        log_header.setStyleSheet("color: #8B949E; font-size: 12px; font-weight: 600;")
        log_layout.addWidget(log_header)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background: #0D1117;
                border: 1px solid #21262D;
                border-radius: 6px;
                color: #8B949E;
                font-size: 11px;
                font-family: 'SF Mono', 'JetBrains Mono', monospace;
                padding: 8px;
            }
        """)
        log_layout.addWidget(self.log_output)
        layout.addWidget(log_card)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.back_btn = QPushButton("← 上一步")
        self.back_btn.setObjectName("secondary_button")
        self.back_btn.setFixedSize(120, 40)
        self.back_btn.clicked.connect(lambda: self.finished.emit("back"))
        btn_layout.addWidget(self.back_btn)

        self.next_btn = QPushButton("导出视频 →")
        self.next_btn.setObjectName("primary_button")
        self.next_btn.setFixedSize(140, 40)
        self.next_btn.hide()
        self.next_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self.next_btn)

        layout.addLayout(btn_layout)

    def bind_controller(self, controller):
        """绑定 PipelineController"""
        self._controller = controller
        self._controller.stage_changed.connect(self._on_stage_changed)
        self._controller.stage_progress.connect(self._on_stage_progress)
        self._controller.finished.connect(self._on_pipeline_finished)
        self._controller.error_occurred.connect(self._on_error)

    def _on_stage_changed(self, stage_value: str, label: str):
        # 找到对应 stage 的 index
        stage_idx = {s.value: i for i, (s, _) in enumerate(self._STAGES)}

        # 标记完成阶段
        for s_val, card in self.stage_cards.items():
            if s_val in stage_idx:
                idx = stage_idx[s_val]
                current_idx = stage_idx.get(stage_value, -1)
                if idx < current_idx:
                    card.set_state("done", "已完成")
                elif idx == current_idx:
                    card.set_state("running", "进行中")
                else:
                    card.set_state("idle", "")

        # Script 完成后可编辑
        if stage_value == PipelineStage.SCRIPT.value:
            self.script_editor.set_read_only(False)
            self._append_log("✅ 解说文案已生成，可编辑后再继续")

    def _on_stage_progress(self, stage_value: str, progress: float):
        if stage_value in self.stage_cards:
            self.stage_cards[stage_value].set_progress(progress)
            pct = int(progress * 100)
            self._append_log(f"[{stage_value}] {pct}%")

    def _on_pipeline_finished(self, output_path: str):
        self.stage_cards[PipelineStage.CAPTION.value].set_state("done", "已完成")
        self._append_log(f"✅ Pipeline 完成: {output_path}")
        self.next_btn.show()

    def _on_error(self, error: str):
        self._append_log(f"❌ 错误: {error}")
        current = self._controller.current_stage()
        if current.value in self.stage_cards:
            self.stage_cards[current.value].set_state("error", "失败")

    def _on_stage_click(self, stage: PipelineStage):
        # 可点击已完成或当前运行阶段查看详情
        pass

    def _on_retry_script(self):
        self._append_log("🔄 请求重试文案生成...")
        self._controller.retry_stage(PipelineStage.SCRIPT)

    def _on_export(self):
        # 进入 Step3 导出页
        self.finished.emit("export")

    def _append_log(self, msg: str):
        self.log_output.append(msg)
        # 自动滚动到底部
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_output.setTextCursor(cursor)
