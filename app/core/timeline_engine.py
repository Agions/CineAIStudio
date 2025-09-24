#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 时间线引擎模块
专业级时间线管理系统，支持多轨道编辑、关键帧动画、实时播放和音频可视化
"""

import os
import time
import threading
import uuid
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import copy
import weakref
from contextlib import contextmanager

from .logger import get_logger
from .event_system import EventBus
from .service_container import ServiceContainer
from .video_engine import get_video_engine, EngineState
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import VideoInfo, get_ffmpeg_utils


class TrackType(Enum):
    """轨道类型枚举"""
    VIDEO = "video"
    AUDIO = "audio"
    EFFECTS = "effects"
    SUBTITLE = "subtitle"
    TRANSITION = "transition"


class ClipState(Enum):
    """剪辑状态枚举"""
    NORMAL = "normal"
    SELECTED = "selected"
    DRAGGING = "dragging"
    RESIZING = "resizing"
    SPLITTING = "splitting"
    MUTED = "muted"
    LOCKED = "locked"


class PlaybackState(Enum):
    """播放状态枚举"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    SEEKING = "seeking"
    BUFFERING = "buffering"


class ZoomLevel(Enum):
    """缩放级别枚举"""
    MIN_ZOOM = "min_zoom"
    FIT = "fit"
    SECOND = "second"
    FRAME = "frame"
    CUSTOM = "custom"


@dataclass
class TimeCode:
    """时间码类"""
    hours: int = 0
    minutes: int = 0
    seconds: int = 0
    frames: int = 0
    frame_rate: float = 30.0

    def to_seconds(self) -> float:
        """转换为秒数"""
        return (self.hours * 3600 + self.minutes * 60 + self.seconds) + (self.frames / self.frame_rate)

    @staticmethod
    def from_seconds(seconds: float, frame_rate: float = 30.0) -> 'TimeCode':
        """从秒数创建时间码"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        frames = int((seconds % 1) * frame_rate)
        return TimeCode(hours, minutes, secs, frames, frame_rate)

    def __str__(self) -> str:
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}:{self.frames:02d}"


@dataclass
class Keyframe:
    """关键帧类"""
    id: str
    time: float
    property_name: str
    value: Any
    easing: str = "linear"
    interpolation: str = "linear"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Clip:
    """剪辑类"""
    id: str
    name: str
    file_path: str
    start_time: float
    end_time: float
    timeline_start: float
    timeline_end: float
    track_id: str
    track_type: TrackType

    # 剪辑属性
    state: ClipState = ClipState.NORMAL
    volume: float = 1.0
    opacity: float = 1.0
    speed: float = 1.0
    pitch: float = 1.0

    # 视觉属性
    position: Tuple[float, float] = (0, 0)
    scale: Tuple[float, float] = (1.0, 1.0)
    rotation: float = 0.0

    # 音频属性
    audio_enabled: bool = True
    audio_offset: float = 0.0

    # 关键帧
    keyframes: Dict[str, List[Keyframe]] = field(default_factory=dict)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 视频信息
    video_info: Optional[VideoInfo] = None

    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = str(uuid.uuid4())

    def get_duration(self) -> float:
        """获取剪辑持续时间"""
        return self.end_time - self.start_time

    def get_timeline_duration(self) -> float:
        """获取时间线持续时间"""
        return self.timeline_end - self.timeline_start

    def add_keyframe(self, keyframe: Keyframe) -> None:
        """添加关键帧"""
        if keyframe.property_name not in self.keyframes:
            self.keyframes[keyframe.property_name] = []
        self.keyframes[keyframe.property_name].append(keyframe)
        self.keyframes[keyframe.property_name].sort(key=lambda k: k.time)

    def remove_keyframe(self, keyframe_id: str) -> bool:
        """移除关键帧"""
        for property_name, keyframe_list in self.keyframes.items():
            for i, keyframe in enumerate(keyframe_list):
                if keyframe.id == keyframe_id:
                    keyframe_list.pop(i)
                    return True
        return False

    def get_keyframe_value(self, property_name: str, time: float) -> Any:
        """获取指定时间的关键帧值"""
        if property_name not in self.keyframes:
            return None

        keyframe_list = self.keyframes[property_name]
        if not keyframe_list:
            return None

        # 找到时间点前后的关键帧
        prev_keyframe = None
        next_keyframe = None

        for keyframe in keyframe_list:
            if keyframe.time <= time:
                prev_keyframe = keyframe
            else:
                next_keyframe = keyframe
                break

        if prev_keyframe is None:
            return keyframe_list[0].value
        if next_keyframe is None:
            return prev_keyframe.value

        # 线性插值
        if prev_keyframe.interpolation == "linear":
            t = (time - prev_keyframe.time) / (next_keyframe.time - prev_keyframe.time)
            return prev_keyframe.value + (next_keyframe.value - prev_keyframe.value) * t

        return prev_keyframe.value


@dataclass
class Track:
    """轨道类"""
    id: str
    name: str
    track_type: TrackType
    index: int
    visible: bool = True
    locked: bool = False
    muted: bool = False
    volume: float = 1.0
    height: int = 100

    # 轨道属性
    clips: List[Clip] = field(default_factory=list)
    effects: List[str] = field(default_factory=list)

    # 音频可视化
    waveforms: Dict[str, List[float]] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = str(uuid.uuid4())

    def add_clip(self, clip: Clip) -> bool:
        """添加剪辑到轨道"""
        # 检查时间重叠
        for existing_clip in self.clips:
            if (clip.timeline_start < existing_clip.timeline_end and
                clip.timeline_end > existing_clip.timeline_start):
                return False

        clip.track_id = self.id
        self.clips.append(clip)
        self.clips.sort(key=lambda c: c.timeline_start)
        return True

    def remove_clip(self, clip_id: str) -> bool:
        """从轨道移除剪辑"""
        for i, clip in enumerate(self.clips):
            if clip.id == clip_id:
                self.clips.pop(i)
                return True
        return False

    def get_clip_at_time(self, time: float) -> Optional[Clip]:
        """获取指定时间的剪辑"""
        for clip in self.clips:
            if clip.timeline_start <= time <= clip.timeline_end:
                return clip
        return None

    def get_clips_in_range(self, start_time: float, end_time: float) -> List[Clip]:
        """获取时间范围内的剪辑"""
        return [clip for clip in self.clips
                if clip.timeline_start <= end_time and clip.timeline_end >= start_time]


@dataclass
class TimelineSettings:
    """时间线设置数据类"""
    frame_rate: float = 30.0
    sample_rate: int = 48000
    time_scale: float = 1.0  # 像素/秒
    zoom_level: ZoomLevel = ZoomLevel.FIT
    auto_save: bool = True
    auto_save_interval: int = 60  # 秒
    snap_enabled: bool = True
    snap_threshold: float = 0.1  # 秒
    loop_enabled: bool = False
    loop_start: float = 0.0
    loop_end: float = 0.0
    max_tracks: Dict[TrackType, int] = field(default_factory=lambda: {
        TrackType.VIDEO: 10,
        TrackType.AUDIO: 8,
        TrackType.EFFECTS: 5,
        TrackType.SUBTITLE: 5,
        TrackType.TRANSITION: 3
    })


@dataclass
class TimelineState:
    """时间线状态数据类"""
    current_time: float = 0.0
    duration: float = 0.0
    playback_state: PlaybackState = PlaybackState.STOPPED
    playback_speed: float = 1.0
    selected_clips: Set[str] = field(default_factory=set)
    zoom_scale: float = 1.0
    scroll_offset: float = 0.0
    marker_positions: List[float] = field(default_factory=list)
    in_point: Optional[float] = None
    out_point: Optional[float] = None


class TimelineEngine:
    """时间线引擎核心类"""

    def __init__(self, settings: Optional[TimelineSettings] = None, logger=None):
        """初始化时间线引擎"""
        self.logger = logger or get_logger("TimelineEngine")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.service_container = ServiceContainer()
        self.video_engine = get_video_engine()
        self.ffmpeg_utils = get_ffmpeg_utils()

        # 设置
        self.settings = settings or TimelineSettings()
        self.state = TimelineState()

        # 轨道管理
        self.tracks: Dict[str, Track] = {}
        self.track_order: List[str] = []
        self.track_lock = threading.Lock()

        # 播放控制
        self.playback_thread: Optional[threading.Thread] = None
        self.playback_stop_event = threading.Event()
        self.playback_callbacks: List[Callable[[float], None]] = []

        # 历史记录
        self.history: List[Dict[str, Any]] = []
        self.history_index = -1
        self.max_history_size = 100
        self.history_lock = threading.Lock()

        # 缓存
        self.cache_dir = "/tmp/cineaistudio/timeline_cache"
        self.cached_waveforms: Dict[str, List[float]] = {}

        # 性能监控
        self.performance_stats = {
            'total_operations': 0,
            'render_time': 0.0,
            'clips_count': 0,
            'tracks_count': 0,
            'memory_usage': 0
        }

        # 初始化
        self._initialize()

    def _initialize(self) -> None:
        """初始化时间线引擎"""
        try:
            # 创建缓存目录
            os.makedirs(self.cache_dir, exist_ok=True)

            # 注册服务
            self._register_services()

            # 设置事件处理器
            self._setup_event_handlers()

            # 创建默认轨道
            self._create_default_tracks()

            self.logger.info("时间线引擎初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"时间线引擎初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="initialize"
                ),
                user_message="时间线引擎初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _register_services(self) -> None:
        """注册服务"""
        try:
            self.service_container.register(TimelineEngine, self)
            self.service_container.register(EventBus, self.event_bus)
            self.logger.info("服务注册完成")
        except Exception as e:
            self.logger.error(f"服务注册失败: {str(e)}")

    def _setup_event_handlers(self) -> None:
        """设置事件处理器"""
        try:
            self.event_bus.subscribe("timeline_modified", self._on_timeline_modified)
            self.event_bus.subscribe("playback_state_changed", self._on_playback_state_changed)
            self.event_bus.subscribe("clip_added", self._on_clip_added)
            self.event_bus.subscribe("clip_removed", self._on_clip_removed)
            self.logger.info("事件处理器设置完成")
        except Exception as e:
            self.logger.error(f"事件处理器设置失败: {str(e)}")

    def _create_default_tracks(self) -> None:
        """创建默认轨道"""
        try:
            # 创建默认视频轨道
            video_track = self.create_track(TrackType.VIDEO, "Video 1", 0)
            self.track_order.append(video_track.id)

            # 创建默认音频轨道
            audio_track = self.create_track(TrackType.AUDIO, "Audio 1", 1)
            self.track_order.append(audio_track.id)

            self.logger.info("默认轨道创建完成")

        except Exception as e:
            self.logger.error(f"默认轨道创建失败: {str(e)}")

    def create_track(self, track_type: TrackType, name: str, index: Optional[int] = None) -> Track:
        """创建轨道"""
        with self.track_lock:
            # 检查轨道数量限制
            track_count = sum(1 for track in self.tracks.values() if track.track_type == track_type)
            max_tracks = self.settings.max_tracks.get(track_type, 10)

            if track_count >= max_tracks:
                raise ValueError(f"已达到{track_type.value}轨道最大数量限制: {max_tracks}")

            # 确定轨道索引
            if index is None:
                index = max([track.index for track in self.tracks.values()], default=-1) + 1

            # 创建轨道
            track = Track(
                id=str(uuid.uuid4()),
                name=name,
                track_type=track_type,
                index=index
            )

            self.tracks[track.id] = track
            self.track_order.append(track.id)

            # 更新性能统计
            self.performance_stats['tracks_count'] = len(self.tracks)

            # 发送事件
            self.event_bus.publish("track_created", {
                'track_id': track.id,
                'track_type': track_type.value,
                'name': name,
                'index': index
            })

            self.logger.info(f"创建轨道: {name} ({track_type.value})")
            return track

    def delete_track(self, track_id: str) -> bool:
        """删除轨道"""
        with self.track_lock:
            if track_id not in self.tracks:
                return False

            track = self.tracks[track_id]

            # 检查是否有剪辑
            if track.clips:
                return False

            # 移除轨道
            del self.tracks[track_id]
            self.track_order.remove(track_id)

            # 更新性能统计
            self.performance_stats['tracks_count'] = len(self.tracks)

            # 发送事件
            self.event_bus.publish("track_deleted", {
                'track_id': track_id,
                'track_type': track.track_type.value
            })

            self.logger.info(f"删除轨道: {track.name}")
            return True

    def get_track(self, track_id: str) -> Optional[Track]:
        """获取轨道"""
        return self.tracks.get(track_id)

    def get_tracks_by_type(self, track_type: TrackType) -> List[Track]:
        """获取指定类型的轨道"""
        return [track for track in self.tracks.values() if track.track_type == track_type]

    def add_clip(self, clip: Clip, track_id: str) -> bool:
        """添加剪辑到时间线"""
        try:
            track = self.get_track(track_id)
            if not track:
                return False

            # 验证剪辑类型与轨道类型匹配
            if clip.track_type != track.track_type:
                return False

            # 添加剪辑到轨道
            success = track.add_clip(clip)
            if not success:
                return False

            # 生成音频波形（如果是音频剪辑）
            if clip.track_type == TrackType.AUDIO:
                self._generate_waveform(clip)

            # 更新时间线持续时间
            self._update_timeline_duration()

            # 更新性能统计
            self.performance_stats['clips_count'] = sum(len(track.clips) for track in self.tracks.values())

            # 记录历史
            self._record_history({
                'action': 'add_clip',
                'clip_id': clip.id,
                'track_id': track_id,
                'clip_data': copy.deepcopy(clip.__dict__)
            })

            # 发送事件
            self.event_bus.publish("clip_added", {
                'clip_id': clip.id,
                'track_id': track_id,
                'clip_data': clip
            })

            self.logger.info(f"添加剪辑: {clip.name} 到轨道 {track.name}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"添加剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="add_clip"
                ),
                user_message="无法添加剪辑到时间线"
            )
            self.error_handler.handle_error(error_info)
            return False

    def remove_clip(self, clip_id: str) -> bool:
        """从时间线移除剪辑"""
        try:
            # 找到剪辑所在的轨道
            track = None
            for t in self.tracks.values():
                if any(clip.id == clip_id for clip in t.clips):
                    track = t
                    break

            if not track:
                return False

            # 移除剪辑
            success = track.remove_clip(clip_id)
            if not success:
                return False

            # 更新时间线持续时间
            self._update_timeline_duration()

            # 更新性能统计
            self.performance_stats['clips_count'] = sum(len(track.clips) for track in self.tracks.values())

            # 记录历史
            self._record_history({
                'action': 'remove_clip',
                'clip_id': clip_id,
                'track_id': track.id
            })

            # 发送事件
            self.event_bus.publish("clip_removed", {
                'clip_id': clip_id,
                'track_id': track.id
            })

            self.logger.info(f"移除剪辑: {clip_id}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"移除剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="remove_clip"
                ),
                user_message="无法移除剪辑"
            )
            self.error_handler.handle_error(error_info)
            return False

    def move_clip(self, clip_id: str, new_track_id: str, new_start_time: float) -> bool:
        """移动剪辑"""
        try:
            # 找到剪辑
            clip = None
            old_track = None
            for track in self.tracks.values():
                for c in track.clips:
                    if c.id == clip_id:
                        clip = c
                        old_track = track
                        break
                if clip:
                    break

            if not clip:
                return False

            # 计算新的结束时间
            duration = clip.get_timeline_duration()
            new_end_time = new_start_time + duration

            # 更新剪辑时间
            old_timeline_start = clip.timeline_start
            old_timeline_end = clip.timeline_end
            clip.timeline_start = new_start_time
            clip.timeline_end = new_end_time

            # 如果轨道不同，需要重新添加
            if old_track.id != new_track_id:
                new_track = self.get_track(new_track_id)
                if not new_track:
                    return False

                # 从原轨道移除
                old_track.remove_clip(clip_id)

                # 添加到新轨道
                success = new_track.add_clip(clip)
                if not success:
                    # 如果失败，恢复原状态
                    clip.timeline_start = old_timeline_start
                    clip.timeline_end = old_timeline_end
                    old_track.add_clip(clip)
                    return False
            else:
                # 同一轨道内移动，需要检查重叠
                for other_clip in old_track.clips:
                    if other_clip.id != clip_id:
                        if (new_start_time < other_clip.timeline_end and
                            new_end_time > other_clip.timeline_start):
                            # 恢复原状态
                            clip.timeline_start = old_timeline_start
                            clip.timeline_end = old_timeline_end
                            return False

                # 重新排序剪辑
                old_track.clips.sort(key=lambda c: c.timeline_start)

            # 记录历史
            self._record_history({
                'action': 'move_clip',
                'clip_id': clip_id,
                'old_track_id': old_track.id,
                'new_track_id': new_track_id,
                'old_start_time': old_timeline_start,
                'new_start_time': new_start_time
            })

            # 发送事件
            self.event_bus.publish("clip_moved", {
                'clip_id': clip_id,
                'old_track_id': old_track.id,
                'new_track_id': new_track_id,
                'start_time': new_start_time,
                'end_time': new_end_time
            })

            self.logger.info(f"移动剪辑: {clip_id} 到时间 {new_start_time}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"移动剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="move_clip"
                ),
                user_message="无法移动剪辑"
            )
            self.error_handler.handle_error(error_info)
            return False

    def trim_clip(self, clip_id: str, new_start_time: float, new_end_time: float) -> bool:
        """修剪剪辑"""
        try:
            # 找到剪辑
            clip = None
            for track in self.tracks.values():
                for c in track.clips:
                    if c.id == clip_id:
                        clip = c
                        break
                if clip:
                    break

            if not clip:
                return False

            # 验证修剪时间
            if new_start_time >= new_end_time:
                return False

            clip_duration = clip.get_duration()
            new_duration = new_end_time - new_start_time

            if new_duration <= 0 or new_duration > clip_duration:
                return False

            # 记录旧值
            old_start = clip.start_time
            old_end = clip.end_time
            old_timeline_start = clip.timeline_start
            old_timeline_end = clip.timeline_end

            # 更新剪辑时间
            clip.start_time = new_start_time
            clip.end_time = new_end_time
            clip.timeline_end = clip.timeline_start + new_duration

            # 记录历史
            self._record_history({
                'action': 'trim_clip',
                'clip_id': clip_id,
                'old_start_time': old_start,
                'old_end_time': old_end,
                'new_start_time': new_start_time,
                'new_end_time': new_end_time,
                'old_timeline_start': old_timeline_start,
                'old_timeline_end': old_timeline_end
            })

            # 发送事件
            self.event_bus.publish("clip_trimmed", {
                'clip_id': clip_id,
                'start_time': new_start_time,
                'end_time': new_end_time,
                'timeline_start': clip.timeline_start,
                'timeline_end': clip.timeline_end
            })

            self.logger.info(f"修剪剪辑: {clip_id} [{new_start_time:.2f} - {new_end_time:.2f}]")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"修剪剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="trim_clip"
                ),
                user_message="无法修剪剪辑"
            )
            self.error_handler.handle_error(error_info)
            return False

    def split_clip(self, clip_id: str, split_time: float) -> Optional[str]:
        """分割剪辑"""
        try:
            # 找到剪辑
            clip = None
            track = None
            for t in self.tracks.values():
                for c in t.clips:
                    if c.id == clip_id:
                        clip = c
                        track = t
                        break
                if clip:
                    break

            if not clip:
                return None

            # 验证分割时间
            if split_time <= clip.timeline_start or split_time >= clip.timeline_end:
                return None

            # 计算分割点在剪辑中的相对时间
            relative_split_time = clip.start_time + (split_time - clip.timeline_start)

            # 创建新剪辑（右半部分）
            new_clip = Clip(
                id=str(uuid.uuid4()),
                name=f"{clip.name}_split",
                file_path=clip.file_path,
                start_time=relative_split_time,
                end_time=clip.end_time,
                timeline_start=split_time,
                timeline_end=clip.timeline_end,
                track_id=clip.track_id,
                track_type=clip.track_type,
                video_info=clip.video_info,
                metadata=clip.metadata.copy()
            )

            # 更新原剪辑（左半部分）
            old_end_time = clip.end_time
            old_timeline_end = clip.timeline_end
            clip.end_time = relative_split_time
            clip.timeline_end = split_time

            # 添加新剪辑到轨道
            success = track.add_clip(new_clip)
            if not success:
                # 恢复原状态
                clip.end_time = old_end_time
                clip.timeline_end = old_timeline_end
                return None

            # 复制关键帧
            for property_name, keyframes in clip.keyframes.items():
                for keyframe in keyframes:
                    if keyframe.time >= relative_split_time:
                        # 创建新的关键帧
                        new_keyframe = Keyframe(
                            id=str(uuid.uuid4()),
                            time=keyframe.time - relative_split_time,
                            property_name=keyframe.property_name,
                            value=keyframe.value,
                            easing=keyframe.easing,
                            interpolation=keyframe.interpolation
                        )
                        new_clip.add_keyframe(new_keyframe)

            # 记录历史
            self._record_history({
                'action': 'split_clip',
                'clip_id': clip_id,
                'new_clip_id': new_clip.id,
                'split_time': split_time
            })

            # 发送事件
            self.event_bus.publish("clip_split", {
                'clip_id': clip_id,
                'new_clip_id': new_clip.id,
                'split_time': split_time
            })

            self.logger.info(f"分割剪辑: {clip_id} 在时间 {split_time:.2f}")
            return new_clip.id

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"分割剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="split_clip"
                ),
                user_message="无法分割剪辑"
            )
            self.error_handler.handle_error(error_info)
            return None

    def add_keyframe(self, clip_id: str, property_name: str, time: float, value: Any) -> Optional[Keyframe]:
        """添加关键帧"""
        try:
            # 找到剪辑
            clip = None
            for track in self.tracks.values():
                for c in track.clips:
                    if c.id == clip_id:
                        clip = c
                        break
                if clip:
                    break

            if not clip:
                return None

            # 创建关键帧
            keyframe = Keyframe(
                id=str(uuid.uuid4()),
                time=time,
                property_name=property_name,
                value=value
            )

            # 添加关键帧
            clip.add_keyframe(keyframe)

            # 记录历史
            self._record_history({
                'action': 'add_keyframe',
                'clip_id': clip_id,
                'keyframe_id': keyframe.id,
                'property_name': property_name,
                'time': time,
                'value': value
            })

            # 发送事件
            self.event_bus.publish("keyframe_added", {
                'clip_id': clip_id,
                'keyframe_id': keyframe.id,
                'property_name': property_name,
                'time': time,
                'value': value
            })

            self.logger.info(f"添加关键帧: {clip_id}.{property_name} @ {time:.2f}")
            return keyframe

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"添加关键帧失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="add_keyframe"
                ),
                user_message="无法添加关键帧"
            )
            self.error_handler.handle_error(error_info)
            return None

    def remove_keyframe(self, clip_id: str, keyframe_id: str) -> bool:
        """移除关键帧"""
        try:
            # 找到剪辑
            clip = None
            for track in self.tracks.values():
                for c in track.clips:
                    if c.id == clip_id:
                        clip = c
                        break
                if clip:
                    break

            if not clip:
                return False

            # 移除关键帧
            success = clip.remove_keyframe(keyframe_id)
            if not success:
                return False

            # 记录历史
            self._record_history({
                'action': 'remove_keyframe',
                'clip_id': clip_id,
                'keyframe_id': keyframe_id
            })

            # 发送事件
            self.event_bus.publish("keyframe_removed", {
                'clip_id': clip_id,
                'keyframe_id': keyframe_id
            })

            self.logger.info(f"移除关键帧: {keyframe_id}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"移除关键帧失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="remove_keyframe"
                ),
                user_message="无法移除关键帧"
            )
            self.error_handler.handle_error(error_info)
            return False

    def start_playback(self) -> bool:
        """开始播放"""
        try:
            if self.state.playback_state == PlaybackState.PLAYING:
                return True

            # 检查是否有可播放的内容
            if not any(track.clips for track in self.tracks.values()):
                return False

            # 重置停止事件
            self.playback_stop_event.clear()

            # 启动播放线程
            self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.playback_thread.start()

            # 更新状态
            self.state.playback_state = PlaybackState.PLAYING

            # 发送事件
            self.event_bus.publish("playback_started", {
                'start_time': self.state.current_time,
                'speed': self.state.playback_speed
            })

            self.logger.info(f"开始播放: {self.state.current_time:.2f}s")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"开始播放失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="start_playback"
                ),
                user_message="无法开始播放"
            )
            self.error_handler.handle_error(error_info)
            return False

    def pause_playback(self) -> bool:
        """暂停播放"""
        try:
            if self.state.playback_state != PlaybackState.PLAYING:
                return True

            # 设置停止事件
            self.playback_stop_event.set()

            # 等待播放线程结束
            if self.playback_thread:
                self.playback_thread.join(timeout=1.0)
                self.playback_thread = None

            # 更新状态
            self.state.playback_state = PlaybackState.PAUSED

            # 发送事件
            self.event_bus.publish("playback_paused", {
                'pause_time': self.state.current_time
            })

            self.logger.info(f"暂停播放: {self.state.current_time:.2f}s")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"暂停播放失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="pause_playback"
                ),
                user_message="无法暂停播放"
            )
            self.error_handler.handle_error(error_info)
            return False

    def stop_playback(self) -> bool:
        """停止播放"""
        try:
            # 设置停止事件
            self.playback_stop_event.set()

            # 等待播放线程结束
            if self.playback_thread:
                self.playback_thread.join(timeout=1.0)
                self.playback_thread = None

            # 重置时间
            self.state.current_time = 0.0

            # 更新状态
            self.state.playback_state = PlaybackState.STOPPED

            # 发送事件
            self.event_bus.publish("playback_stopped", {
                'stop_time': self.state.current_time
            })

            self.logger.info("停止播放")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"停止播放失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="stop_playback"
                ),
                user_message="无法停止播放"
            )
            self.error_handler.handle_error(error_info)
            return False

    def seek_to(self, time: float) -> bool:
        """跳转到指定时间"""
        try:
            # 验证时间
            if time < 0:
                time = 0
            elif time > self.state.duration:
                time = self.state.duration

            # 更新当前时间
            old_time = self.state.current_time
            self.state.current_time = time

            # 发送事件
            self.event_bus.publish("timeline_seeked", {
                'old_time': old_time,
                'new_time': time
            })

            # 调用播放回调
            for callback in self.playback_callbacks:
                try:
                    callback(time)
                except Exception as e:
                    self.logger.error(f"播放回调失败: {e}")

            self.logger.info(f"跳转到: {time:.2f}s")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"跳转失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="seek_to"
                ),
                user_message="无法跳转到指定时间"
            )
            self.error_handler.handle_error(error_info)
            return False

    def set_playback_speed(self, speed: float) -> bool:
        """设置播放速度"""
        try:
            if speed <= 0:
                return False

            old_speed = self.state.playback_speed
            self.state.playback_speed = speed

            # 发送事件
            self.event_bus.publish("playback_speed_changed", {
                'old_speed': old_speed,
                'new_speed': speed
            })

            self.logger.info(f"设置播放速度: {speed}x")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.LOW,
                message=f"设置播放速度失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="set_playback_speed"
                ),
                user_message="无法设置播放速度"
            )
            self.error_handler.handle_error(error_info)
            return False

    def add_playback_callback(self, callback: Callable[[float], None]) -> None:
        """添加播放回调"""
        self.playback_callbacks.append(callback)

    def remove_playback_callback(self, callback: Callable[[float], None]) -> None:
        """移除播放回调"""
        if callback in self.playback_callbacks:
            self.playback_callbacks.remove(callback)

    def _playback_worker(self) -> None:
        """播放工作线程"""
        try:
            start_time = time.time()
            last_frame_time = self.state.current_time

            while not self.playback_stop_event.is_set():
                current_real_time = time.time() - start_time
                current_timeline_time = last_frame_time + (current_real_time * self.state.playback_speed)

                # 检查是否到达时间线末尾
                if current_timeline_time >= self.state.duration:
                    if self.settings.loop_enabled and self.settings.loop_end > 0:
                        # 循环播放
                        current_timeline_time = self.settings.loop_start
                        last_frame_time = current_timeline_time
                        start_time = time.time()
                    else:
                        # 停止播放
                        self.stop_playback()
                        break

                # 更新当前时间
                self.state.current_time = current_timeline_time

                # 调用播放回调
                for callback in self.playback_callbacks:
                    try:
                        callback(current_timeline_time)
                    except Exception as e:
                        self.logger.error(f"播放回调失败: {e}")

                # 控制帧率
                frame_interval = 1.0 / self.settings.frame_rate
                time.sleep(frame_interval)

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"播放线程异常: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="_playback_worker"
                ),
                user_message="播放过程中发生错误"
            )
            self.error_handler.handle_error(error_info)

            # 停止播放
            self.state.playback_state = PlaybackState.STOPPED

    def _generate_waveform(self, clip: Clip) -> None:
        """生成音频波形"""
        try:
            # 检查是否已缓存
            if clip.file_path in self.cached_waveforms:
                clip.track_id = clip.track_id  # 更新波形关联
                return

            # 使用ffmpeg提取音频数据
            waveform_data = self.ffmpeg_utils.extract_waveform(clip.file_path)

            if waveform_data:
                self.cached_waveforms[clip.file_path] = waveform_data
                clip.track_id = clip.track_id  # 更新波形关联

                self.logger.info(f"生成音频波形: {clip.file_path}")

        except Exception as e:
            self.logger.error(f"生成音频波形失败: {e}")

    def get_waveform(self, clip_id: str) -> Optional[List[float]]:
        """获取音频波形"""
        try:
            # 找到剪辑
            clip = None
            for track in self.tracks.values():
                for c in track.clips:
                    if c.id == clip_id:
                        clip = c
                        break
                if clip:
                    break

            if not clip:
                return None

            return self.cached_waveforms.get(clip.file_path)

        except Exception as e:
            self.logger.error(f"获取音频波形失败: {e}")
            return None

    def set_zoom(self, zoom_level: ZoomLevel, scale: float = 1.0) -> None:
        """设置缩放级别"""
        self.settings.zoom_level = zoom_level
        self.state.zoom_scale = scale

        # 发送事件
        self.event_bus.publish("zoom_changed", {
            'zoom_level': zoom_level.value,
            'scale': scale
        })

        self.logger.info(f"设置缩放: {zoom_level.value} ({scale}x)")

    def scroll_to(self, offset: float) -> None:
        """滚动到指定位置"""
        self.state.scroll_offset = offset

        # 发送事件
        self.event_bus.publish("scroll_changed", {
            'offset': offset
        })

    def _update_timeline_duration(self) -> None:
        """更新时间线持续时间"""
        max_end_time = 0.0

        for track in self.tracks.values():
            for clip in track.clips:
                if clip.timeline_end > max_end_time:
                    max_end_time = clip.timeline_end

        self.state.duration = max_end_time

    def _record_history(self, action_data: Dict[str, Any]) -> None:
        """记录历史操作"""
        with self.history_lock:
            # 如果当前不在历史记录末尾，清除后续记录
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]

            # 添加新记录
            self.history.append({
                'timestamp': time.time(),
                'action': action_data,
                'timeline_state': self._get_timeline_state()
            })

            # 限制历史记录大小
            if len(self.history) > self.max_history_size:
                self.history.pop(0)
            else:
                self.history_index += 1

    def _get_timeline_state(self) -> Dict[str, Any]:
        """获取时间线状态快照"""
        return {
            'tracks': copy.deepcopy(self.tracks),
            'track_order': self.track_order.copy(),
            'current_time': self.state.current_time,
            'duration': self.state.duration
        }

    def undo(self) -> bool:
        """撤销操作"""
        with self.history_lock:
            if self.history_index <= 0:
                return False

            self.history_index -= 1
            history_item = self.history[self.history_index]

            # 恢复状态
            self._restore_timeline_state(history_item['timeline_state'])

            # 发送事件
            self.event_bus.publish("undo_performed", {
                'action': history_item['action'],
                'timestamp': history_item['timestamp']
            })

            self.logger.info(f"撤销操作: {history_item['action']}")
            return True

    def redo(self) -> bool:
        """重做操作"""
        with self.history_lock:
            if self.history_index >= len(self.history) - 1:
                return False

            self.history_index += 1
            history_item = self.history[self.history_index]

            # 恢复状态
            self._restore_timeline_state(history_item['timeline_state'])

            # 发送事件
            self.event_bus.publish("redo_performed", {
                'action': history_item['action'],
                'timestamp': history_item['timestamp']
            })

            self.logger.info(f"重做操作: {history_item['action']}")
            return True

    def _restore_timeline_state(self, state: Dict[str, Any]) -> None:
        """恢复时间线状态"""
        self.tracks = copy.deepcopy(state['tracks'])
        self.track_order = state['track_order'].copy()
        self.state.current_time = state['current_time']
        self.state.duration = state['duration']

        # 更新性能统计
        self.performance_stats['tracks_count'] = len(self.tracks)
        self.performance_stats['clips_count'] = sum(len(track.clips) for track in self.tracks.values())

    def get_timeline_info(self) -> Dict[str, Any]:
        """获取时间线信息"""
        return {
            'duration': self.state.duration,
            'current_time': self.state.current_time,
            'playback_state': self.state.playback_state.value,
            'playback_speed': self.state.playback_speed,
            'tracks_count': len(self.tracks),
            'clips_count': sum(len(track.clips) for track in self.tracks.values()),
            'zoom_level': self.settings.zoom_level.value,
            'zoom_scale': self.state.zoom_scale,
            'performance': self.performance_stats.copy()
        }

    def get_timeline_data(self) -> Dict[str, Any]:
        """获取时间线数据（用于保存/加载）"""
        return {
            'settings': self.settings.__dict__,
            'state': self.state.__dict__,
            'tracks': {track_id: track.__dict__ for track_id, track in self.tracks.items()},
            'track_order': self.track_order
        }

    def load_timeline_data(self, data: Dict[str, Any]) -> bool:
        """加载时间线数据"""
        try:
            # 加载设置
            if 'settings' in data:
                settings_data = data['settings']
                self.settings.frame_rate = settings_data.get('frame_rate', 30.0)
                self.settings.sample_rate = settings_data.get('sample_rate', 48000)
                self.settings.time_scale = settings_data.get('time_scale', 1.0)
                self.settings.auto_save = settings_data.get('auto_save', True)
                self.settings.snap_enabled = settings_data.get('snap_enabled', True)

            # 加载状态
            if 'state' in data:
                state_data = data['state']
                self.state.current_time = state_data.get('current_time', 0.0)
                self.state.duration = state_data.get('duration', 0.0)
                self.state.playback_speed = state_data.get('playback_speed', 1.0)
                self.state.zoom_scale = state_data.get('zoom_scale', 1.0)

            # 加载轨道
            if 'tracks' in data:
                self.tracks.clear()
                for track_id, track_data in data['tracks'].items():
                    track = Track(
                        id=track_data['id'],
                        name=track_data['name'],
                        track_type=TrackType(track_data['track_type']),
                        index=track_data['index'],
                        visible=track_data.get('visible', True),
                        locked=track_data.get('locked', False),
                        muted=track_data.get('muted', False),
                        volume=track_data.get('volume', 1.0),
                        height=track_data.get('height', 100)
                    )
                    self.tracks[track_id] = track

            # 加载轨道顺序
            if 'track_order' in data:
                self.track_order = data['track_order']

            # 更新性能统计
            self.performance_stats['tracks_count'] = len(self.tracks)
            self.performance_stats['clips_count'] = sum(len(track.clips) for track in self.tracks.values())

            self.logger.info("时间线数据加载完成")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"加载时间线数据失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="load_timeline_data"
                ),
                user_message="无法加载时间线数据"
            )
            self.error_handler.handle_error(error_info)
            return False

    def export_timeline(self, output_path: str) -> bool:
        """导出时间线"""
        try:
            timeline_data = self.get_timeline_data()

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"时间线导出完成: {output_path}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.EXPORT,
                severity=ErrorSeverity.HIGH,
                message=f"导出时间线失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="export_timeline"
                ),
                user_message="无法导出时间线"
            )
            self.error_handler.handle_error(error_info)
            return False

    def import_timeline(self, input_path: str) -> bool:
        """导入时间线"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)

            return self.load_timeline_data(timeline_data)

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"导入时间线失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="TimelineEngine",
                    operation="import_timeline"
                ),
                user_message="无法导入时间线"
            )
            self.error_handler.handle_error(error_info)
            return False

    def _on_timeline_modified(self, data: Any) -> None:
        """处理时间线修改事件"""
        self.logger.debug(f"时间线修改: {data}")

    def _on_playback_state_changed(self, data: Any) -> None:
        """处理播放状态变更事件"""
        self.logger.debug(f"播放状态变更: {data}")

    def _on_clip_added(self, data: Any) -> None:
        """处理剪辑添加事件"""
        self.logger.debug(f"剪辑添加: {data}")

    def _on_clip_removed(self, data: Any) -> None:
        """处理剪辑移除事件"""
        self.logger.debug(f"剪辑移除: {data}")

    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 停止播放
            self.stop_playback()

            # 清理缓存
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)

            self.logger.info("时间线引擎资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局时间线引擎实例
_timeline_engine: Optional[TimelineEngine] = None


def get_timeline_engine(settings: Optional[TimelineSettings] = None) -> TimelineEngine:
    """获取全局时间线引擎实例"""
    global _timeline_engine
    if _timeline_engine is None:
        _timeline_engine = TimelineEngine(settings)
    return _timeline_engine


def cleanup_timeline_engine() -> None:
    """清理全局时间线引擎实例"""
    global _timeline_engine
    if _timeline_engine is not None:
        _timeline_engine.cleanup()
        _timeline_engine = None