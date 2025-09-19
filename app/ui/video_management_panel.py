#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFrame, QGroupBox, QFileDialog,
    QMessageBox, QMenu, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QFont, QPixmap, QDrag

from app.core.video_manager import VideoManager, VideoClip


class VideoUploadDialog(QDialog):
    """视频上传对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("添加视频")
        self.setModal(True)
        self.resize(500, 400)
        
        self.selected_files = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("选择要添加的视频文件")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 选择方式
        method_group = QGroupBox("选择方式")
        method_layout = QVBoxLayout(method_group)
        
        # 选择文件按钮
        file_btn_layout = QHBoxLayout()
        self.select_files_btn = QPushButton("选择视频文件")
        self.select_files_btn.clicked.connect(self._select_files)
        file_btn_layout.addWidget(self.select_files_btn)
        
        self.select_folder_btn = QPushButton("选择文件夹")
        self.select_folder_btn.clicked.connect(self._select_folder)
        file_btn_layout.addWidget(self.select_folder_btn)
        
        method_layout.addLayout(file_btn_layout)
        
        # 支持格式提示
        format_label = QLabel("支持格式: MP4, AVI, MOV, MKV, WMV, FLV")
        format_label.setStyleSheet("color: #666; font-size: 10px;")
        method_layout.addWidget(format_label)
        
        layout.addWidget(method_group)
        
        # 已选文件列表
        files_group = QGroupBox("已选择的文件")
        files_layout = QVBoxLayout(files_group)
        
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(150)
        files_layout.addWidget(self.files_list)
        
        # 清空按钮
        clear_btn = QPushButton("清空列表")
        clear_btn.clicked.connect(self._clear_files)
        files_layout.addWidget(clear_btn)
        
        layout.addWidget(files_group)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _select_files(self):
        """选择视频文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;所有文件 (*)"
        )
        
        if files:
            self._add_files(files)
    
    def _select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择包含视频的文件夹")
        
        if folder:
            # 扫描文件夹中的视频文件
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
            video_files = []
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in video_extensions):
                        video_files.append(os.path.join(root, file))
            
            if video_files:
                self._add_files(video_files)
            else:
                QMessageBox.information(self, "提示", "所选文件夹中没有找到视频文件")
    
    def _add_files(self, files):
        """添加文件到列表"""
        for file_path in files:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                
                # 添加到显示列表
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                item.setToolTip(file_path)
                self.files_list.addItem(item)
    
    def _clear_files(self):
        """清空文件列表"""
        self.selected_files.clear()
        self.files_list.clear()
    
    def get_selected_files(self):
        """获取选择的文件"""
        return self.selected_files


class VideoListWidget(QListWidget):
    """视频列表控件"""
    
    video_selected = pyqtSignal(VideoClip)
    video_edit_requested = pyqtSignal(VideoClip)
    video_delete_requested = pyqtSignal(str)  # video_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setDragDropMode(QListWidget.DragDropMode.DragOnly)
        
        # 连接信号
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # 设置上下文菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def add_video(self, video: VideoClip):
        """添加视频到列表"""
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, video)
        
        # 设置显示文本
        display_text = f"{video.name}\n"
        display_text += f"时长: {self._format_duration(video.duration)} | "
        display_text += f"大小: {self._format_file_size(video.file_size)}"
        
        item.setText(display_text)
        
        # 设置缩略图（如果有）
        if video.thumbnail_path and os.path.exists(video.thumbnail_path):
            pixmap = QPixmap(video.thumbnail_path)
            if not pixmap.isNull():
                item.setIcon(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        
        self.addItem(item)
    
    def _format_duration(self, duration: float) -> str:
        """格式化时长显示"""
        if duration <= 0:
            return "未知"
        
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _format_file_size(self, size: int) -> str:
        """格式化文件大小显示"""
        if size <= 0:
            return "未知"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _on_item_clicked(self, item):
        """视频点击"""
        video = item.data(Qt.ItemDataRole.UserRole)
        if video:
            self.video_selected.emit(video)
    
    def _on_item_double_clicked(self, item):
        """视频双击"""
        video = item.data(Qt.ItemDataRole.UserRole)
        if video:
            self.video_edit_requested.emit(video)
    
    def _show_context_menu(self, position):
        """显示上下文菜单"""
        item = self.itemAt(position)
        if not item:
            return
        
        video = item.data(Qt.ItemDataRole.UserRole)
        if not video:
            return
        
        menu = QMenu(self)
        
        edit_action = menu.addAction("编辑视频")
        edit_action.triggered.connect(lambda: self.video_edit_requested.emit(video))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("删除视频")
        delete_action.triggered.connect(lambda: self.video_delete_requested.emit(video.id))
        
        menu.exec(self.mapToGlobal(position))


class VideoManagementPanel(QWidget):
    """视频管理面板"""
    
    video_edit_requested = pyqtSignal(VideoClip)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.video_manager = VideoManager()
        self.current_video = None
        
        self._setup_ui()
        self._connect_signals()
        self._load_videos()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("视频管理")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.add_video_btn = QPushButton("添加视频")
        self.add_video_btn.clicked.connect(self._add_videos)
        button_layout.addWidget(self.add_video_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._load_videos)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # 视频列表
        list_group = QGroupBox("视频列表")
        list_layout = QVBoxLayout(list_group)
        
        self.video_list = VideoListWidget()
        list_layout.addWidget(self.video_list)
        
        # 视频操作按钮
        video_action_layout = QHBoxLayout()
        
        self.edit_video_btn = QPushButton("编辑视频")
        self.edit_video_btn.setEnabled(False)
        self.edit_video_btn.clicked.connect(self._edit_selected_video)
        video_action_layout.addWidget(self.edit_video_btn)
        
        self.delete_video_btn = QPushButton("删除视频")
        self.delete_video_btn.setEnabled(False)
        self.delete_video_btn.clicked.connect(self._delete_selected_video)
        video_action_layout.addWidget(self.delete_video_btn)
        
        list_layout.addLayout(video_action_layout)
        
        layout.addWidget(list_group)
    
    def _connect_signals(self):
        """连接信号"""
        self.video_list.video_selected.connect(self._on_video_selected)
        self.video_list.video_edit_requested.connect(self._on_video_edit_requested)
        self.video_list.video_delete_requested.connect(self._on_video_delete_requested)
    
    def _load_videos(self):
        """加载视频列表"""
        self.video_list.clear()
        
        videos = self.video_manager.get_all_videos()
        for video in videos:
            self.video_list.add_video(video)
    
    def _add_videos(self):
        """添加视频"""
        dialog = VideoUploadDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            files = dialog.get_selected_files()
            if files:
                # 添加视频文件
                added_count = 0
                for file_path in files:
                    if self.video_manager.add_video(file_path):
                        added_count += 1
                
                if added_count > 0:
                    QMessageBox.information(self, "成功", f"成功添加 {added_count} 个视频文件")
                    self._load_videos()
                else:
                    QMessageBox.warning(self, "失败", "没有成功添加任何视频文件")
    
    def _on_video_selected(self, video: VideoClip):
        """视频选中"""
        self.current_video = video
        self.edit_video_btn.setEnabled(True)
        self.delete_video_btn.setEnabled(True)
    
    def _on_video_edit_requested(self, video: VideoClip):
        """编辑视频请求"""
        self.video_edit_requested.emit(video)
    
    def _on_video_delete_requested(self, video_id: str):
        """删除视频请求"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个视频吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.video_manager.remove_video(video_id):
                QMessageBox.information(self, "成功", "视频删除成功")
                self._load_videos()
            else:
                QMessageBox.warning(self, "失败", "视频删除失败")
    
    def _edit_selected_video(self):
        """编辑选中的视频"""
        if self.current_video:
            self.video_edit_requested.emit(self.current_video)
    
    def _delete_selected_video(self):
        """删除选中的视频"""
        if self.current_video:
            self._on_video_delete_requested(self.current_video.id)
