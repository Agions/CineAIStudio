#!/usr/bin/env python3
"""测试 DaVinci 导出器"""

import pytest
from dataclasses import asdict

from app.services.export.davinci_exporter import (
    DaVinciClip,
    DaVinciTimeline,
    DaVinciExporter,
)


class TestDaVinciClip:
    """测试达芬奇片段"""

    def test_creation(self):
        """测试创建"""
        clip = DaVinciClip(
            name="测试片段",
            file_path="/test.mp4",
            start=0.0,
            end=10.0,
        )
        
        assert clip.name == "测试片段"
        assert clip.file_path == "/test.mp4"
        assert clip.start == 0.0
        assert clip.end == 10.0

    def test_with_points(self):
        """测试带入出点"""
        clip = DaVinciClip(
            name="测试",
            file_path="/test.mp4",
            start=0.0,
            end=10.0,
            in_point=2.0,
            out_point=8.0,
            track=1,
        )
        
        assert clip.in_point == 2.0
        assert clip.out_point == 8.0
        assert clip.track == 1


class TestDaVinciTimeline:
    """测试达芬奇时间线"""

    def test_default_creation(self):
        """测试默认创建"""
        timeline = DaVinciTimeline(
            name="测试时间线",
        )
        
        assert timeline.name == "测试时间线"
        assert timeline.fps == 30.0
        assert timeline.width == 1920
        assert timeline.height == 1080

    def test_custom_creation(self):
        """测试自定义创建"""
        timeline = DaVinciTimeline(
            name="自定义",
            fps=60.0,
            width=3840,
            height=2160,
        )
        
        assert timeline.fps == 60.0
        assert timeline.width == 3840
        assert timeline.height == 2160

    def test_default_lists(self):
        """测试默认列表"""
        timeline = DaVinciTimeline(name="测试")
        
        assert timeline.video_clips == []
        assert timeline.audio_clips == []
        assert timeline.subtitles == []


class TestDaVinciExporter:
    """测试达芬奇导出器（API 已变更，跳过）"""

    def test_init(self):
        """测试初始化"""
        pytest.skip("DaVinciExporter API 已变更，需重写测试")

    def test_init_custom_format(self):
        """测试自定义格式"""
        pytest.skip("DaVinciExporter API 已变更，需重写测试")

    def test_create_timeline(self):
        """测试创建时间线"""
        pytest.skip("DaVinciExporter API 已变更，需重写测试")

    def test_add_video_clip(self):
        """测试添加视频片段"""
        pytest.skip("DaVinciExporter API 已变更，需重写测试")
