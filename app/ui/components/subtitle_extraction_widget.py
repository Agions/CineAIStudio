#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字幕提取组件
提供现代化的字幕提取界面
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QCheckBox, QComboBox, QGroupBox,
    QFileDialog, QMessageBox, QTabWidget, QListWidget, QListWidgetItem,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QTextCursor

from app.services.subtitle_service import SubtitleExtractionService, SubtitleExtractionResult
from app.ui.professional_ui_system import ProfessionalButton, ProfessionalCard, ProfessionalTheme


class SubtitleExtractionWorker(QThread):
    """字幕提取工作线程"""
    
    progress_updated = pyqtSignal(float, str)
    extraction_completed = pyqtSignal(object)  # SubtitleExtractionResult
    
    def __init__(self, service: SubtitleExtractionService, video_path: str, methods: list):
        super().__init__()
        self.service = service
        self.video_path = video_path
        self.methods = methods
    
    def run(self):
        """执行字幕提取"""
        try:
            result = self.service.extract_subtitles(
                self.video_path,
                self.methods,
                progress_callback=self.progress_updated.emit
            )
            self.extraction_completed.emit(result)
        except Exception as e:
            result = SubtitleExtractionResult()
            result.success = False
            result.error_message = str(e)
            self.extraction_completed.emit(result)


class SubtitleExtractionWidget(QWidget):
    """字幕提取组件"""
    
    # 信号
    extraction_completed = pyqtSignal(object)  # SubtitleExtractionResult
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.service = SubtitleExtractionService()
        self.current_result = None
        self.worker = None
        self.is_dark_theme = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("字幕提取")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 主要内容区域
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：配置面板
        config_panel = self._create_config_panel()
        main_splitter.addWidget(config_panel)
        
        # 右侧：结果面板
        result_panel = self._create_result_panel()
        main_splitter.addWidget(result_panel)
        
        # 设置分割比例
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        
        layout.addWidget(main_splitter)
        
        # 底部：进度和控制
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
    
    def _create_config_panel(self) -> QWidget:
        """创建配置面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        
        # 视频文件选择
        file_card = ProfessionalCard("视频文件")
        
        file_layout = QVBoxLayout()
        
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setWordWrap(True)
        file_layout.addWidget(self.file_path_label)
        
        file_buttons_layout = QHBoxLayout()
        
        self.select_file_btn = ProfessionalButton("📁 选择视频", "primary")
        self.select_file_btn.clicked.connect(self._select_video_file)
        file_buttons_layout.addWidget(self.select_file_btn)
        
        self.clear_file_btn = ProfessionalButton("🗑️ 清除", "default")
        self.clear_file_btn.clicked.connect(self._clear_file)
        self.clear_file_btn.setEnabled(False)
        file_buttons_layout.addWidget(self.clear_file_btn)
        
        file_buttons_widget = QWidget()
        file_buttons_widget.setLayout(file_buttons_layout)
        file_layout.addWidget(file_buttons_widget)
        
        file_card_widget = QWidget()
        file_card_widget.setLayout(file_layout)
        file_card.add_content(file_card_widget)
        
        layout.addWidget(file_card)
        
        # 提取方法选择
        method_card = ProfessionalCard("提取方法")
        
        method_layout = QVBoxLayout()
        
        self.ocr_checkbox = QCheckBox("🔍 OCR字幕提取")
        self.ocr_checkbox.setChecked(True)
        self.ocr_checkbox.setToolTip("从视频帧中识别字幕文字")
        method_layout.addWidget(self.ocr_checkbox)
        
        self.speech_checkbox = QCheckBox("🎤 语音识别提取")
        self.speech_checkbox.setChecked(True)
        self.speech_checkbox.setToolTip("从音频中识别语音内容")
        method_layout.addWidget(self.speech_checkbox)
        
        # 高级选项
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QVBoxLayout(advanced_group)
        
        self.parallel_checkbox = QCheckBox("并行处理")
        self.parallel_checkbox.setChecked(True)
        self.parallel_checkbox.setToolTip("同时进行OCR和语音识别")
        advanced_layout.addWidget(self.parallel_checkbox)
        
        self.auto_merge_checkbox = QCheckBox("自动合并结果")
        self.auto_merge_checkbox.setChecked(True)
        self.auto_merge_checkbox.setToolTip("自动合并多种方法的提取结果")
        advanced_layout.addWidget(self.auto_merge_checkbox)
        
        # 语音模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("语音模型:"))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["base", "small", "medium", "large"])
        self.model_combo.setCurrentText("base")
        self.model_combo.setToolTip("更大的模型精度更高但速度更慢")
        model_layout.addWidget(self.model_combo)
        
        model_widget = QWidget()
        model_widget.setLayout(model_layout)
        advanced_layout.addWidget(model_widget)
        
        method_layout.addWidget(advanced_group)
        
        method_card_widget = QWidget()
        method_card_widget.setLayout(method_layout)
        method_card.add_content(method_card_widget)
        
        layout.addWidget(method_card)
        
        # 预估信息
        self.info_card = ProfessionalCard("提取信息")
        self.info_label = QLabel("请先选择视频文件")
        self.info_card.add_content(self.info_label)
        layout.addWidget(self.info_card)
        
        layout.addStretch()
        
        return panel
    
    def _create_result_panel(self) -> QWidget:
        """创建结果面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        
        # 结果选项卡
        self.result_tabs = QTabWidget()
        
        # 字幕预览选项卡
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        self.subtitle_preview = QTextEdit()
        self.subtitle_preview.setPlaceholderText("字幕内容将在提取完成后显示...")
        self.subtitle_preview.setReadOnly(True)
        preview_layout.addWidget(self.subtitle_preview)
        
        self.result_tabs.addTab(preview_tab, "📝 字幕预览")
        
        # 提取详情选项卡
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        
        self.details_text = QTextEdit()
        self.details_text.setPlaceholderText("提取详情将在处理完成后显示...")
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        self.result_tabs.addTab(details_tab, "📊 提取详情")
        
        # 关键词选项卡
        keywords_tab = QWidget()
        keywords_layout = QVBoxLayout(keywords_tab)
        
        self.keywords_list = QListWidget()
        keywords_layout.addWidget(self.keywords_list)
        
        self.result_tabs.addTab(keywords_tab, "🔑 关键词")
        
        layout.addWidget(self.result_tabs)
        
        # 导出按钮
        export_layout = QHBoxLayout()
        
        self.export_srt_btn = ProfessionalButton("📄 导出SRT", "default")
        self.export_srt_btn.clicked.connect(self._export_srt)
        self.export_srt_btn.setEnabled(False)
        export_layout.addWidget(self.export_srt_btn)
        
        self.export_vtt_btn = ProfessionalButton("📄 导出VTT", "default")
        self.export_vtt_btn.clicked.connect(self._export_vtt)
        self.export_vtt_btn.setEnabled(False)
        export_layout.addWidget(self.export_vtt_btn)
        
        export_layout.addStretch()
        
        export_widget = QWidget()
        export_widget.setLayout(export_layout)
        layout.addWidget(export_widget)
        
        return panel
    
    def _create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Box)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 控制按钮
        buttons_layout = QHBoxLayout()
        
        self.start_btn = ProfessionalButton("🚀 开始提取", "primary")
        self.start_btn.clicked.connect(self._start_extraction)
        self.start_btn.setEnabled(False)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = ProfessionalButton("⏹️ 停止", "danger")
        self.stop_btn.clicked.connect(self._stop_extraction)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        buttons_layout.addStretch()
        
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        layout.addWidget(buttons_widget)
        
        return panel
    
    def _select_video_file(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;所有文件 (*)"
        )
        
        if file_path:
            self.file_path_label.setText(file_path)
            self.clear_file_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            
            # 更新提取信息
            self._update_extraction_info(file_path)
    
    def _clear_file(self):
        """清除文件选择"""
        self.file_path_label.setText("未选择文件")
        self.clear_file_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.info_label.setText("请先选择视频文件")
    
    def _update_extraction_info(self, video_path: str):
        """更新提取信息"""
        try:
            info = self.service.get_extraction_info(video_path)
            
            info_text = f"视频文件: {os.path.basename(video_path)}\n\n"
            info_text += "可用方法:\n"
            for method in info["available_methods"]:
                method_name = {"ocr": "OCR字幕提取", "speech": "语音识别"}.get(method, method)
                estimated_time = info["estimated_time"].get(method, "未知")
                info_text += f"• {method_name} (预计: {estimated_time})\n"
            
            if info["recommendations"]:
                info_text += "\n建议:\n"
                for rec in info["recommendations"]:
                    info_text += f"• {rec}\n"
            
            self.info_label.setText(info_text)
            
        except Exception as e:
            self.info_label.setText(f"获取文件信息失败: {e}")
    
    def _start_extraction(self):
        """开始字幕提取"""
        video_path = self.file_path_label.text()
        if video_path == "未选择文件":
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return
        
        # 检查提取方法
        methods = []
        if self.ocr_checkbox.isChecked():
            methods.append("ocr")
        if self.speech_checkbox.isChecked():
            methods.append("speech")
        
        if not methods:
            QMessageBox.warning(self, "警告", "请至少选择一种提取方法")
            return
        
        # 更新服务配置
        self.service.parallel_extraction = self.parallel_checkbox.isChecked()
        self.service.auto_merge = self.auto_merge_checkbox.isChecked()
        self.service.speech_extractor.set_model_size(self.model_combo.currentText())
        
        # 启动工作线程
        self.worker = SubtitleExtractionWorker(self.service, video_path, methods)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.extraction_completed.connect(self._on_extraction_completed)
        self.worker.start()
        
        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在提取字幕...")
    
    def _stop_extraction(self):
        """停止字幕提取"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        self._reset_ui_state()
        self.status_label.setText("已停止")
    
    def _on_progress_updated(self, progress: float, message: str):
        """进度更新处理"""
        self.progress_bar.setValue(int(progress))
        self.status_label.setText(message)
    
    def _on_extraction_completed(self, result: SubtitleExtractionResult):
        """提取完成处理"""
        self.current_result = result
        
        if result.success:
            self._display_result(result)
            self.status_label.setText(f"提取完成 (耗时: {result.processing_time:.1f}秒)")
            
            # 启用导出按钮
            self.export_srt_btn.setEnabled(True)
            self.export_vtt_btn.setEnabled(True)
            
            # 发射完成信号
            self.extraction_completed.emit(result)
            
        else:
            self.status_label.setText(f"提取失败: {result.error_message}")
            QMessageBox.critical(self, "提取失败", result.error_message)
        
        self._reset_ui_state()
    
    def _display_result(self, result: SubtitleExtractionResult):
        """显示提取结果"""
        # 显示字幕预览
        primary_track = result.get_primary_track()
        if primary_track:
            subtitle_text = ""
            for i, segment in enumerate(primary_track.segments, 1):
                start_time = self._format_time(segment.start_time)
                end_time = self._format_time(segment.end_time)
                subtitle_text += f"{i}\n{start_time} --> {end_time}\n{segment.text}\n\n"
            
            self.subtitle_preview.setText(subtitle_text)
        
        # 显示提取详情
        details_text = f"提取方法: {', '.join(result.methods)}\n"
        details_text += f"处理时间: {result.processing_time:.2f}秒\n"
        details_text += f"字幕轨道数: {len(result.tracks)}\n\n"
        
        for method, extraction_result in result.extraction_results.items():
            details_text += f"{method.upper()}提取结果:\n"
            if extraction_result.success:
                track_count = len(extraction_result.tracks)
                details_text += f"  成功提取 {track_count} 个轨道\n"
                if extraction_result.tracks:
                    segment_count = sum(len(track.segments) for track in extraction_result.tracks)
                    details_text += f"  总片段数: {segment_count}\n"
            else:
                details_text += f"  失败: {extraction_result.error_message}\n"
            details_text += "\n"
        
        self.details_text.setText(details_text)
        
        # 显示关键词
        self.keywords_list.clear()
        if result.keywords:
            for keyword, count in result.keywords:
                item = QListWidgetItem(f"{keyword} ({count})")
                self.keywords_list.addItem(item)
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _reset_ui_state(self):
        """重置UI状态"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
    
    def _export_srt(self):
        """导出SRT格式"""
        if not self.current_result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存SRT文件", "", "SRT文件 (*.srt)"
        )
        
        if file_path:
            try:
                srt_content = self.current_result.export_srt()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                
                QMessageBox.information(self, "成功", "SRT文件导出成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def _export_vtt(self):
        """导出VTT格式"""
        if not self.current_result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存VTT文件", "", "VTT文件 (*.vtt)"
        )
        
        if file_path:
            try:
                vtt_content = self.current_result.export_vtt()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(vtt_content)
                
                QMessageBox.information(self, "成功", "VTT文件导出成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def _apply_styles(self):
        """应用样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        
        self.setStyleSheet(f"""
            SubtitleExtractionWidget {{
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
            QTextEdit {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }}
            QCheckBox {{
                color: {colors['text_primary']};
                font-size: 14px;
            }}
            QComboBox {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }}
            QProgressBar {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                text-align: center;
                color: {colors['text_primary']};
                font-weight: 500;
            }}
            QProgressBar::chunk {{
                background-color: {colors['primary']};
                border-radius: 5px;
            }}
            QGroupBox {{
                color: {colors['text_primary']};
                font-weight: 500;
                border: 1px solid {colors['border']};
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }}
        """)
    
    def set_theme(self, is_dark: bool):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()
        
        # 更新所有专业组件主题
        for card in self.findChildren(ProfessionalCard):
            card.set_theme(is_dark)
        for button in self.findChildren(ProfessionalButton):
            button.set_theme(is_dark)
