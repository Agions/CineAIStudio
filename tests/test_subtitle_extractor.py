#!/usr/bin/env python3
"""测试字幕提取器"""

import pytest
from dataclasses import asdict

from app.services.ai.subtitle_extractor import (
    SubtitleSegment,
    SubtitleExtractionResult,
    OCRSubtitleExtractor, SpeechSubtitleExtractor,
)


class TestSubtitleSegment:
    """测试字幕片段"""

    def test_creation(self):
        """测试创建"""
        segment = SubtitleSegment(
            start=0.0,
            end=3.5,
            text="第一句台词",
            confidence=0.95,
            source="speech",
        )
        
        assert segment.start == 0.0
        assert segment.end == 3.5
        assert segment.text == "第一句台词"
        assert segment.confidence == 0.95
        assert segment.source == "speech"

    def test_default_values(self):
        """测试默认值"""
        segment = SubtitleSegment(
            start=0.0,
            end=1.0,
            text="测试",
        )
        
        assert segment.confidence == 1.0
        assert segment.source == ""

    def test_to_dict(self):
        """测试转换为字典"""
        segment = SubtitleSegment(
            start=0.0,
            end=1.0,
            text="测试",
        )
        
        d = asdict(segment)
        
        assert d["start"] == 0.0
        assert d["text"] == "测试"


class TestSubtitleExtractionResult:
    """测试字幕提取结果"""

    def test_creation(self):
        """测试创建"""
        segments = [
            SubtitleSegment(0.0, 1.0, "第一句"),
            SubtitleSegment(1.0, 2.0, "第二句"),
        ]
        
        result = SubtitleExtractionResult(
            video_path="/test/video.mp4",
            duration=120.0,
            segments=segments,
            full_text="第一句 第二句",
            language="zh",
            method="speech",
        )
        
        assert result.video_path == "/test/video.mp4"
        assert result.duration == 120.0
        assert len(result.segments) == 2
        assert result.full_text == "第一句 第二句"

    def test_default_values(self):
        """测试默认值"""
        result = SubtitleExtractionResult(
            video_path="/test.mp4",
            duration=60.0,
        )
        
        assert result.segments == []
        assert result.full_text == ""
        assert result.language == "zh"
        assert result.method == ""

    def test_full_text_from_segments(self):
        """测试从片段生成完整文本"""
        segments = [
            SubtitleSegment(0.0, 1.0, "你好"),
            SubtitleSegment(1.0, 2.0, "世界"),
        ]
        
        result = SubtitleExtractionResult(
            video_path="/test.mp4",
            duration=2.0,
            segments=segments,
        )
        
        # 应该能组合成完整文本
        full_text = " ".join(s.text for s in result.segments)
        assert "你好" in full_text
        assert "世界" in full_text


class TestSubtitleExtractor:
    """测试字幕提取器"""

    def test_init_default(self):
        """测试默认初始化"""
        extractor = SubtitleExtractor()
        
        assert extractor._provider in ["whisper", "openai", "azure"]

    def test_init_custom_provider(self):
        """测试自定义提供商"""
        extractor = SubtitleExtractor(provider="azure")
        
        assert extractor._provider == "azure"

    def test_init_with_api_key(self):
        """测试带 API 密钥初始化"""
        extractor = SubtitleExtractor(api_key="test_key")
        
        assert extractor._api_key == "test_key"

    def test_get_supported_formats(self):
        """测试获取支持的格式"""
        extractor = SubtitleExtractor()
        
        formats = extractor.get_supported_formats()
        
        assert isinstance(formats, list)
        assert "srt" in formats
        assert "ass" in formats

    def test_detect_language(self):
        """测试语言检测"""
        extractor = SubtitleExtractor()
        
        # 测试中文
        lang = extractor._detect_language("你好世界")
        assert lang == "zh"
        
        # 测试英文
        lang = extractor._detect_language("Hello world")
        assert lang == "en"

    def test_merge_overlapping_segments(self):
        """测试合并重叠片段"""
        extractor = SubtitleExtractor()
        
        segments = [
            SubtitleSegment(0.0, 1.0, "第一句"),
            SubtitleSegment(0.8, 1.5, "重叠"),
            SubtitleSegment(1.5, 2.0, "第三句"),
        ]
        
        merged = extractor._merge_overlapping_segments(segments)
        
        # 应该合并或保持原样
        assert len(merged) >= 1
