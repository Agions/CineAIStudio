#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFormLayout, QComboBox, QTextEdit, QListWidget,
    QListWidgetItem, QMessageBox, QFrame, QProgressBar,
    QFileDialog, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap

from app.core.video_manager import VideoClip
from app.ai.content_generator import GeneratedContent
from app.integrations.jianying_integration import JianYingIntegration, JianYingProject


class JianYingIntegrationPanel(QWidget):
    """剪映集成面板"""
    
    project_exported = pyqtSignal(str)  # 项目路径
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.jianying_integration = JianYingIntegration()
        self.current_video = None
        self.current_content = None
        self.current_project = None
        
        self._setup_ui()
        self._connect_signals()
        self._check_installation()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("剪映集成")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 安装状态
        status_group = QGroupBox("剪映状态")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("检查中...")
        status_layout.addWidget(self.status_label)
        
        # 安装指南按钮
        self.install_guide_btn = QPushButton("查看安装指南")
        self.install_guide_btn.clicked.connect(self._show_installation_guide)
        status_layout.addWidget(self.install_guide_btn)
        
        layout.addWidget(status_group)
        
        # 项目创建
        create_group = QGroupBox("创建剪映项目")
        create_layout = QVBoxLayout(create_group)
        
        # 当前视频信息
        video_info_layout = QHBoxLayout()
        video_info_layout.addWidget(QLabel("当前视频:"))
        self.video_info_label = QLabel("未选择视频")
        self.video_info_label.setStyleSheet("color: #666;")
        video_info_layout.addWidget(self.video_info_label)
        video_info_layout.addStretch()
        create_layout.addLayout(video_info_layout)
        
        # 项目类型选择
        type_layout = QFormLayout()
        
        self.project_type_combo = QComboBox()
        self.project_type_combo.addItems([
            "基础视频项目", "AI解说项目", "AI混剪项目", "AI独白项目"
        ])
        self.project_type_combo.currentTextChanged.connect(self._on_project_type_changed)
        type_layout.addRow("项目类型:", self.project_type_combo)
        
        # 项目名称
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("自动生成项目名称")
        type_layout.addRow("项目名称:", self.project_name_edit)
        
        create_layout.addLayout(type_layout)
        
        # 高级选项
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QFormLayout(advanced_group)
        
        # 视频质量
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["1080p (1920x1080)", "720p (1280x720)", "4K (3840x2160)"])
        advanced_layout.addRow("视频质量:", self.quality_combo)
        
        # 帧率
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30 FPS", "60 FPS", "24 FPS"])
        advanced_layout.addRow("帧率:", self.fps_combo)
        
        # 复制媒体文件
        self.copy_media_check = QCheckBox("复制媒体文件到项目文件夹")
        self.copy_media_check.setChecked(True)
        advanced_layout.addRow("", self.copy_media_check)
        
        create_layout.addWidget(advanced_group)
        
        # 创建按钮
        button_layout = QHBoxLayout()
        
        self.create_basic_btn = QPushButton("创建基础项目")
        self.create_basic_btn.clicked.connect(self._create_basic_project)
        button_layout.addWidget(self.create_basic_btn)
        
        self.create_ai_btn = QPushButton("从AI内容创建")
        self.create_ai_btn.clicked.connect(self._create_ai_project)
        self.create_ai_btn.setEnabled(False)
        button_layout.addWidget(self.create_ai_btn)
        
        create_layout.addLayout(button_layout)
        
        layout.addWidget(create_group)
        
        # 项目管理
        manage_group = QGroupBox("项目管理")
        manage_layout = QVBoxLayout(manage_group)
        
        # 当前项目信息
        self.project_info_label = QLabel("无项目")
        self.project_info_label.setStyleSheet("color: #666;")
        manage_layout.addWidget(self.project_info_label)
        
        # 操作按钮
        manage_button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("导出到剪映")
        self.export_btn.clicked.connect(self._export_project)
        self.export_btn.setEnabled(False)
        manage_button_layout.addWidget(self.export_btn)
        
        self.open_jianying_btn = QPushButton("在剪映中打开")
        self.open_jianying_btn.clicked.connect(self._open_in_jianying)
        self.open_jianying_btn.setEnabled(False)
        manage_button_layout.addWidget(self.open_jianying_btn)
        
        manage_layout.addLayout(manage_button_layout)
        
        # 导出路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("导出路径:"))
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setPlaceholderText("选择导出路径")
        path_layout.addWidget(self.export_path_edit)
        
        self.browse_path_btn = QPushButton("浏览")
        self.browse_path_btn.clicked.connect(self._browse_export_path)
        path_layout.addWidget(self.browse_path_btn)
        
        manage_layout.addLayout(path_layout)
        
        layout.addWidget(manage_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
    
    def _connect_signals(self):
        """连接信号"""
        self.jianying_integration.project_created.connect(self._on_project_created)
        self.jianying_integration.export_completed.connect(self._on_export_completed)
    
    def _check_installation(self):
        """检查剪映安装状态"""
        if self.jianying_integration.is_jianying_installed():
            paths = self.jianying_integration.get_installation_paths()
            self.status_label.setText(f"✅ 剪映已安装\n路径: {paths[0]}")
            self.status_label.setStyleSheet("color: green;")
            
            # 启用相关功能
            self.create_basic_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.open_jianying_btn.setEnabled(True)
        else:
            self.status_label.setText("❌ 未检测到剪映安装")
            self.status_label.setStyleSheet("color: red;")
            
            # 禁用相关功能
            self.create_basic_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.open_jianying_btn.setEnabled(False)
    
    def set_video(self, video: VideoClip):
        """设置当前视频"""
        self.current_video = video
        
        if video:
            self.video_info_label.setText(f"{video.name} ({self._format_duration(video.duration)})")
            self.video_info_label.setStyleSheet("color: black;")
            
            # 自动生成项目名称
            if not self.project_name_edit.text():
                self.project_name_edit.setText(f"VideoEpic_{video.name}")
        else:
            self.video_info_label.setText("未选择视频")
            self.video_info_label.setStyleSheet("color: #666;")
    
    def set_ai_content(self, content: GeneratedContent):
        """设置AI生成的内容"""
        self.current_content = content
        self.create_ai_btn.setEnabled(True)
        
        # 更新项目类型
        if content.editing_mode == "commentary":
            self.project_type_combo.setCurrentText("AI解说项目")
        elif content.editing_mode == "compilation":
            self.project_type_combo.setCurrentText("AI混剪项目")
        elif content.editing_mode == "monologue":
            self.project_type_combo.setCurrentText("AI独白项目")
    
    def _format_duration(self, duration: float) -> str:
        """格式化时长"""
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _on_project_type_changed(self, project_type: str):
        """项目类型变更"""
        if project_type.startswith("AI") and not self.current_content:
            QMessageBox.information(self, "提示", "请先生成AI内容后再选择AI项目类型")
            self.project_type_combo.setCurrentText("基础视频项目")
    
    def _create_basic_project(self):
        """创建基础项目"""
        if not self.current_video:
            QMessageBox.warning(self, "警告", "请先选择一个视频文件")
            return
        
        # 获取项目设置
        project_name = self.project_name_edit.text() or f"VideoEpic_{self.current_video.name}"
        
        # 创建项目
        self.current_project = self.jianying_integration.create_project_from_video(
            self.current_video, project_name
        )
        
        # 应用设置
        self._apply_project_settings()
        
        # 更新UI
        self._update_project_info()
        
        QMessageBox.information(self, "成功", f"基础项目 '{project_name}' 创建成功")
    
    def _create_ai_project(self):
        """从AI内容创建项目"""
        if not self.current_content:
            QMessageBox.warning(self, "警告", "请先生成AI内容")
            return
        
        # 获取项目设置
        project_name = self.project_name_edit.text() or f"VideoEpic_AI_{self.current_content.editing_mode}"
        
        # 创建项目
        self.current_project = self.jianying_integration.create_project_from_content(
            self.current_content
        )
        self.current_project.name = project_name
        
        # 应用设置
        self._apply_project_settings()
        
        # 更新UI
        self._update_project_info()
        
        QMessageBox.information(self, "成功", f"AI项目 '{project_name}' 创建成功")
    
    def _apply_project_settings(self):
        """应用项目设置"""
        if not self.current_project:
            return
        
        # 视频质量设置
        quality_text = self.quality_combo.currentText()
        if "1080p" in quality_text:
            self.current_project.width = 1920
            self.current_project.height = 1080
        elif "720p" in quality_text:
            self.current_project.width = 1280
            self.current_project.height = 720
        elif "4K" in quality_text:
            self.current_project.width = 3840
            self.current_project.height = 2160
        
        # 帧率设置
        fps_text = self.fps_combo.currentText()
        if "30" in fps_text:
            self.current_project.fps = 30
        elif "60" in fps_text:
            self.current_project.fps = 60
        elif "24" in fps_text:
            self.current_project.fps = 24
    
    def _update_project_info(self):
        """更新项目信息"""
        if self.current_project:
            info = f"项目: {self.current_project.name}\n"
            info += f"分辨率: {self.current_project.width}x{self.current_project.height}\n"
            info += f"帧率: {self.current_project.fps} FPS\n"
            info += f"时长: {self._format_duration(self.current_project.duration)}"
            
            self.project_info_label.setText(info)
            self.project_info_label.setStyleSheet("color: black;")
            
            # 启用导出按钮
            self.export_btn.setEnabled(True)
        else:
            self.project_info_label.setText("无项目")
            self.project_info_label.setStyleSheet("color: #666;")
            self.export_btn.setEnabled(False)
    
    def _export_project(self):
        """导出项目"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "没有可导出的项目")
            return
        
        # 获取导出路径
        export_path = self.export_path_edit.text()
        if not export_path:
            export_path = QFileDialog.getExistingDirectory(self, "选择导出路径")
            if not export_path:
                return
            self.export_path_edit.setText(export_path)
        
        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        self.export_btn.setEnabled(False)
        
        try:
            # 导出项目
            project_path = self.jianying_integration.export_to_jianying(
                self.current_project, export_path
            )
            
            # 隐藏进度条
            self.progress_bar.setVisible(False)
            self.export_btn.setEnabled(True)
            
            # 启用打开按钮
            self.open_jianying_btn.setEnabled(True)
            self.exported_project_path = project_path
            
            QMessageBox.information(self, "成功", f"项目已导出到:\n{project_path}")
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.export_btn.setEnabled(True)
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
    
    def _open_in_jianying(self):
        """在剪映中打开项目"""
        if not hasattr(self, 'exported_project_path'):
            QMessageBox.warning(self, "警告", "请先导出项目")
            return
        
        if self.jianying_integration.open_in_jianying(self.exported_project_path):
            QMessageBox.information(self, "成功", "项目已在剪映中打开")
        else:
            QMessageBox.warning(self, "失败", "无法在剪映中打开项目")
    
    def _browse_export_path(self):
        """浏览导出路径"""
        path = QFileDialog.getExistingDirectory(self, "选择导出路径")
        if path:
            self.export_path_edit.setText(path)
    
    def _show_installation_guide(self):
        """显示安装指南"""
        guide = self.jianying_integration.get_installation_guide()
        
        message = f"{guide['title']}\n\n"
        for step in guide['steps']:
            message += f"{step}\n"
        message += f"\n下载地址: {guide['download_url']}"
        
        QMessageBox.information(self, "剪映安装指南", message)
    
    def _on_project_created(self, project_path: str):
        """项目创建完成回调"""
        self.project_exported.emit(project_path)
    
    def _on_export_completed(self, export_path: str):
        """导出完成回调"""
        pass
