#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI服务专用错误处理器
针对AI服务的特殊错误处理需求，包括API连接、认证、速率限制等
"""

import time
import json
import uuid
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
import requests
from PyQt6.QtCore import QObject, pyqtSignal

from ..utils.error_handler import (
    get_global_error_handler, ErrorInfo, ErrorType, ErrorSeverity,
    ErrorContext, RecoveryAction
)
from ..core.logger import Logger


class AIErrorType(Enum):
    """AI服务专用错误类型"""
    API_CONNECTION_ERROR = "api_connection_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    QUOTA_EXCEEDED_ERROR = "quota_exceeded_error"
    MODEL_NOT_FOUND_ERROR = "model_not_found_error"
    MODEL_OVERLOADED_ERROR = "model_overloaded_error"
    INVALID_REQUEST_ERROR = "invalid_request_error"
    CONTENT_FILTER_ERROR = "content_filter_error"
    TIMEOUT_ERROR = "timeout_error"
    SERVICE_UNAVAILABLE_ERROR = "service_unavailable_error"
    UNKNOWN_API_ERROR = "unknown_api_error"


@dataclass
class AIErrorContext:
    """AI错误上下文"""
    service_name: str
    model_id: str
    api_endpoint: str = ""
    request_id: str = ""
    response_code: int = 0
    response_headers: Dict[str, str] = field(default_factory=dict)
    request_payload: Dict[str, Any] = field(default_factory=dict)
    response_body: str = ""
    network_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIErrorDetails:
    """AI错误详情"""
    error_type: AIErrorType
    error_code: str
    error_message: str
    error_details: Dict[str, Any] = field(default_factory=dict)
    suggested_retries: int = 3
    retry_after: float = 0.0
    cost_impact: float = 0.0


class AIErrorHandler(QObject):
    """AI服务专用错误处理器"""

    # 信号定义
    ai_error_occurred = pyqtSignal(ErrorInfo, AIErrorDetails)  # AI错误发生
    recovery_attempt = pyqtSignal(str, str, int)  # 恢复尝试
    quota_warning = pyqtSignal(str, float, float)  # 配额警告
    model_health_update = pyqtSignal(str, str, bool)  # 模型健康状态更新

    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = logger
        self.global_error_handler = get_global_error_handler()

        # 错误统计
        self.error_stats = {
            "total_errors": 0,
            "error_by_type": {},
            "error_by_service": {},
            "error_by_model": {},
            "recovery_success": 0,
            "recovery_failure": 0
        }

        # 服务健康状态
        self.service_health: Dict[str, Dict[str, Any]] = {}
        self.model_health: Dict[str, Dict[str, Any]] = {}

        # 重试配置
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_base": 2.0,
            "jitter": True
        }

        # 熔断器配置
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # 锁
        self.lock = Lock()

    def handle_ai_error(self,
                      exception: Exception,
                      service_name: str,
                      model_id: str,
                      operation: str,
                      context: Optional[AIErrorContext] = None,
                      request_payload: Optional[Dict[str, Any]] = None) -> AIErrorDetails:
        """处理AI服务错误"""
        try:
            # 分析错误类型
            ai_error_details = self._analyze_ai_error(exception, context)

            # 创建错误信息
            error_info = self._create_error_info(
                exception, ai_error_details, service_name, model_id, operation, context, request_payload
            )

            # 记录错误统计
            self._record_error_stats(ai_error_details, service_name, model_id)

            # 更新健康状态
            self._update_health_status(service_name, model_id, ai_error_details)

            # 发送信号
            self.ai_error_occurred.emit(error_info, ai_error_details)

            # 记录到全局错误处理器
            self.global_error_handler.handle_error(error_info, show_dialog=False)

            return ai_error_details

        except Exception as e:
            self.logger.error(f"处理AI错误时发生异常: {e}")
            # 返回基本错误信息
            return AIErrorDetails(
                error_type=AIErrorType.UNKNOWN_API_ERROR,
                error_code="UNKNOWN_ERROR",
                error_message=str(e)
            )

    def _analyze_ai_error(self, exception: Exception, context: Optional[AIErrorContext] = None) -> AIErrorDetails:
        """分析AI错误"""
        error_message = str(exception).lower()

        # 网络连接错误
        if any(keyword in error_message for keyword in [
            "connection", "network", "timeout", "unreachable", "resolve host"
        ]):
            return AIErrorDetails(
                error_type=AIErrorType.API_CONNECTION_ERROR,
                error_code="CONNECTION_ERROR",
                error_message="网络连接失败",
                suggested_retries=3,
                retry_after=1.0
            )

        # 认证错误
        elif any(keyword in error_message for keyword in [
            "401", "unauthorized", "authentication", "invalid key", "access token"
        ]):
            return AIErrorDetails(
                error_type=AIErrorType.AUTHENTICATION_ERROR,
                error_code="AUTH_ERROR",
                error_message="API密钥认证失败",
                suggested_retries=0,  # 认证错误不重试
                retry_after=0.0
            )

        # 速率限制错误
        elif any(keyword in error_message for keyword in [
            "429", "rate limit", "too many requests", "quota exceeded", "requests limit"
        ]):
            retry_after = self._extract_retry_after(context) if context else 1.0
            return AIErrorDetails(
                error_type=AIErrorType.RATE_LIMIT_ERROR,
                error_code="RATE_LIMIT",
                error_message="API速率限制",
                suggested_retries=3,
                retry_after=retry_after
            )

        # 配额不足错误
        elif any(keyword in error_message for keyword in [
            "quota", "billing", "payment", "insufficient credits"
        ]):
            return AIErrorDetails(
                error_type=AIErrorType.QUOTA_EXCEEDED_ERROR,
                error_code="QUOTA_EXCEEDED",
                error_message="API配额不足",
                suggested_retries=0,
                retry_after=0.0,
                cost_impact=0.0
            )

        # 模型错误
        elif any(keyword in error_message for keyword in [
            "model not found", "invalid model", "model unavailable"
        ]):
            return AIErrorDetails(
                error_type=AIErrorType.MODEL_NOT_FOUND_ERROR,
                error_code="MODEL_NOT_FOUND",
                error_message="模型不存在或不可用",
                suggested_retries=0,
                retry_after=0.0
            )

        # 模型过载
        elif any(keyword in error_message for keyword in [
            "overloaded", "capacity", "too busy", "service unavailable"
        ]):
            return AIErrorDetails(
                error_type=AIErrorType.MODEL_OVERLOADED_ERROR,
                error_code="MODEL_OVERLOADED",
                error_message="模型负载过高",
                suggested_retries=3,
                retry_after=5.0
            )

        # 请求错误
        elif any(keyword in error_message for keyword in [
            "400", "bad request", "invalid parameter", "validation error"
        ]):
            return AIErrorDetails(
                error_type=AIErrorType.INVALID_REQUEST_ERROR,
                error_code="INVALID_REQUEST",
                error_message="请求参数无效",
                suggested_retries=0,
                retry_after=0.0
            )

        # 内容过滤错误
        elif any(keyword in error_message for keyword in [
            "content filter", "safety", "policy violation", "inappropriate content"
        ]):
            return AIErrorDetails(
                error_type=AIErrorType.CONTENT_FILTER_ERROR,
                error_code="CONTENT_FILTER",
                error_message="内容被安全策略过滤",
                suggested_retries=0,
                retry_after=0.0
            )

        # 服务不可用
        elif any(keyword in error_message for keyword in [
            "503", "service unavailable", "maintenance", "temporarily unavailable"
        ]):
            return AIErrorDetails(
                error_type=AIErrorType.SERVICE_UNAVAILABLE_ERROR,
                error_code="SERVICE_UNAVAILABLE",
                error_message="服务暂时不可用",
                suggested_retries=3,
                retry_after=10.0
            )

        # 未知错误
        else:
            return AIErrorDetails(
                error_type=AIErrorType.UNKNOWN_API_ERROR,
                error_code="UNKNOWN_ERROR",
                error_message=error_message,
                suggested_retries=2,
                retry_after=2.0
            )

    def _extract_retry_after(self, context: Optional[AIErrorContext]) -> float:
        """从响应头中提取重试延迟时间"""
        if not context or not context.response_headers:
            return 1.0

        retry_after = context.response_headers.get("Retry-After", "")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass

        return 1.0

    def _create_error_info(self,
                          exception: Exception,
                          ai_error_details: AIErrorDetails,
                          service_name: str,
                          model_id: str,
                          operation: str,
                          context: Optional[AIErrorContext] = None,
                          request_payload: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """创建错误信息"""
        # 映射AI错误类型到全局错误类型
        error_type_mapping = {
            AIErrorType.API_CONNECTION_ERROR: ErrorType.NETWORK,
            AIErrorType.AUTHENTICATION_ERROR: ErrorType.CONFIG,
            AIErrorType.RATE_LIMIT_ERROR: ErrorType.NETWORK,
            AIErrorType.QUOTA_EXCEEDED_ERROR: ErrorType.CONFIG,
            AIErrorType.MODEL_NOT_FOUND_ERROR: ErrorType.CONFIG,
            AIErrorType.MODEL_OVERLOADED_ERROR: ErrorType.AI,
            AIErrorType.INVALID_REQUEST_ERROR: ErrorType.VALIDATION,
            AIErrorType.CONTENT_FILTER_ERROR: ErrorType.VALIDATION,
            AIErrorType.TIMEOUT_ERROR: ErrorType.NETWORK,
            AIErrorType.SERVICE_UNAVAILABLE_ERROR: ErrorType.AI,
            AIErrorType.UNKNOWN_API_ERROR: ErrorType.AI
        }

        # 确定严重程度
        severity_mapping = {
            AIErrorType.AUTHENTICATION_ERROR: ErrorSeverity.CRITICAL,
            AIErrorType.QUOTA_EXCEEDED_ERROR: ErrorSeverity.HIGH,
            AIErrorType.CONTENT_FILTER_ERROR: ErrorSeverity.MEDIUM,
            AIErrorType.INVALID_REQUEST_ERROR: ErrorSeverity.MEDIUM,
            AIErrorType.MODEL_NOT_FOUND_ERROR: ErrorSeverity.HIGH,
            AIErrorType.SERVICE_UNAVAILABLE_ERROR: ErrorSeverity.HIGH,
            AIErrorType.MODEL_OVERLOADED_ERROR: ErrorSeverity.MEDIUM,
            AIErrorType.RATE_LIMIT_ERROR: ErrorSeverity.MEDIUM,
            AIErrorType.API_CONNECTION_ERROR: ErrorSeverity.MEDIUM,
            AIErrorType.TIMEOUT_ERROR: ErrorSeverity.MEDIUM,
            AIErrorType.UNKNOWN_API_ERROR: ErrorSeverity.MEDIUM
        }

        # 确定恢复动作
        recovery_mapping = {
            AIErrorType.AUTHENTICATION_ERROR: RecoveryAction.CONTACT_SUPPORT,
            AIErrorType.QUOTA_EXCEEDED_ERROR: RecoveryAction.CONTACT_SUPPORT,
            AIErrorType.MODEL_NOT_FOUND_ERROR: RecoveryAction.CONTACT_SUPPORT,
            AIErrorType.CONTENT_FILTER_ERROR: RecoveryAction.SKIP,
            AIErrorType.INVALID_REQUEST_ERROR: RecoveryAction.NONE,
            AIErrorType.SERVICE_UNAVAILABLE_ERROR: RecoveryAction.RETRY,
            AIErrorType.MODEL_OVERLOADED_ERROR: RecoveryAction.RETRY,
            AIErrorType.RATE_LIMIT_ERROR: RecoveryAction.RETRY,
            AIErrorType.API_CONNECTION_ERROR: RecoveryAction.RETRY,
            AIErrorType.TIMEOUT_ERROR: RecoveryAction.RETRY,
            AIErrorType.UNKNOWN_API_ERROR: RecoveryAction.RETRY
        }

        # 生成用户消息
        user_message_mapping = {
            AIErrorType.AUTHENTICATION_ERROR: "API密钥认证失败，请检查配置",
            AIErrorType.QUOTA_EXCEEDED_ERROR: "API配额不足，请充值或更换模型",
            AIErrorType.MODEL_NOT_FOUND_ERROR: "模型不存在，请检查模型配置",
            AIErrorType.CONTENT_FILTER_ERROR: "内容被安全策略过滤，请修改输入内容",
            AIErrorType.INVALID_REQUEST_ERROR: "请求参数无效，请检查输入",
            AIErrorType.SERVICE_UNAVAILABLE_ERROR: "AI服务暂时不可用，请稍后重试",
            AIErrorType.MODEL_OVERLOADED_ERROR: "AI模型负载过高，请稍后重试",
            AIErrorType.RATE_LIMIT_ERROR: "API调用频率过高，请稍后重试",
            AIErrorType.API_CONNECTION_ERROR: "网络连接失败，请检查网络连接",
            AIErrorType.TIMEOUT_ERROR: "请求超时，请稍后重试",
            AIErrorType.UNKNOWN_API_ERROR: "AI服务出现未知错误，请稍后重试"
        }

        error_info = ErrorInfo(
            error_type=error_type_mapping.get(ai_error_details.error_type, ErrorType.AI),
            severity=severity_mapping.get(ai_error_details.error_type, ErrorSeverity.MEDIUM),
            message=f"[{service_name}.{model_id}] {ai_error_details.error_message}",
            exception=exception,
            context=ErrorContext(
                component=f"AI Service ({service_name})",
                operation=operation,
                system_state={
                    "service_name": service_name,
                    "model_id": model_id,
                    "ai_error_type": ai_error_details.error_type.value,
                    "ai_error_code": ai_error_details.error_code,
                    "suggested_retries": ai_error_details.suggested_retries,
                    "retry_after": ai_error_details.retry_after
                }
            ),
            recovery_action=recovery_mapping.get(ai_error_details.error_type, RecoveryAction.NONE),
            user_message=user_message_mapping.get(ai_error_details.error_type, "AI服务调用失败"),
            technical_details={
                "ai_error_type": ai_error_details.error_type.value,
                "ai_error_code": ai_error_details.error_code,
                "ai_error_details": ai_error_details.error_details,
                "context": context.__dict__ if context else {},
                "request_payload": request_payload or {}
            }
        )

        return error_info

    def _record_error_stats(self, ai_error_details: AIErrorDetails, service_name: str, model_id: str):
        """记录错误统计"""
        with self.lock:
            self.error_stats["total_errors"] += 1

            # 按类型统计
            error_type = ai_error_details.error_type.value
            self.error_stats["error_by_type"][error_type] = self.error_stats["error_by_type"].get(error_type, 0) + 1

            # 按服务统计
            self.error_stats["error_by_service"][service_name] = self.error_stats["error_by_service"].get(service_name, 0) + 1

            # 按模型统计
            model_key = f"{service_name}.{model_id}"
            self.error_stats["error_by_model"][model_key] = self.error_stats["error_by_model"].get(model_key, 0) + 1

    def _update_health_status(self, service_name: str, model_id: str, ai_error_details: AIErrorDetails):
        """更新健康状态"""
        model_key = f"{service_name}.{model_id}"
        current_time = time.time()

        # 更新模型健康状态
        if model_key not in self.model_health:
            self.model_health[model_key] = {
                "last_check": current_time,
                "is_healthy": True,
                "error_count": 0,
                "last_error": None,
                "consecutive_errors": 0
            }

        model_health = self.model_health[model_key]
        model_health["last_check"] = current_time

        if ai_error_details.error_type in [
            AIErrorType.AUTHENTICATION_ERROR,
            AIErrorType.QUOTA_EXCEEDED_ERROR,
            AIErrorType.MODEL_NOT_FOUND_ERROR
        ]:
            # 这些错误表示模型配置问题，标记为不健康
            model_health["is_healthy"] = False
            model_health["consecutive_errors"] += 1
        else:
            # 其他错误可能是暂时的
            model_health["consecutive_errors"] += 1
            if model_health["consecutive_errors"] >= 5:
                model_health["is_healthy"] = False

        model_health["error_count"] += 1
        model_health["last_error"] = ai_error_details

        # 发送健康状态更新信号
        self.model_health_update.emit(service_name, model_id, model_health["is_healthy"])

    def should_retry(self, ai_error_details: AIErrorDetails) -> bool:
        """判断是否应该重试"""
        return ai_error_details.suggested_retries > 0

    def get_retry_delay(self, ai_error_details: AIErrorDetails, attempt: int) -> float:
        """获取重试延迟时间"""
        if ai_error_details.retry_after > 0:
            return ai_error_details.retry_after

        # 指数退避
        delay = self.retry_config["base_delay"] * (
            self.retry_config["exponential_base"] ** (attempt - 1)
        )
        delay = min(delay, self.retry_config["max_delay"])

        # 添加抖动
        if self.retry_config["jitter"]:
            delay = delay * (0.5 + (0.5 * (attempt % 2)))

        return delay

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        with self.lock:
            return self.error_stats.copy()

    def get_model_health(self, service_name: str, model_id: str) -> Optional[Dict[str, Any]]:
        """获取模型健康状态"""
        model_key = f"{service_name}.{model_id}"
        return self.model_health.get(model_key)

    def get_all_model_health(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型健康状态"""
        return self.model_health.copy()

    def reset_model_health(self, service_name: str, model_id: str):
        """重置模型健康状态"""
        model_key = f"{service_name}.{model_id}"
        if model_key in self.model_health:
            self.model_health[model_key].update({
                "is_healthy": True,
                "error_count": 0,
                "consecutive_errors": 0,
                "last_error": None
            })
            self.logger.info(f"已重置模型健康状态: {model_key}")

    def clear_error_stats(self):
        """清空错误统计"""
        with self.lock:
            self.error_stats = {
                "total_errors": 0,
                "error_by_type": {},
                "error_by_service": {},
                "error_by_model": {},
                "recovery_success": 0,
                "recovery_failure": 0
            }
        self.logger.info("已清空AI错误统计")

    def update_retry_config(self, config: Dict[str, Any]):
        """更新重试配置"""
        self.retry_config.update(config)
        self.logger.info(f"已更新AI重试配置: {config}")

    def test_service_connection(self, service_name: str, endpoint: str, headers: Dict[str, str]) -> bool:
        """测试服务连接"""
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"服务连接测试失败 {service_name}: {e}")
            return False