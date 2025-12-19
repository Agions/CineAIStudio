#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 错误管理系统
提供统一的错误处理、恢复机制和错误报告
"""

import traceback
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Dict, List, Any, Optional, Callable, Union, Type, Set,
    ContextManager, Protocol
)
from contextlib import contextmanager
from abc import ABC, abstractmethod

from .logger import Logger
from .event_bus import EventBus


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 低级错误，不影响主要功能
    MEDIUM = "medium"     # 中级错误，影响部分功能
    HIGH = "high"         # 高级错误，影响主要功能
    CRITICAL = "critical" # 关键错误，可能导致系统不可用


class ErrorCategory(Enum):
    """错误类别"""
    SYSTEM = "system"           # 系统错误
    UI = "ui"                   # 用户界面错误
    SERVICE = "service"         # 服务错误
    NETWORK = "network"         # 网络错误
    FILE_IO = "file_io"         # 文件I/O错误
    VIDEO = "video"             # 视频处理错误
    AI = "ai"                   # AI服务错误
    CONFIG = "config"           # 配置错误
    USER = "user"               # 用户操作错误
    UNKNOWN = "unknown"         # 未知错误


class RecoveryAction(Enum):
    """恢复操作类型"""
    NONE = "none"               # 无恢复操作
    RETRY = "retry"             # 重试操作
    FALLBACK = "fallback"       # 使用备用方案
    RESET = "reset"             # 重置状态
    RESTART = "restart"         # 重启组件
    IGNORE = "ignore"           # 忽略错误


@dataclass
class ErrorInfo:
    """错误信息"""
    error_id: str                          # 错误唯一标识
    timestamp: float                        # 时间戳
    category: ErrorCategory                # 错误类别
    severity: ErrorSeverity                # 严重程度
    message: str                          # 错误消息
    details: Optional[str] = None         # 详细信息
    exception: Optional[Exception] = None  # 原始异常
    context: Dict[str, Any] = field(default_factory=dict)  # 上下文信息
    user_action: Optional[str] = None     # 用户建议操作
    recovery_action: RecoveryAction = RecoveryAction.NONE  # 恢复操作
    retry_count: int = 0                  # 重试次数
    resolved: bool = False                 # 是否已解决
    resolved_by: Optional[str] = None     # 解决者
    resolved_at: Optional[float] = None   # 解决时间


class ErrorReporter(ABC):
    """错误报告器接口"""

    @abstractmethod
    def report(self, error_info: ErrorInfo) -> None:
        """报告错误"""
        pass

    @abstractmethod
    def can_report(self, error_info: ErrorInfo) -> bool:
        """判断是否可以报告"""
        pass


class ErrorRecoveryStrategy(ABC):
    """错误恢复策略接口"""

    @abstractmethod
    def can_recover(self, error_info: ErrorInfo) -> bool:
        """判断是否可以恢复"""
        pass

    @abstractmethod
    def recover(self, error_info: ErrorInfo) -> bool:
        """执行恢复操作"""
        pass

    @abstractmethod
    def get_estimated_recovery_time(self, error_info: ErrorInfo) -> float:
        """获取预估恢复时间（秒）"""
        pass


class ErrorManager:
    """错误管理器"""

    def __init__(self, logger: Logger, event_bus: EventBus):
        self._logger = logger
        self._event_bus = event_bus

        # 错误存储
        self._errors: Dict[str, ErrorInfo] = {}
        self._error_history: List[ErrorInfo] = []
        self._max_history = 1000

        # 处理器
        self._reporters: List[ErrorReporter] = []
        self._recovery_strategies: List[ErrorRecoveryStrategy] = []
        self._error_handlers: Dict[ErrorCategory, List[Callable]] = {}

        # 配置
        self._config = {
            "max_retry_count": 3,
            "auto_recovery_enabled": True,
            "reporting_enabled": True,
            "collect_user_feedback": True,
            "error_log_path": "logs/errors.log",
            "crash_dump_path": "logs/crashes/"
        }

        # 统计
        self._stats = {
            "total_errors": 0,
            "resolved_errors": 0,
            "auto_recovered": 0,
            "categories": {},
            "severities": {},
            "recovery_times": []
        }

        # 线程安全
        self._lock = threading.RLock()

    def handle_error(self, error: Union[Exception, ErrorInfo],
                     category: Optional[ErrorCategory] = None,
                     severity: Optional[ErrorSeverity] = None,
                     context: Optional[Dict[str, Any]] = None,
                     user_action: Optional[str] = None) -> ErrorInfo:
        """处理错误"""
        with self._lock:
            # 创建错误信息
            error_info = self._create_error_info(error, category, severity, context, user_action)

            # 存储错误
            self._store_error(error_info)

            # 更新统计
            self._update_stats(error_info)

            # 发布错误事件
            self._event_bus.publish("error.occurred", {
                "error_id": error_info.error_id,
                "category": error_info.category.value,
                "severity": error_info.severity.value
            })

            # 记录日志
            self._log_error(error_info)

            # 尝试自动恢复
            if self._config["auto_recovery_enabled"]:
                self._attempt_recovery(error_info)

            # 报告错误
            if self._config["reporting_enabled"]:
                self._report_error(error_info)

            return error_info

    def resolve_error(self, error_id: str, resolved_by: str = "manual") -> bool:
        """标记错误为已解决"""
        with self._lock:
            if error_id not in self._errors:
                return False

            error_info = self._errors[error_id]
            error_info.resolved = True
            error_info.resolved_by = resolved_by
            error_info.resolved_at = time.time()

            self._stats["resolved_errors"] += 1

            self._event_bus.publish("error.resolved", {
                "error_id": error_id,
                "resolved_by": resolved_by
            })

            self._logger.info(f"Error {error_id} resolved by {resolved_by}")
            return True

    def get_errors(self, category: Optional[ErrorCategory] = None,
                  severity: Optional[ErrorSeverity] = None,
                  resolved: Optional[bool] = None,
                  limit: int = 100) -> List[ErrorInfo]:
        """获取错误列表"""
        with self._lock:
            errors = self._error_history.copy()

            # 过滤
            if category is not None:
                errors = [e for e in errors if e.category == category]
            if severity is not None:
                errors = [e for e in errors if e.severity == severity]
            if resolved is not None:
                errors = [e for e in errors if e.resolved == resolved]

            # 按时间排序（最新的在前）
            errors.sort(key=lambda e: e.timestamp, reverse=True)

            return errors[:limit]

    def get_error_by_id(self, error_id: str) -> Optional[ErrorInfo]:
        """根据ID获取错误信息"""
        with self._lock:
            return self._errors.get(error_id)

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        with self._lock:
            return {
                **self._stats.copy(),
                "unresolved_count": len([e for e in self._errors.values() if not e.resolved]),
                "average_recovery_time": (
                    sum(self._stats["recovery_times"]) / len(self._stats["recovery_times"])
                    if self._stats["recovery_times"] else 0
                )
            }

    def register_reporter(self, reporter: ErrorReporter) -> None:
        """注册错误报告器"""
        self._reporters.append(reporter)

    def register_recovery_strategy(self, strategy: ErrorRecoveryStrategy) -> None:
        """注册错误恢复策略"""
        self._recovery_strategies.append(strategy)

    def register_handler(self, category: ErrorCategory, handler: Callable) -> None:
        """注册错误处理器"""
        if category not in self._error_handlers:
            self._error_handlers[category] = []
        self._error_handlers[category].append(handler)

    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置"""
        self._config.update(config)

    def clear_errors(self, before_timestamp: Optional[float] = None) -> int:
        """清除错误记录"""
        with self._lock:
            if before_timestamp is None:
                # 清除所有已解决的错误
                to_remove = [e for e in self._error_history if e.resolved]
            else:
                # 清除指定时间之前的错误
                to_remove = [e for e in self._error_history if e.timestamp < before_timestamp]

            # 从历史记录中移除
            for error in to_remove:
                if error in self._error_history:
                    self._error_history.remove(error)
                if error.error_id in self._errors:
                    del self._errors[error.error_id]

            return len(to_remove)

    @contextmanager
    def error_context(self, context: Dict[str, Any]):
        """错误上下文管理器"""
        # 这里可以设置线程局部变量来存储上下文
        try:
            yield
        except Exception as e:
            self.handle_error(e, context=context)
            raise

    # 私有方法

    def _create_error_info(self, error: Union[Exception, ErrorInfo],
                          category: Optional[ErrorCategory] = None,
                          severity: Optional[ErrorSeverity] = None,
                          context: Optional[Dict[str, Any]] = None,
                          user_action: Optional[str] = None) -> ErrorInfo:
        """创建错误信息对象"""
        if isinstance(error, ErrorInfo):
            return error

        # 生成错误ID
        error_id = f"ERR_{int(time.time() * 1000)}_{id(error)}"

        # 确定错误类别
        if category is None:
            category = self._determine_category(error)

        # 确定严重程度
        if severity is None:
            severity = self._determine_severity(error, category)

        # 创建错误信息
        return ErrorInfo(
            error_id=error_id,
            timestamp=time.time(),
            category=category,
            severity=severity,
            message=str(error),
            details=traceback.format_exc(),
            exception=error,
            context=context or {},
            user_action=user_action
        )

    def _determine_category(self, error: Exception) -> ErrorCategory:
        """确定错误类别"""
        error_type = type(error).__name__.lower()

        if any(keyword in error_type for keyword in ["file", "path", "directory", "io"]):
            return ErrorCategory.FILE_IO
        elif any(keyword in error_type for keyword in ["network", "connection", "http"]):
            return ErrorCategory.NETWORK
        elif any(keyword in error_type for keyword in ["video", "moviepy", "codec"]):
            return ErrorCategory.VIDEO
        elif any(keyword in error_type for keyword in ["ai", "openai", "claude", "gpt"]):
            return ErrorCategory.AI
        elif any(keyword in error_type for keyword in ["config", "setting"]):
            return ErrorCategory.CONFIG
        elif any(keyword in error_type for keyword in ["qt", "widget", "ui"]):
            return ErrorCategory.UI
        else:
            return ErrorCategory.SYSTEM

    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """确定错误严重程度"""
        error_type = type(error).__name__.lower()

        # 关键错误类型
        critical_keywords = ["critical", "fatal", "systemexit", "keyboardinterrupt"]
        high_keywords = ["runtime", "attribute", "type", "import", "memory"]
        medium_keywords = ["value", "index", "key", "timeout"]

        if any(keyword in error_type for keyword in critical_keywords):
            return ErrorSeverity.CRITICAL
        elif any(keyword in error_type for keyword in high_keywords):
            return ErrorSeverity.HIGH
        elif any(keyword in error_type for keyword in medium_keywords):
            return ErrorSeverity.MEDIUM
        elif category in [ErrorCategory.SYSTEM, ErrorCategory.VIDEO]:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.AI, ErrorCategory.NETWORK]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _store_error(self, error_info: ErrorInfo) -> None:
        """存储错误信息"""
        self._errors[error_info.error_id] = error_info
        self._error_history.append(error_info)

        # 限制历史记录数量
        if len(self._error_history) > self._max_history:
            old_error = self._error_history.pop(0)
            if old_error.error_id in self._errors:
                del self._errors[old_error.error_id]

    def _update_stats(self, error_info: ErrorInfo) -> None:
        """更新统计信息"""
        self._stats["total_errors"] += 1

        # 类别统计
        cat_name = error_info.category.value
        self._stats["categories"][cat_name] = self._stats["categories"].get(cat_name, 0) + 1

        # 严重程度统计
        sev_name = error_info.severity.value
        self._stats["severities"][sev_name] = self._stats["severities"].get(sev_name, 0) + 1

    def _log_error(self, error_info: ErrorInfo) -> None:
        """记录错误日志"""
        log_level = {
            ErrorSeverity.LOW: "warning",
            ErrorSeverity.MEDIUM: "error",
            ErrorSeverity.HIGH: "error",
            ErrorSeverity.CRITICAL: "critical"
        }.get(error_info.severity, "error")

        message = f"[{error_info.error_id}] {error_info.message}"

        if error_info.details:
            message += f"\n{error_info.details}"

        getattr(self._logger, log_level)(message)

    def _attempt_recovery(self, error_info: ErrorInfo) -> None:
        """尝试自动恢复"""
        if error_info.retry_count >= self._config["max_retry_count"]:
            return

        # 查找适用的恢复策略
        for strategy in self._recovery_strategies:
            if strategy.can_recover(error_info):
                try:
                    start_time = time.time()
                    success = strategy.recover(error_info)
                    recovery_time = time.time() - start_time

                    if success:
                        error_info.resolved = True
                        error_info.resolved_by = "auto_recovery"
                        error_info.resolved_at = time.time()
                        self._stats["auto_recovered"] += 1
                        self._stats["recovery_times"].append(recovery_time)

                        self._event_bus.publish("error.auto_recovered", {
                            "error_id": error_info.error_id,
                            "recovery_time": recovery_time
                        })

                        self._logger.info(f"Auto-recovered from error {error_info.error_id}")
                    else:
                        error_info.retry_count += 1

                except Exception as e:
                    self._logger.error(f"Auto-recovery failed for {error_info.error_id}: {e}")
                    error_info.retry_count += 1

    def _report_error(self, error_info: ErrorInfo) -> None:
        """报告错误"""
        for reporter in self._reporters:
            try:
                if reporter.can_report(error_info):
                    reporter.report(error_info)
            except Exception as e:
                self._logger.error(f"Error reporter failed: {e}")


# 预定义的错误报告器
class ConsoleErrorReporter(ErrorReporter):
    """控制台错误报告器"""

    def report(self, error_info: ErrorInfo) -> None:
        print(f"ERROR: {error_info.error_id} - {error_info.message}")

    def can_report(self, error_info: ErrorInfo) -> bool:
        return error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]


class FileErrorReporter(ErrorReporter):
    """文件错误报告器"""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def report(self, error_info: ErrorInfo) -> None:
        with open(self.file_path, 'a', encoding='utf-8') as f:
            f.write(f"{error_info.timestamp},{error_info.error_id},"
                   f"{error_info.category.value},{error_info.severity.value},"
                   f"{error_info.message}\n")

    def can_report(self, error_info: ErrorInfo) -> bool:
        return True


# 预定义的恢复策略
class RetryRecoveryStrategy(ErrorRecoveryStrategy):
    """重试恢复策略"""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def can_recover(self, error_info: ErrorInfo) -> bool:
        return (error_info.retry_count < self.max_retries and
                error_info.category in [ErrorCategory.NETWORK, ErrorCategory.AI])

    def recover(self, error_info: ErrorInfo) -> bool:
        # 这里可以实现具体的重试逻辑
        # 返回 True 表示恢复成功
        return False  # 默认不实现

    def get_estimated_recovery_time(self, error_info: ErrorInfo) -> float:
        return 5.0  # 预估5秒


class FallbackRecoveryStrategy(ErrorRecoveryStrategy):
    """备用方案恢复策略"""

    def can_recover(self, error_info: ErrorInfo) -> bool:
        return error_info.recovery_action == RecoveryAction.FALLBACK

    def recover(self, error_info: ErrorInfo) -> bool:
        # 实现备用方案逻辑
        return True

    def get_estimated_recovery_time(self, error_info: ErrorInfo) -> float:
        return 2.0


# 便捷装饰器
def error_handler(category: ErrorCategory = ErrorCategory.SYSTEM,
                  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                  user_action: Optional[str] = None):
    """错误处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 这里需要获取错误管理器实例
                # 暂时简单处理
                raise
        return wrapper
    return decorator


# 便捷上下文管理器
@contextmanager
def error_handling_context(context: Dict[str, Any] = None):
    """错误处理上下文管理器"""
    try:
        yield
    except Exception as e:
        # 这里需要获取错误管理器实例
        # 暂时简单处理
        raise


# 全局错误管理器（需要在服务系统初始化后设置）
_error_manager = None


def get_error_manager() -> ErrorManager:
    """获取全局错误管理器"""
    global _error_manager
    if _error_manager is None:
        raise RuntimeError("Error manager not initialized")
    return _error_manager


def set_error_manager(manager: ErrorManager) -> None:
    """设置全局错误管理器"""
    global _error_manager
    _error_manager = manager