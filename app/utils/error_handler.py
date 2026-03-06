#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 错误处理模块
提供全局异常处理和错误对话框功能
"""

import sys
import traceback
from typing import Optional, Callable, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import QMessageBox, QWidget


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    error_type: str
    severity: str
    message: str
    exception: Exception = None
    details: str = ""


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