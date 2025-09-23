#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出性能优化器
提供导出性能优化和资源管理功能
"""

import os
import psutil
import platform
import subprocess
import threading
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..core.logger import Logger


class OptimizationLevel(Enum):
    """优化级别"""
    LOW = "low"          # 低优化，优先质量
    MEDIUM = "medium"    # 中等优化
    HIGH = "high"        # 高优化，优先速度
    AUTO = "auto"        # 自动优化


class ResourcePriority(Enum):
    """资源优先级"""
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class SystemResources:
    """系统资源信息"""
    cpu_count: int
    cpu_usage: float
    memory_total: int
    memory_usage: float
    disk_usage: float
    gpu_info: Dict[str, Any] = field(default_factory=dict)
    network_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportOptimizationConfig:
    """导出优化配置"""
    optimization_level: OptimizationLevel
    max_cpu_usage: float = 80.0
    max_memory_usage: float = 70.0
    max_concurrent_tasks: int = 2
    use_gpu_acceleration: bool = True
    use_multi_threading: bool = True
    enable_io_optimization: bool = True
    enable_memory_optimization: bool = True
    cache_enabled: bool = True
    temp_dir: str = "/tmp"
    custom_params: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.monitoring = False
        self.monitor_thread = None
        self.resource_history = []
        self.max_history_size = 1000

    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                resources = self.get_system_resources()
                self.resource_history.append(resources)

                # 限制历史记录大小
                if len(self.resource_history) > self.max_history_size:
                    self.resource_history.pop(0)

                time.sleep(1.0)
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")
                time.sleep(5.0)

    def get_system_resources(self) -> SystemResources:
        """获取系统资源信息"""
        try:
            # CPU信息
            cpu_count = psutil.cpu_count(logical=True)
            cpu_usage = psutil.cpu_percent(interval=0.1)

            # 内存信息
            memory = psutil.virtual_memory()
            memory_total = memory.total
            memory_usage = memory.percent

            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent

            # GPU信息
            gpu_info = self._get_gpu_info()

            # 网络信息
            network_info = self._get_network_info()

            return SystemResources(
                cpu_count=cpu_count,
                cpu_usage=cpu_usage,
                memory_total=memory_total,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                gpu_info=gpu_info,
                network_info=network_info
            )

        except Exception as e:
            self.logger.error(f"Failed to get system resources: {e}")
            return SystemResources(0, 0, 0, 0, 0)

    def _get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU信息"""
        gpu_info = {}

        try:
            # 尝试获取nvidia GPU信息
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
                                  capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    parts = line.split(', ')
                    if len(parts) >= 4:
                        gpu_info[f"gpu_{i}"] = {
                            "name": parts[0],
                            "memory_total": int(parts[1]),
                            "memory_used": int(parts[2]),
                            "utilization": int(parts[3])
                        }
        except:
            pass

        return gpu_info

    def _get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        network_info = {}

        try:
            net_io = psutil.net_io_counters()
            network_info = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except:
            pass

        return network_info

    def get_average_resources(self, window_seconds: int = 60) -> SystemResources:
        """获取平均资源使用情况"""
        if not self.resource_history:
            return self.get_system_resources()

        current_time = time.time()
        cutoff_time = current_time - window_seconds

        recent_resources = [
            r for r in self.resource_history
            if hasattr(r, 'timestamp') and r.timestamp > cutoff_time
        ]

        if not recent_resources:
            return self.get_system_resources()

        # 计算平均值
        avg_cpu = sum(r.cpu_usage for r in recent_resources) / len(recent_resources)
        avg_memory = sum(r.memory_usage for r in recent_resources) / len(recent_resources)
        avg_disk = sum(r.disk_usage for r in recent_resources) / len(recent_resources)

        return SystemResources(
            cpu_count=recent_resources[0].cpu_count,
            cpu_usage=avg_cpu,
            memory_total=recent_resources[0].memory_total,
            memory_usage=avg_memory,
            disk_usage=avg_disk,
            gpu_info=recent_resources[0].gpu_info,
            network_info=recent_resources[0].network_info
        )

    def get_resource_trends(self) -> Dict[str, List[float]]:
        """获取资源使用趋势"""
        if not self.resource_history:
            return {}

        trends = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": []
        }

        for resources in self.resource_history[-100:]:  # 最近100个数据点
            trends["cpu_usage"].append(resources.cpu_usage)
            trends["memory_usage"].append(resources.memory_usage)
            trends["disk_usage"].append(resources.disk_usage)

        return trends


class ExportOptimizer:
    """导出优化器"""

    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.monitor = PerformanceMonitor()
        self.config = ExportOptimizationConfig(OptimizationLevel.AUTO)
        self.optimization_stats = {
            "total_exports": 0,
            "optimized_exports": 0,
            "average_time_saved": 0.0,
            "resource_utilization": {}
        }

    def initialize(self):
        """初始化优化器"""
        self.monitor.start_monitoring()
        self._detect_system_capabilities()
        self._auto_optimize_config()
        self.logger.info("Export optimizer initialized")

    def shutdown(self):
        """关闭优化器"""
        self.monitor.stop_monitoring()
        self.logger.info("Export optimizer shutdown")

    def _detect_system_capabilities(self):
        """检测系统能力"""
        # 检测CPU核心数
        cpu_count = psutil.cpu_count(logical=True)
        if cpu_count >= 8:
            self.config.max_concurrent_tasks = min(4, cpu_count // 2)
        elif cpu_count >= 4:
            self.config.max_concurrent_tasks = 2
        else:
            self.config.max_concurrent_tasks = 1

        # 检测内存大小
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb >= 16:
            self.config.max_memory_usage = 70.0
        elif memory_gb >= 8:
            self.config.max_memory_usage = 60.0
        else:
            self.config.max_memory_usage = 50.0

        # 检测GPU加速支持
        self.config.use_gpu_acceleration = self._check_gpu_support()

        self.logger.info(f"System capabilities detected: CPU={cpu_count}, Memory={memory_gb:.1f}GB, GPU={self.config.use_gpu_acceleration}")

    def _check_gpu_support(self) -> bool:
        """检查GPU加速支持"""
        try:
            # 检查nvidia GPU
            result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=5)
            if result.returncode == 0:
                return True

            # 检查AMD GPU
            result = subprocess.run(['rocm-smi'], capture_output=True, timeout=5)
            if result.returncode == 0:
                return True

            # 检查Intel GPU
            result = subprocess.run(['intel_gpu_top'], capture_output=True, timeout=5)
            if result.returncode == 0:
                return True

        except:
            pass

        return False

    def _auto_optimize_config(self):
        """自动优化配置"""
        current_resources = self.monitor.get_system_resources()

        # 根据当前资源使用情况调整配置
        if current_resources.cpu_usage > 80:
            self.config.max_concurrent_tasks = max(1, self.config.max_concurrent_tasks - 1)
        elif current_resources.cpu_usage < 50:
            self.config.max_concurrent_tasks = min(4, self.config.max_concurrent_tasks + 1)

        if current_resources.memory_usage > 80:
            self.config.max_memory_usage = max(50, self.config.max_memory_usage - 10)
        elif current_resources.memory_usage < 60:
            self.config.max_memory_usage = min(80, self.config.max_memory_usage + 5)

        self.logger.info(f"Auto-optimized config: concurrent_tasks={self.config.max_concurrent_tasks}, memory_usage={self.config.max_memory_usage}%")

    def optimize_export_command(self,
                               base_command: List[str],
                               preset_config: Dict[str, Any]) -> List[str]:
        """优化导出命令"""
        optimized_command = base_command.copy()

        # CPU优化
        if self.config.use_multi_threading:
            cpu_count = self.config.max_concurrent_tasks
            optimized_command.extend(["-threads", str(cpu_count)])

        # GPU优化
        if self.config.use_gpu_acceleration:
            gpu_params = self._get_gpu_acceleration_params(preset_config)
            optimized_command.extend(gpu_params)

        # 内存优化
        if self.config.enable_memory_optimization:
            memory_params = self._get_memory_optimization_params()
            optimized_command.extend(memory_params)

        # I/O优化
        if self.config.enable_io_optimization:
            io_params = self._get_io_optimization_params()
            optimized_command.extend(io_params)

        # 缓存优化
        if self.config.cache_enabled:
            cache_params = self._get_cache_optimization_params()
            optimized_command.extend(cache_params)

        return optimized_command

    def _get_gpu_acceleration_params(self, preset_config: Dict[str, Any]) -> List[str]:
        """获取GPU加速参数"""
        params = []

        if self.config.use_gpu_acceleration:
            # 检查可用的GPU编码器
            if self._check_nvenc_support():
                params.extend(["-c:v", "h264_nvenc"])
                params.extend(["-preset", "p7"])  # 最高质量
                params.extend(["-tune", "hq"])
            elif self._check_amf_support():
                params.extend(["-c:v", "h264_amf"])
                params.extend(["-quality", "quality"])
            elif self._check_qsv_support():
                params.extend(["-c:v", "h264_qsv"])
                params.extend(["-preset", "verygood"])

        return params

    def _check_nvenc_support(self) -> bool:
        """检查NVENC支持"""
        try:
            result = subprocess.run(['ffmpeg', -encoders'], capture_output=True, text=True)
            return 'h264_nvenc' in result.stdout
        except:
            return False

    def _check_amf_support(self) -> bool:
        """检查AMF支持"""
        try:
            result = subprocess.run(['ffmpeg', -encoders], capture_output=True, text=True)
            return 'h264_amf' in result.stdout
        except:
            return False

    def _check_qsv_support(self) -> bool:
        """检查QSV支持"""
        try:
            result = subprocess.run(['ffmpeg', -encoders], capture_output=True, text=True)
            return 'h264_qsv' in result.stdout
        except:
            return False

    def _get_memory_optimization_params(self) -> List[str]:
        """获取内存优化参数"""
        params = []

        # 设置内存限制
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 8:
            params.extend(["-x264opts", "no-mbtree"])
            params.extend(["-movflags", "+faststart"])

        return params

    def _get_io_optimization_params(self) -> List[str]:
        """获取I/O优化参数"""
        params = []

        # 使用更快的I/O模式
        params.extend(["-flush_packets", "1"])
        params.extend(["-movflags", "+faststart"])

        # 使用临时文件目录
        if self.config.temp_dir:
            params.extend(["-f", "segment"])
            params.extend(["-segment_time", "600"])

        return params

    def _get_cache_optimization_params(self) -> List[str]:
        """获取缓存优化参数"""
        params = []

        # 启用缓存
        params.extend(["-cache", "1"])
        params.extend(["-cache_size", "1000000"])

        return params

    def get_optimal_concurrent_tasks(self) -> int:
        """获取最优并发任务数"""
        current_resources = self.monitor.get_system_resources()

        # 根据CPU使用率调整
        if current_resources.cpu_usage > 90:
            return 1
        elif current_resources.cpu_usage > 70:
            return max(1, self.config.max_concurrent_tasks - 1)
        elif current_resources.cpu_usage < 30:
            return min(4, self.config.max_concurrent_tasks + 1)

        return self.config.max_concurrent_tasks

    def get_resource_recommendations(self) -> Dict[str, Any]:
        """获取资源优化建议"""
        current_resources = self.monitor.get_system_resources()
        recommendations = []

        # CPU建议
        if current_resources.cpu_usage > 80:
            recommendations.append({
                "type": "cpu",
                "priority": "high",
                "message": "CPU使用率过高，建议减少并发任务数",
                "action": "reduce_concurrent_tasks"
            })

        # 内存建议
        if current_resources.memory_usage > 80:
            recommendations.append({
                "type": "memory",
                "priority": "high",
                "message": "内存使用率过高，建议启用内存优化",
                "action": "enable_memory_optimization"
            })

        # 磁盘建议
        if current_resources.disk_usage > 90:
            recommendations.append({
                "type": "disk",
                "priority": "medium",
                "message": "磁盘空间不足，建议清理临时文件",
                "action": "cleanup_temp_files"
            })

        # GPU建议
        if self.config.use_gpu_acceleration:
            gpu_utilization = 0
            for gpu_info in current_resources.gpu_info.values():
                gpu_utilization = max(gpu_utilization, gpu_info.get("utilization", 0))

            if gpu_utilization < 20:
                recommendations.append({
                    "type": "gpu",
                    "priority": "low",
                    "message": "GPU利用率较低，可以考虑使用GPU加速",
                    "action": "enable_gpu_acceleration"
                })

        return {
            "current_resources": {
                "cpu_usage": current_resources.cpu_usage,
                "memory_usage": current_resources.memory_usage,
                "disk_usage": current_resources.disk_usage
            },
            "recommendations": recommendations,
            "config": {
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "max_memory_usage": self.config.max_memory_usage,
                "use_gpu_acceleration": self.config.use_gpu_acceleration
            }
        }

    def update_config(self, config: ExportOptimizationConfig):
        """更新优化配置"""
        self.config = config
        self._auto_optimize_config()
        self.logger.info("Export optimization config updated")

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "optimization_stats": self.optimization_stats,
            "current_config": {
                "optimization_level": self.config.optimization_level.value,
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "max_memory_usage": self.config.max_memory_usage,
                "use_gpu_acceleration": self.config.use_gpu_acceleration,
                "use_multi_threading": self.config.use_multi_threading
            },
            "resource_trends": self.monitor.get_resource_trends(),
            "system_resources": self.monitor.get_average_resources().__dict__
        }

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.config.temp_dir):
                import shutil
                shutil.rmtree(self.config.temp_dir)
                os.makedirs(self.config.temp_dir, exist_ok=True)
                self.logger.info("Temporary files cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp files: {e}")


# 全局性能优化器实例
performance_optimizer = ExportOptimizer()