#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM 管理器
统一管理所有 LLM 提供商，支持自动切换和负载均衡
"""

from typing import Dict, Optional, List, Any
from enum import Enum

from .base_LLM_provider import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    ProviderError,
)
from .providers.qwen import QwenProvider
from .providers.kimi import KimiProvider
from .providers.glm5 import GLM5Provider
from .providers.claude import ClaudeProvider
from .providers.gemini import GeminiProvider
from .providers.local import LocalProvider
from .providers.deepseek import DeepSeekProvider


def _safe_import():
    """安全导入依赖"""
    try:
        import httpx
        return httpx
    except ImportError:
        return None


class ProviderType(Enum):
    """提供商类型"""
    QWEN = "qwen"
    KIMI = "kimi"
    GLM5 = "glm5"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"
    LOCAL = "local"
    DEEPSEEK = "deepseek"


class LLMManager:
    """
    LLM 管理器

    功能:
    1. 统一接口访问所有提供商
    2. 自动切换失败提供商
    3. 配置驱动
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化管理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.providers: Dict[ProviderType, BaseLLMProvider] = {}
        self._default_provider: Optional[ProviderType] = None

        # 初始化提供商
        self._init_providers()

    def _init_providers(self):
        """初始化所有提供商"""
        llm_config = self.config.get("LLM", {})

        # 通义千问
        qwen_config = llm_config.get("qwen", {})
        if qwen_config.get("enabled", False):
            api_key = qwen_config.get("api_key", "")
            if api_key and api_key != "${QWEN_API_KEY}":
                self.providers[ProviderType.QWEN] = QwenProvider(
                    api_key=api_key,
                    base_url=qwen_config.get("base_url", ""),
                )

        # Kimi
        kimi_config = llm_config.get("kimi", {})
        if kimi_config.get("enabled", False):
            api_key = kimi_config.get("api_key", "")
            if api_key and api_key != "${KIMI_API_KEY}":
                self.providers[ProviderType.KIMI] = KimiProvider(
                    api_key=api_key,
                    base_url=kimi_config.get("base_url", ""),
                )

        # GLM-5
        glm5_config = llm_config.get("glm5", {})
        if glm5_config.get("enabled", False):
            api_key = glm5_config.get("api_key", "")
            if api_key and api_key != "${GLM5_API_KEY}":
                self.providers[ProviderType.GLM5] = GLM5Provider(
                    api_key=api_key,
                    base_url=glm5_config.get("base_url", ""),
                )

        # Claude
        claude_config = llm_config.get("claude", {})
        if claude_config.get("enabled", False):
            api_key = claude_config.get("api_key", "")
            if api_key and api_key != "${CLAUDE_API_KEY}":
                self.providers[ProviderType.CLAUDE] = ClaudeProvider(
                    api_key=api_key,
                    base_url=claude_config.get("base_url", "https://api.anthropic.com"),
                )

        # Gemini
        gemini_config = llm_config.get("gemini", {})
        if gemini_config.get("enabled", False):
            api_key = gemini_config.get("api_key", "")
            if api_key and api_key != "${GEMINI_API_KEY}":
                self.providers[ProviderType.GEMINI] = GeminiProvider(
                    api_key=api_key,
                    base_url=gemini_config.get("base_url", "https://generativelanguage.googleapis.com"),
                )

        # 本地模型
        local_config = llm_config.get("local", {})
        if local_config.get("enabled", False):
            self.providers[ProviderType.LOCAL] = LocalProvider(
                api_key=local_config.get("api_key", ""),
                base_url=local_config.get("base_url", "http://localhost:11434"),
                backend=local_config.get("backend", "ollama"),
            )

        # DeepSeek
        deepseek_config = llm_config.get("deepseek", {})
        if deepseek_config.get("enabled", False):
            api_key = deepseek_config.get("api_key", "")
            if api_key and api_key != "${DEEPSEEK_API_KEY}":
                self.providers[ProviderType.DEEPSEEK] = DeepSeekProvider(
                    api_key=api_key,
                    base_url=deepseek_config.get("base_url", "https://api.deepseek.com"),
                )

        # 设置默认提供商
        default_name = llm_config.get("default_provider", "qwen")
        try:
            self._default_provider = ProviderType(default_name)
        except ValueError:
            if self.providers:
                self._default_provider = list(self.providers.keys())[0]
            else:
                self._default_provider = None

    async def generate(
        self,
        request: LLMRequest,
        provider: Optional[ProviderType] = None,
    ) -> LLMResponse:
        """
        生成文本

        Args:
            request: LLM 请求
            provider: 指定提供商（可选）

        Returns:
            LLM 响应
        """
        # 确定使用的提供商
        if provider and provider in self.providers:
            active_provider = self.providers[provider]
        else:
            provider = self._default_provider
            if not provider or provider not in self.providers:
                raise ProviderError("没有可用的提供商")
            active_provider = self.providers[provider]

        try:
            return await active_provider.generate(request)

        except ProviderError as e:
            # 自动切换到下一个可用的提供商
            print(f"⚠️  提供商 {provider.value} 失败: {e}")
            return await self._try_fallback(request, exclude=[provider])

    async def _try_fallback(
        self,
        request: LLMRequest,
        exclude: List[ProviderType],
    ) -> LLMResponse:
        """
        尝试备用提供商

        Args:
            request: LLM 请求
            exclude: 要排除的提供商列表

        Returns:
            LLM 响应

        Raises:
            ProviderError: 所有提供商均失败
        """
        for provider_type, provider_instance in self.providers.items():
            if provider_type not in exclude:
                try:
                    print(f"🔄 尝试备用提供商: {provider_type.value}")
                    return await provider_instance.generate(request)
                except ProviderError as e:
                    print(f"⚠️  提供商 {provider_type.value} 失败: {e}")
                    continue

        raise ProviderError("所有提供商均失败")

    def get_provider(self, provider_type: ProviderType) -> BaseLLMProvider:
        """
        获取指定提供商

        Args:
            provider_type: 提供商类型

        Returns:
            提供商实例

        Raises:
            ValueError: 提供商不可用
        """
        if provider_type not in self.providers:
            raise ValueError(f"提供商 {provider_type} 不可用")
        return self.providers[provider_type]

    def get_available_providers(self) -> List[ProviderType]:
        """
        获取可用的提供商列表

        Returns:
            提供商类型列表
        """
        return list(self.providers.keys())

    def health_check(self) -> Dict[ProviderType, bool]:
        """
        健康检查所有提供商

        Returns:
            提供商健康状态字典
        """
        results = {}
        for provider_type, provider in self.providers.items():
            results[provider_type] = provider.health_check()
        return results

    async def close_all(self):
        """关闭所有提供商的连接"""
        for provider in self.providers.values():
            if hasattr(provider, "close"):
                await provider.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_all()


def load_llm_config(config_file: str = "config/llm.yaml") -> Dict[str, Any]:
    """
    加载 LLM 配置

    Args:
        config_file: 配置文件路径

    Returns:
        配置字典
    """
    import os
    from pathlib import Path

    try:
        import yaml
    except ImportError:
        raise ImportError("需要安装 pyyaml: pip install pyyaml")

    config_path = Path(config_file)

    if not config_path.exists():
        # 返回默认配置
        return {"LLM": {"default_provider": "qwen"}}

    # 读取配置
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 替换环境变量
    def replace_env_vars(obj):
        """递归替换环境变量"""
        if isinstance(obj, dict):
            return {k: replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, str):
            if obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                return os.getenv(env_var, obj)
            return obj
        else:
            return obj

    config = replace_env_vars(config)

    return config
