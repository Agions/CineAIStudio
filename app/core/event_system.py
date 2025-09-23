#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 事件总线模块
提供事件发布/订阅功能
"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass


class EventBus:
    """事件总线"""

    def __init__(self):
        """初始化事件总线"""
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """订阅事件"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """取消订阅事件"""
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
            except ValueError:
                pass

    def publish(self, event_name: str, data: Any = None) -> None:
        """发布事件"""
        if event_name in self._handlers:
            for handler in self._handlers[event_name]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"事件处理错误: {e}")


class ApplicationState:
    """应用程序状态枚举"""
    INITIALIZING = "initializing"
    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


class ErrorType:
    """错误类型枚举"""
    UI = "ui"
    SYSTEM = "system"
    FILE = "file"
    NETWORK = "network"
    AI = "ai"


class ErrorSeverity:
    """错误严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    error_type: str
    severity: str
    message: str
    exception: Exception = None


class Application:
    """应用程序基类（简化版）"""

    def __init__(self, config):
        """初始化应用程序"""
        self.config = config
        self._state = ApplicationState.INITIALIZING
        self._services = {}

    def get_config(self):
        """获取配置"""
        return self.config

    def get_service(self, service_type):
        """获取服务"""
        for service in self._services.values():
            if isinstance(service, service_type):
                return service
        return None

    def initialize(self, argv):
        """初始化应用程序"""
        return True

    def start(self):
        """启动应用程序"""
        return True

    def run(self):
        """运行应用程序"""
        return 0

    def shutdown(self):
        """关闭应用程序"""
        pass

    def state_changed(self):
        """状态变更信号"""
        pass

    def error_occurred(self):
        """错误信号"""
        pass


class ErrorHandler:
    """错误处理器（简化版）"""

    def __init__(self, logger):
        """初始化错误处理器"""
        self.logger = logger

    def handle_error(self, error_info):
        """处理错误"""
        if self.logger:
            self.logger.error(f"错误: {error_info.message}")
        else:
            print(f"错误: {error_info.message}")


# 导入必要的模块