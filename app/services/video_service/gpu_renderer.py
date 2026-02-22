#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow GPU加速视频渲染器
支持NVIDIA NVENC、AMD AMF、Intel QSV等硬件加速
"""

import os
import sys
import subprocess
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ...core.logger import Logger
from ...core.event_bus import EventBus


class GPUType(Enum):
    """GPU类型"""
    NVIDIA = "nvidia"      # NVIDIA GPU (CUDA/NVENC)
    AMD = "amd"            # AMD GPU (OpenCL/AMF)
    INTEL = "intel"        # Intel GPU (QSV)
    APPLE = "apple"        # Apple Silicon (VideoToolbox)
    NONE = "none"          # 无硬件加速


class EncoderType(Enum):
    """编码器类型"""
    H264 = "h264"
    HEVC = "hevc"
    AV1 = "av1"
    VP9 = "vp9"


@dataclass
class EncodingConfig:
    """编码配置"""
    encoder: EncoderType
    preset: str = "medium"  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
    crf: int = 23          # 质量参数 (0-51, 越低质量)
    bitrate: Optional[int] = None
    keyframe_interval: int = 250
    gop_size: int = 250
    pixel_format: str = "yuv420p"
    threads: int = 0        # 0 = 自动检测


@dataclass
class RenderTask:
    """渲染任务"""
    task_id: str
    input_path: str
    output_path: str
    start_time: float
    end_time: float
    config: EncodingConfig
    metadata: Dict[str, Any]


class GPURenderer:
    """GPU渲染器"""

    def __init__(self, logger: Logger, event_bus: EventBus):
        self.logger = logger
        self.event_bus = event_bus

        # GPU检测和配置
        self.gpu_type = self._detect_gpu()
        self.available_encoders = self._get_available_encoders()
        self.ffmpeg_path = self._find_ffmpeg()

        # 渲染任务
        self.active_tasks: Dict[str, RenderTask] = {}
        self.render_queue: List[RenderTask] = []
        self.max_concurrent_tasks = 2

        # 性能统计
        self.stats = {
            "total_renders": 0,
            "successful_renders": 0,
            "failed_renders": 0,
            "total_render_time": 0.0,
            "average_fps": 0.0,
            "gpu_utilization": 0.0
        }

        # 初始化FFmpeg
        self._initialize_ffmpeg()

    def detect_hardware_acceleration(self) -> Dict[str, Any]:
        """检测硬件加速能力"""
        capabilities = {
            "gpu_type": self.gpu_type.value,
            "available_encoders": [enc.value for enc in self.available_encoders],
            "hardware_acceleration": self.gpu_type != GPUType.NONE,
            "encoder_support": {}
        }

        # 测试编码器支持
        for encoder in self.available_encoders:
            capabilities["encoder_support"][encoder.value] = self._test_encoder_support(encoder)

        return capabilities

    def render_video(self, input_path: str, output_path: str,
                      config: EncodingConfig, metadata: Optional[Dict[str, Any]] = None) -> str:
        """渲染视频"""
        task_id = f"render_{int(time.time() * 1000)}_{os.path.basename(input_path)}"

        task = RenderTask(
            task_id=task_id,
            input_path=input_path,
            output_path=output_path,
            start_time=time.time(),
            end_time=0.0,
            config=config,
            metadata=metadata or {}
        )

        self.active_tasks[task_id] = task

        # 发布任务开始事件
        self.event_bus.publish("gpu.render.started", {
            "task_id": task_id,
            "input_path": input_path,
            "encoder": config.encoder.value
        })

        # 异步执行渲染
        try:
            success = self._execute_render(task)
            if success:
                self.event_bus.publish("gpu.render.completed", {
                    "task_id": task_id,
                    "output_path": output_path,
                    "render_time": task.end_time - task.start_time
                })
            else:
                self.event_bus.publish("gpu.render.failed", {
                    "task_id": task_id,
                    "error": "Render execution failed"
                })
        except Exception as e:
            self.logger.error(f"GPU render failed for {task_id}: {e}")
            self.event_bus.publish("gpu.render.error", {
                "task_id": task_id,
                "error": str(e)
            })

        finally:
            # 清理任务
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

        return task_id

    def cancel_render(self, task_id: str) -> bool:
        """取消渲染任务"""
        if task_id not in self.active_tasks:
            return False

        task = self.active_tasks[task_id]
        task.end_time = time.time()

        # 发布取消事件
        self.event_bus.publish("gpu.render.cancelled", {
            "task_id": task_id,
            "cancelled_at": task.end_time
        })

        # 取消FFmpeg进程
        if hasattr(task, 'ffmpeg_process') and task.ffmpeg_process:
            task.ffmpeg_process.terminate()

        return True

    def get_render_progress(self, task_id: str) -> Dict[str, Any]:
        """获取渲染进度"""
        if task_id not in self.active_tasks:
            return {"status": "not_found"}

        task = self.active_tasks[task_id]
        elapsed = time.time() - task.start_time

        # 估算进度（简单实现）
        if task.end_time > 0:
            progress = 100.0
        else:
            # 基于时间估算
            estimated_duration = self._estimate_render_duration(task)
            progress = min(100.0, (elapsed / estimated_duration) * 100)

        return {
            "task_id": task_id,
            "status": "completed" if task.end_time > 0 else "running",
            "progress": progress,
            "elapsed_time": elapsed,
            "estimated_duration": self._estimate_render_duration(task)
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            **self.stats,
            "gpu_utilization": self._get_gpu_utilization(),
            "active_tasks": len(self.active_tasks),
            "supported_formats": self._get_supported_formats()
        }

    # 私有方法

    def _detect_gpu(self) -> GPUType:
        """检测GPU类型"""
        try:
            # 检测NVIDIA GPU
            if self._check_command("nvidia-smi"):
                self.logger.info("NVIDIA GPU detected")
                return GPUType.NVIDIA

            # 检测AMD GPU
            if self._check_command("rocm-smi"):
                self.logger.info("AMD GPU detected")
                return GPUType.AMD

            # 检测Intel GPU
            if self._check_command("intel_gpu_top"):
                self.logger.info("Intel GPU detected")
                return GPUType.INTEL

            # 检测Apple Silicon
            if sys.platform == "darwin" and self._check_command("sysctl -n machdep.cpu.brand_string"):
                brand = subprocess.getoutput("sysctl -n machdep.cpu.brand_string").strip()
                if "Apple" in brand:
                    self.logger.info("Apple Silicon detected")
                    return GPUType.APPLE

        except Exception as e:
            self.logger.warning(f"GPU detection failed: {e}")

        return GPUType.NONE

    def _get_available_encoders(self) -> List[EncoderType]:
        """获取可用的编码器"""
        encoders = []

        if self.gpu_type != GPUType.NONE:
            encoders.extend([EncoderType.H264])
            if self.gpu_type in [GPUType.NVIDIA, GPUType.APPLE, GPUType.INTEL]:
                encoders.append(EncoderType.HEVC)

        # 始终添加软件编码器作为备选
        encoders.extend([EncoderType.H264])

        return encoders

    def _find_ffmpeg(self) -> str:
        """查找FFmpeg路径"""
        ffmpeg_paths = [
            "ffmpeg",
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg"
        ]

        for path in ffmpeg_paths:
            if self._check_command(f"{path} -version"):
                return path

        raise RuntimeError("FFmpeg not found. Please install FFmpeg.")

    def _initialize_ffmpeg(self) -> None:
        """初始化FFmpeg"""
        try:
            # 验证FFmpeg版本
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.logger.info(f"FFmpeg found: {self.ffmpeg_path}")

                # 解析版本信息
                for line in result.stdout.split('\n'):
                    if 'ffmpeg version' in line:
                        self.logger.info(f"FFmpeg version: {line.strip()}")
                        break
            else:
                raise RuntimeError("FFmpeg validation failed")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize FFmpeg: {e}")

    def _execute_render(self, task: RenderTask) -> bool:
        """执行渲染任务"""
        try:
            # 构建FFmpeg命令
            cmd = self._build_ffmpeg_command(task)

            # 启动FFmpeg进程
            task.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 监控进程
            return self._monitor_ffmpeg_process(task)

        except Exception as e:
            self.logger.error(f"Failed to execute render: {e}")
            return False

    def _build_ffmpeg_command(self, task: RenderTask) -> List[str]:
        """构建FFmpeg命令"""
        cmd = [self.ffmpeg_path]

        # 输入文件
        cmd.extend(["-i", task.input_path])

        # 硬件加速
        if self.gpu_type != GPUType.NONE:
            if self.gpu_type == GPUType.NVIDIA:
                cmd.extend(["-c:v", "h264_nvenc"])
                cmd.extend(["-rc:v", "constqp"])
            elif self.gpu_type == GPUType.AMD:
                cmd.extend(["-c:v", "h264_amf"])
                cmd.extend(["-rc", "constqp"])
            elif self.gpu_type == GPUType.INTEL:
                cmd.extend(["-c:v", "h264_qsv"])
            elif self.gpu_type == GPUType.APPLE:
                cmd.extend(["-c:v", "h264_videotoolbox"])
                cmd.extend(["-allow_sw", "1"])

        # 编码参数
        if task.config.preset:
            cmd.extend(["-preset", task.config.preset])
        if task.config.crf is not None:
            cmd.extend(["-crf", str(task.config.crf)])
        if task.config.bitrate:
            cmd.extend(["-b:v", str(task.config.bitrate)])
        if task.config.keyframe_interval:
            cmd.extend(["-g", str(task.config.keyframe_interval)])
        if task.config.pixel_format:
            cmd.extend(["-pix_fmt", task.config.pixel_format])
        if task.config.threads > 0:
            cmd.extend(["-threads", str(task.config.threads)])

        # 音频参数（保持原样）
        cmd.extend(["-c:a", "copy"])

        # 输出文件
        cmd.extend(["-y", task.output_path])

        return cmd

    def _monitor_ffmpeg_process(self, task: RenderTask) -> bool:
        """监控FFmpeg进程"""
        try:
            stdout, stderr = task.ffmpeg_process.communicate()

            task.end_time = time.time()
            render_time = task.end_time - task.start_time

            # 更新统计
            self.stats["total_renders"] += 1
            self.stats["total_render_time"] += render_time

            if task.ffmpeg_process.returncode == 0:
                self.stats["successful_renders"] += 1
                self.logger.info(f"Render completed: {task.task_id} in {render_time:.2f}s")
                return True
            else:
                self.stats["failed_renders"] += 1
                self.logger.error(f"Render failed: {task.task_id}")
                if stderr:
                    self.logger.error(f"FFmpeg stderr: {stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to monitor FFmpeg process: {e}")
            return False

    def _estimate_render_duration(self, task: RenderTask) -> float:
        """估算渲染时间"""
        try:
            # 获取视频信息
            result = subprocess.run(
                [self.ffmpeg_path, "-i", task.input_path, "-f", "null"],
                capture_output=True,
                timeout=30
            )

            if result.returncode != 0:
                return 60.0  # 默认估算

            # 解析视频信息
            duration = 0
            for line in result.stderr.split('\n'):
                if "Duration:" in line:
                    time_str = line.split("Duration:")[1].split(",")[0]
                    h, m, s = map(float, time_str.split(":"))
                    duration = h * 3600 + m * 60 + s
                    break

            # 基于视频长度估算渲染时间
            if duration > 0:
                # 假设实时渲染需要1.5倍的视频时长
                return duration * 1.5

        except Exception as e:
            self.logger.warning(f"Failed to estimate render duration: {e}")

        return 60.0

    def _get_gpu_utilization(self) -> float:
        """获取GPU利用率"""
        try:
            if self.gpu_type == GPUType.NVIDIA:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return float(result.stdout.strip())

        except Exception:
            pass

        return 0.0

    def _get_supported_formats(self) -> List[str]:
        """获取支持的格式"""
        formats = ["mp4", "avi", "mov", "mkv", "webm", "flv"]

        # 根据GPU能力添加格式
        if self.gpu_type != GPUType.NONE:
            formats.extend(["h264", "hevc", "av1"])

        return formats

    def _test_encoder_support(self, encoder: EncoderType) -> bool:
        """测试编码器支持"""
        try:
            cmd = [self.ffmpeg_path, "-hide_banner", "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=30"]

            if encoder == EncoderType.H264:
                if self.gpu_type == GPUType.NVIDIA:
                    cmd.extend(["-c:v", "h264_nvenc", "-f", "null", "-"])
                elif self.gpu_type == GPUType.APPLE:
                    cmd.extend(["-c:v", "h264_videotoolbox", "-allow_sw", "1", "-f", "null", "-"])
                else:
                    cmd.extend(["-c:v", "libx264", "-f", "null", "-"])
            elif encoder == EncoderType.HEVC:
                if self.gpu_type == GPUType.NVIDIA:
                    cmd.extend(["-c:v", "hevc_nvenc", "-f", "null", "-"])
                elif self.gpu_type == GPUType.APPLE:
                    cmd.extend(["-c:v", "hevc_videotoolbox", "-allow_sw", "1", "-f", "null", "-"])
                else:
                    return False  # HEVC通常需要硬件支持

            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0

        except Exception:
            return False

    def _check_command(self, command: str) -> bool:
        """检查命令是否可用"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


# 全局GPU渲染器（需要在服务系统初始化后设置）
_gpu_renderer = None


def get_gpu_renderer() -> GPURenderer:
    """获取全局GPU渲染器"""
    global _gpu_renderer
    if _gpu_renderer is None:
        raise RuntimeError("GPU renderer not initialized")
    return _gpu_renderer


def set_gpu_renderer(renderer: GPURenderer) -> None:
    """设置全局GPU渲染器"""
    global _gpu_renderer
    _gpu_renderer = renderer


def create_gpu_config(encoder: str = "h264", preset: str = "medium",
                     crf: int = 23, quality: str = "medium") -> EncodingConfig:
    """创建GPU编码配置"""
    return EncodingConfig(
        encoder=EncoderType(encoder),
        preset=preset,
        crf=crf,
        bitrate=None if quality == "medium" else 5000000 if quality == "high" else 1000000
    )