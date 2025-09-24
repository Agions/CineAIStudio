#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 硬件加速模块
提供GPU加速、内存优化和性能监控功能
"""

import os
import sys
import threading
import time
import subprocess
import platform
import psutil
import logging
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

from .logger import get_logger
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import HWAccelerationType, get_ffmpeg_utils


class GPUVendor(Enum):
    """GPU厂商枚举"""
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"


class GPUArchitecture(Enum):
    """GPU架构枚举"""
    CUDA = "cuda"
    OPENCL = "opencl"
    METAL = "metal"
    VULKAN = "vulkan"
    DIRECTX = "directx"
    OPENGL = "opengl"


@dataclass
class GPUInfo:
    """GPU信息数据类"""
    vendor: GPUVendor
    name: str
    memory_total: int  # MB
    memory_used: int  # MB
    memory_free: int  # MB
    compute_capability: str
    driver_version: str
    temperature: Optional[float] = None
    utilization: Optional[float] = None
    power_usage: Optional[float] = None


@dataclass
class MemoryInfo:
    """内存信息数据类"""
    total: int  # bytes
    available: int  # bytes
    used: int  # bytes
    percentage: float
    swap_total: int
    swap_used: int
    swap_percentage: float


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    cpu_usage: float
    memory_usage: float
    gpu_usage: float
    gpu_memory_usage: float
    temperature: float
    power_usage: float
    fps: float
    processing_time: float


class HardwareAcceleration:
    """硬件加速管理器"""

    def __init__(self, logger=None):
        """初始化硬件加速管理器"""
        self.logger = logger or get_logger("HardwareAcceleration")
        self.error_handler = get_global_error_handler()

        # 系统信息
        self.system = platform.system()
        self.machine = platform.machine()

        # GPU信息
        self.gpus: List[GPUInfo] = []
        self.primary_gpu: Optional[GPUInfo] = None

        # 硬件加速支持
        self.hw_acceleration_type = HWAccelerationType.NONE
        self.hw_acceleration = HWAccelerationType.NONE
        self.supported_frameworks: List[str] = []

        # 性能监控
        self.is_monitoring = False
        self.monitoring_thread = None
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_metrics_history = 1000

        # 内存管理
        self.memory_pool = {}
        self.max_memory_pool_size = 1024 * 1024 * 1024  # 1GB
        self.current_pool_size = 0

        # 线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.task_queue = Queue()

        # 初始化
        self._detect_hardware()
        self._initialize_memory_pool()

    def _detect_hardware(self) -> None:
        """检测硬件信息"""
        self.logger.info("开始检测硬件信息...")

        # 检测GPU
        self._detect_gpus()

        # 检测硬件加速支持
        self._detect_hw_acceleration()
        self.hw_acceleration = self.hw_acceleration_type

        self.logger.info(f"硬件检测完成: {len(self.gpus)}个GPU, 主要GPU: {self.primary_gpu.name if self.primary_gpu else 'None'}")

    def _detect_gpus(self) -> None:
        """检测GPU信息"""
        self.gpus.clear()

        # 检测NVIDIA GPU
        try:
            if self._is_nvidia_available():
                nvidia_gpus = self._get_nvidia_gpus()
                self.gpus.extend(nvidia_gpus)
                if not self.primary_gpu:
                    self.primary_gpu = nvidia_gpus[0]
        except Exception as e:
            self.logger.warning(f"NVIDIA GPU检测失败: {str(e)}")

        # 检测AMD GPU
        try:
            if self._is_amd_available():
                amd_gpus = self._get_amd_gpus()
                self.gpus.extend(amd_gpus)
                if not self.primary_gpu:
                    self.primary_gpu = amd_gpus[0]
        except Exception as e:
            self.logger.warning(f"AMD GPU检测失败: {str(e)}")

        # 检测Intel GPU
        try:
            if self._is_intel_available():
                intel_gpus = self._get_intel_gpus()
                self.gpus.extend(intel_gpus)
                if not self.primary_gpu:
                    self.primary_gpu = intel_gpus[0]
        except Exception as e:
            self.logger.warning(f"Intel GPU检测失败: {str(e)}")

        # 检测Apple Silicon
        try:
            if self._is_apple_available():
                apple_gpus = self._get_apple_gpus()
                self.gpus.extend(apple_gpus)
                if not self.primary_gpu:
                    self.primary_gpu = apple_gpus[0]
        except Exception as e:
            self.logger.warning(f"Apple GPU检测失败: {str(e)}")

    def _is_nvidia_available(self) -> bool:
        """检查NVIDIA是否可用"""
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_nvidia_gpus(self) -> List[GPUInfo]:
        """获取NVIDIA GPU信息"""
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.used,driver_version,temperature.gpu,utilization.gpu,power.draw",
                                   "--format=csv,noheader,nounits"],
                                  capture_output=True, timeout=10, text=True)

            if result.returncode != 0:
                return []

            gpus = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 8:
                        gpu_info = GPUInfo(
                            vendor=GPUVendor.NVIDIA,
                            name=parts[0],
                            memory_total=int(parts[1]),
                            memory_used=int(parts[2]),
                            memory_free=int(parts[1]) - int(parts[2]),
                            compute_capability="",  # 需要额外查询
                            driver_version=parts[4],
                            temperature=float(parts[5]),
                            utilization=float(parts[6]),
                            power_usage=float(parts[7])
                        )
                        gpus.append(gpu_info)

            return gpus
        except Exception as e:
            self.logger.error(f"获取NVIDIA GPU信息失败: {str(e)}")
            return []

    def _is_amd_available(self) -> bool:
        """检查AMD是否可用"""
        try:
            result = subprocess.run(["rocm-smi"], capture_output=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_amd_gpus(self) -> List[GPUInfo]:
        """获取AMD GPU信息"""
        # 简化实现，实际需要调用rocm-smi获取详细信息
        return [GPUInfo(
            vendor=GPUVendor.AMD,
            name="AMD GPU",
            memory_total=8192,
            memory_used=0,
            memory_free=8192,
            compute_capability="",
            driver_version="",
            temperature=0,
            utilization=0,
            power_usage=0
        )]

    def _is_intel_available(self) -> bool:
        """检查Intel是否可用"""
        try:
            result = subprocess.run(["intel_gpu_top", "-l", "1"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_intel_gpus(self) -> List[GPUInfo]:
        """获取Intel GPU信息"""
        return [GPUInfo(
            vendor=GPUVendor.INTEL,
            name="Intel GPU",
            memory_total=1024,
            memory_used=0,
            memory_free=1024,
            compute_capability="",
            driver_version="",
            temperature=0,
            utilization=0,
            power_usage=0
        )]

    def _is_apple_available(self) -> bool:
        """检查Apple是否可用"""
        return self.system == "Darwin" and "Apple" in platform.processor()

    def _get_apple_gpus(self) -> List[GPUInfo]:
        """获取Apple GPU信息"""
        try:
            result = subprocess.run(["system_profiler", "SPDisplaysDataType"],
                                  capture_output=True, timeout=10, text=True)

            if result.returncode != 0:
                return []

            # 解析system_profiler输出
            gpu_name = "Apple Silicon GPU"
            for line in result.stdout.split('\n'):
                if 'Chip' in line or 'GPU' in line:
                    gpu_name = line.split(':')[1].strip()
                    break

            return [GPUInfo(
                vendor=GPUVendor.APPLE,
                name=gpu_name,
                memory_total=8192,  # 估算值
                memory_used=0,
                memory_free=8192,
                compute_capability="",
                driver_version="",
                temperature=0,
                utilization=0,
                power_usage=0
            )]
        except Exception as e:
            self.logger.error(f"获取Apple GPU信息失败: {str(e)}")
            return []

    def _detect_hw_acceleration(self) -> None:
        """检测硬件加速支持"""
        self.supported_frameworks.clear()

        # 检测CUDA
        if self._is_cuda_available():
            self.supported_frameworks.append("CUDA")
            self.hw_acceleration_type = HWAccelerationType.CUDA

        # 检测OpenCL
        if self._is_opencl_available():
            self.supported_frameworks.append("OpenCL")

        # 检测Metal (Apple)
        if self._is_metal_available():
            self.supported_frameworks.append("Metal")
            self.hw_acceleration_type = HWAccelerationType.APPLE

        # 检测Vulkan
        if self._is_vulkan_available():
            self.supported_frameworks.append("Vulkan")

        self.logger.info(f"支持的硬件加速框架: {self.supported_frameworks}")

    def _is_cuda_available(self) -> bool:
        """检查CUDA是否可用"""
        try:
            import pycuda.driver as cuda
            cuda.init()
            return True
        except ImportError:
            pass
        except Exception as e:
            self.logger.debug(f"CUDA检测失败: {str(e)}")

        # 通过nvidia-smi检测
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _is_opencl_available(self) -> bool:
        """检查OpenCL是否可用"""
        try:
            import pyopencl
            platforms = pyopencl.get_platforms()
            return len(platforms) > 0
        except ImportError:
            pass
        except Exception as e:
            self.logger.debug(f"OpenCL检测失败: {str(e)}")

        return False

    def _is_metal_available(self) -> bool:
        """检查Metal是否可用"""
        return self.system == "Darwin" and "Apple" in platform.processor()

    def _is_vulkan_available(self) -> bool:
        """检查Vulkan是否可用"""
        try:
            result = subprocess.run(["vulkaninfo"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_memory_info(self) -> MemoryInfo:
        """获取内存信息"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return MemoryInfo(
                total=memory.total,
                available=memory.available,
                used=memory.used,
                percentage=memory.percent,
                swap_total=swap.total,
                swap_used=swap.used,
                swap_percentage=swap.percent
            )
        except Exception as e:
            self.logger.error(f"获取内存信息失败: {str(e)}")
            return MemoryInfo(0, 0, 0, 0, 0, 0, 0)

    def get_gpu_info(self, gpu_index: int = 0) -> Optional[GPUInfo]:
        """获取指定GPU信息"""
        if 0 <= gpu_index < len(self.gpus):
            return self.gpus[gpu_index]
        return None

    def get_all_gpu_info(self) -> List[GPUInfo]:
        """获取所有GPU信息"""
        return self.gpus.copy()

    def get_performance_metrics(self) -> PerformanceMetrics:
        """获取性能指标"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=0.1)

            # 内存使用率
            memory_info = self.get_memory_info()
            memory_usage = memory_info.percentage

            # GPU使用率
            gpu_usage = 0.0
            gpu_memory_usage = 0.0
            temperature = 0.0
            power_usage = 0.0

            if self.primary_gpu:
                gpu_usage = self.primary_gpu.utilization or 0.0
                if self.primary_gpu.memory_total > 0:
                    gpu_memory_usage = (self.primary_gpu.memory_used / self.primary_gpu.memory_total) * 100
                temperature = self.primary_gpu.temperature or 0.0
                power_usage = self.primary_gpu.power_usage or 0.0

            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                gpu_usage=gpu_usage,
                gpu_memory_usage=gpu_memory_usage,
                temperature=temperature,
                power_usage=power_usage,
                fps=0.0,  # 需要在实际处理时计算
                processing_time=0.0
            )
        except Exception as e:
            self.logger.error(f"获取性能指标失败: {str(e)}")
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0)

    def start_monitoring(self, interval: float = 1.0) -> None:
        """开始性能监控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_worker, args=(interval,))
        self.monitoring_thread.start()
        self.logger.info(f"性能监控已启动，间隔: {interval}秒")

    def stop_monitoring(self) -> None:
        """停止性能监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        self.logger.info("性能监控已停止")

    def _monitoring_worker(self, interval: float) -> None:
        """性能监控工作线程"""
        while self.is_monitoring:
            try:
                metrics = self.get_performance_metrics()
                self.metrics_history.append(metrics)

                # 限制历史记录大小
                if len(self.metrics_history) > self.max_metrics_history:
                    self.metrics_history = self.metrics_history[-self.max_metrics_history:]

                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"性能监控错误: {str(e)}")
                time.sleep(interval)

    def get_metrics_history(self, limit: Optional[int] = None) -> List[PerformanceMetrics]:
        """获取性能指标历史"""
        if limit:
            return self.metrics_history[-limit:]
        return self.metrics_history.copy()

    def _initialize_memory_pool(self) -> None:
        """初始化内存池"""
        self.memory_pool = {}
        self.current_pool_size = 0
        self.logger.info("内存池初始化完成")

    def allocate_memory(self, size: int, tag: str = "default") -> Any:
        """分配内存"""
        try:
            # 检查内存池大小
            if self.current_pool_size + size > self.max_memory_pool_size:
                self._cleanup_memory_pool()

            # 分配内存
            memory = bytearray(size)
            self.memory_pool[tag] = {
                'memory': memory,
                'size': size,
                'allocated_time': time.time()
            }
            self.current_pool_size += size

            self.logger.debug(f"内存分配成功: {tag} ({size} bytes)")
            return memory
        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.MEMORY,
                severity=ErrorSeverity.HIGH,
                message=f"内存分配失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="HardwareAcceleration",
                    operation="allocate_memory"
                ),
                user_message="内存分配失败，系统可能内存不足"
            )
            self.error_handler.handle_error(error_info)
            raise

    def free_memory(self, tag: str) -> None:
        """释放内存"""
        if tag in self.memory_pool:
            del self.memory_pool[tag]
            self.current_pool_size = sum(info['size'] for info in self.memory_pool.values())
            self.logger.debug(f"内存释放成功: {tag}")

    def _cleanup_memory_pool(self) -> None:
        """清理内存池"""
        try:
            # 按分配时间排序，删除最旧的内存块
            sorted_items = sorted(self.memory_pool.items(), key=lambda x: x[1]['allocated_time'])

            # 删除一半的内存块
            items_to_remove = len(sorted_items) // 2
            for i in range(items_to_remove):
                tag = sorted_items[i][0]
                self.free_memory(tag)

            self.logger.info(f"内存池清理完成，保留 {len(self.memory_pool)} 个内存块")
        except Exception as e:
            self.logger.error(f"内存池清理失败: {str(e)}")

    def optimize_for_video_processing(self) -> Dict[str, Any]:
        """为视频处理优化系统设置"""
        optimization_settings = {}

        try:
            # CPU优化
            cpu_count = psutil.cpu_count()
            optimization_settings['cpu_threads'] = cpu_count
            optimization_settings['cpu_priority'] = 'high'

            # 内存优化
            memory_info = self.get_memory_info()
            optimization_settings['memory_limit'] = int(memory_info.available * 0.8)
            optimization_settings['memory_pool_size'] = int(memory_info.available * 0.3)

            # GPU优化
            if self.primary_gpu:
                optimization_settings['gpu_enabled'] = True
                optimization_settings['gpu_memory_limit'] = int(self.primary_gpu.memory_free * 0.8)
                optimization_settings['gpu_threads'] = 4  # 根据GPU类型调整
            else:
                optimization_settings['gpu_enabled'] = False

            # 硬件加速设置
            optimization_settings['hw_acceleration'] = self.hw_acceleration_type.value
            optimization_settings['supported_frameworks'] = self.supported_frameworks

            # 线程池设置
            optimization_settings['max_workers'] = min(cpu_count, 8)
            optimization_settings['queue_size'] = 100

            self.logger.info(f"系统优化完成: {optimization_settings}")
            return optimization_settings

        except Exception as e:
            self.logger.error(f"系统优化失败: {str(e)}")
            return optimization_settings

    def submit_task(self, task: Callable, *args, **kwargs) -> Any:
        """提交任务到线程池"""
        try:
            future = self.thread_pool.submit(task, *args, **kwargs)
            return future
        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"任务提交失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="HardwareAcceleration",
                    operation="submit_task"
                ),
                user_message="任务提交失败，请稍后重试"
            )
            self.error_handler.handle_error(error_info)
            raise

    def get_optimal_settings(self) -> Dict[str, Any]:
        """获取最佳处理设置"""
        settings = {}

        try:
            # 基于硬件性能的设置
            if self.primary_gpu:
                if self.primary_gpu.vendor == GPUVendor.NVIDIA:
                    settings['cuda_device'] = 0
                    settings['cuda_streams'] = 2
                    settings['batch_size'] = 16
                elif self.primary_gpu.vendor == GPUVendor.APPLE:
                    settings['metal_device'] = 0
                    settings['batch_size'] = 8
                else:
                    settings['batch_size'] = 4

            # 基于内存的设置
            memory_info = self.get_memory_info()
            if memory_info.available > 8 * 1024 * 1024 * 1024:  # 8GB+
                settings['max_resolution'] = '4K'
                settings['concurrent_tasks'] = 4
            elif memory_info.available > 4 * 1024 * 1024 * 1024:  # 4GB+
                settings['max_resolution'] = '2K'
                settings['concurrent_tasks'] = 2
            else:
                settings['max_resolution'] = '1080p'
                settings['concurrent_tasks'] = 1

            # 基于CPU的设置
            cpu_count = psutil.cpu_count()
            settings['cpu_threads'] = min(cpu_count, 8)

            self.logger.info(f"最佳设置计算完成: {settings}")
            return settings

        except Exception as e:
            self.logger.error(f"最佳设置计算失败: {str(e)}")
            return settings

    def cleanup(self) -> None:
        """清理资源"""
        self.stop_monitoring()
        self.thread_pool.shutdown(wait=True)
        self.memory_pool.clear()
        self.current_pool_size = 0
        self.logger.info("硬件加速管理器清理完成")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局硬件加速管理器实例
_hardware_acceleration: Optional[HardwareAcceleration] = None


def get_hardware_acceleration() -> HardwareAcceleration:
    """获取全局硬件加速管理器实例"""
    global _hardware_acceleration
    if _hardware_acceleration is None:
        _hardware_acceleration = HardwareAcceleration()
    return _hardware_acceleration


def cleanup_hardware_acceleration() -> None:
    """清理全局硬件加速管理器实例"""
    global _hardware_acceleration
    if _hardware_acceleration is not None:
        _hardware_acceleration.cleanup()
        _hardware_acceleration = None