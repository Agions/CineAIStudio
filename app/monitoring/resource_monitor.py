#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 资源监控器
监控系统资源使用情况
"""

import os
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from collections import deque
from enum import Enum

import psutil
from ..core.logger import Logger
from ..core.event_bus import EventBus


class ResourceType(Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


@dataclass
class ResourceUsage:
    """资源使用情况"""
    resource_type: ResourceType
    usage_percent: float
    used_amount: Optional[float] = None
    total_amount: Optional[float] = None
    unit: str = ""
    timestamp: float = 0.0
    details: Dict[str, Any] = None


class ResourceMonitor:
    """资源监控器"""

    def __init__(self, logger: Logger, event_bus: EventBus,
                 monitoring_interval: float = 1.0):
        self.logger = logger
        self.event_bus = event_bus
        self.monitoring_interval = monitoring_interval

        # 监控状态
        self._is_monitoring = False
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 资源历史数据
        self._resource_history: Dict[ResourceType, deque] = {
            resource_type: deque(maxlen=3600)  # 保存1小时的数据
            for resource_type in ResourceType
        }

        # 警告阈值
        self._warning_thresholds: Dict[ResourceType, float] = {
            ResourceType.CPU: 70.0,
            ResourceType.MEMORY: 80.0,
            ResourceType.DISK: 85.0,
            ResourceType.GPU: 80.0
        }

        # 严重阈值
        self._critical_thresholds: Dict[ResourceType, float] = {
            ResourceType.CPU: 90.0,
            ResourceType.MEMORY: 95.0,
            ResourceType.DISK: 95.0,
            ResourceType.GPU: 95.0
        }

        # 回调函数
        self._alert_callbacks: List[Callable[[ResourceUsage, str], None]] = []

    def start_monitoring(self) -> None:
        """开始资源监控"""
        if self._is_monitoring:
            self.logger.warning("Resource monitoring already started")
            return

        self._is_monitoring = True
        self._stop_event.clear()

        # 启动监控线程
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()

        self.logger.info("Resource monitoring started")

    def stop_monitoring(self) -> None:
        """停止资源监控"""
        if not self._is_monitoring:
            return

        self._is_monitoring = False
        self._stop_event.set()

        # 等待监控线程结束
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)

        self.logger.info("Resource monitoring stopped")

    def get_current_usage(self, resource_type: ResourceType) -> Optional[ResourceUsage]:
        """获取当前资源使用情况"""
        try:
            if resource_type == ResourceType.CPU:
                return self._get_cpu_usage()
            elif resource_type == ResourceType.MEMORY:
                return self._get_memory_usage()
            elif resource_type == ResourceType.DISK:
                return self._get_disk_usage()
            elif resource_type == ResourceType.NETWORK:
                return self._get_network_usage()
            elif resource_type == ResourceType.GPU:
                return self._get_gpu_usage()
        except Exception as e:
            self.logger.error(f"Failed to get {resource_type.value} usage: {e}")
            return None

    def get_all_current_usage(self) -> Dict[ResourceType, ResourceUsage]:
        """获取所有资源的当前使用情况"""
        usage = {}
        for resource_type in ResourceType:
            usage[resource_type] = self.get_current_usage(resource_type)
        return usage

    def get_usage_history(self, resource_type: ResourceType,
                         duration_minutes: int = 60) -> List[ResourceUsage]:
        """获取资源使用历史"""
        cutoff_time = time.time() - (duration_minutes * 60)
        history = self._resource_history[resource_type]
        return [usage for usage in history if usage.timestamp > cutoff_time]

    def get_usage_average(self, resource_type: ResourceType,
                         duration_minutes: int = 60) -> Optional[float]:
        """获取平均资源使用率"""
        history = self.get_usage_history(resource_type, duration_minutes)
        if not history:
            return None

        total_usage = sum(usage.usage_percent for usage in history)
        return total_usage / len(history)

    def get_usage_peak(self, resource_type: ResourceType,
                      duration_minutes: int = 60) -> Optional[float]:
        """获取资源使用峰值"""
        history = self.get_usage_history(resource_type, duration_minutes)
        if not history:
            return None

        return max(usage.usage_percent for usage in history)

    def set_threshold(self, resource_type: ResourceType,
                     warning_threshold: float, critical_threshold: float) -> None:
        """设置资源阈值"""
        self._warning_thresholds[resource_type] = warning_threshold
        self._critical_thresholds[resource_type] = critical_threshold
        self.logger.info(f"Thresholds updated for {resource_type.value}")

    def add_alert_callback(self, callback: Callable[[ResourceUsage, str], None]) -> None:
        """添加告警回调函数"""
        self._alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable[[ResourceUsage, str], None]) -> None:
        """移除告警回调函数"""
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)

    def _monitoring_loop(self) -> None:
        """监控循环"""
        while not self._stop_event.wait(self.monitoring_interval):
            try:
                # 收集所有资源使用情况
                for resource_type in ResourceType:
                    usage = self.get_current_usage(resource_type)
                    if usage:
                        # 保存到历史
                        self._resource_history[resource_type].append(usage)

                        # 检查阈值
                        self._check_thresholds(usage)

            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")

    def _get_cpu_usage(self) -> ResourceUsage:
        """获取CPU使用情况"""
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # 获取每个核心的使用率
        cpu_per_core = psutil.cpu_percent(percpu=True)

        details = {
            "count": cpu_count,
            "frequency": {
                "current": cpu_freq.current if cpu_freq else None,
                "min": cpu_freq.min if cpu_freq else None,
                "max": cpu_freq.max if cpu_freq else None
            },
            "per_core": cpu_per_core,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }

        return ResourceUsage(
            resource_type=ResourceType.CPU,
            usage_percent=cpu_percent,
            used_amount=cpu_count,
            total_amount=cpu_count,
            unit="cores",
            timestamp=time.time(),
            details=details
        )

    def _get_memory_usage(self) -> ResourceUsage:
        """获取内存使用情况"""
        virtual_memory = psutil.virtual_memory()
        swap_memory = psutil.swap_memory()

        details = {
            "available": virtual_memory.available,
            "used": virtual_memory.used,
            "free": virtual_memory.free,
            "buffers": getattr(virtual_memory, 'buffers', 0),
            "cached": getattr(virtual_memory, 'cached', 0),
            "swap": {
                "total": swap_memory.total,
                "used": swap_memory.used,
                "free": swap_memory.free,
                "percent": swap_memory.percent
            }
        }

        return ResourceUsage(
            resource_type=ResourceType.MEMORY,
            usage_percent=virtual_memory.percent,
            used_amount=virtual_memory.used,
            total_amount=virtual_memory.total,
            unit="bytes",
            timestamp=time.time(),
            details=details
        )

    def _get_disk_usage(self) -> ResourceUsage:
        """获取磁盘使用情况"""
        # 获取根目录使用情况
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()

        details = {
            "used": disk_usage.used,
            "free": disk_usage.free,
            "io": {
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0,
                "read_count": disk_io.read_count if disk_io else 0,
                "write_count": disk_io.write_count if disk_io else 0
            }
        }

        # 获取所有磁盘分区信息
        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100
                })
            except PermissionError:
                continue

        details["partitions"] = partitions

        return ResourceUsage(
            resource_type=ResourceType.DISK,
            usage_percent=(disk_usage.used / disk_usage.total) * 100,
            used_amount=disk_usage.used,
            total_amount=disk_usage.total,
            unit="bytes",
            timestamp=time.time(),
            details=details
        )

    def _get_network_usage(self) -> ResourceUsage:
        """获取网络使用情况"""
        net_io = psutil.net_io_counters()
        net_connections = len(psutil.net_connections())

        # 获取网络接口信息
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()

        interfaces = {}
        for interface_name, addresses in net_if_addrs.items():
            interface_info = {
                "addresses": []
            }
            for addr in addresses:
                interface_info["addresses"].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })

            if interface_name in net_if_stats:
                stats = net_if_stats[interface_name]
                interface_info["stats"] = {
                    "isup": stats.isup,
                    "duplex": stats.duplex,
                    "speed": stats.speed,
                    "mtu": stats.mtu
                }

            interfaces[interface_name] = interface_info

        details = {
            "bytes_sent": net_io.bytes_sent if net_io else 0,
            "bytes_recv": net_io.bytes_recv if net_io else 0,
            "packets_sent": net_io.packets_sent if net_io else 0,
            "packets_recv": net_io.packets_recv if net_io else 0,
            "errin": net_io.errin if net_io else 0,
            "errout": net_io.errout if net_io else 0,
            "dropin": net_io.dropin if net_io else 0,
            "dropout": net_io.dropout if net_io else 0,
            "connections": net_connections,
            "interfaces": interfaces
        }

        return ResourceUsage(
            resource_type=ResourceType.NETWORK,
            usage_percent=0.0,  # 网络不使用百分比
            timestamp=time.time(),
            details=details
        )

    def _get_gpu_usage(self) -> Optional[ResourceUsage]:
        """获取GPU使用情况"""
        try:
            # 尝试使用nvidia-ml-py
            try:
                import pynvml
                pynvml.nvmlInit()

                device_count = pynvml.nvmlDeviceGetCount()
                total_memory = 0
                used_memory = 0
                total_utilization = 0
                gpu_count = 0

                gpu_details = []
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')

                    # GPU使用率
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

                    # 内存信息
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                    # 温度和功耗
                    temperature = pynvml.nvmlDeviceGetTemperature(
                        handle, pynvml.NVML_TEMPERATURE_GPU
                    )
                    power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0

                    total_memory += memory_info.total
                    used_memory += memory_info.used
                    total_utilization += utilization.gpu
                    gpu_count += 1

                    gpu_details.append({
                        "index": i,
                        "name": name,
                        "utilization_gpu": utilization.gpu,
                        "utilization_memory": utilization.memory,
                        "memory_total": memory_info.total,
                        "memory_used": memory_info.used,
                        "memory_free": memory_info.free,
                        "temperature": temperature,
                        "power_usage": power_usage
                    })

                pynvml.nvmlShutdown()

                if gpu_count > 0:
                    avg_utilization = total_utilization / gpu_count
                    usage_percent = avg_utilization
                else:
                    usage_percent = 0.0

                details = {
                    "gpus": gpu_details,
                    "gpu_count": gpu_count
                }

                return ResourceUsage(
                    resource_type=ResourceType.GPU,
                    usage_percent=usage_percent,
                    used_amount=used_memory,
                    total_amount=total_memory,
                    unit="bytes",
                    timestamp=time.time(),
                    details=details
                )

            except ImportError:
                self.logger.debug("nvidia-ml-py not available for GPU monitoring")

            # 尝试其他GPU监控方法
            # TODO: 实现AMD GPU和Intel GPU监控

        except Exception as e:
            self.logger.debug(f"GPU monitoring failed: {e}")

        return None

    def _check_thresholds(self, usage: ResourceUsage) -> None:
        """检查资源阈值"""
        resource_type = usage.resource_type

        # 检查严重阈值
        critical_threshold = self._critical_thresholds.get(resource_type)
        if critical_threshold and usage.usage_percent >= critical_threshold:
            self._trigger_alert(usage, "critical", critical_threshold)
            return

        # 检查警告阈值
        warning_threshold = self._warning_thresholds.get(resource_type)
        if warning_threshold and usage.usage_percent >= warning_threshold:
            self._trigger_alert(usage, "warning", warning_threshold)

    def _trigger_alert(self, usage: ResourceUsage, level: str,
                      threshold: float) -> None:
        """触发资源告警"""
        # 调用回调函数
        for callback in self._alert_callbacks:
            try:
                callback(usage, level)
            except Exception as e:
                self.logger.error(f"Resource alert callback error: {e}")

        # 发布告警事件
        self.event_bus.publish("resource.alert", {
            "resource_type": usage.resource_type.value,
            "level": level,
            "usage_percent": usage.usage_percent,
            "threshold": threshold,
            "timestamp": usage.timestamp
        })

        # 记录日志
        message = (f"{level.upper()} {usage.resource_type.value} usage: "
                  f"{usage.usage_percent:.1f}% (threshold: {threshold:.1f}%)")
        if level == "critical":
            self.logger.error(message)
        else:
            self.logger.warning(message)

    def cleanup(self) -> None:
        """清理资源"""
        self.stop_monitoring()