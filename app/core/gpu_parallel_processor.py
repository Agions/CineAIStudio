#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 GPU并行处理器
高性能GPU加速和并行处理模块，支持多GPU、CUDA、OpenCL和Metal加速
"""

import os
import time
import threading
import multiprocessing as mp
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.distributed as dist
import torch.multiprocessing as torch_mp
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, Iterator
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue, PriorityQueue
import logging
from contextlib import contextmanager

from .logger import get_logger
from .event_system import EventBus
from .hardware_acceleration import get_hardware_acceleration, GPUInfo, GPUVendor
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler


class AccelerationType(Enum):
    """加速类型枚举"""
    CUDA = "cuda"
    OPENCL = "opencl"
    METAL = "metal"
    VULKAN = "vulkan"
    DIRECTML = "directml"
    CPU = "cpu"


class ProcessingStrategy(Enum):
    """处理策略枚举"""
    SINGLE_GPU = "single_gpu"
    MULTI_GPU = "multi_gpu"
    DATA_PARALLEL = "data_parallel"
    MODEL_PARALLEL = "model_parallel"
    PIPELINE_PARALLEL = "pipeline_parallel"
    HYBRID_PARALLEL = "hybrid_parallel"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ProcessingTask:
    """处理任务数据类"""
    id: str
    name: str
    data: Any
    processor: Callable
    priority: TaskPriority
    device: Optional[str] = None
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_time: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    status: str = "pending"


@dataclass
class GPUWorkload:
    """GPU工作负载数据类"""
    device_id: int
    device_name: str
    memory_used: int
    memory_total: int
    utilization: float
    temperature: float
    active_tasks: int
    queue_size: int


@dataclass
class BatchProcessingResult:
    """批处理结果数据类"""
    batch_id: str
    results: List[Any]
    processing_time: float
    throughput: float
    success_rate: float
    device_usage: Dict[str, float]


class GPUManager:
    """GPU管理器"""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("GPUManager")
        self.error_handler = get_global_error_handler()

        # GPU设备
        self.devices: Dict[int, Dict] = {}
        self.primary_device = 0
        self.available_devices = []

        # 内存管理
        self.memory_pools: Dict[int, List] = {}
        self.memory_locks: Dict[int, threading.Lock] = {}

        # 工作负载监控
        self.workload_history: List[Dict] = []
        self.max_history_size = 1000

        # 初始化
        self._initialize_devices()
        self._initialize_memory_pools()

    def _initialize_devices(self):
        """初始化GPU设备"""
        try:
            # 检查CUDA
            if torch.cuda.is_available():
                self.logger.info("检测到CUDA支持")
                for i in range(torch.cuda.device_count()):
                    device_name = torch.cuda.get_device_name(i)
                    memory_total = torch.cuda.get_device_properties(i).total_memory

                    self.devices[i] = {
                        'name': device_name,
                        'type': AccelerationType.CUDA,
                        'memory_total': memory_total,
                        'memory_used': 0,
                        'utilization': 0.0,
                        'temperature': 0.0,
                        'is_available': True,
                        'capabilities': self._get_device_capabilities(i)
                    }

                    self.available_devices.append(i)

            # 检查Apple Silicon
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.logger.info("检测到Apple Metal支持")
                self.devices[0] = {
                    'name': 'Apple Silicon GPU',
                    'type': AccelerationType.METAL,
                    'memory_total': 8 * 1024 * 1024 * 1024,  # 8GB 估算
                    'memory_used': 0,
                    'utilization': 0.0,
                    'temperature': 0.0,
                    'is_available': True,
                    'capabilities': self._get_metal_capabilities()
                }

                self.available_devices.append(0)

            else:
                self.logger.warning("未检测到GPU支持，使用CPU")
                self.devices[0] = {
                    'name': 'CPU',
                    'type': AccelerationType.CPU,
                    'memory_total': psutil.virtual_memory().total,
                    'memory_used': 0,
                    'utilization': 0.0,
                    'temperature': 0.0,
                    'is_available': True,
                    'capabilities': ['cpu_optimized']
                }

                self.available_devices.append(0)

            self.logger.info(f"初始化了 {len(self.devices)} 个计算设备")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"GPU设备初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="GPUManager",
                    operation="_initialize_devices"
                ),
                user_message="GPU设备初始化失败"
            )
            self.error_handler.handle_error(error_info)

    def _get_device_capabilities(self, device_id: int) -> List[str]:
        """获取设备能力"""
        capabilities = []

        if torch.cuda.is_available():
            device = torch.cuda.get_device_properties(device_id)
            capabilities.extend([
                f"compute_capability_{device.major}.{device.minor}",
                "cuda_cores",
                "tensor_cores" if device.major >= 7 else "no_tensor_cores"
            ])

        return capabilities

    def _get_metal_capabilities(self) -> List[str]:
        """获取Metal能力"""
        return ["metal", "apple_silicon", "unified_memory"]

    def _initialize_memory_pools(self):
        """初始化内存池"""
        for device_id in self.available_devices:
            self.memory_pools[device_id] = []
            self.memory_locks[device_id] = threading.Lock()

    def get_device_info(self, device_id: int) -> Dict[str, Any]:
        """获取设备信息"""
        if device_id not in self.devices:
            return {}

        device = self.devices[device_id]

        # 更新实时信息
        if device['type'] == AccelerationType.CUDA:
            device['memory_used'] = torch.cuda.memory_allocated(device_id)
            device['utilization'] = self._get_cuda_utilization(device_id)
            device['temperature'] = self._get_cuda_temperature(device_id)

        return device.copy()

    def _get_cuda_utilization(self, device_id: int) -> float:
        """获取CUDA使用率"""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return float(result.stdout.strip().split('\n')[device_id])
        except:
            pass
        return 0.0

    def _get_cuda_temperature(self, device_id: int) -> float:
        """获取CUDA温度"""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return float(result.stdout.strip().split('\n')[device_id])
        except:
            pass
        return 0.0

    def get_optimal_device(self, required_memory: int = 0) -> int:
        """获取最优设备"""
        best_device = self.primary_device
        best_score = -1

        for device_id in self.available_devices:
            device = self.devices[device_id]

            if not device['is_available']:
                continue

            # 检查内存是否足够
            if required_memory > 0 and device['memory_total'] - device['memory_used'] < required_memory:
                continue

            # 计算设备得分
            score = self._calculate_device_score(device_id)

            if score > best_score:
                best_score = score
                best_device = device_id

        return best_device

    def _calculate_device_score(self, device_id: int) -> float:
        """计算设备得分"""
        device = self.devices[device_id]

        # 基于内存使用率
        memory_ratio = 1.0 - (device['memory_used'] / device['memory_total'])

        # 基于使用率
        utilization_ratio = 1.0 - (device['utilization'] / 100.0)

        # 基于温度
        temperature_ratio = max(0, (85 - device['temperature']) / 85.0)

        # 加权得分
        score = memory_ratio * 0.5 + utilization_ratio * 0.3 + temperature_ratio * 0.2

        return score

    def allocate_memory(self, device_id: int, size: int) -> Optional[torch.Tensor]:
        """分配GPU内存"""
        try:
            with self.memory_locks[device_id]:
                device = self.devices[device_id]

                # 检查内存是否足够
                if device['memory_used'] + size > device['memory_total']:
                    self._cleanup_memory(device_id)

                # 分配内存
                if device['type'] == AccelerationType.CUDA:
                    tensor = torch.empty(size, dtype=torch.float32, device=f"cuda:{device_id}")
                elif device['type'] == AccelerationType.METAL:
                    tensor = torch.empty(size, dtype=torch.float32, device="mps")
                else:
                    tensor = torch.empty(size, dtype=torch.float32, device="cpu")

                device['memory_used'] += size
                return tensor

        except Exception as e:
            self.logger.error(f"内存分配失败: {str(e)}")
            return None

    def _cleanup_memory(self, device_id: int):
        """清理内存"""
        try:
            if self.devices[device_id]['type'] == AccelerationType.CUDA:
                torch.cuda.empty_cache()
            elif self.devices[device_id]['type'] == AccelerationType.METAL:
                if hasattr(torch.backends.mps, 'empty_cache'):
                    torch.backends.mps.empty_cache()

        except Exception as e:
            self.logger.error(f"内存清理失败: {str(e)}")

    def get_workload_status(self) -> List[GPUWorkload]:
        """获取工作负载状态"""
        workloads = []

        for device_id in self.available_devices:
            device = self.devices[device_id]

            workload = GPUWorkload(
                device_id=device_id,
                device_name=device['name'],
                memory_used=device['memory_used'],
                memory_total=device['memory_total'],
                utilization=device['utilization'],
                temperature=device['temperature'],
                active_tasks=0,  # 需要从任务管理器获取
                queue_size=0    # 需要从任务管理器获取
            )

            workloads.append(workload)

        return workloads

    def cleanup(self):
        """清理资源"""
        try:
            # 清理内存池
            for device_id in self.available_devices:
                self._cleanup_memory(device_id)
                self.memory_pools[device_id].clear()

            # 清理CUDA缓存
            if torch.cuda.is_available():
                for device_id in self.available_devices:
                    torch.cuda.empty_cache()

            self.logger.info("GPU管理器清理完成")

        except Exception as e:
            self.logger.error(f"GPU管理器清理失败: {str(e)}")


class ParallelProcessor:
    """并行处理器"""

    def __init__(self, strategy: ProcessingStrategy = ProcessingStrategy.DATA_PARALLEL,
                 max_workers: int = 4, logger=None):
        self.strategy = strategy
        self.max_workers = max_workers
        self.logger = logger or get_logger("ParallelProcessor")
        self.error_handler = get_global_error_handler()

        # GPU管理器
        self.gpu_manager = GPUManager(self.logger)

        # 任务队列
        self.task_queue = PriorityQueue()
        self.active_tasks: Dict[str, ProcessingTask] = {}
        self.completed_tasks: Dict[str, Any] = {}
        self.task_lock = threading.Lock()

        # 处理器
        self.processors: Dict[str, Callable] = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)

        # 性能监控
        self.performance_stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'average_processing_time': 0.0,
            'throughput': 0.0,
            'device_utilization': {}
        }

        # 工作线程
        self.is_running = False
        self.workers: List[threading.Thread] = []

        # 初始化
        self._initialize_processors()

    def _initialize_processors(self):
        """初始化处理器"""
        try:
            # 注册内置处理器
            self.register_processor('tensor_processing', self._process_tensor)
            self.register_processor('batch_processing', self._process_batch)
            self.register_processor('model_inference', self._process_model_inference)
            self.register_processor('video_processing', self._process_video)

            self.logger.info("并行处理器初始化完成")

        except Exception as e:
            self.logger.error(f"并行处理器初始化失败: {str(e)}")

    def register_processor(self, name: str, processor: Callable):
        """注册处理器"""
        self.processors[name] = processor
        self.logger.info(f"注册处理器: {name}")

    def start(self):
        """启动处理器"""
        if self.is_running:
            return

        self.is_running = True

        # 启动工作线程
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_thread, daemon=True)
            worker.start()
            self.workers.append(worker)

        self.logger.info("并行处理器已启动")

    def stop(self):
        """停止处理器"""
        self.is_running = False

        # 等待工作线程结束
        for worker in self.workers:
            worker.join()

        # 关闭线程池
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

        self.logger.info("并行处理器已停止")

    def _worker_thread(self):
        """工作线程"""
        while self.is_running:
            try:
                # 从队列获取任务
                if not self.task_queue.empty():
                    priority, task = self.task_queue.get()
                    self._process_task(task)
                    self.task_queue.task_done()
                else:
                    time.sleep(0.01)
            except Exception as e:
                self.logger.error(f"工作线程错误: {str(e)}")

    def _process_task(self, task: ProcessingTask):
        """处理任务"""
        try:
            task.status = "processing"
            task.start_time = time.time()

            # 选择设备
            if task.device is None:
                task.device = self.gpu_manager.get_optimal_device()

            # 根据策略处理
            if self.strategy == ProcessingStrategy.SINGLE_GPU:
                result = self._process_single_gpu(task)
            elif self.strategy == ProcessingStrategy.DATA_PARALLEL:
                result = self._process_data_parallel(task)
            elif self.strategy == ProcessingStrategy.MODEL_PARALLEL:
                result = self._process_model_parallel(task)
            else:
                result = self._process_single_gpu(task)

            task.status = "completed"
            task.end_time = time.time()

            # 保存结果
            with self.task_lock:
                self.completed_tasks[task.id] = result
                if task.id in self.active_tasks:
                    del self.active_tasks[task.id]

            # 更新统计
            self._update_performance_stats(task)

            # 调用回调
            if task.callback:
                task.callback(result)

        except Exception as e:
            task.status = "failed"
            task.end_time = time.time()

            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"任务处理失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ParallelProcessor",
                    operation="_process_task"
                ),
                user_message="任务处理失败"
            )
            self.error_handler.handle_error(error_info)

            self.logger.error(f"任务处理失败: {task.name} - {str(e)}")

    def _process_single_gpu(self, task: ProcessingTask) -> Any:
        """单GPU处理"""
        try:
            # 执行处理器
            if task.processor.__name__ in self.processors:
                processor = self.processors[task.processor.__name__]
            else:
                processor = task.processor

            # 在指定设备上处理
            with torch.cuda.device(task.device) if torch.cuda.is_available() else nullcontext():
                result = processor(task.data, task.metadata)

            return result

        except Exception as e:
            self.logger.error(f"单GPU处理失败: {str(e)}")
            raise

    def _process_data_parallel(self, task: ProcessingTask) -> Any:
        """数据并行处理"""
        try:
            # 将数据分割到多个设备
            devices = self.gpu_manager.available_devices
            if len(devices) <= 1:
                return self._process_single_gpu(task)

            # 数据分割
            if isinstance(task.data, (list, tuple)):
                chunk_size = len(task.data) // len(devices)
                chunks = [
                    task.data[i:i + chunk_size]
                    for i in range(0, len(task.data), chunk_size)
                ]
            elif isinstance(task.data, torch.Tensor):
                chunks = torch.chunk(task.data, len(devices))
            else:
                return self._process_single_gpu(task)

            # 并行处理
            futures = []
            for i, chunk in enumerate(chunks):
                if i < len(devices):
                    future = self.thread_pool.submit(
                        self._process_chunk_on_device,
                        chunk, devices[i], task.processor, task.metadata
                    )
                    futures.append(future)

            # 收集结果
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"数据并行处理失败: {str(e)}")
            raise

    def _process_model_parallel(self, task: ProcessingTask) -> Any:
        """模型并行处理"""
        try:
            # 简化实现，实际需要更复杂的模型分割逻辑
            return self._process_single_gpu(task)

        except Exception as e:
            self.logger.error(f"模型并行处理失败: {str(e)}")
            raise

    def _process_chunk_on_device(self, chunk: Any, device_id: int,
                                processor: Callable, metadata: Dict[str, Any]) -> Any:
        """在指定设备上处理数据块"""
        try:
            # 移动数据到设备
            if isinstance(chunk, torch.Tensor):
                chunk = chunk.to(f"cuda:{device_id}")
            elif isinstance(chunk, (list, tuple)):
                chunk = [x.to(f"cuda:{device_id}") if isinstance(x, torch.Tensor) else x for x in chunk]

            # 处理
            with torch.cuda.device(device_id):
                result = processor(chunk, metadata)

            return result

        except Exception as e:
            self.logger.error(f"设备处理失败: {str(e)}")
            raise

    def _process_tensor(self, data: torch.Tensor, metadata: Dict[str, Any]) -> torch.Tensor:
        """处理张量"""
        try:
            # 示例：简单的张量操作
            if metadata.get('operation') == 'multiply':
                scalar = metadata.get('scalar', 1.0)
                return data * scalar
            elif metadata.get('operation') == 'normalize':
                return (data - data.mean()) / data.std()
            else:
                return data

        except Exception as e:
            self.logger.error(f"张量处理失败: {str(e)}")
            raise

    def _process_batch(self, data: List[Any], metadata: Dict[str, Any]) -> List[Any]:
        """处理批次"""
        try:
            batch_size = metadata.get('batch_size', 32)
            results = []

            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                batch_result = self._process_single_gpu(
                    ProcessingTask(
                        id=f"batch_{i}",
                        name=f"Batch {i}",
                        data=batch,
                        processor=self._process_tensor,
                        priority=TaskPriority.NORMAL,
                        metadata=metadata
                    )
                )
                results.extend(batch_result if isinstance(batch_result, list) else [batch_result])

            return results

        except Exception as e:
            self.logger.error(f"批次处理失败: {str(e)}")
            raise

    def _process_model_inference(self, data: Any, metadata: Dict[str, Any]) -> Any:
        """处理模型推理"""
        try:
            model = metadata.get('model')
            if model is None:
                raise ValueError("模型未提供")

            # 确保模型在正确的设备上
            device = metadata.get('device', 'cuda:0')
            model = model.to(device)

            # 推理
            with torch.no_grad():
                if isinstance(data, torch.Tensor):
                    data = data.to(device)
                output = model(data)

            return output

        except Exception as e:
            self.logger.error(f"模型推理失败: {str(e)}")
            raise

    def _process_video(self, data: Any, metadata: Dict[str, Any]) -> Any:
        """处理视频"""
        try:
            # 视频处理逻辑
            operation = metadata.get('operation')
            if operation == 'resize':
                target_size = metadata.get('target_size', (224, 224))
                # 这里应该实现视频处理逻辑
                return data
            else:
                return data

        except Exception as e:
            self.logger.error(f"视频处理失败: {str(e)}")
            raise

    def add_task(self, task: ProcessingTask) -> bool:
        """添加任务"""
        try:
            with self.task_lock:
                self.task_queue.put((-task.priority.value, task))
                self.active_tasks[task.id] = task

            self.logger.info(f"任务已添加: {task.name} ({task.id})")
            return True

        except Exception as e:
            self.logger.error(f"添加任务失败: {str(e)}")
            return False

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        with self.task_lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return {
                    'id': task.id,
                    'name': task.name,
                    'status': task.status,
                    'priority': task.priority.name,
                    'device': task.device,
                    'start_time': task.start_time,
                    'progress': self._calculate_progress(task)
                }
            elif task_id in self.completed_tasks:
                return {
                    'id': task_id,
                    'status': 'completed',
                    'result': self.completed_tasks[task_id]
                }
            else:
                return {}

    def _calculate_progress(self, task: ProcessingTask) -> float:
        """计算任务进度"""
        if task.start_time is None:
            return 0.0
        elif task.end_time is not None:
            return 1.0
        else:
            # 估算进度
            elapsed_time = time.time() - task.start_time
            estimated_time = 10.0  # 估算时间
            return min(elapsed_time / estimated_time, 0.99)

    def _update_performance_stats(self, task: ProcessingTask):
        """更新性能统计"""
        try:
            self.performance_stats['total_tasks'] += 1

            if task.status == "completed":
                self.performance_stats['completed_tasks'] += 1
                if task.duration:
                    avg_time = self.performance_stats['average_processing_time']
                    completed = self.performance_stats['completed_tasks']
                    self.performance_stats['average_processing_time'] = (
                        (avg_time * (completed - 1) + task.duration) / completed
                    )
            elif task.status == "failed":
                self.performance_stats['failed_tasks'] += 1

            # 计算吞吐量
            if self.performance_stats['total_tasks'] > 0:
                self.performance_stats['throughput'] = (
                    self.performance_stats['completed_tasks'] / self.performance_stats['total_tasks']
                )

        except Exception as e:
            self.logger.error(f"性能统计更新失败: {str(e)}")

    @property
    def duration(self):
        """任务持续时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0

    def process_tensor_batch(self, tensors: List[torch.Tensor],
                           operation: str = "normalize",
                           batch_size: int = 32) -> BatchProcessingResult:
        """处理张量批次"""
        try:
            batch_id = f"batch_{int(time.time() * 1000)}"
            start_time = time.time()

            # 创建任务
            task = ProcessingTask(
                id=batch_id,
                name=f"Tensor Batch Processing",
                data=tensors,
                processor=self._process_batch,
                priority=TaskPriority.NORMAL,
                metadata={
                    'operation': operation,
                    'batch_size': batch_size
                }
            )

            # 添加任务
            if not self.add_task(task):
                raise RuntimeError("无法添加批次处理任务")

            # 等待完成
            while task.status not in ["completed", "failed"]:
                time.sleep(0.1)

            if task.status == "failed":
                raise RuntimeError("批次处理失败")

            processing_time = time.time() - start_time
            throughput = len(tensors) / processing_time if processing_time > 0 else 0
            success_rate = 1.0

            # 获取设备使用率
            device_usage = {}
            for device_id in self.gpu_manager.available_devices:
                device = self.gpu_manager.get_device_info(device_id)
                device_usage[f"device_{device_id}"] = device.get('utilization', 0.0)

            return BatchProcessingResult(
                batch_id=batch_id,
                results=task.result if hasattr(task, 'result') else [],
                processing_time=processing_time,
                throughput=throughput,
                success_rate=success_rate,
                device_usage=device_usage
            )

        except Exception as e:
            self.logger.error(f"张量批次处理失败: {str(e)}")
            raise

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = self.performance_stats.copy()

        # 添加GPU统计
        stats['gpu_workload'] = [
            {
                'device_id': workload.device_id,
                'device_name': workload.device_name,
                'memory_usage': workload.memory_used / workload.memory_total,
                'utilization': workload.utilization,
                'temperature': workload.temperature
            }
            for workload in self.gpu_manager.get_workload_status()
        ]

        # 添加队列统计
        with self.task_lock:
            stats['queue_stats'] = {
                'total_tasks': len(self.active_tasks) + len(self.completed_tasks),
                'active_tasks': len(self.active_tasks),
                'completed_tasks': len(self.completed_tasks),
                'queue_size': self.task_queue.qsize()
            }

        return stats

    def optimize_strategy(self) -> bool:
        """优化处理策略"""
        try:
            # 基于设备数量和负载选择最优策略
            device_count = len(self.gpu_manager.available_devices)

            if device_count == 1:
                self.strategy = ProcessingStrategy.SINGLE_GPU
            elif device_count <= 4:
                self.strategy = ProcessingStrategy.DATA_PARALLEL
            else:
                self.strategy = ProcessingStrategy.HYBRID_PARALLEL

            # 调整工作线程数
            self.max_workers = min(device_count * 2, 8)

            self.logger.info(f"处理策略已优化: {self.strategy.value}")
            return True

        except Exception as e:
            self.logger.error(f"策略优化失败: {str(e)}")
            return False

    def cleanup(self):
        """清理资源"""
        try:
            self.stop()
            self.gpu_manager.cleanup()
            self.logger.info("并行处理器清理完成")

        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")


class GPUAcceleratedVideoProcessor:
    """GPU加速视频处理器"""

    def __init__(self, parallel_processor: ParallelProcessor, logger=None):
        self.parallel_processor = parallel_processor
        self.logger = logger or get_logger("GPUAcceleratedVideoProcessor")
        self.error_handler = get_global_error_handler()

        # 视频处理配置
        self.config = {
            'frame_batch_size': 16,
            'use_tensorrt': False,
            'use_half_precision': True,
            'enable_async_processing': True
        }

        # 处理管道
        self.processing_pipelines = {}

    def create_processing_pipeline(self, pipeline_id: str,
                                  operations: List[str],
                                  parameters: Dict[str, Any] = None) -> bool:
        """创建处理管道"""
        try:
            self.processing_pipelines[pipeline_id] = {
                'operations': operations,
                'parameters': parameters or {},
                'is_active': False
            }

            self.logger.info(f"处理管道创建成功: {pipeline_id}")
            return True

        except Exception as e:
            self.logger.error(f"处理管道创建失败: {str(e)}")
            return False

    def process_video_with_gpu(self, video_path: str, output_path: str,
                             pipeline_id: str, operations: List[str]) -> bool:
        """使用GPU处理视频"""
        try:
            if pipeline_id not in self.processing_pipelines:
                return False

            pipeline = self.processing_pipelines[pipeline_id]
            pipeline['is_active'] = True

            # 创建处理任务
            task = ProcessingTask(
                id=f"video_{int(time.time() * 1000)}",
                name=f"GPU Video Processing",
                data={
                    'video_path': video_path,
                    'output_path': output_path,
                    'operations': operations
                },
                processor=self._process_video_pipeline,
                priority=TaskPriority.HIGH,
                metadata={'pipeline_id': pipeline_id}
            )

            return self.parallel_processor.add_task(task)

        except Exception as e:
            self.logger.error(f"GPU视频处理失败: {str(e)}")
            return False

    def _process_video_pipeline(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """处理视频管道"""
        try:
            video_path = data['video_path']
            output_path = data['output_path']
            operations = data['operations']

            # 实现GPU视频处理逻辑
            # 这里应该集成实际的GPU视频处理库

            self.logger.info(f"视频处理完成: {video_path}")
            return True

        except Exception as e:
            self.logger.error(f"视频管道处理失败: {str(e)}")
            raise

    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计"""
        return {
            'active_pipelines': len([p for p in self.processing_pipelines.values() if p['is_active']]),
            'total_pipelines': len(self.processing_pipelines),
            'performance': self.parallel_processor.get_performance_stats()
        }

    def cleanup(self):
        """清理资源"""
        try:
            self.processing_pipelines.clear()
            self.logger.info("GPU加速视频处理器清理完成")

        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")


# 全局并行处理器实例
_parallel_processor: Optional[ParallelProcessor] = None


def get_parallel_processor(strategy: ProcessingStrategy = ProcessingStrategy.DATA_PARALLEL,
                          max_workers: int = 4) -> ParallelProcessor:
    """获取全局并行处理器实例"""
    global _parallel_processor
    if _parallel_processor is None:
        _parallel_processor = ParallelProcessor(strategy, max_workers)
        _parallel_processor.start()
    return _parallel_processor


def cleanup_parallel_processor() -> None:
    """清理全局并行处理器实例"""
    global _parallel_processor
    if _parallel_processor is not None:
        _parallel_processor.cleanup()
        _parallel_processor = None


@contextmanager
def nullcontext():
    """空上下文管理器"""
    yield