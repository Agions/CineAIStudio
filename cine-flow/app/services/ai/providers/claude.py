#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Anthropic Claude 提供商
支持 Claude Opus 4.6 / Claude Sonnet 4.6 / Claude Haiku 4.5
"""

from typing import List, Dict, Any, Optional
import httpx
import base64
from pathlib import Path

from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude 提供商

    API 文档: https://docs.anthropic.com/claude/reference/messages_post
    """

    # 可用模型列表 (2026.02 最新)
    MODELS = {
        "claude-opus-4-6": {
            "name": "Claude Opus 4.6",
            "description": "最智能模型，适合复杂任务和 Agent",
            "max_tokens": 16384,
            "context_length": 200000,
            "vision": True,
        },
        "claude-sonnet-4-6": {
            "name": "Claude Sonnet 4.6",
            "description": "速度与智能的最佳平衡",
            "max_tokens": 16384,
            "context_length": 200000,
            "vision": True,
        },
        "claude-haiku-4-5": {
            "name": "Claude Haiku 4.5",
            "description": "最快速模型，接近前沿性能",
            "max_tokens": 8192,
            "context_length": 200000,
            "vision": True,
        },
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
    ):
        """
        初始化提供商

        Args:
            api_key: Anthropic API Key
            base_url: API 基础 URL
        """
        super().__init__(api_key, base_url)
        self.http_client = httpx.AsyncClient(
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2025-01-01",
            },
            timeout=120.0,  # Claude 可能需要更长时间
        )

    def _get_model_name(self, model: str) -> str:
        """获取模型实际名称"""
        if model == "default":
            return "claude-opus-4-6"
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
            # Claude 使用单独的 system 参数
            system = request.system_prompt
        else:
            system = None

        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": request.prompt}]
        })

        # 构建请求体
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
        }

        if system:
            payload["system"] = system

        try:
            response = await self.http_client.post(
                f"{self.base_url}/v1/messages",
                json=payload,
            )

            data = response.json()

            # 解析响应
            if "error" in data:
                raise ProviderError(data["error"]["message"])

            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=data.get("usage", {}).get("input_tokens", 0) +
                          data.get("usage", {}).get("output_tokens", 0),
                finish_reason=data.get("stop_reason", "stop"),
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

    async def generate_with_image(
        self,
        request: LLMRequest,
        image_path: str,
    ) -> LLMResponse:
        """
        带图片的生成（Vision 能力）

        Args:
            request: LLM 请求
            image_path: 图片路径

        Returns:
            LLM 响应
        """
        model = self._get_model_name(request.model)

        # 读取图片并转为 base64
        image_path = Path(image_path)
        if not image_path.exists():
            raise ProviderError(f"图片不存在: {image_path}")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # 检测图片类型
        mime_type = "image/jpeg"
        if image_path.suffix.lower() == ".png":
            mime_type = "image/png"
        elif image_path.suffix.lower() in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif image_path.suffix.lower() == ".webp":
            mime_type = "image/webp"

        # 构建消息
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data,
                    }
                },
                {
                    "type": "text",
                    "text": request.prompt,
                }
            ]
        }]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if request.system_prompt:
            payload["system"] = request.system_prompt

        try:
            response = await self.http_client.post(
                f"{self.base_url}/v1/messages",
                json=payload,
            )

            data = response.json()

            if "error" in data:
                raise ProviderError(data["error"]["message"])

            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=data.get("usage", {}).get("input_tokens", 0) +
                          data.get("usage", {}).get("output_tokens", 0),
                finish_reason=data.get("stop_reason", "stop"),
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
