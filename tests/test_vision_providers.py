#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视觉提供商测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.ai.vision_providers import (
    VisionProvider,
    OpenAIVisionProvider,
    QwenVisionProvider,
    ClaudeVisionProvider,
)


class TestVisionProvider:
    """视觉提供商基类测试"""
    
    def test_base_class_abstract(self):
        """测试基类是抽象类"""
        with pytest.raises(TypeError):
            VisionProvider(api_key="test")
    
    def test_subclass_must_implement(self):
        """测试子类必须实现方法"""
        class IncompleteProvider(VisionProvider):
            pass
        
        with pytest.raises(TypeError):
            IncompleteProvider(api_key="test")


class TestOpenAIVisionProvider:
    """OpenAI 视觉提供商测试"""
    
    def test_init(self):
        """测试初始化"""
        provider = OpenAIVisionProvider(api_key="sk-test")
        
        assert provider.api_key == "sk-test"
        assert provider.model == "gpt-4o"
    
    def test_init_custom_model(self):
        """测试自定义模型"""
        provider = OpenAIVisionProvider(
            api_key="sk-test",
            model="gpt-4o-mini"
        )
        
        assert provider.model == "gpt-4o-mini"
    
    @patch('app.services.ai.vision_providers.OpenAI')
    def test_analyze_image(self, mock_openai):
        """测试图像分析"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='{"description": "测试", "tags": ["test"]}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        provider = OpenAIVisionProvider(api_key="sk-test")
        
        result = provider.analyze_image(b"fake_image_data")
        
        assert "description" in result or result is not None
    
    @patch('app.services.ai.vision_providers.OpenAI')
    def test_analyze_video_frame(self, mock_openai):
        """测试视频帧分析"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='测试视频帧描述'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        provider = OpenAIVisionProvider(api_key="sk-test")
        
        result = provider.analyze_video_frame(
            frame_data=b"fake_frame",
            timestamp=10.5
        )
        
        assert result is not None
    
    @patch('app.services.ai.vision_providers.OpenAI')
    def test_batch_analyze(self, mock_openai):
        """测试批量分析"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="描述1"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        provider = OpenAIVisionProvider(api_key="sk-test")
        
        results = provider.batch_analyze([
            b"image1",
            b"image2"
        ])
        
        assert isinstance(results, list)


class TestQwenVisionProvider:
    """通义千问视觉提供商测试"""
    
    def test_init(self):
        """测试初始化"""
        provider = QwenVisionProvider(api_key="test-key")
        
        assert provider.api_key == "test-key"
        assert provider.model == "qwen-vl-max"
    
    @patch('app.services.ai.vision_providers.requests.post')
    def test_analyze_image(self, mock_post):
        """测试图像分析"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": '{"description": "测试", "tags": ["test"]}'
            }
        }
        mock_post.return_value = mock_response
        
        provider = QwenVisionProvider(api_key="test-key")
        
        result = provider.analyze_image(b"fake_image")
        
        assert result is not None


class TestClaudeVisionProvider:
    """Claude 视觉提供商测试"""
    
    def test_init(self):
        """测试初始化"""
        provider = ClaudeVisionProvider(api_key="test-key")
        
        assert provider.api_key == "test-key"
    
    @patch('app.services.ai.vision_providers.anthropic.Anthropic')
    def test_analyze_image(self, mock_anthropic):
        """测试图像分析"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"description": "测试"}')]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        provider = ClaudeVisionProvider(api_key="test-key")
        
        result = provider.analyze_image(b"fake_image")
        
        assert result is not None


class TestVisionProviderFactory:
    """视觉提供商工厂测试"""
    
    def test_get_openai_provider(self):
        """测试获取 OpenAI 提供商"""
        from app.services.ai.vision_providers import get_vision_provider
        
        provider = get_vision_provider(
            "openai",
            api_key="sk-test"
        )
        
        assert isinstance(provider, OpenAIVisionProvider)
    
    def test_get_qwen_provider(self):
        """测试获取千问提供商"""
        from app.services.ai.vision_providers import get_vision_provider
        
        provider = get_vision_provider(
            "qwen",
            api_key="test"
        )
        
        assert isinstance(provider, QwenVisionProvider)
    
    def test_get_claude_provider(self):
        """测试获取 Claude 提供商"""
        from app.services.ai.vision_providers import get_vision_provider
        
        provider = get_vision_provider(
            "claude",
            api_key="test"
        )
        
        assert isinstance(provider, ClaudeVisionProvider)
    
    def test_invalid_provider(self):
        """测试无效提供商"""
        from app.services.ai.vision_providers import get_vision_provider
        
        with pytest.raises(ValueError):
            get_vision_provider("invalid", api_key="test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
