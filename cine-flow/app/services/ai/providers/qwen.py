#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通义千问 Qwen 3.5 提供商
支持 Qwen 3.5 系列模型 (2026.02 最新)
"""

from typing import List, Dict, Any
import httpx

from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class QwenProvider(BaseLLMProvider):
    """
    通义千问提供商

    API 文档: https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope
    """

    # 可用模型列表 (2026.02 最新)
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
        },
    }

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
            return "qwen3.5"
        if model in self.MODELS:
            return model
        raise ValueError(f"Unknown model: {model}")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成文本

        Args:
            request: LLM 请求

        Returns:
            LLM 响应
        """
        model = self._get_model_name(request.model)

        # 构建消息
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

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

            # 解析响应
            if "error" in data:
                raise ProviderError(data["error"]["message"])

            choice = data["choices"][0]
            content = choice["message"]["content"]

            return LLMResponse(
                content=content,
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
        """
        批量生成文本

        Args:
            requests: LLM 请求列表

        Returns:
            LLM 响应列表
        """
        responses = []
        for request in requests:
            response = await self.generate(request)
            responses.append(response)
        return responses

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self.MODELS.keys())

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """获取模型信息"""
        return self.MODELS.get(model, {})

    def supports_vision(self, model: str) -> bool:
        """检查模型是否支持视觉"""
        model_info = self.MODELS.get(model, {})
        return model_info.get("vision", False)

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
