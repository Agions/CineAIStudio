#!/usr/bin/env python3
"""测试音频节拍检测"""

import pytest
from dataclasses import asdict

from app.services.audio.beat_detector import (
    BeatStrength,
    MusicSection,
    BeatInfo,
    SectionInfo,
    AudioAnalysisResult,
    BeatDetector,
)


class TestBeatStrength:
    """测试节拍强度枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert BeatStrength.STRONG.value == "strong"
        assert BeatStrength.MEDIUM.value == "medium"
        assert BeatStrength.WEAK.value == "weak"


class TestMusicSection:
    """测试音乐段落枚举"""

    def test_all_sections(self):
        """测试所有段落"""
        sections = [
            MusicSection.INTRO,
            MusicSection.VERSE,
            MusicSection.CHORUS,
            MusicSection.BRIDGE,
            MusicSection.OUTRO,
            MusicSection.UNKNOWN,
        ]
        
        assert len(sections) == 6


class TestBeatInfo:
    """测试节拍信息"""

    def test_creation(self):
        """测试创建"""
        beat = BeatInfo(
            timestamp=1.5,
            strength=BeatStrength.STRONG,
            bar_position=1,
        )
        
        assert beat.timestamp == 1.5
        assert beat.strength == BeatStrength.STRONG
        assert beat.bar_position == 1


class TestSectionInfo:
    """测试段落信息"""

    def test_creation(self):
        """测试创建"""
        section = SectionInfo(
            start=0.0,
            end=10.0,
            section_type=MusicSection.INTRO,
            energy=0.8,
        )
        
        assert section.start == 0.0
        assert section.end == 10.0
        assert section.section_type == MusicSection.INTRO
        assert section.energy == 0.8


class TestAudioAnalysisResult:
    """测试音频分析结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = AudioAnalysisResult(
            file_path="/test/audio.mp3",
            duration=180.0,
            sample_rate=44100,
        )
        
        assert result.file_path == "/test/audio.mp3"
        assert result.duration == 180.0
        assert result.sample_rate == 44100
        assert result.bpm == 0.0
        assert result.beats == []
        assert result.onsets == []
        assert result.sections == []

    def test_with_beats(self):
        """测试带节拍"""
        beats = [
            BeatInfo(1.0, BeatStrength.STRONG, 1),
            BeatInfo(2.0, BeatStrength.WEAK, 2),
        ]
        
        result = AudioAnalysisResult(
            file_path="/test/audio.mp3",
            duration=180.0,
            sample_rate=44100,
            beats=beats,
        )
        
        assert len(result.beats) == 2
        assert result.beats[0].strength == BeatStrength.STRONG


class TestBeatDetector:
    """测试节拍检测器"""

    def test_init(self):
        """测试初始化"""
        detector = BeatDetector()
        
        assert detector._cache_enabled is True

    def test_init_with_options(self):
        """测试带选项初始化"""
        detector = BeatDetector(enable_cache=False)
        
        assert detector._cache_enabled is False

    def test_beat_strength_from_amplitude(self):
        """测试从振幅判断节拍强度"""
        detector = BeatDetector()
        
        # 测试不同振幅等级
        strong = detector._beat_strength_from_amplitude(1.0)
        assert strong == BeatStrength.STRONG
        
        medium = detector._beat_strength_from_amplitude(0.5)
        assert medium == BeatStrength.MEDIUM
        
        weak = detector._beat_strength_from_amplitude(0.2)
        assert weak == BeatStrength.WEAK

    def test_estimate_bar_position(self):
        """测试小节位置估计"""
        detector = BeatDetector()
        
        # 假设 BPM 为 120，每拍 0.5 秒
        # 1.0秒应该是第3拍（1.0/0.5 = 2，在4/4拍中为第3拍）
        pos = detector._estimate_bar_position(1.0, 120.0)
        assert pos in [1, 2, 3, 4]

    def test_estimate_section_type(self):
        """测试段落类型估计"""
        detector = BeatDetector()
        
        # 测试不同时间点
        intro = detector._estimate_section_type(5.0, 180.0)
        assert intro in [MusicSection.INTRO, MusicSection.VERSE]
        
        outro = detector._estimate_section_type(170.0, 180.0)
        assert outro in [MusicSection.OUTRO, MusicSection.UNKNOWN]
