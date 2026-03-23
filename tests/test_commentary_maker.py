#!/usr/bin/env python3
"""测试视频解说制作器"""

import pytest
from dataclasses import asdict

from app.services.video.commentary_maker import (
    CommentaryStyle,
    CommentarySegment,
    CommentaryProject,
    CommentaryMaker,
)


class TestCommentaryStyle:
    """测试解说风格枚举"""

    def test_all_styles(self):
        """测试所有解说风格"""
        styles = [
            CommentaryStyle.EXPLAINER,
            CommentaryStyle.REVIEW,
            CommentaryStyle.STORYTELLING,
            CommentaryStyle.EDUCATIONAL,
            CommentaryStyle.NEWS,
        ]
        
        assert len(styles) == 5
        assert CommentaryStyle.EXPLAINER.value == "explainer"


class TestCommentarySegment:
    """测试解说片段"""

    def test_creation(self):
        """测试创建"""
        segment = CommentarySegment(
            script="这是解说文案",
            video_start=0.0,
            video_end=5.0,
            audio_path="/path/to/audio.mp3",
            audio_duration=4.5,
        )
        
        assert segment.script == "这是解说文案"
        assert segment.video_start == 0.0
        assert segment.video_end == 5.0
        assert segment.audio_path == "/path/to/audio.mp3"

    def test_default_values(self):
        """测试默认值"""
        segment = CommentarySegment(
            script="测试",
            video_start=0.0,
            video_end=1.0,
        )
        
        assert segment.audio_path == ""
        assert segment.audio_duration == 0.0


class TestCommentaryProject:
    """测试解说项目"""

    def test_creation(self):
        """测试创建"""
        project = CommentaryProject(
            name="测试解说",
            source_video="/test/video.mp4",
        )
        
        assert project.name == "测试解说"
        assert project.source_video == "/test/video.mp4"
        assert project.segments == []

    def test_add_segment(self):
        """测试添加片段"""
        project = CommentaryProject(
            name="测试",
            source_video="/test.mp4",
        )
        
        segment = CommentarySegment(
            script="测试",
            video_start=0.0,
            video_end=1.0,
        )
        
        project.segments.append(segment)
        
        assert len(project.segments) == 1


class TestCommentaryMaker:
    """测试解说制作器"""

    def test_init(self):
        """测试初始化"""
        maker = CommentaryMaker()
        
        assert maker.scene_analyzer is not None

    def test_init_custom_options(self):
        """测试自定义选项"""
        maker = CommentaryMaker(
            voice_provider="azure",
            script_style=CommentaryStyle.REVIEW,
        )
        
        assert maker._voice_provider == "azure"

    def test_default_commentary_style(self):
        """测试默认解说风格"""
        maker = CommentaryMaker()
        
        assert maker._default_style == CommentaryStyle.EXPLAINER
