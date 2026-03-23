#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频内容分析器测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.ai.video_content_analyzer import (
    VideoContentAnalyzer,
    ContentType,
    Emotion,
    VideoFrame,
    ContentAnalysisResult,
)


class TestContentType:
    """内容类型枚举测试"""
    
    def test_content_type_values(self):
        """测试内容类型枚举值"""
        assert ContentType.PERSON.value == "person"
        assert ContentType.LANDSCAPE.value == "landscape"
        assert ContentType.INDOOR.value == "indoor"
        assert ContentType.OUTDOOR.value == "outdoor"
        assert ContentType.TEXT.value == "text"
        assert ContentType.UNKNOWN.value == "unknown"
    
    def test_emotion_values(self):
        """测试情感类型枚举值"""
        assert Emotion.NEUTRAL.value == "neutral"
        assert Emotion.HAPPY.value == "happy"
        assert Emotion.SAD.value == "sad"
        assert Emotion.EXCITED.value == "excited"


class TestVideoFrame:
    """视频帧数据类测试"""
    
    def test_video_frame_creation(self):
        """测试视频帧创建"""
        frame = VideoFrame(
            timestamp=10.5,
            description="测试帧描述",
            content_types=[ContentType.PERSON],
            emotion=Emotion.HAPPY,
            ocr_text="测试文字"
        )
        
        assert frame.timestamp == 10.5
        assert frame.description == "测试帧描述"
        assert ContentType.PERSON in frame.content_types
        assert frame.emotion == Emotion.HAPPY
        assert frame.ocr_text == "测试文字"
    
    def test_video_frame_to_dict(self):
        """测试视频帧转字典"""
        frame = VideoFrame(
            timestamp=10.5,
            description="测试帧",
            content_types=[ContentType.PERSON],
            emotion=Emotion.HAPPY
        )
        
        data = frame.to_dict()
        assert data["timestamp"] == 10.5
        assert data["description"] == "测试帧"
        assert "person" in data["content_types"]


class TestContentAnalysisResult:
    """内容分析结果测试"""
    
    def test_result_creation(self):
        """测试结果创建"""
        frames = [
            VideoFrame(
                timestamp=0.0,
                description="第一帧",
                content_types=[ContentType.PERSON]
            ),
            VideoFrame(
                timestamp=10.0,
                description="第二帧",
                content_types=[ContentType.LANDSCAPE]
            )
        ]
        
        result = ContentAnalysisResult(
            video_path="/test/video.mp4",
            summary="测试视频",
            keyframes=frames,
            total_frames=100,
            duration=100.5
        )
        
        assert result.video_path == "/test/video.mp4"
        assert result.summary == "测试视频"
        assert len(result.keyframes) == 2
        assert result.total_frames == 100
    
    def test_result_to_dict(self):
        """测试结果转字典"""
        result = ContentAnalysisResult(
            video_path="/test/video.mp4",
            summary="测试",
            keyframes=[],
            total_frames=10,
            duration=10.0
        )
        
        data = result.to_dict()
        assert data["video_path"] == "/test/video.mp4"
        assert data["summary"] == "测试"
        assert data["total_frames"] == 10


class TestVideoContentAnalyzer:
    """视频内容分析器测试"""
    
    @patch('app.services.ai.video_content_analyzer.VisionProvider')
    def test_analyzer_init(self, mock_vision):
        """测试分析器初始化"""
        analyzer = VideoContentAnalyzer(vision_api_key="test-key")
        
        assert analyzer.vision_api_key == "test-key"
        assert analyzer.max_frames == 10
        assert analyzer.frame_interval == 5.0
    
    @patch('app.services.ai.video_content_analyzer.VisionProvider')
    def test_analyzer_custom_config(self, mock_vision):
        """测试自定义配置"""
        analyzer = VideoContentAnalyzer(
            vision_api_key="test-key",
            max_frames=20,
            frame_interval=3.0
        )
        
        assert analyzer.max_frames == 20
        assert analyzer.frame_interval == 3.0
    
    @patch('app.services.ai.video_content_analyzer.subprocess.run')
    @patch('app.services.ai.video_content_analyzer.VisionProvider')
    def test_extract_keyframes(self, mock_vision, mock_subprocess):
        """测试关键帧提取"""
        # 模拟 ffmpeg 输出
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="frame=100\nfps=30.0\n"
        )
        
        analyzer = VideoContentAnalyzer(vision_api_key="test-key")
        
        # 模拟视频文件存在
        with patch('os.path.exists', return_value=True):
            frames = analyzer.extract_keyframes("/test/video.mp4")
            
        # 验证调用
        mock_subprocess.assert_called()
    
    @patch('app.services.ai.video_content_analyzer.VisionProvider')
    def test_analyze_frame(self, mock_vision):
        """测试单帧分析"""
        mock_provider = Mock()
        mock_provider.analyze_image.return_value = {
            "description": "测试描述",
            "content_types": ["person"],
            "emotion": "happy"
        }
        mock_vision.return_value = mock_provider
        
        analyzer = VideoContentAnalyzer(vision_api_key="test-key")
        
        frame = VideoFrame(
            timestamp=0.0,
            description="",
            content_types=[],
            image_data=b"fake_image_data"
        )
        
        result = analyzer._analyze_frame(frame)
        
        assert "description" in result
    
    def test_detect_content_type_from_description(self):
        """测试从描述中检测内容类型"""
        analyzer = VideoContentAnalyzer(vision_api_key="test-key")
        
        # 测试人物检测
        assert ContentType.PERSON in analyzer._detect_content_type_from_description(
            "一个人站在草地上"
        )
        
        # 测试风景检测
        assert ContentType.LANDSCAPE in analyzer._detect_content_type_from_description(
            "美丽的山脉和天空"
        )
        
        # 测试室内检测
        assert ContentType.INDOOR in analyzer._detect_content_type_from_description(
            "房间内部的家具"
        )
    
    def test_detect_emotion_from_description(self):
        """测试从描述中检测情感"""
        analyzer = VideoContentAnalyzer(vision_api_key="test-key")
        
        # 测试开心
        assert analyzer._detect_emotion_from_description(
            "人们开心地笑着"
        ) == Emotion.HAPPY
        
        # 测试悲伤
        assert analyzer._detect_emotion_from_description(
            "悲伤的氛围"
        ) == Emotion.SAD
        
        # 测试平静
        assert analyzer._detect_emotion_from_description(
            "平静的湖面"
        ) == Emotion.CALM


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
