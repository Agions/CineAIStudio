#!/usr/bin/env python3
"""测试直接视频导出器"""

import pytest
from dataclasses import asdict

from app.services.export.direct_video_exporter import (
    Resolution,
    VideoCodec,
    VideoExportConfig,
    DirectVideoExporter,
)


class TestResolution:
    """测试分辨率枚举"""

    def test_landscape_resolutions(self):
        """测试横屏分辨率"""
        assert Resolution.FHD_1080P.width == 1920
        assert Resolution.FHD_1080P.height == 1080
        assert Resolution.UHD_4K.width == 3840
        assert Resolution.UHD_4K.height == 2160

    def test_vertical_resolutions(self):
        """测试竖屏分辨率"""
        assert Resolution.VERTICAL_1080P.width == 1080
        assert Resolution.VERTICAL_1080P.height == 1920

    def test_square_resolutions(self):
        """测试方形分辨率"""
        assert Resolution.SQUARE_1080.width == 1080
        assert Resolution.SQUARE_1080.height == 1080


class TestVideoCodec:
    """测试视频编码枚举"""

    def test_codecs(self):
        """测试编码类型"""
        assert VideoCodec.H264.value == "libx264"
        assert VideoCodec.H265.value == "libx265"
        assert VideoCodec.VP9.value == "libvpx-vp9"
        assert VideoCodec.AV1.value == "libaom-av1"


class TestVideoExportConfig:
    """测试视频导出配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = VideoExportConfig()
        
        assert config.resolution == Resolution.FHD_1080P
        assert config.codec == VideoCodec.H264
        assert config.fps == 30

    def test_custom_config(self):
        """测试自定义配置"""
        config = VideoExportConfig(
            resolution=Resolution.UHD_4K,
            codec=VideoCodec.H265,
            fps=60,
            bitrate=50000,
        )
        
        assert config.resolution == Resolution.UHD_4K
        assert config.codec == VideoCodec.H265
        assert config.fps == 60


class TestDirectVideoExporter:
    """测试直接视频导出器"""

    def test_init(self):
        """测试初始化"""
        exporter = DirectVideoExporter()
        
        assert exporter._default_resolution == Resolution.FHD_1080P

    def test_init_custom(self):
        """测试自定义初始化"""
        exporter = DirectVideoExporter(
            default_resolution=Resolution.HD_720P,
            enable_hardware_acceleration=True,
        )
        
        assert exporter._default_resolution == Resolution.HD_720P

    def test_get_ffmpeg_codec(self):
        """测试获取 FFmpeg 编码器"""
        exporter = DirectVideoExporter()
        
        assert exporter._get_ffmpeg_codec(VideoCodec.H264) == "libx264"
        assert exporter._get_ffmpeg_codec(VideoCodec.H265) == "libx265"

    def test_estimate_file_size(self):
        """测试估算文件大小"""
        exporter = DirectVideoExporter()
        
        size = exporter.estimate_file_size(
            duration=60.0,
            bitrate=10000,
        )
        
        # 60秒 * 10000kbps / 8 = 75MB
        assert size > 0
