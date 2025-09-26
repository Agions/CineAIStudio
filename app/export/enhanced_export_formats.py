#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强导出格式支持
扩展现有的导出格式，添加更多专业格式和现代编解码器支持
"""

import os
import json
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .export_system import ExportFormat, ExportQuality, ExportPreset
from ..core.logger import Logger


class EnhancedExportFormat(Enum):
    """增强导出格式枚举"""
    # 视频格式
    MP4_H264 = "mp4_h264"
    MP4_H265 = "mp4_h265"
    MP4_AV1 = "mp4_av1"
    MOV_PRORES = "mov_prores"
    MOV_PRORES_RAW = "mov_prores_raw"
    AVI_UNCOMPRESSED = "avi_uncompressed"
    MKV_H264 = "mkv_h264"
    MKV_H265 = "mkv_h265"
    WEBM_VP9 = "webm_vp9"
    WEBM_AV1 = "webm_av1"
    GIF_ANIMATED = "gif_animated"

    # 音频格式
    MP3_AUDIO = "mp3_audio"
    WAV_AUDIO = "wav_audio"
    FLAC_AUDIO = "flac_audio"
    AAC_AUDIO = "aac_audio"
    OPUS_AUDIO = "opus_audio"

    # 专业格式
    MXF_OP1A = "mxf_op1a"
    MXF_ATOM = "mxf_atom"
    DNXHD = "dnxhd"
    PRORES_LT = "prores_lt"
    PRORES_HQ = "prores_hq"
    PRORES_4444 = "prores_4444"
    PRORES_XQ = "prores_xq"

    # 流媒体格式
    HLS_STREAM = "hls_stream"
    DASH_STREAM = "dash_stream"
    RTMP_STREAM = "rtmp_stream"

    # 特殊格式
    JIANYING_DRAFT = "jianying_draft"
    FCPXML = "fcpxml"
    EDL = "edl"
    SRT = "srt"


class CodecProfile(Enum):
    """编解码器配置文件"""
    H264_BASELINE = "h264_baseline"
    H264_MAIN = "h264_main"
    H264_HIGH = "h264_high"
    H264_HIGH10 = "h264_high10"
    H264_HIGH422 = "h264_high422"
    H264_HIGH444 = "h264_high444"

    H265_MAIN = "h265_main"
    H265_MAIN10 = "h265_main10"
    H265_MAIN422 = "h265_main422"
    H265_MAIN444 = "h265_main444"

    AV1_MAIN = "av1_main"
    AV1_HIGH = "av1_high"
    AV1_PROFESSIONAL = "av1_professional"

    PRORES_PROXY = "prores_proxy"
    PRORES_LT = "prores_lt"
    PRORES_STANDARD = "prores_standard"
    PRORES_HQ = "prores_hq"
    PRORES_4444 = "prores_4444"
    PRORES_XQ = "prores_xq"


@dataclass
class FormatSpecification:
    """格式规格说明"""
    format: EnhancedExportFormat
    name: str
    description: str
    container: str
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    supported_profiles: List[CodecProfile] = field(default_factory=list)
    max_resolution: Tuple[int, int] = (7680, 4320)  # 8K
    max_bitrate: int = 1000000  # 1Gbps
    max_fps: float = 120.0
    supports_alpha: bool = False
    supports_hdr: bool = False
    is_lossless: bool = False
    is_professional: bool = False
    is_streaming: bool = False
    recommended_uses: List[str] = field(default_factory=list)


class EnhancedExportPresets:
    """增强导出预设"""

    @staticmethod
    def get_format_specifications() -> Dict[EnhancedExportFormat, FormatSpecification]:
        """获取格式规格说明"""
        return {
            EnhancedExportFormat.MP4_H264: FormatSpecification(
                format=EnhancedExportFormat.MP4_H264,
                name="MP4 H.264",
                description="广泛兼容的H.264编码MP4格式",
                container="mp4",
                video_codec="libx264",
                audio_codec="aac",
                supported_profiles=[
                    CodecProfile.H264_BASELINE,
                    CodecProfile.H264_MAIN,
                    CodecProfile.H264_HIGH,
                    CodecProfile.H264_HIGH10,
                    CodecProfile.H264_HIGH422,
                    CodecProfile.H264_HIGH444
                ],
                recommended_uses=["YouTube", "Vimeo", "社交媒体", "移动设备"]
            ),

            EnhancedExportFormat.MP4_H265: FormatSpecification(
                format=EnhancedExportFormat.MP4_H265,
                name="MP4 H.265",
                description="高效的H.265编码MP4格式",
                container="mp4",
                video_codec="libx265",
                audio_codec="aac",
                supported_profiles=[
                    CodecProfile.H265_MAIN,
                    CodecProfile.H265_MAIN10,
                    CodecProfile.H265_MAIN422,
                    CodecProfile.H265_MAIN444
                ],
                supports_hdr=True,
                recommended_uses=["4K视频", "HDR内容", "高压缩率需求"]
            ),

            EnhancedExportFormat.MP4_AV1: FormatSpecification(
                format=EnhancedExportFormat.MP4_AV1,
                name="MP4 AV1",
                description="现代AV1编码MP4格式",
                container="mp4",
                video_codec="libaom-av1",
                audio_codec="opus",
                supported_profiles=[
                    CodecProfile.AV1_MAIN,
                    CodecProfile.AV1_HIGH,
                    CodecProfile.AV1_PROFESSIONAL
                ],
                supports_hdr=True,
                recommended_uses=["Web视频", "流媒体", "未来兼容"]
            ),

            EnhancedExportFormat.MOV_PRORES: FormatSpecification(
                format=EnhancedExportFormat.MOV_PRORES,
                name="MOV ProRes",
                description="专业级ProRes编码",
                container="mov",
                video_codec="prores_ks",
                audio_codec="pcm_s24le",
                supported_profiles=[
                    CodecProfile.PRORES_PROXY,
                    CodecProfile.PRORES_LT,
                    CodecProfile.PRORES_STANDARD,
                    CodecProfile.PRORES_HQ,
                    CodecProfile.PRORES_4444,
                    CodecProfile.PRORES_XQ
                ],
                is_professional=True,
                recommended_uses=["后期制作", "广播", "专业编辑"]
            ),

            EnhancedExportFormat.WEBM_AV1: FormatSpecification(
                format=EnhancedExportFormat.WEBM_AV1,
                name="WebM AV1",
                description="WebM容器下的AV1编码",
                container="webm",
                video_codec="libaom-av1",
                audio_codec="libopus",
                supported_profiles=[CodecProfile.AV1_MAIN],
                recommended_uses=["Web播放", "流媒体", "开源项目"]
            ),

            EnhancedExportFormat.FLAC_AUDIO: FormatSpecification(
                format=EnhancedExportFormat.FLAC_AUDIO,
                name="FLAC Audio",
                description="无损音频压缩格式",
                container="flac",
                audio_codec="flac",
                is_lossless=True,
                recommended_uses=["音频存档", "音乐制作", "高保真音频"]
            ),

            EnhancedExportFormat.MXF_OP1A: FormatSpecification(
                format=EnhancedExportFormat.MXF_OP1A,
                name="MXF OP-1A",
                description="专业广播格式",
                container="mxf",
                video_codec="dnxhd",
                audio_codec="pcm_s24le",
                is_professional=True,
                recommended_uses=["广播", "专业制作", "归档"]
            ),

            EnhancedExportFormat.HLS_STREAM: FormatSpecification(
                format=EnhancedExportFormat.HLS_STREAM,
                name="HLS Stream",
                description="HTTP Live Streaming格式",
                container="mpegts",
                video_codec="libx264",
                audio_codec="aac",
                is_streaming=True,
                recommended_uses=["直播", "点播流媒体", "自适应码率"]
            ),

            EnhancedExportFormat.JIANYING_DRAFT: FormatSpecification(
                format=EnhancedExportFormat.JIANYING_DRAFT,
                name="剪映草稿",
                description="剪映草稿文件格式",
                container="json",
                recommended_uses=["剪映编辑", "草稿保存", "项目导出"]
            )
        }

    @staticmethod
    def get_enhanced_presets() -> List[ExportPreset]:
        """获取增强预设"""
        return [
            # 高质量预设
            ExportPreset(
                id="youtube_4k_hdr",
                name="YouTube 4K HDR",
                format=ExportFormat.MP4_H265,
                quality=ExportQuality.ULTRA,
                resolution=(3840, 2160),
                bitrate=45000,
                fps=30,
                audio_bitrate=320,
                codec_params={
                    "profile": "main10",
                    "pix_fmt": "yuv420p10le",
                    "colorspace": "bt2020",
                    "color_primaries": "bt2020",
                    "color_trc": "smpte2084"
                },
                description="适用于YouTube的4K HDR视频"
            ),

            ExportPreset(
                id="cinema_4k_dci",
                name="影院4K DCI",
                format=ExportFormat.MOV_PRORES,
                quality=ExportQuality.ULTRA,
                resolution=(4096, 2160),
                bitrate=50000,
                fps=24,
                audio_bitrate=320,
                codec_params={
                    "profile": "standard",
                    "vendor": "apco",
                    "bits_per_mb": 8000
                },
                description="适用于影院的4K DCI格式"
            ),

            ExportPreset(
                id="social_media_vertical",
                name="社交媒体竖版",
                format=ExportFormat.MP4_H264,
                quality=ExportQuality.MEDIUM,
                resolution=(1080, 1920),
                bitrate=8000,
                fps=30,
                audio_bitrate=128,
                codec_params={
                    "profile": "high",
                    "level": "4.0",
                    "movflags": "+faststart"
                },
                description="适用于Instagram Reels, TikTok等竖版视频"
            ),

            ExportPreset(
                id="web_streaming",
                name="Web流媒体",
                format=ExportFormat.WEBM_VP9,
                quality=ExportQuality.HIGH,
                resolution=(1920, 1080),
                bitrate=6000,
                fps=30,
                audio_bitrate=128,
                codec_params={
                    "deadline": "good",
                    "cpu-used": "2",
                    "row-mt": "1"
                },
                description="适用于Web播放的流媒体优化格式"
            ),

            ExportPreset(
                id="av1_high_quality",
                name="AV1高质量",
                format=ExportFormat.MP4_H264,  # 映射到现有格式
                quality=ExportQuality.HIGH,
                resolution=(1920, 1080),
                bitrate=4000,
                fps=30,
                audio_bitrate=128,
                codec_params={
                    "codec": "libaom-av1",
                    "cpu-used": "3",
                    "row-mt": "1"
                },
                description="使用AV1编码的高质量视频"
            ),

            ExportPreset(
                id="broadcast_1080i",
                name="广播1080i",
                format=ExportFormat.MOV_PRORES,
                quality=ExportQuality.HIGH,
                resolution=(1920, 1080),
                bitrate=22000,
                fps=29.97,  # 29.97fps for NTSC
                audio_bitrate=320,
                codec_params={
                    "profile": "standard",
                    "field_order": "tt"
                },
                description="适用于广播的1080i隔行扫描格式"
            ),

            ExportPreset(
                id="lossless_master",
                name="无损母版",
                format=ExportFormat.MOV_PRORES,
                quality=ExportQuality.ULTRA,
                resolution=(1920, 1080),
                bitrate=80000,
                fps=30,
                audio_bitrate=320,
                codec_params={
                    "profile": "4444",
                    "vendor": "apch",
                    "alpha_bits": "8"
                },
                supports_alpha=True,
                description="无损质量母版，支持Alpha通道"
            ),

            ExportPreset(
                id="podcast_audio",
                name="播客音频",
                format=ExportFormat.MP3_AUDIO,
                quality=ExportQuality.MEDIUM,
                resolution=(0, 0),
                bitrate=0,
                fps=0,
                audio_bitrate=128,
                codec_params={
                    "audio_codec": "libmp3lame",
                    "qscale": "2"
                },
                description="适用于播客的高质量音频"
            ),

            ExportPreset(
                id="music_master",
                name="音乐母版",
                format=ExportFormat.WAV_AUDIO,
                quality=ExportQuality.ULTRA,
                resolution=(0, 0),
                bitrate=0,
                fps=0,
                audio_bitrate=1411,  # 16-bit 44.1kHz PCM
                codec_params={
                    "audio_codec": "pcm_s16le",
                    "sample_rate": "44100",
                    "channels": "2"
                },
                is_lossless=True,
                description="音乐母版无损音频"
            ),

            ExportPreset(
                id="mobile_optimized",
                name="移动优化",
                format=ExportFormat.MP4_H264,
                quality=ExportQuality.MEDIUM,
                resolution=(1280, 720),
                bitrate=2500,
                fps=30,
                audio_bitrate=96,
                codec_params={
                    "profile": "baseline",
                    "level": "3.1",
                    "movflags": "+faststart"
                },
                description="针对移动设备优化的格式"
            )
        ]

    @staticmethod
    def get_codec_parameters(format_type: EnhancedExportFormat,
                            profile: Optional[CodecProfile] = None,
                            quality: ExportQuality = ExportQuality.HIGH) -> Dict[str, Any]:
        """获取编解码器参数"""
        params = {}

        if format_type == EnhancedExportFormat.MP4_H264:
            params.update({
                "c:v": "libx264",
                "preset": "medium",
                "crf": "23"
            })

            if profile:
                profile_map = {
                    CodecProfile.H264_BASELINE: "baseline",
                    CodecProfile.H264_MAIN: "main",
                    CodecProfile.H264_HIGH: "high",
                    CodecProfile.H264_HIGH10: "high10",
                    CodecProfile.H264_HIGH422: "high422",
                    CodecProfile.H264_HIGH444: "high444"
                }
                if profile in profile_map:
                    params["profile:v"] = profile_map[profile]

            # 根据质量调整CRF
            quality_crf = {
                ExportQuality.LOW: 28,
                ExportQuality.MEDIUM: 25,
                ExportQuality.HIGH: 23,
                ExportQuality.ULTRA: 20
            }
            params["crf"] = quality_crf.get(quality, 23)

        elif format_type == EnhancedExportFormat.MP4_H265:
            params.update({
                "c:v": "libx265",
                "preset": "medium",
                "crf": "28"
            })

            if profile == CodecProfile.H265_MAIN10:
                params["pix_fmt"] = "yuv420p10le"

        elif format_type == EnhancedExportFormat.MP4_AV1:
            params.update({
                "c:v": "libaom-av1",
                "cpu-used": "3",
                "row-mt": "1"
            })

        elif format_type in [EnhancedExportFormat.MOV_PRORES, EnhancedExportFormat.PRORES_LT,
                           EnhancedExportFormat.PRORES_HQ, EnhancedExportFormat.PRORES_4444]:
            params.update({
                "c:v": "prores_ks",
                "profile:v": "3"
            })

            # 设置ProRes配置文件
            profile_map = {
                EnhancedExportFormat.PRORES_LT: "1",
                EnhancedExportFormat.PRORES_HQ: "3",
                EnhancedExportFormat.PRORES_4444: "4"
            }
            if format_type in profile_map:
                params["profile:v"] = profile_map[format_type]

        # 音频参数
        if format_type not in [EnhancedExportFormat.MP3_AUDIO, EnhancedExportFormat.WAV_AUDIO,
                               EnhancedExportFormat.FLAC_AUDIO]:
            params.update({
                "c:a": "aac",
                "b:a": "128k"
            })

        return params

    @staticmethod
    def validate_export_parameters(preset: ExportPreset,
                                 source_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证导出参数"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }

        # 检查分辨率
        if preset.resolution[0] > 0 and preset.resolution[1] > 0:
            source_width = source_info.get("width", 0)
            source_height = source_info.get("height", 0)

            if source_width > 0 and source_height > 0:
                if preset.resolution[0] > source_width * 2 or preset.resolution[1] > source_height * 2:
                    validation_result["warnings"].append("输出分辨率远高于源分辨率，可能不会提升质量")

        # 检查比特率
        if preset.bitrate > 0:
            source_bitrate = source_info.get("bitrate", 0)
            if source_bitrate > 0 and preset.bitrate > source_bitrate * 2:
                validation_result["warnings"].append("输出比特率远高于源比特率，可能浪费存储空间")

        # 检查帧率
        if preset.fps > 0:
            source_fps = source_info.get("fps", 0)
            if source_fps > 0 and preset.fps > source_fps * 2:
                validation_result["warnings"].append("输出帧率远高于源帧率，可能造成伪影")

        # 检查格式兼容性
        if preset.format == ExportFormat.MP4_H265:
            # 检查H.265支持
            if not EnhancedExportPresets._check_h265_support():
                validation_result["errors"].append("系统不支持H.265编码")
                validation_result["valid"] = False

        # 生成建议
        if not validation_result["errors"]:
            validation_result["recommendations"] = EnhancedExportPresets._generate_recommendations(
                preset, source_info
            )

        return validation_result

    @staticmethod
    def _check_h265_support() -> bool:
        """检查H.265支持"""
        try:
            result = subprocess.run(['ffmpeg', '-encoders'],
                                  capture_output=True, text=True, timeout=5)
            return 'libx265' in result.stdout
        except:
            return False

    @staticmethod
    def _generate_recommendations(preset: ExportPreset,
                               source_info: Dict[str, Any]) -> List[str]:
        """生成导出建议"""
        recommendations = []

        # 基于源分辨率建议
        source_width = source_info.get("width", 0)
        source_height = source_info.get("height", 0)

        if source_width >= 3840 and source_height >= 2160:
            if preset.format != ExportFormat.MP4_H265:
                recommendations.append("源视频为4K，建议使用H.265以获得更好的压缩率")

        # 基于内容类型建议
        content_type = source_info.get("content_type", "general")
        if content_type == "screen_recording":
            recommendations.append("屏幕录制内容建议使用CRF值18-22以获得更好的清晰度")
        elif content_type == "animation":
            recommendations.append("动画内容建议使用更高的比特率以保持细节")

        # 基于音频建议
        audio_channels = source_info.get("audio_channels", 2)
        if audio_channels > 2:
            recommendations.append("源音频为多声道，建议使用更高的音频比特率")

        return recommendations


class EnhancedExportValidator:
    """增强导出验证器"""

    def __init__(self):
        self.logger = Logger(__name__)
        self.format_specs = EnhancedExportPresets.get_format_specifications()

    def validate_format_support(self, format_type: EnhancedExportFormat) -> Dict[str, Any]:
        """验证格式支持"""
        validation = {
            "supported": True,
            "reason": "",
            "alternative_formats": [],
            "limitations": []
        }

        try:
            if format_type == EnhancedExportFormat.MP4_H264:
                if not self._check_ffmpeg_encoder("libx264"):
                    validation["supported"] = False
                    validation["reason"] = "缺少H.264编码器支持"

            elif format_type == EnhancedExportFormat.MP4_H265:
                if not self._check_ffmpeg_encoder("libx265"):
                    validation["supported"] = False
                    validation["reason"] = "缺少H.265编码器支持"

            elif format_type == EnhancedExportFormat.MP4_AV1:
                if not self._check_ffmpeg_encoder("libaom-av1"):
                    validation["supported"] = False
                    validation["reason"] = "缺少AV1编码器支持"

            elif format_type == EnhancedExportFormat.MOV_PRORES:
                if not self._check_ffmpeg_encoder("prores_ks"):
                    validation["supported"] = False
                    validation["reason"] = "缺少ProRes编码器支持"

            # 检查硬件加速支持
            if validation["supported"]:
                hardware_support = self._check_hardware_acceleration(format_type)
                if hardware_support:
                    validation["limitations"].extend(hardware_support)

        except Exception as e:
            validation["supported"] = False
            validation["reason"] = f"验证失败: {str(e)}"

        # 提供替代格式
        if not validation["supported"]:
            validation["alternative_formats"] = self._get_alternative_formats(format_type)

        return validation

    def _check_ffmpeg_encoder(self, encoder_name: str) -> bool:
        """检查FFmpeg编码器支持"""
        try:
            result = subprocess.run(['ffmpeg', '-encoders'],
                                  capture_output=True, text=True, timeout=10)
            return encoder_name in result.stdout
        except:
            return False

    def _check_hardware_acceleration(self, format_type: EnhancedExportFormat) -> List[str]:
        """检查硬件加速支持"""
        limitations = []

        try:
            # 检查NVENC
            if self._check_ffmpeg_encoder("h264_nvenc"):
                limitations.append("支持NVIDIA GPU加速")

            # 检查AMF
            if self._check_ffmpeg_encoder("h264_amf"):
                limitations.append("支持AMD GPU加速")

            # 检查QSV
            if self._check_ffmpeg_encoder("h264_qsv"):
                limitations.append("支持Intel QSV加速")

        except Exception as e:
            self.logger.warning(f"Hardware acceleration check failed: {e}")

        return limitations

    def _get_alternative_formats(self, format_type: EnhancedExportFormat) -> List[EnhancedExportFormat]:
        """获取替代格式"""
        alternatives = []

        if format_type == EnhancedExportFormat.MP4_H265:
            alternatives.append(EnhancedExportFormat.MP4_H264)
        elif format_type == EnhancedExportFormat.MP4_AV1:
            alternatives.extend([EnhancedExportFormat.MP4_H264, EnhancedExportFormat.WEBM_VP9])
        elif format_type == EnhancedExportFormat.MOV_PRORES:
            alternatives.append(EnhancedExportFormat.MP4_H264)

        return alternatives


# 全局实例
enhanced_export_presets = EnhancedExportPresets()
enhanced_export_validator = EnhancedExportValidator()