#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kimi (月之暗面) 提供商
支持 Kimi 2.5
"""

from typing import List, Dict, Any
import httpx

from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class KimiProvider(BaseLLMProvider):
    """
    Kimi 提供商

    API 文档: https://platform.moonshot.cn/docs
    """

    MODELS = {
        "kimi-2.5": {
            "name": "Kimi 2.5",
            "description": "最新版本",
            "max_tokens": 4000,
            "context_length": 128000,
        },
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.moonshot.cn/v1",
    ):
        super().__init__(api_key, base_url)
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    def _get_model_name(self, model: str) -> str:
        """获取模型实际名称"""
        if model == "default":
            return "kimi-2.5"
        if model in self.MODELS:
            return model
        raise ValueError(f"Unknown model: {model}")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """生成文本"""
        model = self._get_model_name(request.model)

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

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
            choice = data["choices"][0]

            return LLMResponse(
                content=choice["message"]["content"],
                model=model,
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop"),
            )

        except httpx.HTTPStatusError as e:
            raise ProviderError(f"HTTP 错误: {e.response.status_code}")
        except Exception as e:
            raise ProviderError(f"生成失败: {str(e)}")

    async def generate_batch(
        self,
        requests: List[LLMRequest],
    ) -> List[LLMResponse]:
        responses = []
        for request in requests:
            responses.append(await self.generate(request))
        return responses

    def get_available_models(self) -> List[str]:
        return list(self.MODELS.keys())

    def get_model_info(self, model: str) -> Dict[str, Any]:
        return self.MODELS.get(model, {})

    async def close(self):
        await self.http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
