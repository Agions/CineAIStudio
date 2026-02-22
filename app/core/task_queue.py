#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 任务队列
管理视频处理、AI 调用等耗时任务，避免阻塞 UI
"""

import threading
import queue
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from PyQt6.QtCore import QObject, pyqtSignal


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    elapsed: float = 0.0


@dataclass(order=True)
class Task:
    priority: int
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8], compare=False)
    name: str = field(default="", compare=False)
    func: Callable = field(default=None, compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    cancel_flag: threading.Event = field(default_factory=threading.Event, compare=False)


class TaskQueue(QObject):
    """
    线程安全的任务队列

    特性：
    - 优先级排序
    - 可取消任务
    - 并发控制
    - 进度/完成信号回传 UI
    """

    task_started = pyqtSignal(str, str)          # task_id, name
    task_completed = pyqtSignal(str, object)     # task_id, result
    task_failed = pyqtSignal(str, str)           # task_id, error
    task_progress = pyqtSignal(str, int, str)    # task_id, percent, message
    queue_empty = pyqtSignal()

    def __init__(self, max_workers: int = 3, parent=None):
        super().__init__(parent)
        self._queue = queue.PriorityQueue()
        self._workers = []  # type: List[threading.Thread]
        self._max_workers = max_workers
        self._tasks = {}  # type: Dict[str, Task]
        self._running = True
        self._lock = threading.Lock()

        # 启动工作线程
        for i in range(max_workers):
            t = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name=f"TaskWorker-{i}"
            )
            t.start()
            self._workers.append(t)

    def submit(self, func: Callable, *args,
               name: str = "",
               priority: TaskPriority = TaskPriority.NORMAL,
               **kwargs) -> str:
        """
        提交任务

        Returns:
            task_id
        """
        task = Task(
            priority=-priority.value,  # 负数使高优先级排前面
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
        )

        with self._lock:
            self._tasks[task.task_id] = task

        self._queue.put(task)
        return task.task_id

    def cancel(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                task.cancel_flag.set()
                task.status = TaskStatus.CANCELLED
                return True
        return False

    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        with self._lock:
            task = self._tasks.get(task_id)
            return task.status if task else None

    def get_pending_count(self) -> int:
        return self._queue.qsize()

    def _worker_loop(self):
        """工作线程主循环"""
        while self._running:
            try:
                task = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if task.cancel_flag.is_set():
                self._queue.task_done()
                continue

            task.status = TaskStatus.RUNNING
            self.task_started.emit(task.task_id, task.name)

            start_time = time.time()
            try:
                result = task.func(*task.args, **task.kwargs)
                elapsed = time.time() - start_time

                if task.cancel_flag.is_set():
                    task.status = TaskStatus.CANCELLED
                else:
                    task.status = TaskStatus.COMPLETED
                    self.task_completed.emit(task.task_id, result)

            except Exception as e:
                task.status = TaskStatus.FAILED
                self.task_failed.emit(task.task_id, str(e))

            self._queue.task_done()

            if self._queue.empty():
                self.queue_empty.emit()

    def shutdown(self, wait: bool = True):
        """关闭队列"""
        self._running = False
        if wait:
            for w in self._workers:
                w.join(timeout=5)

    def cancel_all(self):
        """取消所有待处理任务"""
        with self._lock:
            for task in self._tasks.values():
                if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                    task.cancel_flag.set()
                    task.status = TaskStatus.CANCELLED


# 全局任务队列
_task_queue = None


def get_task_queue(max_workers: int = 3) -> TaskQueue:
    """获取全局任务队列"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue(max_workers=max_workers)
    return _task_queue


def shutdown_task_queue():
    """关闭全局任务队列"""
    global _task_queue
    if _task_queue:
        _task_queue.shutdown()
        _task_queue = None
