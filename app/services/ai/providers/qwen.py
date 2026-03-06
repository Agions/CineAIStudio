#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通义千问 Qwen 3.5 提供商
支持 Qwen 3.5 系列模型 (2026.02 最新)

使用公共混入类减少重复代码
"""

from typing import List, Dict, Any

from ..base_LLM_provider import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    ProviderError,
    HTTPClientMixin,
    ModelManagerMixin,
)


class QwenProvider(BaseLLMProvider, HTTPClientMixin, ModelManagerMixin):
    """
    通义千问提供商

    API 文档: https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope
    """

    # 模型管理混入需要
    MODELS = {
        "qwen3.5": {
            "name": "Qwen 3.5",
            "description": "397B MoE 原生多模态模型，Agent AI 时代 (2026.02.16)",
            "max_tokens": 8000,
            "context_length": 128000,
            "vision": True,
        },
        "qwen-plus": {
            "name": "Qwen Plus",
            "description": "综合最佳模型",
            "max_tokens": 8000,
            "context_length": 32000,
        },
        "qwen3-max": {
            "name": "Qwen 3 Max",
            "description": "最强性能模型",
            "max_tokens": 8000,
            "context_length": 128000,
        },
        "qwen-flash": {
            "name": "Qwen Flash",
            "description": "超快响应模型",
            "max_tokens": 6000,
            "context_length": 32000,
        },
        "qwq-plus": {
            "name": "QwQ Plus",
            "description": "推理能力模型",
            "max_tokens": 32768,
            "context_length": 32768,
            "reasoning": True,
        },
    }
    DEFAULT_MODEL = "qwen3.5"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ):
        """
        初始化提供商

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
        """
        # 调用父类初始化
        BaseLLMProvider.__init__(self, api_key, base_url)
        HTTPClientMixin.__init__(self, api_key, base_url, timeout=60.0)

        # 初始化HTTP客户端
        self._init_http_client({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成文本

        Args:
            request: LLM 请求

        Returns:
            LLM 响应
        """
        model = self._get_model_name(request.model)

        # 使用混入类的方法构建消息
        messages = self._build_messages(request)

        # 调用 API
        try:
            response = await self.http_client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                },
            )

            data = response.json()

            # 使用混入类的方法解析响应
            return self._parse_response(data, model)

        except httpx.HTTPStatusError as e:
            raise self._handle_http_error(e)
        except Exception as e:
            raise ProviderError(f"生成失败: {str(e)}")

    async def generate_batch(
        self,
        requests: List[LLMRequest],
    ) -> List[LLMResponse]:
        """批量生成"""
        return await super().generate_batch(requests)

    async def close(self):
        """关闭 HTTP 客户端"""
        await self._close_http_client()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, _exc_val, _exc_tb):
        await self.close()


# 需要导入httpx用于类型提示
import httpx
