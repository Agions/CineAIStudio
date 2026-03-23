#!/usr/bin/env python3
"""测试转场效果"""

import pytest
from dataclasses import asdict

from app.services.video.transition_effects import (
    TransitionType,
    TransitionConfig,
    TransitionEffects,
)


class TestTransitionType:
    """测试转场类型枚举"""

    def test_basic_transitions(self):
        """测试基础转场"""
        assert TransitionType.CUT.value == "cut"
        assert TransitionType.FADE.value == "fade"
        assert TransitionType.FADE_BLACK.value == "fade_black"
        assert TransitionType.FADE_WHITE.value == "fade_white"

    def test_dissolve_transitions(self):
        """测试溶解转场"""
        assert TransitionType.DISSOLVE.value == "dissolve"

    def test_wipe_transitions(self):
        """测试擦除转场"""
        assert TransitionType.WIPE_LEFT.value == "wipe_left"
        assert TransitionType.WIPE_RIGHT.value == "wipe_right"
        assert TransitionType.WIPE_UP.value == "wipe_up"
        assert TransitionType.WIPE_DOWN.value == "wipe_down"

    def test_slide_transitions(self):
        """测试滑动转场"""
        assert TransitionType.SLIDE_LEFT.value == "slide_left"
        assert TransitionType.SLIDE_RIGHT.value == "slide_right"
        assert TransitionType.SLIDE_UP.value == "slide_up"
        assert TransitionType.SLIDE_DOWN.value == "slide_down"

    def test_zoom_transitions(self):
        """测试缩放转场"""
        assert TransitionType.ZOOM_IN.value == "zoom_in"
        assert TransitionType.ZOOM_OUT.value == "zoom_out"


class TestTransitionConfig:
    """测试转场配置"""

    def test_default_creation(self):
        """测试默认创建"""
        config = TransitionConfig()
        
        assert config.duration == 0.5
        assert config.easing == "ease-in-out"

    def test_custom_creation(self):
        """测试自定义创建"""
        config = TransitionConfig(
            effect_type=TransitionType.FADE,
            duration=1.0,
            easing="linear",
        )
        
        assert config.effect_type == TransitionType.FADE
        assert config.duration == 1.0
        assert config.easing == "linear"


class TestTransitionEffects:
    """测试转场效果类"""

    def test_init(self):
        """测试初始化"""
        effects = TransitionEffects()
        
        assert effects._default_duration == 0.5

    def test_init_custom_duration(self):
        """测试自定义默认时长"""
        effects = TransitionEffects(default_duration=1.0)
        
        assert effects._default_duration == 1.0

    def test_get_ffmpeg_filter(self):
        """测试获取 FFmpeg 滤镜"""
        effects = TransitionEffects()
        
        # 测试淡入淡出滤镜
        filter_str = effects._get_ffmpeg_filter(TransitionType.FADE, 0.5)
        
        assert filter_str is not None
        assert isinstance(filter_str, str)

    def test_get_ffmpeg_filter_dissolve(self):
        """测试溶解滤镜"""
        effects = TransitionEffects()
        
        filter_str = effects._get_ffmpeg_filter(TransitionType.DISSOLVE, 0.5)
        
        assert filter_str is not None

    def test_get_ffmpeg_filter_zoom(self):
        """测试缩放滤镜"""
        effects = TransitionEffects()
        
        filter_str = effects._get_ffmpeg_filter(TransitionType.ZOOM_IN, 0.5)
        
        assert filter_str is not None

    def test_validate_duration(self):
        """测试验证时长"""
        effects = TransitionEffects()
        
        # 有效时长
        assert effects._validate_duration(0.1) == 0.1
        assert effects._validate_duration(2.0) == 2.0
        
        # 无效时长应返回默认值
        assert effects._validate_duration(-1) == 0.5
        assert effects._validate_duration(100) == 0.5
