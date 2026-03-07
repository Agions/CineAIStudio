#!/usr/bin/env python3
"""测试事件总线"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from app.core.event_bus import EventBus, event_bus


class TestListener(QObject):
    """测试监听器"""
    received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.received.connect(self._on_received)
        self.messages = []
        
    def _on_received(self, message):
        self.messages.append(message)


@pytest.fixture
def qapp():
    """创建 QApplication"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_subscribe_and_emit(qapp):
    """测试订阅和发布"""
    listener = TestListener()
    
    # 订阅事件
    event_bus.subscribe("test.event", listener.received)
    
    # 发布事件
    event_bus.emit("test.event", "hello")
    
    # 处理事件循环
    from PyQt6.QtCore import QCoreApplication
    QCoreApplication.processEvents()
    
    assert "hello" in listener.messages


def test_unsubscribe(qapp):
    """测试取消订阅"""
    listener = TestListener()
    
    event_bus.subscribe("test.event", listener.received)
    event_bus.unsubscribe("test.event", listener.received)
    
    event_bus.emit("test.event", "test")
    QCoreApplication.processEvents()
    
    assert len(listener.messages) == 0


def test_multiple_listeners(qapp):
    """测试多个监听器"""
    listener1 = TestListener()
    listener2 = TestListener()
    
    event_bus.subscribe("test.event", listener1.received)
    event_bus.subscribe("test.event", listener2.received)
    
    event_bus.emit("test.event", "broadcast")
    QCoreApplication.processEvents()
    
    assert "broadcast" in listener1.messages
    assert "broadcast" in listener2.messages


def test_emit_to_all_listeners(qapp):
    """测试向所有监听器发送"""
    listener1 = TestListener()
    listener2 = TestListener()
    
    event_bus.subscribe("event1", listener1.received)
    event_bus.subscribe("event2", listener2.received)
    
    event_bus.emit_to_all("hello")
    QCoreApplication.processEvents()
    
    assert "hello" in listener1.messages
    assert "hello" in listener2.messages
