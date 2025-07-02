#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QFileDialog, QMessageBox,
    QComboBox, QLineEdit, QCheckBox, QProgressBar, QMenu,
    QSizePolicy, QSpacerItem, QTabWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QIcon, QMovie, QPainter, QBrush, QColor

from app.core.video_manager import VideoManager, VideoClip
from app.core.project_manager import ProjectManager, ProjectInfo
from .theme_manager import get_theme_manager
import os
from pathlib import Path


class VideoCard(QFrame):
    """视频卡片组件"""
    
    # 信号
    video_selected = pyqtSignal(VideoClip)
    video_edit_requested = pyqtSignal(VideoClip)
    video_delete_requested = pyqtSignal(VideoClip)
    
    def __init__(self, video: VideoClip, parent=None):
        super().__init__(parent)
        
        self.video = video
        self.is_selected = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        self.setFixedSize(200, 280)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 缩略图区域
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(176, 100)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
            }
        """)
        
        # 加载缩略图
        self._load_thumbnail()
        layout.addWidget(self.thumbnail_label)
        
        # 视频信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # 视频名称
        self.name_label = QLabel(self.video.name)
        self.name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.name_label.setObjectName("video_name")
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(40)
        info_layout.addWidget(self.name_label)
        
        # 视频详情
        details_text = f"时长: {self._format_duration(self.video.duration)}\n"
        details_text += f"大小: {self._format_file_size(self.video.file_size)}"
        
        self.details_label = QLabel(details_text)
        self.details_label.setFont(QFont("Arial", 10))
        self.details_label.setObjectName("video_details")
        info_layout.addWidget(self.details_label)
        
        layout.addLayout(info_layout)
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)
        
        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setMaximumSize(30, 30)
        self.edit_btn.setToolTip("编辑视频")
        self.edit_btn.clicked.connect(lambda: self.video_edit_requested.emit(self.video))
        buttons_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setMaximumSize(30, 30)
        self.delete_btn.setToolTip("删除视频")
        self.delete_btn.clicked.connect(lambda: self.video_delete_requested.emit(self.video))
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # 设置上下文菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _load_thumbnail(self):
        """加载缩略图"""
        if self.video.thumbnail_path and os.path.exists(self.video.thumbnail_path):
            pixmap = QPixmap(self.video.thumbnail_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    176, 100, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(scaled_pixmap)
            else:
                self._set_placeholder_thumbnail()
        else:
            self._set_placeholder_thumbnail()
    
    def _set_placeholder_thumbnail(self):
        """设置占位符缩略图"""
        self.thumbnail_label.setText("🎬\n视频预览")
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                color: #bfbfbf;
                font-size: 14px;
            }
        """)
    
    def _format_duration(self, duration_ms: int) -> str:
        """格式化时长"""
        if duration_ms <= 0:
            return "未知"
        
        seconds = duration_ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes <= 0:
            return "未知"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            VideoCard {
                background-color: #ffffff;
                border: 1px solid #f0f0f0;
                border-radius: 8px;
            }
            
            VideoCard:hover {
                border-color: #1890ff;
                background-color: #f0f9ff;
            }
            
            QLabel#video_name {
                color: #262626;
                font-weight: 600;
            }
            
            QLabel#video_details {
                color: #595959;
                line-height: 1.4;
            }
            
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 12px;
            }
            
            QPushButton:hover {
                background-color: #e6f7ff;
                border-color: #1890ff;
            }
        """)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                VideoCard {
                    background-color: #e6f7ff;
                    border: 2px solid #1890ff;
                    border-radius: 8px;
                }
                
                QLabel#video_name {
                    color: #1890ff;
                    font-weight: 600;
                }
                
                QLabel#video_details {
                    color: #595959;
                }
            """)
        else:
            self._apply_styles()
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.video_selected.emit(self.video)
        super().mousePressEvent(event)
    
    def _show_context_menu(self, position):
        """显示上下文菜单"""
        menu = QMenu(self)
        
        edit_action = menu.addAction("✏️ 编辑视频")
        edit_action.triggered.connect(lambda: self.video_edit_requested.emit(self.video))
        
        menu.addSeparator()
        
        info_action = menu.addAction("ℹ️ 视频信息")
        info_action.triggered.connect(self._show_video_info)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ 删除视频")
        delete_action.triggered.connect(lambda: self.video_delete_requested.emit(self.video))
        
        menu.exec(self.mapToGlobal(position))
    
    def _show_video_info(self):
        """显示视频信息"""
        info_text = f"""视频信息:

文件名: {self.video.name}
文件路径: {self.video.file_path}
文件大小: {self._format_file_size(self.video.file_size)}
视频时长: {self._format_duration(self.video.duration)}
分辨率: {self.video.width} x {self.video.height}
帧率: {self.video.fps} fps
创建时间: {self.video.created_at}"""
        
        QMessageBox.information(self, "视频信息", info_text)


class ProjectCard(QFrame):
    """项目卡片组件"""
    
    # 信号
    project_selected = pyqtSignal(ProjectInfo)
    project_edit_requested = pyqtSignal(ProjectInfo)
    project_delete_requested = pyqtSignal(ProjectInfo)
    
    def __init__(self, project: ProjectInfo, parent=None):
        super().__init__(parent)
        
        self.project = project
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        self.setFixedSize(280, 160)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # 项目标题
        title_layout = QHBoxLayout()
        
        # 项目类型图标
        mode_icons = {
            "commentary": "🎬",
            "compilation": "⚡",
            "monologue": "🎭"
        }
        icon = mode_icons.get(self.project.editing_mode, "📁")
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 20))
        title_layout.addWidget(icon_label)
        
        # 项目名称
        name_label = QLabel(self.project.name)
        name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        name_label.setObjectName("project_name")
        name_label.setWordWrap(True)
        title_layout.addWidget(name_label)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 项目描述
        if self.project.description:
            desc_label = QLabel(self.project.description)
            desc_label.setFont(QFont("Arial", 11))
            desc_label.setObjectName("project_description")
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(40)
            layout.addWidget(desc_label)
        
        # 项目统计
        stats_layout = QHBoxLayout()
        
        # 视频数量
        video_count_label = QLabel(f"📹 {self.project.video_count}")
        video_count_label.setFont(QFont("Arial", 10))
        stats_layout.addWidget(video_count_label)
        
        # 总时长
        duration_text = self._format_duration(self.project.duration)
        duration_label = QLabel(f"⏱️ {duration_text}")
        duration_label.setFont(QFont("Arial", 10))
        stats_layout.addWidget(duration_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # 修改时间
        from datetime import datetime
        try:
            modified_time = datetime.fromisoformat(self.project.modified_at)
            time_text = modified_time.strftime("%Y-%m-%d %H:%M")
        except:
            time_text = "未知"
        
        time_label = QLabel(f"修改: {time_text}")
        time_label.setFont(QFont("Arial", 9))
        time_label.setObjectName("project_time")
        layout.addWidget(time_label)
        
        # 设置上下文菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _format_duration(self, duration_seconds: float) -> str:
        """格式化时长"""
        if duration_seconds <= 0:
            return "0:00"
        
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            ProjectCard {
                background-color: #ffffff;
                border: 1px solid #f0f0f0;
                border-radius: 12px;
            }
            
            ProjectCard:hover {
                border-color: #1890ff;
                background-color: #f0f9ff;
            }
            
            QLabel#project_name {
                color: #262626;
                font-weight: 600;
            }
            
            QLabel#project_description {
                color: #595959;
                line-height: 1.3;
            }
            
            QLabel#project_time {
                color: #8c8c8c;
            }
        """)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.project_selected.emit(self.project)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.project_edit_requested.emit(self.project)
        super().mouseDoubleClickEvent(event)
    
    def _show_context_menu(self, position):
        """显示上下文菜单"""
        menu = QMenu(self)
        
        open_action = menu.addAction("📂 打开项目")
        open_action.triggered.connect(lambda: self.project_edit_requested.emit(self.project))
        
        menu.addSeparator()
        
        rename_action = menu.addAction("✏️ 重命名")
        # TODO: 实现重命名功能
        
        duplicate_action = menu.addAction("📋 复制项目")
        # TODO: 实现复制功能
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ 删除项目")
        delete_action.triggered.connect(lambda: self.project_delete_requested.emit(self.project))
        
        menu.exec(self.mapToGlobal(position))


class ModernVideoManagement(QWidget):
    """现代化视频管理面板"""

    # 信号
    video_edit_requested = pyqtSignal(VideoClip)
    project_edit_requested = pyqtSignal(ProjectInfo)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.video_manager = VideoManager()
        self.project_manager = ProjectManager()
        self.theme_manager = get_theme_manager()

        self.selected_video = None
        self.selected_project = None
        self.video_cards = []
        self.project_cards = []

        self._setup_ui()
        self._connect_signals()
        self._load_data()
        self._apply_theme()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # 视频管理选项卡
        self.video_tab = self._create_video_tab()
        self.tab_widget.addTab(self.video_tab, "📹 视频库")

        # 项目管理选项卡
        self.project_tab = self._create_project_tab()
        self.tab_widget.addTab(self.project_tab, "📁 项目管理")

        layout.addWidget(self.tab_widget)

        # 应用样式
        self._apply_tab_styles()

    def _create_video_tab(self) -> QWidget:
        """创建视频管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 标题和工具栏
        header_layout = QHBoxLayout()

        title_label = QLabel("视频库")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setObjectName("section_title")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 搜索框
        self.video_search = QLineEdit()
        self.video_search.setPlaceholderText("搜索视频...")
        self.video_search.setMaximumWidth(200)
        self.video_search.textChanged.connect(self._filter_videos)
        header_layout.addWidget(self.video_search)

        layout.addLayout(header_layout)

        # 操作按钮
        actions_layout = QHBoxLayout()

        self.add_video_btn = QPushButton("📁 添加视频")
        self.add_video_btn.setObjectName("primary_button")
        self.add_video_btn.setMinimumHeight(40)
        self.add_video_btn.clicked.connect(self._add_videos)
        actions_layout.addWidget(self.add_video_btn)

        self.add_folder_btn = QPushButton("📂 添加文件夹")
        self.add_folder_btn.setMinimumHeight(40)
        self.add_folder_btn.clicked.connect(self._add_video_folder)
        actions_layout.addWidget(self.add_folder_btn)

        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.clicked.connect(self._refresh_videos)
        actions_layout.addWidget(self.refresh_btn)

        actions_layout.addStretch()

        layout.addLayout(actions_layout)

        # 视频网格容器
        self.video_scroll = QScrollArea()
        self.video_scroll.setWidgetResizable(True)
        self.video_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.video_container = QWidget()
        self.video_grid = QGridLayout(self.video_container)
        self.video_grid.setSpacing(16)
        self.video_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.video_scroll.setWidget(self.video_container)
        layout.addWidget(self.video_scroll)

        return tab

    def _create_project_tab(self) -> QWidget:
        """创建项目管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 标题和工具栏
        header_layout = QHBoxLayout()

        title_label = QLabel("项目管理")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setObjectName("section_title")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 项目搜索
        self.project_search = QLineEdit()
        self.project_search.setPlaceholderText("搜索项目...")
        self.project_search.setMaximumWidth(200)
        self.project_search.textChanged.connect(self._filter_projects)
        header_layout.addWidget(self.project_search)

        layout.addLayout(header_layout)

        # 操作按钮
        actions_layout = QHBoxLayout()

        self.new_project_btn = QPushButton("📝 新建项目")
        self.new_project_btn.setObjectName("primary_button")
        self.new_project_btn.setMinimumHeight(40)
        self.new_project_btn.clicked.connect(self._create_new_project)
        actions_layout.addWidget(self.new_project_btn)

        self.import_project_btn = QPushButton("📥 导入项目")
        self.import_project_btn.setMinimumHeight(40)
        self.import_project_btn.clicked.connect(self._import_project)
        actions_layout.addWidget(self.import_project_btn)

        actions_layout.addStretch()

        layout.addLayout(actions_layout)

        # 项目网格容器
        self.project_scroll = QScrollArea()
        self.project_scroll.setWidgetResizable(True)
        self.project_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.project_container = QWidget()
        self.project_grid = QGridLayout(self.project_container)
        self.project_grid.setSpacing(16)
        self.project_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.project_scroll.setWidget(self.project_container)
        layout.addWidget(self.project_scroll)

        return tab

    def _apply_tab_styles(self):
        """应用选项卡样式"""
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #f0f0f0;
                background-color: #ffffff;
                border-radius: 6px;
            }

            QTabBar::tab {
                background-color: #fafafa;
                border: 1px solid #f0f0f0;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 12px 20px;
                margin-right: 2px;
                color: #595959;
                font-weight: 500;
                font-size: 14px;
            }

            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1890ff;
                border-color: #1890ff;
                border-bottom: 2px solid #1890ff;
                font-weight: 600;
            }

            QTabBar::tab:hover:!selected {
                background-color: #f5f5f5;
                color: #262626;
            }
        """)

    def _connect_signals(self):
        """连接信号"""
        # 视频管理器信号
        self.video_manager.video_added.connect(self._on_video_added)
        self.video_manager.video_removed.connect(self._on_video_removed)

        # 项目管理器信号
        self.project_manager.project_created.connect(self._on_project_created)
        self.project_manager.project_loaded.connect(self._on_project_loaded)

        # 主题管理器信号
        self.theme_manager.theme_changed.connect(self._on_theme_changed)

    def _load_data(self):
        """加载数据"""
        self._refresh_videos()
        self._refresh_projects()

    def _refresh_videos(self):
        """刷新视频列表"""
        # 清空现有卡片
        for card in self.video_cards:
            card.setParent(None)
        self.video_cards.clear()

        # 加载视频
        videos = self.video_manager.get_all_videos()

        # 创建视频卡片
        for i, video in enumerate(videos):
            card = VideoCard(video)
            card.video_selected.connect(self._on_video_selected)
            card.video_edit_requested.connect(self.video_edit_requested.emit)
            card.video_delete_requested.connect(self._on_video_delete_requested)

            self.video_cards.append(card)

            # 添加到网格布局
            row = i // 4  # 每行4个卡片
            col = i % 4
            self.video_grid.addWidget(card, row, col)

    def _refresh_projects(self):
        """刷新项目列表"""
        # 清空现有卡片
        for card in self.project_cards:
            card.setParent(None)
        self.project_cards.clear()

        # 加载项目
        projects = self.project_manager.get_project_list()

        # 按修改时间排序
        projects.sort(key=lambda p: p.modified_at, reverse=True)

        # 创建项目卡片
        for i, project in enumerate(projects):
            card = ProjectCard(project)
            card.project_selected.connect(self._on_project_selected)
            card.project_edit_requested.connect(self.project_edit_requested.emit)
            card.project_delete_requested.connect(self._on_project_delete_requested)

            self.project_cards.append(card)

            # 添加到网格布局
            row = i // 3  # 每行3个卡片
            col = i % 3
            self.project_grid.addWidget(card, row, col)

    def _add_videos(self):
        """添加视频文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;所有文件 (*)"
        )

        if files:
            added_count = 0
            for file_path in files:
                if self.video_manager.add_video(file_path):
                    added_count += 1

            if added_count > 0:
                QMessageBox.information(self, "成功", f"成功添加 {added_count} 个视频文件")
                self._refresh_videos()
            else:
                QMessageBox.warning(self, "失败", "没有成功添加任何视频文件")

    def _add_video_folder(self):
        """添加视频文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择包含视频的文件夹")

        if folder:
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
            video_files = []

            for root, dirs, files in os.walk(folder):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in video_extensions):
                        video_files.append(os.path.join(root, file))

            if video_files:
                added_count = 0
                for file_path in video_files:
                    if self.video_manager.add_video(file_path):
                        added_count += 1

                if added_count > 0:
                    QMessageBox.information(self, "成功", f"从文件夹中添加了 {added_count} 个视频文件")
                    self._refresh_videos()
                else:
                    QMessageBox.warning(self, "失败", "没有成功添加任何视频文件")
            else:
                QMessageBox.information(self, "提示", "所选文件夹中没有找到视频文件")

    def _create_new_project(self):
        """创建新项目"""
        # 这里可以添加项目创建对话框
        project_name = f"新项目 {len(self.project_manager.get_project_list()) + 1}"
        project = self.project_manager.create_project(project_name, "新创建的项目")

        if project:
            QMessageBox.information(self, "成功", f"项目 '{project_name}' 创建成功")
            self._refresh_projects()

    def _import_project(self):
        """导入项目"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入项目", "", "项目文件 (*.vecp);;所有文件 (*)"
        )

        if file_path:
            if self.project_manager.load_project(file_path):
                QMessageBox.information(self, "成功", "项目导入成功")
                self._refresh_projects()
            else:
                QMessageBox.critical(self, "错误", "项目导入失败")

    def _filter_videos(self, text):
        """过滤视频"""
        for card in self.video_cards:
            visible = text.lower() in card.video.name.lower()
            card.setVisible(visible)

    def _filter_projects(self, text):
        """过滤项目"""
        for card in self.project_cards:
            visible = text.lower() in card.project.name.lower()
            card.setVisible(visible)

    def _on_video_selected(self, video):
        """视频选中事件"""
        # 取消其他视频的选中状态
        for card in self.video_cards:
            card.set_selected(card.video == video)

        self.selected_video = video

    def _on_project_selected(self, project):
        """项目选中事件"""
        self.selected_project = project

    def _on_video_delete_requested(self, video):
        """删除视频请求"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除视频 '{video.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.video_manager.remove_video_by_id(video.id):
                QMessageBox.information(self, "成功", "视频删除成功")
                self._refresh_videos()
            else:
                QMessageBox.warning(self, "失败", "视频删除失败")

    def _on_project_delete_requested(self, project):
        """删除项目请求"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除项目 '{project.name}' 吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.project_manager.delete_project(project.id):
                QMessageBox.information(self, "成功", "项目删除成功")
                self._refresh_projects()
            else:
                QMessageBox.warning(self, "失败", "项目删除失败")

    def _on_video_added(self, video):
        """视频添加事件"""
        self._refresh_videos()

    def _on_video_removed(self, index):
        """视频移除事件"""
        self._refresh_videos()

    def _on_project_created(self, project):
        """项目创建事件"""
        self._refresh_projects()

    def _on_project_loaded(self, project):
        """项目加载事件"""
        self._refresh_projects()

    def _apply_theme(self):
        """应用主题"""
        current_theme = self.theme_manager.get_current_theme().value
        self._on_theme_changed(current_theme)

    def _on_theme_changed(self, theme_value: str):
        """主题变更处理"""
        is_dark = theme_value == "dark"

        if is_dark:
            # 深色主题样式
            self.setStyleSheet("""
                QLabel#section_title {
                    color: #ffffff;
                    margin-bottom: 8px;
                }
            """)
        else:
            # 浅色主题样式
            self.setStyleSheet("""
                QLabel#section_title {
                    color: #262626;
                    margin-bottom: 8px;
                }
            """)
