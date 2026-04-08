#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CreationWizardPage — 3 步创作向导容器

架构：
    Step1 (上传配置) → Step2 (Pipeline 执行) → Step3 (预览导出)
    横向进度指示器 + 页面切换动画
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .step_upload import StepUpload
from .step_pipeline import StepPipeline
from .step_export import StepExport
from app.orchestration.pipeline_controller import PipelineController


class StepIndicator(QFrame):
    """
    横向步骤指示器
    [● Step1] —— [○ Step2] —— [○ Step3]
    """

    step_clicked = Signal(int)  # 点击跳转到某步

    _STEPS = ["上传", "创作", "导出"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = 0
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(60)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 0, 32, 0)
        layout.setSpacing(8)

        self._dot_labels = []

        for i, label_text in enumerate(self._STEPS):
            # 圆点
            dot = QLabel("●")
            dot.setFont(QFont("", 12))
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setFixedWidth(20)
            self._update_dot(dot, i)
            layout.addWidget(dot)
            self._dot_labels.append(dot)

            # 文字标签
            lbl = QLabel(label_text)
            lbl.setFont(QFont("", 13, QFont.Weight.Bold if i == 0 else QFont.Weight.Normal))
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            self._update_lbl(lbl, i)
            lbl.mousePressEvent = lambda _, idx=i: self.step_clicked.emit(idx)
            layout.addWidget(lbl)

            # 连接线
            if i < len(self._STEPS) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setStyleSheet("border: none; border-top: 2px solid #30363D;")
                layout.addWidget(line, 1)

        layout.addStretch()

    def _update_dot(self, dot, index):
        if index < self._current or (hasattr(self, '_completed') and index in self._completed):
            dot.setText("●")
            dot.setStyleSheet("color: #238636;")
        elif index == self._current:
            dot.setText("●")
            dot.setStyleSheet("color: #388BFD;")
        else:
            dot.setText("○")
            dot.setStyleSheet("color: #30363D;")

    def _update_lbl(self, lbl, index):
        if index <= self._current:
            lbl.setStyleSheet("color: #E6EDF3; font-size: 13px; font-weight: 700;")
        else:
            lbl.setStyleSheet("color: #484F58; font-size: 13px;")

    def set_current(self, step: int):
        self._current = step
        for i, dot in enumerate(self._dot_labels):
            self._update_dot(dot, i)
        # 重新布局以更新标签颜色
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            w = item.widget()
            if isinstance(w, QLabel) and i % 2 == 1:  # 标签在偶数索引
                pass  # 颜色通过样式表处理


class CreationWizardPage(QWidget):
    """
    创作向导主页面

    信号：
        completed(project_output) — 整个 Pipeline 完成
    """

    completed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._controller = PipelineController(self)
        self._setup_ui()
        self._bind_signals()
        self._show_step(0)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 步骤指示器
        self.step_indicator = StepIndicator()
        self.step_indicator.setStyleSheet(
            "background: #161B22; border-bottom: 1px solid #21262D;"
        )
        layout.addWidget(self.step_indicator)

        # 页面堆叠
        self.page_stack = QStackedWidget()

        self._step_upload = StepUpload()
        self._step_pipeline = StepPipeline()
        self._step_export = StepExport()

        self.page_stack.addWidget(self._step_upload)    # index 0
        self.page_stack.addWidget(self._step_pipeline)   # index 1
        self.page_stack.addWidget(self._step_export)    # index 2

        layout.addWidget(self.page_stack, 1)

        # 连接步骤指示器点击
        self.step_indicator.step_clicked.connect(self._show_step)

    def _bind_signals(self):
        # Step1 → 启动 Pipeline
        self._step_upload.config_ready.connect(self._start_pipeline)

        # Step2 ↔ Wizard 导航
        self._step_pipeline.bind_controller(self._controller)
        self._step_pipeline.finished.connect(self._on_pipeline_step_finished)

        # Step3 → 完成
        self._step_export.restart_requested.connect(lambda: self._show_step(0))

    def _show_step(self, index: int):
        """切换到指定步骤"""
        self.step_indicator.set_current(index)
        self.page_stack.setCurrentIndex(index)

    def _start_pipeline(self, video_path, context, emotion, style, output_dir):
        """接收 Step1 配置，启动 Pipeline，跳转到 Step2"""
        self._show_step(1)
        self._step_pipeline.bind_controller(self._controller)
        self._controller.start_pipeline(
            video_path=video_path,
            context=context,
            emotion=emotion,
            style=style,
            output_dir=output_dir,
        )

    def _on_pipeline_step_finished(self, direction: str):
        """
        Step2 发出信号：
        - "export" → 跳 Step3
        - "back" → 回 Step1
        """
        if direction == "export":
            self._show_step(2)
            project = self._controller.current_project()
            self._step_export.set_project(project)
        elif direction == "back":
            self._show_step(0)

    def get_page_name(self) -> str:
        return "创作向导"

    def get_page_icon(self) -> str:
        return "🎬"
