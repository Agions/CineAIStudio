#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek 提供商
支持 DeepSeek Chat 和 DeepSeek Coder 系列模型
"""

from typing import List, Dict, Any
import httpx

from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek 提供商

    API 文档: https://platform.deepseek.com/docs
    """

    # 可用模型列表
    MODELS = {
        "deepseek-chat": {
            "name": "DeepSeek Chat",
            "description": "通用对话模型",
            "max_tokens": 4096,
            "context_length": 64000,
        },
        "deepseek-coder": {
            "name": "DeepSeek Coder",
            "description": "代码生成模型",
            "max_tokens": 4096,
            "context_length": 16000,
        },
        "deepseek-math": {
            "name": "DeepSeek Math",
            "description": "数学推理模型",
            "max_tokens": 4096,
            "context_length": 64000,
        },
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
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
            return "deepseek-chat"
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
            error_msg = f"HTTP 错误: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_msg = f"{error_msg} - {error_data['error']['message']}"
            except Exception:
                pass
            raise ProviderError(error_msg)
        except Exception as e:
            raise ProviderError(f"生成失败: {str(e)}")

    async def generate_batch(
        self,
        requests: List[LLMRequest],
    ) -> List[LLMResponse]:
        """批量生成"""
        return await super().generate_batch(requests)

    async def count_tokens(self, text: str) -> int:
        """计算 token 数量（估算）"""
        # 简单估算：中文约 1.5 token/字符，英文约 0.25 token/字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars * 0.25)

    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self.MODELS.keys())

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                },
            )
            return response.status_code == 200
        except Exception:
            return False
