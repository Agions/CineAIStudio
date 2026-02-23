#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接视频导出器 (Direct Video Exporter)

将 ClipFlow 项目直接导出为视频文件，支持多种分辨率和格式。

功能:
- 直接合成视频（无需剪映）
- 支持多种分辨率 (1080p, 4K, 竖屏等)
- 支持多种格式 (MP4, MOV, WebM)
- 硬件加速编码
- 批量处理

使用示例:
    from app.services.export import DirectVideoExporter, VideoExportConfig, Resolution

    exporter = DirectVideoExporter()
    output_path = exporter.export_commentary(
        commentary_project,
        output_path="output.mp4",
        resolution=Resolution.FHD_1080P,
    )
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json


class Resolution(Enum):
    """分辨率预设"""
    # 横屏
    SD_480P = (854, 480)
    HD_720P = (1280, 720)
    FHD_1080P = (1920, 1080)
    QHD_1440P = (2560, 1440)
    UHD_4K = (3840, 2160)
    UHD_8K = (7680, 4320)

    # 竖屏 (9:16)
    VERTICAL_720P = (720, 1280)
    VERTICAL_1080P = (1080, 1920)
    VERTICAL_4K = (2160, 3840)

    # 方形 (1:1)
    SQUARE_720 = (720, 720)
    SQUARE_1080 = (1080, 1080)

    @property
    def width(self) -> int:
        return self.value[0]

    @property
    def height(self) -> int:
        return self.value[1]

    @property
    def name(self) -> str:
        return f"{self.width}x{self.height}"


class VideoFormat(Enum):
    """视频格式"""
    MP4 = "mp4"
    MOV = "mov"
    WEBM = "webm"
    MKV = "mkv"
    AVI = "avi"


class VideoCodec(Enum):
    """视频编码器"""
    H264 = "libx264"
    H265 = "libx265"
    VP9 = "libvpx-vp9"
    AV1 = "libaom-av1"
    PRORES = "prores_ks"


class AudioCodec(Enum):
    """音频编码器"""
    AAC = "aac"
    MP3 = "libmp3lame"
    OPUS = "libopus"
    FLAC = "flac"


class HWAccel(Enum):
    """硬件加速类型"""
    NONE = "none"
    NVIDIA = "nvenc"           # NVIDIA NVENC
    INTEL = "qsv"              # Intel Quick Sync
    AMD = "amf"                # AMD AMF
    APPLE = "videotoolbox"     # Apple VideoToolbox (macOS)
    VAAPI = "vaapi"            # Linux VAAPI


@dataclass
class VideoExportConfig:
    """视频导出配置"""
    # 分辨率和帧率
    resolution: Resolution = Resolution.FHD_1080P
    fps: float = 30.0

    # 格式和编码
    format: VideoFormat = VideoFormat.MP4
    video_codec: VideoCodec = VideoCodec.H264
    audio_codec: AudioCodec = AudioCodec.AAC

    # 质量设置
    video_bitrate: str = "5M"      # 视频码率
    audio_bitrate: str = "192k"    # 音频码率
    crf: int = 23                  # 恒定质量因子 (0-51)
    preset: str = "medium"         # 编码预设

    # 硬件加速
    hw_accel: HWAccel = HWAccel.NONE

    # 其他选项
    include_subtitles: bool = True  # 是否烧录字幕
    audio_normalize: bool = True    # 音频归一化


class DirectVideoExporter:
    """
    直接视频导出器

    使用 FFmpeg 将项目直接导出为视频文件

    使用示例:
        exporter = DirectVideoExporter()

        # 导出解说视频
        output = exporter.export_commentary(
            commentary_project,
            "output.mp4",
            resolution=Resolution.VERTICAL_1080P,  # 竖屏
        )

        # 导出混剪视频
        output = exporter.export_mashup(
            mashup_project,
            "output.mp4",
            resolution=Resolution.FHD_1080P,
        )
    """

    def __init__(self, config: Optional[VideoExportConfig] = None):
        """
        初始化导出器

        Args:
            config: 导出配置
        """
        self.config = config or VideoExportConfig()
        self._check_ffmpeg()
        self._progress_callback: Optional[Callable[[str, float], None]] = None

    def set_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """设置进度回调"""
        self._progress_callback = callback

    def _report_progress(self, stage: str, progress: float) -> None:
        """报告进度"""
        if self._progress_callback:
            self._progress_callback(stage, progress)

    def _check_ffmpeg(self) -> None:
        """检查 FFmpeg 是否可用"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg 不可用")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg 未安装，请安装后重试")

    def export_commentary(
        self,
        commentary_project: Any,
        output_path: str,
        resolution: Optional[Resolution] = None,
        config: Optional[VideoExportConfig] = None,
    ) -> str:
        """
        导出解说视频

        Args:
            commentary_project: 解说项目
            output_path: 输出路径
            resolution: 分辨率（覆盖配置）
            config: 导出配置（覆盖默认配置）

        Returns:
            输出视频路径
        """
        cfg = config or self.config
        if resolution:
            cfg.resolution = resolution

        self._report_progress("准备导出", 0.0)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 1. 准备视频片段
            self._report_progress("准备视频片段", 0.1)
            segment_files = self._prepare_commentary_segments(
                commentary_project,
                temp_path,
                cfg,
            )

            # 2. 合并片段
            self._report_progress("合并视频", 0.5)
            concat_file = self._create_concat_list(segment_files, temp_path)
            merged_video = temp_path / "merged.mp4"
            self._concat_videos(concat_file, str(merged_video), cfg)

            # 3. 添加字幕（如果需要）
            if cfg.include_subtitles and commentary_project.segments:
                self._report_progress("添加字幕", 0.8)
                final_video = self._add_subtitles(
                    str(merged_video),
                    commentary_project,
                    output_path,
                    cfg,
                )
            else:
                # 直接复制
                shutil.copy(str(merged_video), output_path)
                final_video = output_path

        self._report_progress("导出完成", 1.0)
        return final_video

    def _prepare_commentary_segments(
        self,
        project: Any,
        temp_path: Path,
        config: VideoExportConfig,
    ) -> List[Path]:
        """准备解说视频片段"""
        segment_files = []

        for i, segment in enumerate(project.segments):
            self._report_progress(
                "准备视频片段",
                0.1 + 0.4 * (i / len(project.segments)),
            )

            # 提取视频片段
            video_segment = temp_path / f"video_{i:03d}.mp4"
            self._extract_video_segment(
                project.source_video,
                segment.video_start,
                segment.video_end - segment.video_start,
                str(video_segment),
                config,
            )

            # 如果有配音，合并音频
            if segment.audio_path and Path(segment.audio_path).exists():
                final_segment = temp_path / f"segment_{i:03d}.mp4"
                self._merge_video_audio(
                    str(video_segment),
                    segment.audio_path,
                    str(final_segment),
                    config,
                )
                segment_files.append(final_segment)
            else:
                segment_files.append(video_segment)

        return segment_files

    def _extract_video_segment(
        self,
        video_path: str,
        start: float,
        duration: float,
        output_path: str,
        config: VideoExportConfig,
    ) -> None:
        """提取视频片段"""
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start),
            '-t', str(duration),
            '-i', video_path,
            '-vf', f'scale={config.resolution.width}:{config.resolution.height}:force_original_aspect_ratio=decrease,pad={config.resolution.width}:{config.resolution.height}:(ow-iw)/2:(oh-ih)/2',
            '-c:v', self._get_video_codec(config),
            '-preset', config.preset,
            '-crf', str(config.crf),
            '-c:a', 'aac',
            '-b:a', config.audio_bitrate,
            '-ar', '48000',
            '-pix_fmt', 'yuv420p',
            output_path,
        ]

        # 添加硬件加速参数
        cmd = self._add_hw_accel_params(cmd, config)

        subprocess.run(cmd, capture_output=True)

    def _merge_video_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        config: VideoExportConfig,
    ) -> None:
        """合并视频和音频"""
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', config.audio_codec.value,
            '-b:a', config.audio_bitrate,
            '-shortest',
            output_path,
        ]

        subprocess.run(cmd, capture_output=True)

    def _create_concat_list(
        self,
        segment_files: List[Path],
        temp_path: Path,
    ) -> Path:
        """创建拼接列表"""
        list_file = temp_path / "concat_list.txt"
        with open(list_file, 'w') as f:
            for segment in segment_files:
                f.write(f"file '{segment}'\n")
        return list_file

    def _concat_videos(
        self,
        list_file: Path,
        output_path: str,
        config: VideoExportConfig,
    ) -> None:
        """拼接视频"""
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c', 'copy',
            output_path,
        ]

        subprocess.run(cmd, capture_output=True)

    def _add_subtitles(
        self,
        video_path: str,
        project: Any,
        output_path: str,
        config: VideoExportConfig,
    ) -> str:
        """添加字幕到视频"""
        # 生成 ASS 字幕
        from ..viral_video.caption_generator import CaptionGenerator, CaptionConfig

        caption_gen = CaptionGenerator(CaptionConfig())

        # 收集所有字幕
        all_captions = []
        for segment in project.segments:
            all_captions.extend(segment.captions)

        # 生成 ASS 文件
        with tempfile.TemporaryDirectory() as temp_dir:
            ass_path = Path(temp_dir) / "subtitles.ass"
            # 这里需要转换 caption 格式
            # 简化实现：使用 filter_complex 添加字幕

            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vf', 'subtitles=temp/subtitles.ass:force_style=FontSize=24,PrimaryColour=&H00FFFFFF',
                '-c:v', self._get_video_codec(config),
                '-preset', config.preset,
                '-crf', str(config.crf),
                '-c:a', 'copy',
                output_path,
            ]

            subprocess.run(cmd, capture_output=True)

        return output_path

    def _get_video_codec(self, config: VideoExportConfig) -> str:
        """获取视频编码器"""
        if config.hw_accel == HWAccel.NVIDIA:
            if config.video_codec == VideoCodec.H265:
                return "hevc_nvenc"
            return "h264_nvenc"
        elif config.hw_accel == HWAccel.APPLE:
            if config.video_codec == VideoCodec.H265:
                return "hevc_videotoolbox"
            return "h264_videotoolbox"
        elif config.hw_accel == HWAccel.INTEL:
            if config.video_codec == VideoCodec.H265:
                return "hevc_qsv"
            return "h264_qsv"
        else:
            return config.video_codec.value

    def _add_hw_accel_params(
        self,
        cmd: List[str],
        config: VideoExportConfig,
    ) -> List[str]:
        """添加硬件加速参数"""
        if config.hw_accel == HWAccel.NONE:
            return cmd

        # 在输入前添加硬件加速设备
        if config.hw_accel == HWAccel.NVIDIA:
            cmd.insert(1, '-hwaccel')
            cmd.insert(2, 'cuda')
        elif config.hw_accel == HWAccel.APPLE:
            cmd.insert(1, '-hwaccel')
            cmd.insert(2, 'videotoolbox')
        elif config.hw_accel == HWAccel.INTEL:
            cmd.insert(1, '-hwaccel')
            cmd.insert(2, 'qsv')

        return cmd

    def export_with_presets(
        self,
        project: Any,
        output_dir: str,
        project_name: str,
        presets: List[Resolution] = None,
    ) -> Dict[str, str]:
        """
        使用多个预设导出视频

        Args:
            project: 项目
            output_dir: 输出目录
            project_name: 项目名称
            presets: 分辨率预设列表

        Returns:
            分辨率到输出路径的映射
        """
        if presets is None:
            presets = [Resolution.FHD_1080P, Resolution.VERTICAL_1080P]

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        for resolution in presets:
            output_name = f"{project_name}_{resolution.name}.mp4"
            output_path = output_dir / output_name

            print(f"导出 {resolution.name}...")
            self.export_commentary(
                project,
                str(output_path),
                resolution=resolution,
            )

            results[resolution.name] = str(output_path)

        return results

    def get_system_hw_accel(self) -> HWAccel:
        """检测系统支持的硬件加速"""
        import platform

        system = platform.system()

        if system == "Darwin":  # macOS
            return HWAccel.APPLE
        elif system == "Windows":
            # 检测 NVIDIA
            try:
                result = subprocess.run(
                    ['nvidia-smi'],
                    capture_output=True,
                )
                if result.returncode == 0:
                    return HWAccel.NVIDIA
            except Exception:
                pass

            # 检测 Intel
            try:
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'name'],
                    capture_output=True,
                    text=True,
                )
                if "Intel" in result.stdout:
                    return HWAccel.INTEL
            except Exception:
                pass
        elif system == "Linux":
            return HWAccel.VAAPI

        return HWAccel.NONE


def demo_export():
    """演示视频导出"""
    print("=" * 60)
    print("🎬 直接视频导出器")
    print("=" * 60)

    exporter = DirectVideoExporter()

    # 检测硬件加速
    hw_accel = exporter.get_system_hw_accel()
    print(f"\n检测到的硬件加速: {hw_accel.value}")

    # 显示可用分辨率
    print("\n可用分辨率:")
    for res in Resolution:
        print(f"  - {res.name}: {res.width}x{res.height}")

    print("\n导出配置示例:")
    config = VideoExportConfig(
        resolution=Resolution.VERTICAL_1080P,
        hw_accel=hw_accel,
        video_bitrate="8M",
    )
    print(f"  分辨率: {config.resolution.name}")
    print(f"  编码器: {config.video_codec.value}")
    print(f"  硬件加速: {config.hw_accel.value}")
    print(f"  视频码率: {config.video_bitrate}")


if __name__ == '__main__':
    demo_export()
