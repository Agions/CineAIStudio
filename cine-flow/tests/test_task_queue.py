#!/usr/bin/env python3
"""测试任务队列"""

import time
import threading
import pytest

from app.core.task_queue import TaskQueue, TaskPriority, TaskStatus


@pytest.fixture
def qapp():
    """创建 QApplication（Qt 信号需要）"""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_basic_submit(qapp):
    """基本提交和完成"""
    q = TaskQueue(max_workers=2)
    results = []

    q.task_completed.connect(lambda tid, r: results.append(r))

    def add(a, b):
        return a + b

    task_id = q.submit(add, 1, 2, name="add")
    
    # 处理事件循环让信号传递
    from PyQt6.QtCore import QCoreApplication
    for _ in range(20):
        QCoreApplication.processEvents()
        time.sleep(0.05)

    assert len(results) == 1
    assert results[0] == 3
    q.shutdown()


def test_task_cancel(qapp):
    """取消任务"""
    q = TaskQueue(max_workers=1)

    def slow_task():
        time.sleep(10)
        return "done"

    # 先占满 worker
    q.submit(slow_task, name="blocker")
    time.sleep(0.1)

    # 提交第二个任务然后取消
    tid = q.submit(slow_task, name="to_cancel")
    assert q.cancel(tid) is True

    q.shutdown(wait=False)


def test_priority_ordering(qapp):
    """优先级排序"""
    q = TaskQueue(max_workers=1)
    order = []

    gate = threading.Event()

    def blocker():
        gate.wait(timeout=5)

    def record(name):
        order.append(name)

    q.submit(blocker, name="gate")
    time.sleep(0.1)

    q.submit(record, "low", name="low", priority=TaskPriority.LOW)
    q.submit(record, "urgent", name="urgent", priority=TaskPriority.URGENT)
    q.submit(record, "normal", name="normal", priority=TaskPriority.NORMAL)

    gate.set()
    time.sleep(1)

    assert order[0] == "urgent"
    q.shutdown()


def test_error_handling(qapp):
    """错误处理"""
    q = TaskQueue(max_workers=1)
    errors = []

    q.task_failed.connect(lambda tid, err: errors.append(err))

    def failing():
        raise ValueError("test error")

    q.submit(failing, name="fail")
    
    from PyQt6.QtCore import QCoreApplication
    for _ in range(20):
        QCoreApplication.processEvents()
        time.sleep(0.05)

    assert len(errors) == 1
    assert "test error" in errors[0]
    q.shutdown()
