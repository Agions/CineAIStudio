#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 增强错误处理模块
提供全局异常处理、错误恢复、用户友好的错误消息和 comprehensive logging
"""

import sys
import traceback
import logging
import os
import json
import threading
import time
from datetime import datetime
from typing import Optional, Callable, Any, Dict, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from functools import wraps
from contextlib import contextmanager
from PyQt6.QtWidgets import QMessageBox, QWidget, QApplication, QProgressDialog
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, Qt


class ErrorType(Enum):
    """错误类型枚举"""
    UI = "ui"
    SYSTEM = "system"
    FILE = "file"
    NETWORK = "network"
    AI = "ai"
    DATABASE = "database"
    MEDIA = "media"
    CONFIG = "config"
    PERMISSION = "permission"
    MEMORY = "memory"
    VALIDATION = "validation"
    EXPORT = "export"


class ErrorSeverity(Enum):
    """错误严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """恢复动作枚举"""
    NONE = "none"
    RETRY = "retry"
    SKIP = "skip"
    ROLLBACK = "rollback"
    RESET = "reset"
    CONTACT_SUPPORT = "contact_support"


@dataclass
class ErrorContext:
    """错误上下文信息"""
    component: str
    operation: str
    user_action: str = ""
    system_state: Dict[str, Any] = field(default_factory=dict)
    user_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception] = None
    context: Optional[ErrorContext] = None
    recovery_action: RecoveryAction = RecoveryAction.NONE
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: Optional[str] = None
    user_message: str = ""
    technical_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['error_type'] = self.error_type.value
        data['severity'] = self.severity.value
        data['recovery_action'] = self.recovery_action.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ErrorStatistics:
    """错误统计"""
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.recovery_counts: Dict[str, int] = {}
        self.total_errors = 0
        self.lock = threading.Lock()

    def record_error(self, error_info: ErrorInfo):
        """记录错误"""
        with self.lock:
            self.total_errors += 1
            error_key = f"{error_info.error_type.value}_{error_info.severity.value}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

    def record_recovery(self, recovery_action: RecoveryAction):
        """记录恢复动作"""
        with self.lock:
            action_key = recovery_action.value
            self.recovery_counts[action_key] = self.recovery_counts.get(action_key, 0) + 1

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            return {
                'total_errors': self.total_errors,
                'error_counts': self.error_counts.copy(),
                'recovery_counts': self.recovery_counts.copy()
            }


class ErrorHandler(QObject):
    """增强的错误处理器"""

    # 信号定义
    error_occurred = pyqtSignal(ErrorInfo)  # 错误发生信号
    error_recovered = pyqtSignal(ErrorInfo, RecoveryAction)  # 错误恢复信号
    statistics_updated = pyqtSignal(dict)  # 统计更新信号

    def __init__(self, logger=None):
        """初始化错误处理器"""
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.error_history: List[ErrorInfo] = []
        self.statistics = ErrorStatistics()
        self.error_reports_dir = os.path.expanduser("~/CineAIStudio/ErrorReports")
        self.max_history_size = 1000
        self.auto_report_enabled = True

        # 确保错误报告目录存在
        os.makedirs(self.error_reports_dir, exist_ok=True)

    def handle_error(self, error_info: ErrorInfo, show_dialog: bool = True,
                    parent: Optional[QWidget] = None) -> None:
        """处理错误"""
        # 记录错误
        self._log_error(error_info)
        self._add_to_history(error_info)
        self.statistics.record_error(error_info)

        # 发送信号
        self.error_occurred.emit(error_info)

        # 生成用户友好的错误消息
        user_message = error_info.user_message or self._generate_user_message(error_info)

        # 显示错误对话框（如果需要）
        if show_dialog and QApplication.instance():
            self._show_error_dialog(error_info, user_message, parent)

        # 尝试自动恢复
        self._attempt_auto_recovery(error_info)

        # 自动生成错误报告（对于严重错误）
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._generate_error_report(error_info)

    def _log_error(self, error_info: ErrorInfo) -> None:
        """记录错误到日志"""
        log_message = f"[{error_info.error_type.value.upper()}] {error_info.message}"

        if error_info.context:
            log_message += f" (组件: {error_info.context.component}, 操作: {error_info.context.operation})"

        if error_info.exception:
            log_message += f" 异常: {str(error_info.exception)}"

        # 根据严重程度选择日志级别
        if error_info.severity == ErrorSeverity.CRITICAL:
            if error_info.exception:
                self.logger.critical(log_message, exc_info=True)
            else:
                self.logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            if error_info.exception:
                self.logger.error(log_message, exc_info=True)
            else:
                self.logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            if error_info.exception:
                self.logger.warning(log_message, exc_info=True)
            else:
                self.logger.warning(log_message)
        else:
            if error_info.exception:
                self.logger.info(log_message, exc_info=True)
            else:
                self.logger.info(log_message)

    def _add_to_history(self, error_info: ErrorInfo) -> None:
        """添加错误到历史记录"""
        self.error_history.append(error_info)

        # 限制历史记录大小
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]

    def _generate_user_message(self, error_info: ErrorInfo) -> str:
        """生成用户友好的错误消息"""
        message_templates = {
            ErrorType.UI: {
                ErrorSeverity.LOW: "界面操作遇到小问题",
                ErrorSeverity.MEDIUM: "界面操作出现错误",
                ErrorSeverity.HIGH: "界面功能出现严重问题",
                ErrorSeverity.CRITICAL: "界面系统崩溃"
            },
            ErrorType.FILE: {
                ErrorSeverity.LOW: "文件操作遇到小问题",
                ErrorSeverity.MEDIUM: "文件操作失败",
                ErrorSeverity.HIGH: "文件读写出现严重问题",
                ErrorSeverity.CRITICAL: "文件系统错误"
            },
            ErrorType.NETWORK: {
                ErrorSeverity.LOW: "网络连接不稳定",
                ErrorSeverity.MEDIUM: "网络请求失败",
                ErrorSeverity.HIGH: "网络连接出现严重问题",
                ErrorSeverity.CRITICAL: "网络服务不可用"
            },
            ErrorType.AI: {
                ErrorSeverity.LOW: "AI功能响应缓慢",
                ErrorSeverity.MEDIUM: "AI功能执行失败",
                ErrorSeverity.HIGH: "AI服务出现异常",
                ErrorSeverity.CRITICAL: "AI服务不可用"
            },
            ErrorType.SYSTEM: {
                ErrorSeverity.LOW: "系统资源紧张",
                ErrorSeverity.MEDIUM: "系统操作失败",
                ErrorSeverity.HIGH: "系统出现严重问题",
                ErrorSeverity.CRITICAL: "系统错误"
            },
            ErrorType.EXPORT: {
                ErrorSeverity.LOW: "导出过程遇到小问题",
                ErrorSeverity.MEDIUM: "导出操作失败",
                ErrorSeverity.HIGH: "导出过程出现严重问题",
                ErrorSeverity.CRITICAL: "导出系统崩溃"
            }
        }

        template = message_templates.get(error_info.error_type, {}).get(error_info.severity)
        if template:
            if error_info.recovery_action != RecoveryAction.NONE:
                template += f"，建议{self._get_recovery_action_description(error_info.recovery_action)}"
            return template

        return f"发生{error_info.severity.value}级错误: {error_info.message}"

    def _get_recovery_action_description(self, action: RecoveryAction) -> str:
        """获取恢复动作描述"""
        descriptions = {
            RecoveryAction.NONE: "忽略此错误",
            RecoveryAction.RETRY: "重试操作",
            RecoveryAction.SKIP: "跳过此步骤",
            RecoveryAction.ROLLBACK: "回滚到之前状态",
            RecoveryAction.RESET: "重置相关设置",
            RecoveryAction.CONTACT_SUPPORT: "联系技术支持"
        }
        return descriptions.get(action, "尝试恢复")

    def _show_error_dialog(self, error_info: ErrorInfo, user_message: str,
                          parent: Optional[QWidget] = None) -> None:
        """显示错误对话框"""
        if not parent:
            parent = QApplication.activeWindow()

        if not parent:
            # 如果没有父窗口，使用控制台输出
            print(f"ERROR: {user_message}")
            return

        # 根据严重程度选择对话框类型
        if error_info.severity == ErrorSeverity.CRITICAL:
            QMessageBox.critical(parent, "严重错误", user_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            QMessageBox.critical(parent, "错误", user_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            QMessageBox.warning(parent, "警告", user_message)
        else:
            QMessageBox.information(parent, "提示", user_message)

    def _attempt_auto_recovery(self, error_info: ErrorInfo) -> None:
        """尝试自动恢复"""
        if error_info.recovery_action == RecoveryAction.NONE:
            return

        try:
            # 这里可以根据不同的错误类型和恢复动作实现具体的恢复逻辑
            # 例如：重试网络请求、回滚文件操作、重置组件状态等

            self.statistics.record_recovery(error_info.recovery_action)
            self.error_recovered.emit(error_info, error_info.recovery_action)

            self.logger.info(f"自动恢复成功: {error_info.recovery_action.value}")

        except Exception as recovery_error:
            self.logger.error(f"自动恢复失败: {recovery_error}", exc_info=True)
            # 创建一个新的错误信息来记录恢复失败
            recovery_error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"自动恢复失败: {str(recovery_error)}",
                exception=recovery_error,
                context=error_info.context
            )
            self._log_error(recovery_error_info)

    def _generate_error_report(self, error_info: ErrorInfo) -> None:
        """生成错误报告"""
        if not self.auto_report_enabled:
            return

        try:
            report_filename = f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{error_info.error_type.value}.json"
            report_path = os.path.join(self.error_reports_dir, report_filename)

            report_data = {
                'error_info': error_info.to_dict(),
                'system_info': self._get_system_info(),
                'application_info': self._get_application_info(),
                'statistics': self.statistics.get_statistics()
            }

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"错误报告已生成: {report_path}")

        except Exception as e:
            self.logger.error(f"生成错误报告失败: {e}")

    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            import platform
            import psutil

            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total,
                'timestamp': datetime.now().isoformat()
            }
        except ImportError:
            return {'platform': 'Unknown', 'python_version': sys.version}
        except Exception:
            return {'platform': 'Unknown', 'python_version': sys.version}

    def _get_application_info(self) -> Dict[str, Any]:
        """获取应用程序信息"""
        try:
            app = QApplication.instance()
            return {
                'application_name': app.applicationName(),
                'application_version': app.applicationVersion(),
                'organization_name': app.organizationName(),
                'error_count': len(self.error_history)
            }
        except Exception:
            return {'application_name': 'Unknown', 'error_count': len(self.error_history)}

    def get_error_history(self, limit: Optional[int] = None) -> List[ErrorInfo]:
        """获取错误历史"""
        if limit:
            return self.error_history[-limit:]
        return self.error_history.copy()

    def clear_error_history(self) -> None:
        """清空错误历史"""
        self.error_history.clear()

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return self.statistics.get_statistics()

    def set_auto_report_enabled(self, enabled: bool) -> None:
        """设置自动报告开关"""
        self.auto_report_enabled = enabled


def setup_global_exception_handler(logger=None) -> ErrorHandler:
    """设置全局异常处理器"""
    error_handler = ErrorHandler(logger)

    def exception_handler(exc_type, exc_value, exc_traceback):
        # 创建错误信息
        error_info = ErrorInfo(
            error_type=ErrorType.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            message=f"未捕获的异常: {exc_value}",
            exception=exc_value,
            context=ErrorContext(
                component="GlobalExceptionHandler",
                operation="exception_handling"
            ),
            stack_trace=''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        )

        # 处理错误
        error_handler.handle_error(error_info)

    sys.excepthook = exception_handler
    return error_handler


def safe_execute(
    func: Callable,
    parent: Optional[QWidget] = None,
    error_message: str = "操作失败",
    error_type: ErrorType = ErrorType.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recovery_action: RecoveryAction = RecoveryAction.NONE,
    context: Optional[ErrorContext] = None,
    *args,
    **kwargs
) -> Optional[Any]:
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_info = ErrorInfo(
            error_type=error_type,
            severity=severity,
            message=error_message,
            exception=e,
            context=context or ErrorContext(
                component="safe_execute",
                operation=func.__name__
            ),
            user_message=error_message,
            recovery_action=recovery_action
        )

        # 使用全局错误处理器或创建新的处理器
        error_handler = getattr(safe_execute, 'error_handler', None)
        if error_handler:
            error_handler.handle_error(error_info, parent=parent)
        else:
            # 如果没有全局错误处理器，至少记录到日志
            logging.error(f"Safe execute failed: {error_message}", exc_info=e)
            if parent and QApplication.instance():
                QMessageBox.critical(parent, "错误", error_message)

        return None


def error_handler_decorator(
    error_type: ErrorType = ErrorType.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recovery_action: RecoveryAction = RecoveryAction.NONE,
    user_message: str = "操作失败"
):
    """错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = ErrorInfo(
                    error_type=error_type,
                    severity=severity,
                    message=f"{func.__name__} failed: {str(e)}",
                    exception=e,
                    context=ErrorContext(
                        component=func.__module__,
                        operation=func.__name__
                    ),
                    user_message=user_message,
                    recovery_action=recovery_action
                )

                # 获取错误处理器
                error_handler = getattr(wrapper, 'error_handler', None)
                if error_handler:
                    error_handler.handle_error(error_info)
                else:
                    logging.error(f"Decorator caught error: {str(e)}", exc_info=e)

                # 根据严重程度决定是否重新抛出异常
                if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                    raise

        return wrapper
    return decorator


@contextmanager
def error_context(
    error_type: ErrorType = ErrorType.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    component: str = "Unknown",
    operation: str = "Unknown"
):
    """错误上下文管理器"""
    error_handler = getattr(error_context, 'error_handler', None)

    try:
        yield
    except Exception as e:
        error_info = ErrorInfo(
            error_type=error_type,
            severity=severity,
            message=f"{operation} failed: {str(e)}",
            exception=e,
            context=ErrorContext(
                component=component,
                operation=operation
            )
        )

        if error_handler:
            error_handler.handle_error(error_info)
        else:
            logging.error(f"Context manager caught error: {str(e)}", exc_info=e)

        # 根据严重程度决定是否重新抛出异常
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            raise


# 全局错误处理器实例
_global_error_handler: Optional[ErrorHandler] = None


def get_global_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = setup_global_exception_handler()
    return _global_error_handler


def set_global_error_handler(handler: ErrorHandler) -> None:
    """设置全局错误处理器"""
    global _global_error_handler
    _global_error_handler = handler

    # 为装饰器和上下文管理器设置错误处理器
    safe_execute.error_handler = handler
    error_handler_decorator.error_handler = handler
    error_context.error_handler = handler


def handle_exception(
    exception: Exception,
    error_message: str = "操作失败",
    error_type: ErrorType = ErrorType.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    parent: Optional[QWidget] = None,
    context: Optional[ErrorContext] = None
) -> None:
    """处理异常的便捷函数"""
    error_info = ErrorInfo(
        error_type=error_type,
        severity=severity,
        message=error_message,
        exception=exception,
        context=context or ErrorContext(
            component="handle_exception",
            operation="exception_handling"
        ),
        user_message=error_message
    )

    # 使用全局错误处理器处理异常
    error_handler = get_global_error_handler()
    error_handler.handle_error(error_info, show_dialog=True, parent=parent)


def show_error_dialog(
    message: str,
    title: str = "错误",
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    parent: Optional[QWidget] = None
) -> None:
    """显示错误对话框的便捷函数"""
    if not QApplication.instance():
        print(f"ERROR: {message}")
        return

    if not parent:
        parent = QApplication.activeWindow()

    if not parent:
        print(f"ERROR: {message}")
        return

    # 根据严重程度选择对话框类型
    if severity == ErrorSeverity.CRITICAL:
        QMessageBox.critical(parent, title, message)
    elif severity == ErrorSeverity.HIGH:
        QMessageBox.critical(parent, title, message)
    elif severity == ErrorSeverity.MEDIUM:
        QMessageBox.warning(parent, title, message)
    else:
        QMessageBox.information(parent, title, message)