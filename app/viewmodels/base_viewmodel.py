#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ViewModel 基类
所有 ViewModel 继承此类，统一信号/状态管理
"""

from typing import Any, Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class BaseViewModel(QObject):
    """
    ViewModel 基类

    职责：
    - 持有 UI 状态
    - 调用 Service 层获取/处理数据
    - 通过信号通知 UI 更新
    - UI 不直接接触 Service 层
    """

    # 通用信号
    loading_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._is_loading = False

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @is_loading.setter
    def is_loading(self, value: bool):
        if self._is_loading != value:
            self._is_loading = value
            self.loading_changed.emit(value)

    def _handle_error(self, error: Exception, context: str = ""):
        """统一错误处理"""
        msg = f"{context}: {error}" if context else str(error)
        self.error_occurred.emit(msg)

    def dispose(self):
        """清理资源，子类可重写"""
        pass
