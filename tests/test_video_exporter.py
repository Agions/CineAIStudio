#!/usr/bin/env python3
"""测试视频导出器"""

import pytest
from dataclasses import asdict

from app.services.export.video_exporter import (
    ExportFormat,
    VideoCodec,
    AudioCodec,
    ExportConfig,
    VideoExporter,
)


class TestExportFormat:
    """测试导出格式枚举"""

    def test_all_formats(self):
        """测试所有格式"""
        formats = [
            ExportFormat.MP4,
            ExportFormat.MOV,
            ExportFormat.WEBM,
            ExportFormat.GIF,
        ]
        
        assert len(formats) == 4
        assert ExportFormat.MP4.value == "mp4"


class TestVideoCodec:
    """测试视频编码枚举"""

    def test_codecs(self):
        """测试编码"""
        assert VideoCodec.H264.value == "libx264"
        assert VideoCodec.H265.value == "libx265"
        assert VideoCodec.VP9.value == "libvpx-vp9"


class TestAudioCodec:
    """测试音频编码枚举"""

    def test_codecs(self):
        """测试音频编码"""
        assert AudioCodec.AAC.value == "aac"
        assert AudioCodec.MP3.value == "libmp3lame"
        assert AudioCodec.OPUS.value == "libopus"


class TestExportConfig:
    """测试导出配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = ExportConfig()
        
        assert config.format == ExportFormat.MP4
        assert config.video_codec == VideoCodec.H264
        assert config.audio_codec == AudioCodec.AAC

    def test_custom_config(self):
        """测试自定义配置"""
        config = ExportConfig(
            format=ExportFormat.WEBM,
            video_codec=VideoCodec.VP9,
            crf=18,
            preset="slow",
        )
        
        assert config.format == ExportFormat.WEBM
        assert config.video_codec == VideoCodec.VP9
        assert config.crf == 18


class TestVideoExporter:
    """测试视频导出器"""

    def test_init(self):
        """测试初始化"""
        exporter = VideoExporter()
        
        assert exporter._default_format == ExportFormat.MP4

    def test_init_custom(self):
        """测试自定义初始化"""
        exporter = VideoExporter(
            default_format=ExportFormat.MOV,
            default_cr=23
        )
        
        assert exporter._default_format == ExportFormat.MOV

    def test_get_ffmpeg_format(self):
        """测试获取 FFmpeg 格式"""
        exporter = VideoExporter()
        
        assert exporter._get_ffmpeg_format(ExportFormat.MP4) == "mp4"
        assert exporter._get_ffmpeg_format(ExportFormat.WEBM) == "webm"

    def test_get_video_codec(self):
        """测试获取视频编码"""
        exporter = VideoExporter()
        
        assert exporter._get_video_codec(VideoCodec.H264) == "libx264"
        assert exporter._get_video_codec(VideoCodec.H265) == "libx265"
