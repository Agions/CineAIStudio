#!/usr/bin/env python3
"""测试字幕生成器"""

import pytest
from dataclasses import asdict

from app.services.viral_video.caption_generator import (
    CaptionStyle,
    EmotionLevel,
    Word,
    Caption,
    CaptionConfig,
    CaptionGenerator,
)


class TestCaptionStyle:
    """测试字幕样式枚举"""

    def test_all_styles(self):
        """测试所有样式"""
        styles = [
            CaptionStyle.VIRAL,
            CaptionStyle.MINIMAL,
            CaptionStyle.SUBTITLE,
            CaptionStyle.FLOATING,
        ]
        
        assert len(styles) == 4
        assert CaptionStyle.VIRAL.value == "viral"


class TestEmotionLevel:
    """测试情绪等级枚举"""

    def test_levels(self):
        """测试所有等级"""
        assert EmotionLevel.NEUTRAL.value == 0
        assert EmotionLevel.LOW.value == 1
        assert EmotionLevel.MEDIUM.value == 2
        assert EmotionLevel.HIGH.value == 3


class TestWord:
    """测试单词数据类"""

    def test_creation(self):
        """测试创建"""
        word = Word(
            text="测试",
            start_time=0.0,
            end_time=0.5,
            is_keyword=True,
            emotion=EmotionLevel.HIGH,
        )
        
        assert word.text == "测试"
        assert word.start_time == 0.0
        assert word.end_time == 0.5
        assert word.is_keyword is True
        assert word.emotion == EmotionLevel.HIGH


class TestCaption:
    """测试字幕数据类"""

    def test_creation(self):
        """测试创建"""
        words = [
            Word("测试", 0.0, 0.5, False, EmotionLevel.NEUTRAL),
        ]
        
        caption = Caption(
            text="测试",
            start_time=0.0,
            end_time=0.5,
            words=words,
            style=CaptionStyle.VIRAL,
            position="bottom",
        )
        
        assert caption.text == "测试"
        assert len(caption.words) == 1
        assert caption.style == CaptionStyle.VIRAL


class TestCaptionConfig:
    """测试字幕配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = CaptionConfig()
        
        assert config.style == CaptionStyle.VIRAL
        assert config.font_family == "PingFang SC"
        assert config.font_size == 32

    def test_custom_config(self):
        """测试自定义配置"""
        config = CaptionConfig(
            style=CaptionStyle.MINIMAL,
            font_size=24,
            color="#FFFFFF",
        )
        
        assert config.style == CaptionStyle.MINIMAL
        assert config.font_size == 24
        assert config.color == "#FFFFFF"


class TestCaptionGenerator:
    """测试字幕生成器"""

    def test_init(self):
        """测试初始化"""
        generator = CaptionGenerator()
        
        assert generator.config.style == CaptionStyle.VIRAL

    def test_init_custom_config(self):
        """测试自定义配置初始化"""
        config = CaptionConfig(
            style=CaptionStyle.SUBTITLE,
            font_size=28,
        )
        
        generator = CaptionGenerator(config)
        
        assert generator.config.style == CaptionStyle.SUBTITLE
        assert generator.config.font_size == 28

    def test_word_tokenize(self):
        """测试分词"""
        generator = CaptionGenerator()
        
        words = generator._tokenize("你好世界", 0.0, 1.0)
        
        assert len(words) > 0
        assert all(isinstance(w, Word) for w in words)

    def test_caption_style_presets(self):
        """测试字幕样式预设"""
        generator = CaptionGenerator()
        
        # 测试获取预设
        preset = generator._get_style_preset(CaptionStyle.VIRAL)
        
        assert preset is not None
        assert "font_size" in preset
        assert "animation" in preset

    def test_empty_text(self):
        """测试空文本处理"""
        generator = CaptionGenerator()
        
        result = generator.generate("")
        
        assert result == []

    def test_keyword_detection(self):
        """测试关键词检测"""
        generator = CaptionGenerator()
        
        # 测试关键词模式
        keywords = generator._detect_keywords("这是一个很棒的教程")
        
        assert len(keywords) > 0

    def test_emotion_detection(self):
        """测试情绪检测"""
        generator = CaptionGenerator()
        
        # 测试情绪词检测
        emotion = generator._detect_emotion("太棒了！")
        
        assert emotion in list(EmotionLevel)
