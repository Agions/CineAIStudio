#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 导出系统
提供完整的视频导出功能，包括剪映Draft文件生成、多格式导出、队列管理等
"""

import os
import json
import threading
import queue
import time
import subprocess
import shutil
import tempfile
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QMessageBox

from ..core.event_system import EventBus
from ..core.logger import Logger


class ExportFormat(Enum):
    """导出格式枚举"""
    MP4_H264 = "mp4_h264"
    MP4_H265 = "mp4_h265"
    MOV_PRORES = "mov_prores"
    AVI_UNCOMPRESSED = "avi_uncompressed"
    MKV_H264 = "mkv_h264"
    WEBM_VP9 = "webm_vp9"
    GIF_ANIMATED = "gif_animated"
    MP3_AUDIO = "mp3_audio"
    WAV_AUDIO = "wav_audio"
    JIANYING_DRAFT = "jianying_draft"


class ExportQuality(Enum):
    """导出质量枚举"""
    LOW = "low"          # 480p, 1-2 Mbps
    MEDIUM = "medium"    # 720p, 3-5 Mbps
    HIGH = "high"        # 1080p, 8-12 Mbps
    ULTRA = "ultra"      # 4K, 20-50 Mbps
    CUSTOM = "custom"    # 自定义设置


class ExportStatus(Enum):
    """导出状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExportPreset:
    """导出预设配置"""
    id: str
    name: str
    format: ExportFormat
    quality: ExportQuality
    resolution: tuple[int, int]
    bitrate: int
    fps: float
    audio_bitrate: int
    supports_alpha: bool = False
    hw_acceleration: Optional[str] = None  # e.g., "cuda", "qsv", "nvenc"
    codec_params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class ExportTask:
    """导出任务"""
    id: str
    project_id: str
    output_path: str
    preset: ExportPreset
    status: ExportStatus = ExportStatus.PENDING
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    estimated_duration: Optional[float] = None


@dataclass
class JianyingDraftConfig:
    """剪映Draft配置"""
    project_name: str
    version: str = "1.0"
    fps: float = 30.0
    resolution: tuple[int, int] = (1920, 1080)
    audio_sample_rate: int = 48000
    tracks: List[Dict[str, Any]] = field(default_factory=list)
    materials: List[Dict[str, Any]] = field(default_factory=list)
    effects: List[Dict[str, Any]] = field(default_factory=list)
    text_overlays: List[Dict[str, Any]] = field(default_factory=list)


class ExportEngine:
    """导出引擎基类"""

    def __init__(self):
        self.logger = Logger(__name__)

    def export(self, task: ExportTask) -> bool:
        """执行导出任务"""
        raise NotImplementedError

    def get_capabilities(self) -> List[ExportFormat]:
        """获取支持的格式"""
        raise NotImplementedError

    def validate_config(self, preset: ExportPreset) -> bool:
        """验证配置"""
        raise NotImplementedError


class FFmpegEngine(ExportEngine):
    """FFmpeg导出引擎"""

    def __init__(self):
        super().__init__()
        from ..core.hardware_acceleration import get_hardware_acceleration
        self.hardware_acceleration = get_hardware_acceleration()
        self.ffmpeg_path = self._find_ffmpeg()
        self.supported_formats = [
            ExportFormat.MP4_H264,
            ExportFormat.MP4_H265,
            ExportFormat.MOV_PRORES,
            ExportFormat.AVI_UNCOMPRESSED,
            ExportFormat.MKV_H264,
            ExportFormat.WEBM_VP9,
            ExportFormat.GIF_ANIMATED,
            ExportFormat.MP3_AUDIO,
            ExportFormat.WAV_AUDIO
        ]

    def _find_ffmpeg(self) -> str:
        """查找FFmpeg路径"""
        # 检查系统PATH
        if shutil.which("ffmpeg"):
            return "ffmpeg"

        # 检查常见路径
        common_paths = [
            "/usr/local/bin/ffmpeg",
            "/opt/local/bin/ffmpeg",
            "C:\\ffmpeg\\bin\\ffmpeg.exe"
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        raise RuntimeError("FFmpeg not found")

    def get_capabilities(self) -> List[ExportFormat]:
        return self.supported_formats

    def export(self, task: ExportTask) -> bool:
        """使用FFmpeg导出"""
        try:
            cmd = self._build_ffmpeg_command(task)
            self.logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")

            # 执行FFmpeg命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 监控进度
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break

                if output:
                    progress = self._parse_ffmpeg_progress(output, task)
                    if progress:
                        task.progress = progress

            return process.returncode == 0

        except Exception as e:
            self.logger.error(f"FFmpeg export failed: {e}")
            task.error_message = str(e)
            return False

    def _build_ffmpeg_command(self, task: ExportTask) -> List[str]:
        """构建FFmpeg命令"""
        cmd = [self.ffmpeg_path]

        # 硬件加速参数
        hw_accel = task.preset.hw_acceleration
        if hw_accel and self.hardware_acceleration.hw_acceleration_type != "NONE":
            if hw_accel == "cuda" and self.hardware_acceleration.supported_frameworks:
                cmd.extend(["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"])
                cmd.extend(["-c:v", "h264_nvenc" if task.preset.format == ExportFormat.MP4_H264 else "hevc_nvenc"])
            elif hw_accel == "qsv" and "intel" in [g.vendor.value for g in self.hardware_acceleration.gpus]:
                cmd.extend(["-hwaccel", "qsv", "-c:v", "h264_qsv"])
            # 添加更多如 "nvenc", "quick_sync" 等

        # 输入参数
        cmd.extend(["-i", task.metadata.get("input_file", "")])

        # 视频编码参数
        preset = task.preset
        if preset.format == ExportFormat.MP4_H264 and not hw_accel:
            cmd.extend(["-c:v", "libx264"])
            cmd.extend(["-preset", "medium"])
            cmd.extend(["-crf", "23"])
        elif preset.format == ExportFormat.MP4_H265 and not hw_accel:
            cmd.extend(["-c:v", "libx265"])
            cmd.extend(["-preset", "medium"])
            cmd.extend(["-crf", "28"])
        elif preset.format == ExportFormat.MOV_PRORES:
            cmd.extend(["-c:v", "prores_ks"])
            cmd.extend(["-profile:v", "3"])

        # 分辨率
        if preset.resolution:
            cmd.extend(["-s", f"{preset.resolution[0]}x{preset.resolution[1]}"])

        # 帧率
        if preset.fps:
            cmd.extend(["-r", str(preset.fps)])

        # 比特率
        if preset.bitrate:
            cmd.extend(["-b:v", f"{preset.bitrate}k"])

        # 音频编码
        cmd.extend(["-c:a", "aac"])
        if preset.audio_bitrate:
            cmd.extend(["-b:a", f"{preset.audio_bitrate}k"])

        # 输出文件
        cmd.extend(["-y", task.output_path])

        return cmd

    def _parse_ffmpeg_progress(self, line: str, task: ExportTask) -> Optional[float]:
        """解析FFmpeg进度"""
        try:
            if "time=" in line:
                # 提取时间信息
                time_part = line.split("time=")[1].split()[0]
                current_time = self._parse_time(time_part)
                total_time = task.metadata.get("duration", 0)

                if total_time > 0:
                    return min(100.0, (current_time / total_time) * 100)
        except:
            pass
        return None

    def _parse_time(self, time_str: str) -> float:
        """解析时间字符串"""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        except:
            pass
        return 0.0


class JianyingEngine(ExportEngine):
    """剪映Draft导出引擎"""

    def __init__(self):
        super().__init__()
        self.supported_formats = [ExportFormat.JIANYING_DRAFT]

    def get_capabilities(self) -> List[ExportFormat]:
        return self.supported_formats

    def export(self, task: ExportTask) -> bool:
        """生成剪映Draft文件"""
        try:
            config = task.metadata.get("jianying_config")
            if not config:
                raise ValueError("Jianying config not provided")

            # 生成Draft文件
            draft_data = self._generate_draft_data(config)

            # 保存Draft文件
            with open(task.output_path, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Jianying draft generation failed: {e}")
            task.error_message = str(e)
            return False

    def _generate_draft_data(self, config: JianyingDraftConfig) -> Dict[str, Any]:
        """生成Draft文件数据"""
        return {
            "version": config.version,
            "project_name": config.project_name,
            "settings": {
                "fps": config.fps,
                "resolution": {
                    "width": config.resolution[0],
                    "height": config.resolution[1]
                },
                "audio_sample_rate": config.audio_sample_rate
            },
            "tracks": config.tracks,
            "materials": config.materials,
            "effects": config.effects,
            "text_overlays": config.text_overlays,
            "metadata": {
                "created_by": "CineAIStudio",
                "created_at": time.time()
            }
        }


class ExportQueueManager(QObject):
    """导出队列管理器"""

    # 信号定义
    task_added = pyqtSignal(ExportTask)
    task_started = pyqtSignal(ExportTask)
    task_progress = pyqtSignal(ExportTask, float)
    task_completed = pyqtSignal(ExportTask)
    task_failed = pyqtSignal(ExportTask, str)
    task_cancelled = pyqtSignal(ExportTask)
    queue_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.logger = Logger(__name__)
        self.task_queue = queue.PriorityQueue()
        self.active_tasks: Dict[str, ExportTask] = {}
        self.completed_tasks: List[ExportTask] = []
        self.failed_tasks: List[ExportTask] = {}
        self.engines: Dict[ExportFormat, ExportEngine] = {}
        self.max_concurrent_tasks = 2
        self.is_running = False
        self.worker_thread = None

        self._initialize_engines()
        self._start_worker_thread()

    def _initialize_engines(self):
        """初始化导出引擎"""
        try:
            ffmpeg_engine = FFmpegEngine()
            for format_type in ffmpeg_engine.get_capabilities():
                self.engines[format_type] = ffmpeg_engine

            jianying_engine = JianyingEngine()
            for format_type in jianying_engine.get_capabilities():
                self.engines[format_type] = jianying_engine

            self.logger.info(f"Initialized {len(self.engines)} export engines")
        except Exception as e:
            self.logger.error(f"Failed to initialize engines: {e}")

    def _start_worker_thread(self):
        """启动工作线程"""
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.is_running = True

    def _worker_loop(self):
        """工作线程主循环"""
        from PyQt6.QtCore import QThreadPool, QRunnable, Slot, QThread
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(self.max_concurrent_tasks)

        while self.is_running:
            try:
                # 检查是否有空闲的任务槽
                if len(self.active_tasks) < self.max_concurrent_tasks:
                    # 从队列获取任务
                    try:
                        priority, task_id, task = self.task_queue.get_nowait()
                        task.status = ExportStatus.QUEUED

                        # 创建QRunnable任务
                        class ExportRunnable(QRunnable):
                            def __init__(self, task, manager):
                                super().__init__()
                                self.task = task
                                self.manager = manager

                            @Slot()
                            def run(self):
                                self.manager._execute_task(self.task)

                        runnable = ExportRunnable(task, self)
                        self.thread_pool.start(runnable)
                    except queue.Empty:
                        pass

                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                time.sleep(1)

    def _execute_task(self, task: ExportTask, max_retries: int = 3):
        """执行导出任务，支持重试"""
        for attempt in range(max_retries):
            try:
                task.status = ExportStatus.PROCESSING
                task.started_at = time.time()
                self.active_tasks[task.id] = task

                self.task_started.emit(task)

                # 获取对应的导出引擎
                engine = self.engines.get(task.preset.format)
                if not engine:
                    raise ValueError(f"No engine available for format: {task.preset.format}")

                # 执行导出
                success = engine.export(task)

                if success:
                    task.status = ExportStatus.COMPLETED
                    task.completed_at = time.time()
                    self.completed_tasks.append(task)
                    self.task_completed.emit(task)
                    return  # 成功退出重试循环
                else:
                    raise RuntimeError(f"Export failed on attempt {attempt + 1}: {task.error_message}")

            except Exception as e:
                task.status = ExportStatus.FAILED
                task.error_message = str(e)
                task.completed_at = time.time()
                self.failed_tasks[task.id] = task
                self.task_failed.emit(task, str(e))

                if attempt < max_retries - 1:
                    self.logger.warning(f"Retry {attempt + 1}/{max_retries} for task {task.id}: {e}")
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    self.logger.error(f"All retries failed for task {task.id}: {e}")

            finally:
                self.active_tasks.pop(task.id, None)
                self.queue_changed.emit()

    def add_task(self, task: ExportTask) -> bool:
        """添加导出任务"""
        try:
            task.status = ExportStatus.QUEUED
            self.task_queue.put((-task.priority, task.id, task))
            self.task_added.emit(task)
            self.queue_changed.emit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to add task: {e}")
            return False

    def cancel_task(self, task_id: str) -> bool:
        """取消导出任务"""
        # 检查活动任务
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = ExportStatus.CANCELLED
            task.completed_at = time.time()
            self.task_cancelled.emit(task)
            return True

        # 无法取消队列中的任务（已排队但未开始）
        return False

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "queue_size": self.task_queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "max_concurrent": self.max_concurrent_tasks
        }

    def get_task_history(self, limit: int = 50) -> List[ExportTask]:
        """获取任务历史"""
        all_tasks = self.completed_tasks + list(self.failed_tasks.values())
        # 按完成时间排序
        all_tasks.sort(key=lambda x: x.completed_at or 0, reverse=True)
        return all_tasks[:limit]

    def cleanup_completed_tasks(self, max_age: float = 86400):
        """清理已完成的任务（24小时前）"""
        current_time = time.time()
        self.completed_tasks = [
            task for task in self.completed_tasks
            if (task.completed_at or current_time) > current_time - max_age
        ]

    def shutdown(self):
        """关闭队列管理器"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)


class ExportPresetManager:
    """导出预设管理器"""

    def __init__(self):
        self.logger = Logger(__name__)
        self.presets: Dict[str, ExportPreset] = {}
        self._load_default_presets()

    def _load_default_presets(self):
        """加载默认预设"""
        default_presets = [
            ExportPreset(
                id="youtube_1080p",
                name="YouTube 1080p",
                format=ExportFormat.MP4_H264,
                quality=ExportQuality.HIGH,
                resolution=(1920, 1080),
                bitrate=8000,
                fps=30,
                audio_bitrate=128,
                description="适用于YouTube的高质量1080p视频"
            ),
            ExportPreset(
                id="youtube_4k",
                name="YouTube 4K",
                format=ExportFormat.MP4_H265,
                quality=ExportQuality.ULTRA,
                resolution=(3840, 2160),
                bitrate=35000,
                fps=30,
                audio_bitrate=192,
                description="适用于YouTube的4K超高清视频"
            ),
            ExportPreset(
                id="instagram_reel",
                name="Instagram Reel",
                format=ExportFormat.MP4_H264,
                quality=ExportQuality.MEDIUM,
                resolution=(1080, 1920),
                bitrate=4000,
                fps=30,
                audio_bitrate=128,
                description="适用于Instagram Reel的竖版视频"
            ),
            ExportPreset(
                id="tiktok_video",
                name="TikTok Video",
                format=ExportFormat.MP4_H264,
                quality=ExportQuality.MEDIUM,
                resolution=(1080, 1920),
                bitrate=3000,
                fps=30,
                audio_bitrate=128,
                description="适用于TikTok的竖版视频"
            ),
            ExportPreset(
                id="master_quality",
                name="母版质量",
                format=ExportFormat.MOV_PRORES,
                quality=ExportQuality.ULTRA,
                resolution=(1920, 1080),
                bitrate=50000,
                fps=30,
                audio_bitrate=320,
                description="适用于后期制作的高质量母版"
            ),
            ExportPreset(
                id="jianying_draft",
                name="剪映草稿",
                format=ExportFormat.JIANYING_DRAFT,
                quality=ExportQuality.HIGH,
                resolution=(1920, 1080),
                bitrate=0,
                fps=30,
                audio_bitrate=0,
                description="导出为剪映草稿文件"
            )
        ]

        for preset in default_presets:
            self.presets[preset.id] = preset

    def add_preset(self, preset: ExportPreset) -> bool:
        """添加预设"""
        try:
            self.presets[preset.id] = preset
            self.logger.info(f"Added preset: {preset.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add preset: {e}")
            return False

    def remove_preset(self, preset_id: str) -> bool:
        """删除预设"""
        if preset_id in self.presets:
            del self.presets[preset_id]
            return True
        return False

    def get_preset(self, preset_id: str) -> Optional[ExportPreset]:
        """获取预设"""
        return self.presets.get(preset_id)

    def get_all_presets(self) -> List[ExportPreset]:
        """获取所有预设"""
        return list(self.presets.values())

    def get_presets_by_format(self, format_type: ExportFormat) -> List[ExportPreset]:
        """按格式获取预设"""
        return [p for p in self.presets.values() if p.format == format_type]

    def save_presets(self, file_path: str):
        """保存预设到文件"""
        try:
            presets_data = {}
            for preset_id, preset in self.presets.items():
                presets_data[preset_id] = {
                    "id": preset.id,
                    "name": preset.name,
                    "format": preset.format.value,
                    "quality": preset.quality.value,
                    "resolution": preset.resolution,
                    "bitrate": preset.bitrate,
                    "fps": preset.fps,
                    "audio_bitrate": preset.audio_bitrate,
                    "codec_params": preset.codec_params,
                    "description": preset.description
                }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(presets_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Saved {len(self.presets)} presets to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save presets: {e}")

    def load_presets(self, file_path: str):
        """从文件加载预设"""
        try:
            if not os.path.exists(file_path):
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                presets_data = json.load(f)

            for preset_id, preset_data in presets_data.items():
                preset = ExportPreset(
                    id=preset_data["id"],
                    name=preset_data["name"],
                    format=ExportFormat(preset_data["format"]),
                    quality=ExportQuality(preset_data["quality"]),
                    resolution=tuple(preset_data["resolution"]),
                    bitrate=preset_data["bitrate"],
                    fps=preset_data["fps"],
                    audio_bitrate=preset_data["audio_bitrate"],
                    codec_params=preset_data.get("codec_params", {}),
                    description=preset_data.get("description", "")
                )
                self.presets[preset_id] = preset

            self.logger.info(f"Loaded {len(self.presets)} presets from {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to load presets: {e}")


class ExportSystem(QObject):
    """导出系统主类"""

    # 信号定义
    export_started = pyqtSignal(str)
    export_progress = pyqtSignal(str, float)
    export_completed = pyqtSignal(str, str)
    export_failed = pyqtSignal(str, str)
    export_cancelled = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.logger = Logger(__name__)
        self.queue_manager = ExportQueueManager()
        self.preset_manager = ExportPresetManager()
        self.event_system = EventBus()

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接信号"""
        self.queue_manager.task_started.connect(self._on_task_started)
        self.queue_manager.task_progress.connect(self._on_task_progress)
        self.queue_manager.task_completed.connect(self._on_task_completed)
        self.queue_manager.task_failed.connect(self._on_task_failed)
        self.queue_manager.task_cancelled.connect(self._on_task_cancelled)

    def _on_task_started(self, task: ExportTask):
        """任务开始信号处理"""
        self.export_started.emit(task.id)
        self.event_system.emit("export_started", {"task_id": task.id})

    def _on_task_progress(self, task: ExportTask, progress: float):
        """任务进度信号处理"""
        self.export_progress.emit(task.id, progress)
        self.event_system.emit("export_progress", {
            "task_id": task.id,
            "progress": progress
        })

    def _on_task_completed(self, task: ExportTask):
        """任务完成信号处理"""
        self.export_completed.emit(task.id, task.output_path)
        self.event_system.emit("export_completed", {
            "task_id": task.id,
            "output_path": task.output_path
        })

    def _on_task_failed(self, task: ExportTask, error_message: str):
        """任务失败信号处理"""
        self.export_failed.emit(task.id, error_message)
        self.event_system.emit("export_failed", {
            "task_id": task.id,
            "error": error_message
        })

    def _on_task_cancelled(self, task: ExportTask):
        """任务取消信号处理"""
        self.export_cancelled.emit(task.id)
        self.event_system.emit("export_cancelled", {"task_id": task.id})

    def export_project(self,
                      project_id: str,
                      output_path: str,
                      preset_id: str,
                      metadata: Dict[str, Any] = None) -> str:
        """导出项目"""
        try:
            # 获取预设
            preset = self.preset_manager.get_preset(preset_id)
            if not preset:
                raise ValueError(f"Preset not found: {preset_id}")

            # 创建导出任务
            task = ExportTask(
                id=f"export_{int(time.time() * 1000)}",
                project_id=project_id,
                output_path=output_path,
                preset=preset,
                metadata=metadata or {}
            )

            # 添加到队列
            if self.queue_manager.add_task(task):
                self.logger.info(f"Added export task: {task.id}")
                return task.id
            else:
                raise RuntimeError("Failed to add export task")

        except Exception as e:
            self.logger.error(f"Export project failed: {e}")
            raise

    def export_batch(self,
                    project_configs: List[Dict[str, Any]]) -> List[str]:
        """批量导出"""
        task_ids = []

        for config in project_configs:
            try:
                task_id = self.export_project(
                    project_id=config["project_id"],
                    output_path=config["output_path"],
                    preset_id=config["preset_id"],
                    metadata=config.get("metadata", {})
                )
                task_ids.append(task_id)
            except Exception as e:
                self.logger.error(f"Batch export failed for {config}: {e}")

        return task_ids

    def cancel_export(self, task_id: str) -> bool:
        """取消导出"""
        return self.queue_manager.cancel_task(task_id)

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return self.queue_manager.get_queue_status()

    def get_task_history(self, limit: int = 50) -> List[ExportTask]:
        """获取任务历史"""
        return self.queue_manager.get_task_history(limit)

    def get_presets(self) -> List[ExportPreset]:
        """获取所有预设"""
        return self.preset_manager.get_all_presets()

    def add_preset(self, preset: ExportPreset) -> bool:
        """添加预设"""
        return self.preset_manager.add_preset(preset)

    def remove_preset(self, preset_id: str) -> bool:
        """删除预设"""
        return self.preset_manager.remove_preset(preset_id)

    def shutdown(self):
        """关闭导出系统"""
        self.queue_manager.shutdown()
        self.logger.info("Export system shutdown complete")


# 全局导出系统实例
export_system = ExportSystem()