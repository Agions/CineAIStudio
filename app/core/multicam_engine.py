#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 多摄像机编辑系统
专业级多摄像机源管理、同步、切换和自动剪辑功能
"""

import os
import time
import threading
import asyncio
import uuid
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import copy
import weakref
from contextlib import asynccontextmanager
import numpy as np
from datetime import datetime, timedelta

from .logger import get_logger
from .event_system import EventBus
from .service_container import ServiceContainer
from .video_engine import get_video_engine, EngineState
from .timeline_engine import TimelineEngine, Track, Clip, TrackType, TimeCode
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import get_ffmpeg_utils, VideoInfo, VideoCodec, AudioCodec


class CameraAngle(Enum):
    """摄像机角度枚举"""
    WIDE = "wide"          # 全景
    MEDIUM = "medium"      # 中景
    CLOSE_UP = "close_up"   # 特写
    OVER_SHOULDER = "over_shoulder"  # 过肩
    LOW_ANGLE = "low_angle"         # 仰角
    HIGH_ANGLE = "high_angle"        # 俯角
    DOLLY = "dolly"        # 移动
    HANDHELD = "handheld"  # 手持
    AERIAL = "aerial"      # 航拍
    CUSTOM = "custom"      # 自定义


class SyncMethod(Enum):
    """同步方法枚举"""
    TIMECODE = "timecode"      # 时间码同步
    AUDIO_WAVE = "audio_wave"  # 音频波形同步
    MOTION_DETECT = "motion"   # 运动检测同步
    MANUAL = "manual"         # 手动同步
    MARKER = "marker"         # 标记同步


class SwitchMode(Enum):
    """切换模式枚举"""
    MANUAL = "manual"           # 手动切换
    AUTO_CUT = "auto_cut"       # 自动剪辑
    AUTO_MIX = "auto_mix"       # 自动混合
    FOLLOW_AUDIO = "audio"      # 跟随音频
    FOLLOW_MOTION = "motion"    # 跟随运动
    SCHEDULED = "scheduled"     # 计划切换


class RecordingStatus(Enum):
    """录制状态枚举"""
    IDLE = "idle"
    PREPARING = "preparing"
    RECORDING = "recording"
    PAUSED = "paused"
    STOPPING = "stopping"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class CameraSource:
    """摄像机源数据类"""
    id: str
    name: str
    file_path: str
    camera_angle: CameraAngle
    position: Tuple[int, int] = (0, 0)  # 位置坐标
    offset: float = 0.0  # 时间偏移（秒）
    gain: float = 1.0    # 音频增益
    color_grade: Dict[str, Any] = field(default_factory=dict)

    # 同步信息
    sync_offset: float = 0.0
    sync_confidence: float = 0.0
    sync_method: SyncMethod = SyncMethod.MANUAL

    # 视频信息
    video_info: Optional[VideoInfo] = None
    thumbnail_path: Optional[str] = None

    # 状态
    is_active: bool = True
    is_recording: bool = False
    is_enabled: bool = True

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = str(uuid.uuid4())

    def get_synced_time(self, timeline_time: float) -> float:
        """获取同步后的时间"""
        return timeline_time - self.sync_offset + self.offset

    def get_original_time(self, synced_time: float) -> float:
        """获取原始时间"""
        return synced_time + self.sync_offset - self.offset


@dataclass
class MultiCamClip:
    """多摄像机剪辑数据类"""
    id: str
    start_time: float
    end_time: float
    duration: float
    primary_camera_id: str
    secondary_camera_ids: List[str] = field(default_factory=list)

    # 切换信息
    camera_switches: List[Dict[str, Any]] = field(default_factory=list)
    transition_points: List[Dict[str, Any]] = field(default_factory=list)

    # 自动剪辑决策
    auto_cut_points: List[Dict[str, Any]] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)

    # 音频信息
    audio_mix: Dict[str, float] = field(default_factory=dict)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = str(uuid.uuid4())
        self.duration = self.end_time - self.start_time


@dataclass
class MultiCamProject:
    """多摄像机项目数据类"""
    id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    # 摄像机源
    camera_sources: Dict[str, CameraSource] = field(default_factory=dict)
    camera_order: List[str] = field(default_factory=list)

    # 剪辑
    clips: List[MultiCamClip] = field(default_factory=list)

    # 同步设置
    sync_method: SyncMethod = SyncMethod.AUDIO_WAVE
    sync_accuracy: float = 0.01  # 同步精度（秒）

    # 切换设置
    switch_mode: SwitchMode = SwitchMode.MANUAL
    auto_switch_settings: Dict[str, Any] = field(default_factory=dict)

    # 时间线设置
    timeline_duration: float = 0.0
    frame_rate: float = 30.0

    # 导出设置
    export_settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = str(uuid.uuid4())


class MultiCamEngine:
    """多摄像机引擎核心类"""

    def __init__(self, timeline_engine: Optional[TimelineEngine] = None, logger=None):
        """初始化多摄像机引擎"""
        self.logger = logger or get_logger("MultiCamEngine")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.service_container = ServiceContainer()
        self.timeline_engine = timeline_engine or get_timeline_engine()
        self.video_engine = get_video_engine()
        self.ffmpeg_utils = get_ffmpeg_utils()

        # 项目管理
        self.current_project: Optional[MultiCamProject] = None
        self.projects: Dict[str, MultiCamProject] = field(default_factory=dict)

        # 摄像机管理
        self.camera_sources: Dict[str, CameraSource] = {}
        self.active_cameras: Set[str] = set()
        self.camera_lock = threading.Lock()

        # 同步引擎
        self.sync_engine = MultiCamSyncEngine(self)
        self.switch_engine = MultiCamSwitchEngine(self)
        self.analysis_engine = MultiCamAnalysisEngine(self)

        # 实时预览
        self.preview_manager = MultiCamPreviewManager(self)

        # 录制控制
        self.recording_controller = MultiCamRecordingController(self)

        # 性能监控
        self.performance_stats = {
            'total_operations': 0,
            'sync_operations': 0,
            'switch_operations': 0,
            'analysis_operations': 0,
            'camera_count': 0,
            'clip_count': 0,
            'processing_time': 0.0,
            'memory_usage': 0
        }

        # 初始化
        self._initialize()

    def _initialize(self) -> None:
        """初始化引擎"""
        try:
            # 注册服务
            self._register_services()

            # 设置事件处理器
            self._setup_event_handlers()

            # 启动子系统
            self.sync_engine.start()
            self.switch_engine.start()
            self.analysis_engine.start()

            self.logger.info("多摄像机引擎初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"多摄像机引擎初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamEngine",
                    operation="initialize"
                ),
                user_message="多摄像机引擎初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _register_services(self) -> None:
        """注册服务"""
        try:
            self.service_container.register(MultiCamEngine, self)
            self.service_container.register(MultiCamSyncEngine, self.sync_engine)
            self.service_container.register(MultiCamSwitchEngine, self.switch_engine)
            self.service_container.register(MultiCamAnalysisEngine, self.analysis_engine)
            self.logger.info("服务注册完成")
        except Exception as e:
            self.logger.error(f"服务注册失败: {str(e)}")

    def _setup_event_handlers(self) -> None:
        """设置事件处理器"""
        try:
            self.event_bus.subscribe("camera_added", self._on_camera_added)
            self.event_bus.subscribe("camera_removed", self._on_camera_removed)
            self.event_bus.subscribe("sync_completed", self._on_sync_completed)
            self.event_bus.subscribe("switch_performed", self._on_switch_performed)
            self.event_bus.subscribe("clip_created", self._on_clip_created)
            self.logger.info("事件处理器设置完成")
        except Exception as e:
            self.logger.error(f"事件处理器设置失败: {str(e)}")

    def create_project(self, name: str, description: str = "") -> str:
        """创建多摄像机项目"""
        try:
            project_id = str(uuid.uuid4())
            project = MultiCamProject(
                id=project_id,
                name=name,
                description=description
            )

            self.projects[project_id] = project
            self.current_project = project

            # 发送事件
            self.event_bus.publish("project_created", {
                'project_id': project_id,
                'name': name,
                'description': description
            })

            self.logger.info(f"创建多摄像机项目: {name} ({project_id})")
            return project_id

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"创建项目失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamEngine",
                    operation="create_project"
                ),
                user_message="无法创建多摄像机项目"
            )
            self.error_handler.handle_error(error_info)
            raise

    def add_camera_source(self, file_path: str, name: str,
                         camera_angle: CameraAngle = CameraAngle.WIDE) -> str:
        """添加摄像机源"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"视频文件不存在: {file_path}")

            # 获取视频信息
            video_info = self.ffmpeg_utils.get_video_info(file_path)

            # 创建摄像机源
            camera_id = str(uuid.uuid4())
            camera_source = CameraSource(
                id=camera_id,
                name=name,
                file_path=file_path,
                camera_angle=camera_angle,
                video_info=video_info
            )

            with self.camera_lock:
                self.camera_sources[camera_id] = camera_source
                if self.current_project:
                    self.current_project.camera_sources[camera_id] = camera_source
                    self.current_project.camera_order.append(camera_id)

            # 更新性能统计
            self.performance_stats['camera_count'] = len(self.camera_sources)

            # 发送事件
            self.event_bus.publish("camera_added", {
                'camera_id': camera_id,
                'name': name,
                'file_path': file_path,
                'camera_angle': camera_angle.value
            })

            self.logger.info(f"添加摄像机源: {name} ({camera_id})")
            return camera_id

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.HIGH,
                message=f"添加摄像机源失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamEngine",
                    operation="add_camera_source"
                ),
                user_message="无法添加摄像机源"
            )
            self.error_handler.handle_error(error_info)
            raise

    def remove_camera_source(self, camera_id: str) -> bool:
        """移除摄像机源"""
        try:
            with self.camera_lock:
                if camera_id not in self.camera_sources:
                    return False

                camera_source = self.camera_sources[camera_id]

                # 从当前项目中移除
                if self.current_project and camera_id in self.current_project.camera_sources:
                    del self.current_project.camera_sources[camera_id]
                    if camera_id in self.current_project.camera_order:
                        self.current_project.camera_order.remove(camera_id)

                # 移除摄像机源
                del self.camera_sources[camera_id]
                self.active_cameras.discard(camera_id)

            # 更新性能统计
            self.performance_stats['camera_count'] = len(self.camera_sources)

            # 发送事件
            self.event_bus.publish("camera_removed", {
                'camera_id': camera_id,
                'name': camera_source.name
            })

            self.logger.info(f"移除摄像机源: {camera_source.name} ({camera_id})")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"移除摄像机源失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamEngine",
                    operation="remove_camera_source"
                ),
                user_message="无法移除摄像机源"
            )
            self.error_handler.handle_error(error_info)
            return False

    def synchronize_cameras(self, method: SyncMethod = SyncMethod.AUDIO_WAVE,
                          reference_camera_id: Optional[str] = None) -> bool:
        """同步摄像机"""
        try:
            if len(self.camera_sources) < 2:
                return False

            # 选择参考摄像机
            if not reference_camera_id:
                reference_camera_id = next(iter(self.camera_sources.keys()))

            reference_camera = self.camera_sources.get(reference_camera_id)
            if not reference_camera:
                return False

            # 执行同步
            sync_results = self.sync_engine.synchronize_cameras(
                list(self.camera_sources.values()),
                reference_camera,
                method
            )

            # 应用同步结果
            for camera_id, sync_offset in sync_results.items():
                if camera_id in self.camera_sources:
                    self.camera_sources[camera_id].sync_offset = sync_offset

            # 更新项目同步设置
            if self.current_project:
                self.current_project.sync_method = method

            # 更新性能统计
            self.performance_stats['sync_operations'] += 1

            # 发送事件
            self.event_bus.publish("sync_completed", {
                'method': method.value,
                'reference_camera': reference_camera_id,
                'sync_results': sync_results
            })

            self.logger.info(f"摄像机同步完成: {method.value}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"摄像机同步失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamEngine",
                    operation="synchronize_cameras"
                ),
                user_message="摄像机同步失败"
            )
            self.error_handler.handle_error(error_info)
            return False

    def create_multicam_clip(self, start_time: float, end_time: float,
                           primary_camera_id: str) -> Optional[str]:
        """创建多摄像机剪辑"""
        try:
            if primary_camera_id not in self.camera_sources:
                return None

            primary_camera = self.camera_sources[primary_camera_id]

            # 创建剪辑
            clip_id = str(uuid.uuid4())
            multicam_clip = MultiCamClip(
                id=clip_id,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                primary_camera_id=primary_camera_id,
                secondary_camera_ids=[cid for cid in self.camera_sources.keys() if cid != primary_camera_id]
            )

            # 添加到项目
            if self.current_project:
                self.current_project.clips.append(multicam_clip)
                self.current_project.timeline_duration = max(
                    self.current_project.timeline_duration,
                    end_time
                )

            # 更新性能统计
            self.performance_stats['clip_count'] += 1

            # 发送事件
            self.event_bus.publish("clip_created", {
                'clip_id': clip_id,
                'start_time': start_time,
                'end_time': end_time,
                'primary_camera': primary_camera_id
            })

            self.logger.info(f"创建多摄像机剪辑: {clip_id}")
            return clip_id

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"创建多摄像机剪辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamEngine",
                    operation="create_multicam_clip"
                ),
                user_message="无法创建多摄像机剪辑"
            )
            self.error_handler.handle_error(error_info)
            return None

    def switch_camera(self, timeline_time: float, target_camera_id: str,
                     transition_duration: float = 0.0) -> bool:
        """切换摄像机"""
        try:
            if not self.current_project:
                return False

            # 执行切换
            success = self.switch_engine.switch_camera(
                timeline_time,
                target_camera_id,
                transition_duration
            )

            if success:
                # 更新性能统计
                self.performance_stats['switch_operations'] += 1

                # 发送事件
                self.event_bus.publish("switch_performed", {
                    'timeline_time': timeline_time,
                    'target_camera': target_camera_id,
                    'transition_duration': transition_duration
                })

                self.logger.info(f"摄像机切换: {target_camera_id} @ {timeline_time}")

            return success

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"摄像机切换失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamEngine",
                    operation="switch_camera"
                ),
                user_message="摄像机切换失败"
            )
            self.error_handler.handle_error(error_info)
            return False

    def analyze_footage(self, camera_ids: List[str] = None) -> Dict[str, Any]:
        """分析素材"""
        try:
            if not self.current_project:
                return {}

            # 选择要分析的摄像机
            cameras_to_analyze = camera_ids or list(self.camera_sources.keys())

            # 执行分析
            analysis_results = self.analysis_engine.analyze_footage(
                [self.camera_sources[cid] for cid in cameras_to_analyze if cid in self.camera_sources]
            )

            # 更新性能统计
            self.performance_stats['analysis_operations'] += 1

            # 发送事件
            self.event_bus.publish("analysis_completed", {
                'camera_count': len(cameras_to_analyze),
                'analysis_results': analysis_results
            })

            self.logger.info(f"素材分析完成: {len(cameras_to_analyze)} 个摄像机")
            return analysis_results

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"素材分析失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamEngine",
                    operation="analyze_footage"
                ),
                user_message="素材分析失败"
            )
            self.error_handler.handle_error(error_info)
            return {}

    def export_multicam_edit(self, output_path: str,
                           export_settings: Dict[str, Any] = None) -> bool:
        """导出多摄像机编辑"""
        try:
            if not self.current_project:
                return False

            # 合并导出设置
            final_settings = self.current_project.export_settings.copy()
            if export_settings:
                final_settings.update(export_settings)

            # 执行导出
            success = self.switch_engine.export_edit(
                self.current_project,
                output_path,
                final_settings
            )

            if success:
                self.logger.info(f"多摄像机编辑导出完成: {output_path}")

            return success

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.EXPORT,
                severity=ErrorSeverity.HIGH,
                message=f"导出多摄像机编辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamEngine",
                    operation="export_multicam_edit"
                ),
                user_message="导出多摄像机编辑失败"
            )
            self.error_handler.handle_error(error_info)
            return False

    def get_camera_preview(self, camera_id: str, time: float) -> Optional[str]:
        """获取摄像机预览帧"""
        try:
            if camera_id not in self.camera_sources:
                return None

            return self.preview_manager.get_preview_frame(
                self.camera_sources[camera_id],
                time
            )

        except Exception as e:
            self.logger.error(f"获取摄像机预览失败: {str(e)}")
            return None

    def start_recording(self, camera_ids: List[str] = None) -> bool:
        """开始录制"""
        try:
            cameras_to_record = camera_ids or list(self.camera_sources.keys())
            return self.recording_controller.start_recording(cameras_to_record)

        except Exception as e:
            self.logger.error(f"开始录制失败: {str(e)}")
            return False

    def stop_recording(self) -> bool:
        """停止录制"""
        try:
            return self.recording_controller.stop_recording()

        except Exception as e:
            self.logger.error(f"停止录制失败: {str(e)}")
            return False

    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            'current_project': self.current_project.id if self.current_project else None,
            'camera_count': len(self.camera_sources),
            'active_cameras': len(self.active_cameras),
            'clip_count': len(self.current_project.clips) if self.current_project else 0,
            'sync_status': self.sync_engine.get_status(),
            'switch_status': self.switch_engine.get_status(),
            'analysis_status': self.analysis_engine.get_status(),
            'performance': self.performance_stats.copy()
        }

    def _on_camera_added(self, data: Any) -> None:
        """处理摄像机添加事件"""
        self.logger.debug(f"摄像机添加: {data}")

    def _on_camera_removed(self, data: Any) -> None:
        """处理摄像机移除事件"""
        self.logger.debug(f"摄像机移除: {data}")

    def _on_sync_completed(self, data: Any) -> None:
        """处理同步完成事件"""
        self.logger.debug(f"同步完成: {data}")

    def _on_switch_performed(self, data: Any) -> None:
        """处理切换执行事件"""
        self.logger.debug(f"切换执行: {data}")

    def _on_clip_created(self, data: Any) -> None:
        """处理剪辑创建事件"""
        self.logger.debug(f"剪辑创建: {data}")

    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 停止子系统
            self.sync_engine.stop()
            self.switch_engine.stop()
            self.analysis_engine.stop()

            # 清理预览管理器
            self.preview_manager.cleanup()

            # 停止录制
            self.recording_controller.stop_recording()

            self.logger.info("多摄像机引擎资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局多摄像机引擎实例
_multicam_engine: Optional[MultiCamEngine] = None


def get_multicam_engine(timeline_engine: Optional[TimelineEngine] = None) -> MultiCamEngine:
    """获取全局多摄像机引擎实例"""
    global _multicam_engine
    if _multicam_engine is None:
        _multicam_engine = MultiCamEngine(timeline_engine)
    return _multicam_engine


def cleanup_multicam_engine() -> None:
    """清理全局多摄像机引擎实例"""
    global _multicam_engine
    if _multicam_engine is not None:
        _multicam_engine.cleanup()
        _multicam_engine = None


class MultiCamSyncEngine:
    """多摄像机同步引擎"""

    def __init__(self, multicam_engine: MultiCamEngine):
        self.multicam_engine = multicam_engine
        self.logger = multicam_engine.logger
        self.is_running = False
        self.sync_thread: Optional[threading.Thread] = None
        self.sync_lock = threading.Lock()

    def start(self) -> None:
        """启动同步引擎"""
        self.is_running = True
        self.logger.info("多摄像机同步引擎已启动")

    def stop(self) -> None:
        """停止同步引擎"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5.0)
        self.logger.info("多摄像机同步引擎已停止")

    def synchronize_cameras(self, cameras: List[CameraSource],
                          reference_camera: CameraSource,
                          method: SyncMethod) -> Dict[str, float]:
        """同步摄像机"""
        sync_results = {}

        try:
            if method == SyncMethod.TIMECODE:
                sync_results = self._sync_by_timecode(cameras, reference_camera)
            elif method == SyncMethod.AUDIO_WAVE:
                sync_results = self._sync_by_audio_wave(cameras, reference_camera)
            elif method == SyncMethod.MOTION_DETECT:
                sync_results = self._sync_by_motion(cameras, reference_camera)
            else:
                sync_results = self._sync_manual(cameras, reference_camera)

            return sync_results

        except Exception as e:
            self.logger.error(f"摄像机同步失败: {str(e)}")
            return {}

    def _sync_by_timecode(self, cameras: List[CameraSource],
                        reference_camera: CameraSource) -> Dict[str, float]:
        """基于时间码同步"""
        sync_results = {}

        for camera in cameras:
            if camera.id == reference_camera.id:
                sync_results[camera.id] = 0.0
                continue

            # 从视频信息中提取时间码
            if camera.video_info and reference_camera.video_info:
                # 这里简化处理，实际需要解析时间码
                timecode_diff = 0.0
                sync_results[camera.id] = timecode_diff
                camera.sync_offset = timecode_diff
                camera.sync_confidence = 0.95
                camera.sync_method = SyncMethod.TIMECODE

        return sync_results

    def _sync_by_audio_wave(self, cameras: List[CameraSource],
                           reference_camera: CameraSource) -> Dict[str, float]:
        """基于音频波形同步"""
        sync_results = {}

        try:
            # 提取参考摄像机音频波形
            ref_waveform = self._extract_audio_waveform(reference_camera.file_path)
            if ref_waveform is None:
                return sync_results

            for camera in cameras:
                if camera.id == reference_camera.id:
                    sync_results[camera.id] = 0.0
                    continue

                # 提取当前摄像机音频波形
                camera_waveform = self._extract_audio_waveform(camera.file_path)
                if camera_waveform is None:
                    continue

                # 计算波形相关性
                offset, confidence = self._calculate_waveform_correlation(
                    ref_waveform, camera_waveform
                )

                sync_results[camera.id] = offset
                camera.sync_offset = offset
                camera.sync_confidence = confidence
                camera.sync_method = SyncMethod.AUDIO_WAVE

        except Exception as e:
            self.logger.error(f"音频波形同步失败: {str(e)}")

        return sync_results

    def _sync_by_motion(self, cameras: List[CameraSource],
                       reference_camera: CameraSource) -> Dict[str, float]:
        """基于运动检测同步"""
        sync_results = {}

        try:
            # 提取参考摄像机运动数据
            ref_motion = self._extract_motion_data(reference_camera.file_path)
            if ref_motion is None:
                return sync_results

            for camera in cameras:
                if camera.id == reference_camera.id:
                    sync_results[camera.id] = 0.0
                    continue

                # 提取当前摄像机运动数据
                camera_motion = self._extract_motion_data(camera.file_path)
                if camera_motion is None:
                    continue

                # 计算运动相关性
                offset, confidence = self._calculate_motion_correlation(
                    ref_motion, camera_motion
                )

                sync_results[camera.id] = offset
                camera.sync_offset = offset
                camera.sync_confidence = confidence
                camera.sync_method = SyncMethod.MOTION_DETECT

        except Exception as e:
            self.logger.error(f"运动检测同步失败: {str(e)}")

        return sync_results

    def _sync_manual(self, cameras: List[CameraSource],
                    reference_camera: CameraSource) -> Dict[str, float]:
        """手动同步"""
        sync_results = {}

        for camera in cameras:
            if camera.id == reference_camera.id:
                sync_results[camera.id] = 0.0
            else:
                # 使用当前设置的偏移量
                sync_results[camera.id] = camera.sync_offset
                camera.sync_confidence = 1.0
                camera.sync_method = SyncMethod.MANUAL

        return sync_results

    def _extract_audio_waveform(self, file_path: str) -> Optional[np.ndarray]:
        """提取音频波形"""
        try:
            # 使用FFmpeg提取音频数据
            import subprocess
            import tempfile

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # 提取音频
            cmd = [
                'ffmpeg', '-i', file_path, '-vn', '-ac', '1', '-ar', '44100',
                '-f', 'wav', '-y', tmp_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode != 0:
                return None

            # 读取波形数据
            import wave
            with wave.open(tmp_path, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                waveform = np.frombuffer(frames, dtype=np.int16)
                waveform = waveform.astype(np.float32) / 32768.0

            # 清理临时文件
            os.unlink(tmp_path)

            return waveform

        except Exception as e:
            self.logger.error(f"音频波形提取失败: {str(e)}")
            return None

    def _calculate_waveform_correlation(self, ref_waveform: np.ndarray,
                                      camera_waveform: np.ndarray) -> Tuple[float, float]:
        """计算波形相关性"""
        try:
            # 确保波形长度一致
            min_len = min(len(ref_waveform), len(camera_waveform))
            ref_waveform = ref_waveform[:min_len]
            camera_waveform = camera_waveform[:min_len]

            # 计算互相关
            correlation = np.correlate(ref_waveform, camera_waveform, mode='full')
            max_corr_idx = np.argmax(correlation)
            max_corr_value = correlation[max_corr_idx]

            # 计算偏移量和置信度
            offset = (max_corr_idx - len(camera_waveform) + 1) / 44100.0  # 转换为秒
            confidence = max_corr_value / np.max(correlation)

            return offset, confidence

        except Exception as e:
            self.logger.error(f"波形相关性计算失败: {str(e)}")
            return 0.0, 0.0

    def _extract_motion_data(self, file_path: str) -> Optional[np.ndarray]:
        """提取运动数据"""
        try:
            # 简化的运动检测实现
            # 实际实现需要使用OpenCV等库进行帧差分检测
            motion_data = np.random.random(1000)  # 模拟数据
            return motion_data

        except Exception as e:
            self.logger.error(f"运动数据提取失败: {str(e)}")
            return None

    def _calculate_motion_correlation(self, ref_motion: np.ndarray,
                                   camera_motion: np.ndarray) -> Tuple[float, float]:
        """计算运动相关性"""
        try:
            # 计算运动相关性
            correlation = np.correlate(ref_motion, camera_motion, mode='full')
            max_corr_idx = np.argmax(correlation)
            max_corr_value = correlation[max_corr_idx]

            # 计算偏移量和置信度
            offset = (max_corr_idx - len(camera_motion) + 1) / 30.0  # 假设30fps
            confidence = max_corr_value / np.max(correlation)

            return offset, confidence

        except Exception as e:
            self.logger.error(f"运动相关性计算失败: {str(e)}")
            return 0.0, 0.0

    def get_status(self) -> Dict[str, Any]:
        """获取同步引擎状态"""
        return {
            'is_running': self.is_running,
            'sync_methods': [method.value for method in SyncMethod]
        }


class MultiCamSwitchEngine:
    """多摄像机切换引擎"""

    def __init__(self, multicam_engine: MultiCamEngine):
        self.multicam_engine = multicam_engine
        self.logger = multicam_engine.logger
        self.is_running = False
        self.switch_mode = SwitchMode.MANUAL
        self.auto_switch_thread: Optional[threading.Thread] = None
        self.switch_stop_event = threading.Event()

    def start(self) -> None:
        """启动切换引擎"""
        self.is_running = True
        self.logger.info("多摄像机切换引擎已启动")

    def stop(self) -> None:
        """停止切换引擎"""
        self.is_running = False
        self.switch_stop_event.set()
        if self.auto_switch_thread:
            self.auto_switch_thread.join(timeout=5.0)
        self.logger.info("多摄像机切换引擎已停止")

    def switch_camera(self, timeline_time: float, target_camera_id: str,
                     transition_duration: float = 0.0) -> bool:
        """切换摄像机"""
        try:
            if not self.multicam_engine.current_project:
                return False

            # 找到对应的剪辑
            target_clip = None
            for clip in self.multicam_engine.current_project.clips:
                if clip.start_time <= timeline_time <= clip.end_time:
                    target_clip = clip
                    break

            if not target_clip:
                return False

            # 记录切换点
            switch_point = {
                'time': timeline_time,
                'from_camera': target_clip.primary_camera_id,
                'to_camera': target_camera_id,
                'transition_duration': transition_duration,
                'transition_type': 'cut' if transition_duration == 0 else 'fade'
            }

            target_clip.camera_switches.append(switch_point)

            # 如果是自动切换模式，更新主摄像机
            if self.switch_mode != SwitchMode.MANUAL:
                target_clip.primary_camera_id = target_camera_id

            return True

        except Exception as e:
            self.logger.error(f"摄像机切换失败: {str(e)}")
            return False

    def start_auto_switch(self, mode: SwitchMode, settings: Dict[str, Any] = None) -> bool:
        """启动自动切换"""
        try:
            self.switch_mode = mode
            self.switch_stop_event.clear()

            if mode == SwitchMode.AUTO_CUT:
                self.auto_switch_thread = threading.Thread(
                    target=self._auto_cut_worker,
                    args=(settings or {}),
                    daemon=True
                )
            elif mode == SwitchMode.AUTO_MIX:
                self.auto_switch_thread = threading.Thread(
                    target=self._auto_mix_worker,
                    args=(settings or {}),
                    daemon=True
                )
            elif mode == SwitchMode.FOLLOW_AUDIO:
                self.auto_switch_thread = threading.Thread(
                    target=self._follow_audio_worker,
                    args=(settings or {}),
                    daemon=True
                )
            elif mode == SwitchMode.FOLLOW_MOTION:
                self.auto_switch_thread = threading.Thread(
                    target=self._follow_motion_worker,
                    args=(settings or {}),
                    daemon=True
                )
            else:
                return False

            self.auto_switch_thread.start()
            self.logger.info(f"自动切换已启动: {mode.value}")
            return True

        except Exception as e:
            self.logger.error(f"启动自动切换失败: {str(e)}")
            return False

    def stop_auto_switch(self) -> None:
        """停止自动切换"""
        self.switch_stop_event.set()
        if self.auto_switch_thread:
            self.auto_switch_thread.join(timeout=5.0)
        self.switch_mode = SwitchMode.MANUAL
        self.logger.info("自动切换已停止")

    def _auto_cut_worker(self, settings: Dict[str, Any]) -> None:
        """自动剪辑工作线程"""
        try:
            analysis_interval = settings.get('analysis_interval', 2.0)  # 秒
            confidence_threshold = settings.get('confidence_threshold', 0.7)

            while not self.switch_stop_event.is_set():
                # 分析所有摄像机
                analysis_results = self.multicam_engine.analysis_engine.analyze_footage()

                # 寻找最佳切换点
                current_time = 0.0  # 这里应该从播放器获取当前时间

                for clip in self.multicam_engine.current_project.clips:
                    if clip.start_time <= current_time <= clip.end_time:
                        best_camera = self._find_best_camera_for_cut(
                            analysis_results, clip, confidence_threshold
                        )

                        if best_camera and best_camera != clip.primary_camera_id:
                            self.switch_camera(
                                current_time,
                                best_camera,
                                transition_duration=0.0
                            )

                self.switch_stop_event.wait(analysis_interval)

        except Exception as e:
            self.logger.error(f"自动剪辑工作线程错误: {str(e)}")

    def _auto_mix_worker(self, settings: Dict[str, Any]) -> None:
        """自动混合工作线程"""
        try:
            mix_interval = settings.get('mix_interval', 5.0)
            fade_duration = settings.get('fade_duration', 1.0)

            while not self.switch_stop_event.is_set():
                # 循环切换所有摄像机
                if self.multicam_engine.current_project:
                    cameras = list(self.multicam_engine.current_project.camera_sources.keys())
                    if len(cameras) > 1:
                        current_time = 0.0  # 从播放器获取当前时间

                        for clip in self.multicam_engine.current_project.clips:
                            if clip.start_time <= current_time <= clip.end_time:
                                current_idx = cameras.index(clip.primary_camera_id)
                                next_camera = cameras[(current_idx + 1) % len(cameras)]

                                self.switch_camera(
                                    current_time,
                                    next_camera,
                                    transition_duration=fade_duration
                                )
                                break

                self.switch_stop_event.wait(mix_interval)

        except Exception as e:
            self.logger.error(f"自动混合工作线程错误: {str(e)}")

    def _follow_audio_worker(self, settings: Dict[str, Any]) -> None:
        """跟随音频工作线程"""
        try:
            audio_threshold = settings.get('audio_threshold', 0.5)
            check_interval = settings.get('check_interval', 0.5)

            while not self.switch_stop_event.is_set():
                # 检测音频活跃度
                audio_levels = self._analyze_audio_levels()

                if audio_levels:
                    # 找到音频最活跃的摄像机
                    loudest_camera = max(audio_levels.items(), key=lambda x: x[1])[0]

                    if audio_levels[loudest_camera] > audio_threshold:
                        current_time = 0.0  # 从播放器获取当前时间

                        for clip in self.multicam_engine.current_project.clips:
                            if clip.start_time <= current_time <= clip.end_time:
                                if loudest_camera != clip.primary_camera_id:
                                    self.switch_camera(
                                        current_time,
                                        loudest_camera,
                                        transition_duration=0.3
                                    )
                                break

                self.switch_stop_event.wait(check_interval)

        except Exception as e:
            self.logger.error(f"跟随音频工作线程错误: {str(e)}")

    def _follow_motion_worker(self, settings: Dict[str, Any]) -> None:
        """跟随运动工作线程"""
        try:
            motion_threshold = settings.get('motion_threshold', 0.3)
            check_interval = settings.get('check_interval', 1.0)

            while not self.switch_stop_event.is_set():
                # 检测运动活跃度
                motion_levels = self._analyze_motion_levels()

                if motion_levels:
                    # 找到运动最活跃的摄像机
                    most_active_camera = max(motion_levels.items(), key=lambda x: x[1])[0]

                    if motion_levels[most_active_camera] > motion_threshold:
                        current_time = 0.0  # 从播放器获取当前时间

                        for clip in self.multicam_engine.current_project.clips:
                            if clip.start_time <= current_time <= clip.end_time:
                                if most_active_camera != clip.primary_camera_id:
                                    self.switch_camera(
                                        current_time,
                                        most_active_camera,
                                        transition_duration=0.5
                                    )
                                break

                self.switch_stop_event.wait(check_interval)

        except Exception as e:
            self.logger.error(f"跟随运动工作线程错误: {str(e)}")

    def _find_best_camera_for_cut(self, analysis_results: Dict[str, Any],
                                 clip: MultiCamClip, threshold: float) -> Optional[str]:
        """找到最佳切换摄像机"""
        try:
            # 基于分析结果评估每个摄像机
            camera_scores = {}

            for camera_id in clip.secondary_camera_ids + [clip.primary_camera_id]:
                if camera_id in analysis_results:
                    camera_analysis = analysis_results[camera_id]

                    # 综合评分（可以基于多种因素）
                    score = 0.0

                    # 构图质量
                    if 'composition_score' in camera_analysis:
                        score += camera_analysis['composition_score'] * 0.3

                    # 焦点清晰度
                    if 'focus_score' in camera_analysis:
                        score += camera_analysis['focus_score'] * 0.2

                    # 曝光质量
                    if 'exposure_score' in camera_analysis:
                        score += camera_analysis['exposure_score'] * 0.2

                    # 运动活跃度
                    if 'motion_score' in camera_analysis:
                        score += camera_analysis['motion_score'] * 0.3

                    camera_scores[camera_id] = score

            # 选择得分最高的摄像机
            if camera_scores:
                best_camera = max(camera_scores.items(), key=lambda x: x[1])
                if best_camera[1] > threshold:
                    return best_camera[0]

            return None

        except Exception as e:
            self.logger.error(f"查找最佳摄像机失败: {str(e)}")
            return None

    def _analyze_audio_levels(self) -> Dict[str, float]:
        """分析音频水平"""
        try:
            audio_levels = {}

            for camera_id, camera in self.multicam_engine.camera_sources.items():
                # 简化的音频分析
                # 实际实现需要实时音频分析
                audio_level = np.random.random()  # 模拟数据
                audio_levels[camera_id] = audio_level

            return audio_levels

        except Exception as e:
            self.logger.error(f"音频水平分析失败: {str(e)}")
            return {}

    def _analyze_motion_levels(self) -> Dict[str, float]:
        """分析运动水平"""
        try:
            motion_levels = {}

            for camera_id, camera in self.multicam_engine.camera_sources.items():
                # 简化的运动分析
                # 实际实现需要实时运动检测
                motion_level = np.random.random()  # 模拟数据
                motion_levels[camera_id] = motion_level

            return motion_levels

        except Exception as e:
            self.logger.error(f"运动水平分析失败: {str(e)}")
            return {}

    def export_edit(self, project: MultiCamProject, output_path: str,
                   settings: Dict[str, Any]) -> bool:
        """导出编辑"""
        try:
            # 构建FFmpeg命令
            input_files = []
            filter_complex = []

            # 为每个摄像机源添加输入
            for i, (camera_id, camera) in enumerate(project.camera_sources.items()):
                input_files.extend(['-i', camera.file_path])

                # 应用同步偏移
                if camera.sync_offset != 0:
                    filter_complex.append(f"[{i}:v]setpts=PTS-STARTPTS+{camera.sync_offset}/TB[v{i}]")
                else:
                    filter_complex.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}]")

            # 构建切换逻辑
            current_time = 0.0
            last_camera_idx = 0

            for clip in project.clips:
                # 找到摄像机索引
                camera_idx = None
                for i, camera_id in enumerate(project.camera_sources.keys()):
                    if camera_id == clip.primary_camera_id:
                        camera_idx = i
                        break

                if camera_idx is None:
                    continue

                # 添加切换点
                if camera_idx != last_camera_idx:
                    fade_duration = 0.0
                    for switch in clip.camera_switches:
                        if switch['transition_type'] == 'fade':
                            fade_duration = switch['transition_duration']
                            break

                    if fade_duration > 0:
                        # 淡入淡出切换
                        filter_complex.append(
                            f"[v{last_camera_idx}][v{camera_idx}]xfade=transition=fade:"
                            f"duration={fade_duration}:offset={current_time}[out{len(filter_complex)}]"
                        )
                    else:
                        # 硬切
                        filter_complex.append(f"[v{camera_idx}]split[out{len(filter_complex)}][v{camera_idx}]")

                last_camera_idx = camera_idx
                current_time = clip.end_time

            # 执行导出
            cmd = ['ffmpeg']
            cmd.extend(input_files)
            cmd.extend(['-filter_complex', ','.join(filter_complex)])
            cmd.extend(['-map', f'[out{len(filter_complex)-1}]'])
            cmd.extend(['-c:v', 'libx264', '-preset', 'medium', '-crf', '23'])
            cmd.extend(['-y', output_path])

            result = subprocess.run(cmd, capture_output=True, timeout=3600)

            if result.returncode == 0:
                self.logger.info(f"多摄像机编辑导出成功: {output_path}")
                return True
            else:
                self.logger.error(f"导出失败: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"导出编辑失败: {str(e)}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取切换引擎状态"""
        return {
            'is_running': self.is_running,
            'switch_mode': self.switch_mode.value,
            'auto_switch_active': self.auto_switch_thread is not None
        }


class MultiCamAnalysisEngine:
    """多摄像机分析引擎"""

    def __init__(self, multicam_engine: MultiCamEngine):
        self.multicam_engine = multicam_engine
        self.logger = multicam_engine.logger
        self.is_running = False
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.analysis_lock = threading.Lock()

    def start(self) -> None:
        """启动分析引擎"""
        self.is_running = True
        self.logger.info("多摄像机分析引擎已启动")

    def stop(self) -> None:
        """停止分析引擎"""
        self.is_running = False
        self.logger.info("多摄像机分析引擎已停止")

    def analyze_footage(self, cameras: List[CameraSource]) -> Dict[str, Any]:
        """分析素材"""
        try:
            analysis_results = {}

            for camera in cameras:
                # 检查缓存
                if camera.id in self.analysis_cache:
                    analysis_results[camera.id] = self.analysis_cache[camera.id]
                    continue

                # 执行分析
                camera_analysis = self._analyze_single_camera(camera)
                analysis_results[camera.id] = camera_analysis

                # 缓存结果
                with self.analysis_lock:
                    self.analysis_cache[camera.id] = camera_analysis

            return analysis_results

        except Exception as e:
            self.logger.error(f"素材分析失败: {str(e)}")
            return {}

    def _analyze_single_camera(self, camera: CameraSource) -> Dict[str, Any]:
        """分析单个摄像机素材"""
        try:
            analysis_result = {
                'camera_id': camera.id,
                'camera_name': camera.name,
                'camera_angle': camera.camera_angle.value,
                'analysis_timestamp': datetime.now().isoformat()
            }

            # 构图分析
            composition_score = self._analyze_composition(camera)
            analysis_result['composition_score'] = composition_score

            # 焦点分析
            focus_score = self._analyze_focus(camera)
            analysis_result['focus_score'] = focus_score

            # 曝光分析
            exposure_score = self._analyze_exposure(camera)
            analysis_result['exposure_score'] = exposure_score

            # 运动分析
            motion_score = self._analyze_motion(camera)
            analysis_result['motion_score'] = motion_score

            # 音频质量分析
            audio_quality = self._analyze_audio_quality(camera)
            analysis_result['audio_quality'] = audio_quality

            # 推荐切换点
            recommended_cuts = self._recommend_cut_points(camera)
            analysis_result['recommended_cuts'] = recommended_cuts

            return analysis_result

        except Exception as e:
            self.logger.error(f"单个摄像机分析失败: {str(e)}")
            return {}

    def _analyze_composition(self, camera: CameraSource) -> float:
        """分析构图质量"""
        try:
            # 简化的构图分析
            # 实际实现需要使用计算机视觉算法分析三分法、平衡性等
            if camera.camera_angle in [CameraAngle.WIDE, CameraAngle.MEDIUM]:
                return 0.8
            elif camera.camera_angle == CameraAngle.CLOSE_UP:
                return 0.9
            else:
                return 0.7

        except Exception as e:
            self.logger.error(f"构图分析失败: {str(e)}")
            return 0.5

    def _analyze_focus(self, camera: CameraSource) -> float:
        """分析焦点质量"""
        try:
            # 简化的焦点分析
            # 实际实现需要分析图像清晰度、边缘检测等
            return 0.8

        except Exception as e:
            self.logger.error(f"焦点分析失败: {str(e)}")
            return 0.5

    def _analyze_exposure(self, camera: CameraSource) -> float:
        """分析曝光质量"""
        try:
            # 简化的曝光分析
            # 实际实现需要分析直方图、亮度分布等
            return 0.7

        except Exception as e:
            self.logger.error(f"曝光分析失败: {str(e)}")
            return 0.5

    def _analyze_motion(self, camera: CameraSource) -> float:
        """分析运动活跃度"""
        try:
            # 简化的运动分析
            # 实际实现需要光流法、帧差分等运动检测
            return 0.6

        except Exception as e:
            self.logger.error(f"运动分析失败: {str(e)}")
            return 0.5

    def _analyze_audio_quality(self, camera: CameraSource) -> Dict[str, float]:
        """分析音频质量"""
        try:
            # 简化的音频质量分析
            # 实际实现需要分析信噪比、频率分布等
            return {
                'clarity': 0.8,
                'noise_level': 0.2,
                'dynamic_range': 0.7
            }

        except Exception as e:
            self.logger.error(f"音频质量分析失败: {str(e)}")
            return {}

    def _recommend_cut_points(self, camera: CameraSource) -> List[Dict[str, Any]]:
        """推荐切换点"""
        try:
            # 简化的切换点推荐
            # 实际实现需要基于场景变化、动作完成等
            recommendations = []

            if camera.video_info:
                duration = camera.video_info.duration
                # 每10秒推荐一个切换点
                for t in range(10, int(duration), 10):
                    recommendations.append({
                        'time': t,
                        'confidence': 0.7,
                        'reason': 'regular_cut_point'
                    })

            return recommendations

        except Exception as e:
            self.logger.error(f"切换点推荐失败: {str(e)}")
            return []


class MultiCamPreviewManager:
    """多摄像机预览管理器"""

    def __init__(self, multicam_engine: MultiCamEngine):
        self.multicam_engine = multicam_engine
        self.logger = multicam_engine.logger
        self.preview_cache: Dict[str, Dict[str, str]] = {}
        self.preview_lock = threading.Lock()
        self.cache_dir = "/tmp/cineaistudio/multicam_preview"

        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_preview_frame(self, camera: CameraSource, time: float) -> Optional[str]:
        """获取预览帧"""
        try:
            cache_key = f"{camera.id}_{time:.2f}"

            # 检查缓存
            with self.preview_lock:
                if cache_key in self.preview_cache:
                    return self.preview_cache[cache_key]

            # 生成预览帧
            preview_path = os.path.join(
                self.cache_dir,
                f"preview_{camera.id}_{time:.2f}.jpg"
            )

            if not os.path.exists(preview_path):
                # 使用FFmpeg提取帧
                sync_time = camera.get_synced_time(time)
                self.multicam_engine.ffmpeg_utils.create_thumbnail(
                    camera.file_path,
                    preview_path,
                    sync_time,
                    (320, 180)
                )

            # 缓存结果
            with self.preview_lock:
                self.preview_cache[cache_key] = preview_path

            return preview_path

        except Exception as e:
            self.logger.error(f"获取预览帧失败: {str(e)}")
            return None

    def cleanup_cache(self) -> None:
        """清理缓存"""
        try:
            with self.preview_lock:
                self.preview_cache.clear()

            if os.path.exists(self.cache_dir):
                import shutil
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)

            self.logger.info("预览缓存清理完成")

        except Exception as e:
            self.logger.error(f"预览缓存清理失败: {str(e)}")

    def cleanup(self) -> None:
        """清理资源"""
        self.cleanup_cache()


class MultiCamRecordingController:
    """多摄像机录制控制器"""

    def __init__(self, multicam_engine: MultiCamEngine):
        self.multicam_engine = multicam_engine
        self.logger = multicam_engine.logger
        self.recording_status = RecordingStatus.IDLE
        self.recording_cameras: Set[str] = set()
        self.recording_start_time: Optional[float] = None
        self.recording_output_dir: Optional[str] = None

    def start_recording(self, camera_ids: List[str]) -> bool:
        """开始录制"""
        try:
            if self.recording_status != RecordingStatus.IDLE:
                return False

            self.recording_status = RecordingStatus.PREPARING
            self.recording_cameras = set(camera_ids)
            self.recording_start_time = time.time()

            # 创建输出目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.recording_output_dir = os.path.join(
                "/tmp/cineaistudio/recordings",
                f"multicam_{timestamp}"
            )
            os.makedirs(self.recording_output_dir, exist_ok=True)

            # 为每个摄像机启动录制
            # 这里简化处理，实际需要实现真正的录制功能
            self.recording_status = RecordingStatus.RECORDING

            self.logger.info(f"多摄像机录制已启动: {len(camera_ids)} 个摄像机")
            return True

        except Exception as e:
            self.logger.error(f"启动录制失败: {str(e)}")
            self.recording_status = RecordingStatus.ERROR
            return False

    def stop_recording(self) -> bool:
        """停止录制"""
        try:
            if self.recording_status != RecordingStatus.RECORDING:
                return False

            self.recording_status = RecordingStatus.STOPPING

            # 停止所有摄像机录制
            # 这里简化处理，实际需要停止真正的录制进程

            recording_duration = time.time() - self.recording_start_time

            self.recording_status = RecordingStatus.FINISHED
            self.logger.info(f"多摄像机录制已停止，时长: {recording_duration:.2f}秒")

            # 清理状态
            self.recording_cameras.clear()
            self.recording_start_time = None

            return True

        except Exception as e:
            self.logger.error(f"停止录制失败: {str(e)}")
            self.recording_status = RecordingStatus.ERROR
            return False

    def get_recording_status(self) -> Dict[str, Any]:
        """获取录制状态"""
        return {
            'status': self.recording_status.value,
            'recording_cameras': list(self.recording_cameras),
            'start_time': self.recording_start_time,
            'output_dir': self.recording_output_dir
        }