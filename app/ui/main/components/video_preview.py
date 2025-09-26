"""
视频预览组件
支持实际视频播放、控制和位置更新
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QVideoWidget, QSlider, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt, QMediaPlayer, QMediaContent, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget


class VideoPreview(QWidget):
    """视频预览组件"""

    # 信号定义
    playback_position_changed = pyqtSignal(int)
    playback_state_changed = pyqtSignal(bool)  # playing or paused

    def __init__(self, application):
        super().__init__()
        self.application = application
        self.current_video = None
        self.media_player = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.play_button = QPushButton("播放")
        self.status_label = QLabel("就绪")

        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.stateChanged.connect(self.state_changed)
        self.media_player.mediaStatusChanged.connect(self.media_status_changed)

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 视频显示区域
        layout.addWidget(self.video_widget)

        # 控制区域
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.status_label)

        # 进度条
        self.position_slider.setRange(0, 0)
        control_layout.addWidget(self.position_slider)

        # 控制按钮
        button_layout = QHBoxLayout()
        self.play_button.setIcon(QIcon("resources/icons/play.png"))  # 假设图标存在
        button_layout.addWidget(self.play_button)
        pause_button = QPushButton("暂停")
        pause_button.setIcon(QIcon("resources/icons/pause.png"))
        button_layout.addWidget(pause_button)
        control_layout.addLayout(button_layout)

        layout.addLayout(control_layout)

        self.update_theme()

    def _setup_connections(self):
        """设置信号连接"""
        self.position_slider.sliderMoved.connect(self.set_position)
        self.play_button.clicked.connect(self.play)
        pause_button = self.findChild(QPushButton, "暂停")  # 假设命名
        if pause_button:
            pause_button.clicked.connect(self.pause)

    def load_video(self, video_path: str):
        """加载视频"""
        if self.current_video == video_path:
            return
        self.current_video = video_path
        media_content = QMediaContent(QUrl.fromLocalFile(video_path))
        self.media_player.setMedia(media_content)
        self.status_label.setText(f"加载: {os.path.basename(video_path)}")

    def play(self):
        """播放"""
        self.media_player.play()
        self.play_button.setText("暂停")
        self.playback_state_changed.emit(True)

    def pause(self):
        """暂停"""
        self.media_player.pause()
        self.play_button.setText("播放")
        self.playback_state_changed.emit(False)

    def set_position(self, position: int):
        """设置位置"""
        self.media_player.setPosition(position)

    def position_changed(self, position: int):
        """位置变化"""
        self.position_slider.setValue(position)
        self.playback_position_changed.emit(position)

    def duration_changed(self, duration: int):
        """持续时间变化"""
        self.position_slider.setRange(0, duration)

    def state_changed(self, state):
        """状态变化"""
        if state == QMediaPlayer.PlayingState:
            self.status_label.setText("播放中")
        else:
            self.status_label.setText("暂停")

    def media_status_changed(self, status):
        """媒体状态变化"""
        statuses = {
            QMediaPlayer.LoadedMedia: "加载完成",
            QMediaPlayer.BufferingMedia: "缓冲中",
            QMediaPlayer.EndOfMedia: "结束",
            QMediaPlayer.InvalidMedia: "无效媒体"
        }
        self.status_label.setText(statuses.get(status, "未知状态"))

    def cleanup(self):
        """清理资源"""
        self.media_player.stop()
        self.media_player.setMedia(QMediaContent())

    def update_theme(self, is_dark: bool = True):
        """更新主题"""
        if is_dark:
            self.setStyleSheet("""
                QVideoWidget { background-color: #2D2D2D; }
                QSlider { background-color: #3D3D3D; }
                QPushButton { background-color: #4D4D4D; color: white; }
                QLabel { color: white; }
            """)
        else:
            self.setStyleSheet("")
