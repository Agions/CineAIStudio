#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Gemini 提供商
支持 Gemini 3 Flash / Gemini 3 Pro / Gemini 3.1 Pro (2026.02 最新)
"""

from typing import List, Dict, Any, Optional
import httpx
import base64
from pathlib import Path

from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini 提供商

    API 文档: https://ai.google.dev/docs
    """

    # 可用模型列表 (2026.02 最新)
    MODELS = {
        "gemini-3-flash": {
            "name": "Gemini 3 Flash",
            "description": "新一代智能，闪电般速度 (2026.02 默认模型)",
            "max_tokens": 8192,
            "context_length": 1000000,
            "vision": True,
        },
        "gemini-3.1-pro": {
            "name": "Gemini 3.1 Pro",
            "description": "最智能模型，适合复杂任务 (2026.02)",
            "max_tokens": 8192,
            "context_length": 2000000,
            "vision": True,
        },
        "gemini-3-pro": {
            "name": "Gemini 3 Pro",
            "description": "强大性能，支持超长上下文",
            "max_tokens": 8192,
            "context_length": 2000000,
            "vision": True,
        },
        "gemini-3-flash-8b": {
            "name": "Gemini 3 Flash-8B",
            "description": "轻量级模型，适合简单任务",
            "max_tokens": 8192,
            "context_length": 1000000,
            "vision": True,
        },
        "gemini-3-deep-think": {
            "name": "Gemini 3 Deep Think",
            "description": "高级推理模型，适合科学和工程 (2026.02)",
            "max_tokens": 8192,
            "context_length": 1000000,
            "vision": True,
        },
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://generativelanguage.googleapis.com",
    ):
        """
        初始化提供商

        Args:
            api_key: Google API Key
            base_url: API 基础 URL
        """
        super().__init__(api_key, base_url)
        self.http_client = httpx.AsyncClient(
            timeout=120.0,
        )

    def _get_model_name(self, model: str) -> str:
        """获取模型实际名称"""
        if model == "default":
            return "gemini-3-flash"
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

        # 构建内容
        contents = []

        # 系统提示作为第一条消息
        if request.system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System: {request.system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will follow the system instructions."}]
            })

        # 用户消息
        contents.append({
            "role": "user",
            "parts": [{"text": request.prompt}]
        })

        # 构建请求体
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
                "topP": request.top_p,
            },
        }

        try:
            response = await self.http_client.post(
                f"{self.base_url}/v1beta/models/{model}:generateContent",
                params={"key": self.api_key},
                json=payload,
            )

            data = response.json()

            # 解析响应
            if "error" in data:
                raise ProviderError(data["error"]["message"])

            # 提取内容
            candidates = data.get("candidates", [])
            if not candidates:
                raise ProviderError("No response generated")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(part.get("text", "") for part in content_parts)

            # 获取 token 使用量
            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=input_tokens + output_tokens,
                finish_reason=candidates[0].get("finishReason", "STOP"),
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
        elif image_path.suffix.lower() == ".gif":
            mime_type = "image/gif"

        # 构建内容
        contents = []

        if request.system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System: {request.system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood."}]
            })

        # 用户消息（包含图片）
        contents.append({
            "role": "user",
            "parts": [
                {
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": image_data,
                    }
                },
                {"text": request.prompt},
            ]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
                "topP": request.top_p,
            },
        }

        try:
            response = await self.http_client.post(
                f"{self.base_url}/v1beta/models/{model}:generateContent",
                params={"key": self.api_key},
                json=payload,
            )

            data = response.json()

            if "error" in data:
                raise ProviderError(data["error"]["message"])

            candidates = data.get("candidates", [])
            if not candidates:
                raise ProviderError("No response generated")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(part.get("text", "") for part in content_parts)

            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=input_tokens + output_tokens,
                finish_reason=candidates[0].get("finishReason", "STOP"),
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
