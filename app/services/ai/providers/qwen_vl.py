#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通义千问 Qwen-VL 提供商
支持视觉-语言多模态理解
"""

from typing import List, Dict, Any, Union, Optional
import httpx
import base64
from pathlib import Path

from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class QwenVLProvider(BaseLLMProvider):
    """
    通义千问视觉-语言提供商

    支持图像理解、视觉问答、OCR、标签生成等
    API 文档: https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-vl-api
    """

    # 可用模型列表
    MODELS = {
        "qwen-vl-plus": {
            "name": "Qwen VL Plus",
            "description": "最强视觉理解",
            "max_tokens": 4000,
            "supports_ocr": True,
        },
        "qwen-vl-max": {
            "name": "Qwen VL Max",
            "description": "高端视觉理解",
            "max_tokens": 8000,
            "supports_ocr": True,
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
            return "qwen-vl-plus"
        if model in self.MODELS:
            return model
        raise ValueError(f"Unknown VL model: {model}")

    def _encode_image(self, image_path: str) -> str:
        """
        编码图像为 Base64

        Args:
            image_path: 图像文件路径

        Returns:
            Base64 编码的图像
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: str = "default",
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        分析图像

        Args:
            image_path: 图像文件路径
            prompt: 分析提示词
            model: 模型名称
            system_prompt: 系统提示词
            **kwargs: 其他参数

        Returns:
            LLM 响应
        """
        model_name = self._get_model_name(model)

        # 编码图像
        try:
            image_base64 = self._encode_image(image_path)
        except FileNotFoundError:
            raise ProviderError(f"Image not found: {image_path}")
        except Exception as e:
            raise ProviderError(f"Failed to encode image: {str(e)}")

        # 构建消息
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 用户消息包含图像和文本
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        })

        # 调用 API
        try:
            response = await self.http_client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model_name,
                    "messages": messages,
                    "max_tokens": kwargs.get("max_tokens", 2000),
                    "temperature": kwargs.get("temperature", 0.7),
                }
            )
            response.raise_for_status()
            data = response.json()

            # 解析响应
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=model_name,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )

        except httpx.HTTPStatusError as e:
            error_msg = e.response.json().get("error", {}).get("message", str(e))
            raise ProviderError(f"API error: {error_msg}")
        except Exception as e:
            raise ProviderError(f"Request failed: {str(e)}")

    async def understand_scene(
        self,
        image_path: str,
        detail: str = "high"
    ) -> Dict[str, Any]:
        """
        理解场景内容

        Args:
            image_path: 图像路径
            detail: 详细程度 (high/medium/low)

        Returns:
            场景理解结果
        """
        prompt = (
            "请详细描述这张图片的内容，包括：\n"
            "1. 主要物体和人物\n"
            "2. 环境和背景\n"
            "3. 颜色和构图\n"
            "4. 可能的情感或氛围\n"
            "5. 适合的电影/视频风格标签（如：科幻、悬疑、喜剧等）"
        )

        response = await self.analyze_image(image_path, prompt)

        return {
            "description": response.content,
            "tokens": {
                "input": response.input_tokens,
                "output": response.output_tokens,
                "total": response.total_tokens,
            },
        }

    async def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        从图像中提取文字 (OCR)

        Args:
            image_path: 图像路径

        Returns:
            提取的文字
        """
        prompt = (
            "请识别图片中的所有文字内容，包括：\n"
            "1. 标题和字幕\n"
            "2. 标签和水印\n"
            "3. 任何可见的文字\n\n"
            "请按清晰度分类输出。"
        )

        response = await self.analyze_image(image_path, prompt)

        return {
            "text": response.content,
            "tokens": {
                "input": response.input_tokens,
                "output": response.output_tokens,
                "total": response.total_tokens,
            },
        }

    async def generate_tags(self, image_path: str) -> List[str]:
        """
        生成图像标签

        Args:
            image_path: 图像路径

        Returns:
            标签列表
        """
        prompt = (
            "请为这张图片生成 10-15 个标签，包括：\n"
            "- 主体标签（人物、物体、动物）\n"
            "- 环境标签（室内、室外、城市、自然）\n"
            "- 风格标签（科幻、复古、暗黑、明亮）\n"
            "- 情感标签（紧张、温馨、恐惧、幽默）\n\n"
            "请用逗号分隔输出。"
        )

        response = await self.analyze_image(image_path, prompt)

        # 解析标签
        tags = [tag.strip() for tag in response.content.split(",")]

        return tags

    async def subtitle_suggestion(
        self,
        image_path: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        字幕建议

        Args:
            image_path: 图像路径
            context: 上下文信息

        Returns:
            字幕建议
        """
        prompt = (
            f"根据这张图片的视觉内容，建议 2-3 句合适的台词/字幕。\n"
            f"{'上下文：' + context if context else ''}\n\n"
            "要求：\n"
            "- 符合画面氛围\n"
            "- 简洁有力\n"
            "- 可以有多种风格选项"
        )

        response = await self.analyze_image(image_path, prompt)

        return {
            "suggestions": response.content,
            "tokens": {
                "input": response.input_tokens,
                "output": response.output_tokens,
                "total": response.total_tokens,
            },
        }

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        兼容基础接口（仅文本生成）
        VL 模型主要用于视觉理解，但也可以处理文本
        """
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
                    "model": self._get_model_name(request.model),
                    "messages": messages,
                    "max_tokens": request.max_tokens or 2000,
                    "temperature": request.temperature or 0.7,
                }
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=request.model,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )

        except httpx.HTTPStatusError as e:
            error_msg = e.response.json().get("error", {}).get("message", str(e))
            raise ProviderError(f"API error: {error_msg}")
        except Exception as e:
            raise ProviderError(f"Request failed: {str(e)}")

    async def close(self):
        """关闭连接"""
        await self.http_client.aclose()
