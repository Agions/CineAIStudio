#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI服务管理器
管理所有AI服务的配置、调度和监控
支持国产AI模型的真实API调用和视频处理功能
"""

import json
import time
import threading
import asyncio
import queue
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, pyqtSlot
from functools import lru_cache
from datetime import datetime, timedelta
import gc
import weakref

from .base_ai_service import (
    BaseAIService, ModelInfo, ModelRequest, ModelResponse,
    ModelStatus, ModelCapability
)
from .chinese_ai_services import ChineseAIServiceFactory
from .ai_error_handler import AIErrorHandler, RetryConfig
from ..core.secure_key_manager import get_secure_key_manager
from ..core.logger import Logger


class ServiceStatus(Enum):
    """服务状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class ServiceHealth:
    """服务健康状态"""
    service_name: str
    status: ServiceStatus
    last_check: float
    response_time: float
    error_rate: float
    success_count: int
    error_count: int
    is_available: bool
    error_message: str = ""


@dataclass
class ServiceUsageStats:
    """服务使用统计"""
    service_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_cost: float
    average_response_time: float
    last_used: float


class AIServiceManager(QObject):
    """AI服务管理器"""

    # 信号定义
    service_registered = pyqtSignal(str, object)  # 服务注册
    service_unregistered = pyqtSignal(str)  # 服务注销
    service_status_changed = pyqtSignal(str, str)  # 服务状态变化
    service_health_updated = pyqtSignal(str, object)  # 服务健康状态更新
    request_started = pyqtSignal(str, str)  # 请求开始
    request_completed = pyqtSignal(str, str, object)  # 请求完成
    request_failed = pyqtSignal(str, str, str)  # 请求失败
    stats_updated = pyqtSignal(object)  # 统计数据更新
    model_configured = pyqtSignal(str, str, object)  # 模型配置完成
    configuration_error = pyqtSignal(str, str)  # 配置错误

    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = logger
        self.services: Dict[str, BaseAIService] = {}
        self.service_health: Dict[str, ServiceHealth] = {}
        self.usage_stats: Dict[str, ServiceUsageStats] = {}
        self.active_requests = weakref.WeakValueDictionary()  # request_id -> service_name (弱引用)
        self.request_callbacks = weakref.WeakValueDictionary()  # request_id -> callback (弱引用)
        self.key_manager = get_secure_key_manager()

        # 响应缓存：键为cache_key，值为(weakref.ref(response), timestamp)
        self.response_cache = {}
        self.cache_ttl = 300  # 5分钟TTL

        # 错误处理器
        self.error_handler = AIErrorHandler(self.logger)

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=10)

        # 定时器
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._perform_health_check_async)
        self.health_check_timer.start(60000)  # 增加到60秒，减少频率

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(60000)  # 60秒更新一次统计

        # 配置锁
        self.config_lock = threading.Lock()

        # 初始化
        self._initialize_services()

    def _initialize_services(self):
        """初始化服务"""
        try:
            # 注册所有国产AI服务
            for service_name in ChineseAIServiceFactory.get_available_services():
                self.register_service(service_name)

            # 加载已配置的模型
            self._load_configured_models()

            self.logger.info("AI服务管理器初始化完成")

        except Exception as e:
            self.logger.error(f"AI服务管理器初始化失败: {e}")

    def register_service(self, service_name: str) -> bool:
        """注册服务"""
        try:
            if service_name in self.services:
                return True

            # 创建服务实例
            service = ChineseAIServiceFactory.create_service(service_name)
            if not service:
                self.logger.error(f"无法创建服务: {service_name}")
                return False

            # 连接服务信号
            service.status_changed.connect(self._on_service_status_changed)
            service.request_started.connect(self._on_request_started)
            service.request_progress.connect(self._on_request_progress)
            service.request_completed.connect(self._on_request_completed)
            service.request_error.connect(self._on_request_error)
            service.model_info_loaded.connect(self._on_model_info_loaded)

            # 注册服务
            self.services[service_name] = service

            # 初始化健康状态
            self.service_health[service_name] = ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.INACTIVE,
                last_check=time.time(),
                response_time=0.0,
                error_rate=0.0,
                success_count=0,
                error_count=0,
                is_available=False
            )

            # 初始化统计信息
            self.usage_stats[service_name] = ServiceUsageStats(
                service_name=service_name,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                total_tokens=0,
                total_cost=0.0,
                average_response_time=0.0,
                last_used=0.0
            )

            self.service_registered.emit(service_name, service)
            self.logger.info(f"服务注册成功: {service_name}")
            return True

        except Exception as e:
            self.logger.error(f"注册服务失败 {service_name}: {e}")
            return False

    def unregister_service(self, service_name: str) -> bool:
        """注销服务"""
        try:
            if service_name not in self.services:
                return True

            service = self.services[service_name]
            service.cleanup()

            # 移除服务
            del self.services[service_name]
            del self.service_health[service_name]
            del self.usage_stats[service_name]

            self.service_unregistered.emit(service_name)
            self.logger.info(f"服务注销成功: {service_name}")
            return True

        except Exception as e:
            self.logger.error(f"注销服务失败 {service_name}: {e}")
            return False

    def configure_model(self, service_name: str, model_id: str, api_key: str, **kwargs) -> bool:
        """配置模型"""
        with self.config_lock:
            try:
                if service_name not in self.services:
                    self.configuration_error.emit(service_name, f"服务不存在: {service_name}")
                    return False

                service = self.services[service_name]

                # 验证API密钥格式
                if not self._validate_api_key_format(service_name, api_key):
                    self.configuration_error.emit(service_name, "API密钥格式错误")
                    return False

                # 配置模型
                success = service.configure_model(model_id, api_key, **kwargs)
                if success:
                    self.model_configured.emit(service_name, model_id, service.get_model_info(model_id))
                    self.logger.info(f"模型配置成功: {service_name}.{model_id}")
                else:
                    self.configuration_error.emit(service_name, f"配置失败: {service_name}.{model_id}")

                return success

            except Exception as e:
                error_msg = f"配置模型异常 {service_name}.{model_id}: {e}"
                self.logger.error(error_msg)
                self.configuration_error.emit(service_name, error_msg)
                return False

    def _validate_api_key_format(self, service_name: str, api_key: str) -> bool:
        """验证API密钥格式"""
        if not api_key or not api_key.strip():
            return False

        # 根据不同服务商验证格式
        if service_name == "wenxin":
            # 文心一言: client_id|client_secret
            return "|" in api_key and len(api_key.split("|")) == 2
        elif service_name == "spark":
            # 讯飞星火: api_key|api_secret
            return "|" in api_key and len(api_key.split("|")) == 2
        elif service_name in ["qwen", "glm", "baichuan", "moonshot"]:
            # 其他: 直接是API密钥
            return len(api_key) >= 16

        return True

    def send_request(self, service_name: str, model_id: str, prompt: str,
                    callback: Optional[Callable] = None, **kwargs) -> Optional[str]:
        """发送请求（带缓存）"""
        try:
            if service_name not in self.services:
                self.logger.error(f"服务不存在: {service_name}")
                return None

            service = self.services[service_name]
            if model_id not in service.get_configured_models():
                self.logger.error(f"模型未配置: {service_name}.{model_id}")
                return None

            # 检查缓存
            cache_key = f"{service_name}_{model_id}_{hash(prompt[:100])}"  # 简化hash
            now = datetime.now()
            if cache_key in self.response_cache:
                cached_response, timestamp = self.response_cache[cache_key]
                if now - timestamp < timedelta(seconds=self.cache_ttl):
                    # 缓存命中
                    self.logger.info(f"缓存命中: {cache_key}")
                    if callback:
                        callback(cached_response)
                    return cache_key  # 使用cache_key作为request_id

            # 创建请求
            request = ModelRequest(
                prompt=prompt,
                model_id=model_id,
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
                top_p=kwargs.get("top_p", 0.9),
                stream=kwargs.get("stream", False),
                system_prompt=kwargs.get("system_prompt"),
                context=kwargs.get("context"),
                metadata=kwargs.get("metadata")
            )

            # 生成请求ID
            request_id = f"{service_name}_{model_id}_{int(time.time() * 1000)}"
            self.active_requests[request_id] = service_name  # 弱引用自动管理

            if callback:
                self.request_callbacks[request_id] = callback  # 弱引用

            # 异步发送请求
            def send_async_request():
                try:
                    # 使用错误处理器执行请求
                    response = self.error_handler.execute_with_retry(
                        service.send_request,
                        service_name,
                        model_id,
                        request_id,
                        request
                    )

                    # 缓存响应
                    self.response_cache[cache_key] = (response, now)
                    # 限制缓存大小
                    if len(self.response_cache) > 100:
                        # 移除最旧
                        oldest_key = min(self.response_cache.keys(), key=lambda k: self.response_cache[k][1])
                        del self.response_cache[oldest_key]

                    # 更新统计
                    self._update_usage_stats(service_name, request, response)

                    # 调用回调（弱引用可能已过期）
                    callback_ref = self.request_callbacks.get(request_id)
                    if callback_ref:
                        try:
                            callback_ref()(response)
                        except Exception as e:
                            self.logger.error(f"回调函数执行失败: {e}")

                    # 弱引用自动清理，无需del

                except Exception as e:
                    # 处理错误
                    error_info = self.error_handler.handle_error(
                        e, service_name, model_id, request_id,
                        {"prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt}
                    )

                    self.logger.error(f"请求失败: {error_info.message}")

                    # 调用错误回调（弱引用）
                    callback_ref = self.request_callbacks.get(request_id)
                    if callback_ref:
                        try:
                            callback_ref()(None)
                        except Exception as callback_error:
                            self.logger.error(f"错误回调执行失败: {callback_error}")

                    # 弱引用自动清理

            # 提交到线程池执行
            self.executor.submit(send_async_request)

            return request_id

        except Exception as e:
            self.logger.error(f"发送请求失败: {e}")
            return None

    def cancel_request(self, request_id: str) -> bool:
        """取消请求"""
        try:
            if request_id not in self.active_requests:
                return False

            service_name = self.active_requests[request_id]
            if service_name not in self.services:
                return False

            service = self.services[service_name]
            success = service.cancel_current_request()

            # 弱引用自动清理
            return success

        except Exception as e:
            self.logger.error(f"取消请求失败: {e}")
            return False

    def test_connection(self, service_name: str, model_id: str) -> bool:
        """测试连接"""
        try:
            if service_name not in self.services:
                return False

            service = self.services[service_name]
            return service.test_connection(model_id)

        except Exception as e:
            self.logger.error(f"测试连接失败: {e}")
            return False

    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """获取服务状态"""
        return self.service_health.get(service_name)

    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """获取服务健康状态"""
        return self.service_health.get(service_name)

    def get_usage_stats(self, service_name: str) -> Optional[ServiceUsageStats]:
        """获取使用统计"""
        return self.usage_stats.get(service_name)

    def get_all_services(self) -> Dict[str, BaseAIService]:
        """获取所有服务"""
        return self.services.copy()

    def get_configured_models(self) -> Dict[str, List[str]]:
        """获取已配置的模型"""
        result = {}
        for service_name, service in self.services.items():
            configured_models = service.get_configured_models()
            if configured_models:
                result[service_name] = configured_models
        return result

    def get_available_models(self) -> Dict[str, List[str]]:
        """获取可用模型"""
        result = {}
        for service_name, service in self.services.items():
            available_models = service.get_available_models()
            if available_models:
                result[service_name] = available_models
        return result

    def get_model_info(self, service_name: str, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        if service_name not in self.services:
            return None

        service = self.services[service_name]
        return service.get_model_info(model_id)

    @lru_cache(maxsize=128)
    def estimate_cost(self, service_name: str, model_id: str, prompt: str) -> float:
        """估算成本（缓存）"""
        try:
            if service_name not in self.services:
                return 0.0

            service = self.services[service_name]
            request = ModelRequest(prompt=prompt, model_id=model_id)
            return service.estimate_cost(request)

        except Exception as e:
            self.logger.error(f"估算成本失败: {e}")
            return 0.0

    def _perform_health_check_async(self):
        """异步执行健康检查"""
        def async_check():
            try:
                for service_name, service in self.services.items():
                    if service.get_configured_models():
                        self._check_service_health(service_name)
                gc.collect()  # 清理临时对象
            except Exception as e:
                self.logger.error(f"健康检查失败: {e}")

        # 使用线程池异步执行
        self.executor.submit(async_check)

    def _check_service_health(self, service_name: str):
        """检查单个服务健康状态"""
        try:
            service = self.services[service_name]
            health = self.service_health[service_name]

            # 测试第一个配置的模型
            configured_models = service.get_configured_models()
            if not configured_models:
                health.status = ServiceStatus.INACTIVE
                health.is_available = False
                health.error_message = "未配置模型"
                self.service_health_updated.emit(service_name, health)
                return

            test_model = configured_models[0]
            start_time = time.time()

            success = service.test_connection(test_model)
            response_time = time.time() - start_time

            # 更新健康状态
            health.last_check = time.time()
            health.response_time = response_time

            if success:
                health.status = ServiceStatus.ACTIVE
                health.is_available = True
                health.success_count += 1
                health.error_message = ""
            else:
                health.status = ServiceStatus.ERROR
                health.is_available = False
                health.error_count += 1
                health.error_message = "连接测试失败"

            # 计算错误率
            total_requests = health.success_count + health.error_count
            health.error_rate = health.error_count / total_requests if total_requests > 0 else 0.0

            self.service_health_updated.emit(service_name, health)

        except Exception as e:
            self.logger.error(f"检查服务健康状态失败 {service_name}: {e}")
            health = self.service_health[service_name]
            health.status = ServiceStatus.ERROR
            health.is_available = False
            health.error_message = str(e)
            self.service_health_updated.emit(service_name, health)

    def _update_stats(self):
        """更新统计信息"""
        try:
            # 这里可以添加更详细的统计逻辑
            self.stats_updated.emit(self.usage_stats)
            gc.collect()  # 定期垃圾回收

        except Exception as e:
            self.logger.error(f"更新统计失败: {e}")

    def _update_usage_stats(self, service_name: str, request: ModelRequest, response: Optional[ModelResponse]):
        """更新使用统计"""
        try:
            stats = self.usage_stats.get(service_name)
            if not stats:
                return

            stats.total_requests += 1
            stats.last_used = time.time()

            if response:
                stats.successful_requests += 1
                stats.total_tokens += response.usage.get("total_tokens", 0)
                stats.total_cost += response.cost
                # 弱引用响应
                weak_response = weakref.ref(response)
            else:
                stats.failed_requests += 1

            # 计算平均响应时间
            if stats.total_requests > 0:
                stats.average_response_time = (
                    stats.average_response_time * (stats.total_requests - 1) +
                    (time.time() - stats.last_used)
                ) / stats.total_requests

        except Exception as e:
            self.logger.error(f"更新使用统计失败: {e}")

    def _load_configured_models(self):
        """加载已配置的模型"""
        try:
            stored_keys = self.key_manager.list_stored_keys()
            for key_name in stored_keys:
                try:
                    # 解析密钥名称格式: service_model_id
                    parts = key_name.split("_")
                    if len(parts) >= 2:
                        service_name = parts[0]
                        model_id = "_".join(parts[1:])  # 处理可能包含下划线的模型ID

                        if service_name in self.services:
                            key_data = self.key_manager.get_api_key(key_name)
                            if key_data and "api_key" in key_data:
                                self.configure_model(
                                    service_name,
                                    model_id,
                                    key_data["api_key"]
                                )

                except Exception as e:
                    self.logger.error(f"加载模型配置失败 {key_name}: {e}")

        except Exception as e:
            self.logger.error(f"加载配置的模型失败: {e}")

    def _on_service_status_changed(self, service_name: str, status: ModelStatus):
        """服务状态变化处理"""
        self.service_status_changed.emit(service_name, status.name)

    def _on_request_started(self, request_id: str):
        """请求开始处理"""
        self.request_started.emit(request_id, self.active_requests.get(request_id, ""))

    def _on_request_progress(self, request_id: str, progress: int):
        """请求进度更新"""
        # 这里可以添加进度处理逻辑
        pass

    def _on_request_completed(self, request_id: str, response: ModelResponse):
        """请求完成处理"""
        service_name = self.active_requests.get(request_id, "")
        self.request_completed.emit(request_id, service_name, response)

        # 调用回调函数（弱引用）
        callback_ref = self.request_callbacks.get(request_id)
        if callback_ref:
            try:
                callback_ref()(response)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {e}")

        # 弱引用自动清理

    def _on_request_error(self, request_id: str, error_message: str):
        """请求错误处理"""
        service_name = self.active_requests.get(request_id, "")
        self.request_failed.emit(request_id, service_name, error_message)

        # 调用回调函数（弱引用）
        callback_ref = self.request_callbacks.get(request_id)
        if callback_ref:
            try:
                callback_ref()(None)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {e}")

        # 弱引用自动清理

    def _on_model_info_loaded(self, model_id: str, model_info: ModelInfo):
        """模型信息加载完成处理"""
        # 这里可以添加模型信息处理逻辑
        pass

    def get_summary(self) -> Dict[str, Any]:
        """获取管理器摘要信息"""
        return {
            "total_services": len(self.services),
            "active_services": sum(1 for h in self.service_health.values() if h.status == ServiceStatus.ACTIVE),
            "total_requests": sum(s.total_requests for s in self.usage_stats.values()),
            "total_cost": sum(s.total_cost for s in self.usage_stats.values()),
            "total_tokens": sum(s.total_tokens for s in self.usage_stats.values()),
            "service_health": {name: health.status.value for name, health in self.service_health.items()},
            "configured_models": self.get_configured_models()
        }

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        try:
            return self.error_handler.get_error_statistics()
        except Exception as e:
            self.logger.error(f"获取错误统计失败: {e}")
            return {}

    def get_circuit_breaker_status(self) -> Dict[str, str]:
        """获取熔断器状态"""
        try:
            return self.error_handler.get_circuit_breaker_status()
        except Exception as e:
            self.logger.error(f"获取熔断器状态失败: {e}")
            return {}

    def reset_service_circuit_breaker(self, service_name: str):
        """重置服务熔断器"""
        try:
            self.error_handler.reset_circuit_breaker(service_name)
            self.logger.info(f"已重置服务 {service_name} 的熔断器")
        except Exception as e:
            self.logger.error(f"重置熔断器失败: {e}")

    def update_retry_config(self, max_retries: int = 3, base_delay: float = 1.0,
                          max_delay: float = 60.0, enable_jitter: bool = True):
        """更新重试配置"""
        try:
            from .ai_error_handler import RetryConfig
            config = RetryConfig(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                jitter=enable_jitter
            )
            self.error_handler.update_retry_config(config)
            self.logger.info("已更新重试配置")
        except Exception as e:
            self.logger.error(f"更新重试配置失败: {e}")

    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            self.health_check_timer.stop()
            self.stats_timer.stop()

            # 关闭线程池
            self.executor.shutdown(wait=True)

            # 清理所有服务
            for service in self.services.values():
                service.cleanup()

            # 清理错误处理器
            self.error_handler.clear_error_history()

            # 清理数据（弱引用自动处理）
            self.services.clear()
            self.service_health.clear()
            self.usage_stats.clear()
            self.response_cache.clear()
            gc.collect()

            self.logger.info("AI服务管理器清理完成")

        except Exception as e:
            self.logger.error(f"AI服务管理器清理失败: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()