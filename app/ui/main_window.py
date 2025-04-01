#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, 
    QListWidget, QListWidgetItem, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QSize, QFileInfo, QUrl, QMimeData
from PyQt6.QtGui import QAction, QIcon, QPixmap, QDrag, QDropEvent

from app.ui.video_player import VideoPlayer
from app.ui.timeline_widget import TimelineWidget
from app.ui.ai_panel import AIPanel
from app.core.video_manager import VideoManager


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("VideoEpicCreator")
        self.setGeometry(100, 100, 1280, 720)
        self.setAcceptDrops(True)  # 启用拖放
        
        # 创建视频管理器
        self.video_manager = VideoManager()
        self.video_manager.video_added.connect(self._on_video_added)
        self.video_manager.video_removed.connect(self._on_video_removed)
        self.video_manager.thumbnail_generated.connect(self._on_thumbnail_updated)
        self.video_manager.metadata_updated.connect(self._on_metadata_updated)
        
        # 创建UI组件
        self._create_actions()
        self._create_toolbars()
        self._create_central_widget()
        self._create_statusbar()
        self._create_context_menus()
        
        # 设置样式
        self._setup_styles()
    
    def _create_actions(self):
        """创建菜单和工具栏操作"""
        # 文件操作
        self.new_action = QAction(QIcon("resources/icons/new.png"), "新建项目", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self._on_new_project)
        
        self.open_action = QAction(QIcon("resources/icons/open.png"), "打开项目", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self._on_open_project)
        
        self.save_action = QAction(QIcon("resources/icons/save.png"), "保存项目", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self._on_save_project)
        
        self.export_action = QAction(QIcon("resources/icons/export.png"), "导出到剪映", self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.triggered.connect(self._on_export_project)
        
        # 视频操作
        self.import_action = QAction(QIcon(), "导入视频", self)
        self.import_action.setShortcut("Ctrl+I")
        self.import_action.triggered.connect(self._on_import_video)
        
        self.batch_import_action = QAction(QIcon(), "批量导入", self)
        self.batch_import_action.triggered.connect(self._on_batch_import)
        
        # 设置操作
        self.settings_action = QAction(QIcon("resources/icons/settings.png"), "设置", self)
        self.settings_action.setShortcut("Ctrl+,")
        self.settings_action.triggered.connect(self._on_settings)
    
    def _create_toolbars(self):
        """创建工具栏"""
        # 主工具栏
        self.main_toolbar = QToolBar("主工具栏", self)
        self.main_toolbar.setIconSize(QSize(32, 32))
        self.main_toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_toolbar)
        
        self.main_toolbar.addAction(self.new_action)
        self.main_toolbar.addAction(self.open_action)
        self.main_toolbar.addAction(self.save_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.export_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.settings_action)
    
    def _create_central_widget(self):
        """创建中央窗口部件"""
        # 创建主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建上下分隔面板
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(self.main_splitter)
        
        # 创建上半部分的左右分隔面板
        self.top_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(self.top_splitter)
        
        # 左侧区域 - 视频库
        self.video_library = QWidget()
        self.video_library_layout = QVBoxLayout(self.video_library)
        self.video_library_layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频列表
        self.video_list = QListWidget()
        self.video_list.setIconSize(QSize(120, 67))  # 16:9比例的缩略图
        self.video_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.video_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.video_list.setMovement(QListWidget.Movement.Static)
        self.video_list.setGridSize(QSize(150, 120))
        self.video_list.setSpacing(10)
        self.video_list.setDragEnabled(True)  # 允许从列表中拖出项目
        self.video_list.itemDoubleClicked.connect(self._on_video_double_clicked)
        self.video_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.video_list.customContextMenuRequested.connect(self._show_video_context_menu)
        
        self.video_library_layout.addWidget(self.video_list)
        self.top_splitter.addWidget(self.video_library)
        
        # 中间区域 - 视频播放器
        self.video_player = VideoPlayer()
        self.top_splitter.addWidget(self.video_player)
        
        # 右侧区域 - AI面板
        self.ai_panel = AIPanel()
        self.top_splitter.addWidget(self.ai_panel)
        
        # 设置顶部分隔面板的初始大小比例
        self.top_splitter.setSizes([250, 600, 250])
        
        # 下半部分 - 时间线
        self.timeline = TimelineWidget()
        self.main_splitter.addWidget(self.timeline)
        
        # 设置主分隔面板的初始大小比例
        self.main_splitter.setSizes([400, 300])
    
    def _create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")
    
    def _create_context_menus(self):
        """创建上下文菜单"""
        # 视频列表上下文菜单
        self.video_context_menu = QMenu(self)
        self.video_context_menu.addAction("播放", self._play_selected_video)
        self.video_context_menu.addAction("添加到时间线", self._add_to_timeline)
        self.video_context_menu.addSeparator()
        self.video_context_menu.addAction("从列表中移除", self._remove_from_list)
        self.video_context_menu.addSeparator()
        self.video_context_menu.addAction("刷新缩略图", self._refresh_thumbnail)
        self.video_context_menu.addAction("刷新元数据", self._refresh_metadata)
    
    def _setup_styles(self):
        """设置样式"""
        # 使视频列表项的选中状态更明显
        self.video_list.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #3a7eff;
                border-radius: 5px;
            }
            QListWidget::item:hover {
                background-color: #eaeaea;
                border-radius: 5px;
            }
        """)
    
    def _on_new_project(self):
        """新建项目"""
        # 询问是否保存当前项目
        if self.video_manager.timeline_clips:
            reply = QMessageBox.question(
                self, "新建项目", "是否保存当前项目?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._on_save_project()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        # 清空当前项目
        self.video_list.clear()
        self.video_manager.videos.clear()
        self.video_manager.timeline_clips.clear()
        self.timeline.clear()
        self.video_manager.project_path = None
        self.statusbar.showMessage("已创建新项目")
    
    def _on_open_project(self):
        """打开项目"""
        # 询问是否保存当前项目
        if self.video_manager.timeline_clips:
            reply = QMessageBox.question(
                self, "打开项目", "是否保存当前项目?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._on_save_project()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        # 选择项目文件
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("VideoEpicCreator项目文件 (*.vec)")
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            success = self.video_manager.load_project(file_path)
            
            if success:
                # 更新UI
                self.video_list.clear()
                self.timeline.clear()
                
                # 加载视频列表
                for clip in self.video_manager.videos:
                    self._add_video_to_list(clip)
                
                # TODO: 加载时间线
                
                self.statusbar.showMessage(f"已打开项目: {file_path}")
            else:
                QMessageBox.warning(self, "打开失败", f"无法打开项目文件: {file_path}")
    
    def _on_save_project(self):
        """保存项目"""
        if not self.video_manager.project_path:
            # 未保存过，显示保存对话框
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("VideoEpicCreator项目文件 (*.vec)")
            file_dialog.setDefaultSuffix("vec")
            
            if file_dialog.exec():
                file_path = file_dialog.selectedFiles()[0]
                success = self.video_manager.save_project(file_path)
                
                if success:
                    self.statusbar.showMessage(f"项目已保存: {file_path}")
                else:
                    QMessageBox.warning(self, "保存失败", f"无法保存项目: {file_path}")
        else:
            # 已有保存路径，直接保存
            success = self.video_manager.save_project(self.video_manager.project_path)
            
            if success:
                self.statusbar.showMessage(f"项目已保存: {self.video_manager.project_path}")
            else:
                QMessageBox.warning(
                    self, "保存失败", 
                    f"无法保存项目: {self.video_manager.project_path}"
                )
    
    def _on_export_project(self):
        """导出项目到剪映"""
        # 选择导出位置
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if file_dialog.exec():
            export_dir = file_dialog.selectedFiles()[0]
            success = self.video_manager.export_to_jianying(export_dir)
            
            if success:
                QMessageBox.information(
                    self, "导出成功", 
                    f"项目已导出为剪映格式到: {export_dir}"
                )
            else:
                QMessageBox.warning(
                    self, "导出失败", 
                    "导出剪映格式失败，请查看日志。"
                )
    
    def _on_import_video(self):
        """导入视频"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm)")
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            self._import_video_files(file_paths)
    
    def _on_batch_import(self):
        """批量导入视频"""
        folder_dialog = QFileDialog(self)
        folder_dialog.setFileMode(QFileDialog.FileMode.Directory)
        folder_dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if folder_dialog.exec():
            folder_path = folder_dialog.selectedFiles()[0]
            self._import_videos_from_folder(folder_path)
    
    def _on_settings(self):
        """打开设置对话框"""
        # TODO: 实现设置对话框
        self.statusbar.showMessage("设置功能尚未实现")
    
    def _import_video_files(self, file_paths):
        """导入视频文件"""
        added_clips = self.video_manager.add_videos_batch(file_paths)
        
        if added_clips:
            self.statusbar.showMessage(f"已导入 {len(added_clips)} 个视频文件")
        else:
            self.statusbar.showMessage("没有导入任何视频文件")
    
    def _import_videos_from_folder(self, folder_path):
        """从文件夹导入视频"""
        # 查找视频文件
        video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"]
        video_files = []
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in video_extensions:
                    video_files.append(os.path.join(root, file))
        
        # 导入视频
        if video_files:
            self._import_video_files(video_files)
        else:
            self.statusbar.showMessage(f"在文件夹中未找到视频文件: {folder_path}")
    
    def _add_video_to_list(self, clip):
        """将视频添加到列表中"""
        item = QListWidgetItem(self.video_list)
        
        # 设置缩略图
        if clip.thumbnail and os.path.exists(clip.thumbnail):
            pixmap = QPixmap(clip.thumbnail)
            item.setIcon(QIcon(pixmap))
        else:
            # 使用默认图标
            item.setIcon(QIcon())
        
        # 设置视频信息
        duration_str = self._format_duration(clip.duration)
        
        # 从元数据获取分辨率
        resolution = ""
        if "width" in clip.metadata and "height" in clip.metadata:
            resolution = f"{clip.metadata['width']}x{clip.metadata['height']}"
        
        # 设置文本为视频名称和时长
        display_text = f"{clip.name}\n{duration_str}"
        if resolution:
            display_text += f" | {resolution}"
        
        item.setText(display_text)
        item.setData(Qt.ItemDataRole.UserRole, clip.clip_id)  # 存储剪辑ID用于引用
        
        # 添加提示信息（更详细的元数据）
        tooltip = f"文件: {clip.file_path}\n时长: {duration_str}"
        
        for key, value in clip.metadata.items():
            if key not in ["duration", "width", "height"]:  # 这些已经显示了
                tooltip += f"\n{key}: {value}"
                
        item.setToolTip(tooltip)
        
        self.video_list.addItem(item)
    
    def _on_video_added(self, clip):
        """视频添加回调"""
        self._add_video_to_list(clip)
    
    def _on_video_removed(self, index):
        """视频移除回调"""
        self.video_list.takeItem(index)
    
    def _on_thumbnail_updated(self, clip):
        """缩略图更新回调"""
        # 查找对应的列表项并更新缩略图
        for i in range(self.video_list.count()):
            item = self.video_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == clip.clip_id:
                if clip.thumbnail and os.path.exists(clip.thumbnail):
                    pixmap = QPixmap(clip.thumbnail)
                    item.setIcon(QIcon(pixmap))
                break
    
    def _on_metadata_updated(self, clip):
        """元数据更新回调"""
        # 查找对应的列表项并更新信息
        for i in range(self.video_list.count()):
            item = self.video_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == clip.clip_id:
                # 更新显示文本
                duration_str = self._format_duration(clip.duration)
                
                resolution = ""
                if "width" in clip.metadata and "height" in clip.metadata:
                    resolution = f"{clip.metadata['width']}x{clip.metadata['height']}"
                
                display_text = f"{clip.name}\n{duration_str}"
                if resolution:
                    display_text += f" | {resolution}"
                
                item.setText(display_text)
                
                # 更新提示信息
                tooltip = f"文件: {clip.file_path}\n时长: {duration_str}"
                
                for key, value in clip.metadata.items():
                    if key not in ["duration", "width", "height"]:
                        tooltip += f"\n{key}: {value}"
                        
                item.setToolTip(tooltip)
                break
    
    def _on_video_double_clicked(self, item):
        """视频列表项双击回调"""
        clip_id = item.data(Qt.ItemDataRole.UserRole)
        clip = self.video_manager.find_video_by_id(clip_id)
        
        if clip:
            # 在播放器中播放视频
            self.video_player.load_video(clip.file_path)
            self.video_player.play()
    
    def _show_video_context_menu(self, position):
        """显示视频列表的上下文菜单"""
        # 确保有选中的项
        if self.video_list.currentItem():
            self.video_context_menu.exec(self.video_list.mapToGlobal(position))
    
    def _play_selected_video(self):
        """播放选中的视频"""
        item = self.video_list.currentItem()
        if item:
            clip_id = item.data(Qt.ItemDataRole.UserRole)
            clip = self.video_manager.find_video_by_id(clip_id)
            
            if clip:
                self.video_player.load_video(clip.file_path)
                self.video_player.play()
    
    def _add_to_timeline(self):
        """将选中的视频添加到时间线"""
        item = self.video_list.currentItem()
        if item:
            clip_id = item.data(Qt.ItemDataRole.UserRole)
            clip = self.video_manager.find_video_by_id(clip_id)
            
            if clip:
                # 添加到时间线
                # TODO: 实现时间线添加逻辑
                timeline_clip = self.video_manager.add_to_timeline(clip)
                self.statusbar.showMessage(f"视频已添加到时间线: {clip.name}")
    
    def _remove_from_list(self):
        """从列表中移除选中的视频"""
        item = self.video_list.currentItem()
        if item:
            clip_id = item.data(Qt.ItemDataRole.UserRole)
            
            # 找到视频索引
            index = -1
            for i, clip in enumerate(self.video_manager.videos):
                if clip.clip_id == clip_id:
                    index = i
                    break
            
            if index >= 0:
                # 询问确认
                reply = QMessageBox.question(
                    self, "移除视频", 
                    f"确定要从列表中移除视频 '{self.video_manager.videos[index].name}' 吗?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.video_manager.remove_video(index)
                    self.statusbar.showMessage("视频已从列表中移除")
    
    def _refresh_thumbnail(self):
        """刷新选中视频的缩略图"""
        item = self.video_list.currentItem()
        if item:
            clip_id = item.data(Qt.ItemDataRole.UserRole)
            clip = self.video_manager.find_video_by_id(clip_id)
            
            if clip:
                # 重新生成缩略图
                self.video_manager._generate_thumbnail(clip)
                self.statusbar.showMessage(f"正在刷新缩略图: {clip.name}")
    
    def _refresh_metadata(self):
        """刷新选中视频的元数据"""
        item = self.video_list.currentItem()
        if item:
            clip_id = item.data(Qt.ItemDataRole.UserRole)
            clip = self.video_manager.find_video_by_id(clip_id)
            
            if clip:
                # 重新提取元数据
                self.video_manager.refresh_metadata(clip)
                self.statusbar.showMessage(f"正在刷新元数据: {clip.name}")
    
    def _format_duration(self, duration_ms):
        """格式化时长（毫秒转为时:分:秒）"""
        if not duration_ms:
            return "未知时长"
        
        # 转换为秒
        total_seconds = int(duration_ms / 1000)
        
        # 计算时、分、秒
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        # 格式化
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def dragEnterEvent(self, event):
        """拖动进入事件"""
        mime_data = event.mimeData()
        
        # 检查是否包含URL（文件路径）
        if mime_data.hasUrls():
            # 检查是否为视频文件
            has_video = False
            video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"]
            
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                
                if ext in video_extensions:
                    has_video = True
                    break
            
            if has_video:
                event.acceptProposedAction()
                return
        
        event.ignore()
    
    def dropEvent(self, event):
        """拖放事件"""
        mime_data = event.mimeData()
        
        if mime_data.hasUrls():
            # 获取有效的视频文件
            video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"]
            video_files = []
            
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                
                if ext in video_extensions:
                    video_files.append(file_path)
            
            if video_files:
                self._import_video_files(video_files)
                event.acceptProposedAction()
                return
        
        event.ignore() 