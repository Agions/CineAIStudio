#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 视频处理器模块
提供专业的视频处理管道，支持实时处理、多格式支持和智能优化
"""

import os
import time
import threading
import queue
import logging
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from contextlib import asynccontextmanager
import asyncio

from .logger import get_logger
from .event_system import EventBus
from .hardware_acceleration import get_hardware_acceleration, PerformanceMetrics
from .config_manager import get_config_manager
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import (
    get_ffmpeg_utils, VideoInfo, VideoCodec, AudioCodec, ContainerFormat,
    HWAccelerationType, FFmpegCommand
)


class ProcessingStage(Enum):
    """处理阶段枚举"""
    INPUT = "input"
    PREPROCESS = "preprocess"
    ANALYSIS = "analysis"
    PROCESSING = "processing"
    POSTPROCESS = "postprocess"
    OUTPUT = "output"


class ProcessingPriority(Enum):
    """处理优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class ProcessingStatus(Enum):
    """处理状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VideoFrame:
    """视频帧数据类"""
    data: bytes
    timestamp: float
    index: int
    width: int
    height: int
    format: str = "rgb24"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingTask:
    """处理任务数据类"""
    id: str
    name: str
    input_path: str
    output_path: str
    priority: ProcessingPriority
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable[['ProcessingTask'], None]] = None
    cancel_flag: threading.Event = field(default_factory=threading.Event)

    @property
    def duration(self) -> Optional[float]:
        """任务持续时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return None

    def cancel(self) -> None:
        """取消任务"""
        self.cancel_flag.set()
        self.status = ProcessingStatus.CANCELLED


@dataclass
class ProcessingConfig:
    """处理配置数据类"""
    max_concurrent_tasks: int = 4
    max_queue_size: int = 100
    use_gpu: bool = True
    use_hardware_acceleration: bool = True
    memory_limit: int = 1024 * 1024 * 1024  # 1GB
    temp_dir: str = "/tmp/cineaistudio"
    enable_real_time: bool = True
    enable_caching: bool = True
    enable_progress_monitoring: bool = True
    auto_optimize: bool = True
    quality_preset: str = "medium"  # low, medium, high
    output_format: ContainerFormat = ContainerFormat.MP4
    video_codec: VideoCodec = VideoCodec.H264
    audio_codec: AudioCodec = AudioCodec.AAC


class VideoProcessor:
    """视频处理器"""

    def __init__(self, config: Optional[ProcessingConfig] = None, logger=None):
        """初始化视频处理器"""
        self.logger = logger or get_logger("VideoProcessor")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.config = config or ProcessingConfig()
        self.ffmpeg_utils = get_ffmpeg_utils()
        self.hardware_acceleration = get_hardware_acceleration()
        self.config_manager = get_config_manager()

        # 任务管理
        self.tasks: Dict[str, ProcessingTask] = {}
        self.task_queue = queue.PriorityQueue(maxsize=self.config.max_queue_size)
        self.active_tasks: Dict[str, Future] = {}
        self.completed_tasks: Dict[str, ProcessingTask] = {}
        self.task_lock = threading.Lock()

        # 处理线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_concurrent_tasks)
        self.processing_thread = None
        self.is_running = False

        # 性能监控
        self.metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'average_processing_time': 0.0,
            'throughput': 0.0
        }

        # 缓存系统
        self.cache = {}
        self.cache_lock = threading.Lock()

        # 初始化
        self._initialize_directories()
        self._initialize_optimization()

    def _initialize_directories(self) -> None:
        """初始化目录"""
        try:
            os.makedirs(self.config.temp_dir, exist_ok=True)
            self.logger.info(f"临时目录创建成功: {self.config.temp_dir}")
        except Exception as e:
            self.logger.error(f"临时目录创建失败: {str(e)}")

    def _initialize_optimization(self) -> None:
        """初始化优化设置"""
        try:
            if self.config.auto_optimize:
                optimization_settings = self.hardware_acceleration.optimize_for_video_processing()
                self.config.max_concurrent_tasks = optimization_settings.get('max_workers', 4)
                self.config.use_gpu = optimization_settings.get('gpu_enabled', True)
                self.config.memory_limit = optimization_settings.get('memory_limit', 1024 * 1024 * 1024)

                # 重新初始化线程池
                self.thread_pool.shutdown(wait=True)
                self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_concurrent_tasks)

                self.logger.info("系统优化设置已应用")
        except Exception as e:
            self.logger.error(f"系统优化失败: {str(e)}")

    def start(self) -> None:
        """启动处理器"""
        if self.is_running:
            return

        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
        self.processing_thread.start()

        # 启动性能监控
        self.hardware_acceleration.start_monitoring()

        self.logger.info("视频处理器已启动")

    def stop(self) -> None:
        """停止处理器"""
        self.is_running = False

        # 等待处理线程结束
        if self.processing_thread:
            self.processing_thread.join()

        # 停止线程池
        self.thread_pool.shutdown(wait=True)

        # 停止性能监控
        self.hardware_acceleration.stop_monitoring()

        self.logger.info("视频处理器已停止")

    def _processing_worker(self) -> None:
        """处理工作线程"""
        while self.is_running:
            try:
                # 从队列获取任务
                task = self.task_queue.get(timeout=1.0)
                self._process_task(task)
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"处理工作线程错误: {str(e)}")

    def _process_task(self, task: ProcessingTask) -> None:
        """处理单个任务"""
        try:
            with self.task_lock:
                task.status = ProcessingStatus.PROCESSING
                task.start_time = time.time()
                self.active_tasks[task.id] = self.thread_pool.submit(self._execute_task, task)

            # 发送任务开始事件
            self.event_bus.publish("task_started", task)

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"任务处理失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoProcessor",
                    operation="_process_task"
                ),
                user_message="任务处理失败，请稍后重试"
            )
            self.error_handler.handle_error(error_info)
            task.status = ProcessingStatus.FAILED
            task.error = str(e)

    def _execute_task(self, task: ProcessingTask) -> None:
        """执行任务"""
        try:
            self.logger.info(f"开始处理任务: {task.name} ({task.id})")

            # 检查任务是否被取消
            if task.cancel_flag.is_set():
                task.status = ProcessingStatus.CANCELLED
                return

            # 获取视频信息
            video_info = self.ffmpeg_utils.get_video_info(task.input_path)

            # 根据任务类型执行不同的处理
            if task.metadata.get('type') == 'transcode':
                self._transcode_video(task, video_info)
            elif task.metadata.get('type') == 'resize':
                self._resize_video(task, video_info)
            elif task.metadata.get('type') == 'concat':
                self._concat_videos(task)
            elif task.metadata.get('type') == 'extract_frames':
                self._extract_frames(task, video_info)
            elif task.metadata.get('type') == 'apply_filter':
                self._apply_filter(task, video_info)
            else:
                # 默认处理
                self._transcode_video(task, video_info)

            # 任务完成
            task.status = ProcessingStatus.COMPLETED
            task.end_time = time.time()
            task.progress = 1.0

            # 更新统计信息
            self._update_metrics(task)

            # 调用回调函数
            if task.callback:
                task.callback(task)

            # 发送任务完成事件
            self.event_bus.publish("task_completed", task)

            self.logger.info(f"任务处理完成: {task.name} ({task.id})")

        except Exception as e:
            task.status = ProcessingStatus.FAILED
            task.error = str(e)
            task.end_time = time.time()

            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.HIGH,
                message=f"任务执行失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoProcessor",
                    operation="_execute_task"
                ),
                user_message=f"视频处理失败: {task.name}"
            )
            self.error_handler.handle_error(error_info)

            # 发送任务失败事件
            self.event_bus.publish("task_failed", task)

            self.logger.error(f"任务执行失败: {task.name} ({task.id}) - {str(e)}")

    def _transcode_video(self, task: ProcessingTask, video_info: VideoInfo) -> None:
        """转码视频"""
        try:
            # 构建FFmpeg命令
            cmd = [
                self.ffmpeg_utils.ffmpeg_path,
                "-i", task.input_path,
            ]

            # 添加硬件加速参数
            if self.config.use_hardware_acceleration:
                cmd.extend(self.ffmpeg_utils.get_hw_acceleration_params())

            # 添加编码参数
            cmd.extend(self.ffmpeg_utils.get_encoding_params(
                self.config.video_codec,
                self.config.quality_preset
            ))

            # 添加音频参数
            cmd.extend([
                "-c:a", self.config.audio_codec.value,
                "-b:a", "192k"
            ])

            # 输出参数
            cmd.extend([
                "-y",
                task.output_path
            ])

            # 创建FFmpeg命令对象
            ffmpeg_cmd = FFmpegCommand(
                command=cmd,
                description=f"转码视频: {task.name}",
                timeout=3600,
                expected_duration=video_info.duration,
                progress_callback=lambda progress: self._update_task_progress(task, progress),
                output_path=task.output_path
            )

            # 执行命令
            self.ffmpeg_utils.add_to_queue(ffmpeg_cmd)

            self.logger.info(f"视频转码任务已提交: {task.name}")

        except Exception as e:
            self.logger.error(f"视频转码失败: {str(e)}")
            raise

    def _resize_video(self, task: ProcessingTask, video_info: VideoInfo) -> None:
        """调整视频尺寸"""
        try:
            target_width = task.metadata.get('width', 1920)
            target_height = task.metadata.get('height', 1080)

            cmd = [
                self.ffmpeg_utils.ffmpeg_path,
                "-i", task.input_path,
            ]

            # 添加硬件加速参数
            if self.config.use_hardware_acceleration:
                cmd.extend(self.ffmpeg_utils.get_hw_acceleration_params())

            # 添加尺寸调整参数
            cmd.extend([
                "-vf", f"scale={target_width}:{target_height}",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "copy",
                "-y",
                task.output_path
            ])

            # 创建FFmpeg命令对象
            ffmpeg_cmd = FFmpegCommand(
                command=cmd,
                description=f"调整视频尺寸: {task.name}",
                timeout=1800,
                expected_duration=video_info.duration,
                progress_callback=lambda progress: self._update_task_progress(task, progress),
                output_path=task.output_path
            )

            # 执行命令
            self.ffmpeg_utils.add_to_queue(ffmpeg_cmd)

            self.logger.info(f"视频尺寸调整任务已提交: {task.name}")

        except Exception as e:
            self.logger.error(f"视频尺寸调整失败: {str(e)}")
            raise

    def _concat_videos(self, task: ProcessingTask) -> None:
        """合并视频"""
        try:
            video_paths = task.metadata.get('video_paths', [])
            if not video_paths:
                raise ValueError("没有提供要合并的视频路径")

            # 使用FFmpeg工具的合并功能
            self.ffmpeg_utils.concat_videos(video_paths, task.output_path)

            self.logger.info(f"视频合并任务完成: {task.name}")

        except Exception as e:
            self.logger.error(f"视频合并失败: {str(e)}")
            raise

    def _extract_frames(self, task: ProcessingTask, video_info: VideoInfo) -> None:
        """提取视频帧"""
        try:
            frame_rate = task.metadata.get('frame_rate', 1)
            output_dir = task.output_path

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)

            cmd = [
                self.ffmpeg_utils.ffmpeg_path,
                "-i", task.input_path,
                "-vf", f"fps={frame_rate}",
                "-q:v", "2",
                f"{output_dir}/frame_%06d.jpg"
            ]

            # 创建FFmpeg命令对象
            ffmpeg_cmd = FFmpegCommand(
                command=cmd,
                description=f"提取视频帧: {task.name}",
                timeout=1800,
                expected_duration=video_info.duration,
                progress_callback=lambda progress: self._update_task_progress(task, progress),
                output_path=output_dir
            )

            # 执行命令
            self.ffmpeg_utils.add_to_queue(ffmpeg_cmd)

            self.logger.info(f"视频帧提取任务已提交: {task.name}")

        except Exception as e:
            self.logger.error(f"视频帧提取失败: {str(e)}")
            raise

    def _apply_filter(self, task: ProcessingTask, video_info: VideoInfo) -> None:
        """应用滤镜"""
        try:
            filter_chain = task.metadata.get('filter_chain', '')
            if not filter_chain:
                raise ValueError("没有提供滤镜链")

            cmd = [
                self.ffmpeg_utils.ffmpeg_path,
                "-i", task.input_path,
            ]

            # 添加硬件加速参数
            if self.config.use_hardware_acceleration:
                cmd.extend(self.ffmpeg_utils.get_hw_acceleration_params())

            # 添加滤镜参数
            cmd.extend([
                "-vf", filter_chain,
                "-c:a", "copy",
                "-y",
                task.output_path
            ])

            # 创建FFmpeg命令对象
            ffmpeg_cmd = FFmpegCommand(
                command=cmd,
                description=f"应用视频滤镜: {task.name}",
                timeout=1800,
                expected_duration=video_info.duration,
                progress_callback=lambda progress: self._update_task_progress(task, progress),
                output_path=task.output_path
            )

            # 执行命令
            self.ffmpeg_utils.add_to_queue(ffmpeg_cmd)

            self.logger.info(f"视频滤镜应用任务已提交: {task.name}")

        except Exception as e:
            self.logger.error(f"视频滤镜应用失败: {str(e)}")
            raise

    def _update_task_progress(self, task: ProcessingTask, progress: float) -> None:
        """更新任务进度"""
        task.progress = progress
        self.event_bus.publish("task_progress", {"task_id": task.id, "progress": progress})

    def _update_metrics(self, task: ProcessingTask) -> None:
        """更新统计信息"""
        self.metrics['total_tasks'] += 1

        if task.status == ProcessingStatus.COMPLETED:
            self.metrics['completed_tasks'] += 1
            if task.duration:
                self.metrics['average_processing_time'] = (
                    (self.metrics['average_processing_time'] * (self.metrics['completed_tasks'] - 1) + task.duration) /
                    self.metrics['completed_tasks']
                )
        elif task.status == ProcessingStatus.FAILED:
            self.metrics['failed_tasks'] += 1
        elif task.status == ProcessingStatus.CANCELLED:
            self.metrics['cancelled_tasks'] += 1

        # 计算吞吐量
        if self.metrics['total_tasks'] > 0:
            self.metrics['throughput'] = self.metrics['completed_tasks'] / self.metrics['total_tasks']

    def add_task(self, task: ProcessingTask) -> bool:
        """添加任务"""
        try:
            if not self.is_running:
                raise RuntimeError("处理器未启动")

            with self.task_lock:
                if len(self.tasks) >= self.config.max_queue_size:
                    raise RuntimeError("任务队列已满")

                self.tasks[task.id] = task
                # 优先级队列需要比较元组，使用负数让高优先级先出队
                self.task_queue.put((-task.priority.value, task.id, task))
                task.status = ProcessingStatus.QUEUED

            self.logger.info(f"任务已添加: {task.name} ({task.id})")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"添加任务失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoProcessor",
                    operation="add_task"
                ),
                user_message="无法添加处理任务"
            )
            self.error_handler.handle_error(error_info)
            return False

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            with self.task_lock:
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    task.cancel()

                    if task_id in self.active_tasks:
                        future = self.active_tasks[task_id]
                        future.cancel()

                    self.logger.info(f"任务已取消: {task.name} ({task_id})")
                    return True
                return False

        except Exception as e:
            self.logger.error(f"取消任务失败: {str(e)}")
            return False

    def get_task(self, task_id: str) -> Optional[ProcessingTask]:
        """获取任务信息"""
        with self.task_lock:
            return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[ProcessingTask]:
        """获取所有任务"""
        with self.task_lock:
            return list(self.tasks.values())

    def get_active_tasks(self) -> List[ProcessingTask]:
        """获取活动任务"""
        with self.task_lock:
            return [task for task in self.tasks.values() if task.status == ProcessingStatus.PROCESSING]

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        with self.task_lock:
            return {
                'total_tasks': len(self.tasks),
                'queued_tasks': len([t for t in self.tasks.values() if t.status == ProcessingStatus.QUEUED]),
                'processing_tasks': len([t for t in self.tasks.values() if t.status == ProcessingStatus.PROCESSING]),
                'completed_tasks': len([t for t in self.tasks.values() if t.status == ProcessingStatus.COMPLETED]),
                'failed_tasks': len([t for t in self.tasks.values() if t.status == ProcessingStatus.FAILED]),
                'cancelled_tasks': len([t for t in self.tasks.values() if t.status == ProcessingStatus.CANCELLED]),
                'queue_size': self.task_queue.qsize(),
                'metrics': self.metrics.copy()
            }

    def wait_for_completion(self, timeout: Optional[float] = None) -> None:
        """等待所有任务完成"""
        try:
            self.task_queue.join()
            for future in as_completed(self.active_tasks.values(), timeout=timeout):
                future.result()
        except Exception as e:
            self.logger.error(f"等待任务完成失败: {str(e)}")

    def clear_completed_tasks(self) -> None:
        """清理已完成的任务"""
        try:
            with self.task_lock:
                completed_ids = [task_id for task_id, task in self.tasks.items()
                               if task.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]]
                for task_id in completed_ids:
                    del self.tasks[task_id]

            self.logger.info(f"清理了 {len(completed_ids)} 个已完成任务")
        except Exception as e:
            self.logger.error(f"清理已完成任务失败: {str(e)}")

    def optimize_settings(self) -> None:
        """优化设置"""
        try:
            optimization_settings = self.hardware_acceleration.optimize_for_video_processing()

            self.config.max_concurrent_tasks = optimization_settings.get('max_workers', 4)
            self.config.use_gpu = optimization_settings.get('gpu_enabled', True)
            self.config.memory_limit = optimization_settings.get('memory_limit', 1024 * 1024 * 1024)

            # 重新初始化线程池
            self.thread_pool.shutdown(wait=True)
            self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_concurrent_tasks)

            self.logger.info("处理器设置已优化")

        except Exception as e:
            self.logger.error(f"优化设置失败: {str(e)}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            metrics = self.get_queue_status()
            metrics['hardware_metrics'] = self.hardware_acceleration.get_performance_metrics()
            metrics['ffmpeg_queue'] = {
                'is_busy': self.ffmpeg_utils.is_busy(),
                'queue_size': self.ffmpeg_utils.command_queue.qsize()
            }
            return metrics
        except Exception as e:
            self.logger.error(f"获取性能指标失败: {str(e)}")
            return {}

    def cleanup(self) -> None:
        """清理资源"""
        try:
            self.stop()
            self.clear_completed_tasks()
            self.ffmpeg_utils.cleanup()
            self.logger.info("视频处理器清理完成")
        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局视频处理器实例
_video_processor: Optional[VideoProcessor] = None


def get_video_processor(config: Optional[ProcessingConfig] = None) -> VideoProcessor:
    """获取全局视频处理器实例"""
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor(config)
        _video_processor.start()
    return _video_processor


def cleanup_video_processor() -> None:
    """清理全局视频处理器实例"""
    global _video_processor
    if _video_processor is not None:
        _video_processor.cleanup()
        _video_processor = None