#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VideoForge - AI 剧情分析页面
基于故事的智能视频剪辑工具
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar, QComboBox, QSpinBox,
    QTabWidget, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QCheckBox, QFrame, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PySide6.QtGui import QFont, QColor

from .base_page import BasePage
from app.ui.components import (
    MacCard, MacElevatedCard, MacTitleLabel, MacPrimaryButton,
    MacSecondaryButton, MacLabel, MacScrollArea, MacEmptyState,
    MacPageToolbar
)
from app.services.ai.story_analyzer import (
    StoryAnalyzer, StoryAnalysisResult, PlotType, SceneType
)


logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """剧情分析工作线程"""
    progress = pyqtSignal(str, float)  # stage, percentage
    finished = pyqtSignal(StoryAnalysisResult)
    error = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, analyzer: StoryAnalyzer, video_path: str, style: str, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.video_path = video_path
        self.style = style
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.progress.emit("正在提取视频帧...", 10)

            if self._cancelled:
                self.cancelled.emit()
                return

            # 分析剧情
            result = self.analyzer.analyze(self.video_path)

            if self._cancelled:
                self.cancelled.emit()
                return

            self.progress.emit("正在分析叙事结构...", 60)

            if self._cancelled:
                self.cancelled.emit()
                return

            # 获取剪辑建议
            cuts = self.analyzer.get_cut_recommendations(result, style=self.style)
            result.recommended_cuts = cuts

            self.progress.emit("分析完成", 100)
            self.finished.emit(result)

        except Exception as e:
            logger.error(f"Story analysis error: {e}")
            self.error.emit(str(e))


class StoryAnalysisPage(BasePage):
    """剧情分析页面"""

    # 剪辑风格选项
    STYLE_OPTIONS = [
        ("narrative", "叙事完整版", "保留故事完整性，按叙事结构剪辑"),
        ("highlight", "高光集锦", "只保留精彩片段，删除平淡内容"),
        ("trailer", "悬念预告", "制造悬念和期待，适合做预告片"),
    ]

    def __init__(self, application):
        super().__init__("story_analysis", "剧情分析", application)
        self.logger = logging.getLogger(__name__)
        self.analysis_result: Optional[StoryAnalysisResult] = None
        self.worker: Optional[AnalysisWorker] = None
        self._init_services()

    def _init_services(self):
        """初始化服务"""
        # 获取 AI 服务
        self.llm_manager = self.application.get_service_by_name("llm_manager")
        self.vision_provider = self.application.get_service_by_name("vision_provider")

        # 创建剧情分析器
        self.analyzer = StoryAnalyzer(
            llm_manager=self.llm_manager,
            vision_provider=self.vision_provider
        )

    def create_content(self) -> None:
        """创建页面内容"""
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)

        # 顶部工具栏
        toolbar = self._create_toolbar()
        self.main_layout.addWidget(toolbar)

        # 主内容区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setSizes([400, 600])
        content_splitter.setCollapsible(0, False)

        # 左侧：输入和控制
        left_panel = self._create_input_panel()
        content_splitter.addWidget(left_panel)

        # 右侧：结果展示
        right_panel = self._create_result_panel()
        content_splitter.addWidget(right_panel)

        self.main_layout.addWidget(content_splitter, 1)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = MacPageToolbar("🎬 AI 剧情分析")

        # 添加操作按钮
        new_btn = MacPrimaryButton("📂 新建分析")
        new_btn.clicked.connect(self._on_new_analysis)
        toolbar.add_action(new_btn)

        export_btn = MacSecondaryButton("📤 导出剪辑点")
        export_btn.clicked.connect(self._on_export_cuts)
        toolbar.add_action(export_btn)

        return toolbar

    def _create_input_panel(self) -> QWidget:
        """创建输入面板"""
        scroll = MacScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        # 视频选择卡片
        video_card = MacCard("📹 视频文件")
        video_layout = video_card.layout()
        video_layout.setSpacing(12)

        self.video_path_label = MacLabel("未选择视频")
        video_layout.addWidget(self.video_path_label)

        select_btn = MacSecondaryButton("选择视频")
        select_btn.clicked.connect(self._on_select_video)
        video_layout.addWidget(select_btn)

        layout.addWidget(video_card)

        # 分析设置卡片
        settings_card = MacCard("⚙️ 分析设置")
        settings_layout = settings_card.layout()
        settings_layout.setSpacing(12)

        # 剪辑风格选择
        style_label = MacLabel("剪辑风格")
        settings_layout.addWidget(style_label)

        self.style_combo = QComboBox()
        for value, name, desc in self.STYLE_OPTIONS:
            self.style_combo.addItem(f"{name} - {desc}", value)
        settings_layout.addWidget(self.style_combo)

        # 目标时长（可选）
        duration_label = MacLabel("目标时长（秒，可选）")
        settings_layout.addWidget(duration_label)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 3600)
        self.duration_spin.setValue(0)
        self.duration_spin.setPrefix("")
        self.duration_spin.setSuffix(" 秒 (0=保持原长)")
        self.duration_spin.setSpecialValueText("保持原长")
        settings_layout.addWidget(self.duration_spin)

        layout.addWidget(settings_card)

        # 分析按钮
        self.analyze_btn = MacPrimaryButton("🔍 开始分析")
        self.analyze_btn.clicked.connect(self._on_start_analysis)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)

        # 取消按钮（分析中可见）
        self.cancel_btn = MacSecondaryButton("❌ 取消")
        self.cancel_btn.clicked.connect(self._on_cancel_analysis)
        self.cancel_btn.setVisible(False)
        layout.addWidget(self.cancel_btn)

        # 进度条
        progress_card = MacCard("📊 分析进度")
        progress_layout = progress_card.layout()
        progress_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = MacLabel("等待开始...")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_card)

        layout.addStretch()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        return scroll

    def _create_result_panel(self) -> QWidget:
        """创建结果展示面板"""
        scroll = MacScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        # 故事概览卡片
        self.overview_card = MacElevatedCard("📋 故事概览")
        overview_layout = self.overview_card.layout()
        overview_layout.setSpacing(8)

        self.plot_type_label = MacLabel("剧情类型：-")
        overview_layout.addWidget(self.plot_type_label)

        self.summary_label = MacLabel("概要：-")
        overview_layout.addWidget(self.summary_label)

        self.duration_label = MacLabel("时长：-")
        overview_layout.addWidget(self.duration_label)

        self.themes_label = MacLabel("主题：-")
        overview_layout.addWidget(self.themes_label)

        layout.addWidget(self.overview_card)

        # 叙事结构卡片
        self.structure_card = MacCard("🎬 叙事结构")
        structure_layout = self.structure_card.layout()
        structure_layout.setSpacing(8)

        self.structure_label = MacLabel("等待分析...")
        structure_layout.addWidget(self.structure_label)

        layout.addWidget(self.structure_card)

        # 情感曲线卡片
        self.emotion_card = MacCard("💭 情感曲线")
        emotion_layout = self.emotion_card.layout()
        emotion_layout.setSpacing(8)

        self.emotion_label = MacLabel("等待分析...")
        emotion_layout.addWidget(self.emotion_label)

        layout.addWidget(self.emotion_card)

        # 剪辑建议卡片
        self.cuts_card = MacCard("✂️ 剪辑建议")
        cuts_layout = self.cuts_card.layout()
        cuts_layout.setSpacing(8)

        # 剪辑点表格
        self.cuts_table = QTableWidget()
        self.cuts_table.setColumnCount(5)
        self.cuts_table.setHorizontalHeaderLabels(["类型", "开始", "结束", "时长", "说明"])
        self.cuts_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.cuts_table.setMaximumHeight(300)
        cuts_layout.addWidget(self.cuts_table)

        layout.addWidget(self.cuts_card)

        # 高光时刻卡片
        self.highlights_card = MacCard("🌟 高光时刻")
        highlights_layout = self.highlights_card.layout()
        highlights_layout.setSpacing(8)

        self.highlights_label = MacLabel("等待分析...")
        highlights_layout.addWidget(self.highlights_label)

        layout.addWidget(self.highlights_card)

        layout.addStretch()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        return scroll

    def _on_select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.webm);;所有文件 (*.*)"
        )

        if file_path:
            self.video_path = file_path
            self.video_path_label.setText(os.path.basename(file_path))
            self.analyze_btn.setEnabled(True)

    def _on_start_analysis(self):
        """开始分析"""
        if not hasattr(self, 'video_path'):
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return

        style_value = self.style_combo.currentData()
        style_name = self.style_combo.currentText().split(" - ")[0]

        self.logger.info(f"Starting story analysis: {self.video_path}, style={style_name}")

        # 更新 UI 状态
        self.analyze_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("正在初始化...")

        # 创建工作线程
        self.worker = AnalysisWorker(
            self.analyzer,
            self.video_path,
            style_value
        )

        # 连接信号
        self.worker.progress.connect(self._on_analysis_progress)
        self.worker.finished.connect(self._on_analysis_finished)
        self.worker.error.connect(self._on_analysis_error)
        self.worker.cancelled.connect(self._on_analysis_cancelled)

        # 启动分析
        self.worker.start()

    def _on_cancel_analysis(self):
        """取消分析"""
        if self.worker and self.worker.isRunning():
            self.logger.info("Cancelling story analysis")
            self.worker.cancel()
            self.worker.wait()

        self._reset_ui()

    def _on_analysis_progress(self, stage: str, percentage: float):
        """分析进度更新"""
        self.progress_bar.setValue(int(percentage))
        self.progress_label.setText(stage)

    def _on_analysis_finished(self, result: StoryAnalysisResult):
        """分析完成"""
        self.analysis_result = result
        self.logger.info(f"Analysis finished: {result.plot_type.value}")

        # 更新 UI
        self._update_result_display(result)
        self._reset_ui()

        QMessageBox.information(self, "完成", "剧情分析完成！请查看右侧结果。")

    def _on_analysis_error(self, error: str):
        """分析错误"""
        self.logger.error(f"Analysis error: {error}")
        self._reset_ui()
        QMessageBox.critical(self, "错误", f"分析失败：{error}")

    def _on_analysis_cancelled(self):
        """分析取消"""
        self.logger.info("Analysis cancelled by user")
        self._reset_ui()
        QMessageBox.information(self, "取消", "分析已取消")

    def _reset_ui(self):
        """重置 UI 状态"""
        self.analyze_btn.setVisible(True)
        self.cancel_btn.setVisible(False)

    def _update_result_display(self, result: StoryAnalysisResult):
        """更新结果展示"""
        # 故事概览
        self.plot_type_label.setText(f"剧情类型：{result.plot_type.display_name}")
        self.summary_label.setText(f"概要：{result.summary or '无'}")
        self.duration_label.setText(f"时长：{int(result.duration // 60)}分{int(result.duration % 60)}秒")
        self.themes_label.setText(f"主题：{', '.join(result.themes) if result.themes else '无'}")

        # 叙事结构
        if result.segments:
            structure_text = []
            for seg in result.segments[:10]:  # 只显示前10个
                structure_text.append(
                    f"• [{seg.scene_type.display_name}] {seg.title} "
                    f"({int(seg.start_time)}s - {int(seg.end_time)}s)"
                )
            if len(result.segments) > 10:
                structure_text.append(f"... 还有 {len(result.segments) - 10} 个场景")
            self.structure_label.setText("\n".join(structure_text) if structure_text else "无")
        else:
            self.structure_label.setText("无场景分段数据")

        # 情感曲线
        if result.emotional_curve:
            emotion_text = []
            for ep in result.emotional_curve[:5]:  # 只显示前5个
                bar = "█" * int(ep.intensity * 10)
                emotion_text.append(f"• {int(ep.timestamp)}s: {ep.emotion} {bar}")
            if len(result.emotional_curve) > 5:
                emotion_text.append(f"... 还有 {len(result.emotional_curve) - 5} 个情感点")
            self.emotion_label.setText("\n".join(emotion_text) if emotion_text else "无")
        else:
            self.emotion_label.setText("无情感数据")

        # 剪辑建议表格
        self._update_cuts_table(result.recommended_cuts)

        # 高光时刻
        if result.highlight_moments:
            highlights_text = []
            for i, hl in enumerate(result.highlight_moments[:5], 1):
                ts = hl.get("timestamp", 0)
                desc = hl.get("description", "")
                highlights_text.append(f"{i}. [{int(ts)}s] {desc}")
            if len(result.highlight_moments) > 5:
                highlights_text.append(f"... 还有 {len(result.highlight_moments) - 5} 个高光")
            self.highlights_label.setText("\n".join(highlights_text) if highlights_text else "无")
        else:
            self.highlights_label.setText("无高光数据")

    def _update_cuts_table(self, cuts: List[Dict[str, Any]]):
        """更新剪辑点表格"""
        self.cuts_table.setRowCount(len(cuts))

        for row, cut in enumerate(cuts):
            # 类型
            type_item = QTableWidgetItem(cut.get("type", "keep"))
            self.cuts_table.setItem(row, 0, type_item)

            # 开始时间
            start_item = QTableWidgetItem(f"{cut.get('start', 0):.1f}s")
            self.cuts_table.setItem(row, 1, start_item)

            # 结束时间
            end_item = QTableWidgetItem(f"{cut.get('end', 0):.1f}s")
            self.cuts_table.setItem(row, 2, end_item)

            # 时长
            duration_item = QTableWidgetItem(f"{cut.get('duration', 0):.1f}s")
            self.cuts_table.setItem(row, 3, duration_item)

            # 说明
            reason = cut.get("reason", "")
            self.cuts_table.setItem(row, 4, QTableWidgetItem(reason))

        self.cuts_table.resizeRowsToContents()

    def _on_new_analysis(self):
        """新建分析"""
        self.analysis_result = None
        self.video_path_label.setText("未选择视频")
        self.analyze_btn.setEnabled(False)

        # 清空结果
        self.plot_type_label.setText("剧情类型：-")
        self.summary_label.setText("概要：-")
        self.duration_label.setText("时长：-")
        self.themes_label.setText("主题：-")
        self.structure_label.setText("等待分析...")
        self.emotion_label.setText("等待分析...")
        self.highlights_label.setText("等待分析...")
        self.cuts_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.progress_label.setText("等待开始...")

    def _on_export_cuts(self):
        """导出剪辑点"""
        if not self.analysis_result or not self.analysis_result.recommended_cuts:
            QMessageBox.warning(self, "警告", "没有可导出的剪辑点")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出剪辑点",
            "story_cuts.json",
            "JSON 文件 (*.json);;文本文件 (*.txt)"
        )

        if file_path:
            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "video_path": self.analysis_result.video_path,
                        "plot_type": self.analysis_result.plot_type.value,
                        "cuts": self.analysis_result.recommended_cuts
                    }, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"已导出到：{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败：{e}")
