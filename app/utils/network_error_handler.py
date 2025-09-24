#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 网络请求错误处理模块
专门处理网络请求和AI API相关的错误，提供重试机制和错误恢复
"""

import time
import json
import asyncio
import aiohttp
import requests
from typing import Optional, Dict, Any, List, Union, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager

from .error_handler import (
    ErrorHandler, ErrorInfo, ErrorType, ErrorSeverity,
    RecoveryAction, ErrorContext
)


@dataclass
class NetworkRequest:
    """网络请求信息"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    data: Optional[Union[str, Dict[str, Any]]] = None
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0


@dataclass
class NetworkResponse:
    """网络响应信息"""
    success: bool
    status_code: Optional[int] = None
    data: Optional[Union[str, Dict[str, Any]]] = None
    headers: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None
    response_time: float = 0.0
    attempts: int = 1


class APIProvider(Enum):
    """AI服务提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"


class NetworkErrorType(Enum):
    """网络错误类型"""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION_ERROR = "authentication_error"
    SERVER_ERROR = "server_error"
    SSL_ERROR = "ssl_error"
    PROXY_ERROR = "proxy_error"
    NETWORK_UNAVAILABLE = "network_unavailable"


class NetworkErrorHandler(ErrorHandler):
    """网络请求错误处理器"""

    def __init__(self, logger=None):
        """初始化网络错误处理器"""
        super().__init__(logger)
        self.request_history: List[Dict[str, Any]] = []
        self.rate_limit_info: Dict[str, Dict[str, Any]] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.session_pool: Optional[aiohttp.ClientSession] = None

        # 默认配置
        self.default_timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60  # 秒

    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self.session_pool is None:
            timeout = aiohttp.ClientTimeout(total=self.default_timeout)
            self.session_pool = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session_pool:
            await self.session_pool.close()

    async def make_request(
        self,
        request: NetworkRequest,
        provider: APIProvider = APIProvider.CUSTOM,
        component: str = "NetworkRequest"
    ) -> NetworkResponse:
        """发送网络请求"""
        start_time = time.time()
        attempts = 0
        last_error = None

        # 检查断路器状态
        if self._is_circuit_open(request.url):
            error_info = ErrorInfo(
                error_type=ErrorType.NETWORK,
                severity=ErrorSeverity.HIGH,
                message=f"断路器开启，暂时不发送请求: {request.url}",
                context=ErrorContext(
                    component=component,
                    operation="circuit_breaker_check",
                    system_state={"url": request.url, "provider": provider.value}
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message="服务暂时不可用，请稍后重试"
            )
            self.handle_error(error_info)
            return NetworkResponse(
                success=False,
                error_message="Circuit breaker is open",
                attempts=0
            )

        for attempt in range(request.retry_count + 1):
            attempts = attempt + 1
            try:
                # 检查速率限制
                if self._is_rate_limited(request.url, provider):
                    await self._wait_for_rate_limit(request.url, provider)

                # 发送请求
                if self.session_pool and asyncio.get_event_loop().is_running():
                    response = await self._make_async_request(request, provider)
                else:
                    response = self._make_sync_request(request, provider)

                response_time = time.time() - start_time
                response.response_time = response_time
                response.attempts = attempts

                # 记录请求历史
                self._record_request(request, response, provider)

                # 处理响应
                if response.success:
                    # 重置断路器
                    self._reset_circuit_breaker(request.url)
                    return response
                else:
                    # 处理错误响应
                    last_error = response.error_message
                    if await self._handle_response_error(response, request.url, provider, component):
                        continue  # 重试

            except Exception as e:
                last_error = str(e)
                error_info = ErrorInfo(
                    error_type=ErrorType.NETWORK,
                    severity=ErrorSeverity.HIGH,
                    message=f"网络请求失败 (尝试 {attempts}/{request.retry_count + 1}): {request.url} - {str(e)}",
                    exception=e,
                    context=ErrorContext(
                        component=component,
                        operation="network_request",
                        system_state={"url": request.url, "method": request.method, "attempt": attempts}
                    ),
                    recovery_action=RecoveryAction.RETRY,
                    user_message="网络请求失败，正在重试..."
                )
                self.handle_error(error_info, show_dialog=False)

                # 更新断路器
                self._update_circuit_breaker(request.url, False)

                # 如果不是最后一次尝试，等待后重试
                if attempt < request.retry_count:
                    await asyncio.sleep(request.retry_delay * (attempt + 1))

        # 所有尝试都失败
        error_info = ErrorInfo(
            error_type=ErrorType.NETWORK,
            severity=ErrorSeverity.CRITICAL,
            message=f"网络请求最终失败: {request.url} - {last_error}",
            context=ErrorContext(
                component=component,
                operation="network_request_final",
                system_state={"url": request.url, "method": request.method, "total_attempts": attempts}
            ),
            recovery_action=RecoveryAction.CONTACT_SUPPORT,
            user_message="网络服务暂时不可用，请检查网络连接或稍后重试"
        )
        self.handle_error(error_info)

        return NetworkResponse(
            success=False,
            error_message=last_error or "Unknown error",
            attempts=attempts
        )

    async def _make_async_request(
        self,
        request: NetworkRequest,
        provider: APIProvider
    ) -> NetworkResponse:
        """发送异步网络请求"""
        if not self.session_pool:
            raise RuntimeError("Session pool not initialized")

        kwargs = {
            "timeout": aiohttp.ClientTimeout(total=request.timeout),
            "headers": request.headers or {}
        }

        if request.data:
            if isinstance(request.data, dict):
                kwargs["json"] = request.data
            else:
                kwargs["data"] = request.data

        async with self.session_pool.request(request.method, request.url, **kwargs) as response:
            response_data = await response.text()
            response_headers = dict(response.headers)

            if response.status >= 400:
                return NetworkResponse(
                    success=False,
                    status_code=response.status,
                    error_message=f"HTTP {response.status}: {response_data}",
                    headers=response_headers
                )

            # 尝试解析JSON
            try:
                json_data = json.loads(response_data)
                return NetworkResponse(
                    success=True,
                    status_code=response.status,
                    data=json_data,
                    headers=response_headers
                )
            except json.JSONDecodeError:
                return NetworkResponse(
                    success=True,
                    status_code=response.status,
                    data=response_data,
                    headers=response_headers
                )

    def _make_sync_request(
        self,
        request: NetworkRequest,
        provider: APIProvider
    ) -> NetworkResponse:
        """发送同步网络请求"""
        kwargs = {
            "timeout": request.timeout,
            "headers": request.headers or {}
        }

        if request.data:
            if isinstance(request.data, dict):
                kwargs["json"] = request.data
            else:
                kwargs["data"] = request.data

        response = requests.request(request.method, request.url, **kwargs)

        if response.status_code >= 400:
            return NetworkResponse(
                success=False,
                status_code=response.status_code,
                error_message=f"HTTP {response.status_code}: {response.text}",
                headers=dict(response.headers)
            )

        # 尝试解析JSON
        try:
            json_data = response.json()
            return NetworkResponse(
                success=True,
                status_code=response.status_code,
                data=json_data,
                headers=dict(response.headers)
            )
        except json.JSONDecodeError:
            return NetworkResponse(
                success=True,
                status_code=response.status_code,
                data=response.text,
                headers=dict(response.headers)
            )

    async def _handle_response_error(
        self,
        response: NetworkResponse,
        url: str,
        provider: APIProvider,
        component: str
    ) -> bool:
        """处理响应错误，返回是否应该重试"""
        if response.status_code == 429:  # Rate limit
            self._update_rate_limit(url, provider, response.headers)
            error_info = ErrorInfo(
                error_type=ErrorType.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f"API速率限制: {url}",
                context=ErrorContext(
                    component=component,
                    operation="rate_limit",
                    system_state={"url": url, "status_code": response.status_code}
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message="请求过于频繁，请稍后重试"
            )
            self.handle_error(error_info, show_dialog=False)
            return True  # 重试

        elif response.status_code >= 500:  # Server error
            error_info = ErrorInfo(
                error_type=ErrorType.NETWORK,
                severity=ErrorSeverity.HIGH,
                message=f"服务器错误: {url} - {response.status_code}",
                context=ErrorContext(
                    component=component,
                    operation="server_error",
                    system_state={"url": url, "status_code": response.status_code}
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message="服务器暂时不可用，请稍后重试"
            )
            self.handle_error(error_info, show_dialog=False)
            return True  # 重试

        elif response.status_code == 401:  # Unauthorized
            error_info = ErrorInfo(
                error_type=ErrorType.NETWORK,
                severity=ErrorSeverity.CRITICAL,
                message=f"认证失败: {url}",
                context=ErrorContext(
                    component=component,
                    operation="authentication_error",
                    system_state={"url": url, "status_code": response.status_code}
                ),
                recovery_action=RecoveryAction.CONTACT_SUPPORT,
                user_message="API认证失败，请检查配置"
            )
            self.handle_error(error_info)
            return False  # 不重试

        elif response.status_code >= 400:  # Client error
            error_info = ErrorInfo(
                error_type=ErrorType.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f"客户端错误: {url} - {response.status_code}",
                context=ErrorContext(
                    component=component,
                    operation="client_error",
                    system_state={"url": url, "status_code": response.status_code}
                ),
                recovery_action=RecoveryAction.SKIP,
                user_message="请求参数错误，请检查输入"
            )
            self.handle_error(error_info)
            return False  # 不重试

        return False

    def _is_rate_limited(self, url: str, provider: APIProvider) -> bool:
        """检查是否被速率限制"""
        rate_key = f"{provider.value}_{url}"
        if rate_key in self.rate_limit_info:
            limit_info = self.rate_limit_info[rate_key]
            if time.time() < limit_info["reset_time"]:
                return True
        return False

    def _update_rate_limit(self, url: str, provider: APIProvider, headers: Dict[str, str]) -> None:
        """更新速率限制信息"""
        rate_key = f"{provider.value}_{url}"

        # 解析速率限制头
        reset_time = time.time() + 60  # 默认1分钟
        remaining_requests = 0

        if "X-RateLimit-Reset" in headers:
            try:
                reset_time = int(headers["X-RateLimit-Reset"])
            except ValueError:
                pass

        if "X-RateLimit-Remaining" in headers:
            try:
                remaining_requests = int(headers["X-RateLimit-Remaining"])
            except ValueError:
                pass

        self.rate_limit_info[rate_key] = {
            "reset_time": reset_time,
            "remaining": remaining_requests,
            "url": url,
            "provider": provider.value
        }

    async def _wait_for_rate_limit(self, url: str, provider: APIProvider) -> None:
        """等待速率限制重置"""
        rate_key = f"{provider.value}_{url}"
        if rate_key in self.rate_limit_info:
            reset_time = self.rate_limit_info[rate_key]["reset_time"]
            wait_time = max(0, reset_time - time.time())
            if wait_time > 0:
                self.logger.info(f"等待速率限制重置: {wait_time:.1f}秒")
                await asyncio.sleep(wait_time)

    def _is_circuit_open(self, url: str) -> bool:
        """检查断路器是否开启"""
        if url in self.circuit_breakers:
            breaker = self.circuit_breakers[url]
            if breaker["state"] == "open":
                if time.time() < breaker["last_failure_time"] + self.circuit_breaker_timeout:
                    return True
                else:
                    # 超时后重置为半开状态
                    breaker["state"] = "half_open"
        return False

    def _update_circuit_breaker(self, url: str, success: bool) -> None:
        """更新断路器状态"""
        if url not in self.circuit_breakers:
            self.circuit_breakers[url] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure_time": 0
            }

        breaker = self.circuit_breakers[url]

        if success:
            breaker["failure_count"] = 0
            breaker["state"] = "closed"
        else:
            breaker["failure_count"] += 1
            breaker["last_failure_time"] = time.time()

            if breaker["failure_count"] >= self.circuit_breaker_threshold:
                breaker["state"] = "open"
                self.logger.warning(f"断路器开启: {url}")

    def _reset_circuit_breaker(self, url: str) -> None:
        """重置断路器"""
        if url in self.circuit_breakers:
            self.circuit_breakers[url]["state"] = "closed"
            self.circuit_breakers[url]["failure_count"] = 0

    def _record_request(
        self,
        request: NetworkRequest,
        response: NetworkResponse,
        provider: APIProvider
    ) -> None:
        """记录请求历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "url": request.url,
            "method": request.method,
            "provider": provider.value,
            "success": response.success,
            "status_code": response.status_code,
            "response_time": response.response_time,
            "attempts": response.attempts
        }

        self.request_history.append(record)

        # 限制历史记录大小
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]

    async def make_ai_request(
        self,
        provider: APIProvider,
        endpoint: str,
        data: Dict[str, Any],
        api_key: Optional[str] = None,
        component: str = "AIRequest"
    ) -> NetworkResponse:
        """发送AI API请求"""
        # 根据提供商构建URL和请求
        url, headers, request_data = self._build_ai_request(provider, endpoint, data, api_key)

        request = NetworkRequest(
            url=url,
            method="POST",
            headers=headers,
            data=request_data,
            timeout=60.0,  # AI请求通常需要更长时间
            retry_count=2,
            retry_delay=2.0
        )

        return await self.make_request(request, provider, component)

    def _build_ai_request(
        self,
        provider: APIProvider,
        endpoint: str,
        data: Dict[str, Any],
        api_key: Optional[str] = None
    ) -> tuple[str, Dict[str, str], Dict[str, Any]]:
        """构建AI API请求"""
        if provider == APIProvider.OPENAI:
            url = f"https://api.openai.com/v1/{endpoint}"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            return url, headers, data

        elif provider == APIProvider.ANTHROPIC:
            url = f"https://api.anthropic.com/v1/{endpoint}"
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            return url, headers, data

        elif provider == APIProvider.HUGGINGFACE:
            url = f"https://api-inference.huggingface.co/models/{endpoint}"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            return url, headers, data

        elif provider == APIProvider.LOCAL:
            url = f"http://localhost:8000/{endpoint}"
            headers = {"Content-Type": "application/json"}
            return url, headers, data

        else:
            # 自定义提供商
            url = endpoint
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return url, headers, data

    def get_network_statistics(self) -> Dict[str, Any]:
        """获取网络统计信息"""
        if not self.request_history:
            return {
                "total_requests": 0,
                "success_rate": 0,
                "average_response_time": 0,
                "providers": {}
            }

        total_requests = len(self.request_history)
        successful_requests = sum(1 for r in self.request_history if r["success"])
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        average_response_time = sum(r["response_time"] for r in self.request_history) / total_requests

        # 按提供商统计
        providers = {}
        for record in self.request_history:
            provider = record["provider"]
            if provider not in providers:
                providers[provider] = {
                    "total": 0,
                    "successful": 0,
                    "average_response_time": 0
                }

            providers[provider]["total"] += 1
            if record["success"]:
                providers[provider]["successful"] += 1

            # 计算平均响应时间
            total_time = sum(r["response_time"] for r in self.request_history if r["provider"] == provider)
            provider_total = sum(1 for r in self.request_history if r["provider"] == provider)
            providers[provider]["average_response_time"] = total_time / provider_total if provider_total > 0 else 0

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": success_rate,
            "average_response_time": average_response_time,
            "providers": providers,
            "rate_limits": self.rate_limit_info,
            "circuit_breakers": self.circuit_breakers
        }

    def clear_request_history(self) -> None:
        """清空请求历史"""
        self.request_history.clear()

    def reset_rate_limits(self) -> None:
        """重置速率限制"""
        self.rate_limit_info.clear()

    def reset_circuit_breakers(self) -> None:
        """重置断路器"""
        self.circuit_breakers.clear()


# 全局网络错误处理器实例
_global_network_error_handler: Optional[NetworkErrorHandler] = None


async def get_network_error_handler() -> NetworkErrorHandler:
    """获取全局网络错误处理器"""
    global _global_network_error_handler
    if _global_network_error_handler is None:
        _global_network_error_handler = NetworkErrorHandler()
        await _global_network_error_handler.__aenter__()
    return _global_network_error_handler


def set_network_error_handler(handler: NetworkErrorHandler) -> None:
    """设置全局网络错误处理器"""
    global _global_network_error_handler
    _global_network_error_handler = handler


@asynccontextmanager
async def network_request_context(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
    component: str = "NetworkRequest"
):
    """网络请求上下文管理器"""
    handler = await get_network_error_handler()

    request = NetworkRequest(
        url=url,
        method=method,
        headers=headers,
        data=data,
        timeout=timeout
    )

    try:
        response = await handler.make_request(request, component=component)
        yield response
    except Exception as e:
        error_info = ErrorInfo(
            error_type=ErrorType.NETWORK,
            severity=ErrorSeverity.HIGH,
            message=f"网络请求上下文错误: {str(e)}",
            exception=e,
            context=ErrorContext(
                component=component,
                operation="network_request_context",
                system_state={"url": url, "method": method}
            ),
            recovery_action=RecoveryAction.RETRY,
            user_message="网络请求失败"
        )
        handler.handle_error(error_info)
        raise