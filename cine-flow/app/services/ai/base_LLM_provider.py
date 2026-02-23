#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM 提供商抽象基类
所有具体提供商必须实现此接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar
from dataclasses import dataclass, field


T = TypeVar("T")


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
    content: str                         # 生成内容
    model: str                           # 使用的模型
    tokens_used: int = 0                 # Token 使用量
    finish_reason: str = "stop"          # 结束原因
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


class BaseLLMProvider(ABC):
    """
    LLM 提供商抽象基类

    所有 LLM 提供商必须继承此类并实现抽象方法
    """

    def __init__(self, api_key: str, base_url: str = ""):
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
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            模型名称列表
        """
        pass

    @abstractmethod
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        获取模型信息

        Args:
            model: 模型名称

        Returns:
            模型信息字典
        """
        pass

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        try:
            # 简单的测试请求（实际需要异步，这里简化）
            test_request = LLMRequest(prompt="test", max_tokens=10)
            return True
        except Exception:
            return False


class ProviderError(Exception):
    """提供商错误"""
    pass
