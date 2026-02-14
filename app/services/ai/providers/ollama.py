#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ollama 本地 LLM 提供商
支持在本地运行开源大模型
"""

from typing import List, Dict, Any
import httpx

from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class OllamaProvider(BaseLLMProvider):
    """
    Ollama 本地提供商

    支持在本地运行的多种开源模型：
    - llama2, llama3, mistral, codellama
    - qwen2, qwen2.5 (国产)
    - gemma, phi3 等

    需要先安装 Ollama: https://ollama.com
    运行模型: ollama pull qwen2.5
    启动服务: ollama serve
    """

    # 推荐模型列表
    MODELS = {
        "qwen2.5": {
            "name": "Qwen 2.5",
            "description": "国产最强开源模型",
            "max_tokens": 32768,
            "context_length": 32768,
        },
        "qwen2.5-coder": {
            "name": "Qwen 2.5 Coder",
            "description": "代码专用模型",
            "max_tokens": 32768,
            "context_length": 32768,
        },
        "llama3.2": {
            "name": "Llama 3.2",
            "description": "Meta 开源模型",
            "max_tokens": 8192,
            "context_length": 131072,
        },
        "mistral": {
            "name": "Mistral",
            "description": "轻量级模型",
            "max_tokens": 4096,
            "context_length": 8192,
        },
        "codellama": {
            "name": "Code Llama",
            "description": "代码生成模型",
            "max_tokens": 4096,
            "context_length": 16384,
        },
    }

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "http://localhost:11434",
    ):
        """
        初始化提供商

        Args:
            api_key: Ollama 不需要 API key，留空即可
            base_url: Ollama 服务地址，默认本地
        """
        super().__init__(api_key or "unused", base_url)

        # Ollama API 不需要 Authorization 头
        self.http_client = httpx.AsyncClient(
            headers={
                "Content-Type": "application/json",
            },
            timeout=120.0,  # 本地模型可能较慢
        )

    def _get_model_name(self, model: str) -> str:
        """获取模型实际名称"""
        if model == "default":
            return "qwen2.5"
        if model in self.MODELS:
            return model
        # 也可以使用任何已安装的模型
        return model

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

        # 调用 Ollama API
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": request.max_tokens or 2000,
                        "temperature": request.temperature or 0.7,
                        "top_p": request.top_p or 0.9,
                    },
                }
            )
            response.raise_for_status()
            data = response.json()

            # 解析响应
            content = data["message"]["content"]

            # Ollama 的 token 计数需要额外获取或估算
            # 这里简化处理
            input_tokens = len(request.prompt.encode("utf-8")) // 4
            output_tokens = len(content.encode("utf-8")) // 4

            return LLMResponse(
                content=content,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            )

        except httpx.ConnectError:
            raise ProviderError(
                "无法连接到 Ollama 服务。"
                "\n请确保 Ollama 已安装并运行: ollama serve"
                "\n下载模型: ollama pull qwen2.5"
            )
        except httpx.HTTPStatusError as e:
            error_msg = e.response.json().get("error", str(e))
            raise ProviderError(f"Ollama API error: {error_msg}")
        except Exception as e:
            raise ProviderError(f"Request failed: {str(e)}")

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        列出已安装的模型

        Returns:
            模型列表
        """
        try:
            response = await self.http_client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("models", []):
                models.append({
                    "name": model["name"],
                    "size": model.get("size", 0),
                    "modified": model.get("modified_at", ""),
                })

            return models

        except Exception as e:
            raise ProviderError(f"Failed to list models: {str(e)}")

    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """
        下载模型

        Args:
            model_name: 模型名称

        Returns:
            下载进度
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name, "stream": True},
            )
            response.raise_for_status()

            # Ollama pull 返回流式响应
            # 这里简化处理，实际应该处理流
            return {"status": "downloading", "model": model_name}

        except Exception as e:
            raise ProviderError(f"Failed to pull model: {str(e)}")

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否可用
        """
        try:
            # 使用同步方法检查（简化）
            import httpx as sync_httpx
            response = sync_httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    async def is_model_available(self, model_name: str) -> bool:
        """
        检查模型是否已安装

        Args:
            model_name: 模型名称

        Returns:
            模型是否可用
        """
        try:
            models = await self.list_models()
            return any(m["name"].startswith(model_name) for m in models)
        except:
            return False

    async def close(self):
        """关闭连接"""
        await self.http_client.aclose()
