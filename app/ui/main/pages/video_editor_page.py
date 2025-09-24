"""
视频编辑页面 - 根据截图实现的专业视频编辑器界面
"""

import os
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QFrame, QScrollArea, QStackedWidget, QToolBar, QStatusBar,
    QMenuBar, QMenu, QPushButton, QToolButton, QComboBox,
    QSlider, QProgressBar, QTabWidget, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QRadioButton, QButtonGroup,
    QTextEdit, QLineEdit, QMessageBox, QFileDialog, QApplication,
    QToolBox, QAbstractItemView, QGraphicsView, QGraphicsScene, QSizePolicy
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QPoint, QMimeData, QUrl
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap, QPalette, QColor, QDragEnterEvent, QDropEvent

from .base_page import BasePage
from app.services.mock_ai_service import MockAIService
from app.core.icon_manager import get_icon
from app.ui.main.components.enhanced_media_library import EnhancedMediaLibrary, MediaLibraryConfig
  class MediaLibraryPanel(QWidget):
    """增强的媒体库面板"""

    video_selected = pyqtSignal(str)
    audio_selected = pyqtSignal(str)
    image_selected = pyqtSignal(str)
    project_opened = pyqtSignal(str)
    media_imported = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        # 配置增强媒体库
        config = MediaLibraryConfig(
            thumbnail_size=QSize(120, 68),
            grid_spacing=8,
            items_per_row=3,
            show_details=True,
            auto_refresh=True,
            cache_enabled=True
        )

        # 创建增强媒体库
        self.media_library = EnhancedMediaLibrary(config)
        layout.addWidget(self.media_library)

        # 连接信号
        self.media_library.media_selected.connect(self._on_media_selected)
        self.media_library.media_double_clicked.connect(self._on_media_double_clicked)
        self.media_library.media_imported.connect(self._on_media_imported)
        self.media_library.refresh_requested.connect(self._on_refresh_requested)

    def _on_media_selected(self, file_path: str):
        """处理媒体选择"""
        # 根据文件类型发出相应信号
        if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')):
            self.video_selected.emit(file_path)
        elif file_path.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a')):
            self.audio_selected.emit(file_path)
        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')):
            self.image_selected.emit(file_path)

    def _on_media_double_clicked(self, file_path: str):
        """处理媒体双击"""
        self._on_media_selected(file_path)

    def _on_media_imported(self, media_list: list):
        """处理媒体导入完成"""
        self.media_imported.emit(media_list)

    def _on_refresh_requested(self):
        """处理刷新请求"""
        self.media_library.refresh_media_library()

    def import_media_files(self):
        """导入媒体文件"""
        self.media_library.import_media_files()

    def refresh_library(self):
        """刷新媒体库"""
        self.media_library.refresh_media_library()

    def get_statistics(self):
        """获取统计信息"""
        return self.media_library.get_statistics()

    def cleanup(self):
        """清理资源"""
        self.media_library.cleanup()
        
    def _show_video_context_menu(self, position):
        """显示视频文件右键菜单"""
        menu = QMenu()
        import_action = menu.addAction("导入文件")
        delete_action = menu.addAction("删除文件")
        preview_action = menu.addAction("预览")

        action = menu.exec(self.video_list.mapToGlobal(position))

        if action == import_action:
            self._import_video_files()
        elif action == delete_action:
            self._delete_selected_video()
        elif action == preview_action:
            self._preview_selected_video()

    def _show_audio_context_menu(self, position):
        """显示音频文件右键菜单"""
        menu = QMenu()
        import_action = menu.addAction("导入文件")
        delete_action = menu.addAction("删除文件")
        play_action = menu.addAction("播放")

        action = menu.exec(self.audio_list.mapToGlobal(position))

        if action == import_action:
            self._import_audio_files()
        elif action == delete_action:
            self._delete_selected_audio()
        elif action == play_action:
            self._play_selected_audio()

    def _show_image_context_menu(self, position):
        """显示图片文件右键菜单"""
        menu = QMenu()
        import_action = menu.addAction("导入文件")
        delete_action = menu.addAction("删除文件")
        view_action = menu.addAction("查看")

        action = menu.exec(self.image_list.mapToGlobal(position))

        if action == import_action:
            self._import_image_files()
        elif action == delete_action:
            self._delete_selected_image()
        elif action == view_action:
            self._view_selected_image()

    def _import_video_files(self):
        """导入视频文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm)"
        )
        if files:
            self.add_media_files(files)

    def _import_audio_files(self):
        """导入音频文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", "",
            "音频文件 (*.mp3 *.wav *.flac *.aac *.ogg *.m4a)"
        )
        if files:
            self.add_media_files(files)

    def _import_image_files(self):
        """导入图片文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp)"
        )
        if files:
            self.add_media_files(files)

    def _delete_selected_video(self):
        """删除选中的视频文件"""
        current_item = self.video_list.currentItem()
        if current_item:
            row = self.video_list.row(current_item)
            self.video_list.takeItem(row)

    def _delete_selected_audio(self):
        """删除选中的音频文件"""
        current_item = self.audio_list.currentItem()
        if current_item:
            row = self.audio_list.row(current_item)
            self.audio_list.takeItem(row)

    def _delete_selected_image(self):
        """删除选中的图片文件"""
        current_item = self.image_list.currentItem()
        if current_item:
            row = self.image_list.row(current_item)
            self.image_list.takeItem(row)

    def _preview_selected_video(self):
        """预览选中的视频文件"""
        current_item = self.video_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            self.video_selected.emit(file_path)

    def _play_selected_audio(self):
        """播放选中的音频文件"""
        current_item = self.audio_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            self.audio_selected.emit(file_path)

    def _view_selected_image(self):
        """查看选中的图片文件"""
        current_item = self.image_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            self.image_selected.emit(file_path)

    def _on_video_double_clicked(self, item):
        """双击视频文件事件"""
        if item:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.video_selected.emit(file_path)
            else:
                # 示例文件处理
                self.video_selected.emit(f"/path/to/{item.text()}")

    def _on_audio_double_clicked(self, item):
        """双击音频文件事件"""
        if item:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.audio_selected.emit(file_path)
            else:
                # 示例文件处理
                self.audio_selected.emit(f"/path/to/{item.text()}")

    def _on_image_double_clicked(self, item):
        """双击图片文件事件"""
        if item:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.image_selected.emit(file_path)
            else:
                # 示例文件处理
                self.image_selected.emit(f"/path/to/{item.text()}")

    def _on_export_double_clicked(self, item):
        """双击导出文件事件"""
        if item:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.video_selected.emit(file_path)
            else:
                # 示例文件处理
                self.video_selected.emit(f"/path/to/{item.text()}")


class PreviewPanel(QWidget):
    """预览面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_player = None
        self.video_widget = None
        self.audio_output = None
        self.current_video_path = None
        self.is_playing = False
        self.logger = None
        self.setup_ui()
        self.setup_media_player()

    def setup_media_player(self):
        """设置媒体播放器"""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        # 连接信号
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.media_player.errorOccurred.connect(self._on_media_error)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 预览区域
        self.preview_area = QFrame()
        self.preview_area.setMinimumHeight(400)
        self.preview_area.setStyleSheet("""
            QFrame {
                background: #1A1A1A;
                border: 2px solid #3A3A3A;
                border-radius: 4px;
            }
        """)

        preview_layout = QVBoxLayout(self.preview_area)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # 创建视频播放器
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("""
            QVideoWidget {
                background: #000000;
                border: none;
            }
        """)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 创建提示标签
        self.placeholder_label = QLabel("拖拽视频文件到这里或从媒体库选择")
        self.placeholder_label.setStyleSheet("color: #B0B0B0; font-size: 14px;")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 初始显示占位符
        preview_layout.addWidget(self.placeholder_label)

        layout.addWidget(self.preview_area)

        # 播放控制栏
        control_layout = QHBoxLayout()

        # 播放按钮
        self.play_btn = QPushButton(get_icon("play", 16), "")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #404040;
                color: #FFFFFF;
                border: 1px solid #3A3A3A;
                padding: 8px;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #505050;
            }
        """)
        self.play_btn.setToolTip("播放/暂停 (空格键)")
        self.play_btn.clicked.connect(self._toggle_playback)

        # 时间显示
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet("color: #B0B0B0;")

        # 进度条
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2A2A2A;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #00A8FF;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
        """)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.setToolTip("播放进度 (左右箭头键: ±5秒)")
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.valueChanged.connect(self._on_slider_changed)

        # 音量控制
        self.volume_btn = QPushButton(get_icon("audio", 16), "")
        self.volume_btn.setStyleSheet(self.play_btn.styleSheet())
        self.volume_btn.setToolTip("静音/取消静音 (M键)")
        self.volume_btn.clicked.connect(self._toggle_mute)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setToolTip("音量控制 (上下箭头键: ±10%)")
        self.volume_slider.setStyleSheet(self.progress_slider.styleSheet())
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

        # 缩放控制
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["25%", "50%", "75%", "100%", "125%", "150%", "适应窗口"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setStyleSheet("""
            QComboBox {
                background: #2A2A2A;
                color: #FFFFFF;
                border: 1px solid #3A3A3A;
                padding: 4px;
                border-radius: 4px;
            }
        """)
        self.zoom_combo.currentTextChanged.connect(self._on_zoom_changed)

        # 全屏按钮
        self.fullscreen_btn = QPushButton(get_icon("fullscreen", 16), "")
        self.fullscreen_btn.setStyleSheet(self.play_btn.styleSheet())
        self.fullscreen_btn.setToolTip("全屏 (F键)")
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)

        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.time_label)
        control_layout.addWidget(self.progress_slider, 1)
        control_layout.addWidget(self.volume_btn)
        control_layout.addWidget(self.volume_slider)
        control_layout.addWidget(self.zoom_combo)
        control_layout.addWidget(self.fullscreen_btn)

        layout.addLayout(control_layout)

    def load_video(self, video_path: str):
        """加载视频文件"""
        try:
            if not os.path.exists(video_path):
                QMessageBox.warning(self, "错误", f"视频文件不存在: {video_path}")
                return False

            self.current_video_path = video_path

            # 设置视频源
            self.media_player.setSource(QUrl.fromLocalFile(video_path))

            # 显示视频播放器
            self.preview_layout().removeWidget(self.placeholder_label)
            self.placeholder_label.hide()
            self.preview_layout().addWidget(self.video_widget)
            self.video_widget.show()

            # 设置音量
            self.audio_output.setVolume(self.volume_slider.value() / 100.0)

            self.logger.info(f"视频加载成功: {os.path.basename(video_path)}")
            return True

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载视频失败: {str(e)}")
            self.logger.error(f"视频加载失败: {e}")
            return False

    def preview_layout(self):
        """获取预览区域的布局"""
        return self.preview_area.layout()

    def _toggle_playback(self):
        """切换播放/暂停"""
        if self.current_video_path is None:
            return

        if self.is_playing:
            self.media_player.pause()
        else:
            self.media_player.play()

    def _toggle_mute(self):
        """切换静音"""
        if self.audio_output.volume() == 0:
            self.audio_output.setVolume(self.volume_slider.value() / 100.0)
            self.volume_btn.setText("🔊")
        else:
            self.audio_output.setVolume(0)
            self.volume_btn.setText("🔇")

    def _toggle_fullscreen(self):
        """切换全屏"""
        if self.video_widget.isFullScreen():
            self.video_widget.showNormal()
        else:
            self.video_widget.showFullScreen()

    def _on_position_changed(self, position: int):
        """播放位置变化"""
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)

        # 更新时间显示
        current_time = self._format_time(position)
        duration = self._format_time(self.media_player.duration())
        self.time_label.setText(f"{current_time} / {duration}")

    def _on_duration_changed(self, duration: int):
        """视频时长变化"""
        self.progress_slider.setRange(0, duration)

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState):
        """播放状态变化"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.is_playing = True
            self.play_btn.setText("⏸")
        else:
            self.is_playing = False
            self.play_btn.setText("▶")

    def _on_media_error(self, error: QMediaPlayer.Error):
        """媒体播放错误"""
        error_message = f"播放错误: {error}"
        QMessageBox.critical(self, "播放错误", error_message)
        self.logger.error(error_message)

    def _on_slider_pressed(self):
        """滑块按下"""
        self.media_player.setPosition(self.progress_slider.value())

    def _on_slider_released(self):
        """滑块释放"""
        self.media_player.setPosition(self.progress_slider.value())

    def _on_slider_changed(self, value: int):
        """滑块值变化"""
        if self.progress_slider.isSliderDown():
            self.media_player.setPosition(value)

    def _on_volume_changed(self, value: int):
        """音量变化"""
        self.audio_output.setVolume(value / 100.0)

    def _on_zoom_changed(self, text: str):
        """缩放变化"""
        if text == "适应窗口":
            self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        else:
            try:
                scale = float(text.replace('%', '')) / 100.0
                # 这里可以实现具体的缩放逻辑
            except ValueError:
                pass

    def _format_time(self, milliseconds: int) -> str:
        """格式化时间"""
        if milliseconds < 0:
            return "00:00:00"

        seconds = milliseconds // 1000
        minutes = seconds // 60
        hours = minutes // 60

        seconds = seconds % 60
        minutes = minutes % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def keyPressEvent(self, event):
        """键盘事件处理"""
        if self.current_video_path is None:
            super().keyPressEvent(event)
            return

        # 空格键：播放/暂停
        if event.key() == Qt.Key.Key_Space:
            self._toggle_playback()
        # 左箭头：后退5秒
        elif event.key() == Qt.Key.Key_Left:
            new_position = max(0, self.media_player.position() - 5000)
            self.media_player.setPosition(new_position)
        # 右箭头：前进5秒
        elif event.key() == Qt.Key.Key_Right:
            new_position = min(self.media_player.duration(), self.media_player.position() + 5000)
            self.media_player.setPosition(new_position)
        # 上箭头：增加音量
        elif event.key() == Qt.Key.Key_Up:
            current_volume = self.volume_slider.value()
            new_volume = min(100, current_volume + 10)
            self.volume_slider.setValue(new_volume)
        # 下箭头：减少音量
        elif event.key() == Qt.Key.Key_Down:
            current_volume = self.volume_slider.value()
            new_volume = max(0, current_volume - 10)
            self.volume_slider.setValue(new_volume)
        # F键：全屏切换
        elif event.key() == Qt.Key.Key_F:
            self._toggle_fullscreen()
        # M键：静音切换
        elif event.key() == Qt.Key.Key_M:
            self._toggle_mute()
        # Home键：跳转到开始
        elif event.key() == Qt.Key.Key_Home:
            self.media_player.setPosition(0)
        # End键：跳转到结束
        elif event.key() == Qt.Key.Key_End:
            self.media_player.setPosition(self.media_player.duration())
        else:
            super().keyPressEvent(event)

    def cleanup(self):
        """清理资源"""
        if self.media_player:
            self.media_player.stop()
            self.media_player.setVideoOutput(None)
            self.media_player.setAudioOutput(None)
            self.media_player = None

        if self.audio_output:
            self.audio_output = None

        # 清理完成
class PropertiesPanel(QWidget):
    """属性面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 工具箱
        self.toolbox = QToolBox()
        self.toolbox.setStyleSheet("""
            QToolBox::tab {
                background: #2A2A2A;
                color: #B0B0B0;
                padding: 8px;
                border: 1px solid #3A3A3A;
            }
            QToolBox::tab:selected {
                background: #404040;
                color: #FFFFFF;
                border-bottom: 2px solid #00A8FF;
            }
        """)

        # 视频属性页
        self.video_props_page = QWidget()
        video_props_layout = QVBoxLayout(self.video_props_page)
        video_props_layout.setSpacing(10)

        # 基本信息
        info_group = QGroupBox("基本信息")
        info_layout = QFormLayout()

        self.resolution_label = QLabel("1920x1080")
        self.resolution_label.setStyleSheet("color: #B0B0B0;")

        self.duration_label = QLabel("00:05:30")
        self.duration_label.setStyleSheet("color: #B0B0B0;")

        self.fps_label = QLabel("30 fps")
        self.fps_label.setStyleSheet("color: #B0B0B0;")

        info_layout.addRow("分辨率:", self.resolution_label)
        info_layout.addRow("时长:", self.duration_label)
        info_layout.addRow("帧率:", self.fps_label)

        info_group.setLayout(info_layout)
        video_props_layout.addWidget(info_group)

        # 调整参数
        adjust_group = QGroupBox("调整参数")
        adjust_layout = QFormLayout()

        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)

        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)

        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)

        adjust_layout.addRow("亮度:", self.brightness_slider)
        adjust_layout.addRow("对比度:", self.contrast_slider)
        adjust_layout.addRow("饱和度:", self.saturation_slider)

        adjust_group.setLayout(adjust_layout)
        video_props_layout.addWidget(adjust_group)

        video_props_layout.addStretch()

        # AI增强页
        self.ai_enhance_page = QWidget()
        ai_layout = QVBoxLayout(self.ai_enhance_page)
        ai_layout.setSpacing(10)

        # AI功能按钮
        ai_buttons = [
            ("智能剪辑", "AI自动识别精彩片段"),
            ("AI降噪", "智能去除背景噪音"),
            ("自动字幕", "AI生成字幕文件"),
            ("画质增强", "AI提升视频清晰度")
        ]

        for btn_text, tooltip in ai_buttons:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2A2A2A;
                    color: #00A8FF;
                    border: 1px solid #00A8FF;
                    padding: 10px;
                    border-radius: 4px;
                    text-align: left;
                }
                QPushButton:hover {
                    background: #3A3A3A;
                }
            """)
            btn.setToolTip(tooltip)
            ai_layout.addWidget(btn)

        ai_layout.addStretch()

        # AI字幕页
        self.ai_subtitle_page = QWidget()
        subtitle_layout = QVBoxLayout(self.ai_subtitle_page)
        subtitle_layout.setSpacing(10)

        # 字幕设置
        subtitle_group = QGroupBox("字幕设置")
        subtitle_settings_layout = QFormLayout()

        self.subtitle_style_combo = QComboBox()
        self.subtitle_style_combo.addItems(["默认", "科技", "文艺", "复古"])

        self.subtitle_size_spin = QSpinBox()
        self.subtitle_size_spin.setRange(12, 48)
        self.subtitle_size_spin.setValue(24)

        self.subtitle_color_combo = QComboBox()
        self.subtitle_color_combo.addItems(["白色", "黄色", "黑色"])

        subtitle_settings_layout.addRow("字幕样式:", self.subtitle_style_combo)
        subtitle_settings_layout.addRow("字幕大小:", self.subtitle_size_spin)
        subtitle_settings_layout.addRow("字幕颜色:", self.subtitle_color_combo)

        subtitle_group.setLayout(subtitle_settings_layout)
        subtitle_layout.addWidget(subtitle_group)

        # 生成按钮
        self.generate_subtitle_btn = QPushButton(get_icon("subtitle", 16), "生成AI字幕")
        self.generate_subtitle_btn.setStyleSheet("""
            QPushButton {
                background: #00A8FF;
                color: #FFFFFF;
                border: none;
                padding: 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0090E6;
            }
        """)
        self.generate_subtitle_btn.setToolTip("使用AI技术自动生成视频字幕")
        subtitle_layout.addWidget(self.generate_subtitle_btn)

        subtitle_layout.addStretch()

        # 为字幕生成按钮设置属性以便查找
        self.generate_subtitle_btn.setProperty("ai_function", "subtitle_generation")

        # 添加页面到工具箱
        self.toolbox.addItem(self.video_props_page, "视频属性")
        self.toolbox.addItem(self.ai_enhance_page, "AI增强")
        self.toolbox.addItem(self.ai_subtitle_page, "AI字幕")

        layout.addWidget(self.toolbox)


class TimelinePanel(QWidget):
    """时间线面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_drag_drop()

    def setup_drag_drop(self):
        """设置拖放功能"""
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]

        if file_paths:
            self.logger.info(f"拖拽文件到时间线: {len(file_paths)} 个文件")
            # 这里可以实现文件添加到时间线的逻辑

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # AI编辑工具栏
        ai_toolbar = QHBoxLayout()

        ai_tools = [
            ("短剧解说", "AI生成短剧解说"),
            ("高能混剪", "智能混剪精彩片段"),
            ("第三人称解说", "生成第三人称解说")
        ]

        for tool_name, tooltip in ai_tools:
            btn = QPushButton(tool_name)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2A2A2A;
                    color: #00A8FF;
                    border: 1px solid #00A8FF;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #3A3A3A;
                }
            """)
            btn.setToolTip(tooltip)
            ai_toolbar.addWidget(btn)

        ai_toolbar.addStretch()

        layout.addLayout(ai_toolbar)

        # 时间线轨道
        self.timeline_widget = QWidget()
        self.timeline_widget.setMinimumHeight(150)
        self.timeline_widget.setStyleSheet("""
            QWidget {
                background: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
            }
        """)

        timeline_layout = QVBoxLayout(self.timeline_widget)

        # 时间标尺
        ruler = QFrame()
        ruler.setFixedHeight(30)
        ruler.setStyleSheet("""
            QFrame {
                background: #1A1A1A;
                border-bottom: 1px solid #3A3A3A;
            }
        """)

        ruler_layout = QHBoxLayout(ruler)
        ruler_layout.setContentsMargins(10, 5, 10, 5)

        # 添加时间刻度
        for i in range(0, 61, 10):
            time_label = QLabel(f"{i:02d}:00")
            time_label.setStyleSheet("color: #B0B0B0; font-size: 10px;")
            ruler_layout.addWidget(time_label)
            ruler_layout.addStretch()

        timeline_layout.addWidget(ruler)

        # 视频轨道
        video_track = QFrame()
        video_track.setFixedHeight(60)
        video_track.setStyleSheet("""
            QFrame {
                background: #1A1A1A;
                border: 1px solid #3A3A3A;
                border-radius: 2px;
            }
        """)

        video_track_layout = QHBoxLayout(video_track)
        video_track_layout.setContentsMargins(10, 5, 10, 5)

        track_label = QLabel("视频轨道")
        track_label.setStyleSheet("color: #B0B0B0;")
        video_track_layout.addWidget(track_label)

        video_track_layout.addStretch()

        timeline_layout.addWidget(video_track)

        # 音频轨道
        audio_track = QFrame()
        audio_track.setFixedHeight(40)
        audio_track.setStyleSheet(video_track.styleSheet())

        audio_track_layout = QHBoxLayout(audio_track)
        audio_track_layout.setContentsMargins(10, 5, 10, 5)

        audio_label = QLabel("音频轨道")
        audio_label.setStyleSheet("color: #B0B0B0;")
        audio_track_layout.addWidget(audio_label)

        audio_track_layout.addStretch()

        timeline_layout.addWidget(audio_track)

        timeline_layout.addStretch()

        layout.addWidget(self.timeline_widget)


class VideoEditorPage(BasePage):
    """视频编辑页面 - 根据截图实现的专业视频编辑器界面"""

    def __init__(self, application):
        super().__init__("video_editor", "视频编辑器", application)

        # 页面组件
        self.media_panel = None
        self.preview_panel = None
        self.properties_panel = None
        self.timeline_panel = None

        # 布局组件
        self.main_splitter = None
        self.center_splitter = None

        # AI服务
        self.ai_service = MockAIService()
        self.ai_service.processing_started.connect(self._on_ai_processing_started)
        self.ai_service.processing_progress.connect(self._on_ai_processing_progress)
        self.ai_service.processing_completed.connect(self._on_ai_processing_completed)
        self.ai_service.processing_error.connect(self._on_ai_processing_error)

        # 状态
        self.has_project = False
        self.current_video = None
        self.current_ai_task = None

    def initialize(self) -> bool:
        """初始化页面"""
        try:
            self.log_info("Initializing video editor page")
            return True
        except Exception as e:
            self.handle_error(e, "initialize")
            return False

    def create_content(self) -> None:
        """创建页面内容"""
        # 创建主分割器
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.add_widget_to_main_layout(self.main_splitter)

        # 创建左侧媒体库面板
        self.media_panel = MediaLibraryPanel()
        self.media_panel.setMinimumWidth(200)
        self.media_panel.setMaximumWidth(300)
        self.main_splitter.addWidget(self.media_panel)

        # 创建中央分割器
        self.center_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.center_splitter)

        # 创建预览面板
        self.preview_panel = PreviewPanel()
        self.preview_panel.logger = self.logger
        self.preview_panel.setMinimumHeight(400)
        self.center_splitter.addWidget(self.preview_panel)

        # 创建时间线面板
        self.timeline_panel = TimelinePanel()
        self.timeline_panel.logger = self.logger
        self.timeline_panel.setMinimumHeight(200)
        self.timeline_panel.setMaximumHeight(300)
        self.center_splitter.addWidget(self.timeline_panel)

        # 创建右侧属性面板
        self.properties_panel = PropertiesPanel()
        self.properties_panel.setMinimumWidth(250)
        self.properties_panel.setMaximumWidth(300)
        self.main_splitter.addWidget(self.properties_panel)

        # 设置分割器比例
        self.main_splitter.setStretchFactor(0, 1)  # 左侧媒体库
        self.main_splitter.setStretchFactor(1, 3)  # 中央预览和时间线
        self.main_splitter.setStretchFactor(2, 1)  # 右侧属性面板

        self.center_splitter.setStretchFactor(0, 3)  # 预览区域
        self.center_splitter.setStretchFactor(1, 1)  # 时间线区域

        # 设置分割器样式
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background: #2A2A2A;
                width: 2px;
            }
            QSplitter::handle:hover {
                background: #3A3A3A;
            }
        """)

        self.center_splitter.setStyleSheet("""
            QSplitter::handle {
                background: #2A2A2A;
                height: 2px;
            }
            QSplitter::handle:hover {
                background: #3A3A3A;
            }
        """)

        # 连接信号
        self._connect_component_signals()

        self.log_info("Video editor page content created")

    def _connect_component_signals(self) -> None:
        """连接组件信号"""
        if self.media_panel:
            self.media_panel.video_selected.connect(self._on_video_selected)
            self.media_panel.audio_selected.connect(self._on_audio_selected)
            self.media_panel.image_selected.connect(self._on_image_selected)

        if self.properties_panel:
            # 连接AI功能按钮信号
            self._connect_ai_signals()

        if self.timeline_panel:
            # 连接时间线工具栏信号
            self._connect_timeline_signals()

    def _connect_ai_signals(self):
        """连接AI功能信号"""
        # 智能剪辑
        if hasattr(self.properties_panel, 'ai_enhance_page'):
            ai_page = self.properties_panel.ai_enhance_page
            for i in range(ai_page.layout().count()):
                widget = ai_page.layout().itemAt(i).widget()
                if isinstance(widget, QPushButton):
                    if widget.text() == "智能剪辑":
                        widget.clicked.connect(self._apply_smart_editing)
                    elif widget.text() == "AI降噪":
                        widget.clicked.connect(self._apply_noise_reduction)
                    elif widget.text() == "自动字幕":
                        widget.clicked.connect(self._apply_auto_subtitle)
                    elif widget.text() == "画质增强":
                        widget.clicked.connect(self._apply_quality_enhancement)

        # 连接AI字幕生成按钮
        if hasattr(self.properties_panel, 'ai_subtitle_page'):
            subtitle_page = self.properties_panel.ai_subtitle_page
            for i in range(subtitle_page.layout().count()):
                widget = subtitle_page.layout().itemAt(i).widget()
                if isinstance(widget, QPushButton) and widget.property("ai_function") == "subtitle_generation":
                    widget.clicked.connect(self._apply_auto_subtitle)

    def _connect_timeline_signals(self):
        """连接时间线工具栏信号"""
        if hasattr(self.timeline_panel, 'ai_toolbar'):
            timeline_layout = self.timeline_panel.layout()
            if timeline_layout:
                toolbar_item = timeline_layout.itemAt(0)
                if toolbar_item:
                    toolbar_layout = toolbar_item.layout()
                    if toolbar_layout:
                        for i in range(toolbar_layout.count()):
                            widget = toolbar_layout.itemAt(i).widget()
                            if isinstance(widget, QPushButton):
                                if widget.text() == "短剧解说":
                                    widget.clicked.connect(self._apply_drama_commentary)
                                elif widget.text() == "高能混剪":
                                    widget.clicked.connect(self._apply_highlight_mix)
                                elif widget.text() == "第三人称解说":
                                    widget.clicked.connect(self._apply_third_person_commentary)

    def _on_video_selected(self, video_path: str) -> None:
        """视频选中处理"""
        self.current_video = video_path
        self.update_status(f"已选择视频: {os.path.basename(video_path)}")

        # 加载视频到预览器
        if self.preview_panel:
            success = self.preview_panel.load_video(video_path)
            if not success:
                self.show_error("视频加载失败")

    def _on_audio_selected(self, audio_path: str) -> None:
        """音频选中处理"""
        self.update_status(f"已选择音频: {os.path.basename(audio_path)}")
        # 这里可以实现音频播放逻辑

    def _on_image_selected(self, image_path: str) -> None:
        """图片选中处理"""
        self.update_status(f"已选择图片: {os.path.basename(image_path)}")
        # 这里可以实现图片预览逻辑

    # AI功能实现
    def _apply_smart_editing(self):
        """智能剪辑"""
        if not self.current_video:
            self.show_error("请先选择视频文件")
            return

        try:
            self.current_ai_task = "智能剪辑"
            self.update_status("正在执行智能剪辑...")
            self.show_progress_dialog("智能剪辑", "正在分析视频内容并生成智能剪辑方案...")
            self.ai_service.smart_editing(self.current_video, self._on_ai_result)
        except Exception as e:
            self.handle_ai_error("智能剪辑", e)
            self.close_progress_dialog()

    def _apply_noise_reduction(self):
        """AI降噪"""
        if not self.current_video:
            self.show_error("请先选择视频文件")
            return

        try:
            self.current_ai_task = "AI降噪"
            self.update_status("正在执行AI降噪...")
            self.show_progress_dialog("AI降噪", "正在分析音频并去除背景噪声...")
            self.ai_service.reduce_noise(self.current_video, self._on_ai_result)
        except Exception as e:
            self.handle_ai_error("AI降噪", e)
            self.close_progress_dialog()

    def _apply_auto_subtitle(self):
        """自动字幕"""
        if not self.current_video:
            self.show_error("请先选择视频文件")
            return

        try:
            self.current_ai_task = "自动字幕"
            self.update_status("正在生成自动字幕...")
            self.show_progress_dialog("自动字幕", "正在分析语音并生成字幕...")
            self.ai_service.generate_subtitle(self.current_video, "zh", self._on_ai_result)
        except Exception as e:
            self.handle_ai_error("自动字幕", e)
            self.close_progress_dialog()

    def _apply_quality_enhancement(self):
        """画质增强"""
        if not self.current_video:
            self.show_error("请先选择视频文件")
            return

        try:
            self.current_ai_task = "画质增强"
            self.update_status("正在执行画质增强...")
            self.show_progress_dialog("画质增强", "正在提升视频画质和清晰度...")
            self.ai_service.enhance_quality(self.current_video, "medium", self._on_ai_result)
        except Exception as e:
            self.handle_ai_error("画质增强", e)
            self.close_progress_dialog()

    def _apply_drama_commentary(self):
        """短剧解说"""
        if not self.current_video:
            self.show_error("请先选择视频文件")
            return

        try:
            self.current_ai_task = "短剧解说"
            self.update_status("正在生成短剧解说...")
            self.show_progress_dialog("短剧解说", "正在分析视频内容并生成短剧解说...")
            self.ai_service.generate_commentary(self.current_video, "drama", self._on_ai_result)
        except Exception as e:
            self.handle_ai_error("短剧解说", e)
            self.close_progress_dialog()

    def _apply_highlight_mix(self):
        """高能混剪"""
        if not self.current_video:
            self.show_error("请先选择视频文件")
            return

        try:
            self.current_ai_task = "高能混剪"
            self.update_status("正在执行高能混剪...")
            self.show_progress_dialog("高能混剪", "正在分析视频高光片段并生成混剪...")
            self.ai_service.generate_commentary(self.current_video, "highlight", self._on_ai_result)
        except Exception as e:
            self.handle_ai_error("高能混剪", e)
            self.close_progress_dialog()

    def _apply_third_person_commentary(self):
        """第三人称解说"""
        if not self.current_video:
            self.show_error("请先选择视频文件")
            return

        try:
            self.current_ai_task = "第三人称解说"
            self.update_status("正在生成第三人称解说...")
            self.show_progress_dialog("第三人称解说", "正在分析视频内容并生成第三人称解说...")
            self.ai_service.generate_commentary(self.current_video, "third_person", self._on_ai_result)
        except Exception as e:
            self.handle_ai_error("第三人称解说", e)
            self.close_progress_dialog()

    # AI服务回调
    def _on_ai_processing_started(self, task_name: str):
        """AI处理开始"""
        self.update_status(f"开始{task_name}...")
        self._show_ai_progress_dialog(task_name)

    def _on_ai_processing_progress(self, task_name: str, progress: int):
        """AI处理进度"""
        self.update_status(f"{task_name}进度: {progress}%")
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setValue(progress)

    def _on_ai_processing_completed(self, task_name: str, result: str):
        """AI处理完成"""
        self.update_status(f"{task_name}完成")
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        QMessageBox.information(self, "完成", f"{task_name}已完成！\n结果: {result}")

    def _on_ai_processing_error(self, task_name: str, error: str):
        """AI处理错误"""
        self.update_status(f"{task_name}失败")
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        QMessageBox.critical(self, "错误", f"{task_name}失败: {error}")

    def show_progress_dialog(self, title: str, message: str):
        """显示进度对话框"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()

        from PyQt6.QtWidgets import QProgressDialog
        self.progress_dialog = QProgressDialog(message, "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle(title)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(500)
        self.progress_dialog.canceled.connect(self._on_progress_canceled)
        self.progress_dialog.show()

    def close_progress_dialog(self):
        """关闭进度对话框"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def _on_progress_canceled(self):
        """进度对话框取消"""
        if hasattr(self, 'ai_service') and self.ai_service:
            self.ai_service.cancel_processing()
        self.update_status("操作已取消")

    def handle_ai_error(self, task_name: str, error: Exception):
        """处理AI错误"""
        error_msg = f"{task_name}失败: {str(error)}"
        self.log_error(error_msg)
        self.show_error(error_msg)
        self.close_progress_dialog()

    def _on_ai_result(self, result):
        """AI处理结果回调"""
        if isinstance(result, dict) and "error" in result:
            self.show_error(result["error"])
        else:
            self.update_status("AI处理完成")

    def _show_ai_progress_dialog(self, task_name: str):
        """显示AI处理进度对话框"""
        from PyQt6.QtWidgets import QProgressDialog

        self.progress_dialog = QProgressDialog(f"正在{task_name}...", "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle("AI处理")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.canceled.connect(self._cancel_ai_processing)
        self.progress_dialog.show()

    def _cancel_ai_processing(self):
        """取消AI处理"""
        if self.ai_service:
            self.ai_service.cancel_processing()
        self.update_status("AI处理已取消")

    def _on_project_opened(self, project_path: str) -> None:
        """项目打开处理"""
        self.has_project = True
        self.update_status(f"已打开项目: {os.path.basename(project_path)}")

    def new_project(self) -> None:
        """新建项目"""
        self.has_project = True
        self.current_video = None
        self.update_status("新建项目")

    def open_project(self, project_path: str) -> None:
        """打开项目"""
        self.has_project = True
        self.update_status(f"打开项目: {os.path.basename(project_path)}")

    def save_project(self) -> None:
        """保存项目"""
        if not self.has_project:
            self.show_error("没有打开的项目")
            return
        self.update_status("保存项目")

    def save_project_as(self, project_path: str) -> None:
        """项目另存为"""
        self.has_project = True
        self.update_status(f"项目另存为: {os.path.basename(project_path)}")

    def import_media(self, file_paths: List[str]) -> None:
        """导入媒体"""
        self.update_status(f"导入了 {len(file_paths)} 个媒体文件")

    def export_video(self, export_path: str) -> None:
        """导出视频"""
        if not self.has_project:
            self.show_error("没有打开的项目")
            return
        self.update_status("导出视频")

    def export_to_jianying(self, project_path: str) -> None:
        """导出到剪映"""
        if not self.has_project:
            self.show_error("没有打开的项目")
            return
        self.update_status("导出到剪映项目")

    def apply_ai_analysis(self) -> None:
        """应用AI分析"""
        if not self.current_video:
            self.show_error("没有选择视频")
            return
        self.update_status("AI视频分析中...")

    def apply_ai_subtitle(self) -> None:
        """应用AI字幕"""
        if not self.current_video:
            self.show_error("没有选择视频")
            return
        self.update_status("AI字幕生成中...")

    def apply_ai_voiceover(self) -> None:
        """应用AI配音"""
        if not self.current_video:
            self.show_error("没有选择视频")
            return
        self.update_status("AI配音生成中...")

    def apply_ai_enhance(self) -> None:
        """应用AI增强"""
        if not self.current_video:
            self.show_error("没有选择视频")
            return
        self.update_status("AI画质增强中...")

    def save_state(self) -> None:
        """保存页面状态"""
        self.page_state = {
            'has_project': self.has_project,
            'current_video': self.current_video,
            'splitter_sizes': self.main_splitter.sizes() if self.main_splitter else [],
            'center_splitter_sizes': self.center_splitter.sizes() if self.center_splitter else []
        }

    def restore_state(self) -> None:
        """恢复页面状态"""
        if 'has_project' in self.page_state:
            self.has_project = self.page_state['has_project']

        if 'current_video' in self.page_state:
            self.current_video = self.page_state['current_video']

        if 'splitter_sizes' in self.page_state and self.main_splitter:
            sizes = self.page_state['splitter_sizes']
            if sizes and len(sizes) == 3:
                self.main_splitter.setSizes(sizes)

        if 'center_splitter_sizes' in self.page_state and self.center_splitter:
            sizes = self.page_state['center_splitter_sizes']
            if sizes and len(sizes) == 2:
                self.center_splitter.setSizes(sizes)

    def cleanup(self) -> None:
        """清理资源"""
        pass

    def handle_shortcut(self, key_sequence: str) -> bool:
        """处理快捷键"""
        if key_sequence == "Ctrl+N":
            self.new_project()
            return True
        elif key_sequence == "Ctrl+O":
            self.request_action("open_project")
            return True
        elif key_sequence == "Ctrl+S":
            self.save_project()
            return True
        elif key_sequence == "Ctrl+I":
            self.request_action("import_media")
            return True
        elif key_sequence == "Ctrl+E":
            self.request_action("export_video")
            return True
        return False

    def get_current_video(self) -> Optional[str]:
        """获取当前视频"""
        return self.current_video

    def has_active_project(self) -> bool:
        """检查是否有活动项目"""
        return self.has_project

    def _on_application_state_changed(self, state) -> None:
        """应用程序状态变化处理"""
        pass

    def _on_config_changed(self, key: str, value) -> None:
        """配置变化处理"""
        if key.startswith("video_editor."):
            pass
        elif key.startswith("theme."):
            self._update_theme()

    def _update_theme(self) -> None:
        """更新主题"""
        pass