#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 事件总线模块
提供事件发布/订阅功能
"""

from typing import Dict, List, Callable, Any
from .logger import Logger


class EventBus:
    """事件总线"""

    def __init__(self):
        """初始化事件总线"""
        self._handlers: Dict[str, List[Callable]] = {}
        self.logger = Logger("EventBus")

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """订阅事件
        
        Args:
            event_name: 事件名称
            handler: 事件处理函数
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        # 避免重复订阅
        if handler not in self._handlers[event_name]:
            self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """取消订阅事件
        
        Args:
            event_name: 事件名称
            handler: 事件处理函数
        """
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
            except ValueError:
                pass

    def publish(self, event_name: str, data: Any = None) -> None:
        """发布事件
        
        Args:
            event_name: 事件名称
            data: 事件数据，可选
        """
        if event_name in self._handlers:
            for handler in self._handlers[event_name]:
                try:
                    handler(data)
                except Exception as e:
                    self.logger.error(f"事件 {event_name} 处理错误: {e}")

    def emit(self, event_name: str, data: Any = None) -> None:
        """发布事件（emit是publish的别名，保持API兼容性）
        
        Args:
            event_name: 事件名称
            data: 事件数据，可选
        """
        self.publish(event_name, data)

    def clear_handlers(self, event_name: str = None) -> None:
        """清除事件处理器
        
        Args:
            event_name: 可选，指定事件名称，若为None则清除所有事件处理器
        """
        if event_name:
            if event_name in self._handlers:
                self._handlers[event_name].clear()
        else:
            self._handlers.clear()

    def get_handler_count(self, event_name: str = None) -> int:
        """获取事件处理器数量
        
        Args:
            event_name: 可选，指定事件名称，若为None则返回所有事件处理器总数
        
        Returns:
            int: 事件处理器数量
        """
        if event_name:
            return len(self._handlers.get(event_name, []))
        else:
            return sum(len(handlers) for handlers in self._handlers.values())

    def has_handlers(self, event_name: str) -> bool:
        """检查事件是否有处理器
        
        Args:
            event_name: 事件名称
        
        Returns:
            bool: 若事件有处理器则返回True，否则返回False
        """
        return event_name in self._handlers and len(self._handlers[event_name]) > 0