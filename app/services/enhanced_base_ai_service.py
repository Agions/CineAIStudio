#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强的基础AI服务抽象类
提供完善的错误处理、重试机制、熔断器和降级方案
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock, Event
import time
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread

from .base_ai_service import BaseAIService, ModelStatus, ModelCapability, ModelInfo, ModelRequest, ModelResponse
from .enhanced_ai_error_handler import AIErrorHandler, AIErrorType, AIErrorContext, AIErrorDetails
from ..core.logger import Logger
from ..utils.error_handler import get_global_error_handler, ErrorInfo, ErrorType, ErrorSeverity, ErrorContext as GlobalErrorContext, RecoveryAction


@dataclass
class ServiceConfig:
    """服务配置"""
    max_retries: int = 3
    base_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    timeout: float = 30.0
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    enable_fallback: bool = True
    health_check_interval: float = 30.0
    request_timeout: float = 30.0


@dataclass
class ServiceMetrics:
    """服务指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    last_request_time: float = 0.0
    uptime: float = 0.0
    error_rate: float = 0.0


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """熔断器"""

    def __init__(self, threshold: int = 5, timeout: float = 60.0):
        self.threshold = threshold
        self.timeout = timeout
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.lock = Lock()

    def call(self, func: Callable, *args, **kwargs):
        """调用函数"""
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
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
            self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """失败回调"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = CircuitBreakerState.OPEN

    def get_state(self) -> CircuitBreakerState:
        """获取状态"""
        with self.lock:
            return self.state

    def reset(self):
        """重置"""
        with self.lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.last_failure_time = 0.0


class EnhancedBaseAIService(BaseAIService):
    """增强的基础AI服务"""

    # 新增信号
    request_retried = pyqtSignal(str, int)  # 请求重试
    fallback_used = pyqtSignal(str, str)  # 使用降级服务
    circuit_breaker_triggered = pyqtSignal(str, str)  # 熔断器触发
    health_status_changed = pyqtSignal(str, bool)  # 健康状态变化
    metrics_updated = pyqtSignal(object)  # 指标更新

    def __init__(self, service_name: str, config: Optional[ServiceConfig] = None):
        super().__init__(service_name)
        self.config = config or ServiceConfig()
        self.logger = Logger(f"Enhanced{service_name}")
        self.ai_error_handler = AIErrorHandler(self.logger)
        self.global_error_handler = get_global_error_handler()

        # 服务指标
        self.metrics = ServiceMetrics()
        self.metrics_lock = Lock()

        # 熔断器
        self.circuit_breaker = CircuitBreaker(
            self.config.circuit_breaker_threshold,
            self.config.circuit_breaker_timeout
        )

        # 降级服务
        self.fallback_services: Dict[str, Callable] = {}
        self.fallback_lock = Lock()

        # 健康检查
        self.is_healthy = True
        self.last_health_check = 0.0
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._perform_health_check)
        self.health_check_timer.start(int(self.config.health_check_interval * 1000))

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=5)

        # 活跃请求
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.active_requests_lock = Lock()

        # 启动时间
        self.start_time = time.time()

    @abstractmethod
    def get_provider_name(self) -> str:
        """获取服务提供商名称"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        pass

    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        pass

    @abstractmethod
    def _send_request_internal(self, request: ModelRequest) -> ModelResponse:
        """内部发送请求方法"""
        pass

    @abstractmethod
    def _test_connection_internal(self, model_id: str) -> bool:
        """内部测试连接方法"""
        pass

    def configure_model(self, model_id: str, api_key: str, **kwargs) -> bool:
        """配置模型"""
        try:
            if not self._validate_model_config(model_id, api_key, **kwargs):
                self.logger.error(f"模型配置验证失败: {model_id}")
                return False

            # 具体的配置逻辑由子类实现
            success = self._configure_model_internal(model_id, api_key, **kwargs)
            if success:
                self.configured_models[model_id] = self.get_model_info(model_id)
                self.status = ModelStatus.CONFIGURED
                self.status_changed.emit(model_id, self.status)
                self.logger.info(f"模型配置成功: {model_id}")
            return success

        except Exception as e:
            self.logger.error(f"配置模型失败 {model_id}: {e}")
            return False

    def _configure_model_internal(self, model_id: str, api_key: str, **kwargs) -> bool:
        """内部配置模型方法"""
        # 子类需要实现具体逻辑
        return True

    def _validate_model_config(self, model_id: str, api_key: str, **kwargs) -> bool:
        """验证模型配置"""
        if not model_id or not api_key:
            return False
        if model_id not in self.get_available_models():
            return False
        return True

    def send_request(self, request: ModelRequest, callback: Optional[Callable] = None) -> Optional[str]:
        """发送请求"""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # 记录请求开始
        with self.active_requests_lock:
            self.active_requests[request_id] = {
                "request": request,
                "start_time": start_time,
                "callback": callback,
                "attempts": 0
            }

        with self.metrics_lock:
            self.metrics.total_requests += 1
            self.metrics.last_request_time = start_time

        self.request_started.emit(request_id)

        # 异步处理请求
        def process_request():
            try:
                # 使用熔断器
                if self.config.enable_circuit_breaker:
                    result = self.circuit_breaker.call(
                        self._execute_request_with_retry,
                        request_id,
                        request
                    )
                else:
                    result = self._execute_request_with_retry(request_id, request)

                # 处理成功
                self._handle_request_success(request_id, result, start_time)

                if callback:
                    callback(result)

            except Exception as e:
                # 处理失败
                self._handle_request_failure(request_id, e, start_time)

                if callback:
                    callback(None)

        # 提交到线程池
        self.executor.submit(process_request)

        return request_id

    def _execute_request_with_retry(self, request_id: str, request: ModelRequest) -> ModelResponse:
        """带重试的请求执行"""
        attempt = 0
        last_error = None

        while attempt < self.config.max_retries:
            attempt += 1

            # 更新尝试次数
            with self.active_requests_lock:
                if request_id in self.active_requests:
                    self.active_requests[request_id]["attempts"] = attempt

            self.request_retried.emit(request_id, attempt)

            try:
                # 发送请求
                response = self._send_request_internal(request)
                return response

            except Exception as e:
                last_error = e

                # 处理AI错误
                ai_context = AIErrorContext(
                    service_name=self.service_name,
                    model_id=request.model_id,
                    request_id=request_id,
                    request_payload=request.__dict__
                )

                ai_error_details = self.ai_error_handler.handle_ai_error(
                    e, self.service_name, request.model_id, "send_request", ai_context, request.__dict__
                )

                # 判断是否重试
                if not self.ai_error_handler.should_retry(ai_error_details):
                    break

                # 获取重试延迟
                delay = self.ai_error_handler.get_retry_delay(ai_error_details, attempt)
                self.logger.info(f"等待 {delay:.2f} 秒后重试第 {attempt} 次...")

                # 等待重试
                time.sleep(delay)

        # 所有重试都失败，尝试降级服务
        if self.config.enable_fallback:
            fallback_result = self._try_fallback_service(request)
            if fallback_result:
                self.fallback_used.emit(request_id, "fallback_service")
                return fallback_result

        # 所有尝试都失败
        raise last_error or Exception("请求失败")

    def _handle_request_success(self, request_id: str, response: ModelResponse, start_time: float):
        """处理请求成功"""
        # 更新指标
        processing_time = time.time() - start_time
        with self.metrics_lock:
            self.metrics.successful_requests += 1
            self.metrics.total_tokens += response.usage.get("total_tokens", 0)
            self.metrics.total_cost += response.cost

            # 更新平均响应时间
            total = self.metrics.successful_requests + self.metrics.failed_requests
            self.metrics.average_response_time = (
                self.metrics.average_response_time * (total - 1) + processing_time
            ) / total

            # 更新错误率
            self.metrics.error_rate = self.metrics.failed_requests / total if total > 0 else 0.0

        # 清理活跃请求
        with self.active_requests_lock:
            if request_id in self.active_requests:
                del self.active_requests[request_id]

        # 发送信号
        self.request_completed.emit(request_id, response)
        self.metrics_updated.emit(self.metrics)

    def _handle_request_failure(self, request_id: str, error: Exception, start_time: float):
        """处理请求失败"""
        # 更新指标
        with self.metrics_lock:
            self.metrics.failed_requests += 1
            total = self.metrics.successful_requests + self.metrics.failed_requests
            self.metrics.error_rate = self.metrics.failed_requests / total if total > 0 else 0.0

        # 清理活跃请求
        with self.active_requests_lock:
            if request_id in self.active_requests:
                del self.active_requests[request_id]

        # 发送信号
        self.request_error.emit(request_id, str(error))
        self.metrics_updated.emit(self.metrics)

    def _try_fallback_service(self, request: ModelRequest) -> Optional[ModelResponse]:
        """尝试降级服务"""
        with self.fallback_lock:
            for service_name, service_func in self.fallback_services.items():
                try:
                    self.logger.info(f"尝试降级服务: {service_name}")
                    result = service_func(request)
                    if result:
                        return result
                except Exception as e:
                    self.logger.warning(f"降级服务 {service_name} 失败: {e}")
                    continue

        return None

    def test_connection(self, model_id: str) -> bool:
        """测试连接"""
        try:
            if self.config.enable_circuit_breaker:
                return self.circuit_breaker.call(
                    self._test_connection_internal,
                    model_id
                )
            else:
                return self._test_connection_internal(model_id)

        except Exception as e:
            self.logger.error(f"测试连接失败 {model_id}: {e}")
            return False

    def cancel_request(self, request_id: str) -> bool:
        """取消请求"""
        with self.active_requests_lock:
            if request_id in self.active_requests:
                del self.active_requests[request_id]
                self.request_error.emit(request_id, "用户取消")
                return True
        return False

    def get_status(self) -> ModelStatus:
        """获取服务状态"""
        return self.status

    def get_metrics(self) -> ServiceMetrics:
        """获取服务指标"""
        with self.metrics_lock:
            # 更新运行时间
            self.metrics.uptime = time.time() - self.start_time
            return self.metrics

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "state": self.circuit_breaker.get_state().value,
            "failure_count": self.circuit_breaker.failure_count,
            "threshold": self.circuit_breaker.threshold,
            "timeout": self.circuit_breaker.timeout
        }

    def reset_circuit_breaker(self):
        """重置熔断器"""
        self.circuit_breaker.reset()
        self.logger.info("熔断器已重置")

    def _perform_health_check(self):
        """执行健康检查"""
        try:
            current_time = time.time()
            self.last_health_check = current_time

            # 检查所有配置的模型
            healthy = True
            for model_id in self.configured_models.keys():
                if not self.test_connection(model_id):
                    healthy = False
                    break

            # 更新健康状态
            if self.is_healthy != healthy:
                self.is_healthy = healthy
                self.health_status_changed.emit(self.service_name, healthy)
                self.logger.info(f"健康状态变化: {self.service_name} -> {healthy}")

        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")

    def register_fallback_service(self, name: str, service_func: Callable):
        """注册降级服务"""
        with self.fallback_lock:
            self.fallback_services[name] = service_func
            self.logger.info(f"已注册降级服务: {name}")

    def unregister_fallback_service(self, name: str):
        """注销降级服务"""
        with self.fallback_lock:
            if name in self.fallback_services:
                del self.fallback_services[name]
                self.logger.info(f"已注销降级服务: {name}")

    def get_active_requests(self) -> Dict[str, Dict[str, Any]]:
        """获取活跃请求"""
        with self.active_requests_lock:
            return self.active_requests.copy()

    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            self.health_check_timer.stop()

            # 关闭线程池
            self.executor.shutdown(wait=True)

            # 清理资源
            self.active_requests.clear()
            self.fallback_services.clear()
            self.configured_models.clear()

            self.logger.info(f"服务 {self.service_name} 清理完成")

        except Exception as e:
            self.logger.error(f"清理服务 {self.service_name} 失败: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()