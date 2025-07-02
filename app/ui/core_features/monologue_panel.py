#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI第一人称独白功能面板
提供完整的独白生成用户界面
"""

import os
import asyncio
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QSlider, QProgressBar,
    QTextEdit, QFileDialog, QMessageBox, QGroupBox,
    QFormLayout, QCheckBox, QSpinBox, QTabWidget,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

from ...ai.ai_manager import AIManager
from ...ai.generators.monologue_generator import MonologueGenerator, MonologueResult
from ...core.video_processor import VideoProcessor
from ..components.video_player import VideoPlayer


class MonologueWorker(QThread):
    """独白生成工作线程"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    generation_completed = pyqtSignal(object)  # MonologueResult
    error_occurred = pyqtSignal(str)
    
    def __init__(self, generator: MonologueGenerator, video_path: str, 
                 character_type: str, perspective: str):
        super().__init__()
        self.generator = generator
        self.video_path = video_path
        self.character_type = character_type
        self.perspective = perspective
        
        # 连接信号
        self.generator.progress_updated.connect(self.progress_updated)
        self.generator.status_updated.connect(self.status_updated)
        self.generator.generation_completed.connect(self.generation_completed)
        self.generator.error_occurred.connect(self.error_occurred)
    
    def run(self):
        """运行独白生成"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.generator.generate_monologue(
                    self.video_path, self.character_type, self.perspective
                )
            )
            
            loop.close()
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class MonologuePanel(QWidget):
    """AI第一人称独白面板"""
    
    # 信号
    video_generated = pyqtSignal(str)  # 生成的视频路径
    
    def __init__(self, ai_manager: AIManager):
        super().__init__()
        self.ai_manager = ai_manager
        self.monologue_generator = MonologueGenerator(ai_manager)
        self.video_processor = VideoProcessor()
        
        self.current_video_path = ""
        self.current_result: Optional[MonologueResult] = None
        self.worker_thread: Optional[MonologueWorker] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("💭 AI第一人称独白生成")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1e40af; padding: 8px 0px;")
        layout.addWidget(title_label)
        
        # 创建主要内容区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)
        
        # 左侧控制面板
        left_panel = self._create_control_panel()
        content_splitter.addWidget(left_panel)
        
        # 右侧预览面板
        right_panel = self._create_preview_panel()
        content_splitter.addWidget(right_panel)
        
        # 设置分隔比例
        content_splitter.setSizes([400, 600])
        
        # 底部状态栏
        status_layout = self._create_status_bar()
        layout.addLayout(status_layout)
    
    def _create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        
        # 视频选择区域
        video_group = QGroupBox("📁 视频文件")
        video_layout = QVBoxLayout(video_group)
        
        # 文件选择
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("请选择视频文件...")
        self.file_path_label.setStyleSheet("color: #6b7280; font-style: italic;")
        file_layout.addWidget(self.file_path_label)
        
        self.select_file_btn = QPushButton("选择文件")
        self.select_file_btn.setObjectName("primary_button")
        self.select_file_btn.clicked.connect(self._select_video_file)
        file_layout.addWidget(self.select_file_btn)
        
        video_layout.addLayout(file_layout)
        
        # 视频信息显示
        self.video_info_label = QLabel("")
        self.video_info_label.setStyleSheet("color: #374151; font-size: 12px;")
        video_layout.addWidget(self.video_info_label)
        
        layout.addWidget(video_group)
        
        # 角色设置区域
        character_group = QGroupBox("👤 角色设置")
        character_layout = QFormLayout(character_group)
        
        # 角色类型
        self.character_combo = QComboBox()
        self.character_combo.addItems(["都市白领", "校园学生", "家庭主妇", "创业者", "退休老人"])
        self.character_combo.setCurrentText("都市白领")
        character_layout.addRow("角色类型:", self.character_combo)
        
        # 视角选择
        self.perspective_combo = QComboBox()
        self.perspective_combo.addItems(["主角", "配角", "旁观者"])
        self.perspective_combo.setCurrentText("主角")
        character_layout.addRow("视角选择:", self.perspective_combo)
        
        # AI模型选择
        self.model_combo = QComboBox()
        self._update_model_list()
        character_layout.addRow("AI模型:", self.model_combo)
        
        # 高级设置
        self.emotion_analysis_check = QCheckBox("启用情感分析")
        self.emotion_analysis_check.setChecked(True)
        character_layout.addRow("", self.emotion_analysis_check)
        
        self.scene_matching_check = QCheckBox("场景情感匹配")
        self.scene_matching_check.setChecked(True)
        character_layout.addRow("", self.scene_matching_check)
        
        layout.addWidget(character_group)
        
        # 生成控制
        control_group = QGroupBox("🚀 生成控制")
        control_layout = QVBoxLayout(control_group)
        
        # 生成按钮
        self.generate_btn = QPushButton("💭 开始生成独白")
        self.generate_btn.setObjectName("primary_button")
        self.generate_btn.setMinimumHeight(45)
        self.generate_btn.clicked.connect(self._start_generation)
        control_layout.addWidget(self.generate_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("⏹️ 停止生成")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_generation)
        control_layout.addWidget(self.stop_btn)
        
        layout.addWidget(control_group)
        
        # 导出控制
        export_group = QGroupBox("📤 导出设置")
        export_layout = QVBoxLayout(export_group)
        
        self.export_btn = QPushButton("💾 导出视频")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_video)
        export_layout.addWidget(self.export_btn)
        
        self.open_folder_btn = QPushButton("📁 打开文件夹")
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        export_layout.addWidget(self.open_folder_btn)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        return panel
    
    def _create_preview_panel(self) -> QWidget:
        """创建预览面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        
        # 预览标题
        preview_title = QLabel("🎥 预览与结果")
        preview_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        preview_title.setStyleSheet("color: #1e40af;")
        layout.addWidget(preview_title)
        
        # 选项卡
        self.preview_tabs = QTabWidget()
        layout.addWidget(self.preview_tabs)
        
        # 视频预览选项卡
        self.video_preview_tab = self._create_video_preview_tab()
        self.preview_tabs.addTab(self.video_preview_tab, "视频预览")
        
        # 独白内容选项卡
        self.monologue_tab = self._create_monologue_tab()
        self.preview_tabs.addTab(self.monologue_tab, "独白内容")
        
        # 角色档案选项卡
        self.character_tab = self._create_character_tab()
        self.preview_tabs.addTab(self.character_tab, "角色档案")
        
        # 生成日志选项卡
        self.log_tab = self._create_log_tab()
        self.preview_tabs.addTab(self.log_tab, "生成日志")
        
        return panel
    
    def _create_video_preview_tab(self) -> QWidget:
        """创建视频预览选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 视频播放器
        self.video_player = VideoPlayer()
        self.video_player.setMinimumHeight(300)
        layout.addWidget(self.video_player)
        
        # 播放控制
        control_layout = QHBoxLayout()
        
        self.play_original_btn = QPushButton("播放原视频")
        self.play_original_btn.clicked.connect(self._play_original)
        control_layout.addWidget(self.play_original_btn)
        
        self.play_result_btn = QPushButton("播放独白版")
        self.play_result_btn.setEnabled(False)
        self.play_result_btn.clicked.connect(self._play_result)
        control_layout.addWidget(self.play_result_btn)
        
        layout.addLayout(control_layout)
        
        return tab
    
    def _create_monologue_tab(self) -> QWidget:
        """创建独白内容选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 独白片段列表
        self.monologue_list = QListWidget()
        self.monologue_list.setMinimumHeight(200)
        layout.addWidget(self.monologue_list)
        
        # 内容编辑
        edit_layout = QHBoxLayout()
        
        self.edit_monologue_btn = QPushButton("编辑选中独白")
        self.edit_monologue_btn.setEnabled(False)
        edit_layout.addWidget(self.edit_monologue_btn)
        
        self.regenerate_btn = QPushButton("重新生成")
        self.regenerate_btn.setEnabled(False)
        edit_layout.addWidget(self.regenerate_btn)
        
        layout.addLayout(edit_layout)
        
        return tab
    
    def _create_character_tab(self) -> QWidget:
        """创建角色档案选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 角色信息显示
        self.character_info = QTextEdit()
        self.character_info.setReadOnly(True)
        self.character_info.setMaximumHeight(200)
        layout.addWidget(self.character_info)
        
        return tab
    
    def _create_log_tab(self) -> QWidget:
        """创建日志选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # 日志控制
        log_control_layout = QHBoxLayout()
        
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self._clear_log)
        log_control_layout.addWidget(self.clear_log_btn)
        
        self.save_log_btn = QPushButton("保存日志")
        self.save_log_btn.clicked.connect(self._save_log)
        log_control_layout.addWidget(self.save_log_btn)
        
        log_control_layout.addStretch()
        layout.addLayout(log_control_layout)
        
        return tab
    
    def _create_status_bar(self) -> QHBoxLayout:
        """创建状态栏"""
        layout = QHBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        layout.addWidget(self.progress_bar)
        
        return layout
    
    def _connect_signals(self):
        """连接信号"""
        pass
    
    def _update_model_list(self):
        """更新AI模型列表"""
        self.model_combo.clear()
        available_models = self.ai_manager.get_available_models()
        
        for model in available_models:
            display_name = {
                "zhipu": "智谱AI",
                "qianwen": "通义千问", 
                "wenxin": "文心一言",
                "xunfei": "讯飞星火",
                "hunyuan": "腾讯混元",
                "deepseek": "DeepSeek",
                "openai": "OpenAI",
                "ollama": "Ollama"
            }.get(model, model.title())
            
            self.model_combo.addItem(display_name, model)
    
    def _select_video_file(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv);;所有文件 (*)"
        )
        
        if file_path:
            self.current_video_path = file_path
            self.file_path_label.setText(os.path.basename(file_path))
            self.file_path_label.setStyleSheet("color: #374151;")
            
            # 分析视频信息
            self._analyze_video_info()
    
    def _analyze_video_info(self):
        """分析视频信息"""
        try:
            video_info = self.video_processor.analyze_video(self.current_video_path)
            
            info_text = f"""
            时长: {video_info.duration:.1f}秒
            分辨率: {video_info.width}x{video_info.height}
            帧率: {video_info.fps:.1f}fps
            文件大小: {video_info.file_size / (1024*1024):.1f}MB
            """
            
            self.video_info_label.setText(info_text.strip())
            
            # 加载到播放器
            self.video_player.load_video(self.current_video_path)
            
        except Exception as e:
            self._add_log(f"视频分析失败: {str(e)}", "error")
    
    def _start_generation(self):
        """开始生成独白"""
        if not self.current_video_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return
        
        # 获取设置
        character_type = self.character_combo.currentText()
        perspective = self.perspective_combo.currentText()
        
        # 禁用控制按钮
        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 创建工作线程
        self.worker_thread = MonologueWorker(
            self.monologue_generator, self.current_video_path, character_type, perspective
        )
        
        # 连接信号
        self.worker_thread.progress_updated.connect(self._on_progress_updated)
        self.worker_thread.status_updated.connect(self._on_status_updated)
        self.worker_thread.generation_completed.connect(self._on_generation_completed)
        self.worker_thread.error_occurred.connect(self._on_generation_error)
        
        # 启动线程
        self.worker_thread.start()
        
        self._add_log("开始生成AI第一人称独白...", "info")
    
    def _stop_generation(self):
        """停止生成"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
        
        self._reset_ui_state()
        self._add_log("生成已停止", "warning")
    
    def _on_progress_updated(self, progress: int):
        """进度更新"""
        self.progress_bar.setValue(progress)
    
    def _on_status_updated(self, status: str):
        """状态更新"""
        self.status_label.setText(status)
        self._add_log(status, "info")
    
    def _on_generation_completed(self, result: MonologueResult):
        """生成完成"""
        self.current_result = result
        self._reset_ui_state()
        
        # 启用相关按钮
        self.export_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(True)
        self.play_result_btn.setEnabled(True)
        
        # 更新内容显示
        self._update_monologue_list(result)
        self._update_character_info(result)
        
        # 切换到预览选项卡
        self.preview_tabs.setCurrentIndex(0)
        
        self._add_log(f"独白生成完成！输出文件: {result.output_video_path}", "success")
        
        # 发送信号
        self.video_generated.emit(result.output_video_path)
    
    def _on_generation_error(self, error: str):
        """生成错误"""
        self._reset_ui_state()
        self._add_log(f"生成失败: {error}", "error")
        QMessageBox.critical(self, "错误", f"独白生成失败:\n{error}")
    
    def _reset_ui_state(self):
        """重置UI状态"""
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("就绪")
    
    def _update_monologue_list(self, result: MonologueResult):
        """更新独白列表"""
        self.monologue_list.clear()
        
        for i, segment in enumerate(result.segments):
            item_text = f"[{segment.start_time:.1f}s-{segment.end_time:.1f}s] {segment.emotion}: {segment.text[:30]}..."
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, segment)
            self.monologue_list.addItem(item)
    
    def _update_character_info(self, result: MonologueResult):
        """更新角色信息"""
        character = result.character_profile
        
        info_text = f"""
角色档案
========

角色名称: {character.name}
性格特征: {character.personality}
年龄段: {character.age_group}
说话风格: {character.speaking_style}

角色背景:
{character.background}

情感特质:
{', '.join(character.emotional_traits)}

生成统计:
- 独白片段数: {len(result.segments)}
- 总独白时长: {sum(s.end_time - s.start_time for s in result.segments):.1f}秒
- 视频总时长: {result.total_duration:.1f}秒
        """
        
        self.character_info.setText(info_text.strip())
    
    def _play_original(self):
        """播放原视频"""
        if self.current_video_path:
            self.video_player.load_video(self.current_video_path)
    
    def _play_result(self):
        """播放独白版视频"""
        if self.current_result:
            self.video_player.load_video(self.current_result.output_video_path)
    
    def _export_video(self):
        """导出视频"""
        if not self.current_result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存独白视频", "monologue_output.mp4",
            "MP4文件 (*.mp4);;所有文件 (*)"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(self.current_result.output_video_path, file_path)
                QMessageBox.information(self, "成功", f"视频已保存到:\n{file_path}")
                self._add_log(f"视频已导出: {file_path}", "success")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
    
    def _open_output_folder(self):
        """打开输出文件夹"""
        if self.current_result:
            import subprocess
            import platform
            
            folder_path = os.path.dirname(self.current_result.output_video_path)
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", folder_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
    
    def _add_log(self, message: str, level: str = "info"):
        """添加日志"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        color_map = {
            "info": "#374151",
            "success": "#059669", 
            "warning": "#d97706",
            "error": "#dc2626"
        }
        
        color = color_map.get(level, "#374151")
        formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        
        self.log_text.append(formatted_message)
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def _clear_log(self):
        """清空日志"""
        self.log_text.clear()
    
    def _save_log(self):
        """保存日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志", "monologue_log.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "成功", "日志已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
