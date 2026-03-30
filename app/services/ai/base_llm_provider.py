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
- 速率限制器 (RateLimiter)
- 熔断器 (CircuitBreaker)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import deque
import asyncio
import httpx
import logging
import time
import hashlib
logger = logging.getLogger(__name__)


T = TypeVar("T")


# ============ 枚举定义 ============

class ProviderType(Enum):
    """LLM 提供商类型 (2026年3月最新国产模型)"""
    QWEN = "qwen"           # 阿里通义千问
    KIMI = "kimi"           # 月之暗面 Kimi
    GLM5 = "glm5"           # 智谱 GLM
    DOUBAO = "doubao"       # 字节豆包 (新增)
    HUNYUAN = "hunyuan"     # 腾讯混元 (新增)
    DEEPSEEK = "deepseek"    # 深度求索
    CLAUDE = "claude"        # Anthropic Claude
    GEMINI = "gemini"        # Google Gemini
    OPENAI = "openai"        # OpenAI
    LOCAL = "local"          # 本地模型


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


class RateLimitError(ProviderError):
    """速率限制错误"""
    pass


class CircuitOpenError(ProviderError):
    """熔断器开启错误"""
    pass


# ============ 速率限制器 ============

class RateLimiter:
    """
    令牌桶速率限制器
    防止 API 调用超出限制
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_second: int = 10,
        burst_size: int = 20
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        
        # 滑动窗口追踪
        self.minute_window: deque = deque(maxlen=requests_per_minute)
        self.second_window: deque = deque(maxlen=requests_per_second)
        
        # 令牌桶
        self.tokens = float(burst_size)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, timeout: float = 30.0) -> bool:
        """
        获取请求许可
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            是否获得许可
            
        Raises:
            RateLimitError: 超时
        """
        start_time = time.monotonic()
        
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.last_update = now
                
                # 补充令牌
                self.tokens = min(
                    self.burst_size,
                    self.tokens + elapsed * self.requests_per_second
                )
                
                # 清理分钟窗口
                cutoff = now - 60
                while self.minute_window and self.minute_window[0] < cutoff:
                    self.minute_window.popleft()
                
                # 清理秒窗口
                cutoff_sec = now - 1
                while self.second_window and self.second_window[0] < cutoff_sec:
                    self.second_window.popleft()
                
                # 检查限制
                if (len(self.minute_window) < self.requests_per_minute and
                    len(self.second_window) < self.requests_per_second and
                    self.tokens >= 1):
                    
                    # 消耗令牌
                    self.tokens -= 1
                    self.minute_window.append(now)
                    self.second_window.append(now)
                    return True
                
                # 计算等待时间
                wait_time = 1.0 / self.requests_per_second
                if self.tokens < 1:
                    wait_time = max(wait_time, (1 - self.tokens) / self.requests_per_second)
                
                if time.monotonic() - start_time + wait_time > timeout:
                    raise RateLimitError(
                        f"速率限制超时: {timeout}秒内无法获得许可"
                    )
            
            # 等待后重试
            await asyncio.sleep(wait_time)


# ============ 熔断器 ============

class CircuitState(Enum):
    CLOSED = "closed"      # 正常熔断
    OPEN = "open"         # 熔断开启
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreaker:
    """
    熔断器模式实现
    防止级联故障，快速失败
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        """
        通过熔断器执行函数
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
            
        Returns:
            函数返回值
            
        Raises:
            CircuitOpenError: 熔断器开启
        """
        async with self._lock:
            # 检查是否应该转换状态
            await self._check_state_transition()
            
            # 如果熔断开启，直接拒绝
            if self.state == CircuitState.OPEN:
                raise CircuitOpenError(
                    f"熔断器开启，请 {self.recovery_timeout:.0f}秒 后重试"
                )
        
        # 执行函数
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _check_state_transition(self):
        """检查状态转换"""
        if self.state == CircuitState.OPEN:
            # 检查是否应该进入半开状态
            if (self.last_failure_time and
                time.monotonic() - self.last_failure_time >= self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("熔断器进入半开状态")
    
    async def _on_success(self):
        """处理成功调用"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
                if self.half_open_calls >= self.half_open_max_calls:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info("熔断器关闭，恢复正常")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0
    
    async def _on_failure(self):
        """处理失败调用"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("熔断器重新开启(半开状态失败)")
            elif (self.state == CircuitState.CLOSED and
                  self.failure_count >= self.failure_threshold):
                self.state = CircuitState.OPEN
                logger.warning(f"熔断器开启(连续 {self.failure_count} 次失败)")


# ============ 请求缓存 ============

class RequestCache:
    """
    请求缓存 - 基于哈希的简单缓存
    减少重复 API 调用
    """
    
    def __init__(self, max_size: int = 1000, ttl: float = 3600.0):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry)
        self._lock = asyncio.Lock()
    
    def _make_key(self, request: LLMRequest) -> str:
        """生成缓存键"""
        content = f"{request.model}:{request.prompt[:100]}:{request.temperature}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get(self, request: LLMRequest) -> Optional[LLMResponse]:
        """获取缓存的响应"""
        key = self._make_key(request)
        
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.monotonic() < expiry:
                    logger.debug(f"缓存命中: {key[:8]}...")
                    return value
                else:
                    del self._cache[key]
        
        return None
    
    async def set(self, request: LLMRequest, response: LLMResponse):
        """缓存响应"""
        key = self._make_key(request)
        
        async with self._lock:
            # 清理过期项
            if len(self._cache) >= self.max_size:
                self._cleanup()
            
            self._cache[key] = (
                response,
                time.monotonic() + self.ttl
            )
    
    def _cleanup(self):
        """清理过期缓存"""
        now = time.monotonic()
        expired = [k for k, (_, expiry) in self._cache.items() if now >= expiry]
        for k in expired:
            del self._cache[k]
        
        # 如果还是太多，删除最老的
        if len(self._cache) >= self.max_size:
            oldest = sorted(
                self._cache.items(),
                key=lambda x: x[1][1]
            )[:len(self._cache) // 2]
            for k, _ in oldest:
                del self._cache[k]
    
    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self._cache.clear()


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

        # 安全配置：限制重定向、防超时
        self.http_client = httpx.AsyncClient(
            headers=merged_headers,
            timeout=self.timeout,
            follow_redirects=False,  # 安全：不自动重定向
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0
            )
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
            # 针对特定状态码的处理
            if e.response.status_code == 429:
                error_msg = f"速率限制: {error_msg}"
            elif e.response.status_code == 500:
                error_msg = f"服务器错误: {error_msg}"
            elif e.response.status_code == 401:
                error_msg = f"认证失败: {error_msg}"
        except Exception:
            logger.debug("无法解析错误响应")
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
        
        # 初始化安全组件
        self._rate_limiter = RateLimiter()
        self._circuit_breaker = CircuitBreaker()
        self._cache = RequestCache()

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
    "RateLimitError",
    "CircuitOpenError",
    "RateLimiter",
    "CircuitBreaker",
    "RequestCache",
    "HTTPClientMixin",
    "ModelManagerMixin",
    "BaseLLMProvider",
]
