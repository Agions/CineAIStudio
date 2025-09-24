"""
增强的媒体库组件
提供专业的媒体文件管理、预览、搜索和组织功能
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QComboBox, QLineEdit, QProgressBar, QGroupBox,
    QScrollArea, QFrame, QToolBar, QMenu, QMessageBox, QDialog,
    QFileDialog, QApplication, QStatusBar, QTabWidget, QStackedWidget,
    QGridLayout, QFormLayout, QSpinBox, QCheckBox, QSlider
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QSize, QPoint, QTimer, QModelIndex, QUrl,
    QMimeData, QRect, QThread, pyqtSlot
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QDrag, QPainter, QPen, QColor,
    QFont, QCursor, QAction, QKeyEvent, QKeySequence
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from app.core.logger import Logger
from app.services.media_manager import MediaManager, MediaMetadata
from app.utils.error_handler import handle_exception, show_error_dialog, safe_execute
from app.utils.ui_error_handler import UIErrorInfo, UIErrorSeverity


@dataclass
class MediaLibraryConfig:
    """媒体库配置"""
    thumbnail_size: QSize = QSize(160, 90)
    grid_spacing: int = 10
    items_per_row: int = 5
    show_details: bool = True
    auto_refresh: bool = True
    cache_enabled: bool = True


class MediaItemWidget(QWidget):
    """媒体项组件"""

    clicked = pyqtSignal(str)
    double_clicked = pyqtSignal(str)
    context_menu_requested = pyqtSignal(str, QPoint)

    def __init__(self, media_info: Dict[str, Any], config: MediaLibraryConfig):
        super().__init__()
        self.media_info = media_info
        self.config = config
        self.logger = Logger.get_logger("MediaItemWidget")

        self.setObjectName("media_item")
        self.setFixedSize(config.thumbnail_size + QSize(0, 40))
        self.setMouseTracking(True)

        self._setup_ui()
        self._load_thumbnail()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # 缩略图标签
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(self.config.thumbnail_size)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.thumbnail_label)

        # 文件名标签
        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 10px;
                background: transparent;
            }
        """)
        layout.addWidget(self.name_label)

        # 更新显示
        self._update_display()

    def _update_display(self):
        """更新显示信息"""
        metadata = self.media_info.get('metadata', {})
        file_name = metadata.get('file_name', 'Unknown')

        # 截断文件名
        if len(file_name) > 20:
            file_name = file_name[:17] + '...'

        self.name_label.setText(file_name)

        # 设置工具提示
        self._set_tooltip()

    def _set_tooltip(self):
        """设置工具提示"""
        metadata = self.media_info.get('metadata', {})
        file_size = metadata.get('file_size', 0)
        file_type = metadata.get('file_type', 'unknown')
        duration = metadata.get('duration')

        tooltip_text = f"""
        <b>文件名:</b> {metadata.get('file_name', 'Unknown')}<br>
        <b>大小:</b> {self._format_file_size(file_size)}<br>
        <b>类型:</b> {file_type}<br>
        """

        if duration:
            tooltip_text += f"<b>时长:</b> {self._format_duration(duration)}<br>"

        if file_type == 'video':
            width = metadata.get('width')
            height = metadata.get('height')
            if width and height:
                tooltip_text += f"<b>分辨率:</b> {width}x{height}<br>"

            fps = metadata.get('fps')
            if fps:
                tooltip_text += f"<b>帧率:</b> {fps:.1f} fps<br>"

        self.setToolTip(tooltip_text.strip())

    def _load_thumbnail(self):
        """加载缩略图"""
        file_path = self.media_info.get('metadata', {}).get('file_path')
        if file_path:
            # 异步加载缩略图
            QTimer.singleShot(100, lambda: self._async_load_thumbnail(file_path))

    def _async_load_thumbnail(self, file_path: str):
        """异步加载缩略图"""
        try:
            # 这里应该使用MediaManager获取缩略图
            # 暂时使用占位符
            icon = self._get_file_icon()
            self.thumbnail_label.setPixmap(icon)

        except Exception as e:
            self.logger.error(f"Failed to load thumbnail: {e}")
            self.thumbnail_label.setText("❌")

    def _get_file_icon(self) -> QPixmap:
        """获取文件图标"""
        file_type = self.media_info.get('metadata', {}).get('file_type', 'unknown')

        icon_size = self.config.thumbnail_size

        # 根据文件类型返回不同的图标
        if file_type == 'video':
            return self._create_video_icon(icon_size)
        elif file_type == 'audio':
            return self._create_audio_icon(icon_size)
        elif file_type == 'image':
            return self._create_image_icon(icon_size)
        else:
            return self._create_default_icon(icon_size)

    def _create_video_icon(self, size: QSize) -> QPixmap:
        """创建视频图标"""
        pixmap = QPixmap(size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制播放按钮
        center_x = size.width() // 2
        center_y = size.height() // 2
        radius = min(size.width(), size.height()) // 4

        # 背景
        painter.setBrush(QColor(0, 0, 0, 180))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # 播放三角形
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon([
            QPoint(center_x - radius // 2, center_y - radius // 2),
            QPoint(center_x - radius // 2, center_y + radius // 2),
            QPoint(center_x + radius // 2, center_y)
        ])

        painter.end()
        return pixmap

    def _create_audio_icon(self, size: QSize) -> QPixmap:
        """创建音频图标"""
        pixmap = QPixmap(size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制音频波形
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        center_y = size.height() // 2

        # 简单的波形图案
        for i in range(5):
            x = size.width() // 6 * (i + 1)
            height = (i + 1) * size.height() // 12
            painter.drawLine(x, center_y - height, x, center_y + height)

        painter.end()
        return pixmap

    def _create_image_icon(self, size: QSize) -> QPixmap:
        """创建图片图标"""
        pixmap = QPixmap(size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制山形图案
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QColor(255, 255, 255, 50))

        # 简单的山形
        points = [
            QPoint(0, size.height()),
            QPoint(size.width() // 3, size.height() // 3),
            QPoint(size.width() * 2 // 3, size.height() // 2),
            QPoint(size.width(), size.height() // 4),
            QPoint(size.width(), size.height())
        ]
        painter.drawPolygon(points)

        painter.end()
        return pixmap

    def _create_default_icon(self, size: QSize) -> QPixmap:
        """创建默认图标"""
        pixmap = QPixmap(size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制问号
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        font = QFont()
        font.setPointSize(size.width() // 3)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "?")

        painter.end()
        return pixmap

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    def _format_duration(self, duration_seconds: float) -> str:
        """格式化时长"""
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.media_info.get('metadata', {}).get('file_path', ''))
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(
                self.media_info.get('metadata', {}).get('file_path', ''),
                event.globalPosition().toPoint()
            )

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.media_info.get('metadata', {}).get('file_path', ''))


class MediaGridView(QScrollArea):
    """媒体网格视图"""

    item_selected = pyqtSignal(str)
    item_double_clicked = pyqtSignal(str)
    item_context_menu = pyqtSignal(str, QPoint)

    def __init__(self, config: MediaLibraryConfig):
        super().__init__()
        self.config = config
        self.logger = Logger.get_logger("MediaGridView")

        self.media_items = []
        self.selected_items = set()

        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        """设置UI"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 创建内容容器
        self.content_widget = QWidget()
        self.content_widget.setObjectName("media_grid_content")
        self.setWidget(self.content_widget)

        # 设置主布局
        self.main_layout = QGridLayout(self.content_widget)
        self.main_layout.setSpacing(self.config.grid_spacing)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def set_media_items(self, media_list: List[Dict[str, Any]]):
        """设置媒体项"""
        # 清除现有项
        self._clear_items()

        # 添加新项
        for i, media_info in enumerate(media_list):
            item_widget = MediaItemWidget(media_info, self.config)

            # 连接信号
            item_widget.clicked.connect(self._on_item_clicked)
            item_widget.double_clicked.connect(self._on_item_double_clicked)
            item_widget.context_menu_requested.connect(self._on_item_context_menu)

            # 添加到网格
            row = i // self.config.items_per_row
            col = i % self.config.items_per_row
            self.main_layout.addWidget(item_widget, row, col)

            self.media_items.append(item_widget)

    def _clear_items(self):
        """清除所有项"""
        for item in self.media_items:
            item.deleteLater()
        self.media_items.clear()
        self.selected_items.clear()

    def _on_item_clicked(self, file_path: str):
        """项点击事件"""
        self.item_selected.emit(file_path)

    def _on_item_double_clicked(self, file_path: str):
        """项双击事件"""
        self.item_double_clicked.emit(file_path)

    def _on_item_context_menu(self, file_path: str, pos: QPoint):
        """项右键菜单事件"""
        self.item_context_menu.emit(file_path, pos)

    def clear_selection(self):
        """清除选择"""
        self.selected_items.clear()

    def get_selected_items(self) -> List[str]:
        """获取选中的项"""
        return list(self.selected_items)


class EnhancedMediaLibrary(QWidget):
    """增强的媒体库组件"""

    media_selected = pyqtSignal(str)
    media_double_clicked = pyqtSignal(str)
    media_imported = pyqtSignal(list)
    refresh_requested = pyqtSignal()

    def __init__(self, config: MediaLibraryConfig = None):
        super().__init__()
        self.config = config or MediaLibraryConfig()
        self.logger = Logger.get_logger("EnhancedMediaLibrary")

        # 初始化媒体管理器
        self.media_manager = MediaManager()

        # 支持的文件类型
        self.supported_filters = {
            'video': '视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.3gp *.mpg *.mpeg)',
            'audio': '音频文件 (*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma *.opus *.aiff)',
            'image': '图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp *.tga *.svg)',
            'all': '所有支持的文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.3gp *.mpg *.mpeg *.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma *.opus *.aiff *.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp *.tga *.svg)'
        }

        self._setup_ui()
        self._setup_connections()
        self._setup_style()

        # 加载数据
        self.refresh_media_library()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 创建搜索和过滤器栏
        filter_bar = self._create_filter_bar()
        layout.addWidget(filter_bar)

        # 创建主分割器
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setHandleWidth(2)

        # 创建媒体视图
        self.media_grid = MediaGridView(self.config)
        main_splitter.addWidget(self.media_grid)

        # 创建预览面板
        self.preview_panel = self._create_preview_panel()
        main_splitter.addWidget(self.preview_panel)

        # 设置分割器比例
        main_splitter.setSizes([600, 200])
        layout.addWidget(main_splitter)

        # 创建状态栏
        self.status_bar = self._create_status_bar()
        layout.addWidget(self.status_bar)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        toolbar.setObjectName("media_toolbar")
        toolbar.setFixedHeight(40)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 5, 5, 5)

        # 导入按钮
        self.import_button = QPushButton("📥 导入媒体")
        self.import_button.setFixedWidth(100)
        layout.addWidget(self.import_button)

        # 视图模式
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["网格视图", "列表视图", "详细视图"])
        self.view_mode_combo.setFixedWidth(100)
        layout.addWidget(self.view_mode_combo)

        # 缩略图大小
        self.thumbnail_size_combo = QComboBox()
        self.thumbnail_size_combo.addItems(["小图标", "中图标", "大图标"])
        self.thumbnail_size_combo.setFixedWidth(80)
        layout.addWidget(self.thumbnail_size_combo)

        layout.addStretch()

        # 刷新按钮
        self.refresh_button = QPushButton("🔄 刷新")
        self.refresh_button.setFixedWidth(80)
        layout.addWidget(self.refresh_button)

        # 设置按钮
        self.settings_button = QPushButton("⚙️ 设置")
        self.settings_button.setFixedWidth(80)
        layout.addWidget(self.settings_button)

        return toolbar

    def _create_filter_bar(self) -> QWidget:
        """创建过滤栏"""
        filter_bar = QWidget()
        filter_bar.setObjectName("media_filter_bar")
        filter_bar.setFixedHeight(35)
        layout = QHBoxLayout(filter_bar)
        layout.setContentsMargins(5, 5, 5, 5)

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索媒体文件...")
        layout.addWidget(self.search_input, 1)

        # 文件类型过滤器
        self.type_filter = QComboBox()
        self.type_filter.addItems(["全部", "视频", "音频", "图片"])
        self.type_filter.setFixedWidth(80)
        layout.addWidget(self.type_filter)

        # 排序方式
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按名称", "按大小", "按日期", "按类型"])
        self.sort_combo.setFixedWidth(100)
        layout.addWidget(self.sort_combo)

        return filter_bar

    def _create_preview_panel(self) -> QWidget:
        """创建预览面板"""
        preview_panel = QWidget()
        preview_panel.setObjectName("media_preview_panel")
        preview_panel.setFixedHeight(150)
        layout = QHBoxLayout(preview_panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # 预览区域
        self.preview_widget = QLabel()
        self.preview_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_widget.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 1px solid #404040;
                border-radius: 4px;
                color: #888888;
            }
        """)
        self.preview_widget.setText("选择文件进行预览")
        layout.addWidget(self.preview_widget, 1)

        # 文件信息
        info_group = QGroupBox("文件信息")
        info_layout = QFormLayout(info_group)

        self.file_name_label = QLabel("-")
        self.file_size_label = QLabel("-")
        self.file_type_label = QLabel("-")
        self.file_duration_label = QLabel("-")

        info_layout.addRow("文件名:", self.file_name_label)
        info_layout.addRow("大小:", self.file_size_label)
        info_layout.addRow("类型:", self.file_type_label)
        info_layout.addRow("时长:", self.file_duration_label)

        layout.addWidget(info_group, 1)

        return preview_panel

    def _create_status_bar(self) -> QStatusBar:
        """创建状态栏"""
        status_bar = QStatusBar()
        status_bar.setObjectName("media_status_bar")

        # 文件数量标签
        self.file_count_label = QLabel("共 0 个文件")
        status_bar.addPermanentWidget(self.file_count_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setVisible(False)
        status_bar.addPermanentWidget(self.progress_bar)

        return status_bar

    def _setup_connections(self):
        """设置信号连接"""
        # 工具栏
        self.import_button.clicked.connect(self.import_media_files)
        self.refresh_button.clicked.connect(self.refresh_media_library)
        self.settings_button.clicked.connect(self.show_settings)

        # 搜索和过滤
        self.search_input.textChanged.connect(self._filter_media)
        self.type_filter.currentTextChanged.connect(self._filter_media)
        self.sort_combo.currentTextChanged.connect(self._sort_media)

        # 视图
        self.view_mode_combo.currentTextChanged.connect(self._change_view_mode)
        self.thumbnail_size_combo.currentTextChanged.connect(self._change_thumbnail_size)

        # 媒体项
        self.media_grid.item_selected.connect(self._on_media_selected)
        self.media_grid.item_double_clicked.connect(self._on_media_double_clicked)
        self.media_grid.item_context_menu.connect(self._on_media_context_menu)

        # 媒体管理器
        self.media_manager.media_imported.connect(self._on_media_imported)
        self.media_manager.import_progress.connect(self._on_import_progress)

    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QWidget#media_toolbar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #404040;
            }
            QWidget#media_filter_bar {
                background-color: #252525;
                border-bottom: 1px solid #404040;
            }
            QWidget#media_preview_panel {
                background-color: #2b2b2b;
                border-top: 1px solid #404040;
            }
            QPushButton {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4b4b4b;
            }
            QPushButton:pressed {
                background-color: #2b2b2b;
            }
            QComboBox {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 3px 5px;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QGroupBox {
                background-color: transparent;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

    def import_media_files(self):
        """导入媒体文件"""
        try:
            # 打开文件选择对话框
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            file_dialog.setNameFilter(self.supported_filters['all'])
            file_dialog.setWindowTitle("选择媒体文件")

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                file_paths = file_dialog.selectedFiles()
                if file_paths:
                    # 显示进度条
                    self.progress_bar.setVisible(True)
                    self.progress_bar.setRange(0, len(file_paths))

                    # 导入文件
                    imported_files = self.media_manager.import_media_files(file_paths)

                    # 隐藏进度条
                    self.progress_bar.setVisible(False)

                    # 刷新视图
                    self.refresh_media_library()

                    # 发送信号
                    self.media_imported.emit(imported_files)

                    self.logger.info(f"Imported {len(imported_files)} media files")

        except Exception as e:
            self.logger.error(f"Failed to import media files: {e}")
            show_error_dialog("导入失败", f"导入媒体文件时发生错误: {e}")

    def refresh_media_library(self):
        """刷新媒体库"""
        try:
            # 获取所有媒体文件
            all_media = []

            # 从媒体管理器获取媒体
            # 这里应该从媒体管理器获取，暂时使用示例数据
            # 实际实现中应该从MediaManager获取

            self.media_grid.set_media_items(all_media)
            self._update_status()

        except Exception as e:
            self.logger.error(f"Failed to refresh media library: {e}")
            show_error_dialog("刷新失败", f"刷新媒体库时发生错误: {e}")

    def _filter_media(self):
        """过滤媒体"""
        try:
            search_text = self.search_input.text().lower()
            file_type = self.type_filter.currentText()

            # 获取过滤后的媒体列表
            # 这里应该实现实际的过滤逻辑
            # filtered_media = self._get_filtered_media(search_text, file_type)

            # 更新网格视图
            # self.media_grid.set_media_items(filtered_media)
            self._update_status()

        except Exception as e:
            self.logger.error(f"Failed to filter media: {e}")

    def _sort_media(self):
        """排序媒体"""
        try:
            sort_by = self.sort_combo.currentText()

            # 获取排序后的媒体列表
            # 这里应该实现实际的排序逻辑
            # sorted_media = self._get_sorted_media(sort_by)

            # 更新网格视图
            # self.media_grid.set_media_items(sorted_media)
            self._update_status()

        except Exception as e:
            self.logger.error(f"Failed to sort media: {e}")

    def _change_view_mode(self, mode: str):
        """改变视图模式"""
        try:
            # 这里应该实现视图模式切换
            self.logger.info(f"Changing view mode to: {mode}")

        except Exception as e:
            self.logger.error(f"Failed to change view mode: {e}")

    def _change_thumbnail_size(self, size: str):
        """改变缩略图大小"""
        try:
            # 映射大小到实际的尺寸
            size_map = {
                "小图标": QSize(120, 68),
                "中图标": QSize(160, 90),
                "大图标": QSize(200, 113)
            }

            new_size = size_map.get(size, self.config.thumbnail_size)
            self.config.thumbnail_size = new_size

            # 重新设置媒体项
            self.refresh_media_library()

        except Exception as e:
            self.logger.error(f"Failed to change thumbnail size: {e}")

    def _on_media_selected(self, file_path: str):
        """媒体项选择事件"""
        try:
            self.media_selected.emit(file_path)
            self._update_preview(file_path)

        except Exception as e:
            self.logger.error(f"Failed to handle media selection: {e}")

    def _on_media_double_clicked(self, file_path: str):
        """媒体项双击事件"""
        try:
            self.media_double_clicked.emit(file_path)
            # 这里可以实现打开预览窗口等

        except Exception as e:
            self.logger.error(f"Failed to handle media double click: {e}")

    def _on_media_context_menu(self, file_path: str, pos: QPoint):
        """媒体项右键菜单事件"""
        try:
            menu = QMenu(self)

            # 添加菜单项
            preview_action = menu.addAction("👁️ 预览")
            edit_action = menu.addAction("✏️ 编辑")
            export_action = menu.addAction("📤 导出")
            delete_action = menu.addAction("🗑️ 删除")
            properties_action = menu.addAction("📋 属性")

            # 显示菜单
            action = menu.exec(pos)

            # 处理菜单选择
            if action == preview_action:
                self._preview_media(file_path)
            elif action == edit_action:
                self._edit_media(file_path)
            elif action == export_action:
                self._export_media(file_path)
            elif action == delete_action:
                self._delete_media(file_path)
            elif action == properties_action:
                self._show_properties(file_path)

        except Exception as e:
            self.logger.error(f"Failed to show context menu: {e}")

    def _on_media_imported(self, media_list: List[Dict[str, Any]]):
        """媒体导入完成事件"""
        self.logger.info(f"Media import completed: {len(media_list)} files")
        self.refresh_media_library()

    def _on_import_progress(self, current: int, total: int, status: str):
        """导入进度更新"""
        if self.progress_bar.isVisible():
            self.progress_bar.setValue(current)
            self.progress_bar.setFormat(f"{status} ({current}/{total})")

    def _update_preview(self, file_path: str):
        """更新预览"""
        try:
            # 获取媒体信息
            media_info = self.media_manager.get_media_info(file_path)
            if media_info:
                metadata = media_info.get('metadata', {})

                # 更新文件信息
                self.file_name_label.setText(metadata.get('file_name', '-'))
                self.file_size_label.setText(self._format_file_size(metadata.get('file_size', 0)))
                self.file_type_label.setText(metadata.get('file_type', '-'))

                # 更新时长
                duration = metadata.get('duration')
                if duration:
                    self.file_duration_label.setText(self._format_duration(duration))
                else:
                    self.file_duration_label.setText('-')

                # 更新预览图像
                thumbnail = self.media_manager.get_thumbnail(file_path)
                if thumbnail:
                    self.preview_widget.setPixmap(thumbnail)
                else:
                    self.preview_widget.setText("无预览")

        except Exception as e:
            self.logger.error(f"Failed to update preview: {e}")

    def _update_status(self):
        """更新状态栏"""
        try:
            # 更新文件数量
            # 这里应该从媒体管理器获取实际的文件数量
            file_count = len(self.media_grid.media_items)
            self.file_count_label.setText(f"共 {file_count} 个文件")

        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    def _format_duration(self, duration_seconds: float) -> str:
        """格式化时长"""
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def show_settings(self):
        """显示设置对话框"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("媒体库设置")
            dialog.setModal(True)
            dialog.setMinimumWidth(400)

            layout = QVBoxLayout(dialog)

            # 缩略图设置
            thumbnail_group = QGroupBox("缩略图设置")
            thumbnail_layout = QFormLayout(thumbnail_group)

            cache_checkbox = QCheckBox("启用缩略图缓存")
            cache_checkbox.setChecked(self.config.cache_enabled)
            thumbnail_layout.addRow("缓存设置:", cache_checkbox)

            auto_refresh_checkbox = QCheckBox("自动刷新")
            auto_refresh_checkbox.setChecked(self.config.auto_refresh)
            thumbnail_layout.addRow("自动刷新:", auto_refresh_checkbox)

            show_details_checkbox = QCheckBox("显示详细信息")
            show_details_checkbox.setChecked(self.config.show_details)
            thumbnail_layout.addRow("显示详情:", show_details_checkbox)

            layout.addWidget(thumbnail_group)

            # 性能设置
            performance_group = QGroupBox("性能设置")
            performance_layout = QFormLayout(performance_group)

            items_per_row_spin = QSpinBox()
            items_per_row_spin.setRange(1, 10)
            items_per_row_spin.setValue(self.config.items_per_row)
            performance_layout.addRow("每行项目数:", items_per_row_spin)

            layout.addWidget(performance_group)

            # 按钮
            button_layout = QHBoxLayout()
            save_button = QPushButton("保存")
            cancel_button = QPushButton("取消")
            button_layout.addWidget(save_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)

            # 连接信号
            save_button.clicked.connect(lambda: self._save_settings(
                cache_checkbox.isChecked(),
                auto_refresh_checkbox.isChecked(),
                show_details_checkbox.isChecked(),
                items_per_row_spin.value(),
                dialog
            ))
            cancel_button.clicked.connect(dialog.reject)

            dialog.exec()

        except Exception as e:
            self.logger.error(f"Failed to show settings: {e}")

    def _save_settings(self, cache_enabled: bool, auto_refresh: bool, show_details: bool,
                      items_per_row: int, dialog: QDialog):
        """保存设置"""
        try:
            self.config.cache_enabled = cache_enabled
            self.config.auto_refresh = auto_refresh
            self.config.show_details = show_details
            self.config.items_per_row = items_per_row

            # 应用设置
            self.media_grid.config = self.config
            self.refresh_media_library()

            dialog.accept()

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")

    def _preview_media(self, file_path: str):
        """预览媒体"""
        try:
            self.logger.info(f"Previewing media: {file_path}")
            # 这里应该实现媒体预览功能

        except Exception as e:
            self.logger.error(f"Failed to preview media: {e}")

    def _edit_media(self, file_path: str):
        """编辑媒体"""
        try:
            self.logger.info(f"Editing media: {file_path}")
            # 这里应该实现媒体编辑功能

        except Exception as e:
            self.logger.error(f"Failed to edit media: {e}")

    def _export_media(self, file_path: str):
        """导出媒体"""
        try:
            self.logger.info(f"Exporting media: {file_path}")
            # 这里应该实现媒体导出功能

        except Exception as e:
            self.logger.error(f"Failed to export media: {e}")

    def _delete_media(self, file_path: str):
        """删除媒体"""
        try:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除文件 {os.path.basename(file_path)} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success = self.media_manager.delete_media(file_path)
                if success:
                    self.refresh_media_library()
                    self.logger.info(f"Deleted media: {file_path}")
                else:
                    show_error_dialog("删除失败", f"无法删除文件: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to delete media: {e}")

    def _show_properties(self, file_path: str):
        """显示属性"""
        try:
            # 获取媒体信息
            media_info = self.media_manager.get_media_info(file_path)
            if media_info:
                self._show_properties_dialog(file_path, media_info)

        except Exception as e:
            self.logger.error(f"Failed to show properties: {e}")

    def _show_properties_dialog(self, file_path: str, media_info: Dict[str, Any]):
        """显示属性对话框"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("文件属性")
            dialog.setModal(True)
            dialog.setMinimumWidth(400)

            layout = QVBoxLayout(dialog)

            # 基本信息
            basic_group = QGroupBox("基本信息")
            basic_layout = QFormLayout(basic_group)

            metadata = media_info.get('metadata', {})

            basic_layout.addRow("文件名:", QLabel(metadata.get('file_name', '-')))
            basic_layout.addRow("文件路径:", QLabel(metadata.get('file_path', '-')))
            basic_layout.addRow("文件大小:", QLabel(self._format_file_size(metadata.get('file_size', 0))))
            basic_layout.addRow("文件类型:", QLabel(metadata.get('file_type', '-')))
            basic_layout.addRow("MIME类型:", QLabel(metadata.get('mime_type', '-')))

            layout.addWidget(basic_group)

            # 媒体信息
            media_group = QGroupBox("媒体信息")
            media_layout = QFormLayout(media_group)

            duration = metadata.get('duration')
            if duration:
                media_layout.addRow("时长:", QLabel(self._format_duration(duration)))

            if metadata.get('file_type') == 'video':
                media_layout.addRow("分辨率:", QLabel(f"{metadata.get('width', 0)}x{metadata.get('height', 0)}"))
                media_layout.addRow("帧率:", QLabel(f"{metadata.get('fps', 0):.1f} fps"))
                media_layout.addRow("视频编码:", QLabel(metadata.get('codec', '-')))

            if metadata.get('audio_codec'):
                media_layout.addRow("音频编码:", QLabel(metadata.get('audio_codec', '-')))
                media_layout.addRow("音频码率:", QLabel(f"{metadata.get('audio_bitrate', 0)} kbps"))
                media_layout.addRow("声道数:", QLabel(str(metadata.get('audio_channels', 0))))
                media_layout.addRow("采样率:", QLabel(f"{metadata.get('sample_rate', 0)} Hz"))

            layout.addWidget(media_group)

            # 按钮
            button_layout = QHBoxLayout()
            ok_button = QPushButton("确定")
            button_layout.addWidget(ok_button)
            layout.addLayout(button_layout)

            ok_button.clicked.connect(dialog.accept)

            dialog.exec()

        except Exception as e:
            self.logger.error(f"Failed to show properties dialog: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取媒体库统计信息"""
        try:
            return self.media_manager.get_statistics()
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}

    def cleanup(self):
        """清理资源"""
        try:
            self.media_manager.shutdown()
            self.logger.info("Media library cleanup completed")
        except Exception as e:
            self.logger.error(f"Failed to cleanup media library: {e}")