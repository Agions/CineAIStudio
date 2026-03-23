#!/usr/bin/env python3
"""测试节奏分析器"""

import pytest
from dataclasses import asdict

from app.services.viral_video.pace_analyzer import (
    PaceLevel,
    PaceMetrics,
    SceneChange,
    PaceAnalysisResult,
    PaceAnalyzer,
)


class TestPaceLevel:
    """测试节奏等级枚举"""

    def test_all_levels(self):
        """测试所有节奏等级"""
        levels = [
            PaceLevel.SLOW,
            PaceLevel.MODERATE,
            PaceLevel.FAST,
            PaceLevel.VIRAL,
        ]
        
        assert len(levels) == 4
        assert PaceLevel.SLOW.value == "慢节奏"
        assert PaceLevel.VIRAL.value == "爆款节奏"


class TestPaceMetrics:
    """测试节奏指标"""

    def test_creation(self):
        """测试创建"""
        metrics = PaceMetrics(
            cuts_per_minute=20.0,
            avg_shot_duration=3.0,
            visual_change_rate=0.8,
            audio_energy_variance=0.5,
            pace_level=PaceLevel.FAST,
            viral_score=75.0,
        )
        
        assert metrics.cuts_per_minute == 20.0
        assert metrics.pace_level == PaceLevel.FAST
        assert metrics.viral_score == 75.0


class TestSceneChange:
    """测试场景变化"""

    def test_creation(self):
        """测试创建"""
        change = SceneChange(
            timestamp=5.0,
            score=0.9,
            type="cut",
        )
        
        assert change.timestamp == 5.0
        assert change.score == 0.9
        assert change.type == "cut"


class TestPaceAnalysisResult:
    """测试节奏分析结果"""

    def test_creation(self):
        """测试创建"""
        metrics = PaceMetrics(
            cuts_per_minute=15.0,
            avg_shot_duration=4.0,
            visual_change_rate=0.6,
            audio_energy_variance=0.3,
            pace_level=PaceLevel.MODERATE,
            viral_score=60.0,
        )
        
        scene_changes = [
            SceneChange(1.0, 0.8, "cut"),
            SceneChange(5.0, 0.9, "fade"),
        ]
        
        result = PaceAnalysisResult(
            video_duration=60.0,
            metrics=metrics,
            scene_changes=scene_changes,
            energy_curve=[],
            recommendations=[],
        )
        
        assert result.video_duration == 60.0
        assert len(result.scene_changes) == 2


class TestPaceAnalyzer:
    """测试节奏分析器"""

    def test_init(self):
        """测试初始化"""
        analyzer = PaceAnalyzer()
        
        assert analyzer._min_cpm is not None

    def test_init_custom_options(self):
        """测试自定义选项"""
        analyzer = PaceAnalyzer(viral_threshold=80.0)
        
        assert analyzer._viral_threshold == 80.0

    def test_calculate_viral_score(self):
        """测试计算爆款分数"""
        analyzer = PaceAnalyzer()
        
        metrics = PaceMetrics(
            cuts_per_minute=25.0,
            avg_shot_duration=2.5,
            visual_change_rate=0.9,
            audio_energy_variance=0.7,
            pace_level=PaceLevel.FAST,
            viral_score=0.0,
        )
        
        score = analyzer._calculate_viral_score(metrics)
        
        assert score >= 0
        assert score <= 100

    def test_determine_pace_level(self):
        """测试判断节奏等级"""
        analyzer = PaceAnalyzer()
        
        assert analyzer._determine_pace_level(5.0) == PaceLevel.SLOW
        assert analyzer._determine_pace_level(10.0) == PaceLevel.MODERATE
        assert analyzer._determine_pace_level(18.0) == PaceLevel.FAST
        assert analyzer._determine_pace_level(30.0) == PaceLevel.VIRAL

    def test_generate_recommendations(self):
        """测试生成建议"""
        analyzer = PaceAnalyzer()
        
        metrics = PaceMetrics(
            cuts_per_minute=5.0,
            avg_shot_duration=10.0,
            visual_change_rate=0.2,
            audio_energy_variance=0.1,
            pace_level=PaceLevel.SLOW,
            viral_score=30.0,
        )
        
        recommendations = analyzer._generate_recommendations(metrics)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
