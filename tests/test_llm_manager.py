#!/usr/bin/env python3
"""测试 LLM 管理器"""

import pytest
from unittest.mock import Mock, patch

from app.services.ai.llm_manager import LLMManager


class TestLLMManager:
    """测试 LLM 管理器"""

    def test_init_default(self):
        """测试默认初始化"""
        config = {"default_provider": "openai"}
        
        with patch('app.services.ai.llm_manager.QwenProvider'):
            manager = LLMManager(config)
            
            assert manager.config == config

    def test_init_providers(self):
        """测试初始化提供商"""
        config = {
            "default_provider": "qwen",
            "qwen": {"api_key": "test_key"}
        }
        
        with patch('app.services.ai.llm_manager.QwenProvider') as mock_qwen:
            mock_provider = Mock()
            mock_qwen.return_value = mock_provider
            
            manager = LLMManager(config)
            
            # 验证提供商被创建
            mock_qwen.assert_called()

    def test_get_provider(self):
        """测试获取提供商"""
        config = {"default_provider": "qwen"}
        
        with patch('app.services.ai.llm_manager.QwenProvider'):
            manager = LLMManager(config)
            
            # 获取提供商
            provider = manager.get_provider("qwen")
            
            assert provider is not None

    def test_get_default_provider(self):
        """测试获取默认提供商"""
        config = {"default_provider": "kimi"}
        
        with patch('app.services.ai.llm_manager.KimiProvider'):
            manager = LLMManager(config)
            
            provider = manager.get_default_provider()
            
            assert provider is not None

    def test_set_default_provider(self):
        """测试设置默认提供商"""
        config = {"default_provider": "qwen"}
        
        with patch('app.services.ai.llm_manager.QwenProvider'):
            manager = LLMManager(config)
            
            # 切换默认提供商
            manager.set_default_provider("kimi")
            
            assert manager._default_provider.value == "kimi"

    def test_list_providers(self):
        """测试列出可用提供商"""
        config = {"default_provider": "qwen"}
        
        with patch('app.services.ai.llm_manager.QwenProvider'):
            with patch('app.services.ai.llm_manager.KimiProvider'):
                manager = LLMManager(config)
                
                providers = manager.list_providers()
                
                assert isinstance(providers, list)

    def test_validate_provider_config(self):
        """测试验证提供商配置"""
        config = {"default_provider": "qwen"}
        
        with patch('app.services.ai.llm_manager.QwenProvider'):
            manager = LLMManager(config)
            
            # 验证有效配置
            result = manager.validate_provider_config("qwen", {"api_key": "test"})
            assert result is True
            
            # 验证无效配置
            result = manager.validate_provider_config("qwen", {})
            assert result is False
