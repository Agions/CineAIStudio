#!/usr/bin/env python3
"""测试 Final Cut Pro 导出器"""

import pytest
from dataclasses import asdict

from app.services.export.finalcut_exporter import (
    FCPVersion,
    VideoFormat,
    FCPConfig,
    FinalCutExporter,
)


class TestFCPVersion:
    """测试 FCP 版本枚举"""

    def test_all_versions(self):
        """测试所有版本"""
        versions = [
            FCPVersion.V1_10,
            FCPVersion.V1_9,
            FCPVersion.V1_8,
        ]
        
        assert len(versions) == 3
        assert FCPVersion.V1_10.value == "1.10"


class TestVideoFormat:
    """测试视频格式枚举"""

    def test_formats(self):
        """测试视频格式"""
        assert VideoFormat.HD_1080.value == "FFVideoFormat1080p30"
        assert VideoFormat.UHD_4K.value == "FFVideoFormat3840x2160p30"


class TestFCPConfig:
    """测试 Final Cut 配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = FCPConfig()
        
        assert config.version == FCPVersion.V1_10
        assert config.width == 1920
        assert config.height == 1080

    def test_custom_config(self):
        """测试自定义配置"""
        config = FCPConfig(
            version=FCPVersion.V1_9,
            width=3840,
            height=2160,
            fps=60.0,
        )
        
        assert config.version == FCPVersion.V1_9
        assert config.width == 3840
        assert config.height == 2160


class TestFinalCutExporter:
    """测试 Final Cut 导出器"""

    def test_init(self):
        """测试初始化"""
        exporter = FinalCutExporter()

        assert exporter.config is not None
        assert exporter.config.version == FCPVersion.V1_10

    def test_init_custom_version(self):
        """测试自定义版本"""
        config = FCPConfig(version=FCPVersion.V1_8)
        exporter = FinalCutExporter(config=config)

        assert exporter.config.version == FCPVersion.V1_8

    def test_create_library(self):
        """测试创建媒体库"""
        exporter = FinalCutExporter()
        
        library = exporter.create_library("测试库")
        
        assert library is not None

    def test_create_project(self):
        """测试创建项目"""
        exporter = FinalCutExporter()
        
        project = exporter.create_project("测试项目")
        
        assert project is not None
