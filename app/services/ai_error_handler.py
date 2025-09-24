#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI服务错误处理和重试机制
提供完善的错误处理、重试策略和降级方案
"""

import time
import json
import random
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
import logging

from ..core.logger import Logger


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    AUTH_ERROR = "auth_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorInfo:
    """错误信息"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    service_name: str
    model_id: str
    timestamp: float
    request_id: str
    retry_count: int = 0
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.NETWORK_ERROR,
        ErrorType.API_ERROR,
        ErrorType.RATE_LIMIT_ERROR,
        ErrorType.TIMEOUT_ERROR
    ])


class CircuitBreaker:
    """熔断器模式"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half_open
        self.lock = Lock()

    def call(self, func: Callable, *args, **kwargs):
        """调用函数"""
        with self.lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half_open"
                    self.failure_count = 0
                else:
                    raise Exception("熔断器开启，拒绝调用")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """成功回调"""
        with self.lock:
            self.failure_count = 0
            self.state = "closed"

    def _on_failure(self):
        """失败回调"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"

    def get_state(self) -> str:
        """获取熔断器状态"""
        with self.lock:
            return self.state


class AIErrorHandler:
    """AI服务错误处理器"""

    def __init__(self, logger: Logger):
        self.logger = logger
        self.retry_config = RetryConfig()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_history: List[ErrorInfo] = []
        self.lock = Lock()

    def handle_error(self, error: Exception, service_name: str, model_id: str,
                    request_id: str, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """处理错误"""
        try:
            # 分析错误类型
            error_type = self._analyze_error_type(error)
            severity = self._analyze_severity(error_type, error)

            # 创建错误信息
            error_info = ErrorInfo(
                error_type=error_type,
                severity=severity,
                message=str(error),
                service_name=service_name,
                model_id=model_id,
                timestamp=time.time(),
                request_id=request_id,
                context=context or {}
            )

            # 记录错误
            self._log_error(error_info)

            # 添加到历史记录
            with self.lock:
                self.error_history.append(error_info)
                # 保持最近1000条错误记录
                if len(self.error_history) > 1000:
                    self.error_history = self.error_history[-1000:]

            return error_info

        except Exception as e:
            self.logger.error(f"处理错误时发生异常: {e}")
            return ErrorInfo(
                error_type=ErrorType.UNKNOWN_ERROR,
                severity=ErrorSeverity.HIGH,
                message=str(error),
                service_name=service_name,
                model_id=model_id,
                timestamp=time.time(),
                request_id=request_id
            )

    def should_retry(self, error_info: ErrorInfo) -> bool:
        """判断是否应该重试"""
        try:
            # 检查重试次数
            if error_info.retry_count >= self.retry_config.max_retries:
                return False

            # 检查错误类型
            if error_info.error_type not in self.retry_config.retryable_errors:
                return False

            # 特殊错误类型的处理
            if error_info.error_type == ErrorType.RATE_LIMIT_ERROR:
                # 速率限制错误需要等待更长时间
                return True

            if error_info.error_type == ErrorType.AUTH_ERROR:
                # 认证错误不重试
                return False

            return True

        except Exception as e:
            self.logger.error(f"判断重试时发生异常: {e}")
            return False

    def get_retry_delay(self, error_info: ErrorInfo) -> float:
        """获取重试延迟时间"""
        try:
            # 基础延迟
            delay = self.retry_config.base_delay * (
                self.retry_config.exponential_base ** error_info.retry_count
            )

            # 特殊错误类型的延迟调整
            if error_info.error_type == ErrorType.RATE_LIMIT_ERROR:
                delay *= 3  # 速率限制错误延迟更长时间

            # 限制最大延迟
            delay = min(delay, self.retry_config.max_delay)

            # 添加抖动
            if self.retry_config.jitter:
                delay = delay * (0.5 + random.random() * 0.5)

            return delay

        except Exception as e:
            self.logger.error(f"计算重试延迟时发生异常: {e}")
            return self.retry_config.base_delay

    def execute_with_retry(self, func: Callable, service_name: str, model_id: str,
                          request_id: str, *args, **kwargs) -> Any:
        """带重试的函数执行"""
        try:
            # 获取熔断器
            circuit_breaker = self._get_circuit_breaker(service_name)

            def wrapper():
                return func(*args, **kwargs)

            # 使用熔断器调用
            return circuit_breaker.call(wrapper)

        except Exception as e:
            error_info = self.handle_error(e, service_name, model_id, request_id)

            if self.should_retry(error_info):
                # 重试逻辑
                return self._retry_execution(
                    func, error_info, service_name, model_id, request_id, *args, **kwargs
                )
            else:
                # 不重试，直接抛出异常
                raise

    def _retry_execution(self, func: Callable, error_info: ErrorInfo,
                        service_name: str, model_id: str, request_id: str,
                        *args, **kwargs) -> Any:
        """重试执行"""
        retry_count = 0
        last_error = error_info

        while retry_count < self.retry_config.max_retries:
            retry_count += 1
            error_info.retry_count = retry_count

            # 计算延迟
            delay = self.get_retry_delay(error_info)
            self.logger.info(f"等待 {delay:.2f} 秒后重试第 {retry_count} 次...")
            time.sleep(delay)

            try:
                # 重新执行
                result = func(*args, **kwargs)
                self.logger.info(f"重试第 {retry_count} 次成功")
                return result

            except Exception as e:
                last_error = self.handle_error(e, service_name, model_id, request_id)
                last_error.retry_count = retry_count

                if not self.should_retry(last_error):
                    break

                self.logger.warning(f"重试第 {retry_count} 次失败: {e}")

        # 所有重试都失败
        raise Exception(f"重试 {retry_count} 次后仍然失败: {last_error.message}")

    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """获取熔断器"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]

    def _analyze_error_type(self, error: Exception) -> ErrorType:
        """分析错误类型"""
        error_message = str(error).lower()

        if any(keyword in error_message for keyword in [
            "connection", "network", "timeout", "unreachable"
        ]):
            return ErrorType.NETWORK_ERROR

        elif any(keyword in error_message for keyword in [
            "401", "unauthorized", "authentication", "invalid key"
        ]):
            return ErrorType.AUTH_ERROR

        elif any(keyword in error_message for keyword in [
            "429", "rate limit", "too many requests", "quota"
        ]):
            return ErrorType.RATE_LIMIT_ERROR

        elif any(keyword in error_message for keyword in [
            "timeout", "time out"
        ]):
            return ErrorType.TIMEOUT_ERROR

        elif any(keyword in error_message for keyword in [
            "400", "invalid", "validation", "bad request"
        ]):
            return ErrorType.VALIDATION_ERROR

        elif any(keyword in error_message for keyword in [
            "500", "502", "503", "504", "server error"
        ]):
            return ErrorType.API_ERROR

        else:
            return ErrorType.UNKNOWN_ERROR

    def _analyze_severity(self, error_type: ErrorType, error: Exception) -> ErrorSeverity:
        """分析错误严重程度"""
        if error_type == ErrorType.AUTH_ERROR:
            return ErrorSeverity.CRITICAL
        elif error_type == ErrorType.VALIDATION_ERROR:
            return ErrorSeverity.HIGH
        elif error_type == ErrorType.RATE_LIMIT_ERROR:
            return ErrorSeverity.MEDIUM
        elif error_type in [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR]:
            return ErrorSeverity.MEDIUM
        elif error_type == ErrorType.API_ERROR:
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.MEDIUM

    def _log_error(self, error_info: ErrorInfo):
        """记录错误"""
        try:
            log_message = (
                f"AI服务错误 - "
                f"服务: {error_info.service_name}, "
                f"模型: {error_info.model_id}, "
                f"类型: {error_info.error_type.value}, "
                f"严重程度: {error_info.severity.value}, "
                f"消息: {error_info.message}, "
                f"请求ID: {error_info.request_id}"
            )

            if error_info.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                self.logger.error(log_message)
            elif error_info.severity == ErrorSeverity.MEDIUM:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)

        except Exception as e:
            self.logger.error(f"记录错误时发生异常: {e}")

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        try:
            with self.lock:
                if not self.error_history:
                    return {
                        "total_errors": 0,
                        "error_types": {},
                        "service_errors": {},
                        "recent_errors": []
                    }

                # 统计错误类型
                error_types = {}
                for error in self.error_history:
                    error_type = error.error_type.value
                    error_types[error_type] = error_types.get(error_type, 0) + 1

                # 统计服务错误
                service_errors = {}
                for error in self.error_history:
                    service = error.service_name
                    service_errors[service] = service_errors.get(service, 0) + 1

                # 最近错误
                recent_errors = [
                    {
                        "service": error.service_name,
                        "model": error.model_id,
                        "type": error.error_type.value,
                        "message": error.message,
                        "timestamp": error.timestamp
                    }
                    for error in self.error_history[-10:]
                ]

                return {
                    "total_errors": len(self.error_history),
                    "error_types": error_types,
                    "service_errors": service_errors,
                    "recent_errors": recent_errors
                }

        except Exception as e:
            self.logger.error(f"获取错误统计时发生异常: {e}")
            return {"error": str(e)}

    def get_circuit_breaker_status(self) -> Dict[str, str]:
        """获取熔断器状态"""
        try:
            return {
                service: breaker.get_state()
                for service, breaker in self.circuit_breakers.items()
            }
        except Exception as e:
            self.logger.error(f"获取熔断器状态时发生异常: {e}")
            return {}

    def reset_circuit_breaker(self, service_name: str):
        """重置熔断器"""
        try:
            if service_name in self.circuit_breakers:
                del self.circuit_breakers[service_name]
                self.logger.info(f"已重置服务 {service_name} 的熔断器")
        except Exception as e:
            self.logger.error(f"重置熔断器时发生异常: {e}")

    def clear_error_history(self):
        """清空错误历史"""
        try:
            with self.lock:
                self.error_history.clear()
                self.logger.info("已清空错误历史")
        except Exception as e:
            self.logger.error(f"清空错误历史时发生异常: {e}")

    def update_retry_config(self, config: RetryConfig):
        """更新重试配置"""
        try:
            self.retry_config = config
            self.logger.info("已更新重试配置")
        except Exception as e:
            self.logger.error(f"更新重试配置时发生异常: {e}")