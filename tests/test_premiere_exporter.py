#!/usr/bin/env python3
"""测试 Premiere 导出器"""

import pytest
from dataclasses import asdict

from app.services.export.premiere_exporter import (
    PremiereVersion,
    VideoStandard,
    PremiereConfig,
    PremiereExporter,
)


class TestPremiereVersion:
    """测试 Premiere 版本枚举"""

    def test_all_versions(self):
        """测试所有版本"""
        versions = [
            PremiereVersion.CC2024,
            PremiereVersion.CC2023,
            PremiereVersion.CC2022,
            PremiereVersion.CC2021,
            PremiereVersion.CC2020,
        ]
        
        assert len(versions) == 5
        assert PremiereVersion.CC2024.value == "2024"


class TestVideoStandard:
    """测试视频标准枚举"""

    def test_standards(self):
        """测试视频标准"""
        assert VideoStandard.NTSC.value == "NTSC"
        assert VideoStandard.PAL.value == "PAL"


class TestPremiereConfig:
    """测试 Premiere 配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = PremiereConfig()
        
        assert config.version == PremiereVersion.CC2024
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 30.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = PremiereConfig(
            version=PremiereVersion.CC2023,
            width=3840,
            height=2160,
            fps=60.0,
        )
        
        assert config.version == PremiereVersion.CC2023
        assert config.width == 3840
        assert config.height == 2160
        assert config.fps == 60.0


class TestPremiereExporter:
    """测试 Premiere 导出器"""

    def test_init(self):
        """测试初始化"""
        exporter = PremiereExporter()
        
        assert exporter._version == PremiereVersion.CC2024

    def test_init_custom_version(self):
        """测试自定义版本"""
        exporter = PremiereExporter(version=PremiereVersion.CC2022)
        
        assert exporter._version == PremiereVersion.CC2022

    def test_create_project(self):
        """测试创建项目"""
        exporter = PremiereExporter()
        
        project = exporter.create_project("测试项目")
        
        assert project is not None

    def test_default_project_settings(self):
        """测试默认项目设置"""
        exporter = PremiereExporter()
        
        settings = exporter._get_default_project_settings()
        
        assert "width" in settings
        assert "height" in settings
        assert "fps" in settings
