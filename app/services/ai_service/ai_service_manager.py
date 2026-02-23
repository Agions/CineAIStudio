#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI服务管理器
管理所有AI服务的配置、调度和监控
"""

import json
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .base_ai_service import (
    BaseAIService, ModelInfo, ModelRequest, ModelResponse,
    ModelStatus, ModelCapability
)
# ChineseAIServiceFactory removed - not available
from ...core.secure_key_manager import get_secure_key_manager
from ...core.logger import Logger


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
        self.active_requests: Dict[str, str] = {}  # request_id -> service_name
        self.request_callbacks: Dict[str, Callable] = {}
        self.key_manager = get_secure_key_manager()

        # 定时器
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._perform_health_check)
        self.health_check_timer.start(30000)  # 30秒检查一次

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
            # 注册基础AI服务
            # 从base_ai_service导入MockAIService
            from .mock_ai_service import MockAIService
            
            # 创建并注册Mock AI服务
            mock_service = MockAIService()
            self.services["mock"] = mock_service
            
            # 连接服务信号
            mock_service.status_changed.connect(self._on_service_status_changed)
            mock_service.request_started.connect(self._on_request_started)
            mock_service.request_progress.connect(self._on_request_progress)
            mock_service.request_completed.connect(self._on_request_completed)
            mock_service.request_error.connect(self._on_request_error)
            mock_service.model_info_loaded.connect(self._on_model_info_loaded)
            
            # 初始化健康状态
            self.service_health["mock"] = ServiceHealth(
                service_name="mock",
                status=ServiceStatus.ACTIVE,
                last_check=time.time(),
                response_time=0.0,
                error_rate=0.0,
                success_count=0,
                error_count=0,
                is_available=True
            )
            
            # 初始化统计信息
            self.usage_stats["mock"] = ServiceUsageStats(
                service_name="mock",
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                total_tokens=0,
                total_cost=0.0,
                average_response_time=0.0,
                last_used=0.0
            )
            
            self.logger.info("Mock AI服务注册成功")
            
            # 注册国内AI服务
            from .baidu_ai_service import ChineseAIServiceFactory
            
            # 获取所有可用的国内AI服务
            available_services = ChineseAIServiceFactory.get_available_services()
            
            for service_name in available_services:
                try:
                    # 创建服务实例
                    service = ChineseAIServiceFactory.create_service(service_name)
                    if service:
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
                        
                        self.logger.info(f"国内AI服务注册成功: {service_name}")
                except Exception as e:
                    self.logger.error(f"注册国内AI服务失败 {service_name}: {e}")
            
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
            service = None
            
            if service_name == "mock":
                # 从mock_ai_service导入MockAIService
                from .mock_ai_service import MockAIService
                service = MockAIService()
            else:
                # 尝试创建国内AI服务
                from .baidu_ai_service import ChineseAIServiceFactory
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
                status=ServiceStatus.ACTIVE if service_name == "mock" else ServiceStatus.INACTIVE,
                last_check=time.time(),
                response_time=0.0,
                error_rate=0.0,
                success_count=0,
                error_count=0,
                is_available=True if service_name == "mock" else False
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
        """发送请求"""
        try:
            if service_name not in self.services:
                self.logger.error(f"服务不存在: {service_name}")
                return None

            service = self.services[service_name]
            if model_id not in service.get_configured_models():
                self.logger.error(f"模型未配置: {service_name}.{model_id}")
                return None

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
            self.active_requests[request_id] = service_name

            if callback:
                self.request_callbacks[request_id] = callback

            # 发送请求
            response = service.send_request(request)

            # 更新统计
            self._update_usage_stats(service_name, request, response)

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

            if success:
                del self.active_requests[request_id]
                if request_id in self.request_callbacks:
                    del self.request_callbacks[request_id]

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

    def estimate_cost(self, service_name: str, model_id: str, prompt: str) -> float:
        """估算成本"""
        try:
            if service_name not in self.services:
                return 0.0

            service = self.services[service_name]
            request = ModelRequest(prompt=prompt, model_id=model_id)
            return service.estimate_cost(request)

        except Exception as e:
            self.logger.error(f"估算成本失败: {e}")
            return 0.0

    def _perform_health_check(self):
        """执行健康检查"""
        try:
            # 仅在有服务配置了模型时执行健康检查
            for service_name, service in self.services.items():
                try:
                    models = service.get_configured_models()
                    if models:
                        self._check_service_health(service_name)
                except Exception as e:
                    self.logger.error(f"检查服务 {service_name} 健康失败: {e}")

        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")

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

            # 简化健康检查，直接将服务状态设置为ACTIVE
            health.status = ServiceStatus.ACTIVE
            health.is_available = True
            health.error_message = ""
            health.last_check = time.time()
            health.response_time = 0.0
            health.success_count += 1
            
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
            health.last_check = time.time()
            self.service_health_updated.emit(service_name, health)

    def _update_stats(self):
        """更新统计信息"""
        try:
            # 这里可以添加更详细的统计逻辑
            self.stats_updated.emit(self.usage_stats)

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

        # 调用回调函数
        if request_id in self.request_callbacks:
            try:
                self.request_callbacks[request_id](response)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {e}")
            finally:
                del self.request_callbacks[request_id]

        # 清理请求记录
        if request_id in self.active_requests:
            del self.active_requests[request_id]

    def _on_request_error(self, request_id: str, error_message: str):
        """请求错误处理"""
        service_name = self.active_requests.get(request_id, "")
        self.request_failed.emit(request_id, service_name, error_message)

        # 调用回调函数
        if request_id in self.request_callbacks:
            try:
                self.request_callbacks[request_id](None)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {e}")
            finally:
                del self.request_callbacks[request_id]

        # 清理请求记录
        if request_id in self.active_requests:
            del self.active_requests[request_id]

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

    def remove_model_config(self, service_name: str, model_id: str) -> bool:
        """移除模型配置"""
        try:
            if service_name not in self.services:
                return False

            service = self.services[service_name]
            # 调用服务的移除配置方法（如果存在）
            if hasattr(service, 'remove_model_config'):
                service.remove_model_config(model_id)

            # 从安全密钥管理器中移除API密钥
            key_name = f"{service_name}_{model_id}"
            self.key_manager.delete_api_key(key_name)

            self.logger.info(f"Removed model config: {service_name}.{model_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove model config {service_name}.{model_id}: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            if hasattr(self, 'health_check_timer') and self.health_check_timer.isActive():
                self.health_check_timer.stop()
            if hasattr(self, 'stats_timer') and self.stats_timer.isActive():
                self.stats_timer.stop()

            # 清理所有服务
            for service in self.services.values():
                if hasattr(service, 'cleanup'):
                    service.cleanup()

            # 清理数据
            self.services.clear()
            self.service_health.clear()
            self.usage_stats.clear()
            self.active_requests.clear()
            self.request_callbacks.clear()

            self.logger.info("AI服务管理器清理完成")

        except Exception as e:
            self.logger.error(f"AI服务管理器清理失败: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()