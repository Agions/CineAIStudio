#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频摘要模块测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.ai.video_summarizer import (
    VideoSummarizer,
    SummaryStyle,
    SummaryLength,
    SummaryResult,
)


class TestSummaryStyle:
    """摘要风格测试"""
    
    def test_style_values(self):
        """测试风格枚举值"""
        assert SummaryStyle.PROFESSIONAL.value == "professional"
        assert SummaryStyle.CASUAL.value == "casual"
        assert SummaryStyle.HUMOROUS.value == "humorous"
        assert SummaryStyle.ACADEMIC.value == "academic"


class TestSummaryLength:
    """摘要长度测试"""
    
    def test_length_values(self):
        """测试长度枚举值"""
        assert SummaryLength.SHORT.value == "short"
        assert SummaryLength.MEDIUM.value == "medium"
        assert SummaryLength.LONG.value == "long"


class TestSummaryResult:
    """摘要结果测试"""
    
    def test_result_creation(self):
        """测试结果创建"""
        result = SummaryResult(
            video_path="/test/video.mp4",
            summary="这是一个测试摘要",
            highlights=["高光1", "高光2"],
            tags=["test", "video"],
            duration=120.5
        )
        
        assert result.video_path == "/test/video.mp4"
        assert result.summary == "这是一个测试摘要"
        assert len(result.highlights) == 2
        assert result.duration == 120.5
    
    def test_result_to_dict(self):
        """测试结果转字典"""
        result = SummaryResult(
            video_path="/test/video.mp4",
            summary="测试",
            highlights=[],
            tags=[],
            duration=0
        )
        
        data = result.to_dict()
        assert data["video_path"] == "/test/video.mp4"
        assert "summary" in data


class TestVideoSummarizer:
    """视频摘要测试"""
    
    @patch('app.services.ai.video_summarizer.LLMManager')
    @patch('app.services.ai.video_summarizer.VideoContentAnalyzer')
    def test_init(self, mock_analyzer, mock_llm):
        """测试初始化"""
        summarizer = VideoSummarizer(
            llm_manager=mock_llm,
            content_analyzer=mock_analyzer
        )
        
        assert summarizer.llm_manager == mock_llm
        assert summarizer.content_analyzer == mock_analyzer
    
    @patch('app.services.ai.video_summarizer.LLMManager')
    @patch('app.services.ai.video_summarizer.VideoContentAnalyzer')
    def test_summarize_default(self, mock_analyzer, mock_llm):
        """测试默认摘要"""
        mock_analyzer.return_value.analyze.return_value = {
            "summary": "测试分析",
            "keyframes": []
        }
        mock_llm.return_value.generate.return_value = "生成的摘要"
        
        summarizer = VideoSummarizer(
            llm_manager=mock_llm,
            content_analyzer=mock_analyzer
        )
        
        result = summarizer.summarize("/test.mp4")
        
        assert result is not None
        assert result.video_path == "/test.mp4"
    
    @patch('app.services.ai.video_summarizer.LLMManager')
    @patch('app.services.ai.video_summarizer.VideoContentAnalyzer')
    def test_summarize_custom_style(self, mock_analyzer, mock_llm):
        """测试自定义风格摘要"""
        summarizer = VideoSummarizer(
            llm_manager=mock_llm,
            content_analyzer=mock_analyzer
        )
        
        result = summarizer.summarize(
            video_path="/test.mp4",
            style=SummaryStyle.HUMOROUS,
            length=SummaryLength.SHORT
        )
        
        assert result is not None
    
    @patch('app.services.ai.video_summarizer.LLMManager')
    @patch('app.services.ai.video_summarizer.VideoContentAnalyzer')
    def test_extract_highlights(self, mock_analyzer, mock_llm):
        """测试提取高光时刻"""
        mock_analyzer.return_value.analyze.return_value = {
            "keyframes": [
                {"timestamp": 10, "description": "精彩时刻1"},
                {"timestamp": 50, "description": "精彩时刻2"}
            ]
        }
        
        summarizer = VideoSummarizer(
            llm_manager=mock_llm,
            content_analyzer=mock_analyzer
        )
        
        highlights = summarizer.extract_highlights("/test.mp4")
        
        assert isinstance(highlights, list)
    
    @patch('app.services.ai.video_summarizer.LLMManager')
    @patch('app.services.ai.video_summarizer.VideoContentAnalyzer')
    def test_generate_tags(self, mock_analyzer, mock_llm):
        """测试生成标签"""
        mock_analyzer.return_value.analyze.return_value = {
            "summary": "自然风景视频",
            "keyframes": []
        }
        
        summarizer = VideoSummarizer(
            llm_manager=mock_llm,
            content_analyzer=mock_analyzer
        )
        
        tags = summarizer.generate_tags("/test.mp4")
        
        assert isinstance(tags, list)
    
    @patch('app.services.ai.video_summarizer.LLMManager')
    @patch('app.services.ai.video_summarizer.VideoContentAnalyzer')
    def test_batch_summarize(self, mock_analyzer, mock_llm):
        """测试批量摘要"""
        summarizer = VideoSummarizer(
            llm_manager=mock_llm,
            content_analyzer=mock_analyzer
        )
        
        results = summarizer.batch_summarize([
            "/test1.mp4",
            "/test2.mp4"
        ])
        
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
