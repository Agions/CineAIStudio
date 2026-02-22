#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 异步桥接模块
解决 PyQt6 同步 UI 与 async LLM Provider 之间的交互问题
"""

import asyncio
import threading
from typing import Any, Callable, Optional, TypeVar
from concurrent.futures import Future

from PyQt6.QtCore import QObject, pyqtSignal, QThread


T = TypeVar('T')


class AsyncBridge(QObject):
    """
    异步桥接器

    在 PyQt6 的同步事件循环中安全地调用 async 函数，
    并将结果通过信号传递回 UI 线程。
    """

    # 通用结果信号
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._loop = None
        self._thread = None
        self._start_event_loop()

    def _start_event_loop(self):
        """在后台线程中启动 asyncio 事件循环"""
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="AsyncBridge-EventLoop"
        )
        self._thread.start()

    def _run_loop(self):
        """运行事件循环"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run_async(self, coro, callback: Optional[Callable] = None,
                  error_callback: Optional[Callable] = None):
        """
        在后台事件循环中执行异步协程

        Args:
            coro: 异步协程
            callback: 成功回调（在 UI 线程中调用）
            error_callback: 错误回调（在 UI 线程中调用）
        """
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)

        def _on_done(fut):
            try:
                result = fut.result()
                if callback:
                    self.result_ready.emit(result)
                    # 断开之前的连接再连新的
                    try:
                        self.result_ready.disconnect()
                    except TypeError:
                        pass
                    self.result_ready.connect(callback)
                    self.result_ready.emit(result)
            except Exception as e:
                if error_callback:
                    self.error_occurred.emit(str(e))
                    try:
                        self.error_occurred.disconnect()
                    except TypeError:
                        pass
                    self.error_occurred.connect(error_callback)
                    self.error_occurred.emit(str(e))

        future.add_done_callback(_on_done)
        return future

    def run_sync(self, coro, timeout: float = 30.0) -> Any:
        """
        同步等待异步协程结果（阻塞调用，不要在 UI 线程中使用）

        Args:
            coro: 异步协程
            timeout: 超时时间（秒）

        Returns:
            协程返回值
        """
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    def shutdown(self):
        """关闭事件循环"""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)


class AsyncWorker(QThread):
    """
    异步工作线程

    用于在后台执行耗时任务（视频处理、AI 调用等），
    不阻塞 UI 线程。
    """

    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, coro_or_func, *args, **kwargs):
        super().__init__()
        self._coro_or_func = coro_or_func
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            if asyncio.iscoroutinefunction(self._coro_or_func):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self._coro_or_func(*self._args, **self._kwargs)
                    )
                finally:
                    loop.close()
            else:
                result = self._coro_or_func(*self._args, **self._kwargs)

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# 全局异步桥接实例
_async_bridge = None


def get_async_bridge() -> AsyncBridge:
    """获取全局异步桥接实例"""
    global _async_bridge
    if _async_bridge is None:
        _async_bridge = AsyncBridge()
    return _async_bridge


def shutdown_async_bridge():
    """关闭全局异步桥接"""
    global _async_bridge
    if _async_bridge:
        _async_bridge.shutdown()
        _async_bridge = None
