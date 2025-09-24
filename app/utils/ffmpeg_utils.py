#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 FFmpeg Utilities Module
提供专业的FFmpeg封装工具，支持硬件加速、4K视频处理和多格式支持
"""

import os
import subprocess
import json
import logging
import re
import shutil
import tempfile
import threading
import time
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Empty

from ..core.logger import get_logger
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler


class HWAccelerationType(Enum):
    """硬件加速类型枚举"""
    NONE = "none"
    NVIDIA = "nvidia"  # NVIDIA NVDEC/NVENC
    AMD = "amd"  # AMD AMF
    INTEL = "intel"  # Intel Quick Sync
    APPLE = "apple"  # Apple VideoToolbox
    VAAPI = "vaapi"  # VAAPI (Linux)
    CUDA = "cuda"  # CUDA
    OPENCL = "opencl"  # OpenCL


class VideoCodec(Enum):
    """视频编解码器枚举"""
    H264 = "h264"
    H265 = "hevc"
    VP9 = "vp9"
    AV1 = "av1"
    PRORES = "prores"
    DNxHD = "dnxhd"
    RAW = "raw"


class AudioCodec(Enum):
    """音频编解码器枚举"""
    AAC = "aac"
    MP3 = "mp3"
    OPUS = "opus"
    FLAC = "flac"
    PCM = "pcm"
    AC3 = "ac3"
    EAC3 = "eac3"


class ContainerFormat(Enum):
    """容器格式枚举"""
    MP4 = "mp4"
    MOV = "mov"
    MKV = "mkv"
    AVI = "avi"
    WEBM = "webm"
    M4V = "m4v"
    MXF = "mxf"


@dataclass
class VideoInfo:
    """视频信息数据类"""
    path: str
    duration: float  # 秒
    width: int
    height: int
    fps: float
    bitrate: int  # bps
    codec: str
    audio_codec: str
    audio_bitrate: int
    audio_channels: int
    file_size: int  # bytes
    has_video: bool = True
    has_audio: bool = True
    is_4k: bool = False
    is_hdr: bool = False

    def __post_init__(self):
        """后处理计算"""
        self.is_4k = self.width >= 3840 and self.height >= 2160


@dataclass
class FFmpegCommand:
    """FFmpeg命令数据类"""
    command: List[str]
    description: str
    timeout: int = 3600  # 默认1小时超时
    expected_duration: Optional[float] = None
    progress_callback: Optional[Callable[[float], None]] = None
    output_path: Optional[str] = None


class FFmpegUtils:
    """FFmpeg工具类"""

    def __init__(self, logger=None):
        """初始化FFmpeg工具"""
        self.logger = logger or get_logger("FFmpegUtils")
        self.error_handler = get_global_error_handler()
        self.ffmpeg_path = self._find_ffmpeg_executable()
        self.ffprobe_path = self._find_ffprobe_executable()
        self.hw_acceleration = self._detect_hardware_acceleration()
        self.supported_frameworks = ["videotoolbox"] if self.hw_acceleration == HWAccelerationType.APPLE else []
        self.temp_dir = tempfile.mkdtemp(prefix="cineaistudio_ffmpeg_")
        self.command_queue = Queue()
        self.processing_thread = None
        self.is_processing = False
        self._start_processing_thread()

    def _find_ffmpeg_executable(self) -> str:
        """查找FFmpeg可执行文件"""
        possible_paths = [
            "ffmpeg",
            "ffmpeg.exe",
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",
            "/usr/bin/ffmpeg",
            os.path.join(os.path.dirname(__file__), "..", "bin", "ffmpeg")
        ]

        for path in possible_paths:
            try:
                result = subprocess.run([path, "-version"],
                                       capture_output=True,
                                       timeout=10,
                                       text=True)
                if result.returncode == 0:
                    self.logger.info(f"找到FFmpeg: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        raise RuntimeError("未找到FFmpeg可执行文件")

    def _find_ffprobe_executable(self) -> str:
        """查找FFprobe可执行文件"""
        possible_paths = [
            "ffprobe",
            "ffprobe.exe",
            "/usr/local/bin/ffprobe",
            "/opt/homebrew/bin/ffprobe",
            "/usr/bin/ffprobe",
            os.path.join(os.path.dirname(__file__), "..", "bin", "ffprobe")
        ]

        for path in possible_paths:
            try:
                result = subprocess.run([path, "-version"],
                                       capture_output=True,
                                       timeout=10,
                                       text=True)
                if result.returncode == 0:
                    self.logger.info(f"找到FFprobe: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        raise RuntimeError("未找到FFprobe可执行文件")

    def _detect_hardware_acceleration(self) -> HWAccelerationType:
        """检测可用的硬件加速"""
        # 检查NVIDIA GPU
        try:
            result = subprocess.run(["nvidia-smi"],
                                  capture_output=True,
                                  timeout=5,
                                  text=True)
            if result.returncode == 0:
                self.logger.info("检测到NVIDIA GPU，启用NVDEC/NVENC硬件加速")
                return HWAccelerationType.NVIDIA
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # 检查Apple Silicon
        if os.uname().sysname == "Darwin":
            try:
                result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                      capture_output=True,
                                      timeout=5,
                                      text=True)
                if "Apple" in result.stdout or "M1" in result.stdout or "M2" in result.stdout:
                    self.logger.info("检测到Apple Silicon，启用VideoToolbox硬件加速")
                    return HWAccelerationType.APPLE
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        # 检查Intel Quick Sync
        try:
            result = subprocess.run(["vainfo"],
                                  capture_output=True,
                                  timeout=5,
                                  text=True)
            if result.returncode == 0:
                self.logger.info("检测到Intel GPU，启用Quick Sync硬件加速")
                return HWAccelerationType.INTEL
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        self.logger.info("未检测到硬件加速，使用软件解码")
        return HWAccelerationType.NONE

    def get_video_info(self, video_path: str) -> VideoInfo:
        """获取视频信息"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        try:
            # 使用ffprobe获取视频信息
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=30, text=True)

            if result.returncode != 0:
                raise RuntimeError(f"FFprobe执行失败: {result.stderr}")

            data = json.loads(result.stdout)

            # 提取视频流信息
            video_stream = None
            audio_stream = None

            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                elif stream.get("codec_type") == "audio":
                    audio_stream = stream

            # 解析视频信息
            if video_stream:
                duration = float(video_stream.get("duration", data["format"].get("duration", 0)))
                width = int(video_stream.get("width", 0))
                height = int(video_stream.get("height", 0))
                fps = eval(video_stream.get("r_frame_rate", "30/1"))
                bitrate = int(video_stream.get("bit_rate", data["format"].get("bit_rate", 0)))
                codec = video_stream.get("codec_name", "unknown")
            else:
                duration = float(data["format"].get("duration", 0))
                width = height = fps = bitrate = 0
                codec = "unknown"

            # 解析音频信息
            if audio_stream:
                audio_codec = audio_stream.get("codec_name", "unknown")
                audio_bitrate = int(audio_stream.get("bit_rate", 0))
                audio_channels = int(audio_stream.get("channels", 0))
            else:
                audio_codec = "unknown"
                audio_bitrate = 0
                audio_channels = 0

            file_size = int(data["format"].get("size", 0))

            video_info = VideoInfo(
                path=video_path,
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                bitrate=bitrate,
                codec=codec,
                audio_codec=audio_codec,
                audio_bitrate=audio_bitrate,
                audio_channels=audio_channels,
                file_size=file_size,
                has_video=video_stream is not None,
                has_audio=audio_stream is not None
            )

            self.logger.info(f"视频信息获取成功: {video_info.width}x{video_info.height} @ {video_info.fps}fps")
            return video_info

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.HIGH,
                message=f"获取视频信息失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="FFmpegUtils",
                    operation="get_video_info"
                ),
                user_message="无法读取视频文件信息"
            )
            self.error_handler.handle_error(error_info)
            raise

    def get_hw_acceleration_params(self) -> List[str]:
        """获取硬件加速参数"""
        if self.hw_acceleration == HWAccelerationType.NVIDIA:
            return ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
        elif self.hw_acceleration == HWAccelerationType.APPLE:
            return ["-hwaccel", "videotoolbox", "-hwaccel_output_format", "videotoolbox"]
        elif self.hw_acceleration == HWAccelerationType.INTEL:
            return ["-hwaccel", "qsv", "-hwaccel_output_format", "qsv"]
        elif self.hw_acceleration == HWAccelerationType.AMD:
            return ["-hwaccel", "amf", "-hwaccel_output_format", "amf"]
        elif self.hw_acceleration == HWAccelerationType.VAAPI:
            return ["-hwaccel", "vaapi", "-hwaccel_output_format", "vaapi"]
        else:
            return []

    def get_encoding_params(self, codec: VideoCodec, quality: str = "medium") -> List[str]:
        """获取编码参数"""
        params = []

        if codec == VideoCodec.H264:
            if self.hw_acceleration == HWAccelerationType.NVIDIA:
                params.extend(["-c:v", "h264_nvenc"])
            elif self.hw_acceleration == HWAccelerationType.APPLE:
                params.extend(["-c:v", "h264_videotoolbox"])
            elif self.hw_acceleration == HWAccelerationType.INTEL:
                params.extend(["-c:v", "h264_qsv"])
            elif self.hw_acceleration == HWAccelerationType.AMD:
                params.extend(["-c:v", "h264_amf"])
            else:
                params.extend(["-c:v", "libx264"])

            # 质量参数
            quality_params = {
                "high": ["-crf", "18", "-preset", "slow"],
                "medium": ["-crf", "23", "-preset", "medium"],
                "low": ["-crf", "28", "-preset", "fast"]
            }
            params.extend(quality_params.get(quality, quality_params["medium"]))

        elif codec == VideoCodec.H265:
            if self.hw_acceleration == HWAccelerationType.NVIDIA:
                params.extend(["-c:v", "hevc_nvenc"])
            elif self.hw_acceleration == HWAccelerationType.APPLE:
                params.extend(["-c:v", "hevc_videotoolbox"])
            elif self.hw_acceleration == HWAccelerationType.INTEL:
                params.extend(["-c:v", "hevc_qsv"])
            elif self.hw_acceleration == HWAccelerationType.AMD:
                params.extend(["-c:v", "hevc_amf"])
            else:
                params.extend(["-c:v", "libx265"])

            quality_params = {
                "high": ["-crf", "20", "-preset", "slow"],
                "medium": ["-crf", "28", "-preset", "medium"],
                "low": ["-crf", "35", "-preset", "fast"]
            }
            params.extend(quality_params.get(quality, quality_params["medium"]))

        elif codec == VideoCodec.PRORES:
            params.extend(["-c:v", "prores_ks", "-profile:v", "standard"])

        elif codec == VideoCodec.DNxHD:
            params.extend(["-c:v", "dnxhd", "-profile:v", "dnxhr_hqx"])

        return params

    def create_thumbnail(self, video_path: str, output_path: str,
                        timestamp: float = 0.0, size: Tuple[int, int] = (320, 180)) -> str:
        """创建视频缩略图"""
        try:
            cmd = [
                self.ffmpeg_path,
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-s", f"{size[0]}x{size[1]}",
                "-q:v", "2",
                "-y",
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=30)

            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg执行失败: {result.stderr}")

            self.logger.info(f"缩略图创建成功: {output_path}")
            return output_path

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.MEDIUM,
                message=f"创建缩略图失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="FFmpegUtils",
                    operation="create_thumbnail"
                ),
                user_message="无法创建视频缩略图"
            )
            self.error_handler.handle_error(error_info)
            raise

    def extract_audio(self, video_path: str, output_path: str,
                    codec: AudioCodec = AudioCodec.AAC,
                    bitrate: int = 128000) -> str:
        """提取音频"""
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vn",  # 禁用视频
                "-c:a", codec.value,
                "-b:a", f"{bitrate}",
                "-y",
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=300)

            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg执行失败: {result.stderr}")

            self.logger.info(f"音频提取成功: {output_path}")
            return output_path

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.MEDIUM,
                message=f"音频提取失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="FFmpegUtils",
                    operation="extract_audio"
                ),
                user_message="无法提取音频"
            )
            self.error_handler.handle_error(error_info)
            raise

    def concat_videos(self, video_paths: List[str], output_path: str) -> str:
        """合并多个视频"""
        try:
            # 创建临时文件列表
            list_file = os.path.join(self.temp_dir, "concat_list.txt")
            with open(list_file, "w") as f:
                for path in video_paths:
                    f.write(f"file '{path}'\n")

            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                "-y",
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=600)

            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg执行失败: {result.stderr}")

            self.logger.info(f"视频合并成功: {output_path}")
            return output_path

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.MEDIA,
                severity=ErrorSeverity.HIGH,
                message=f"视频合并失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="FFmpegUtils",
                    operation="concat_videos"
                ),
                user_message="无法合并视频"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _start_processing_thread(self) -> None:
        """启动处理线程"""
        self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
        self.processing_thread.start()
        self.logger.info("FFmpeg处理线程已启动")

    def _processing_worker(self) -> None:
        """处理工作线程"""
        while True:
            try:
                ffmpeg_cmd = self.command_queue.get(timeout=1)
                self.is_processing = True
                try:
                    self._execute_ffmpeg_command(ffmpeg_cmd)
                except Exception as e:
                    self.logger.error(f"FFmpeg命令执行失败: {str(e)}")
                finally:
                    self.is_processing = False
                    self.command_queue.task_done()
            except Empty:
                continue

    def _execute_ffmpeg_command(self, ffmpeg_cmd: FFmpegCommand) -> None:
        """执行FFmpeg命令"""
        self.logger.info(f"执行FFmpeg命令: {ffmpeg_cmd.description}")

        try:
            # 启动进程
            process = subprocess.Popen(
                ffmpeg_cmd.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 监控进度
            if ffmpeg_cmd.progress_callback and ffmpeg_cmd.expected_duration:
                self._monitor_progress(process, ffmpeg_cmd)

            # 等待完成
            stdout, stderr = process.communicate(timeout=ffmpeg_cmd.timeout)

            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg执行失败: {stderr}")

            self.logger.info(f"FFmpeg命令执行成功: {ffmpeg_cmd.description}")

        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError(f"FFmpeg命令超时: {ffmpeg_cmd.description}")
        except Exception as e:
            raise

    def _monitor_progress(self, process: subprocess.Popen, ffmpeg_cmd: FFmpegCommand) -> None:
        """监控处理进度"""
        import re

        progress_pattern = r"time=(\d+):(\d+):(\d+)\.(\d+)"

        while process.poll() is None:
            try:
                line = process.stderr.readline()
                if not line:
                    continue

                match = re.search(progress_pattern, line)
                if match:
                    hours, minutes, seconds, milliseconds = match.groups()
                    current_time = (int(hours) * 3600 +
                                  int(minutes) * 60 +
                                  int(seconds) +
                                  int(milliseconds) / 1000)

                    progress = min(current_time / ffmpeg_cmd.expected_duration, 1.0)
                    ffmpeg_cmd.progress_callback(progress)

            except Exception as e:
                self.logger.warning(f"进度监控错误: {str(e)}")

    def add_to_queue(self, ffmpeg_cmd: FFmpegCommand) -> None:
        """添加命令到队列"""
        self.command_queue.put(ffmpeg_cmd)
        self.logger.info(f"FFmpeg命令已添加到队列: {ffmpeg_cmd.description}")

    def is_busy(self) -> bool:
        """检查是否正在处理"""
        return self.is_processing or not self.command_queue.empty()

    def wait_for_completion(self, timeout: Optional[float] = None) -> None:
        """等待所有任务完成"""
        self.command_queue.join()

    def cleanup(self) -> None:
        """清理临时文件"""
        try:
            shutil.rmtree(self.temp_dir)
            self.logger.info("临时文件清理完成")
        except Exception as e:
            self.logger.error(f"临时文件清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局FFmpeg工具实例
_ffmpeg_utils: Optional[FFmpegUtils] = None


def get_ffmpeg_utils() -> FFmpegUtils:
    """获取全局FFmpeg工具实例"""
    global _ffmpeg_utils
    if _ffmpeg_utils is None:
        _ffmpeg_utils = FFmpegUtils()
    return _ffmpeg_utils


def cleanup_ffmpeg_utils() -> None:
    """清理全局FFmpeg工具实例"""
    global _ffmpeg_utils
    if _ffmpeg_utils is not None:
        _ffmpeg_utils.cleanup()
        _ffmpeg_utils = None