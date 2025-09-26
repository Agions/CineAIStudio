#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 多摄像机系统集成模块
提供与现有时间线、项目管理和导出系统的完整集成
"""

import os
import json
import threading
import time
import uuid
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import weakref

from .multicam_engine import (
    get_multicam_engine, MultiCamEngine, CameraSource, CameraAngle,
    SyncMethod, SwitchMode, MultiCamProject, MultiCamClip
)
from .timeline_engine import TimelineEngine, Track, Clip, TrackType, TimeCode
from .project_manager import ProjectManager, Project, ProjectMetadata, ProjectType
from .video_engine import VideoEngine, EngineState
from .logger import get_logger
from .event_system import EventBus
from .hardware_acceleration import HardwareAcceleration
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import get_ffmpeg_utils, VideoCodec, AudioCodec
from ..export.export_system import ExportSystem, ExportSettings


class IntegrationMode(Enum):
    """集成模式枚举"""
    STANDALONE = "standalone"    # 独立模式
    EMBEDDED = "embedded"       # 嵌入模式
    REPLACEMENT = "replacement" # 替换模式


class ConversionStrategy(Enum):
    """转换策略枚举"""
    PRESERVE_STRUCTURE = "preserve_structure"   # 保留结构
    FLATTEN = "flatten"      # 扁平化
    NESTED = "nested"        # 嵌套结构


@dataclass
class ConversionSettings:
    """转换设置"""
    mode: ConversionStrategy = ConversionStrategy.PRESERVE_STRUCTURE
    create_backup: bool = True
    preserve_metadata: bool = True
    convert_effects: bool = True
    convert_audio: bool = True
    auto_sync: bool = True


class MultiCamIntegrationManager:
    """多摄像机集成管理器"""

    def __init__(self, timeline_engine: Optional[TimelineEngine] = None,
                 project_manager: Optional[ProjectManager] = None,
                 export_system: Optional[ExportSystem] = None):
        """初始化集成管理器"""
        self.logger = get_logger("MultiCamIntegrationManager")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()

        # 核心组件
        self.multicam_engine = get_multicam_engine(timeline_engine)
        self.timeline_engine = timeline_engine or self.multicam_engine.timeline_engine
        self.project_manager = project_manager
        self.export_system = export_system
        self.ffmpeg_utils = get_ffmpeg_utils()

        # 集成设置
        self.integration_mode = IntegrationMode.EMBEDDED
        self.conversion_settings = ConversionSettings()

        # 性能管理
        self.performance_monitor = MultiCamPerformanceManager(self)
        self.cache_manager = MultiCamCacheManager(self)
        self.resource_manager = MultiCamResourceManager(self)

        # 状态管理
        self.is_converting = False
        self.conversion_progress = 0.0
        self.conversion_status = ""

        # 工作线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # 初始化
        self._initialize()

    def _initialize(self) -> None:
        """初始化集成管理器"""
        try:
            # 设置事件处理器
            self._setup_event_handlers()

            # 启动性能监控
            self.performance_monitor.start()

            # 初始化缓存
            self.cache_manager.initialize()

            self.logger.info("多摄像机集成管理器初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"集成管理器初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamIntegrationManager",
                    operation="initialize"
                ),
                user_message="集成管理器初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _setup_event_handlers(self) -> None:
        """设置事件处理器"""
        try:
            # 多摄像机引擎事件
            self.multicam_engine.event_bus.subscribe("project_created", self._on_multicam_project_created)
            self.multicam_engine.event_bus.subscribe("clip_created", self._on_multicam_clip_created)
            self.multicam_engine.event_bus.subscribe("sync_completed", self._on_multicam_sync_completed)
            self.multicam_engine.event_bus.subscribe("switch_performed", self._on_multicam_switch_performed)

            # 时间线引擎事件
            if self.timeline_engine:
                self.timeline_engine.event_bus.subscribe("track_created", self._on_track_created)
                self.timeline_engine.event_bus.subscribe("clip_added", self._on_clip_added)

            # 项目管理器事件
            if self.project_manager:
                self.project_manager.project_created.connect(self._on_project_created)
                self.project_manager.project_opened.connect(self._on_project_opened)

        except Exception as e:
            self.logger.error(f"事件处理器设置失败: {str(e)}")

    def create_multicam_project(self, name: str, description: str = "",
                              convert_existing: bool = False) -> str:
        """创建多摄像机项目"""
        try:
            if convert_existing and self.project_manager:
                # 从现有项目转换
                project_id = self._convert_existing_project(name, description)
            else:
                # 创建新的多摄像机项目
                project_id = self.multicam_engine.create_project(name, description)

            return project_id

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"创建多摄像机项目失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamIntegrationManager",
                    operation="create_multicam_project"
                ),
                user_message="无法创建多摄像机项目"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _convert_existing_project(self, name: str, description: str) -> str:
        """转换现有项目为多摄像机项目"""
        try:
            if not self.project_manager or not self.project_manager.current_project:
                raise ValueError("没有当前项目可以转换")

            existing_project = self.project_manager.current_project

            # 创建备份
            if self.conversion_settings.create_backup:
                backup_path = existing_project.create_backup()
                self.logger.info(f"创建项目备份: {backup_path}")

            # 创建多摄像机项目
            multicam_project_id = self.multicam_engine.create_project(name, description)
            multicam_project = self.multicam_engine.current_project

            # 转换媒体文件
            self._convert_media_files(existing_project, multicam_project)

            # 转换时间线
            self._convert_timeline(existing_project, multicam_project)

            # 转换设置
            self._convert_settings(existing_project, multicam_project)

            return multicam_project_id

        except Exception as e:
            self.logger.error(f"转换现有项目失败: {str(e)}")
            raise

    def _convert_media_files(self, existing_project: Project,
                            multicam_project: MultiCamProject) -> None:
        """转换媒体文件"""
        try:
            # 分析现有媒体文件，识别多摄像机素材
            media_analysis = self._analyze_media_for_multicam(existing_project)

            # 按摄像机角度分组
            camera_groups = self._group_media_by_camera(media_analysis)

            # 创建摄像机源
            for camera_angle, media_files in camera_groups.items():
                for media_file in media_files:
                    camera_id = self.multicam_engine.add_camera_source(
                        media_file.file_path,
                        f"{camera_angle.value}_{len(multicam_project.camera_sources) + 1}",
                        camera_angle
                    )

                    if camera_id:
                        multicam_project.camera_sources[camera_id] = self.multicam_engine.camera_sources[camera_id]
                        multicam_project.camera_order.append(camera_id)

            self.logger.info(f"转换了 {len(multicam_project.camera_sources)} 个摄像机源")

        except Exception as e:
            self.logger.error(f"媒体文件转换失败: {str(e)}")

    def _convert_timeline(self, existing_project: Project,
                        multicam_project: MultiCamProject) -> None:
        """转换时间线"""
        try:
            if not existing_project.timeline:
                return

            # 分析剪辑模式
            clip_patterns = self._analyze_clip_patterns(existing_project.timeline)

            # 创建多摄像机剪辑
            for pattern in clip_patterns:
                if pattern['type'] == 'multicam_pattern':
                    multicam_clip_id = self.multicam_engine.create_multicam_clip(
                        pattern['start_time'],
                        pattern['end_time'],
                        pattern['primary_camera']
                    )

                    if multicam_clip_id and self.multicam_engine.current_project:
                        multicam_clip = next(
                            (clip for clip in self.multicam_engine.current_project.clips
                             if clip.id == multicam_clip_id),
                            None
                        )

                        if multicam_clip:
                            # 添加切换点
                            for switch_point in pattern['switch_points']:
                                multicam_clip.camera_switches.append({
                                    'time': switch_point['time'],
                                    'from_camera': switch_point['from_camera'],
                                    'to_camera': switch_point['to_camera'],
                                    'transition_duration': switch_point.get('duration', 0.0),
                                    'transition_type': switch_point.get('type', 'cut')
                                })

            self.logger.info(f"转换了 {len(clip_patterns)} 个剪辑模式")

        except Exception as e:
            self.logger.error(f"时间线转换失败: {str(e)}")

    def _convert_settings(self, existing_project: Project,
                        multicam_project: MultiCamProject) -> None:
        """转换项目设置"""
        try:
            # 复制基本设置
            multicam_project.frame_rate = existing_project.settings.video_fps

            # 设置导出设置
            multicam_project.export_settings = {
                'video_codec': existing_project.settings.video_bitrate,
                'audio_codec': existing_project.settings.audio_bitrate,
                'resolution': existing_project.settings.video_resolution,
                'frame_rate': existing_project.settings.video_fps
            }

            # 设置同步方法
            if self.conversion_settings.auto_sync:
                multicam_project.sync_method = SyncMethod.AUDIO_WAVE

        except Exception as e:
            self.logger.error(f"设置转换失败: {str(e)}")

    def _analyze_media_for_multicam(self, project: Project) -> List[Dict[str, Any]]:
        """分析媒体文件以识别多摄像机素材"""
        media_analysis = []

        for media_file in project.get_all_media_files():
            analysis = {
                'id': media_file.id,
                'file_path': media_file.file_path,
                'file_name': media_file.file_name,
                'duration': media_file.duration,
                'camera_angle': self._detect_camera_angle(media_file),
                'timecode_offset': 0.0,
                'sync_confidence': 0.0
            }

            # 获取视频信息
            try:
                video_info = self.ffmpeg_utils.get_video_info(media_file.file_path)
                analysis['video_info'] = video_info
                analysis['width'] = video_info.width
                analysis['height'] = video_info.height
                analysis['fps'] = video_info.fps

                # 分析时间码
                timecode_offset = self._extract_timecode_offset(video_info)
                if timecode_offset is not None:
                    analysis['timecode_offset'] = timecode_offset

            except Exception as e:
                self.logger.warning(f"无法分析视频文件 {media_file.file_path}: {str(e)}")

            media_analysis.append(analysis)

        return media_analysis

    def _detect_camera_angle(self, media_file) -> CameraAngle:
        """检测摄像机角度"""
        # 基于文件名和元数据检测摄像机角度
        file_name_lower = media_file.file_name.lower()

        if any(keyword in file_name_lower for keyword in ['wide', '全景', '总']):
            return CameraAngle.WIDE
        elif any(keyword in file_name_lower for keyword in ['medium', '中景', '中']):
            return CameraAngle.MEDIUM
        elif any(keyword in file_name_lower for keyword in ['close', '特写', '近']):
            return CameraAngle.CLOSE_UP
        elif any(keyword in file_name_lower for keyword in ['over', '过肩', 'shoulder']):
            return CameraAngle.OVER_SHOULDER
        elif any(keyword in file_name_lower for keyword in ['low', '仰角', '低']):
            return CameraAngle.LOW_ANGLE
        elif any(keyword in file_name_lower for keyword in ['high', '俯角', '高']):
            return CameraAngle.HIGH_ANGLE
        elif any(keyword in file_name_lower for keyword in ['dolly', '移动', '轨道']):
            return CameraAngle.DOLLY
        elif any(keyword in file_name_lower for keyword in ['hand', '手持', '手']):
            return CameraAngle.HANDHELD
        elif any(keyword in file_name_lower for keyword in ['aerial', '航拍', '空']):
            return CameraAngle.AERIAL
        else:
            return CameraAngle.CUSTOM

    def _extract_timecode_offset(self, video_info) -> Optional[float]:
        """提取时间码偏移"""
        # 这里简化处理，实际需要解析视频文件中的时间码
        # 可以使用FFmpeg或其他工具提取时间码信息
        return None

    def _group_media_by_camera(self, media_analysis: List[Dict[str, Any]]) -> Dict[CameraAngle, List[Dict[str, Any]]]:
        """按摄像机角度分组媒体文件"""
        camera_groups = {}

        for media in media_analysis:
            camera_angle = media['camera_angle']
            if camera_angle not in camera_groups:
                camera_groups[camera_angle] = []
            camera_groups[camera_angle].append(media)

        return camera_groups

    def _analyze_clip_patterns(self, timeline) -> List[Dict[str, Any]]:
        """分析剪辑模式"""
        patterns = []

        # 这里简化处理，实际需要分析剪辑的排列模式
        # 识别可能的摄像机切换点和剪辑规则
        if hasattr(timeline, 'tracks'):
            for track in timeline.tracks:
                if track.get('type') == 'video':
                    for clip in track.get('clips', []):
                        pattern = {
                            'type': 'single_clip',
                            'start_time': clip.get('start_time', 0),
                            'end_time': clip.get('end_time', 0),
                            'primary_camera': clip.get('name', 'unknown'),
                            'switch_points': []
                        }
                        patterns.append(pattern)

        return patterns

    def export_to_timeline(self, multicam_project_id: str,
                         target_timeline_id: Optional[str] = None) -> str:
        """导出多摄像机项目到时间线"""
        try:
            multicam_project = self.multicam_engine.projects.get(multicam_project_id)
            if not multicam_project:
                raise ValueError(f"多摄像机项目不存在: {multicam_project_id}")

            # 创建或获取目标时间线
            if target_timeline_id and self.timeline_engine:
                timeline_id = target_timeline_id
            else:
                timeline_id = self._create_timeline_from_multicam(multicam_project)

            # 转换多摄像机剪辑到时间线剪辑
            self._convert_multicam_to_timeline(multicam_project, timeline_id)

            return timeline_id

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.EXPORT,
                severity=ErrorSeverity.HIGH,
                message=f"导出到时间线失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamIntegrationManager",
                    operation="export_to_timeline"
                ),
                user_message="无法导出到时间线"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _create_timeline_from_multicam(self, multicam_project: MultiCamProject) -> str:
        """从多摄像机项目创建时间线"""
        try:
            if not self.timeline_engine:
                raise RuntimeError("时间线引擎不可用")

            # 创建视频轨道
            video_track_id = self.timeline_engine.create_track(
                "主视频", TrackType.VIDEO, 0
            )

            # 为每个摄像机创建音频轨道
            audio_tracks = {}
            for camera_id, camera in multicam_project.camera_sources.items():
                audio_track_id = self.timeline_engine.create_track(
                    f"{camera.name} 音频", TrackType.AUDIO, 1
                )
                audio_tracks[camera_id] = audio_track_id

            return f"timeline_{multicam_project_id}"

        except Exception as e:
            self.logger.error(f"创建时间线失败: {str(e)}")
            raise

    def _convert_multicam_to_timeline(self, multicam_project: MultiCamProject,
                                    timeline_id: str) -> None:
        """转换多摄像机剪辑到时间线剪辑"""
        try:
            if not self.timeline_engine:
                return

            for multicam_clip in multicam_project.clips:
                # 创建主视频剪辑
                primary_camera = multicam_project.camera_sources.get(multicam_clip.primary_camera_id)
                if not primary_camera:
                    continue

                # 应用切换逻辑，生成视频剪辑序列
                video_clips = self._generate_video_clips_from_switches(multicam_clip, primary_camera)

                # 添加到时间线
                for clip_data in video_clips:
                    timeline_clip = Clip(
                        id=str(uuid.uuid4()),
                        name=clip_data['name'],
                        file_path=clip_data['file_path'],
                        start_time=clip_data['source_start'],
                        end_time=clip_data['source_end'],
                        timeline_start=clip_data['timeline_start'],
                        timeline_end=clip_data['timeline_end'],
                        track_type=TrackType.VIDEO
                    )

                    self.timeline_engine.add_clip(timeline_clip, 0)  # 视频轨道

                # 添加音频剪辑
                for camera_id, audio_track_id in audio_tracks.items():
                    camera = multicam_project.camera_sources.get(camera_id)
                    if camera:
                        audio_clip = Clip(
                            id=str(uuid.uuid4()),
                            name=f"{camera.name} 音频",
                            file_path=camera.file_path,
                            start_time=multicam_clip.start_time,
                            end_time=multicam_clip.end_time,
                            timeline_start=multicam_clip.start_time,
                            timeline_end=multicam_clip.end_time,
                            track_type=TrackType.AUDIO
                        )

                        self.timeline_engine.add_clip(audio_clip, audio_track_id)

        except Exception as e:
            self.logger.error(f"转换多摄像机剪辑失败: {str(e)}")

    def _generate_video_clips_from_switches(self, multicam_clip: MultiCamClip,
                                          primary_camera: CameraSource) -> List[Dict[str, Any]]:
        """从切换点生成视频剪辑"""
        video_clips = []

        if not multicam_clip.camera_switches:
            # 没有切换点，使用整个主摄像机
            video_clips.append({
                'name': primary_camera.name,
                'file_path': primary_camera.file_path,
                'source_start': multicam_clip.start_time,
                'source_end': multicam_clip.end_time,
                'timeline_start': multicam_clip.start_time,
                'timeline_end': multicam_clip.end_time
            })
        else:
            # 根据切换点分割视频
            sorted_switches = sorted(multicam_clip.camera_switches, key=lambda x: x['time'])

            current_time = multicam_clip.start_time
            current_camera = primary_camera

            for switch in sorted_switches:
                if switch['time'] > current_time:
                    # 添加当前摄像机剪辑
                    video_clips.append({
                        'name': current_camera.name,
                        'file_path': current_camera.file_path,
                        'source_start': current_time,
                        'source_end': switch['time'],
                        'timeline_start': current_time,
                        'timeline_end': switch['time']
                    })

                # 切换到新摄像机
                new_camera = self.multicam_engine.camera_sources.get(switch['to_camera'])
                if new_camera:
                    current_camera = new_camera
                current_time = switch['time']

            # 添加最后一个剪辑
            if current_time < multicam_clip.end_time:
                video_clips.append({
                    'name': current_camera.name,
                    'file_path': current_camera.file_path,
                    'source_start': current_time,
                    'source_end': multicam_clip.end_time,
                    'timeline_start': current_time,
                    'timeline_end': multicam_clip.end_time
                })

        return video_clips

    def synchronize_with_project(self, project_id: str) -> bool:
        """与项目同步"""
        try:
            if not self.project_manager:
                return False

            project = self.project_manager.get_project(project_id)
            if not project:
                return False

            # 同步媒体文件
            self._sync_media_files(project)

            # 同步设置
            self._sync_project_settings(project)

            return True

        except Exception as e:
            self.logger.error(f"项目同步失败: {str(e)}")
            return False

    def _sync_media_files(self, project: Project) -> None:
        """同步媒体文件"""
        try:
            # 比较项目媒体文件与多摄像机源
            project_media = {media.id: media for media in project.get_all_media_files()}
            multicam_cameras = self.multicam_engine.camera_sources

            # 添加缺失的摄像机源
            for media_id, media_file in project_media.items():
                if media_id not in [cam.id for cam in multicam_cameras.values()]:
                    camera_angle = self._detect_camera_angle(media_file)
                    camera_id = self.multicam_engine.add_camera_source(
                        media_file.file_path,
                        media_file.file_name,
                        camera_angle
                    )

                    if camera_id and self.multicam_engine.current_project:
                        self.multicam_engine.current_project.camera_sources[camera_id] = self.multicam_engine.camera_sources[camera_id]

            # 移除多余的摄像机源
            cameras_to_remove = []
            for camera in multicam_cameras.values():
                if camera.id not in project_media:
                    cameras_to_remove.append(camera.id)

            for camera_id in cameras_to_remove:
                self.multicam_engine.remove_camera_source(camera_id)

        except Exception as e:
            self.logger.error(f"媒体文件同步失败: {str(e)}")

    def _sync_project_settings(self, project: Project) -> None:
        """同步项目设置"""
        try:
            if not self.multicam_engine.current_project:
                return

            # 同步基本设置
            self.multicam_engine.current_project.frame_rate = project.settings.video_fps

            # 同步导出设置
            self.multicam_engine.current_project.export_settings = {
                'video_codec': project.settings.video_bitrate,
                'audio_codec': project.settings.audio_bitrate,
                'resolution': project.settings.video_resolution,
                'frame_rate': project.settings.video_fps
            }

        except Exception as e:
            self.logger.error(f"项目设置同步失败: {str(e)}")

    def export_multicam_project(self, multicam_project_id: str,
                              output_path: str,
                              export_settings: Optional[Dict[str, Any]] = None) -> bool:
        """导出多摄像机项目"""
        try:
            multicam_project = self.multicam_engine.projects.get(multicam_project_id)
            if not multicam_project:
                raise ValueError(f"多摄像机项目不存在: {multicam_project_id}")

            # 合并导出设置
            final_settings = multicam_project.export_settings.copy()
            if export_settings:
                final_settings.update(export_settings)

            # 使用导出系统或直接导出
            if self.export_system:
                success = self._export_via_system(multicam_project, output_path, final_settings)
            else:
                success = self.multicam_engine.export_multicam_edit(
                    output_path, final_settings
                )

            if success:
                self.logger.info(f"多摄像机项目导出成功: {output_path}")

            return success

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.EXPORT,
                severity=ErrorSeverity.HIGH,
                message=f"导出多摄像机项目失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="MultiCamIntegrationManager",
                    operation="export_multicam_project"
                ),
                user_message="无法导出多摄像机项目"
            )
            self.error_handler.handle_error(error_info)
            return False

    def _export_via_system(self, multicam_project: MultiCamProject,
                          output_path: str, settings: Dict[str, Any]) -> bool:
        """通过导出系统导出"""
        try:
            if not self.export_system:
                return False

            # 准备导出设置
            export_settings = ExportSettings(
                output_path=output_path,
                video_codec=settings.get('video_codec', 'h264'),
                video_bitrate=int(settings.get('video_bitrate', '8000k').replace('k', '')) * 1000,
                audio_codec=settings.get('audio_codec', 'aac'),
                audio_bitrate=int(settings.get('audio_bitrate', '192k').replace('k', '')) * 1000,
                resolution=settings.get('resolution', '1920x1080'),
                frame_rate=settings.get('frame_rate', 30),
                quality='medium'
            )

            # 生成临时视频文件
            temp_video_path = self._generate_temp_video(multicam_project)

            if temp_video_path:
                # 使用导出系统导出
                success = self.export_system.export_video(
                    temp_video_path, export_settings
                )

                # 清理临时文件
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)

                return success

            return False

        except Exception as e:
            self.logger.error(f"通过导出系统导出失败: {str(e)}")
            return False

    def _generate_temp_video(self, multicam_project: MultiCamProject) -> Optional[str]:
        """生成临时视频文件"""
        try:
            import tempfile

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_path = temp_file.name
            temp_file.close()

            # 生成多摄像机编辑视频
            success = self.multicam_engine.export_multicam_edit(
                temp_path, multicam_project.export_settings
            )

            if success:
                return temp_path
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None

        except Exception as e:
            self.logger.error(f"生成临时视频失败: {str(e)}")
            return None

    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        return {
            'integration_mode': self.integration_mode.value,
            'conversion_settings': self.conversion_settings.__dict__,
            'performance_status': self.performance_monitor.get_status(),
            'cache_status': self.cache_manager.get_status(),
            'resource_status': self.resource_manager.get_status()
        }

    def set_integration_mode(self, mode: IntegrationMode) -> None:
        """设置集成模式"""
        self.integration_mode = mode
        self.logger.info(f"集成模式设置为: {mode.value}")

    def set_conversion_settings(self, settings: ConversionSettings) -> None:
        """设置转换设置"""
        self.conversion_settings = settings
        self.logger.info(f"转换设置已更新")

    # 事件处理器
    def _on_multicam_project_created(self, data: Any) -> None:
        """多摄像机项目创建事件"""
        project_id = data.get('project_id')
        self.logger.info(f"多摄像机项目创建: {project_id}")

    def _on_multicam_clip_created(self, data: Any) -> None:
        """多摄像机剪辑创建事件"""
        clip_id = data.get('clip_id')
        self.logger.debug(f"多摄像机剪辑创建: {clip_id}")

    def _on_multicam_sync_completed(self, data: Any) -> None:
        """多摄像机同步完成事件"""
        method = data.get('method')
        self.logger.info(f"多摄像机同步完成: {method}")

    def _on_multicam_switch_performed(self, data: Any) -> None:
        """多摄像机切换执行事件"""
        target_camera = data.get('target_camera')
        timeline_time = data.get('timeline_time')
        self.logger.debug(f"多摄像机切换: {target_camera} @ {timeline_time}")

    def _on_project_created(self, project_id: str) -> None:
        """项目创建事件"""
        self.logger.info(f"项目创建: {project_id}")

    def _on_project_opened(self, project_id: str) -> None:
        """项目打开事件"""
        self.logger.info(f"项目打开: {project_id}")

    def _on_track_created(self, data: Any) -> None:
        """轨道创建事件"""
        track_id = data.get('track_id')
        self.logger.debug(f"轨道创建: {track_id}")

    def _on_clip_added(self, data: Any) -> None:
        """剪辑添加事件"""
        clip_id = data.get('clip_id')
        self.logger.debug(f"剪辑添加: {clip_id}")

    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 停止性能监控
            self.performance_monitor.stop()

            # 清理缓存
            self.cache_manager.cleanup()

            # 关闭线程池
            self.thread_pool.shutdown(wait=True)

            self.logger.info("多摄像机集成管理器资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理失败: {str(e)}")


class MultiCamPerformanceManager:
    """多摄像机性能管理器"""

    def __init__(self, integration_manager: MultiCamIntegrationManager):
        self.integration_manager = integration_manager
        self.logger = integration_manager.logger
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.performance_data = {
            'cpu_usage': [],
            'memory_usage': [],
            'preview_fps': [],
            'sync_operations': [],
            'switch_operations': [],
            'cache_hit_rate': [],
            'render_times': []
        }

    def start(self) -> None:
        """启动性能监控"""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.monitor_thread.start()
        self.logger.info("性能监控已启动")

    def stop(self) -> None:
        """停止性能监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("性能监控已停止")

    def _monitor_performance(self) -> None:
        """监控性能"""
        import psutil
        import time

        while self.is_monitoring:
            try:
                # CPU使用率
                cpu_usage = psutil.cpu_percent(interval=1)
                self.performance_data['cpu_usage'].append(cpu_usage)

                # 内存使用率
                memory_info = psutil.virtual_memory()
                memory_usage = memory_info.percent
                self.performance_data['memory_usage'].append(memory_usage)

                # 限制数据长度
                max_data_points = 100
                for key in self.performance_data:
                    if len(self.performance_data[key]) > max_data_points:
                        self.performance_data[key] = self.performance_data[key][-max_data_points:]

                time.sleep(1)

            except Exception as e:
                self.logger.error(f"性能监控错误: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """获取性能状态"""
        return {
            'is_monitoring': self.is_monitoring,
            'performance_data': self.performance_data.copy()
        }


class MultiCamCacheManager:
    """多摄像机缓存管理器"""

    def __init__(self, integration_manager: MultiCamIntegrationManager):
        self.integration_manager = integration_manager
        self.logger = integration_manager.logger
        self.cache_dir = "/tmp/cineaistudio/multicam_cache"
        self.preview_cache = {}
        self.analysis_cache = {}
        self.metadata_cache = {}
        self.cache_stats = {
            'preview_hits': 0,
            'preview_misses': 0,
            'analysis_hits': 0,
            'analysis_misses': 0,
            'metadata_hits': 0,
            'metadata_misses': 0
        }

    def initialize(self) -> None:
        """初始化缓存"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            self.logger.info(f"缓存目录初始化: {self.cache_dir}")

            # 加载现有缓存
            self._load_cache_metadata()

        except Exception as e:
            self.logger.error(f"缓存初始化失败: {str(e)}")

    def _load_cache_metadata(self) -> None:
        """加载缓存元数据"""
        try:
            metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    cache_metadata = json.load(f)

                self.cache_stats = cache_metadata.get('stats', self.cache_stats)

        except Exception as e:
            self.logger.warning(f"加载缓存元数据失败: {str(e)}")

    def _save_cache_metadata(self) -> None:
        """保存缓存元数据"""
        try:
            metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
            metadata = {
                'stats': self.cache_stats,
                'timestamp': datetime.now().isoformat()
            }

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            self.logger.warning(f"保存缓存元数据失败: {str(e)}")

    def get_preview_frame(self, camera_id: str, time: float) -> Optional[str]:
        """获取预览帧"""
        cache_key = f"{camera_id}_{time:.2f}"

        if cache_key in self.preview_cache:
            self.cache_stats['preview_hits'] += 1
            return self.preview_cache[cache_key]
        else:
            self.cache_stats['preview_misses'] += 1
            return None

    def cache_preview_frame(self, camera_id: str, time: float, frame_path: str) -> None:
        """缓存预览帧"""
        cache_key = f"{camera_id}_{time:.2f}"
        self.preview_cache[cache_key] = frame_path

    def get_analysis_result(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """获取分析结果"""
        if camera_id in self.analysis_cache:
            self.cache_stats['analysis_hits'] += 1
            return self.analysis_cache[camera_id]
        else:
            self.cache_stats['analysis_misses'] += 1
            return None

    def cache_analysis_result(self, camera_id: str, result: Dict[str, Any]) -> None:
        """缓存分析结果"""
        self.analysis_cache[camera_id] = result

    def get_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        total_requests = sum(self.cache_stats.values())
        hit_rate = 0.0
        if total_requests > 0:
            total_hits = (self.cache_stats['preview_hits'] +
                         self.cache_stats['analysis_hits'] +
                         self.cache_stats['metadata_hits'])
            hit_rate = total_hits / total_requests

        return {
            'cache_dir': self.cache_dir,
            'cache_size': len(self.preview_cache) + len(self.analysis_cache) + len(self.metadata_cache),
            'stats': self.cache_stats.copy(),
            'hit_rate': hit_rate
        }

    def cleanup(self) -> None:
        """清理缓存"""
        try:
            # 清理缓存目录
            if os.path.exists(self.cache_dir):
                import shutil
                shutil.rmtree(self.cache_dir)

            # 清理内存缓存
            self.preview_cache.clear()
            self.analysis_cache.clear()
            self.metadata_cache.clear()

            self.logger.info("缓存清理完成")

        except Exception as e:
            self.logger.error(f"缓存清理失败: {str(e)}")


class MultiCamResourceManager:
    """多摄像机资源管理器"""

    def __init__(self, integration_manager: MultiCamIntegrationManager):
        self.integration_manager = integration_manager
        self.logger = integration_manager.logger
        self.hardware_acceleration = HardwareAcceleration()
        self.resource_usage = {
            'gpu_memory': 0,
            'cpu_threads': 0,
            'disk_io': 0,
            'network_bandwidth': 0
        }

    def allocate_resources(self, camera_count: int) -> Dict[str, Any]:
        """分配资源"""
        try:
            # 检查GPU内存
            gpu_memory_required = camera_count * 512  # MB per camera
            available_gpu_memory = self.hardware_acceleration.get_available_gpu_memory()

            # 检查CPU线程
            cpu_threads_required = min(camera_count * 2, os.cpu_count())
            available_cpu_threads = os.cpu_count()

            # 检查磁盘空间
            disk_space_required = camera_count * 1024  # MB per camera
            available_disk_space = self._get_available_disk_space()

            allocation = {
                'gpu_memory': min(gpu_memory_required, available_gpu_memory),
                'cpu_threads': min(cpu_threads_required, available_cpu_threads),
                'disk_space': min(disk_space_required, available_disk_space),
                'success': True
            }

            if (gpu_memory_required > available_gpu_memory or
                cpu_threads_required > available_cpu_threads or
                disk_space_required > available_disk_space):
                allocation['success'] = False
                allocation['error'] = "Insufficient resources"

            return allocation

        except Exception as e:
            self.logger.error(f"资源分配失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _get_available_disk_space(self) -> int:
        """获取可用磁盘空间"""
        try:
            import shutil
            disk_usage = shutil.disk_usage("/")
            return disk_usage.free // (1024 * 1024)  # MB
        except Exception as e:
            self.logger.error(f"获取磁盘空间失败: {str(e)}")
            return 0

    def get_status(self) -> Dict[str, Any]:
        """获取资源状态"""
        return {
            'resource_usage': self.resource_usage.copy(),
            'hardware_acceleration': self.hardware_acceleration.get_status(),
            'system_resources': {
                'cpu_count': os.cpu_count(),
                'total_memory': psutil.virtual_memory().total // (1024 * 1024),  # MB
                'available_memory': psutil.virtual_memory().available // (1024 * 1024),  # MB
                'available_disk_space': self._get_available_disk_space()
            }
        }