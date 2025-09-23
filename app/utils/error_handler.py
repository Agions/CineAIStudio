#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 错误处理模块
提供全局异常处理和错误对话框功能
"""

import sys
import traceback
from typing import Optional, Callable, Any
from PyQt6.QtWidgets import QMessageBox, QWidget


class ErrorHandler:
    """错误处理器"""

    def __init__(self, logger=None):
        """初始化错误处理器"""
        self.logger = logger

    def handle_error(self, error_info):
        """处理错误"""
        if self.logger:
            self.logger.error(f"错误: {error_info.message}")
        else:
            print(f"错误: {error_info.message}")

    def show_error_dialog(self, parent, title, message):
        """显示错误对话框"""
        QMessageBox.critical(parent, title, message)


def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    print(f"未捕获的异常: {exc_value}")
    traceback.print_exception(exc_type, exc_value, exc_traceback)


def show_error_dialog(parent: QWidget, title: str, message: str) -> None:
    """显示错误对话框"""
    QMessageBox.critical(parent, title, message)


def setup_global_exception_handler(logger=None) -> ErrorHandler:
    """设置全局异常处理器"""
    def exception_handler(exc_type, exc_value, exc_traceback):
        if logger:
            logger.error(f"未捕获的异常: {exc_value}")
        else:
            print(f"未捕获的异常: {exc_value}")
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler
    return ErrorHandler(logger)


def safe_execute(
    func: Callable,
    parent: Optional[QWidget] = None,
    error_message: str = "操作失败",
    *args,
    **kwargs
) -> Optional[any]:
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_exception(e, parent, "错误", error_message)
        return None