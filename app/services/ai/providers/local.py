#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地 LLM 提供商
支持 Ollama、LM Studio、llama.cpp 等本地推理服务
"""

from typing import List, Dict, Any, Optional
import httpx
import json
from pathlib import Path

from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class LocalProvider(BaseLLMProvider):
    """
    本地 LLM 提供商

    支持:
    - Ollama (http://localhost:11434)
    - LM Studio (http://localhost:1234)
    - llama.cpp server (http://localhost:8080)
    - 其他 OpenAI 兼容的本地服务

    API 文档:
    - Ollama: https://github.com/ollama/ollama/blob/main/docs/api.md
    - LM Studio: https://lmstudio.ai/docs/local-server
    """

    # 常用本地模型
    COMMON_MODELS = {
        # Ollama 模型
        "llama3.2": {
            "name": "Llama 3.2",
            "description": "Meta Llama 3.2 (Ollama)",
            "max_tokens": 4096,
            "context_length": 128000,
        },
        "qwen2.5": {
            "name": "Qwen 2.5",
            "description": "阿里通义千问 2.5 (Ollama)",
            "max_tokens": 4096,
            "context_length": 128000,
        },
        "deepseek-r1": {
            "name": "DeepSeek-R1",
            "description": "DeepSeek 推理模型 (Ollama)",
            "max_tokens": 4096,
            "context_length": 128000,
        },
        "phi4": {
            "name": "Phi-4",
            "description": "Microsoft Phi-4 (Ollama)",
            "max_tokens": 4096,
            "context_length": 16000,
        },
        "gemma2": {
            "name": "Gemma 2",
            "description": "Google Gemma 2 (Ollama)",
            "max_tokens": 4096,
            "context_length": 8000,
        },
        "mistral": {
            "name": "Mistral",
            "description": "Mistral AI (Ollama)",
            "max_tokens": 4096,
            "context_length": 32000,
        },
    }

    def __init__(
        self,
        api_key: str = "",  # 本地服务通常不需要 API Key
        base_url: str = "http://localhost:11434",
        backend: str = "ollama",  # ollama, lmstudio, llamacpp, openai-compatible
    ):
        """
        初始化提供商

        Args:
            api_key: API Key（本地服务通常不需要）
            base_url: 本地服务地址
            backend: 后端类型 (ollama, lmstudio, llamacpp, openai-compatible)
        """
        super().__init__(api_key, base_url)
        self.backend = backend.lower()

        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.http_client = httpx.AsyncClient(
            headers=headers,
            timeout=300.0,  # 本地模型可能需要更长时间
        )

    def _get_model_name(self, model: str) -> str:
        """获取模型实际名称"""
        if model == "default":
            # 根据后端选择默认模型
            defaults = {
                "ollama": "llama3.2",
                "lmstudio": "local-model",
                "llamacpp": "local-model",
                "openai-compatible": "local-model",
            }
            return defaults.get(self.backend, "llama3.2")
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

        # 根据后端类型选择不同的 API 格式
        if self.backend == "ollama":
            return await self._generate_ollama(request, model)
        elif self.backend in ["lmstudio", "openai-compatible"]:
            return await self._generate_openai_compatible(request, model)
        elif self.backend == "llamacpp":
            return await self._generate_llamacpp(request, model)
        else:
            # 默认使用 Ollama 格式
            return await self._generate_ollama(request, model)

    async def _generate_ollama(
        self,
        request: LLMRequest,
        model: str,
    ) -> LLMResponse:
        """使用 Ollama API 生成"""

        # 构建提示词（包含系统提示）
        prompt = request.prompt
        if request.system_prompt:
            prompt = f"{request.system_prompt}\n\n{prompt}"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_tokens,
            },
        }

        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )

            data = response.json()

            if "error" in data:
                raise ProviderError(data["error"])

            return LLMResponse(
                content=data.get("response", ""),
                model=model,
                tokens_used=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
                finish_reason="stop" if not data.get("done", False) else "stop",
            )

        except httpx.HTTPStatusError as e:
            raise ProviderError(f"HTTP 错误: {e.response.status_code}")
        except Exception as e:
            raise ProviderError(f"生成失败: {str(e)}")

    async def _generate_openai_compatible(
        self,
        request: LLMRequest,
        model: str,
    ) -> LLMResponse:
        """使用 OpenAI 兼容 API 生成（LM Studio 等）"""

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": False,
        }

        try:
            response = await self.http_client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            )

            data = response.json()

            if "error" in data:
                raise ProviderError(data["error"]["message"])

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

    async def _generate_llamacpp(
        self,
        request: LLMRequest,
        model: str,
    ) -> LLMResponse:
        """使用 llama.cpp server API 生成"""

        # 构建提示词
        prompt = request.prompt
        if request.system_prompt:
            prompt = f"System: {request.system_prompt}\nUser: {prompt}\nAssistant:"
        else:
            prompt = f"User: {prompt}\nAssistant:"

        payload = {
            "prompt": prompt,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "n_predict": request.max_tokens,
            "stream": False,
        }

        try:
            response = await self.http_client.post(
                f"{self.base_url}/completion",
                json=payload,
            )

            data = response.json()

            if "error" in data:
                raise ProviderError(data["error"]["message"])

            return LLMResponse(
                content=data.get("content", ""),
                model=model,
                tokens_used=data.get("tokens_evaluated", 0) + data.get("tokens_predicted", 0),
                finish_reason="stop",
            )

        except httpx.HTTPStatusError as e:
            raise ProviderError(f"HTTP 错误: {e.response.status_code}")
        except Exception as e:
            raise ProviderError(f"生成失败: {str(e)}")

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        列出本地可用的模型

        Returns:
            模型列表
        """
        if self.backend == "ollama":
            try:
                response = await self.http_client.get(
                    f"{self.base_url}/api/tags"
                )
                data = response.json()
                models = data.get("models", [])
                return [
                    {
                        "name": m.get("name"),
                        "size": m.get("size"),
                        "modified_at": m.get("modified_at"),
                    }
                    for m in models
                ]
            except Exception as e:
                raise ProviderError(f"获取模型列表失败: {str(e)}")
        else:
            # 其他后端返回常用模型
            return [
                {"name": name, "description": info["description"]}
                for name, info in self.COMMON_MODELS.items()
            ]

    async def pull_model(self, model: str) -> bool:
        """
        拉取模型（仅 Ollama）

        Args:
            model: 模型名称

        Returns:
            是否成功
        """
        if self.backend != "ollama":
            raise ProviderError("仅 Ollama 支持拉取模型")

        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": False},
                timeout=600.0,  # 拉取模型可能需要很长时间
            )
            return response.status_code == 200
        except Exception as e:
            raise ProviderError(f"拉取模型失败: {str(e)}")

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
        return list(self.COMMON_MODELS.keys())

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """获取模型信息"""
        return self.COMMON_MODELS.get(model, {})

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否可用
        """
        try:
            import asyncio

            async def _check():
                if self.backend == "ollama":
                    response = await self.http_client.get(
                        f"{self.base_url}/api/tags",
                        timeout=5.0,
                    )
                else:
                    response = await self.http_client.get(
                        f"{self.base_url}/health" if self.backend == "llamacpp" else f"{self.base_url}/v1/models",
                        timeout=5.0,
                    )
                return response.status_code == 200

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_check())
            finally:
                loop.close()

        except Exception:
            return False

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
