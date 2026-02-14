#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ollama 提供商测试
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from app.services.ai.providers.ollama import OllamaProvider
from app.services.ai.base_LLM_provider import LLMRequest, LLMResponse, ProviderError


class TestOllamaProvider:
    """Ollama 提供商测试"""

    @pytest.fixture
    def provider(self):
        """创建提供商实例"""
        return OllamaProvider(
            base_url="http://localhost:11434"
        )

    def test_model_name_default(self, provider):
        """测试默认模型名称"""
        assert provider._get_model_name("default") == "qwen2.5"

    def test_model_name_custom(self, provider):
        """测试自定义模型名称"""
        assert provider._get_model_name("llama3.2") == "llama3.2"
        assert provider._get_model_name("mistral") == "mistral"

    def test_models_dict(self, provider):
        """测试模型字典"""
        assert "qwen2.5" in provider.MODELS
        assert "llama3.2" in provider.MODELS
        assert provider.MODELS["qwen2.5"]["name"] == "Qwen 2.5"

    @pytest.mark.asyncio
    async def test_generate_success(self, provider, monkeypatch):
        """测试生成成功"""
        # Mock httpx AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": "测试回复"
            }
        }
        mock_response.raise_for_status = MagicMock()

        mock_post = MagicMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.post = mock_post

        monkeypatch.setattr(provider, "http_client", mock_client)

        request = LLMRequest(
            prompt="测试",
            model="qwen2.5"
        )

        response = await provider.generate(request)

        assert response.content == "测试回复"
        assert response.model == "qwen2.5"
        assert response.total_tokens > 0

    @pytest.mark.asyncio
    async def test_generate_connect_error(self, provider, monkeypatch):
        """测试连接错误"""
        import httpx

        mock_post = MagicMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client = MagicMock()
        mock_client.post = mock_post

        monkeypatch.setattr(provider, "http_client", mock_client)

        request = LLMRequest(prompt="测试")

        with pytest.raises(ProviderError, match="无法连接到 Ollama 服务"):
            await provider.generate(request)

    @pytest.mark.asyncio
    async def test_list_models(self, provider, monkeypatch):
        """测试列出模型"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:latest", "size": 4294967296},
                {"name": "llama3.2:latest", "size": 2147483648}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_get = MagicMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.get = mock_get

        monkeypatch.setattr(provider, "http_client", mock_client)

        models = await provider.list_models()

        assert len(models) == 2
        assert models[0]["name"] == "qwen2.5:latest"

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, provider, monkeypatch):
        """测试包含系统提示的生成"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": "系统提示生效的回复"
            }
        }
        mock_response.raise_for_status = MagicMock()

        mock_post = MagicMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.post = mock_post

        monkeypatch.setattr(provider, "http_client", mock_client)

        request = LLMRequest(
            prompt="测试",
            system_prompt="你是一个助手"
        )

        response = await provider.generate(request)

        # 验证请求包含系统提示
        call_args = mock_post.call_args
        messages = call_args[1]["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"

    @pytest.mark.asyncio
    async def test_close(self, provider, monkeypatch):
        """测试关闭连接"""
        mock_aclose = MagicMock(return_value=asyncio.sleep(0))
        mock_client = MagicMock()
        mock_client.aclose = mock_aclose

        monkeypatch.setattr(provider, "http_client", mock_client)

        await provider.close()

        mock_aclose.assert_called_once()


def test_provider_not_available():
    """测试当 Ollama 不可用时"""
    provider = OllamaProvider(base_url="http://localhost:9999")

    assert not provider.health_check()
