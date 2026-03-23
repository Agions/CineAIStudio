#!/usr/bin/env python3
"""测试静音检测与移除"""

import pytest
from dataclasses import asdict

from app.services.viral_video.silence_remover import (
    SilenceSegment,
    RemovalResult,
    SilenceRemover,
)


class TestSilenceSegment:
    """测试静音片段"""

    def test_creation(self):
        """测试创建"""
        segment = SilenceSegment(
            start_time=5.0,
            end_time=8.0,
            duration=3.0,
            confidence=0.95,
        )
        
        assert segment.start_time == 5.0
        assert segment.end_time == 8.0
        assert segment.duration == 3.0
        assert segment.confidence == 0.95

    def test_default_confidence(self):
        """测试默认置信度"""
        segment = SilenceSegment(
            start_time=0.0,
            end_time=1.0,
            duration=1.0,
        )
        
        assert segment.confidence == 0.0


class TestRemovalResult:
    """测试移除结果"""

    def test_creation(self):
        """测试创建"""
        removed = [
            SilenceSegment(5.0, 8.0, 3.0, 0.9),
        ]
        keep = [(0.0, 5.0), (8.0, 10.0)]
        
        result = RemovalResult(
            original_duration=10.0,
            new_duration=7.0,
            removed_segments=removed,
            keep_segments=keep,
            compression_ratio=0.7,
        )
        
        assert result.original_duration == 10.0
        assert result.new_duration == 7.0
        assert len(result.removed_segments) == 1


class TestSilenceRemover:
    """测试静音移除器"""

    def test_init_default(self):
        """测试默认初始化"""
        remover = SilenceRemover()
        
        assert remover.silence_threshold_db == -40.0
        assert remover.min_silence_duration == 0.5

    def test_init_custom(self):
        """测试自定义初始化"""
        remover = SilenceRemover(
            silence_threshold_db=-50.0,
            min_silence_duration=1.0,
            padding_duration=0.2,
        )
        
        assert remover.silence_threshold_db == -50.0
        assert remover.min_silence_duration == 1.0
        assert remover.padding_duration == 0.2

    def test_validate_threshold(self):
        """测试验证阈值"""
        remover = SilenceRemover()
        
        # 有效阈值
        assert remover._validate_threshold(-40.0) == -40.0
        assert remover._validate_threshold(-60.0) == -60.0
        
        # 无效阈值应返回默认值
        assert remover._validate_threshold(0.0) == -40.0
        assert remover._validate_threshold(-100.0) == -40.0

    def test_calculate_compression_ratio(self):
        """测试计算压缩比例"""
        remover = SilenceRemover()
        
        ratio = remover._calculate_compression_ratio(10.0, 7.0)
        
        assert ratio == 0.7

    def test_merge_close_segments(self):
        """测试合并接近的片段"""
        remover = SilenceRemover()
        
        segments = [
            SilenceSegment(0.0, 0.5, 0.5, 0.9),
            SilenceSegment(0.6, 1.0, 0.4, 0.9),  # 间隔只有0.1秒
        ]
        
        merged = remover._merge_close_segments(segments, merge_threshold=0.3)
        
        # 间隔小于阈值应该被合并
        assert len(merged) <= len(segments)
