#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 剪辑管理器模块
专业的剪辑管理系统，提供剪辑的创建、编辑、分析和优化功能
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
import hashlib
from contextlib import contextmanager

from .logger import get_logger
from .event_system import EventBus
from .service_container import ServiceContainer
from .timeline_engine import TimelineEngine, Clip, Track, TrackType, ClipState
from .video_engine import get_video_engine, EngineState, VideoStream
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import VideoInfo, get_ffmpeg_utils


class ClipOperation(Enum):
    """剪辑操作枚举"""
    CREATE = "create"
    EDIT = "edit"
    TRIM = "trim"
    SPLIT = "split"
    MERGE = "merge"
    DELETE = "delete"
    DUPLICATE = "duplicate"
    CROP = "crop"
    ROTATE = "rotate"
    SCALE = "scale"
    EFFECT_APPLY = "effect_apply"
    TRANSITION_APPLY = "transition_apply"


class ClipFormat(Enum):
    """剪辑格式枚举"""
    MP4 = "mp4"
    MOV = "mov"
    AVI = "avi"
    MKV = "mkv"
    WMV = "wmv"
    FLV = "flv"
    WEBM = "webm"
    M4V = "m4v"


class ClipQuality(Enum):
    """剪辑质量枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"
    ORIGINAL = "original"


@dataclass
class ClipMetadata:
    """剪辑元数据"""
    format: ClipFormat
    quality: ClipQuality
    resolution: Tuple[int, int]
    frame_rate: float
    duration: float
    file_size: int
    bitrate: int
    codec: str
    audio_codec: str
    audio_channels: int
    audio_sample_rate: int
    has_audio: bool
    has_video: bool
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    description: str = ""
    thumbnail_path: Optional[str] = None


@dataclass
class ClipAnalysis:
    """剪辑分析结果"""
    brightness: float = 0.0
    contrast: float = 0.0
    saturation: float = 0.0
    sharpness: float = 0.0
    noise_level: float = 0.0
    motion_level: float = 0.0
    audio_level: float = 0.0
    audio_clipping: bool = False
    scene_changes: List[float] = field(default_factory=list)
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    face_detected: bool = False
    face_count: int = 0
    text_detected: bool = False
    text_regions: List[Tuple[int, int, int, int]] = field(default_factory=list)


@dataclass
class ClipEffect:
    """剪辑效果"""
    id: str
    name: str
    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    start_time: float = 0.0
    end_time: float = 0.0
    intensity: float = 1.0


@dataclass
class ClipTransition:
    """剪辑转场"""
    id: str
    name: str
    type: str
    duration: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    from_clip_id: Optional[str] = None
    to_clip_id: Optional[str] = None


class ClipManager:
    """剪辑管理器核心类"""

    def __init__(self, timeline_engine: Optional[TimelineEngine] = None, logger=None):
        """初始化剪辑管理器"""
        self.logger = logger or get_logger("ClipManager")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.service_container = ServiceContainer()
        self.timeline_engine = timeline_engine or get_timeline_engine()
        self.video_engine = get_video_engine()
        self.ffmpeg_utils = get_ffmpeg_utils()

        # 剪辑缓存
        self.clips_cache: Dict[str, Clip] = {}
        self.metadata_cache: Dict[str, ClipMetadata] = {}
        self.analysis_cache: Dict[str, ClipAnalysis] = {}
        self.thumbnails_cache: Dict[str, str] = {}

        # 效果和转场
        self.effects_library: Dict[str, ClipEffect] = {}
        self.transitions_library: Dict[str, ClipTransition] = {}

        # 分析队列
        self.analysis_queue: List[str] = []
        self.analysis_thread: Optional[threading.Thread] = None
        self.analysis_stop_event = threading.Event()

        # 缓存设置
        self.cache_dir = "/tmp/cineaistudio/clip_cache"
        self.max_cache_size = 1000  # 最大缓存剪辑数

        # 性能监控
        self.performance_stats = {
            'total_clips_created': 0,
            'total_clips_analyzed': 0,
            'analysis_queue_size': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'processing_time': 0.0
        }

        # 初始化
        self._initialize()

    def _initialize(self) -> None:
        """初始化剪辑管理器"""
        try:
            # 创建缓存目录
            os.makedirs(self.cache_dir, exist_ok=True)

            # 注册服务
            self._register_services()

            # 设置事件处理器
            self._setup_event_handlers()

            # 初始化效果库
            self._initialize_effects_library()

            # 初始化转场库
            self._initialize_transitions_library()

            # 启动分析线程
            self._start_analysis_thread()

            self.logger.info("剪辑管理器初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"剪辑管理器初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ClipManager",
                    operation="initialize"
                ),
                user_message="剪辑管理器初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _register_services(self) -> None:
        """注册服务"""
        try:
            self.service_container.register(ClipManager, self)
            self.service_container.register(EventBus, self.event_bus)
            self.logger.info("服务注册完成")
        except Exception as e:
            self.logger.error(f"服务注册失败: {str(e)}")

    def _setup_event_handlers(self) -> None:
        """设置事件处理器"""
        try:
            self.event_bus.subscribe("clip_created", self._on_clip_created)
            self.event_bus.subscribe("clip_modified", self._on_clip_modified)
            self.event_bus.subscribe("clip_deleted", self._on_clip_deleted)
            self.event_bus.subscribe("timeline_modified", self._on_timeline_modified)
            self.logger.info("事件处理器设置完成")
        except Exception as e:
            self.logger.error(f"事件处理器设置失败: {str(e)}")

    def _initialize_effects_library(self) -> None:
        """初始化效果库"""
        try:
            # 视频效果
            self.effects_library.update({
                "brightness": ClipEffect(
                    id="brightness",
                    name="亮度调整",
                    type="video",
                    parameters={"level": 0.0, "min": -1.0, "max": 1.0}
                ),
                "contrast": ClipEffect(
                    id="contrast",
                    name="对比度调整",
                    type="video",
                    parameters={"level": 1.0, "min": 0.0, "max": 2.0}
                ),
                "saturation": ClipEffect(
                    id="saturation",
                    name="饱和度调整",
                    type="video",
                    parameters={"level": 1.0, "min": 0.0, "max": 2.0}
                ),
                "blur": ClipEffect(
                    id="blur",
                    name="模糊",
                    type="video",
                    parameters={"radius": 0.0, "min": 0.0, "max": 10.0}
                ),
                "sharpen": ClipEffect(
                    id="sharpen",
                    name="锐化",
                    type="video",
                    parameters={"intensity": 0.0, "min": 0.0, "max": 1.0}
                ),
                "noise_reduction": ClipEffect(
                    id="noise_reduction",
                    name="降噪",
                    type="video",
                    parameters={"level": 0.0, "min": 0.0, "max": 1.0}
                ),
                "color_grading": ClipEffect(
                    id="color_grading",
                    name="调色",
                    type="video",
                    parameters={
                        "temperature": 0.0,
                        "tint": 0.0,
                        "exposure": 0.0,
                        "highlights": 0.0,
                        "shadows": 0.0,
                        "whites": 0.0,
                        "blacks": 0.0
                    }
                )
            })

            # 音频效果
            self.effects_library.update({
                "volume": ClipEffect(
                    id="volume",
                    name="音量调整",
                    type="audio",
                    parameters={"level": 1.0, "min": 0.0, "max": 2.0}
                ),
                "equalizer": ClipEffect(
                    id="equalizer",
                    name="均衡器",
                    type="audio",
                    parameters={
                        "low": 0.0, "mid": 0.0, "high": 0.0,
                        "low_freq": 250, "mid_freq": 1000, "high_freq": 4000
                    }
                ),
                "reverb": ClipEffect(
                    id="reverb",
                    name="混响",
                    type="audio",
                    parameters={"room_size": 0.5, "damping": 0.5, "wet_level": 0.3}
                ),
                "delay": ClipEffect(
                    id="delay",
                    name="延迟",
                    type="audio",
                    parameters={"delay_time": 0.3, "feedback": 0.5, "mix": 0.3}
                ),
                "compression": ClipEffect(
                    id="compression",
                    name="压缩",
                    type="audio",
                    parameters={
                        "threshold": -20.0, "ratio": 4.0, "attack": 0.01, "release": 0.1
                    }
                )
            })

            self.logger.info(f"效果库初始化完成，共 {len(self.effects_library)} 个效果")

        except Exception as e:
            self.logger.error(f"效果库初始化失败: {str(e)}")

    def _initialize_transitions_library(self) -> None:
        """初始化转场库"""
        try:
            self.transitions_library.update({
                "fade": ClipTransition(
                    id="fade",
                    name="淡入淡出",
                    type="fade",
                    duration=1.0,
                    parameters={"direction": "in_out"}
                ),
                "dissolve": ClipTransition(
                    id="dissolve",
                    name="溶解",
                    type="dissolve",
                    duration=1.0,
                    parameters={"smoothness": 0.5}
                ),
                "slide": ClipTransition(
                    id="slide",
                    name="滑动",
                    type="slide",
                    duration=0.8,
                    parameters={"direction": "left", "smoothness": 0.8}
                ),
                "zoom": ClipTransition(
                    id="zoom",
                    name="缩放",
                    type="zoom",
                    duration=1.0,
                    parameters={"direction": "in", "scale": 1.5}
                ),
                "wipe": ClipTransition(
                    id="wipe",
                    name="擦除",
                    type="wipe",
                    duration=0.8,
                    parameters={"direction": "left", "softness": 0.3}
                ),
                "push": ClipTransition(
                    id="push",
                    name="推动",
                    type="push",
                    duration=0.6,
                    parameters={"direction": "left"}
                ),
                "reveal": ClipTransition(
                    id="reveal",
                    name="揭示",
                    type="reveal",
                    duration=1.2,
                    parameters={"direction": "up", "pattern": "circle"}
                )
            })

            self.logger.info(f"转场库初始化完成，共 {len(self.transitions_library)} 个转场")

        except Exception as e:
            self.logger.error(f"转场库初始化失败: {str(e)}")

    def _start_analysis_thread(self) -> None:
        """启动分析线程"""
        self.analysis_thread = threading.Thread(target=self._analysis_worker, daemon=True)
        self.analysis_thread.start()

    def _analysis_worker(self) -> None:
        """分析工作线程"""
        while not self.analysis_stop_event.is_set():
            try:
                if self.analysis_queue:
                    clip_id = self.analysis_queue.pop(0)
                    self._analyze_clip(clip_id)
                else:
                    time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"分析线程异常: {e}")
                time.sleep(1.0)

    def create_clip(self, file_path: str, name: Optional[str] = None,
                   track_type: TrackType = TrackType.VIDEO) -> Optional[Clip]:
        """创建剪辑"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"文件不存在: {file_path}")
                return None

            # 获取视频信息
            video_info = self.ffmpeg_utils.get_video_info(file_path)

            # 生成剪辑名称
            if not name:
                name = Path(file_path).stem

            # 创建剪辑
            clip = Clip(
                id=str(uuid.uuid4()),
                name=name,
                file_path=file_path,
                start_time=0.0,
                end_time=video_info.duration,
                timeline_start=0.0,
                timeline_end=video_info.duration,
                track_id="",  # 将在添加到轨道时设置
                track_type=track_type,
                video_info=video_info
            )

            # 创建元数据
            metadata = self._create_metadata(file_path, video_info)
            self.metadata_cache[clip.id] = metadata

            # 缓存剪辑
            self.clips_cache[clip.id] = clip

            # 生成缩略图
            thumbnail_path = self._generate_thumbnail(clip)
            if thumbnail_path:
                metadata.thumbnail_path = thumbnail_path
                self.thumbnails_cache[clip.id] = thumbnail_path

            # 添加到分析队列
            self.analysis_queue.append(clip.id)

            # 更新性能统计
            self.performance_stats['total_clips_created'] += 1

            # 发送事件
            self.event_bus.publish("clip_created", {
                'clip_id': clip.id,
                'name': name,
                'file_path': file_path,
                'track_type': track_type.value
            })

            self.logger.info(f"创建剪辑: {name} ({clip.id})")
            return clip

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"创建剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ClipManager",
                    operation="create_clip"
                ),
                user_message="无法创建剪辑"
            )
            self.error_handler.handle_error(error_info)
            return None

    def _create_metadata(self, file_path: str, video_info: VideoInfo) -> ClipMetadata:
        """创建剪辑元数据"""
        try:
            # 确定文件格式
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            format_map = {
                'mp4': ClipFormat.MP4,
                'mov': ClipFormat.MOV,
                'avi': ClipFormat.AVI,
                'mkv': ClipFormat.MKV,
                'wmv': ClipFormat.WMV,
                'flv': ClipFormat.FLV,
                'webm': ClipFormat.WEBM,
                'm4v': ClipFormat.M4V
            }
            clip_format = format_map.get(file_ext, ClipFormat.MP4)

            # 确定质量级别
            if video_info.width >= 1920 and video_info.height >= 1080:
                quality = ClipQuality.HIGH
            elif video_info.width >= 1280 and video_info.height >= 720:
                quality = ClipQuality.MEDIUM
            else:
                quality = ClipQuality.LOW

            return ClipMetadata(
                format=clip_format,
                quality=quality,
                resolution=(video_info.width, video_info.height),
                frame_rate=video_info.frame_rate,
                duration=video_info.duration,
                file_size=os.path.getsize(file_path),
                bitrate=video_info.bit_rate,
                codec=video_info.video_codec,
                audio_codec=video_info.audio_codec,
                audio_channels=video_info.audio_channels,
                audio_sample_rate=video_info.sample_rate,
                has_audio=video_info.has_audio,
                has_video=video_info.has_video
            )

        except Exception as e:
            self.logger.error(f"创建元数据失败: {e}")
            return ClipMetadata(
                format=ClipFormat.MP4,
                quality=ClipQuality.MEDIUM,
                resolution=(1920, 1080),
                frame_rate=30.0,
                duration=0.0,
                file_size=0,
                bitrate=0,
                codec="unknown",
                audio_codec="unknown",
                audio_channels=0,
                audio_sample_rate=0,
                has_audio=False,
                has_video=False
            )

    def _generate_thumbnail(self, clip: Clip) -> Optional[str]:
        """生成缩略图"""
        try:
            thumbnail_filename = f"thumbnail_{clip.id}.jpg"
            thumbnail_path = os.path.join(self.cache_dir, thumbnail_filename)

            # 使用ffmpeg生成缩略图
            success = self.ffmpeg_utils.create_thumbnail(
                clip.file_path,
                thumbnail_path,
                clip.duration * 0.25,  # 取25%位置的帧
                (320, 180)
            )

            if success and os.path.exists(thumbnail_path):
                return thumbnail_path

        except Exception as e:
            self.logger.error(f"生成缩略图失败: {e}")

        return None

    def _analyze_clip(self, clip_id: str) -> None:
        """分析剪辑"""
        try:
            clip = self.clips_cache.get(clip_id)
            if not clip:
                return

            # 使用ffmpeg分析视频
            analysis_result = self.ffmpeg_utils.analyze_video(clip.file_path)

            # 创建分析结果
            analysis = ClipAnalysis(
                brightness=analysis_result.get('brightness', 0.0),
                contrast=analysis_result.get('contrast', 0.0),
                saturation=analysis_result.get('saturation', 0.0),
                sharpness=analysis_result.get('sharpness', 0.0),
                noise_level=analysis_result.get('noise_level', 0.0),
                motion_level=analysis_result.get('motion_level', 0.0),
                audio_level=analysis_result.get('audio_level', 0.0),
                audio_clipping=analysis_result.get('audio_clipping', False),
                scene_changes=analysis_result.get('scene_changes', []),
                dominant_colors=analysis_result.get('dominant_colors', []),
                face_detected=analysis_result.get('face_detected', False),
                face_count=analysis_result.get('face_count', 0),
                text_detected=analysis_result.get('text_detected', False),
                text_regions=analysis_result.get('text_regions', [])
            )

            self.analysis_cache[clip_id] = analysis

            # 更新性能统计
            self.performance_stats['total_clips_analyzed'] += 1

            # 发送事件
            self.event_bus.publish("clip_analyzed", {
                'clip_id': clip_id,
                'analysis': analysis
            })

            self.logger.info(f"剪辑分析完成: {clip_id}")

        except Exception as e:
            self.logger.error(f"分析剪辑失败: {e}")

    def get_clip(self, clip_id: str) -> Optional[Clip]:
        """获取剪辑"""
        return self.clips_cache.get(clip_id)

    def get_clip_metadata(self, clip_id: str) -> Optional[ClipMetadata]:
        """获取剪辑元数据"""
        if clip_id in self.metadata_cache:
            self.performance_stats['cache_hits'] += 1
            return self.metadata_cache[clip_id]
        else:
            self.performance_stats['cache_misses'] += 1
            return None

    def get_clip_analysis(self, clip_id: str) -> Optional[ClipAnalysis]:
        """获取剪辑分析结果"""
        if clip_id in self.analysis_cache:
            return self.analysis_cache[clip_id]
        return None

    def get_all_clips(self) -> List[Clip]:
        """获取所有剪辑"""
        return list(self.clips_cache.values())

    def get_clips_by_type(self, track_type: TrackType) -> List[Clip]:
        """获取指定类型的剪辑"""
        return [clip for clip in self.clips_cache.values() if clip.track_type == track_type]

    def duplicate_clip(self, clip_id: str, new_name: Optional[str] = None) -> Optional[Clip]:
        """复制剪辑"""
        try:
            original_clip = self.clips_cache.get(clip_id)
            if not original_clip:
                return None

            # 创建新剪辑
            new_clip = Clip(
                id=str(uuid.uuid4()),
                name=new_name or f"{original_clip.name}_copy",
                file_path=original_clip.file_path,
                start_time=original_clip.start_time,
                end_time=original_clip.end_time,
                timeline_start=original_clip.timeline_start,
                timeline_end=original_clip.timeline_end,
                track_id=original_clip.track_id,
                track_type=original_clip.track_type,
                video_info=original_clip.video_info,
                metadata=original_clip.metadata.copy()
            )

            # 复制关键帧
            for property_name, keyframes in original_clip.keyframes.items():
                for keyframe in keyframes:
                    new_keyframe = copy.deepcopy(keyframe)
                    new_keyframe.id = str(uuid.uuid4())
                    new_clip.add_keyframe(new_keyframe)

            # 缓存新剪辑
            self.clips_cache[new_clip.id] = new_clip

            # 复制元数据
            if clip_id in self.metadata_cache:
                self.metadata_cache[new_clip.id] = copy.deepcopy(self.metadata_cache[clip_id])

            # 复制分析结果
            if clip_id in self.analysis_cache:
                self.analysis_cache[new_clip.id] = copy.deepcopy(self.analysis_cache[clip_id])

            # 发送事件
            self.event_bus.publish("clip_duplicated", {
                'original_clip_id': clip_id,
                'new_clip_id': new_clip.id,
                'name': new_clip.name
            })

            self.logger.info(f"复制剪辑: {original_clip.name} -> {new_clip.name}")
            return new_clip

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"复制剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ClipManager",
                    operation="duplicate_clip"
                ),
                user_message="无法复制剪辑"
            )
            self.error_handler.handle_error(error_info)
            return None

    def crop_clip(self, clip_id: str, x: int, y: int, width: int, height: int) -> bool:
        """裁剪剪辑"""
        try:
            clip = self.clips_cache.get(clip_id)
            if not clip:
                return False

            # 验证裁剪参数
            if width <= 0 or height <= 0:
                return False

            if x < 0 or y < 0:
                return False

            # 添加裁剪效果
            crop_effect = ClipEffect(
                id=f"crop_{clip_id}",
                name="裁剪",
                type="crop",
                parameters={
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "original_width": clip.video_info.width if clip.video_info else 1920,
                    "original_height": clip.video_info.height if clip.video_info else 1080
                }
            )

            # 应用效果
            success = self._apply_effect(clip, crop_effect)
            if success:
                # 更新元数据
                if clip_id in self.metadata_cache:
                    metadata = self.metadata_cache[clip_id]
                    metadata.resolution = (width, height)

                # 发送事件
                self.event_bus.publish("clip_cropped", {
                    'clip_id': clip_id,
                    'crop_params': {"x": x, "y": y, "width": width, "height": height}
                })

                self.logger.info(f"裁剪剪辑: {clip_id} [{width}x{height}]")
                return True

            return False

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"裁剪剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ClipManager",
                    operation="crop_clip"
                ),
                user_message="无法裁剪剪辑"
            )
            self.error_handler.handle_error(error_info)
            return False

    def rotate_clip(self, clip_id: str, angle: float) -> bool:
        """旋转剪辑"""
        try:
            clip = self.clips_cache.get(clip_id)
            if not clip:
                return False

            # 添加旋转效果
            rotate_effect = ClipEffect(
                id=f"rotate_{clip_id}",
                name="旋转",
                type="rotate",
                parameters={"angle": angle}
            )

            # 应用效果
            success = self._apply_effect(clip, rotate_effect)
            if success:
                # 发送事件
                self.event_bus.publish("clip_rotated", {
                    'clip_id': clip_id,
                    'angle': angle
                })

                self.logger.info(f"旋转剪辑: {clip_id} [{angle}°]")
                return True

            return False

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"旋转剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ClipManager",
                    operation="rotate_clip"
                ),
                user_message="无法旋转剪辑"
            )
            self.error_handler.handle_error(error_info)
            return False

    def scale_clip(self, clip_id: str, scale_x: float, scale_y: float) -> bool:
        """缩放剪辑"""
        try:
            clip = self.clips_cache.get(clip_id)
            if not clip:
                return False

            if scale_x <= 0 or scale_y <= 0:
                return False

            # 添加缩放效果
            scale_effect = ClipEffect(
                id=f"scale_{clip_id}",
                name="缩放",
                type="scale",
                parameters={"scale_x": scale_x, "scale_y": scale_y}
            )

            # 应用效果
            success = self._apply_effect(clip, scale_effect)
            if success:
                # 发送事件
                self.event_bus.publish("clip_scaled", {
                    'clip_id': clip_id,
                    'scale_x': scale_x,
                    'scale_y': scale_y
                })

                self.logger.info(f"缩放剪辑: {clip_id} [{scale_x}x{scale_y}]")
                return True

            return False

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"缩放剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ClipManager",
                    operation="scale_clip"
                ),
                user_message="无法缩放剪辑"
            )
            self.error_handler.handle_error(error_info)
            return False

    def _apply_effect(self, clip: Clip, effect: ClipEffect) -> bool:
        """应用效果到剪辑"""
        try:
            # 将效果参数添加到剪辑的元数据中
            if 'effects' not in clip.metadata:
                clip.metadata['effects'] = []

            clip.metadata['effects'].append({
                'id': effect.id,
                'name': effect.name,
                'type': effect.type,
                'parameters': effect.parameters,
                'enabled': effect.enabled
            })

            return True

        except Exception as e:
            self.logger.error(f"应用效果失败: {e}")
            return False

    def apply_preset_effect(self, clip_id: str, effect_id: str, parameters: Dict[str, Any] = None) -> bool:
        """应用预设效果"""
        try:
            clip = self.clips_cache.get(clip_id)
            if not clip:
                return False

            effect_template = self.effects_library.get(effect_id)
            if not effect_template:
                return False

            # 创建效果实例
            effect = ClipEffect(
                id=f"{effect_id}_{clip_id}",
                name=effect_template.name,
                type=effect_template.type,
                parameters=parameters or effect_template.parameters.copy(),
                enabled=True
            )

            # 应用效果
            success = self._apply_effect(clip, effect)
            if success:
                # 发送事件
                self.event_bus.publish("effect_applied", {
                    'clip_id': clip_id,
                    'effect_id': effect_id,
                    'effect_name': effect.name
                })

                self.logger.info(f"应用效果: {effect.name} 到剪辑 {clip_id}")
                return True

            return False

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"应用效果失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ClipManager",
                    operation="apply_preset_effect"
                ),
                user_message="无法应用效果"
            )
            self.error_handler.handle_error(error_info)
            return False

    def get_available_effects(self, effect_type: Optional[str] = None) -> List[ClipEffect]:
        """获取可用效果"""
        if effect_type:
            return [effect for effect in self.effects_library.values() if effect.type == effect_type]
        return list(self.effects_library.values())

    def get_available_transitions(self) -> List[ClipTransition]:
        """获取可用转场"""
        return list(self.transitions_library.values())

    def optimize_clip(self, clip_id: str, optimization_params: Dict[str, Any]) -> bool:
        """优化剪辑"""
        try:
            clip = self.clips_cache.get(clip_id)
            if not clip:
                return False

            # 应用优化参数
            if 'brightness' in optimization_params:
                self.apply_preset_effect(clip_id, 'brightness', {'level': optimization_params['brightness']})

            if 'contrast' in optimization_params:
                self.apply_preset_effect(clip_id, 'contrast', {'level': optimization_params['contrast']})

            if 'saturation' in optimization_params:
                self.apply_preset_effect(clip_id, 'saturation', {'level': optimization_params['saturation']})

            if 'sharpness' in optimization_params:
                self.apply_preset_effect(clip_id, 'sharpen', {'intensity': optimization_params['sharpness']})

            if 'noise_reduction' in optimization_params:
                self.apply_preset_effect(clip_id, 'noise_reduction', {'level': optimization_params['noise_reduction']})

            # 发送事件
            self.event_bus.publish("clip_optimized", {
                'clip_id': clip_id,
                'optimization_params': optimization_params
            })

            self.logger.info(f"优化剪辑: {clip_id}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"优化剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ClipManager",
                    operation="optimize_clip"
                ),
                user_message="无法优化剪辑"
            )
            self.error_handler.handle_error(error_info)
            return False

    def merge_clips(self, clip_ids: List[str], output_path: str) -> bool:
        """合并剪辑"""
        try:
            if len(clip_ids) < 2:
                return False

            # 获取剪辑信息
            clips = []
            for clip_id in clip_ids:
                clip = self.clips_cache.get(clip_id)
                if clip:
                    clips.append(clip)

            if len(clips) < 2:
                return False

            # 使用ffmpeg合并视频
            success = self.ffmpeg_utils.merge_videos(
                [clip.file_path for clip in clips],
                output_path
            )

            if success:
                # 发送事件
                self.event_bus.publish("clips_merged", {
                    'clip_ids': clip_ids,
                    'output_path': output_path
                })

                self.logger.info(f"合并剪辑: {len(clip_ids)} 个剪辑 -> {output_path}")
                return True

            return False

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"合并剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ClipManager",
                    operation="merge_clips"
                ),
                user_message="无法合并剪辑"
            )
            self.error_handler.handle_error(error_info)
            return False

    def get_clip_statistics(self) -> Dict[str, Any]:
        """获取剪辑统计信息"""
        total_clips = len(self.clips_cache)
        video_clips = len([clip for clip in self.clips_cache.values() if clip.track_type == TrackType.VIDEO])
        audio_clips = len([clip for clip in self.clips_cache.values() if clip.track_type == TrackType.AUDIO])

        # 计算总时长
        total_duration = sum(clip.get_duration() for clip in self.clips_cache.values())

        # 计算平均分析时间
        avg_analysis_time = 0.0
        if self.performance_stats['total_clips_analyzed'] > 0:
            avg_analysis_time = self.performance_stats['processing_time'] / self.performance_stats['total_clips_analyzed']

        return {
            'total_clips': total_clips,
            'video_clips': video_clips,
            'audio_clips': audio_clips,
            'total_duration': total_duration,
            'cache_hits': self.performance_stats['cache_hits'],
            'cache_misses': self.performance_stats['cache_misses'],
            'cache_hit_rate': self.performance_stats['cache_hits'] / (self.performance_stats['cache_hits'] + self.performance_stats['cache_misses']) if (self.performance_stats['cache_hits'] + self.performance_stats['cache_misses']) > 0 else 0,
            'analysis_queue_size': len(self.analysis_queue),
            'avg_analysis_time': avg_analysis_time,
            'performance': self.performance_stats.copy()
        }

    def _on_clip_created(self, data: Any) -> None:
        """处理剪辑创建事件"""
        self.logger.debug(f"剪辑创建: {data}")

    def _on_clip_modified(self, data: Any) -> None:
        """处理剪辑修改事件"""
        self.logger.debug(f"剪辑修改: {data}")

    def _on_clip_deleted(self, data: Any) -> None:
        """处理剪辑删除事件"""
        self.logger.debug(f"剪辑删除: {data}")

    def _on_timeline_modified(self, data: Any) -> None:
        """处理时间线修改事件"""
        self.logger.debug(f"时间线修改: {data}")

    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 停止分析线程
            self.analysis_stop_event.set()
            if self.analysis_thread:
                self.analysis_thread.join(timeout=5.0)

            # 清理缓存
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)

            # 清理剪辑缓存
            self.clips_cache.clear()
            self.metadata_cache.clear()
            self.analysis_cache.clear()
            self.thumbnails_cache.clear()

            self.logger.info("剪辑管理器资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局剪辑管理器实例
_clip_manager: Optional[ClipManager] = None


def get_clip_manager(timeline_engine: Optional[TimelineEngine] = None) -> ClipManager:
    """获取全局剪辑管理器实例"""
    global _clip_manager
    if _clip_manager is None:
        _clip_manager = ClipManager(timeline_engine)
    return _clip_manager


def cleanup_clip_manager() -> None:
    """清理全局剪辑管理器实例"""
    global _clip_manager
    if _clip_manager is not None:
        _clip_manager.cleanup()
        _clip_manager = None