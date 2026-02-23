#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 视频处理性能优化器
提供视频渲染、编码、解码的性能优化功能
"""

import os
import tempfile
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Tuple
from pathlib import Path

from ...core.logger import Logger
from ...core.event_bus import EventBus


class OptimizationLevel(Enum):
    """优化级别"""
    DISABLED = "disabled"      # 禁用优化
    BASIC = "basic"           # 基础优化
    STANDARD = "standard"     # 标准优化
    AGGRESSIVE = "aggressive" # 激进优化


class CacheStrategy(Enum):
    """缓存策略"""
    NONE = "none"              # 无缓存
    MEMORY = "memory"          # 内存缓存
    DISK = "disk"              # 磁盘缓存
    HYBRID = "hybrid"          # 混合缓存


@dataclass
class PerformanceConfig:
    """性能配置"""
    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    cache_strategy: CacheStrategy = CacheStrategy.HYBRID
    max_memory_usage: int = 1024 * 1024 * 1024  # 1GB
    max_disk_cache: int = 10 * 1024 * 1024 * 1024  # 10GB
    thread_pool_size: int = 4
    process_pool_size: int = 2
    enable_gpu_acceleration: bool = True
    enable_multi_threading: bool = True
    enable_background_processing: bool = True
    cache_ttl: int = 3600  # 1小时
    preview_quality: str = "medium"  # low, medium, high
    chunk_size: int = 1024 * 1024  # 1MB chunks


class VideoTask:
    """视频处理任务"""

    def __init__(self, task_id: str, operation: str, input_path: str,
                 output_path: Optional[str] = None, parameters: Optional[Dict] = None):
        self.task_id = task_id
        self.operation = operation
        self.input_path = input_path
        self.output_path = output_path
        self.parameters = parameters or {}
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.status = "pending"
        self.progress = 0.0
        self.error: Optional[str] = None


class VideoCache:
    """视频缓存管理器"""

    def __init__(self, config: PerformanceConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self._memory_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_sizes: Dict[str, int] = {}
        self._memory_usage = 0
        self._lock = threading.RLock()
        self._temp_dir = Path(tempfile.mkdtemp(prefix="video_cache_"))

    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        with self._lock:
            if key in self._memory_cache:
                if self._is_cache_valid(key):
                    return self._memory_cache[key]
                else:
                    del self._memory_cache[key]
                    del self._cache_timestamps[key]
                    del self._cache_sizes[key]
                    return None

            if self.config.cache_strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
                cache_file = self._temp_dir / f"{key}.cache"
                if cache_file.exists():
                    if self._is_cache_valid(key):
                        try:
                            import pickle
                            with open(cache_file, 'rb') as f:
                                data = pickle.load(f)
                            # 加载到内存缓存
                            self._add_to_memory_cache(key, data)
                            return data
                        except Exception as e:
                            self.logger.warning(f"Failed to load cache {key}: {e}")
                            cache_file.unlink(missing_ok=True)

        return None

    def put(self, key: str, value: Any) -> None:
        """存储缓存项"""
        with self._lock:
            # 内存缓存
            if self.config.cache_strategy in [CacheStrategy.MEMORY, CacheStrategy.HYBRID]:
                self._add_to_memory_cache(key, value)

            # 磁盘缓存
            if self.config.cache_strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
                try:
                    import pickle
                    cache_file = self._temp_dir / f"{key}.cache"
                    with open(cache_file, 'wb') as f:
                        pickle.dump(value, f)
                except Exception as e:
                    self.logger.warning(f"Failed to save cache {key}: {e}")

    def clear(self, pattern: Optional[str] = None) -> None:
        """清除缓存"""
        with self._lock:
            if pattern:
                keys_to_remove = [k for k in self._memory_cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self._memory_cache[key]
                    del self._cache_timestamps[key]
                    del self._cache_sizes[key]

                # 清除磁盘缓存
                for cache_file in self._temp_dir.glob(f"*{pattern}*.cache"):
                    cache_file.unlink(missing_ok=True)
            else:
                self._memory_cache.clear()
                self._cache_timestamps.clear()
                self._cache_sizes.clear()
                self._memory_usage = 0

                # 清除所有磁盘缓存
                for cache_file in self._temp_dir.glob("*.cache"):
                    cache_file.unlink(missing_ok=True)

    def cleanup(self) -> None:
        """清理资源"""
        self.clear()
        self._temp_dir.rmdir(missing_ok=True)

    def get_memory_usage(self) -> int:
        """获取内存使用量"""
        return self._memory_usage

    def _add_to_memory_cache(self, key: str, value: Any) -> None:
        """添加到内存缓存"""
        import sys

        # 估算对象大小
        size = sys.getsizeof(value)

        # 检查内存限制
        if self._memory_usage + size > self.config.max_memory_usage:
            self._evict_lru()

        self._memory_cache[key] = value
        self._cache_timestamps[key] = time.time()
        self._cache_sizes[key] = size
        self._memory_usage += size

    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._cache_timestamps:
            return False
        return time.time() - self._cache_timestamps[key] < self.config.cache_ttl

    def _evict_lru(self) -> None:
        """LRU淘汰策略"""
        if not self._cache_timestamps:
            return

        # 找到最旧的缓存项
        oldest_key = min(self._cache_timestamps.keys(),
                        key=lambda k: self._cache_timestamps[k])

        # 移除最旧的项
        size = self._cache_sizes.get(oldest_key, 0)
        del self._memory_cache[oldest_key]
        del self._cache_timestamps[oldest_key]
        del self._cache_sizes[oldest_key]
        self._memory_usage -= size


class PerformanceOptimizer:
    """视频处理性能优化器"""

    def __init__(self, config: PerformanceConfig, logger: Logger, event_bus: EventBus):
        self.config = config
        self.logger = logger
        self.event_bus = event_bus

        # 线程池和进程池
        self._thread_pool = ThreadPoolExecutor(
            max_workers=config.thread_pool_size,
            thread_name_prefix="VideoOpt"
        )
        self._process_pool = ProcessPoolExecutor(
            max_workers=config.process_pool_size
        )

        # 缓存系统
        self.cache = VideoCache(config, logger)

        # 任务队列
        self._task_queue = queue.Queue()
        self._running_tasks: Dict[str, VideoTask] = {}
        self._completed_tasks: List[VideoTask] = []
        self._background_worker_thread = threading.Thread(
            target=self._background_worker, daemon=True
        )

        # 统计信息
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0.0,
            "average_task_time": 0.0
        }

        # 启动后台工作线程
        self._background_worker_thread.start()

    def optimize_video_operation(self, operation: str, input_path: str,
                                output_path: Optional[str] = None,
                                parameters: Optional[Dict] = None,
                                priority: int = 0) -> str:
        """优化视频处理操作"""
        task_id = f"task_{int(time.time() * 1000)}_{id(operation)}"

        task = VideoTask(
            task_id=task_id,
            operation=operation,
            input_path=input_path,
            output_path=output_path,
            parameters=parameters
        )

        # 根据优化级别选择处理策略
        if self.config.optimization_level == OptimizationLevel.AGGRESSIVE:
            # 激进优化：使用多进程
            self._process_pool.submit(self._execute_task, task)
        elif self.config.optimization_level == OptimizationLevel.STANDARD:
            # 标准优化：使用多线程
            self._thread_pool.submit(self._execute_task, task)
        else:
            # 基础优化：加入队列
            self._task_queue.put((priority, task))

        self._running_tasks[task_id] = task
        self._stats["total_tasks"] += 1

        self.event_bus.publish("video.task.started", {
            "task_id": task_id,
            "operation": operation
        })

        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self._running_tasks.get(task_id)
        if not task:
            # 查找已完成任务
            for completed_task in self._completed_tasks:
                if completed_task.task_id == task_id:
                    return {
                        "task_id": task_id,
                        "status": completed_task.status,
                        "progress": completed_task.progress,
                        "error": completed_task.error,
                        "created_at": completed_task.created_at,
                        "started_at": completed_task.started_at,
                        "completed_at": completed_task.completed_at
                    }
            return None

        return {
            "task_id": task_id,
            "status": task.status,
            "progress": task.progress,
            "error": task.error,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at
        }

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            if task.status == "pending":
                task.status = "cancelled"
                del self._running_tasks[task_id]
                self.event_bus.publish("video.task.cancelled", {"task_id": task_id})
                return True
        return False

    def optimize_preview_generation(self, video_path: str,
                                  timestamp: float,
                                  duration: float = 10.0) -> Optional[str]:
        """优化预览生成"""
        cache_key = f"preview_{video_path}_{timestamp}"

        # 尝试从缓存获取
        preview_path = self.cache.get(cache_key)
        if preview_path:
            self._stats["cache_hits"] += 1
            return preview_path

        self._stats["cache_misses"] += 1

        # 生成预览
        try:
            preview_path = self._generate_preview(video_path, timestamp, duration)
            self.cache.put(cache_key, preview_path)
            return preview_path
        except Exception as e:
            self.logger.error(f"Failed to generate preview: {e}")
            return None

    def optimize_thumbnail_generation(self, video_path: str,
                                    timestamps: List[float]) -> List[Optional[str]]:
        """批量优化缩略图生成"""
        results = []

        # 并行生成缩略图
        futures = []
        for timestamp in timestamps:
            future = self._thread_pool.submit(
                self._generate_thumbnail, video_path, timestamp
            )
            futures.append(future)

        # 收集结果
        for future in futures:
            try:
                thumbnail_path = future.result(timeout=30)
                results.append(thumbnail_path)
            except Exception as e:
                self.logger.warning(f"Failed to generate thumbnail: {e}")
                results.append(None)

        return results

    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "memory_usage": self.cache.get_memory_usage(),
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "hit_rate": (
                self._stats["cache_hits"] /
                (self._stats["cache_hits"] + self._stats["cache_misses"])
                if (self._stats["cache_hits"] + self._stats["cache_misses"]) > 0 else 0
            )
        }

    def get_performance_statistics(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            **self._stats,
            "running_tasks": len(self._running_tasks),
            "thread_pool_active": self._thread_pool._threads.__len__(),
            "process_pool_active": len(self._process_pool._processes)
        }

    def cleanup(self) -> None:
        """清理资源"""
        # 停止后台工作线程
        self._task_queue.put((float('inf'), None))  # 停止信号

        # 等待线程池和进程池完成
        self._thread_pool.shutdown(wait=True)
        self._process_pool.shutdown(wait=True)

        # 清理缓存
        self.cache.cleanup()

    # 私有方法

    def _background_worker(self) -> None:
        """后台工作线程"""
        while True:
            try:
                priority, task = self._task_queue.get(timeout=1.0)

                # 停止信号
                if task is None:
                    break

                # 执行任务
                self._execute_task(task)

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Background worker error: {e}")

    def _execute_task(self, task: VideoTask) -> None:
        """执行任务"""
        task.status = "running"
        task.started_at = time.time()

        try:
            # 这里应该根据操作类型执行具体的视频处理
            # 暂时使用模拟实现
            self._simulate_video_processing(task)

            task.status = "completed"
            task.completed_at = time.time()
            task.progress = 100.0

            self._stats["completed_tasks"] += 1

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = time.time()

            self._stats["failed_tasks"] += 1
            self.logger.error(f"Task {task.task_id} failed: {e}")

        finally:
            # 更新统计
            if task.started_at and task.completed_at:
                processing_time = task.completed_at - task.started_at
                self._stats["total_processing_time"] += processing_time

            # 移动到完成队列
            if task.task_id in self._running_tasks:
                del self._running_tasks[task.task_id]
            self._completed_tasks.append(task)

            # 保持完成队列大小
            if len(self._completed_tasks) > 1000:
                self._completed_tasks = self._completed_tasks[-500:]

            # 发布事件
            self.event_bus.publish("video.task.completed", {
                "task_id": task.task_id,
                "status": task.status,
                "error": task.error
            })

    def _simulate_video_processing(self, task: VideoTask) -> None:
        """模拟视频处理（临时实现）"""
        import time
        import random

        steps = 100
        for i in range(steps):
            if task.status == "cancelled":
                raise Exception("Task cancelled")

            task.progress = (i + 1) / steps * 100
            time.sleep(0.01)  # 模拟处理时间

            # 偶尔失败（用于测试）
            if random.random() < 0.01:  # 1% 失败率
                raise Exception("Simulated processing error")

    def _generate_preview(self, video_path: str, timestamp: float, duration: float) -> str:
        """生成预览视频"""
        # 这里应该使用MoviePy或其他视频处理库
        # 暂时返回模拟路径
        preview_path = os.path.join(
            tempfile.gettempdir(),
            f"preview_{timestamp}.mp4"
        )

        # 模拟处理时间
        time.sleep(0.5)

        return preview_path

    def _generate_thumbnail(self, video_path: str, timestamp: float) -> Optional[str]:
        """生成缩略图"""
        # 这里应该使用FFmpeg或其他工具
        # 暂时返回模拟路径
        thumbnail_path = os.path.join(
            tempfile.gettempdir(),
            f"thumb_{timestamp}.jpg"
        )

        try:
            # 模拟处理时间
            time.sleep(0.2)

            # 创建空文件作为模拟
            with open(thumbnail_path, 'w') as f:
                f.write("")

            return thumbnail_path
        except Exception:
            return None


# 全局性能优化器（需要在服务系统初始化后设置）
_performance_optimizer = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """获取全局性能优化器"""
    global _performance_optimizer
    if _performance_optimizer is None:
        raise RuntimeError("Performance optimizer not initialized")
    return _performance_optimizer


def set_performance_optimizer(optimizer: PerformanceOptimizer) -> None:
    """设置全局性能优化器"""
    global _performance_optimizer
    _performance_optimizer = optimizer