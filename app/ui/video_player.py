#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QStyle, QSizePolicy,
    QToolButton, QFrame, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class VideoPlayer(QWidget):
    """视频播放器组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建媒体播放器
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # 连接播放器信号
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status_changed)
        self.media_player.playbackStateChanged.connect(self.handle_playback_state_changed)
        self.media_player.errorOccurred.connect(self.handle_error)
        
        # 创建UI组件
        self.init_ui()
        
        # 设置定时器用于帧进帧退
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self.go_to_next_frame)
        self.frame_step_size = 33  # 默认约为30fps (1000ms / 30 ≈ 33ms)
        
        # 初始播放速度为1.0倍速
        self.playback_speed = 1.0
        
        # 添加标记列表
        self.markers = []
    
    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频显示区域
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        
        # 视频控制区域
        controls_layout = QVBoxLayout()
        
        # 播放进度条
        position_layout = QHBoxLayout()
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.sliderPressed.connect(self.on_slider_pressed)
        self.position_slider.sliderReleased.connect(self.on_slider_released)
        
        self.position_label = QLabel("00:00 / 00:00")
        self.position_label.setMinimumWidth(120)
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        position_layout.addWidget(self.position_slider)
        position_layout.addWidget(self.position_label)
        
        # 播放控制按钮
        buttons_layout = QHBoxLayout()
        
        # 帧退按钮
        self.frame_back_button = QToolButton()
        self.frame_back_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward))
        self.frame_back_button.setToolTip("帧退 (左箭头)")
        self.frame_back_button.clicked.connect(self.go_to_previous_frame)
        
        # 上一关键帧按钮
        self.prev_keyframe_button = QToolButton()
        self.prev_keyframe_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekBackward))
        self.prev_keyframe_button.setToolTip("上一关键帧")
        self.prev_keyframe_button.clicked.connect(self.go_to_previous_keyframe)
        
        # 播放/暂停按钮
        self.play_button = QToolButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.setToolTip("播放/暂停 (空格)")
        self.play_button.clicked.connect(self.toggle_play)
        
        # 下一关键帧按钮
        self.next_keyframe_button = QToolButton()
        self.next_keyframe_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward))
        self.next_keyframe_button.setToolTip("下一关键帧")
        self.next_keyframe_button.clicked.connect(self.go_to_next_keyframe)
        
        # 帧进按钮
        self.frame_forward_button = QToolButton()
        self.frame_forward_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))
        self.frame_forward_button.setToolTip("帧进 (右箭头)")
        self.frame_forward_button.clicked.connect(self.go_to_next_frame)
        
        # 设置按钮大小
        for button in [self.frame_back_button, self.prev_keyframe_button, 
                        self.play_button, self.next_keyframe_button, 
                        self.frame_forward_button]:
            button.setFixedSize(30, 30)
        
        # 播放速度下拉框
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self.change_playback_speed)
        self.speed_combo.setFixedWidth(70)
        
        # 音量控制
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)  # 默认音量50%
        self.volume_slider.setFixedWidth(70)
        self.volume_slider.valueChanged.connect(self.change_volume)
        
        # 标记按钮
        self.mark_button = QToolButton()
        self.mark_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.mark_button.setToolTip("添加标记 (M)")
        self.mark_button.clicked.connect(self.add_marker)
        
        # 截图按钮
        self.snapshot_button = QToolButton()
        self.snapshot_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.snapshot_button.setToolTip("截图 (S)")
        self.snapshot_button.clicked.connect(self.take_snapshot)
        
        # 添加按钮到布局
        buttons_layout.addWidget(self.frame_back_button)
        buttons_layout.addWidget(self.prev_keyframe_button)
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.next_keyframe_button)
        buttons_layout.addWidget(self.frame_forward_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(QLabel("播放速度:"))
        buttons_layout.addWidget(self.speed_combo)
        buttons_layout.addSpacing(10)
        buttons_layout.addWidget(QLabel("音量:"))
        buttons_layout.addWidget(self.volume_slider)
        buttons_layout.addSpacing(10)
        buttons_layout.addWidget(self.mark_button)
        buttons_layout.addWidget(self.snapshot_button)
        
        # 添加到控制布局
        controls_layout.addLayout(position_layout)
        controls_layout.addLayout(buttons_layout)
        
        # 创建视频信息标签
        self.info_label = QLabel("未加载视频")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("background-color: #222; color: #eee; padding: 8px;")
        
        # 设置视频区域
        video_container = QVBoxLayout()
        video_container.addWidget(self.video_widget)
        video_container.addWidget(self.info_label)
        
        main_layout.addLayout(video_container)
        main_layout.addLayout(controls_layout)
        
        # 设置视频区域和控制区域的比例
        main_layout.setStretch(0, 10)  # 视频区域占比较大
        main_layout.setStretch(1, 1)   # 控制区域占比较小
        
        # 设置初始状态
        self.change_volume(50)
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key.Key_Space:
            self.toggle_play()
        elif event.key() == Qt.Key.Key_Left:
            self.go_to_previous_frame()
        elif event.key() == Qt.Key.Key_Right:
            self.go_to_next_frame()
        elif event.key() == Qt.Key.Key_M:
            self.add_marker()
        elif event.key() == Qt.Key.Key_S:
            self.take_snapshot()
        elif event.key() == Qt.Key.Key_Up:
            self.change_volume(self.volume_slider.value() + 5)
        elif event.key() == Qt.Key.Key_Down:
            self.change_volume(self.volume_slider.value() - 5)
        else:
            super().keyPressEvent(event)
    
    def load_video(self, file_path):
        """加载视频文件"""
        if not os.path.exists(file_path):
            self.info_label.setText(f"错误: 文件不存在 - {file_path}")
            return False
        
        # 设置媒体源
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        
        # 更新UI
        self.video_file_path = file_path
        self.video_filename = os.path.basename(file_path)
        self.info_label.setText(f"已加载: {self.video_filename}")
        
        # 重置播放速度
        self.speed_combo.setCurrentText("1.0x")
        self.playback_speed = 1.0
        
        # 清空标记
        self.markers = []
        
        return True
    
    def play(self):
        """播放视频"""
        if self.media_player.source().isEmpty():
            return
        
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            return
            
        self.media_player.play()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
    
    def pause(self):
        """暂停视频"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            return
            
        self.media_player.pause()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
    
    def toggle_play(self):
        """播放/暂停切换"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()
    
    def stop(self):
        """停止播放"""
        self.media_player.stop()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
    
    def set_position(self, position):
        """设置播放位置"""
        self.media_player.setPosition(position)
    
    def update_position(self, position):
        """更新播放位置"""
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        
        self.update_position_label(position)
    
    def update_duration(self, duration):
        """更新视频时长"""
        self.position_slider.setRange(0, duration)
        self.update_position_label(self.media_player.position())
    
    def update_position_label(self, position):
        """更新时间标签显示"""
        duration = self.media_player.duration()
        
        position_str = self.format_time(position)
        duration_str = self.format_time(duration)
        
        self.position_label.setText(f"{position_str} / {duration_str}")
    
    def on_slider_pressed(self):
        """进度条按下处理"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.was_playing = True
        else:
            self.was_playing = False
    
    def on_slider_released(self):
        """进度条释放处理"""
        position = self.position_slider.value()
        self.media_player.setPosition(position)
        
        if self.was_playing:
            self.media_player.play()
    
    def change_volume(self, volume):
        """调整音量"""
        self.volume_slider.setValue(volume)
        self.audio_output.setVolume(volume / 100.0)
    
    def change_playback_speed(self, speed_text):
        """改变播放速度"""
        speed = float(speed_text.rstrip('x'))
        self.playback_speed = speed
        self.media_player.setPlaybackRate(speed)
    
    def go_to_previous_frame(self):
        """帧退"""
        # 确保视频已暂停
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        
        # 计算帧退的位置
        current_position = self.media_player.position()
        new_position = max(0, current_position - self.frame_step_size)
        
        # 设置新位置
        self.media_player.setPosition(new_position)
    
    def go_to_next_frame(self):
        """帧进"""
        # 确保视频已暂停
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        
        # 计算帧进的位置
        current_position = self.media_player.position()
        duration = self.media_player.duration()
        new_position = min(duration, current_position + self.frame_step_size)
        
        # 设置新位置
        self.media_player.setPosition(new_position)
    
    def go_to_previous_keyframe(self):
        """跳转到上一个关键帧"""
        # TODO: 实现关键帧跳转功能
        # 注意：这需要集成FFmpeg或其他库来提取关键帧信息
        self.info_label.setText("关键帧跳转功能尚未实现")
    
    def go_to_next_keyframe(self):
        """跳转到下一个关键帧"""
        # TODO: 实现关键帧跳转功能
        self.info_label.setText("关键帧跳转功能尚未实现")
    
    def add_marker(self):
        """添加时间标记"""
        current_position = self.media_player.position()
        
        # 添加到标记列表
        self.markers.append(current_position)
        self.markers.sort()
        
        # 显示通知
        position_str = self.format_time(current_position)
        self.info_label.setText(f"已添加标记: {position_str}")
    
    def take_snapshot(self):
        """截取当前帧为图片"""
        if not hasattr(self, 'video_file_path') or not self.video_file_path:
            return
        
        # 获取截图保存路径
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("图片文件 (*.png *.jpg)")
        file_dialog.setDefaultSuffix("png")
        
        # 设置建议的文件名称
        file_name = os.path.splitext(self.video_filename)[0]
        position_str = self.format_time(self.media_player.position()).replace(':', '-')
        suggested_name = f"{file_name}_frame_{position_str}.png"
        file_dialog.selectFile(suggested_name)
        
        if file_dialog.exec():
            save_path = file_dialog.selectedFiles()[0]
            
            # TODO: 实现截图功能
            # 注意：这需要使用OpenCV或FFmpeg来截取当前帧
            self.info_label.setText(f"截图功能尚未实现，将保存到: {save_path}")
    
    def handle_media_status_changed(self, status):
        """媒体状态变化处理"""
        # 处理各种媒体状态变化
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # 媒体已加载
            video_info = self.get_video_info()
            self.info_label.setText(video_info)
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            # 播放结束
            self.stop()
            self.info_label.setText("播放结束")
    
    def handle_playback_state_changed(self, state):
        """播放状态变化处理"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
    
    def handle_error(self, error, error_string):
        """错误处理"""
        self.info_label.setText(f"错误: {error_string}")
    
    def get_video_info(self):
        """获取视频信息"""
        if hasattr(self, 'video_filename'):
            duration = self.format_time(self.media_player.duration())
            return f"{self.video_filename} | 时长: {duration}"
        return "未加载视频"
    
    def format_time(self, ms):
        """将毫秒转换为时:分:秒格式"""
        if ms <= 0:
            return "00:00"
        
        s = ms // 1000
        m = s // 60
        h = m // 60
        
        if h > 0:
            return f"{h:02d}:{m%60:02d}:{s%60:02d}"
        else:
            return f"{m:02d}:{s%60:02d}" 