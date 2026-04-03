#!/usr/bin/env python3
"""Test Video Mashup Maker"""

import pytest
from dataclasses import asdict

from app.services.video.mashup_maker import (
    MashupStyle,
    TransitionType,
    ClipInfo,
    BeatInfo,
    MashupProject,
)


class TestMashupStyle:
    """Test mashup style enum"""

    def test_all_styles(self):
        """Test all mashup styles"""
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
    """Test transition type enum"""

    def test_all_types(self):
        """Test all transition types"""
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
    """Test clip info"""

    def test_creation(self):
        """Test creation"""
        segment = ClipInfo(
            source_video="/test/clip1.mp4",
            source_index=0,
            start=0.0,
            end=5.0,
            duration=5.0,
        )
        
        assert segment.source_video == "/test/clip1.mp4"
        assert segment.start == 0.0
        assert segment.end == 5.0
        assert segment.duration == 5.0


class TestMashupProject:
    """Test mashup project"""

    def test_creation(self):
        """Test creation"""
        project = MashupProject(
            name="测试混剪",
            source_videos=["/test/v1.mp4", "/test/v2.mp4"],
            background_music="/test/bgm.mp3",
        )
        
        assert project.name == "测试混剪"
        assert len(project.source_videos) == 2
        assert project.background_music == "/test/bgm.mp3"

    def test_default_values(self):
        """Test default values"""
        project = MashupProject(
            name="测试",
            source_videos=[],
        )
        
        assert project.style == MashupStyle.FAST_PACED


