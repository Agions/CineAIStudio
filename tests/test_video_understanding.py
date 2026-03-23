#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频理解模块测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.ai.video_understanding import (
    VideoUnderstanding,
    UnderstandingLevel,
    QueryType,
    UnderstandingResult,
)


class TestUnderstandingLevel:
    """理解级别测试"""
    
    def test_level_values(self):
        """测试级别枚举值"""
        assert UnderstandingLevel.BASIC.value == "basic"
        assert UnderstandingLevel.DETAILED.value == "detailed"
        assert UnderstandingLevel.DEEP.value == "deep"


class TestQueryType:
    """查询类型测试"""
    
    def test_query_type_values(self):
        """测试查询类型枚举值"""
        assert QueryType.SUMMARY.value == "summary"
        assert QueryType.CONTENT.value == "content"
        assert QueryType.EMOTION.value == "emotion"
        assert QueryType.ACTION.value == "action"
        assert QueryType.CUSTOM.value == "custom"


class TestUnderstandingResult:
    """理解结果测试"""
    
    def test_result_creation(self):
        """测试结果创建"""
        result = UnderstandingResult(
            video_path="/test/video.mp4",
            level=UnderstandingLevel.DETAILED,
            summary="这是一个关于自然的视频",
            key_points=["要点1", "要点2"],
            tags=["nature", "landscape"],
            qa_pairs=[
                {"question": "视频主题是什么?", "answer": "自然风景"}
            ]
        )
        
        assert result.video_path == "/test/video.mp4"
        assert result.level == UnderstandingLevel.DETAILED
        assert result.summary == "这是一个关于自然的视频"
        assert len(result.key_points) == 2
        assert "nature" in result.tags
    
    def test_result_to_dict(self):
        """测试结果转字典"""
        result = UnderstandingResult(
            video_path="/test/video.mp4",
            level=UnderstandingLevel.BASIC,
            summary="测试",
            key_points=[],
            tags=[],
            qa_pairs=[]
        )
        
        data = result.to_dict()
        assert data["video_path"] == "/test/video.mp4"
        assert data["level"] == "basic"


class TestVideoUnderstanding:
    """视频理解测试"""
    
    @patch('app.services.ai.video_understanding.VideoContentAnalyzer')
    @patch('app.services.ai.video_understanding.LLMManager')
    def test_init(self, mock_llm, mock_analyzer):
        """测试初始化"""
        understanding = VideoUnderstanding(
            llm_manager=mock_llm,
            analyzer=mock_analyzer
        )
        
        assert understanding.llm_manager == mock_llm
        assert understanding.analyzer == mock_analyzer
    
    @patch('app.services.ai.video_understanding.VideoContentAnalyzer')
    @patch('app.services.ai.video_understanding.LLMManager')
    def test_understand_basic(self, mock_llm, mock_analyzer):
        """测试基础理解"""
        mock_analyzer.return_value.analyze.return_value = {
            "summary": "测试视频",
            "keyframes": []
        }
        
        understanding = VideoUnderstanding(
            llm_manager=mock_llm,
            analyzer=mock_analyzer
        )
        
        result = understanding.understand(
            video_path="/test.mp4",
            level=UnderstandingLevel.BASIC
        )
        
        assert result is not None
    
    @patch('app.services.ai.video_understanding.VideoContentAnalyzer')
    @patch('app.services.ai.video_understanding.LLMManager')
    def test_query_video(self, mock_llm, mock_analyzer):
        """测试视频查询"""
        mock_llm.return_value.generate.return_value = "测试回答"
        
        understanding = VideoUnderstanding(
            llm_manager=mock_llm,
            analyzer=mock_analyzer
        )
        
        answer = understanding.query_video(
            video_path="/test.mp4",
            question="视频主题是什么?"
        )
        
        assert answer is not None
    
    @patch('app.services.ai.video_understanding.VideoContentAnalyzer')
    @patch('app.services.ai.video_understanding.LLMManager')
    def test_extract_key_moments(self, mock_llm, mock_analyzer):
        """测试提取精彩时刻"""
        understanding = VideoUnderstanding(
            llm_manager=mock_llm,
            analyzer=mock_analyzer
        )
        
        moments = understanding.extract_key_moments("/test.mp4")
        
        assert isinstance(moments, list)
    
    @patch('app.services.ai.video_understanding.VideoContentAnalyzer')
    @patch('app.services.ai.video_understanding.LLMManager')
    def test_analyze_emotions(self, mock_llm, mock_analyzer):
        """测试情感分析"""
        understanding = VideoUnderstanding(
            llm_manager=mock_llm,
            analyzer=mock_analyzer
        )
        
        emotions = understanding.analyze_emotions("/test.mp4")
        
        assert isinstance(emotions, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
