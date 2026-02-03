#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 指标收集器
收集应用程序的各种性能指标
"""

import os
import time
import threading
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from enum import Enum

from ..core.logger import Logger
from ..core.event_bus import EventBus


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"          # 计数器
    GAUGE = "gauge"             # 瞬时值
    HISTOGRAM = "histogram"      # 直方图
    TIMER = "timer"             # 计时器
    METER = "meter"             # 速率仪


@dataclass
class Metric:
    """指标数据"""
    name: str
    metric_type: MetricType
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class HistogramBucket:
    """直方图桶"""
    upper_bound: float
    count: int


@dataclass
class HistogramMetric:
    """直方图指标"""
    name: str
    count: int
    sum: float
    buckets: List[HistogramBucket]
    timestamp: float


class MetricsCollector:
    """指标收集器"""

    def __init__(self, logger: Logger, event_bus: EventBus,
                 collection_interval: float = 1.0):
        self.logger = logger
        self.event_bus = event_bus
        self.collection_interval = collection_interval

        # 指标存储
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._meters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # 自定义指标
        self._custom_metrics: List[Metric] = []

        # 系统监控
        self._system_metrics: Dict[str, Any] = {}

        # 收集线程
        self._collection_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 回调函数
        self._metric_callbacks: List[Callable[[Metric], None]] = []

        # 启动收集
        self._start_collection()

    def increment_counter(self, name: str, value: float = 1.0,
                         labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数器"""
        self._counters[name] += value

        metric = Metric(
            name=name,
            metric_type=MetricType.COUNTER,
            value=self._counters[name],
            timestamp=time.time(),
            labels=labels or {}
        )
        self._notify_callbacks(metric)

    def set_gauge(self, name: str, value: float,
                  labels: Optional[Dict[str, str]] = None) -> None:
        """设置瞬时值"""
        self._gauges[name] = value

        metric = Metric(
            name=name,
            metric_type=MetricType.GAUGE,
            value=value,
            timestamp=time.time(),
            labels=labels or {}
        )
        self._notify_callbacks(metric)

    def record_histogram(self, name: str, value: float,
                        labels: Optional[Dict[str, str]] = None) -> None:
        """记录直方图数据"""
        self._histograms[name].append(value)

        metric = Metric(
            name=name,
            metric_type=MetricType.HISTOGRAM,
            value=value,
            timestamp=time.time(),
            labels=labels or {}
        )
        self._notify_callbacks(metric)

    def record_timer(self, name: str, duration: float,
                    labels: Optional[Dict[str, str]] = None) -> None:
        """记录计时"""
        self._timers[name].append(duration)

        metric = Metric(
            name=name,
            metric_type=MetricType.TIMER,
            value=duration,
            timestamp=time.time(),
            labels=labels or {}
        )
        self._notify_callbacks(metric)

    def record_meter(self, name: str, value: float = 1.0,
                    labels: Optional[Dict[str, str]] = None) -> None:
        """记录速率"""
        current_time = time.time()
        self._meters[name].append((current_time, value))

        metric = Metric(
            name=name,
            metric_type=MetricType.METER,
            value=value,
            timestamp=current_time,
            labels=labels or {}
        )
        self._notify_callbacks(metric)

    def add_custom_metric(self, metric: Metric) -> None:
        """添加自定义指标"""
        self._custom_metrics.append(metric)
        self._notify_callbacks(metric)

    def get_counter(self, name: str) -> float:
        """获取计数器值"""
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> Optional[float]:
        """获取瞬时值"""
        return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Optional[Dict[str, float]]:
        """获取直方图统计"""
        values = self._histograms.get(name, [])
        if not values:
            return None

        values.sort()
        count = len(values)
        total = sum(values)

        return {
            "count": count,
            "sum": total,
            "min": values[0],
            "max": values[-1],
            "mean": total / count,
            "median": values[count // 2],
            "p95": values[int(count * 0.95)] if count > 0 else 0,
            "p99": values[int(count * 0.99)] if count > 0 else 0
        }

    def get_timer_stats(self, name: str) -> Optional[Dict[str, float]]:
        """获取计时统计"""
        return self.get_histogram_stats(name)  # Timer和Histogram统计相同

    def get_meter_rate(self, name: str, window_seconds: float = 60.0) -> float:
        """获取速率（每秒）"""
        entries = self._meters.get(name, [])
        if not entries:
            return 0.0

        current_time = time.time()
        cutoff_time = current_time - window_seconds

        # 计算窗口内的总和
        total = sum(value for timestamp, value in entries if timestamp > cutoff_time)

        return total / window_seconds

    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        metrics = {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {},
            "timers": {},
            "meters": {},
            "custom": [],
            "system": self._system_metrics
        }

        # 添加直方图统计
        for name in self._histograms:
            metrics["histograms"][name] = self.get_histogram_stats(name)

        # 添加计时统计
        for name in self._timers:
            metrics["timers"][name] = self.get_timer_stats(name)

        # 添加速率
        for name in self._meters:
            metrics["meters"][name] = {
                "rate_1m": self.get_meter_rate(name, 60.0),
                "rate_5m": self.get_meter_rate(name, 300.0)
            }

        # 添加自定义指标
        metrics["custom"] = [
            {
                "name": m.name,
                "type": m.metric_type.value,
                "value": m.value,
                "timestamp": m.timestamp,
                "labels": m.labels,
                "unit": m.unit
            }
            for m in self._custom_metrics
        ]

        return metrics

    def reset_metric(self, name: str) -> None:
        """重置指标"""
        self._counters.pop(name, None)
        self._gauges.pop(name, None)
        self._histograms.pop(name, None)
        self._timers.pop(name, None)
        self._meters.pop(name, None)

    def reset_all_metrics(self) -> None:
        """重置所有指标"""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timers.clear()
        self._meters.clear()
        self._custom_metrics.clear()

    def add_callback(self, callback: Callable[[Metric], None]) -> None:
        """添加指标回调函数"""
        self._metric_callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Metric], None]) -> None:
        """移除指标回调函数"""
        if callback in self._metric_callbacks:
            self._metric_callbacks.remove(callback)

    def _start_collection(self) -> None:
        """启动指标收集线程"""
        self._collection_thread = threading.Thread(
            target=self._collection_loop,
            daemon=True
        )
        self._collection_thread.start()

    def _stop_collection(self) -> None:
        """停止指标收集线程"""
        self._stop_event.set()
        if self._collection_thread:
            self._collection_thread.join(timeout=5.0)

    def _collection_loop(self) -> None:
        """指标收集循环"""
        while not self._stop_event.wait(self.collection_interval):
            try:
                self._collect_system_metrics()
            except Exception as e:
                self.logger.error(f"System metrics collection error: {e}")

    def _collect_system_metrics(self) -> None:
        """收集系统指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # 内存指标
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # 磁盘指标
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()

            # 网络指标
            network_io = psutil.net_io_counters()

            # 进程指标
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()

            # GPU指标（如果有）
            gpu_metrics = self._collect_gpu_metrics()

            self._system_metrics = {
                "timestamp": time.time(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": {
                        "current": cpu_freq.current if cpu_freq else None,
                        "min": cpu_freq.min if cpu_freq else None,
                        "max": cpu_freq.max if cpu_freq else None
                    }
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent
                },
                "disk": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": disk_usage.percent,
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                    "read_count": disk_io.read_count if disk_io else 0,
                    "write_count": disk_io.write_count if disk_io else 0
                },
                "network": {
                    "bytes_sent": network_io.bytes_sent if network_io else 0,
                    "bytes_recv": network_io.bytes_recv if network_io else 0,
                    "packets_sent": network_io.packets_sent if network_io else 0,
                    "packets_recv": network_io.packets_recv if network_io else 0
                },
                "process": {
                    "pid": process.pid,
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process_cpu,
                    "num_threads": process.num_threads(),
                    "num_fds": process.num_fds()
                },
                "gpu": gpu_metrics
            }

        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")

    def _collect_gpu_metrics(self) -> Dict[str, Any]:
        """收集GPU指标"""
        try:
            # 尝试使用nvidia-ml-py收集NVIDIA GPU指标
            try:
                import pynvml
                pynvml.nvmlInit()

                gpu_metrics = {}
                device_count = pynvml.nvmlDeviceGetCount()

                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')

                    # GPU使用率
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    temperature = pynvml.nvmlDeviceGetTemperature(
                        handle, pynvml.NVML_TEMPERATURE_GPU
                    )
                    power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # W

                    gpu_metrics[f"gpu_{i}"] = {
                        "name": name,
                        "utilization_gpu": utilization.gpu,
                        "utilization_memory": utilization.memory,
                        "memory_total": memory_info.total,
                        "memory_used": memory_info.used,
                        "memory_free": memory_info.free,
                        "temperature": temperature,
                        "power_usage": power_usage
                    }

                pynvml.nvmlShutdown()
                return gpu_metrics

            except ImportError:
                # nvidia-ml-py不可用，尝试其他方法
                pass

            # 尝试使用AMD GPU指标
            # TODO: 实现AMD GPU指标收集

            # 尝试使用Intel GPU指标
            # TODO: 实现Intel GPU指标收集

        except Exception as e:
            self.logger.debug(f"GPU metrics collection failed: {e}")

        return {}

    def _notify_callbacks(self, metric: Metric) -> None:
        """通知所有回调函数"""
        for callback in self._metric_callbacks:
            try:
                callback(metric)
            except Exception as e:
                self.logger.error(f"Metric callback error: {e}")

    def cleanup(self) -> None:
        """清理资源"""
        self._stop_collection()


# 上下文管理器，用于计时操作

class TimerContext:
    """计时器上下文管理器"""

    def __init__(self, collector: MetricsCollector, name: str,
                 labels: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.collector.record_timer(self.name, duration, self.labels)


def timer(collector: MetricsCollector, name: str,
         labels: Optional[Dict[str, str]] = None) -> TimerContext:
    """创建计时器上下文管理器"""
    return TimerContext(collector, name, labels)


# 全局指标收集器实例
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        raise RuntimeError("Metrics collector not initialized")
    return _metrics_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """设置全局指标收集器"""
    global _metrics_collector
    _metrics_collector = collector