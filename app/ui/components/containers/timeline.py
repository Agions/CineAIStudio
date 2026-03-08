#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时间轴组件
视频剪辑时间轴
"""

from typing import List, Optional, Callable, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QSlider, QMenu,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QMouseEvent, QPaintEvent


class TimelineClip:
    """时间轴片段"""
    
    def __init__(
        self,
        clip_id: str,
        name: str,
        start: float,
        duration: float,
        color: str = "#7C3AED",
    ):
        self.id = clip_id
        self.name = name
        self.start = start      # 开始时间(秒)
        self.duration = duration  # 持续时间(秒)
        self.end = start + duration
        self.color = color
        self.thumbnail: Optional[QPixmap] = None
        self.muted = False
        self.locked = False
        self.selected = False
    
    @property
    def position(self) -> float:
        return self.start


class TimelineTrack:
    """时间轴轨道"""
    
    def __init__(self, track_id: str, name: str, track_type: str = "video"):
        self.id = track_id
        self.name = name
        self.track_type = track_type  # video/audio
        self.clips: List[TimelineClip] = []
        self.muted = False
        self.hidden = False
        self.height = 60
    
    def add_clip(self, clip: TimelineClip):
        """添加片段"""
        self.clips.append(clip)
        self.clips.sort(key=lambda c: c.start)
    
    def remove_clip(self, clip_id: str) -> bool:
        """移除片段"""
        for i, clip in enumerate(self.clips):
            if clip.id == clip_id:
                self.clips.pop(i)
                return True
        return False
    
    def get_clip_at(self, time: float) -> Optional[TimelineClip]:
        """获取指定时间的片段"""
        for clip in self.clips:
            if clip.start <= time < clip.end:
                return clip
        return None


class TimelineRuler(QWidget):
    """时间轴标尺"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 60.0  # 总时长(秒)
        self._pixels_per_second = 50  # 像素/秒
        self._scroll_offset = 0
        self.setFixedHeight(30)
    
    def set_duration(self, duration: float):
        self._duration = duration
        self.update()
    
    def set_zoom(self, pixels_per_second: float):
        self._pixels_per_second = pixels_per_second
        self.update()
    
    def set_scroll(self, offset: float):
        self._scroll_offset = offset
        self.update()
    
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 背景
        painter.fillRect(self.rect(), QColor("#1C1C28"))
        
        # 刻度
        pen = QPen(QColor("#6B7280"))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 主刻度 (每秒)
        for sec in range(int(self._duration) + 1):
            x = sec * self._pixels_per_second - self._scroll_offset
            
            if x < 0 or x > self.width():
                continue
            
            # 整秒刻度
            if sec % 10 == 0:
                # 长刻度
                painter.drawLine(x, 10, x, 30)
                # 时间标签
                time_text = f"{sec//60:02d}:{sec%60:02d}"
                painter.drawText(x + 2, 20, time_text)
            elif sec % 5 == 0:
                # 中刻度
                painter.drawLine(x, 18, x, 30)
            else:
                # 短刻度
                painter.drawLine(x, 22, x, 30)


class TimelineClipWidget(QFrame):
    """时间轴片段组件"""
    
    clicked = pyqtSignal(str)  # clip_id
    double_clicked = pyqtSignal(str)
    
    def __init__(self, clip: TimelineClip, parent=None):
        super().__init__(parent)
        self._clip = clip
        self._init_ui()
    
    def _init_ui(self):
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background: {self._clip.color};
                border-radius: 4px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
            QFrame:hover {{
                border: 1px solid rgba(255,255,255,0.3);
            }}
        """)
        
        # 片段名称
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        
        name_label = QLabel(self._clip.name)
        name_label.setStyleSheet("color: white; font-size: 11px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(name_label)
        
        # 时长
        duration_label = QLabel(f"{self._clip.duration:.1f}s")
        duration_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 10px;")
        layout.addWidget(duration_label)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._clip.id)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.double_clicked.emit(self._clip.id)
        super().mouseDoubleClickEvent(event)


class TimelineTrackWidget(QFrame):
    """时间轴轨道组件"""
    
    clip_clicked = pyqtSignal(str)  # clip_id
    
    def __init__(self, track: TimelineTrack, parent=None):
        super().__init__(parent)
        self._track = track
        self._pixels_per_second = 50
        self._scroll_offset = 0
        self._clip_widgets: Dict[str, TimelineClipWidget] = {}
        self._init_ui()
    
    def _init_ui(self):
        self.setFixedHeight(self._track.height)
        self.setStyleSheet("""
            QFrame {
                background:, 28, 40, 0.5);
 rgba(28                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
        """)
        
        # 轨道标签
        label = QLabel(self._track.name)
        label.setFixedWidth(80)
        label.setStyleSheet("color: #A1A4B3; font-size: 12px;")
        
        # 片段区域
        self._clips_area = QFrame()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.addWidget(self._clips_area, 1)
    
    def set_zoom(self, pixels_per_second: float):
        self._pixels_per_second = pixels_per_second
        self._update_clips()
    
    def set_scroll(self, offset: float):
        self._scroll_offset = offset
        self._update_clips()
    
    def add_clip_widget(self, clip: TimelineClip):
        """添加片段组件"""
        widget = TimelineClipWidget(clip)
        widget.clicked.connect(self.clip_clicked.emit)
        widget.setFixedHeight(self._track.height - 4)
        
        x = clip.start * self._pixels_per_second - self._scroll_offset
        width = clip.duration * self._pixels_per_second
        
        widget.setGeometry(x, 2, width, self._track.height - 4)
        widget.show()
        
        self._clip_widgets[clip.id] = widget
    
    def _update_clips(self):
        """更新片段位置"""
        for clip_id, widget in self._clip_widgets.items():
            clip = next((c for c in self._track.clips if c.id == clip_id), None)
            if clip:
                x = clip.start * self._pixels_per_second - self._scroll_offset
                width = clip.duration * self._pixels_per_second
                widget.setGeometry(x, 2, width, self._track.height - 4)


class TimelineWidget(QWidget):
    """时间轴组件"""
    
    # 信号
    position_changed = pyqtSignal(float)  # 当前位置(秒)
    clip_selected = pyqtSignal(str)      # 选中的片段
    clip_double_clicked = pyqtSignal(str)  # 双击片段
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._duration = 60.0  # 总时长
        self._current_position = 0.0  # 当前播放位置
        self._pixels_per_second = 50  # 缩放
        self._scroll_offset = 0
        
        self._tracks: List[TimelineTrack] = []
        self._track_widgets: List[TimelineTrackWidget] = []
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标尺
        self._ruler = TimelineRuler()
        layout.addWidget(self._ruler)
        
        # 轨道区域 (可滚动)
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        
        self._tracks_container = QFrame()
        self._tracks_layout = QVBoxLayout(self._tracks_container)
        self._tracks_layout.setSpacing(0)
        self._tracks_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self._tracks_container)
        layout.addWidget(scroll)
        
        # 播放头
        self._playhead_x = 0
    
    # ===== 公共方法 =====
    
    def set_duration(self, duration: float):
        """设置总时长"""
        self._duration = duration
        self._ruler.set_duration(duration)
        self.update()
    
    def set_position(self, position: float):
        """设置当前位置"""
        self._current_position = position
        self.position_changed.emit(position)
        self.update()
    
    def add_track(self, track: TimelineTrack):
        """添加轨道"""
        self._tracks.append(track)
        
        # 创建轨道组件
        track_widget = TimelineTrackWidget(track)
        track_widget.clip_clicked.connect(self.clip_selected.emit)
        track_widget.clip_double_clicked.connect(self.clip_double_clicked.emit)
        
        self._tracks_layout.addWidget(track_widget)
        self._track_widgets.append(track_widget)
    
    def add_clip(self, track_id: str, clip: TimelineClip):
        """添加片段"""
        track = next((t for t in self._tracks if t.id == track_id), None)
        if track:
            track.add_clip(clip)
            
            # 添加片段组件
            track_widget = next((w for w in self._track_widgets if w._track.id == track_id), None)
            if track_widget:
                track_widget.add_clip_widget(clip)
    
    def set_zoom(self, pixels_per_second: float):
        """设置缩放"""
        self._pixels_per_second = pixels_per_second
        self._ruler.set_zoom(pixels_per_second)
        
        for track_widget in self._track_widgets:
            track_widget.set_zoom(pixels_per_second)
    
    def scroll_to_position(self, position: float):
        """滚动到指定位置"""
        x = position * self._pixels_per_second
        # TODO: 实现滚动
        self._ruler.set_scroll(x)
    
    # ===== 属性 =====
    
    @property
    def duration(self) -> float:
        return self._duration
    
    @property
    def position(self) -> float:
        return self._current_position
    
    @property
    def tracks(self) -> List[TimelineTrack]:
        return self._tracks


__all__ = [
    "TimelineClip",
    "TimelineTrack",
    "TimelineRuler",
    "TimelineTrackWidget",
    "TimelineClipWidget",
    "TimelineWidget",
]
