#!/usr/bin/env python3
"""测试视频混剪制作器"""

import pytest
from dataclasses import asdict

from app.services.video.mashup_maker import (
    MashupStyle,
    TransitionType,
    ClipInfo,
    MashupProject,
    MashupMaker,
)


class TestMashupStyle:
    """测试混剪风格枚举"""

    def test_all_styles(self):
        """测试所有混剪风格"""
        styles = [
            MashupStyle.FAST_PACED,
            MashupStyle.CINEMATIC,
            MashupStyle.VLOG,
            MashupStyle.HIGHLIGHT,
            MashupStyle.MONTAGE,
        ]
        
        assert len(styles) == 5
        assert MashupStyle.FAST_PACED.value == "fast_paced"


class TestTransitionType:
    """测试转场类型枚举"""

    def test_all_types(self):
        """测试所有转场类型"""
        types = [
            TransitionType.CUT,
            TransitionType.FADE,
            TransitionType.DISSOLVE,
            TransitionType.WIPE,
            TransitionType.ZOOM,
            TransitionType.SLIDE,
        ]
        
        assert len(types) == 6
        assert TransitionType.CUT.value == "cut"


class TestClipInfo:
    """测试混剪片段"""

    def test_creation(self):
        """测试创建"""
        segment = ClipInfo(
            source_video="/test/clip1.mp4",
            start_time=0.0,
            duration=5.0,
            transition=TransitionType.DISSOLVE,
        )
        
        assert segment.source_video == "/test/clip1.mp4"
        assert segment.start_time == 0.0
        assert segment.duration == 5.0
        assert segment.transition == TransitionType.DISSOLVE


class TestMashupProject:
    """测试混剪项目"""

    def test_creation(self):
        """测试创建"""
        project = MashupProject(
            name="测试混剪",
            source_videos=["/test/v1.mp4", "/test/v2.mp4"],
            background_music="/test/bgm.mp3",
        )
        
        assert project.name == "测试混剪"
        assert len(project.source_videos) == 2
        assert project.background_music == "/test/bgm.mp3"

    def test_default_values(self):
        """测试默认值"""
        project = MashupProject(
            name="测试",
            source_videos=[],
        )
        
        assert project.style == MashupStyle.FAST_PACED
        assert project.segments == []


class TestMashupMaker:
    """测试混剪制作器"""

    def test_init(self):
        """测试初始化"""
        maker = MashupMaker()
        
        assert maker.scene_analyzer is not None

    def test_init_custom_style(self):
        """测试自定义风格"""
        maker = MashupMaker(style=MashupStyle.CINEMATIC)
        
        assert maker._style == MashupStyle.CINEMATIC

    def test_default_style(self):
        """测试默认风格"""
        maker = MashupMaker()
        
        assert maker._style == MashupStyle.FAST_PACED
