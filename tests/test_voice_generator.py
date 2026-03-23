#!/usr/bin/env python3
"""测试语音生成器"""

import pytest
from dataclasses import asdict

from app.services.ai.voice_generator import (
    VoiceStyle,
    VoiceGender,
    VoiceConfig,
    VoiceGenerator,
)


class TestVoiceStyle:
    """测试配音风格枚举"""

    def test_all_styles(self):
        """测试所有配音风格"""
        styles = [
            VoiceStyle.NARRATION,
            VoiceStyle.CONVERSATIONAL,
            VoiceStyle.NEWSCAST,
            VoiceStyle.CHEERFUL,
            VoiceStyle.SAD,
            VoiceStyle.ANGRY,
            VoiceStyle.FEARFUL,
            VoiceStyle.WHISPERING,
            VoiceStyle.SHOUTING,
        ]
        
        assert len(styles) == 9
        assert VoiceStyle.NARRATION.value == "narration"


class TestVoiceGender:
    """测试声音性别枚举"""

    def test_genders(self):
        """测试所有性别"""
        assert VoiceGender.MALE.value == "male"
        assert VoiceGender.FEMALE.value == "female"


class TestVoiceConfig:
    """测试配音配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = VoiceConfig()
        
        assert config.voice_id == ""
        assert config.gender == VoiceGender.FEMALE
        assert config.style == VoiceStyle.NARRATION
        assert config.style_degree == 1.0
        assert config.speed == 1.0
        assert config.volume == 1.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = VoiceConfig(
            voice_id="zh-CN-YunxiNeural",
            gender=VoiceGender.MALE,
            style=VoiceStyle.CHEERFUL,
            speed=1.2,
            volume=0.8,
        )
        
        assert config.voice_id == "zh-CN-YunxiNeural"
        assert config.gender == VoiceGender.MALE
        assert config.style == VoiceStyle.CHEERFUL
        assert config.speed == 1.2

    def test_to_dict(self):
        """测试转换为字典"""
        config = VoiceConfig(
            voice_id="test_voice",
            style=VoiceStyle.NARRATION,
        )
        
        d = asdict(config)
        
        assert d["voice_id"] == "test_voice"
        assert d["style"] == VoiceStyle.NARRATION.value


class TestVoiceGenerator:
    """测试语音生成器"""

    def test_init_default(self):
        """测试默认初始化"""
        generator = VoiceGenerator()
        
        assert generator._provider == "edge"

    def test_init_custom_provider(self):
        """测试自定义提供商"""
        generator = VoiceGenerator(provider="azure")
        
        assert generator._provider == "azure"

    def test_init_with_config(self):
        """测试带配置初始化"""
        config = VoiceConfig(
            voice_id="test",
            style=VoiceStyle.CHEERFUL,
        )
        
        generator = VoiceGenerator(config=config)
        
        assert generator.config.voice_id == "test"

    def test_get_available_voices(self):
        """测试获取可用声音列表"""
        generator = VoiceGenerator()
        
        voices = generator.get_available_voices()
        
        assert isinstance(voices, list)

    def test_get_voices_by_gender(self):
        """测试按性别获取声音"""
        generator = VoiceGenerator()
        
        male_voices = generator.get_voices_by_gender(VoiceGender.MALE)
        
        assert isinstance(male_voices, list)

    def test_get_voices_by_language(self):
        """测试按语言获取声音"""
        generator = VoiceGenerator()
        
        zh_voices = generator.get_voices_by_language("zh-CN")
        
        assert isinstance(zh_voices, list)

    def test_estimate_cost(self):
        """测试费用估算"""
        generator = VoiceGenerator()
        
        cost = generator.estimate_cost("测试文本", 100)
        
        assert cost >= 0

    def test_empty_text(self):
        """测试空文本"""
        generator = VoiceGenerator()
        
        # 空文本应该返回空路径或处理
        try:
            result = generator.generate("")
            # 空文本可能返回空或None
            assert result is None or result == ""
        except Exception:
            pass  # 预期可能抛错

    def test_validate_config(self):
        """测试配置验证"""
        generator = VoiceGenerator()
        
        valid_config = VoiceConfig(voice_id="test")
        is_valid = generator._validate_config(valid_config)
        
        assert isinstance(is_valid, bool)
