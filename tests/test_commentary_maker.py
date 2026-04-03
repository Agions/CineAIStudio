#!/usr/bin/env python3
"""Test Commentary Maker"""

import pytest
from dataclasses import asdict

from app.services.video.commentary_maker import (
    CommentaryStyle,
    CommentarySegment,
    CommentaryProject,
    CommentaryMaker,
)


class TestCommentaryStyle:
    """Test commentary style enum"""

    def test_all_styles(self):
        """Test all styles"""
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
    """Test commentary segment"""

    def test_creation(self):
        """Test creation"""
        segment = CommentarySegment(
            script="这是解说内容",
            video_start=0.0,
            video_end=5.0,
        )
        
        assert segment.script == "这是解说内容"
        assert segment.video_start == 0.0
        assert segment.video_end == 5.0


class TestCommentaryProject:
    """Test commentary project"""

    def test_creation(self):
        """Test creation"""
        project = CommentaryProject(
            name="测试项目",
            source_video="/test/video.mp4",
            topic="测试主题",
        )
        
        assert project.name == "测试项目"
        assert project.source_video == "/test/video.mp4"
        assert project.topic == "测试主题"
        assert project.style == CommentaryStyle.EXPLAINER


class TestCommentaryMaker:
    """Test commentary maker"""

    def test_init(self):
        """Test initialization"""
        maker = CommentaryMaker()
        
        assert maker.voice_provider == "edge"
