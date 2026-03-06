#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM 提供商抽象基类
所有具体提供商必须实现此接口

包含:
- 枚举定义 (ProviderType, etc.)
- 数据类 (LLMRequest, LLMResponse)
- 异常类 (ProviderError)
- 混入类 (HTTPClientMixin, ModelManagerMixin)
- 基类 (BaseLLMProvider)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar
from dataclasses import dataclass, field
from enum import Enum
import httpx


T = TypeVar("T")


# ============ 枚举定义 ============

class ProviderType(Enum):
    """LLM 提供商类型"""
    QWEN = "qwen"
    KIMI = "kimi"
    GLM5 = "glm5"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"
    LOCAL = "local"
    DEEPSEEK = "deepseek"


# ============ 数据类 ============

@dataclass
class LLMRequest:
    """LLM 请求"""
    prompt: str                          # 提示词
    system_prompt: str = ""               # 系统提示词
    model: str = "default"                # 模型名称
    max_tokens: int = 2000               # 最大生成长度
    temperature: float = 0.7              # 温度参数
    top_p: float = 0.9                   # Top-p 参数


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str                         # 生成的文本
    model: str                           # 使用的模型
    tokens_used: int = 0                # 使用的 token 数量
    finish_reason: str = "stop"          # 结束原因
    raw_response: Optional[Dict] = None  # 原始响应


# ============ 异常类 ============

class ProviderError(Exception):
    """LLM 提供商错误"""
    pass


# ============ 混入类 (Mixins) ============

class HTTPClientMixin:
    """HTTP客户端混入类 - 提供通用的HTTP请求功能"""

    def __init__(self, api_key: str, base_url: str, timeout: float = 60.0):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.http_client: Optional[httpx.AsyncClient] = None
        self._default_headers: Dict[str, str] = {}

    def _init_http_client(self, headers: Optional[Dict[str, str]] = None):
        """初始化HTTP客户端"""
        merged_headers = {**self._default_headers}
        if headers:
            merged_headers.update(headers)

        self.http_client = httpx.AsyncClient(
            headers=merged_headers,
            timeout=self.timeout,
        )

    async def _close_http_client(self):
        """关闭HTTP客户端"""
        if self.http_client:
            await self.http_client.aclose()

    def _build_messages(self, request: LLMRequest) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages

    def _parse_response(self, data: Dict[str, Any], model: str) -> LLMResponse:
        """解析标准OpenAI格式的响应"""
        if "error" in data:
            raise ProviderError(data["error"]["message"])

        # 验证响应格式
        if not data.get("choices"):
            raise ProviderError("API 响应格式错误: 缺少 choices 字段")
        
        choice = data["choices"][0]
        if not choice.get("message"):
            raise ProviderError("API 响应格式错误: 缺少 message 字段")
            
        content = choice["message"].get("content", "")

        return LLMResponse(
            content=content,
            model=model,
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    def _handle_http_error(self, e: httpx.HTTPStatusError) -> ProviderError:
        """处理HTTP错误"""
        error_msg = f"HTTP 错误: {e.response.status_code}"
        try:
            error_data = e.response.json()
            if "error" in error_data:
                error_msg = f"{error_msg} - {error_data['error']['message']}"
        except Exception:
            pass
        return ProviderError(error_msg)


class ModelManagerMixin:
    """模型管理混入类 - 提供通用的模型管理功能"""

    # 子类需要定义: MODELS, DEFAULT_MODEL
    MODELS: Dict[str, Dict[str, Any]] = {}
    DEFAULT_MODEL: str = ""

    def _get_model_name(self, model: str) -> str:
        """获取模型实际名称"""
        if model == "default":
            return self.DEFAULT_MODEL
        if model in self.MODELS:
            return model
        raise ValueError(f"Unknown model: {model}")

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

    def is_reasoning_model(self, model: str) -> bool:
        """检查是否是推理模型"""
        model_info = self.MODELS.get(model, {})
        return model_info.get("reasoning", False)


# ============ 基类 ============

class BaseLLMProvider(ABC):
    """LLM 提供商抽象基类"""

    def __init__(self, api_key: str, base_url: str):
        """
        初始化提供商

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成文本

        Args:
            request: LLM 请求

        Returns:
            LLM 响应

        Raises:
            ProviderError: 提供商错误
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        pass

    async def close(self):
        """关闭连接"""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.base_url}>"


__all__ = [
    "ProviderType",
    "LLMRequest",
    "LLMResponse",
    "ProviderError",
    "HTTPClientMixin",
    "ModelManagerMixin",
    "BaseLLMProvider",
]
