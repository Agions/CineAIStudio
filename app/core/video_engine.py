#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 视频引擎模块
核心视频处理引擎，提供完整的视频I/O、处理、优化和集成功能
"""

import os
import time
import asyncio
import threading
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, AsyncGenerator
from PyQt6.QtCore import QThreadPool, QRunnable, pyqtSignal, QObject
from functools import lru_cache
import gc
import weakref
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from contextlib import asynccontextmanager

from .logger import get_logger
from .event_system import EventBus
from .service_container import ServiceContainer
from .config_manager import get_config_manager
from .hardware_acceleration import get_hardware_acceleration, PerformanceMetrics
from .video_processor import VideoProcessor, ProcessingTask, ProcessingConfig, ProcessingPriority, ProcessingStatus
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import get_ffmpeg_utils, VideoInfo, VideoCodec, AudioCodec, ContainerFormat


class EngineState(Enum):
    """引擎状态枚举"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


class EngineCapability(Enum):
    """引擎能力枚举"""
    VIDEO_DECODING = "video_decoding"
    VIDEO_ENCODING = "video_encoding"
    AUDIO_DECODING = "audio_decoding"
    AUDIO_ENCODING = "audio_encoding"
    HARDWARE_ACCELERATION = "hardware_acceleration"
    REAL_TIME_PROCESSING = "real_time_processing"
    BATCH_PROCESSING = "batch_processing"
    FORMAT_CONVERSION = "format_conversion"
    FILTER_APPLICATION = "filter_application"
    METADATA_EXTRACTION = "metadata_extraction"
    THUMBNAIL_GENERATION = "thumbnail_generation"
    FRAME_EXTRACTION = "frame_extraction"
    VIDEO_CONCATENATION = "video_concatenation"
    VIDEO_SPLITTING = "video_splitting"
    SUBTITLE_SUPPORT = "subtitle_support"
    HDR_SUPPORT = "hdr_support"
    VR_SUPPORT = "vr_support"


@dataclass
class EngineSettings:
    """引擎设置数据类"""
    max_concurrent_operations: int = 8
    memory_limit: int = 2048 * 1024 * 1024  # 2GB
    temp_directory: str = "/tmp/cineaistudio"
    cache_directory: str = "/tmp/cineaistudio/cache"
    log_level: str = "INFO"
    enable_hardware_acceleration: bool = True
    enable_real_time_processing: bool = True
    enable_caching: bool = True
    enable_auto_optimization: bool = True
    default_output_format: ContainerFormat = ContainerFormat.MP4
    default_video_codec: VideoCodec = VideoCodec.H264
    default_audio_codec: AudioCodec = AudioCodec.AAC
    default_quality_preset: str = "medium"
    enable_metadata_preservation: bool = True
    enable_error_recovery: bool = True
    max_retry_attempts: int = 3
    timeout_seconds: int = 3600


@dataclass
class OperationResult:
    """操作结果数据类"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[Exception] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoStream:
    """视频流数据类"""
    id: str
    path: str
    video_info: VideoInfo
    is_open: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    callbacks: Dict[str, List[Callable]] = field(default_factory=dict)


class VideoEngine:
    """视频引擎核心类"""

    def __init__(self, settings: Optional[EngineSettings] = None, logger=None):
        """初始化视频引擎"""
        self.logger = logger or get_logger("VideoEngine")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.service_container = ServiceContainer()
        self.config_manager = get_config_manager()

        # 设置
        self.settings = settings or EngineSettings()
        self.state = EngineState.UNINITIALIZED

        # 核心组件
        self.video_processor: Optional[VideoProcessor] = None
        self.hardware_acceleration = get_hardware_acceleration()
        self.ffmpeg_utils = get_ffmpeg_utils()

        # 流管理
        self.streams = weakref.WeakValueDictionary()  # 弱引用字典，避免内存泄漏
        self.stream_lock = threading.Lock()

        # 操作历史
        self.operation_history: List[OperationResult] = []
        self.max_history_size = 1000

        # 性能监控
        self.performance_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'average_operation_time': 0.0,
            'throughput': 0.0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'gpu_usage': 0
        }

        # 线程池 for 异步操作
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(4)

        # video_info 缓存
        self.video_info_cache = {}
        self.cache_ttl = 3600  # 1小时

        # 初始化锁
        self.init_lock = threading.Lock()

        # 注册服务
        self._register_services()

        # 连接事件
        self._setup_event_handlers()

    def _register_services(self) -> None:
        """注册服务"""
        try:
            self.service_container.register(VideoEngine, self)
            self.service_container.register(EventBus, self.event_bus)
            self.service_container.register(ServiceContainer, self.service_container)
            self.logger.info("服务注册完成")
        except Exception as e:
            self.logger.error(f"服务注册失败: {str(e)}")

    def _setup_event_handlers(self) -> None:
        """设置事件处理器"""
        try:
            self.event_bus.subscribe("engine_error", self._handle_engine_error)
            self.event_bus.subscribe("performance_warning", self._handle_performance_warning)
            self.event_bus.subscribe("memory_warning", self._handle_memory_warning)
            self.logger.info("事件处理器设置完成")
        except Exception as e:
            self.logger.error(f"事件处理器设置失败: {str(e)}")

    def initialize(self) -> OperationResult:
        """初始化引擎"""
        with self.init_lock:
            if self.state != EngineState.UNINITIALIZED:
                return OperationResult(
                    success=False,
                    message=f"引擎已初始化，当前状态: {self.state.value}"
                )

            self.state = EngineState.INITIALIZING
            start_time = time.time()

            try:
                # 创建目录
                self._create_directories()

                # 初始化硬件加速
                self._initialize_hardware_acceleration()

                # 初始化视频处理器
                self._initialize_video_processor()

                # 检测引擎能力
                capabilities = self._detect_capabilities()

                # 加载配置
                self._load_configuration()

                # 启动性能监控
                self.hardware_acceleration.start_monitoring()

                self.state = EngineState.READY
                duration = time.time() - start_time

                result = OperationResult(
                    success=True,
                    message="视频引擎初始化成功",
                    data={'capabilities': capabilities, 'state': self.state.value},
                    duration=duration,
                    metadata={'capabilities': capabilities}
                )

                self.event_bus.publish("engine_initialized", result)
                self.logger.info("视频引擎初始化成功")
                gc.collect()  # 初始化后垃圾回收
                return result

            except Exception as e:
                self.state = EngineState.ERROR
                duration = time.time() - start_time

                error_info = ErrorInfo(
                    error_type=ErrorType.SYSTEM,
                    severity=ErrorSeverity.CRITICAL,
                    message=f"视频引擎初始化失败: {str(e)}",
                    exception=e,
                    context=ErrorContext(
                        component="VideoEngine",
                        operation="initialize"
                    ),
                    user_message="视频引擎初始化失败，请检查系统配置"
                )
                self.error_handler.handle_error(error_info)

                result = OperationResult(
                    success=False,
                    message=f"初始化失败: {str(e)}",
                    error=e,
                    duration=duration
                )

                self.event_bus.publish("engine_error", result)
                return result

    def _create_directories(self) -> None:
        """创建必要目录"""
        try:
            directories = [
                self.settings.temp_directory,
                self.settings.cache_directory,
                os.path.join(self.settings.temp_directory, "streams"),
                os.path.join(self.settings.temp_directory, "processing"),
                os.path.join(self.settings.temp_directory, "output")
            ]

            for directory in directories:
                os.makedirs(directory, exist_ok=True)

            self.logger.info("目录创建完成")
        except Exception as e:
            self.logger.error(f"目录创建失败: {str(e)}")
            raise

    def _initialize_hardware_acceleration(self) -> None:
        """初始化硬件加速，包括NVENC支持"""
        try:
            # 检查硬件加速是否可用
            if self.settings.enable_hardware_acceleration:
                # 检测NVIDIA GPU for NVENC
                nvidia_info = self.hardware_acceleration.get_gpu_info('nvidia')
                if nvidia_info and nvidia_info.get('nvenc_supported', False):
                    self.settings.default_video_codec = VideoCodec.H264_NVENC
                    self.logger.info("NVENC硬件加速已启用 (NVIDIA GPU检测到)")
                else:
                    self.logger.info("硬件加速已启用 (CPU/其他GPU)")
            else:
                self.logger.info("硬件加速已禁用")

        except Exception as e:
            self.logger.error(f"硬件加速初始化失败: {str(e)}")
            raise

    def _initialize_video_processor(self) -> None:
        """初始化视频处理器"""
        try:
            processing_config = ProcessingConfig(
                max_concurrent_tasks=self.settings.max_concurrent_operations,
                use_gpu=self.settings.enable_hardware_acceleration,
                use_hardware_acceleration=self.settings.enable_hardware_acceleration,
                memory_limit=self.settings.memory_limit,
                temp_dir=self.settings.temp_directory,
                enable_real_time=self.settings.enable_real_time_processing,
                enable_caching=self.settings.enable_caching,
                quality_preset=self.settings.default_quality_preset,
                output_format=self.settings.default_output_format,
                video_codec=self.settings.default_video_codec,
                audio_codec=self.settings.default_audio_codec
            )

            self.video_processor = VideoProcessor(processing_config, self.logger)
            self.video_processor.start()

            self.logger.info("视频处理器初始化完成")
        except Exception as e:
            self.logger.error(f"视频处理器初始化失败: {str(e)}")
            raise

    def _detect_capabilities(self) -> List[EngineCapability]:
        """检测引擎能力"""
        capabilities = []

        try:
            # 基本解码编码能力
            capabilities.extend([
                EngineCapability.VIDEO_DECODING,
                EngineCapability.VIDEO_ENCODING,
                EngineCapability.AUDIO_DECODING,
                EngineCapability.AUDIO_ENCODING,
                EngineCapability.FORMAT_CONVERSION,
                EngineCapability.METADATA_EXTRACTION,
                EngineCapability.THUMBNAIL_GENERATION,
                EngineCapability.FRAME_EXTRACTION,
                EngineCapability.VIDEO_CONCATENATION,
                EngineCapability.VIDEO_SPLITTING
            ])

            # 硬件加速能力
            if self.settings.enable_hardware_acceleration:
                capabilities.append(EngineCapability.HARDWARE_ACCELERATION)

            # 实时处理能力
            if self.settings.enable_real_time_processing:
                capabilities.append(EngineCapability.REAL_TIME_PROCESSING)

            # 批处理能力
            capabilities.append(EngineCapability.BATCH_PROCESSING)

            # 滤镜应用能力
            capabilities.append(EngineCapability.FILTER_APPLICATION)

            # 字幕支持
            capabilities.append(EngineCapability.SUBTITLE_SUPPORT)

            # HDR支持
            capabilities.append(EngineCapability.HDR_SUPPORT)

            self.logger.info(f"检测到 {len(capabilities)} 种引擎能力")
            return capabilities

        except Exception as e:
            self.logger.error(f"能力检测失败: {str(e)}")
            return []

    def _load_configuration(self) -> None:
        """加载配置"""
        try:
            # 从配置管理器加载设置
            config = self.config_manager.get_config("video_engine")

            if config:
                self.settings.max_concurrent_operations = config.get("max_concurrent_operations", self.settings.max_concurrent_operations)
                self.settings.memory_limit = config.get("memory_limit", self.settings.memory_limit)
                self.settings.enable_hardware_acceleration = config.get("enable_hardware_acceleration", self.settings.enable_hardware_acceleration)
                self.settings.enable_real_time_processing = config.get("enable_real_time_processing", self.settings.enable_real_time_processing)
                self.settings.default_quality_preset = config.get("default_quality_preset", self.settings.default_quality_preset)

            self.logger.info("配置加载完成")
            gc.collect()  # 初始化后清理
        except Exception as e:
            self.logger.error(f"配置加载失败: {str(e)}")

    def open_video_stream(self, video_path: str, stream_id: Optional[str] = None) -> OperationResult:
        """打开视频流"""
        if self.state != EngineState.READY:
            return OperationResult(
                success=False,
                message=f"引擎未就绪，当前状态: {self.state.value}"
            )

        if not os.path.exists(video_path):
            return OperationResult(
                success=False,
                message=f"视频文件不存在: {video_path}"
            )

        start_time = time.time()

        try:
            # 生成流ID
            if not stream_id:
                stream_id = f"stream_{int(time.time() * 1000)}"

            # 异步获取视频信息（使用worker）
            worker = VideoInfoWorker(video_path, self)
            worker.signals.result.connect(lambda info: self._on_video_info_ready(info, stream_id, start_time, video_path))
            worker.signals.error.connect(lambda err: self._on_video_info_error(err, stream_id, start_time))
            self.thread_pool.start(worker)
            return OperationResult(success=True, message=f"视频流打开任务已提交: {stream_id}")  # 异步返回

        except Exception as e:
            duration = time.time() - start_time

            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.HIGH,
                message=f"打开视频流失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoEngine",
                    operation="open_video_stream"
                ),
                user_message="无法打开视频文件"
            )
            self.error_handler.handle_error(error_info)

            result = OperationResult(
                success=False,
                message=f"打开视频流失败: {str(e)}",
                error=e,
                duration=duration
            )

            self.event_bus.publish("stream_error", result)
            return result

    def _on_video_info_ready(self, video_info: VideoInfo, stream_id: str, start_time: float, video_path: str):
        """视频信息准备完成"""
        try:
            # 缓存video_info
            self.video_info_cache[video_path] = (video_info, time.time())

            # 创建视频流
            video_stream = VideoStream(
                id=stream_id,
                path=video_path,
                video_info=video_info,
                is_open=True
            )

            with self.stream_lock:
                self.streams[stream_id] = video_stream

            duration = time.time() - start_time

            result = OperationResult(
                success=True,
                message=f"视频流已打开: {stream_id}",
                data={'stream_id': stream_id, 'video_info': video_info},
                duration=duration,
                metadata={'stream_id': stream_id}
            )

            self.event_bus.publish("stream_opened", result)
            self.logger.info(f"视频流已打开: {stream_id}")
            gc.collect()  # 打开流后清理

        except Exception as e:
            self._on_video_info_error(str(e), stream_id, start_time)

    def _on_video_info_error(self, error_msg: str, stream_id: str, start_time: float):
        """视频信息错误"""
        duration = time.time() - start_time
        result = OperationResult(
            success=False,
            message=f"打开视频流失败: {error_msg}",
            error=Exception(error_msg),
            duration=duration
        )
        self.event_bus.publish("stream_error", result)
        self.logger.error(f"视频流打开失败: {stream_id}, {error_msg}")

    def close_video_stream(self, stream_id: str) -> OperationResult:
        """关闭视频流"""
        if self.state != EngineState.READY:
            return OperationResult(
                success=False,
                message=f"引擎未就绪，当前状态: {self.state.value}"
            )

        start_time = time.time()

        try:
            with self.stream_lock:
                if stream_id not in self.streams:
                    return OperationResult(
                        success=False,
                        message=f"视频流不存在: {stream_id}"
                    )

                video_stream = self.streams.get(stream_id)
                if video_stream:
                    video_stream.is_open = False
    
                # 弱引用自动清理，无需del

            duration = time.time() - start_time

            result = OperationResult(
                success=True,
                message=f"视频流已关闭: {stream_id}",
                duration=duration,
                metadata={'stream_id': stream_id}
            )

            self.event_bus.publish("stream_closed", result)
            self.logger.info(f"视频流已关闭: {stream_id}")
            return result

        except Exception as e:
            duration = time.time() - start_time

            result = OperationResult(
                success=False,
                message=f"关闭视频流失败: {str(e)}",
                error=e,
                duration=duration
            )

            self.event_bus.publish("stream_error", result)
            return result

    def get_video_stream(self, stream_id: str) -> Optional[VideoStream]:
        """获取视频流"""
        with self.stream_lock:
            return self.streams.get(stream_id)  # 弱引用，如果已回收返回None

    def get_all_streams(self) -> List[VideoStream]:
        """获取所有视频流"""
        with self.stream_lock:
            return list(self.streams.values())  # 自动排除已回收的

    def process_video(self, input_path: str, output_path: str, operation_type: str,
                     operation_params: Optional[Dict[str, Any]] = None,
                     priority: ProcessingPriority = ProcessingPriority.NORMAL,
                     callback: Optional[Callable[[ProcessingTask], None]] = None) -> OperationResult:
        """处理视频（异步提交，支持NVENC编码）"""
        if self.state != EngineState.READY:
            return OperationResult(
                success=False,
                message=f"引擎未就绪，当前状态: {self.state.value}"
            )

        if not self.video_processor:
            return OperationResult(
                success=False,
                message="视频处理器未初始化"
            )

        start_time = time.time()

        try:
            # 默认启用NVENC如果可用
            params = operation_params or {}
            if self.settings.enable_hardware_acceleration and 'encoder' not in params:
                nvidia_info = self.hardware_acceleration.get_gpu_info('nvidia')
                if nvidia_info and nvidia_info.get('nvenc_supported', False):
                    params['encoder'] = 'nvenc'
                    params['video_codec'] = 'h264_nvenc'
                    self.logger.info("自动启用NVENC编码")

            # 创建处理任务
            task_id = f"task_{int(time.time() * 1000)}"
            task = ProcessingTask(
                id=task_id,
                name=f"{operation_type}_{os.path.basename(input_path)}",
                input_path=input_path,
                output_path=output_path,
                priority=priority,
                callback=callback,
                metadata={'type': operation_type, **params}
            )

            # 异步添加任务，使用thread_pool
            class ProcessingWorker(QRunnable):
                def __init__(self, task, start_time, engine):
                    super().__init__()
                    self.task = task
                    self.start_time = start_time
                    self.engine = engine

                def run(self):
                    success = self.engine.video_processor.add_task(self.task)
                    duration = time.time() - self.start_time
                    if success:
                        result = OperationResult(
                            success=True,
                            message=f"视频处理任务已提交: {self.task.id}",
                            data={'task_id': self.task.id, 'task': self.task},
                            duration=duration,
                            metadata={'task_id': self.task.id, 'operation_type': self.task.metadata.get('type')}
                        )
                        self.engine.event_bus.publish("video_processing_started", result)
                        self.engine.logger.info(f"视频处理任务已提交: {self.task.id} (编码器: {self.task.metadata.get('encoder', 'software')})")
                    else:
                        result = OperationResult(
                            success=False,
                            message="无法添加处理任务",
                            duration=duration
                        )
                        self.engine.event_bus.publish("video_processing_error", result)
                        self.engine.logger.error(f"视频处理任务添加失败: {self.task.id}")

            worker = ProcessingWorker(task, start_time, self)
            self.thread_pool.start(worker)

            return OperationResult(success=True, message=f"视频处理任务提交中: {task_id}")

        except Exception as e:
            duration = time.time() - start_time
            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.HIGH,
                message=f"视频处理失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoEngine",
                    operation="process_video"
                ),
                user_message="视频处理失败，请稍后重试"
            )
            self.error_handler.handle_error(error_info)

            result = OperationResult(
                success=False,
                message=f"视频处理失败: {str(e)}",
                error=e,
                duration=duration
            )

            self.event_bus.publish("video_processing_error", result)
            return result

    @lru_cache(maxsize=50)
    def create_thumbnail(self, video_path: str, output_path: str,
                        timestamp: float = 0.0, size: Tuple[int, int] = (320, 180)) -> OperationResult:
        """创建缩略图（缓存）"""
        if self.state != EngineState.READY:
            return OperationResult(
                success=False,
                message=f"引擎未就绪，当前状态: {self.state.value}"
            )

        start_time = time.time()

        try:
            thumbnail_path = self.ffmpeg_utils.create_thumbnail(video_path, output_path, timestamp, size)

            duration = time.time() - start_time

            result = OperationResult(
                success=True,
                message="缩略图创建成功",
                data={'thumbnail_path': thumbnail_path},
                duration=duration,
                metadata={'video_path': video_path, 'thumbnail_path': thumbnail_path}
            )

            self.event_bus.publish("thumbnail_created", result)
            self.logger.info(f"缩略图创建成功: {thumbnail_path}")
            gc.collect()  # 清理临时FFmpeg资源
            return result

        except Exception as e:
            duration = time.time() - start_time

            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.MEDIUM,
                message=f"创建缩略图失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoEngine",
                    operation="create_thumbnail"
                ),
                user_message="无法创建缩略图"
            )
            self.error_handler.handle_error(error_info)

            result = OperationResult(
                success=False,
                message=f"创建缩略图失败: {str(e)}",
                error=e,
                duration=duration
            )

            self.event_bus.publish("thumbnail_error", result)
            return result

    def extract_audio(self, video_path: str, output_path: str,
                     codec: AudioCodec = AudioCodec.AAC, bitrate: int = 192000) -> OperationResult:
        """提取音频"""
        if self.state != EngineState.READY:
            return OperationResult(
                success=False,
                message=f"引擎未就绪，当前状态: {self.state.value}"
            )

        start_time = time.time()

        try:
            audio_path = self.ffmpeg_utils.extract_audio(video_path, output_path, codec, bitrate)

            duration = time.time() - start_time

            result = OperationResult(
                success=True,
                message="音频提取成功",
                data={'audio_path': audio_path},
                duration=duration,
                metadata={'video_path': video_path, 'audio_path': audio_path}
            )

            self.event_bus.publish("audio_extracted", result)
            self.logger.info(f"音频提取成功: {audio_path}")
            return result

        except Exception as e:
            duration = time.time() - start_time

            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.MEDIUM,
                message=f"音频提取失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoEngine",
                    operation="extract_audio"
                ),
                user_message="无法提取音频"
            )
            self.error_handler.handle_error(error_info)

            result = OperationResult(
                success=False,
                message=f"音频提取失败: {str(e)}",
                error=e,
                duration=duration
            )

            self.event_bus.publish("audio_extraction_error", result)
            return result

    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        status = {
            'state': self.state.value,
            'streams': len(self.streams),
            'capabilities': [cap.value for cap in self._detect_capabilities()],
            'performance': self.performance_stats.copy(),
            'settings': {
                'max_concurrent_operations': self.settings.max_concurrent_operations,
                'memory_limit': self.settings.memory_limit,
                'enable_hardware_acceleration': self.settings.enable_hardware_acceleration,
                'enable_real_time_processing': self.settings.enable_real_time_processing
            }
        }

        if self.video_processor:
            status['video_processor'] = self.video_processor.get_queue_status()

        if self.hardware_acceleration:
            status['hardware'] = {
                'gpus': [gpu.name for gpu in self.hardware_acceleration.get_all_gpu_info()],
                'hw_acceleration': self.hardware_acceleration.hw_acceleration_type.value
            }

        return status

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        metrics = {
            'engine_stats': self.performance_stats.copy(),
            'hardware_metrics': self.hardware_acceleration.get_performance_metrics().__dict__,
            'ffmpeg_metrics': {
                'is_busy': self.ffmpeg_utils.is_busy(),
                'queue_size': self.ffmpeg_utils.command_queue.qsize()
            },
            'cache_size': len(self.video_info_cache)
        }

        if self.video_processor:
            metrics['video_processor'] = self.video_processor.get_performance_metrics()

        # 清理过期缓存
        now = time.time()
        expired = [k for k, v in self.video_info_cache.items() if now - v[1] > self.cache_ttl]
        for k in expired:
            del self.video_info_cache[k]

        return metrics

    def optimize_performance(self) -> OperationResult:
        """优化性能，包括NVENC配置"""
        if self.state != EngineState.READY:
            return OperationResult(
                success=False,
                message=f"引擎未就绪，当前状态: {self.state.value}"
            )

        start_time = time.time()

        try:
            # 优化硬件加速设置
            self.hardware_acceleration.optimize_for_video_processing()

            # NVENC特定优化
            nvidia_info = self.hardware_acceleration.get_gpu_info('nvidia')
            if nvidia_info and nvidia_info.get('nvenc_supported', False):
                self.settings.default_video_codec = VideoCodec.H264_NVENC
                self.settings.default_quality_preset = 'fast'  # NVENC fast preset
                self.logger.info("NVENC性能优化已应用")

            # 优化视频处理器设置
            if self.video_processor:
                self.video_processor.optimize_settings()

            # 更新引擎设置
            optimization_settings = self.hardware_acceleration.optimize_for_video_processing()
            self.settings.max_concurrent_operations = optimization_settings.get('max_workers', 8)
            self.settings.memory_limit = optimization_settings.get('memory_limit', 2048 * 1024 * 1024)

            duration = time.time() - start_time

            result = OperationResult(
                success=True,
                message="性能优化完成 (NVENC启用)",
                data={'optimization_settings': optimization_settings},
                duration=duration,
                metadata={'optimization_settings': optimization_settings, 'nvenc_enabled': nvidia_info is not None}
            )

            self.event_bus.publish("performance_optimized", result)
            self.logger.info("性能优化完成")
            return result

        except Exception as e:
            duration = time.time() - start_time

            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"性能优化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoEngine",
                    operation="optimize_performance"
                ),
                user_message="性能优化失败"
            )
            self.error_handler.handle_error(error_info)

            result = OperationResult(
                success=False,
                message=f"性能优化失败: {str(e)}",
                error=e,
                duration=duration
            )

            self.event_bus.publish("performance_optimization_error", result)
            return result

    def _handle_engine_error(self, error_data: Any) -> None:
        """处理引擎错误"""
        self.logger.error(f"引擎错误: {error_data}")

    def _handle_performance_warning(self, warning_data: Any) -> None:
        """处理性能警告"""
        self.logger.warning(f"性能警告: {warning_data}")

    def _handle_memory_warning(self, warning_data: Any) -> None:
        """处理内存警告"""
        self.logger.warning(f"内存警告: {warning_data}")

    def shutdown(self) -> OperationResult:
        """关闭引擎"""
        if self.state in [EngineState.SHUTTING_DOWN, EngineState.UNINITIALIZED]:
            return OperationResult(
                success=False,
                message=f"引擎已关闭，当前状态: {self.state.value}"
            )

        self.state = EngineState.SHUTTING_DOWN
        start_time = time.time()

        try:
            # 关闭视频处理器
            if self.video_processor:
                self.video_processor.stop()

            # 关闭硬件加速监控
            self.hardware_acceleration.stop_monitoring()

            # 清理资源
            self.cleanup()

            duration = time.time() - start_time

            result = OperationResult(
                success=True,
                message="视频引擎已关闭",
                duration=duration
            )

            self.state = EngineState.UNINITIALIZED
            self.event_bus.publish("engine_shutdown", result)
            self.logger.info("视频引擎已关闭")
            return result

        except Exception as e:
            duration = time.time() - start_time

            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"引擎关闭失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoEngine",
                    operation="shutdown"
                ),
                user_message="引擎关闭失败"
            )
            self.error_handler.handle_error(error_info)

            result = OperationResult(
                success=False,
                message=f"引擎关闭失败: {str(e)}",
                error=e,
                duration=duration
            )

            self.event_bus.publish("engine_shutdown_error", result)
            return result

    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 关闭所有流
            with self.stream_lock:
                for stream_id in list(self.streams.keys()):
                    self.close_video_stream(stream_id)

            # 清空缓存
            self.video_info_cache.clear()

            # 清理临时文件
            import shutil
            if os.path.exists(self.settings.temp_directory):
                shutil.rmtree(self.settings.temp_directory)

            # 清理缓存
            if os.path.exists(self.settings.cache_directory):
                shutil.rmtree(self.settings.cache_directory)

            gc.collect()
            self.logger.info("资源清理完成")
        except Exception as e:
            self.logger.error(f"资源清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.shutdown()


# Worker类用于异步视频信息提取
class VideoInfoSignals(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)

class VideoInfoWorker(QRunnable):
    def __init__(self, video_path: str, engine: VideoEngine):
        super().__init__()
        self.video_path = video_path
        self.engine = engine
        self.signals = VideoInfoSignals()

    def run(self):
        try:
            # 检查缓存
            cache_key = self.video_path
            if hasattr(self.engine, 'video_info_cache') and cache_key in self.engine.video_info_cache:
                info, timestamp = self.engine.video_info_cache[cache_key]
                if time.time() - timestamp < self.engine.cache_ttl:
                    self.signals.result.emit(info)
                    return

            # 获取信息
            info = self.engine.ffmpeg_utils.get_video_info(self.video_path)
            self.signals.result.emit(info)
        except Exception as e:
            self.signals.error.emit(str(e))

# 全局视频引擎实例
_video_engine: Optional[VideoEngine] = None


def get_video_engine(settings: Optional[EngineSettings] = None) -> VideoEngine:
    """获取全局视频引擎实例"""
    global _video_engine
    if _video_engine is None:
        _video_engine = VideoEngine(settings)
        result = _video_engine.initialize()
        if not result.success:
            raise RuntimeError(f"视频引擎初始化失败: {result.message}")
    return _video_engine


def cleanup_video_engine() -> None:
    """清理全局视频引擎实例"""
    global _video_engine
    if _video_engine is not None:
        _video_engine.shutdown()
        _video_engine = None