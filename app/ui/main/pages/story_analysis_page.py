#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VideoForge - AI 剧情分析页面
基于故事的智能视频剪辑工具，支持单个视频和批量处理
"""

import os
import logging
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFileDialog, QProgressBar, QComboBox, QSpinBox,
    QTabWidget, QListWidget, QListWidgetItem, QSplitter,
    QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal

from .base_page import BasePage
from app.ui.components import (
    MacCard, MacElevatedCard, MacPrimaryButton,
    MacSecondaryButton, MacLabel, MacScrollArea, MacPageToolbar
)
from app.services.ai.story_analyzer import (
    StoryAnalyzer, StoryAnalysisResult
)
from app.services.ai.batch_story_processor import (
    BatchStoryProcessor, BatchStatus
)
from app.services.ai.cut_preview import CutPreviewGenerator


logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """剧情分析工作线程"""
    progress = Signal(str, float)  # stage, percentage
    finished = Signal(StoryAnalysisResult)
    error = Signal(str)
    cancelled = Signal()

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
        self.batch_processor: Optional[BatchStoryProcessor] = None
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

        # 创建批量处理器
        self.batch_processor = BatchStoryProcessor(max_concurrency=2)

    def create_content(self) -> None:
        """创建页面内容"""
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)

        # 选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("story_analysis_tabs")

        # 单个分析标签页
        self.single_tab = self._create_single_tab()
        self.tab_widget.addTab(self.single_tab, "📹 单个视频")

        # 批量处理标签页
        self.batch_tab = self._create_batch_tab()
        self.tab_widget.addTab(self.batch_tab, "📚 批量处理")

        self.main_layout.addWidget(self.tab_widget, 1)

    def _create_single_tab(self) -> QWidget:
        """创建单个分析标签页"""
        scroll = MacScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        # 工具栏
        toolbar = MacPageToolbar("🎬 AI 剧情分析")

        new_btn = MacPrimaryButton("📂 新建分析")
        new_btn.clicked.connect(self._on_new_analysis)
        toolbar.add_action(new_btn)

        export_btn = MacSecondaryButton("📤 导出剪辑点")
        export_btn.clicked.connect(self._on_export_cuts)
        toolbar.add_action(export_btn)

        self.preview_btn = MacSecondaryButton("🎬 预览剪辑")
        self.preview_btn.clicked.connect(self._on_generate_preview)
        self.preview_btn.setEnabled(False)
        toolbar.add_action(self.preview_btn)

        template_btn = MacSecondaryButton("📋 模板管理")
        template_btn.clicked.connect(self._on_open_template_editor)
        toolbar.add_action(template_btn)

        layout.addWidget(toolbar)

        # 主内容区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setSizes([400, 600])
        content_splitter.setCollapsible(0, False)

        # 左侧：输入和控制
        left_panel = self._create_single_input_panel()
        content_splitter.addWidget(left_panel)

        # 右侧：结果展示
        right_panel = self._create_single_result_panel()
        content_splitter.addWidget(right_panel)

        layout.addWidget(content_splitter, 1)

        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        return scroll

    def _create_batch_tab(self) -> QWidget:
        """创建批量处理标签页"""
        scroll = MacScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        # 工具栏
        toolbar = MacPageToolbar("📚 批量剧情分析")

        add_btn = MacPrimaryButton("➕ 添加视频")
        add_btn.clicked.connect(self._on_batch_add_videos)
        toolbar.add_action(add_btn)

        start_btn = MacSecondaryButton("▶ 开始处理")
        start_btn.clicked.connect(self._on_batch_start)
        toolbar.add_action(start_btn)

        export_btn = MacSecondaryButton("📤 导出结果")
        export_btn.clicked.connect(self._on_batch_export)
        toolbar.add_action(export_btn)

        clear_btn = MacSecondaryButton("🗑️ 清空")
        clear_btn.clicked.connect(self._on_batch_clear)
        toolbar.add_action(clear_btn)

        layout.addWidget(toolbar)

        # 任务列表
        task_card = MacCard("📋 任务列表")
        task_layout = task_card.layout()

        self.batch_list = QListWidget()
        self.batch_list.setMinimumHeight(200)
        task_layout.addWidget(self.batch_list)

        layout.addWidget(task_card)

        # 进度区域
        progress_card = MacCard("📊 处理进度")
        progress_layout = progress_card.layout()
        progress_layout.setSpacing(8)

        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setRange(0, 100)
        self.batch_progress_bar.setValue(0)
        progress_layout.addWidget(self.batch_progress_bar)

        self.batch_status_label = MacLabel("等待添加视频...")
        progress_layout.addWidget(self.batch_status_label)

        self.batch_cancel_btn = MacSecondaryButton("❌ 取消")
        self.batch_cancel_btn.clicked.connect(self._on_batch_cancel)
        self.batch_cancel_btn.setVisible(False)
        progress_layout.addWidget(self.batch_cancel_btn)

        layout.addWidget(progress_card)

        # 结果预览
        result_card = MacCard("📋 处理结果")
        result_layout = result_card.layout()
        result_layout.setSpacing(8)

        self.batch_results_table = QTableWidget()
        self.batch_results_table.setColumnCount(4)
        self.batch_results_table.setHorizontalHeaderLabels(["视频", "状态", "剧情类型", "时长"])
        self.batch_results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.batch_results_table.setMaximumHeight(200)
        result_layout.addWidget(self.batch_results_table)

        layout.addWidget(result_card)

        layout.addStretch()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        return scroll

    def _create_single_input_panel(self) -> QWidget:
        """创建单个分析输入面板"""
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

        # 目标时长
        duration_label = MacLabel("目标时长（秒，可选）")
        settings_layout.addWidget(duration_label)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 3600)
        self.duration_spin.setValue(0)
        self.duration_spin.setSuffix(" 秒 (0=保持原长)")
        settings_layout.addWidget(self.duration_spin)

        layout.addWidget(settings_card)

        # 分析按钮
        self.analyze_btn = MacPrimaryButton("🔍 开始分析")
        self.analyze_btn.clicked.connect(self._on_start_analysis)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)

        # 取消按钮
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

    def _create_single_result_panel(self) -> QWidget:
        """创建单个分析结果面板"""
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

        self.cuts_table = QTableWidget()
        self.cuts_table.setColumnCount(5)
        self.cuts_table.setHorizontalHeaderLabels(["类型", "开始", "结束", "时长", "说明"])
        self.cuts_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.cuts_table.setMaximumHeight(250)
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

    # ==================== 单个分析相关方法 ====================

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

        self.logger.info(f"Starting story analysis: {self.video_path}")

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
        self._reset_single_ui()

    def _on_analysis_progress(self, stage: str, percentage: float):
        """分析进度更新"""
        self.progress_bar.setValue(int(percentage))
        self.progress_label.setText(stage)

    def _on_analysis_finished(self, result: StoryAnalysisResult):
        """分析完成"""
        self.analysis_result = result
        self.logger.info(f"Analysis finished: {result.plot_type.value}")
        self._update_single_result_display(result)
        self._reset_single_ui()
        self.preview_btn.setEnabled(True)
        QMessageBox.information(self, "完成", "剧情分析完成！")

    def _on_analysis_error(self, error: str):
        """分析错误"""
        self.logger.error(f"Analysis error: {error}")
        self._reset_single_ui()
        QMessageBox.critical(self, "错误", f"分析失败：{error}")

    def _on_analysis_cancelled(self):
        """分析取消"""
        self.logger.info("Analysis cancelled by user")
        self._reset_single_ui()

    def _reset_single_ui(self):
        """重置单个分析 UI"""
        self.analyze_btn.setVisible(True)
        self.cancel_btn.setVisible(False)

    def _update_single_result_display(self, result: StoryAnalysisResult):
        """更新单个分析结果展示"""
        # 故事概览
        self.plot_type_label.setText(f"剧情类型：{result.plot_type.display_name}")
        self.summary_label.setText(f"概要：{result.summary or '无'}")
        self.duration_label.setText(f"时长：{int(result.duration // 60)}分{int(result.duration % 60)}秒")
        self.themes_label.setText(f"主题：{', '.join(result.themes) if result.themes else '无'}")

        # 叙事结构
        if result.segments:
            structure_text = []
            for seg in result.segments[:10]:
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
            for ep in result.emotional_curve[:5]:
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
            self.cuts_table.setItem(row, 0, QTableWidgetItem(cut.get("type", "keep")))
            self.cuts_table.setItem(row, 1, QTableWidgetItem(f"{cut.get('start', 0):.1f}s"))
            self.cuts_table.setItem(row, 2, QTableWidgetItem(f"{cut.get('end', 0):.1f}s"))
            self.cuts_table.setItem(row, 3, QTableWidgetItem(f"{cut.get('duration', 0):.1f}s"))
            self.cuts_table.setItem(row, 4, QTableWidgetItem(cut.get("reason", "")))
        self.cuts_table.resizeRowsToContents()

    def _on_new_analysis(self):
        """新建分析"""
        self.analysis_result = None
        self.video_path_label.setText("未选择视频")
        self.analyze_btn.setEnabled(False)

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

    def _on_generate_preview(self):
        """生成预览视频"""
        if not self.analysis_result or not self.analysis_result.recommended_cuts:
            QMessageBox.warning(self, "警告", "没有可用的剪辑点")
            return

        if not hasattr(self, 'video_path'):
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return

        # 选择输出位置
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存预览视频",
            "preview.mp4",
            "MP4 文件 (*.mp4)"
        )

        if not file_path:
            return

        self.logger.info(f"Generating preview: {file_path}")

        # 显示进度对话框
        progress = QProgressDialog(
            "正在生成预览...", "取消", 0, 100, self
        )
        progress.setWindowTitle("生成预览")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setValue(0)
        progress.show()

        try:
            generator = CutPreviewGenerator()

            def update_progress(p):
                progress.setValue(int(p))
                if progress.wasCanceled():
                    raise Exception("用户取消")

            # 生成预览
            output_path = generator.generate_preview_with_concat(
                self.video_path,
                self.analysis_result.recommended_cuts,
                output_path=file_path,
                progress_callback=update_progress
            )

            progress.close()

            # 打开预览
            import subprocess
            if os.name == 'darwin':  # macOS
                subprocess.run(['open', output_path])
            elif os.name == 'nt':  # Windows
                subprocess.run(['start', '', output_path], shell=True)
            else:  # Linux
                subprocess.run(['xdg-open', output_path])

            QMessageBox.information(
                self, "完成",
                f"预览已生成：{os.path.basename(output_path)}\n\n位置：{output_path}"
            )

        except Exception as e:
            progress.close()
            self.logger.error(f"Preview generation failed: {e}")
            QMessageBox.critical(self, "错误", f"生成预览失败：{e}")

    # ==================== 批量处理相关方法 ====================

    def _on_batch_add_videos(self):
        """添加视频到批量处理"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.webm);;所有文件 (*.*)"
        )

        if not file_paths:
            return

        for path in file_paths:
            # 添加任务
            task_id = self.batch_processor.add_task(path)

            # 添加到列表
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.ItemDataRole.UserRole, task_id)
            self.batch_list.addItem(item)

        self._update_batch_status()

    def _on_open_template_editor(self):
        """打开模板编辑器"""
        from app.ui.main.main_window import PageType

        main_window = self.application.get_service_by_name("main_window")
        if main_window and hasattr(main_window, 'switch_to_page'):
            main_window.switch_to_page(PageType.TEMPLATE_EDITOR)

    def _on_batch_start(self):
        """开始批量处理"""
        if self.batch_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先添加视频文件")
            return

        self.logger.info("Starting batch processing")

        # 显示取消按钮
        self.batch_cancel_btn.setVisible(True)

        # 创建进度对话框
        self.batch_progress_dialog = QProgressDialog(
            "正在处理...", "取消", 0, self.batch_list.count(), self
        )
        self.batch_progress_dialog.setWindowTitle("批量处理进度")
        self.batch_progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.batch_progress_dialog.canceled.connect(self._on_batch_cancel)
        self.batch_progress_dialog.show()

        # 处理所有任务
        _style = self.style_combo.currentData()
        self.batch_result = self.batch_processor.process_all(
            self.analyzer,
            progress_callback=self._on_batch_task_progress
        )

        # 更新结果表格
        self._update_batch_results()

        # 关闭进度对话框
        if self.batch_progress_dialog:
            self.batch_progress_dialog.close()

        self.batch_cancel_btn.setVisible(False)
        self._update_batch_status()

        # 显示完成信息
        QMessageBox.information(
            self,
            "完成",
            f"批量处理完成！\n成功：{self.batch_result.success_count}\n失败：{self.batch_result.failed_count}"
        )

    def _on_batch_task_progress(self, task_id: str, progress: float):
        """批量任务进度更新"""
        if self.batch_progress_dialog:
            completed = len([t for t in self.batch_processor.get_completed_tasks()])
            self.batch_progress_dialog.setValue(completed)
            self.batch_progress_dialog.setLabelText(
                f"正在处理... {completed}/{self.batch_list.count()}"
            )

    def _on_batch_cancel(self):
        """取消批量处理"""
        self.logger.info("Cancelling batch processing")
        self.batch_processor.cancel_all()
        self.batch_cancel_btn.setVisible(False)
        self._update_batch_status()

    def _update_batch_status(self):
        """更新批量处理状态"""
        total = self.batch_list.count()
        completed = len(self.batch_processor.get_completed_tasks())
        failed = len(self.batch_processor.get_failed_tasks())

        if total == 0:
            self.batch_status_label.setText("等待添加视频...")
            self.batch_progress_bar.setValue(0)
        else:
            self.batch_status_label.setText(f"总计: {total} | 完成: {completed} | 失败: {failed}")
            self.batch_progress_bar.setValue(int((completed + failed) / total * 100))

    def _update_batch_results(self):
        """更新批量处理结果表格"""
        self.batch_results_table.setRowCount(0)

        for task in self.batch_result.results:
            row = self.batch_results_table.rowCount()
            self.batch_results_table.insertRow(row)

            # 视频名称
            self.batch_results_table.setItem(row, 0, QTableWidgetItem(os.path.basename(task.video_path)))

            # 状态
            status_text = {
                BatchStatus.COMPLETED: "✅ 完成",
                BatchStatus.FAILED: "❌ 失败",
                BatchStatus.CANCELLED: "⚠️ 取消",
                BatchStatus.PROCESSING: "🔄 处理中",
                BatchStatus.PENDING: "⏳ 等待"
            }.get(task.status, str(task.status.value))
            self.batch_results_table.setItem(row, 1, QTableWidgetItem(status_text))

            # 剧情类型
            plot_type = task.result.plot_type.display_name if task.result else "-"
            self.batch_results_table.setItem(row, 2, QTableWidgetItem(plot_type))

            # 时长
            duration = f"{int(task.duration)}s" if task.duration else "-"
            self.batch_results_table.setItem(row, 3, QTableWidgetItem(duration))

        self.batch_results_table.resizeRowsToContents()

    def _on_batch_export(self):
        """导出批量处理结果"""
        if not self.batch_result:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出批量结果",
            "batch_results.json",
            "JSON 文件 (*.json)"
        )

        if file_path:
            try:
                output_file = self.batch_processor.export_results(self.batch_result)
                QMessageBox.information(self, "成功", f"已导出到：{output_file}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败：{e}")

    def _on_batch_clear(self):
        """清空批量任务"""
        self.batch_processor.clear_completed()
        self.batch_list.clear()
        self.batch_results_table.setRowCount(0)
        self._update_batch_status()
