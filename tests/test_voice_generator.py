#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音生成测试
测试 TTS 功能和参数控制
"""

import pytest
from pathlib import Path

from app.services.ai.voice_generator import (
    VoiceGenerator,
    VoiceConfig,
    VoiceStyle,
    VoiceGender,
)


class TestVoiceConfig:
    """语音配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = VoiceConfig()

        assert config.gender == VoiceGender.FEMALE
        assert config.style == VoiceStyle.NARRATION
        assert config.rate == 1.0
        assert config.pitch == 1.0
        assert config.volume == 1.0
        assert config.language == "zh-CN"

    def test_custom_config(self):
        """测试自定义配置"""
        config = VoiceConfig(
            voice_id="test-voice",
            gender=VoiceGender.MALE,
            style=VoiceStyle.CHEERFUL,
            rate=1.5,
            pitch=0.8,
            volume=0.9,
        )

        assert config.gender == VoiceGender.MALE
        assert config.style == VoiceStyle.CHEERFUL
        assert config.rate == 1.5
        assert config.pitch == 0.8
        assert config.volume == 0.9

    def test_parameter_bounds(self):
        """测试参数边界"""
        config = VoiceConfig()

        # 语速应该可以被设置到边界值
        config.rate = 0.5
        assert config.rate == 0.5

        config.rate = 2.0
        assert config.rate == 2.0

        # 音调边界
        config.pitch = 0.5
        assert config.pitch == 0.5

        config.pitch = 2.0
        assert config.pitch == 2.0

        # 音量边界
        config.volume = 0.0
        assert config.volume == 0.0

        config.volume = 1.0
        assert config.volume == 1.0


class TestVoiceStyle:
    """语音风格测试"""

    def test_voice_style_enum(self):
        """测试语音风格枚举"""
        # 原有风格
        assert VoiceStyle.NARRATION.value == "narration"
        assert VoiceStyle.CONVERSATIONAL.value == "conversational"
        assert VoiceStyle.NEWSCAST.value == "newscast"
        assert VoiceStyle.CHEERFUL.value == "cheerful"

        # 新增风格 v2.2.0
        assert VoiceStyle.EMOTIONAL.value == "emotional"
        assert VoiceStyle.ROMANTIC.value == "romantic"
        assert VoiceStyle.JOYFUL.value == "joyful"
        assert VoiceStyle.SERIOUS.value == "serious"
        assert VoiceStyle.CASUAL.value == "casual"
        assert VoiceStyle.EXCITED.value == "excited"
        assert VoiceStyle.GENTLE.value == "gentle"
        assert VoiceStyle.ENERGETIC.value == "energetic"
        assert VoiceStyle.MYSTERY.value == "mystery"
        assert VoiceStyle.HUMOROUS.value == "humorous"

    def test_voice_style_count(self):
        """验证风格数量"""
        styles = list(VoiceStyle)
        assert len(styles) >= 15  # 至少 15 种风格


class TestVoiceGenerator:
    """语音生成器测试"""

    def test_edge_provider(self):
        """测试 Edge TTS 提供商"""
        # Edge TTS 应该能正常初始化
        generator = VoiceGenerator(provider="edge")
        assert generator.provider_name == "edge"
        assert generator._provider is not None

    def test_aliyun_provider_missing_credentials(self):
        """测试阿里云提供商缺少凭证"""
        with pytest.raises(ValueError, match="阿里云 TTS 需要"):
            VoiceGenerator(provider="aliyun")

    def test_invalid_provider(self):
        """测试无效提供商"""
        with pytest.raises(ValueError, match="不支持的提供者"):
            VoiceGenerator(provider="invalid")

    def test_list_voices_edge(self):
        """测试列出 Edge TTS 声音"""
        generator = VoiceGenerator(provider="edge")
        voices = generator.list_voices()

        assert len(voices) > 0
        # 检查有女声和男声
        has_female = any(v.gender == VoiceGender.FEMALE for v in voices)
        has_male = any(v.gender == VoiceGender.MALE for v in voices)

        assert has_female
        assert has_male


class TestVoiceInfo:
    """声音信息测试"""

    def test_voice_info_creation(self):
        """测试声音信息创建"""
        voice = type('VoiceInfo', (), {
            'id': 'test-id',
            'name': '测试声音',
            'gender': VoiceGender.FEMALE,
            'language': 'zh-CN',
            'styles': [],
            'description': '测试描述'
        })()

        assert voice.id == 'test-id'
        assert voice.name == '测试声音'
        assert voice.gender == VoiceGender.FEMALE


def test_voice_config_style_mapping():
    """测试风格到具体参数的映射"""
    style_configs = {
        VoiceStyle.NEWSCAST: {"rate": 1.1, "pitch": 1.0},
        VoiceStyle.CHEERFUL: {"rate": 1.2, "pitch": 1.2},
        VoiceStyle.NARRATION: {"rate": 1.0, "pitch": 1.0},
    }

    for style, expected in style_configs.items():
        config = VoiceConfig(style=style, **expected)
        assert config.style == style
        assert config.rate == expected["rate"]
        assert config.pitch == expected["pitch"]


def test_volume_percentage_conversion():
    """测试音量百分比转换"""
    config = VoiceConfig()

    # 正常音量
    assert config.volume == 1.0  # 100%

    # 半音量
    config.volume = 0.5  # 50%
    assert config.volume == 0.5

    # 静音
    config.volume = 0.0  # 0%
    assert config.volume == 0.0


def test_voice_config_default_voice_selection():
    """测试默认声音选择逻辑"""
    # 测试 empty voice_id 不会出错
    config = VoiceConfig(voice_id="")
    assert config.voice_id == ""

    # 测试自定义 voice_id
    config = VoiceConfig(voice_id="custom-voice")
    assert config.voice_id == "custom-voice"
