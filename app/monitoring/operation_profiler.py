#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 操作性能分析器
分析和监控各种操作的执行性能
"""

import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum

from ..core.logger import Logger
from ..core.event_bus import EventBus


class OperationStatus(Enum):
    """操作状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationRecord:
    """操作记录"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: OperationStatus = OperationStatus.RUNNING
    success: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationStats:
    """操作统计"""
    name: str
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0
    p50_duration: float = 0.0
    p95_duration: float = 0.0
    p99_duration: float = 0.0
    current_operations: int = 0
    last_operation_time: float = 0.0


class OperationProfiler:
    """操作性能分析器"""

    def __init__(self, logger: Logger, event_bus: EventBus,
                 max_history: int = 10000):
        self.logger = logger
        self.event_bus = event_bus
        self.max_history = max_history

        # 当前运行的操作
        self._running_operations: Dict[str, OperationRecord] = {}

        # 操作历史
        self._operation_history: deque = deque(maxlen=max_history)

        # 操作统计
        self._operation_stats: Dict[str, OperationStats] = defaultdict(
            lambda: OperationStats(name="")
        )

        # 线程安全
        self._lock = threading.RLock()

    def start_operation(self, name: str, operation_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """开始操作"""
        with self._lock:
            # 生成唯一ID
            if operation_id is None:
                operation_id = f"{name}_{int(time.time() * 1000000)}_{id(name)}"

            # 创建操作记录
            record = OperationRecord(
                name=name,
                start_time=time.time(),
                metadata=metadata or {}
            )

            # 添加到运行列表
            self._running_operations[operation_id] = record

            # 更新统计
            stats = self._operation_stats[name]
            stats.name = name
            stats.current_operations += 1

            # 发布事件
            self.event_bus.publish("operation.started", {
                "operation_id": operation_id,
                "name": name,
                "metadata": metadata
            })

            self.logger.debug(f"Operation started: {name} ({operation_id})")

            return operation_id

    def complete_operation(self, operation_id: str, success: bool = True,
                          error: Optional[str] = None) -> Optional[float]:
        """完成操作"""
        with self._lock:
            record = self._running_operations.pop(operation_id, None)
            if record is None:
                self.logger.warning(f"Operation not found: {operation_id}")
                return None

            # 更新记录
            end_time = time.time()
            duration = end_time - record.start_time

            record.end_time = end_time
            record.duration = duration
            record.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
            record.success = success
            record.error = error

            # 添加到历史
            self._operation_history.append(record)

            # 更新统计
            self._update_stats(record)

            # 发布事件
            event_data = {
                "operation_id": operation_id,
                "name": record.name,
                "duration": duration,
                "success": success,
                "metadata": record.metadata
            }

            if error:
                event_data["error"] = error

            event_name = "operation.completed" if success else "operation.failed"
            self.event_bus.publish(event_name, event_data)

            # 记录日志
            if success:
                self.logger.debug(f"Operation completed: {record.name} in {duration:.3f}s")
            else:
                self.logger.error(f"Operation failed: {record.name} in {duration:.3f}s - {error}")

            return duration

    def cancel_operation(self, operation_id: str) -> bool:
        """取消操作"""
        with self._lock:
            record = self._running_operations.get(operation_id)
            if record is None:
                return False

            # 更新记录
            end_time = time.time()
            duration = end_time - record.start_time

            record.end_time = end_time
            record.duration = duration
            record.status = OperationStatus.CANCELLED

            # 从运行列表移除
            del self._running_operations[operation_id]

            # 添加到历史
            self._operation_history.append(record)

            # 更新统计
            stats = self._operation_stats[record.name]
            stats.current_operations -= 1

            # 发布事件
            self.event_bus.publish("operation.cancelled", {
                "operation_id": operation_id,
                "name": record.name,
                "duration": duration
            })

            self.logger.debug(f"Operation cancelled: {record.name}")

            return True

    def get_running_operations(self) -> List[Dict[str, Any]]:
        """获取正在运行的操作"""
        with self._lock:
            return [
                {
                    "operation_id": op_id,
                    "name": record.name,
                    "start_time": record.start_time,
                    "duration": time.time() - record.start_time,
                    "metadata": record.metadata
                }
                for op_id, record in self._running_operations.items()
            ]

    def get_operation_history(self, operation_name: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """获取操作历史"""
        with self._lock:
            history = list(self._operation_history)

            if operation_name:
                history = [r for r in history if r.name == operation_name]

            # 按时间倒序排列
            history.sort(key=lambda x: x.start_time, reverse=True)

            # 限制数量
            history = history[:limit]

            return [
                {
                    "name": record.name,
                    "start_time": record.start_time,
                    "end_time": record.end_time,
                    "duration": record.duration,
                    "status": record.status.value,
                    "success": record.success,
                    "error": record.error,
                    "metadata": record.metadata
                }
                for record in history
            ]

    def get_operation_stats(self, operation_name: Optional[str] = None) -> List[OperationStats]:
        """获取操作统计"""
        with self._lock:
            if operation_name:
                stats = self._operation_stats.get(operation_name)
                return [stats] if stats else []
            else:
                return list(self._operation_stats.values())

    def get_slow_operations(self, threshold_seconds: float = 1.0,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """获取慢操作"""
        with self._lock:
            # 获取所有已完成的操作
            completed_operations = [
                record for record in self._operation_history
                if record.duration is not None and record.status == OperationStatus.COMPLETED
            ]

            # 按持续时间排序
            completed_operations.sort(key=lambda x: x.duration, reverse=True)

            # 过滤慢操作
            slow_operations = [
                record for record in completed_operations
                if record.duration >= threshold_seconds
            ][:limit]

            return [
                {
                    "name": record.name,
                    "duration": record.duration,
                    "start_time": record.start_time,
                    "metadata": record.metadata
                }
                for record in slow_operations
            ]

    def get_operation_summary(self, time_range_seconds: float = 300.0) -> Dict[str, Any]:
        """获取操作汇总"""
        with self._lock:
            cutoff_time = time.time() - time_range_seconds

            # 获取时间范围内的操作
            recent_operations = [
                record for record in self._operation_history
                if record.start_time >= cutoff_time
            ]

            # 统计各状态的数量
            status_counts = defaultdict(int)
            operation_counts = defaultdict(int)
            total_duration = 0.0
            failed_operations = 0

            for record in recent_operations:
                status_counts[record.status.value] += 1
                operation_counts[record.name] += 1

                if record.duration:
                    total_duration += record.duration
                    if not record.success:
                        failed_operations += 1

            # 计算最常用的操作
            most_common = sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "time_range": time_range_seconds,
                "total_operations": len(recent_operations),
                "status_counts": dict(status_counts),
                "failure_rate": (failed_operations / len(recent_operations) * 100) if recent_operations else 0,
                "average_duration": total_duration / len(recent_operations) if recent_operations else 0,
                "most_common_operations": most_common,
                "current_running": len(self._running_operations)
            }

    def reset_stats(self, operation_name: Optional[str] = None) -> None:
        """重置统计"""
        with self._lock:
            if operation_name:
                self._operation_stats[operation_name] = OperationStats(name=operation_name)
            else:
                self._operation_stats.clear()

    def export_stats(self, file_path: str, format: str = "json") -> bool:
        """导出统计数据"""
        try:
            with self._lock:
                stats_data = {
                    "timestamp": time.time(),
                    "operation_stats": {},
                    "running_operations": len(self._running_operations),
                    "total_history": len(self._operation_history)
                }

                for name, stats in self._operation_stats.items():
                    stats_data["operation_stats"][name] = {
                        "total_count": stats.total_count,
                        "success_count": stats.success_count,
                        "failure_count": stats.failure_count,
                        "total_duration": stats.total_duration,
                        "min_duration": stats.min_duration,
                        "max_duration": stats.max_duration,
                        "avg_duration": stats.avg_duration,
                        "p50_duration": stats.p50_duration,
                        "p95_duration": stats.p95_duration,
                        "p99_duration": stats.p99_duration,
                        "current_operations": stats.current_operations,
                        "last_operation_time": stats.last_operation_time
                    }

            if format.lower() == "json":
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")

            self.logger.info(f"Operation stats exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export operation stats: {e}")
            return False

    def _update_stats(self, record: OperationRecord) -> None:
        """更新操作统计"""
        if record.duration is None:
            return

        stats = self._operation_stats[record.name]
        stats.total_count += 1

        if record.success:
            stats.success_count += 1
        else:
            stats.failure_count += 1

        stats.total_duration += record.duration
        stats.min_duration = min(stats.min_duration, record.duration)
        stats.max_duration = max(stats.max_duration, record.duration)
        stats.avg_duration = stats.total_duration / stats.total_count
        stats.current_operations -= 1
        stats.last_operation_time = record.end_time or time.time()

        # 计算百分位数
        self._calculate_percentiles(record.name)

    def _calculate_percentiles(self, operation_name: str) -> None:
        """计算百分位数"""
        # 获取该操作的所有持续时间
        durations = [
            record.duration
            for record in self._operation_history
            if record.name == operation_name and record.duration is not None
        ]

        if not durations:
            return

        durations.sort()
        count = len(durations)

        stats = self._operation_stats[operation_name]
        stats.p50_duration = durations[int(count * 0.5)]
        stats.p95_duration = durations[int(count * 0.95)]
        stats.p99_duration = durations[int(count * 0.99)]

    def cleanup(self) -> None:
        """清理资源"""
        with self._lock:
            # 取消所有运行中的操作
            running_ids = list(self._running_operations.keys())
            for operation_id in running_ids:
                self.cancel_operation(operation_id)


# 上下文管理器，用于自动跟踪操作
class OperationContext:
    """操作上下文管理器"""

    def __init__(self, profiler: OperationProfiler, name: str,
                 operation_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.profiler = profiler
        self.name = name
        self.operation_id = operation_id
        self.metadata = metadata
        self._actual_operation_id: Optional[str] = None

    def __enter__(self):
        self._actual_operation_id = self.profiler.start_operation(
            self.name, self.operation_id, self.metadata
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._actual_operation_id:
            success = exc_type is None
            error = str(exc_val) if exc_val else None
            self.profiler.complete_operation(self._actual_operation_id, success, error)


def profile_operation(profiler: OperationProfiler, name: str,
                     operation_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> OperationContext:
    """创建操作分析上下文管理器"""
    return OperationContext(profiler, name, operation_id, metadata)


# 装饰器版本
def profile(name: Optional[str] = None):
    """操作分析装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 获取全局操作分析器
            from ..monitoring.performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
            profiler = monitor.operation_profiler

            operation_name = name or f"{func.__module__}.{func.__name__}"

            with profile_operation(profiler, operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator