#!/usr/bin/env python3
"""测试音画同步引擎"""

import pytest
from dataclasses import asdict

from app.services.audio.sync_engine import (
    SyncStrategy,
    TransitionType,
    SyncPoint,
    SyncPlan,
    SyncEngine,
)


class TestSyncStrategy:
    """测试同步策略枚举"""

    def test_all_strategies(self):
        """测试所有同步策略"""
        strategies = [
            SyncStrategy.BEAT_SYNC,
            SyncStrategy.PHRASE_SYNC,
            SyncStrategy.ENERGY_SYNC,
            SyncStrategy.HYBRID,
        ]
        
        assert len(strategies) == 4
        assert SyncStrategy.BEAT_SYNC.value == "beat_sync"


class TestTransitionType:
    """测试转场类型枚举"""

    def test_all_types(self):
        """测试所有转场类型"""
        types = [
            TransitionType.HARD_CUT,
            TransitionType.CROSSFADE,
            TransitionType.FADE_IN,
            TransitionType.FADE_OUT,
            TransitionType.ZOOM,
            TransitionType.WHIP,
        ]
        
        assert len(types) == 6
        assert TransitionType.HARD_CUT.value == "hard_cut"


class TestSyncPoint:
    """测试同步点"""

    def test_creation(self):
        """测试创建"""
        point = SyncPoint(
            timestamp=5.0,
            clip_index=0,
            transition=TransitionType.HARD_CUT,
            speed_factor=1.0,
        )
        
        assert point.timestamp == 5.0
        assert point.clip_index == 0
        assert point.transition == TransitionType.HARD_CUT


class TestSyncPlan:
    """测试同步计划"""

    def test_creation(self):
        """测试创建"""
        plan = SyncPlan(
            total_duration=60.0,
            bpm=120.0,
            strategy=SyncStrategy.BEAT_SYNC,
        )
        
        assert plan.total_duration == 60.0
        assert plan.bpm == 120.0
        assert plan.strategy == SyncStrategy.BEAT_SYNC


class TestSyncEngine:
    """测试同步引擎"""

    def test_init(self):
        """测试初始化"""
        engine = SyncEngine()
        
        assert engine._default_strategy == SyncStrategy.BEAT_SYNC

    def test_init_custom_strategy(self):
        """测试自定义策略"""
        engine = SyncEngine(strategy=SyncStrategy.HYBRID)
        
        assert engine._strategy == SyncStrategy.HYBRID

    def test_calculate_sync_points_beat(self):
        """测试计算节拍同步点"""
        from app.services.audio.beat_detector import (
            AudioAnalysisResult, BeatInfo, BeatStrength
        )
        
        engine = SyncEngine(strategy=SyncStrategy.BEAT_SYNC)
        
        # 创建模拟分析结果
        result = AudioAnalysisResult(
            file_path="/test.mp3",
            duration=60.0,
            sample_rate=44100,
            bpm=120.0,
            beats=[
                BeatInfo(0.5, BeatStrength.STRONG, 1),
                BeatInfo(1.0, BeatStrength.WEAK, 2),
                BeatInfo(1.5, BeatStrength.STRONG, 3),
            ]
        )
        
        plan = engine.create_sync_plan(result, ["clip1.mp4", "clip2.mp4"])
        
        assert plan is not None
        assert plan.bpm == 120.0

    def test_calculate_sync_points_empty(self):
        """测试空节拍"""
        from app.services.audio.beat_detector import AudioAnalysisResult
        
        engine = SyncEngine()
        
        result = AudioAnalysisResult(
            file_path="/test.mp3",
            duration=60.0,
            sample_rate=44100,
            beats=[]
        )
        
        plan = engine.create_sync_plan(result, ["clip.mp4"])
        
        # 空节拍时应该创建基本的同步计划
        assert plan is not None
