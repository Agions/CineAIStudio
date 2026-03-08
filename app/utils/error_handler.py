#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 错误处理模块
提供全局异常处理和错误对话框功能

功能:
- 全局异常捕获
- 错误分类 (API/网络/文件/UI/未知)
- 错误恢复建议
- 错误重试机制
- 错误上报
"""

import sys
import traceback
import logging
import functools
from typing import Optional, Callable, Any, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import QObject, pyqtSignal


class ErrorType(Enum):
    """错误类型"""
    API = "api"              # API 调用错误
    NETWORK = "network"      # 网络错误
    FILE = "file"           # 文件操作错误
    VALIDATION = "validation"  # 数据验证错误
    PERMISSION = "permission"  # 权限错误
    TIMEOUT = "timeout"     # 超时错误
    UI = "ui"               # UI 错误
    UNKNOWN = "unknown"     # 未知错误


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """恢复操作"""
    RETRY = "retry"           # 重试
    FALLBACK = "fallback"    # 使用备用方案
    SKIP = "skip"            # 跳过
    NOTIFY = "notify"         # 通知用户
    EXIT = "exit"             # 退出程序


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    error_type: str = "unknown"
    severity: str = "medium"
    message: str = ""
    exception: Exception = None
    details: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    recovery_actions: List[RecoveryAction] = field(default_factory=list)


class ErrorHandler:
    """错误处理器"""

    def __init__(self, logger=None):
        """初始化错误处理器"""
        self.logger = logger

    def handle_error(self, error_info: ErrorInfo):
        """处理错误
        
        Args:
            error_info: 错误信息对象
        """
        error_message = f"{error_info.error_type}: {error_info.message}"
        if error_info.details:
            error_message += f"\n详情: {error_info.details}"
        
        if self.logger:
            if error_info.severity == "critical":
                self.logger.critical(error_message, exc_info=error_info.exception)
            elif error_info.severity == "error":
                self.logger.error(error_message, exc_info=error_info.exception)
            elif error_info.severity == "warning":
                self.logger.warning(error_message)
            else:
                self.logger.info(error_message)
        else:
            print(error_message)
            if error_info.exception:
                traceback.print_exception(type(error_info.exception), error_info.exception, error_info.exception.__traceback__)

    def show_error_dialog(self, parent: Optional[QWidget], title: str, message: str, details: str = "") -> None:
        """显示错误对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 错误消息
            details: 详细错误信息
        """
        if parent:
            msg_box = QMessageBox(parent)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            if details:
                msg_box.setDetailedText(details)
            msg_box.exec()
        else:
            QMessageBox.critical(None, title, message)

    def log_and_show_error(self, parent: Optional[QWidget], error_info: ErrorInfo) -> None:
        """记录错误并显示错误对话框
        
        Args:
            parent: 父窗口
            error_info: 错误信息对象
        """
        self.handle_error(error_info)
        self.show_error_dialog(parent, "错误", error_info.message, error_info.details)


def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    print(f"未捕获的异常: {exc_value}")
    traceback.print_exception(exc_type, exc_value, exc_traceback)


def show_error_dialog(parent: Optional[QWidget], title: str, message: str, details: str = "") -> None:
    """显示错误对话框
    
    Args:
        parent: 父窗口
        title: 对话框标题
        message: 错误消息
        details: 详细错误信息
    """
    if parent:
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        if details:
            msg_box.setDetailedText(details)
        msg_box.exec()
    else:
        QMessageBox.critical(None, title, message)


def setup_global_exception_handler(logger=None) -> ErrorHandler:
    """设置全局异常处理器
    
    Args:
        logger: 日志记录器
        
    Returns:
        ErrorHandler: 错误处理器实例
    """
    def exception_handler(exc_type, exc_value, exc_traceback):
        error_info = ErrorInfo(
            error_type="UnhandledException",
            severity="critical",
            message=f"未捕获的异常: {exc_value}",
            exception=exc_value,
            details=str(exc_value)
        )
        
        if logger:
            logger.critical(error_info.message, exc_info=(exc_type, exc_value, exc_traceback))
        else:
            print(f"{error_info.error_type}: {error_info.message}")
            traceback.print_exception(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler
    return ErrorHandler(logger)


def safe_execute(
    func: Callable,
    parent: Optional[QWidget] = None,
    error_message: str = "操作失败",
    logger=None,
    *args,
    **kwargs
) -> Optional[Any]:
    """安全执行函数
    
    Args:
        func: 要执行的函数
        parent: 父窗口，用于显示错误对话框
        error_message: 错误消息
        logger: 日志记录器
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        Any: 函数返回值，如果执行失败则返回None
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_info = ErrorInfo(
            error_type="ExecutionError",
            severity="error",
            message=error_message,
            exception=e,
            details=str(e)
        )
        
        # 记录错误
        if logger:
            logger.error(error_info.message, exc_info=e)
        else:
            print(f"{error_info.error_type}: {error_info.message}")
            traceback.print_exception(type(e), e, e.__traceback__)
        
        # 显示错误对话框
        if parent:
            show_error_dialog(parent, "错误", error_info.message, error_info.details)
        
        return None


# ============ 错误分类和恢复 ============

def classify_error(exception: Exception) -> ErrorType:
    """分类错误类型
    
    Args:
        exception: 异常对象
        
    Returns:
        ErrorType: 错误类型
    """
    error_msg = str(exception).lower()
    error_type = type(exception).__name__.lower()
    
    # 网络相关
    if any(kw in error_msg for kw in ['network', 'connection', 'timeout', 'dns', 'ssl']):
        return ErrorType.NETWORK
    
    # API 相关
    if any(kw in error_msg for kw in ['api', 'rate limit', 'quota', '403', '401', '429']):
        return ErrorType.API
    
    # 文件相关
    if any(kw in error_msg for kw in ['file', 'not found', 'permission denied', 'ENOENT', 'IOError']):
        return ErrorType.FILE
    
    # 超时
    if 'timeout' in error_msg or 'timed out' in error_msg:
        return ErrorType.TIMEOUT
    
    # 权限
    if 'permission' in error_msg or 'denied' in error_msg:
        return ErrorType.PERMISSION
    
    # 验证
    if any(kw in error_type for kw in ['validation', 'valueerror', 'typeerror']):
        return ErrorType.VALIDATION
    
    return ErrorType.UNKNOWN


def get_recovery_actions(error_type: ErrorType, exception: Exception) -> List[RecoveryAction]:
    """获取错误恢复建议
    
    Args:
        error_type: 错误类型
        exception: 异常对象
        
    Returns:
        List[RecoveryAction]: 恢复操作列表
    """
    actions = [RecoveryAction.NOTIFY]
    
    if error_type == ErrorType.NETWORK:
        actions.extend([RecoveryAction.RETRY, RecoveryAction.FALLBACK])
    elif error_type == ErrorType.API:
        if 'rate limit' in str(exception).lower():
            actions.insert(0, RecoveryAction.WAIT)  # 等待后重试
        else:
            actions.extend([RecoveryAction.RETRY, RecoveryAction.FALLBACK])
    elif error_type == ErrorType.TIMEOUT:
        actions.extend([RecoveryAction.RETRY])
    elif error_type == ErrorType.FILE:
        if 'not found' in str(exception).lower():
            actions = [RecoveryAction.SKIP, RecoveryAction.NOTIFY]
        else:
            actions.extend([RecoveryAction.RETRY])
    
    return actions


# ============ 重试装饰器 ============

def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger=None
):
    """重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间(秒)
        backoff: 延迟倍增
        exceptions: 需要重试的异常类型
        logger: 日志记录器
        
    Example:
        @retry_on_error(max_retries=3, delay=1.0)
        def fetch_data():
            return api_call()
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if logger:
                            logger.warning(
                                f"重试 {attempt + 1}/{max_retries} - {str(e)}, "
                                f"等待 {current_delay}s..."
                            )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if logger:
                            logger.error(f"重试失败 {max_retries} 次: {str(e)}")
            
            raise last_exception
        return wrapper
    return decorator


# ============ 错误上报 (可选) ============

class ErrorReporter:
    """错误上报器"""
    
    def __init__(self, endpoint: str = "", api_key: str = ""):
        self.endpoint = endpoint
        self.api_key = api_key
        self.errors: List[ErrorInfo] = []
    
    def report(self, error_info: ErrorInfo) -> bool:
        """上报错误
        
        Args:
            error_info: 错误信息
            
        Returns:
            bool: 是否上报成功
        """
        if not self.endpoint:
            return False
            
        self.errors.append(error_info)
        
        # 实际上报逻辑 (可选实现)
        # 可以发送到 Sentry、LogRocket 等服务
        if self.endpoint:
            try:
                import json
                # 构建上报数据
                payload = {
                    "error_type": error_info.error_type,
                    "message": error_info.message,
                    "details": error_info.details,
                    "timestamp": error_info.timestamp.isoformat(),
                }
                # 发送错误报告到服务端
                try:
                    import httpx
                    if hasattr(self, 'endpoint') and self.endpoint:
                        headers = {"Content-Type": "application/json"}
                        if hasattr(self, 'api_key') and self.api_key:
                            headers["Authorization"] = f"Bearer {self.api_key}"
                        httpx.post(self.endpoint, json=payload, headers=headers, timeout=5.0)
                except Exception:
                    pass  # 上报失败不影响主流程
        return True
    
    def get_error_summary(self) -> Dict[str, int]:
        """获取错误摘要
        
        Returns:
            Dict[str, int]: 错误类型统计
        """
        summary = {}
        for error in self.errors:
            error_type = error.error_type
            summary[error_type] = summary.get(error_type, 0) + 1
        return summary