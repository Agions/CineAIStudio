#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量视频处理器
支持队列化的批量视频分析、渲染、导出
"""

import os
import time
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal


class BatchStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchItem:
    """批量处理项"""
    id: str
    input_path: str
    output_path: str = ""
    status: BatchStatus = BatchStatus.PENDING
    progress: int = 0
    error: str = ""
    result: Any = None
    started_at: float = 0.0
    finished_at: float = 0.0


@dataclass
class BatchJob:
    """批量处理任务"""
    job_id: str
    items: List[BatchItem] = field(default_factory=list)
    status: BatchStatus = BatchStatus.PENDING
    created_at: float = field(default_factory=time.time)
    max_concurrent: int = 2


class BatchVideoProcessor(QObject):
    """
    批量视频处理器

    功能：
    - 批量视频分析
    - 批量渲染/转码
    - 批量导出
    - 进度追踪
    - 错误恢复
    """

    # 信号
    item_started = pyqtSignal(str, str)        # job_id, item_id
    item_completed = pyqtSignal(str, str)      # job_id, item_id
    item_failed = pyqtSignal(str, str, str)    # job_id, item_id, error
    item_progress = pyqtSignal(str, str, int)  # job_id, item_id, percent
    job_completed = pyqtSignal(str, dict)      # job_id, summary
    job_progress = pyqtSignal(str, int)        # job_id, overall_percent

    def __init__(self, parent=None):
        super().__init__(parent)
        self._jobs = {}  # type: Dict[str, BatchJob]
        self._cancel_flags = {}  # type: Dict[str, threading.Event]
        self._semaphore = threading.Semaphore(2)

    def create_job(self, video_paths: List[str],
                   output_dir: str = "",
                   job_id: str = "",
                   max_concurrent: int = 2) -> str:
        """
        创建批量处理任务

        Args:
            video_paths: 视频文件路径列表
            output_dir: 输出目录
            job_id: 任务ID（自动生成）
            max_concurrent: 最大并发数

        Returns:
            job_id
        """
        if not job_id:
            job_id = f"batch_{int(time.time())}"

        items = []
        for i, path in enumerate(video_paths):
            name = Path(path).stem
            out_path = ""
            if output_dir:
                out_path = str(Path(output_dir) / f"{name}_processed.mp4")

            items.append(BatchItem(
                id=f"item_{i}",
                input_path=path,
                output_path=out_path,
            ))

        job = BatchJob(
            job_id=job_id,
            items=items,
            max_concurrent=max_concurrent,
        )
        self._jobs[job_id] = job
        self._cancel_flags[job_id] = threading.Event()
        return job_id

    def start_job(self, job_id: str,
                  process_func: Callable[[BatchItem], Any]) -> None:
        """
        启动批量处理（后台线程）

        Args:
            job_id: 任务ID
            process_func: 处理函数，接收 BatchItem，返回结果
        """
        if job_id not in self._jobs:
            raise ValueError(f"任务 {job_id} 不存在")

        thread = threading.Thread(
            target=self._run_job,
            args=(job_id, process_func),
            daemon=True,
            name=f"BatchJob-{job_id}",
        )
        thread.start()

    def cancel_job(self, job_id: str):
        """取消任务"""
        flag = self._cancel_flags.get(job_id)
        if flag:
            flag.set()

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        job = self._jobs.get(job_id)
        if not job:
            return None

        completed = sum(1 for i in job.items
                       if i.status == BatchStatus.COMPLETED)
        failed = sum(1 for i in job.items
                    if i.status == BatchStatus.FAILED)
        total = len(job.items)

        return {
            "job_id": job_id,
            "status": job.status.value,
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": total - completed - failed,
            "progress": int(completed / total * 100) if total > 0 else 0,
        }

    def _run_job(self, job_id: str,
                 process_func: Callable[[BatchItem], Any]):
        """执行批量任务"""
        job = self._jobs[job_id]
        job.status = BatchStatus.PROCESSING
        cancel_flag = self._cancel_flags[job_id]

        semaphore = threading.Semaphore(job.max_concurrent)
        threads = []

        for item in job.items:
            if cancel_flag.is_set():
                item.status = BatchStatus.CANCELLED
                continue

            semaphore.acquire()
            t = threading.Thread(
                target=self._process_item,
                args=(job_id, item, process_func, semaphore, cancel_flag),
                daemon=True,
            )
            t.start()
            threads.append(t)

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 汇总结果
        completed = sum(1 for i in job.items
                       if i.status == BatchStatus.COMPLETED)
        failed = sum(1 for i in job.items
                    if i.status == BatchStatus.FAILED)

        if cancel_flag.is_set():
            job.status = BatchStatus.CANCELLED
        elif failed == 0:
            job.status = BatchStatus.COMPLETED
        else:
            job.status = BatchStatus.COMPLETED  # 部分成功也算完成

        summary = {
            "total": len(job.items),
            "completed": completed,
            "failed": failed,
            "cancelled": sum(1 for i in job.items
                           if i.status == BatchStatus.CANCELLED),
        }
        self.job_completed.emit(job_id, summary)

    def _process_item(self, job_id: str, item: BatchItem,
                      process_func: Callable, semaphore: threading.Semaphore,
                      cancel_flag: threading.Event):
        """处理单个项目"""
        try:
            if cancel_flag.is_set():
                item.status = BatchStatus.CANCELLED
                return

            item.status = BatchStatus.PROCESSING
            item.started_at = time.time()
            self.item_started.emit(job_id, item.id)

            result = process_func(item)

            item.result = result
            item.status = BatchStatus.COMPLETED
            item.finished_at = time.time()
            self.item_completed.emit(job_id, item.id)

        except Exception as e:
            item.status = BatchStatus.FAILED
            item.error = str(e)
            item.finished_at = time.time()
            self.item_failed.emit(job_id, item.id, str(e))

        finally:
            semaphore.release()
            # 更新总进度
            job = self._jobs[job_id]
            done = sum(1 for i in job.items
                      if i.status in (BatchStatus.COMPLETED,
                                      BatchStatus.FAILED,
                                      BatchStatus.CANCELLED))
            pct = int(done / len(job.items) * 100) if job.items else 100
            self.job_progress.emit(job_id, pct)
