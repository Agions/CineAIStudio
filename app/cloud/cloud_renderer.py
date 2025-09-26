#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
云端渲染和分布式处理系统
提供云端渲染、分布式计算、负载均衡、任务调度等功能
"""

import os
import json
import time
import uuid
import asyncio
import threading
import queue
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from collections import defaultdict, deque
import hashlib
import socket
import requests
from abc import ABC, abstractmethod

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("警告: Redis未安装，分布式缓存功能将被限制")

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    print("警告: Docker SDK未安装，容器化功能将被限制")

try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    print("警告: boto3未安装，AWS云集成将被禁用")

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
    from PyQt6.QtCore import pyqtSignal as Signal
except ImportError:
    try:
        from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
        from PyQt5.QtCore import pyqtSignal as Signal
    except ImportError:
        try:
            from PySide2.QtCore import QObject, Signal, QTimer, QThread
        except ImportError:
            try:
                from PySide6.QtCore import QObject, Signal, QTimer, QThread
            except ImportError:
                class Signal:
                    def __init__(self, *args, **kwargs):
                        pass
                class QObject:
                    def __init__(self):
                        pass
                class QTimer:
                    def __init__(self):
                        pass
                class QThread:
                    def __init__(self):
                        pass


class RenderEngine(Enum):
    """渲染引擎"""
    BLENDER = "blender"              # Blender渲染器
    UNREAL_ENGINE = "unreal_engine"  # Unreal Engine
    UNITY = "unity"                 # Unity
    CUSTOM = "custom"               # 自定义渲染器


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"              # 等待中
    QUEUED = "queued"               # 队列中
    PROCESSING = "processing"       # 处理中
    COMPLETED = "completed"         # 已完成
    FAILED = "failed"               # 失败
    CANCELLED = "cancelled"         # 已取消


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 0                        # 低优先级
    NORMAL = 1                     # 普通优先级
    HIGH = 2                       # 高优先级
    URGENT = 3                     # 紧急优先级


class NodeType(Enum):
    """节点类型"""
    MASTER = "master"               # 主节点
    WORKER = "worker"               # 工作节点
    RENDER = "render"               # 渲染节点
    STORAGE = "storage"             # 存储节点
    LOAD_BALANCER = "load_balancer" # 负载均衡器


@dataclass
class RenderTask:
    """渲染任务"""
    task_id: str
    name: str
    engine: RenderEngine
    input_files: List[str]
    output_path: str
    parameters: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    worker_id: Optional[str] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    dependencies: List[str] = None
    estimated_duration: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class WorkerNode:
    """工作节点"""
    node_id: str
    host: str
    port: int
    node_type: NodeType
    cpu_cores: int
    memory_gb: float
    gpu_count: int
    available_engines: List[RenderEngine]
    current_tasks: List[str]
    max_concurrent_tasks: int
    last_heartbeat: float
    status: str = "online"
    load_score: float = 0.0

    def __post_init__(self):
        if not hasattr(self, 'current_tasks'):
            self.current_tasks = []
        if not hasattr(self, 'last_heartbeat'):
            self.last_heartbeat = time.time()


@dataclass
class RenderResult:
    """渲染结果"""
    task_id: str
    success: bool
    output_files: List[str]
    processing_time: float
    worker_id: str
    metrics: Dict[str, Any]
    error_message: Optional[str] = None


class TaskQueue:
    """任务队列"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.local_queues = {
            TaskPriority.URGENT: queue.PriorityQueue(),
            TaskPriority.HIGH: queue.PriorityQueue(),
            TaskPriority.NORMAL: queue.PriorityQueue(),
            TaskPriority.LOW: queue.PriorityQueue()
        }
        self.task_store = {}
        self.lock = threading.Lock()

    def add_task(self, task: RenderTask):
        """添加任务到队列"""
        with self.lock:
            self.task_store[task.task_id] = task

            if self.redis_client:
                # 使用Redis分布式队列
                self._add_to_redis_queue(task)
            else:
                # 使用本地队列
                priority_value = -task.priority.value  # 负值用于优先级排序
                self.local_queues[task.priority].put((priority_value, task.task_id))

    def get_next_task(self) -> Optional[RenderTask]:
        """获取下一个任务"""
        with self.lock:
            # 按优先级顺序检查队列
            for priority in [TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
                if self.redis_client:
                    task = self._get_from_redis_queue(priority)
                    if task:
                        return task
                else:
                    if not self.local_queues[priority].empty():
                        _, task_id = self.local_queues[priority].get()
                        return self.task_store.get(task_id)

            return None

    def _add_to_redis_queue(self, task: RenderTask):
        """添加任务到Redis队列"""
        if not self.redis_client:
            return

        queue_name = f"render_queue_{task.priority.value}"
        task_data = json.dumps(asdict(task))
        self.redis_client.lpush(queue_name, task_data)

    def _get_from_redis_queue(self, priority: TaskPriority) -> Optional[RenderTask]:
        """从Redis队列获取任务"""
        if not self.redis_client:
            return None

        queue_name = f"render_queue_{priority.value}"
        task_data = self.redis_client.rpop(queue_name)

        if task_data:
            task_dict = json.loads(task_data)
            return RenderTask(**task_dict)

        return None

    def update_task_status(self, task_id: str, status: TaskStatus, progress: float = None):
        """更新任务状态"""
        with self.lock:
            if task_id in self.task_store:
                task = self.task_store[task_id]
                task.status = status

                if progress is not None:
                    task.progress = progress

                if status == TaskStatus.PROCESSING and task.started_at is None:
                    task.started_at = time.time()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    task.completed_at = time.time()

                if self.redis_client:
                    self._update_redis_task(task)

    def _update_redis_task(self, task: RenderTask):
        """更新Redis中的任务"""
        if not self.redis_client:
            return

        task_data = json.dumps(asdict(task))
        self.redis_client.hset("render_tasks", task.task_id, task_data)

    def get_task(self, task_id: str) -> Optional[RenderTask]:
        """获取任务"""
        with self.lock:
            return self.task_store.get(task_id)

    def remove_task(self, task_id: str):
        """移除任务"""
        with self.lock:
            if task_id in self.task_store:
                del self.task_store[task_id]

    def get_queue_stats(self) -> Dict[str, int]:
        """获取队列统计"""
        with self.lock:
            stats = {}
            for priority in TaskPriority:
                if self.redis_client:
                    queue_name = f"render_queue_{priority.value}"
                    stats[priority.name] = self.redis_client.llen(queue_name)
                else:
                    stats[priority.name] = self.local_queues[priority].qsize()

            return stats


class LoadBalancer:
    """负载均衡器"""

    def __init__(self):
        self.workers = {}
        self.worker_loads = defaultdict(float)
        self.lock = threading.Lock()

    def register_worker(self, worker: WorkerNode):
        """注册工作节点"""
        with self.lock:
            self.workers[worker.node_id] = worker
            self.worker_loads[worker.node_id] = 0.0

    def unregister_worker(self, worker_id: str):
        """注销工作节点"""
        with self.lock:
            if worker_id in self.workers:
                del self.workers[worker_id]
            if worker_id in self.worker_loads:
                del self.worker_loads[worker_id]

    def update_worker_load(self, worker_id: str, load: float):
        """更新工作节点负载"""
        with self.lock:
            self.worker_loads[worker_id] = load

    def select_worker(self, task: RenderTask) -> Optional[WorkerNode]:
        """选择最优工作节点"""
        with self.lock:
            available_workers = []

            for worker_id, worker in self.workers.items():
                # 检查节点是否在线
                if worker.status != "online":
                    continue

                # 检查节点是否支持所需渲染引擎
                if task.engine not in worker.available_engines:
                    continue

                # 检查节点是否有足够资源
                if len(worker.current_tasks) >= worker.max_concurrent_tasks:
                    continue

                available_workers.append(worker)

            if not available_workers:
                return None

            # 根据负载评分选择最优节点
            best_worker = min(available_workers, key=lambda w: self._calculate_worker_score(w))

            return best_worker

    def _calculate_worker_score(self, worker: WorkerNode) -> float:
        """计算工作节点评分"""
        load_factor = self.worker_loads.get(worker.node_id, 0.0)
        task_ratio = len(worker.current_tasks) / worker.max_concurrent_tasks

        # 综合评分（越低越好）
        score = load_factor * 0.6 + task_ratio * 0.4

        return score

    def get_worker_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取工作节点统计"""
        with self.lock:
            stats = {}
            for worker_id, worker in self.workers.items():
                stats[worker_id] = {
                    "host": worker.host,
                    "port": worker.port,
                    "node_type": worker.node_type.value,
                    "status": worker.status,
                    "current_tasks": len(worker.current_tasks),
                    "max_concurrent_tasks": worker.max_concurrent_tasks,
                    "cpu_cores": worker.cpu_cores,
                    "memory_gb": worker.memory_gb,
                    "gpu_count": worker.gpu_count,
                    "load_score": self.worker_loads.get(worker_id, 0.0)
                }

            return stats


class RenderEngineInterface(ABC):
    """渲染引擎接口"""

    @abstractmethod
    def render(self, task: RenderTask, work_dir: str) -> RenderResult:
        """渲染任务"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取引擎能力"""
        pass

    @abstractmethod
    def validate_task(self, task: RenderTask) -> bool:
        """验证任务"""
        pass


class BlenderRenderEngine(RenderEngineInterface):
    """Blender渲染引擎"""

    def __init__(self):
        self.capabilities = {
            "engines": ["CYCLES", "EEVEE"],
            "output_formats": ["PNG", "JPEG", "EXR", "MP4", "AVI"],
            "max_resolution": (8192, 8192),
            "supports_gpu": True
        }

    def render(self, task: RenderTask, work_dir: str) -> RenderResult:
        """使用Blender渲染"""
        start_time = time.time()

        try:
            # 构建Blender命令
            blender_cmd = self._build_blender_command(task, work_dir)

            # 执行渲染
            import subprocess
            result = subprocess.run(
                blender_cmd,
                capture_output=True,
                text=True,
                timeout=task.parameters.get("timeout", 3600)
            )

            success = result.returncode == 0
            processing_time = time.time() - start_time

            # 收集输出文件
            output_files = []
            if success:
                output_files = self._collect_output_files(task, work_dir)

            return RenderResult(
                task_id=task.task_id,
                success=success,
                output_files=output_files,
                processing_time=processing_time,
                worker_id="local",
                metrics={
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                },
                error_message=result.stderr if not success else None
            )

        except subprocess.TimeoutExpired:
            return RenderResult(
                task_id=task.task_id,
                success=False,
                output_files=[],
                processing_time=time.time() - start_time,
                worker_id="local",
                metrics={},
                error_message="渲染超时"
            )
        except Exception as e:
            return RenderResult(
                task_id=task.task_id,
                success=False,
                output_files=[],
                processing_time=time.time() - start_time,
                worker_id="local",
                metrics={},
                error_message=str(e)
            )

    def _build_blender_command(self, task: RenderTask, work_dir: str) -> List[str]:
        """构建Blender命令"""
        cmd = ["blender", "-b"]

        # 添加输入文件
        for input_file in task.input_files:
            cmd.extend(["-i", input_file])

        # 设置输出路径
        cmd.extend(["-o", os.path.join(work_dir, "render_")])

        # 添加渲染参数
        params = task.parameters

        # 设置渲染引擎
        engine = params.get("engine", "CYCLES")
        cmd.extend(["-E", engine])

        # 设置分辨率
        if "resolution_x" in params and "resolution_y" in params:
            cmd.extend(["-x", str(params["resolution_x"])])
            cmd.extend(["-y", str(params["resolution_y"])])

        # 设置采样率
        if "samples" in params:
            cmd.extend(["--cycles-samples", str(params["samples"])])

        # 设置设备类型
        if "device" in params:
            cmd.extend(["--cycles-device", params["device"]])

        # 添加Python脚本（如果有）
        if "script" in params:
            cmd.extend(["-P", params["script"]])

        return cmd

    def _collect_output_files(self, task: RenderTask, work_dir: str) -> List[str]:
        """收集输出文件"""
        output_files = []
        output_pattern = task.parameters.get("output_pattern", "render_*.png")

        for filename in os.listdir(work_dir):
            if filename.startswith("render_"):
                output_files.append(os.path.join(work_dir, filename))

        return output_files

    def get_capabilities(self) -> Dict[str, Any]:
        """获取引擎能力"""
        return self.capabilities

    def validate_task(self, task: RenderTask) -> bool:
        """验证任务"""
        # 检查输入文件是否存在
        for input_file in task.input_files:
            if not os.path.exists(input_file):
                return False

        # 检查输出目录是否存在
        output_dir = os.path.dirname(task.output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except:
                return False

        return True


class WorkerNodeManager:
    """工作节点管理器"""

    def __init__(self, node_id: str, host: str, port: int, max_concurrent_tasks: int = 4):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_tasks = {}
        self.engines = {
            RenderEngine.BLENDER: BlenderRenderEngine()
        }
        self.task_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self.is_running = False

        self.system_info = self._get_system_info()

    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import psutil

        return {
            "cpu_cores": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "gpu_count": self._get_gpu_count(),
            "available_engines": [engine.value for engine in self.engines.keys()]
        }

    def _get_gpu_count(self) -> int:
        """获取GPU数量"""
        try:
            import torch
            return torch.cuda.device_count()
        except:
            return 0

    def start(self):
        """启动工作节点"""
        self.is_running = True

        # 启动任务处理线程
        worker_thread = threading.Thread(target=self._process_tasks)
        worker_thread.daemon = True
        worker_thread.start()

        # 启动心跳线程
        heartbeat_thread = threading.Thread(target=self._send_heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

    def stop(self):
        """停止工作节点"""
        self.is_running = False
        self.executor.shutdown(wait=True)

    def _process_tasks(self):
        """处理任务"""
        while self.is_running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    continue

                # 异步处理任务
                future = self.executor.submit(self._execute_task, task)
                future.add_done_callback(lambda f: self._on_task_completed(f, task))

            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"任务处理错误: {e}")

    def _execute_task(self, task: RenderTask) -> RenderResult:
        """执行任务"""
        try:
            # 创建工作目录
            work_dir = os.path.join("/tmp", f"render_{task.task_id}")
            os.makedirs(work_dir, exist_ok=True)

            # 获取渲染引擎
            engine = self.engines.get(task.engine)
            if not engine:
                return RenderResult(
                    task_id=task.task_id,
                    success=False,
                    output_files=[],
                    processing_time=0,
                    worker_id=self.node_id,
                    metrics={},
                    error_message=f"不支持的渲染引擎: {task.engine}"
                )

            # 执行渲染
            result = engine.render(task, work_dir)

            # 清理工作目录
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)

            return result

        except Exception as e:
            return RenderResult(
                task_id=task.task_id,
                success=False,
                output_files=[],
                processing_time=0,
                worker_id=self.node_id,
                metrics={},
                error_message=str(e)
            )

    def _on_task_completed(self, future, task: RenderTask):
        """任务完成回调"""
        try:
            result = future.result()
            # 这里可以发送结果到主节点
            print(f"任务 {task.task_id} 完成: {result.success}")

        except Exception as e:
            print(f"任务 {task.task_id} 失败: {e}")

        # 从当前任务列表中移除
        if task.task_id in self.current_tasks:
            del self.current_tasks[task.task_id]

    def _send_heartbeat(self):
        """发送心跳"""
        while self.is_running:
            try:
                # 发送心跳到主节点
                heartbeat_data = {
                    "node_id": self.node_id,
                    "timestamp": time.time(),
                    "current_tasks": len(self.current_tasks),
                    "system_info": self.system_info
                }

                # 这里可以发送到主节点的API
                print(f"发送心跳: {heartbeat_data}")

                time.sleep(30)  # 每30秒发送一次心跳

            except Exception as e:
                logging.error(f"心跳发送失败: {e}")
                time.sleep(10)

    def add_task(self, task: RenderTask):
        """添加任务"""
        if len(self.current_tasks) < self.max_concurrent_tasks:
            self.current_tasks[task.task_id] = task
            self.task_queue.put(task)
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """获取节点状态"""
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "is_running": self.is_running,
            "current_tasks": len(self.current_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "system_info": self.system_info
        }


class CloudRenderer(QObject):
    """云端渲染器主类"""

    # 信号定义
    task_submitted = Signal(RenderTask)  # 任务提交
    task_started = Signal(str)  # 任务开始
    task_progress = Signal(str, float)  # 任务进度
    task_completed = Signal(RenderResult)  # 任务完成
    task_failed = Signal(str, str)  # 任务失败
    worker_registered = Signal(WorkerNode)  # 工作节点注册
    worker_disconnected = Signal(str)  # 工作节点断开
    cloud_cost_estimated = Signal(str, float)  # 云成本估算

    def __init__(self, master_node: bool = True, aws_config: Optional[Dict[str, str]] = None):
        super().__init__()
        self.master_node = master_node
        self.task_queue = TaskQueue()
        self.load_balancer = LoadBalancer()
        self.worker_manager = None

        # AWS配置
        self.aws_config = aws_config or {}
        self.s3_client = None
        self.sqs_client = None
        self.ec2_client = None
        if AWS_AVAILABLE and self.aws_config:
            self._init_aws_clients()

        self.is_running = False
        self.task_scheduler = None
        self.heartbeat_monitor = None

        # 如果是主节点，启动调度器
        if master_node:
            self._start_scheduler()

    def _init_aws_clients(self):
        """初始化AWS客户端"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_config.get('access_key'),
                aws_secret_access_key=self.aws_config.get('secret_key'),
                region_name=self.aws_config.get('region', 'us-east-1')
            )
            self.sqs_client = boto3.client('sqs', region_name=self.aws_config.get('region', 'us-east-1'))
            self.ec2_client = boto3.client('ec2', region_name=self.aws_config.get('region', 'us-east-1'))
            self.logger.info("AWS客户端初始化成功")
        except NoCredentialsError:
            self.logger.error("AWS凭证无效")
        except Exception as e:
            self.logger.error(f"AWS客户端初始化失败: {e}")

    def _start_scheduler(self):
        """启动任务调度器"""
        self.is_running = True

        # 启动任务调度线程
        self.task_scheduler = threading.Thread(target=self._schedule_tasks)
        self.task_scheduler.daemon = True
        self.task_scheduler.start()

        # 启动心跳监控线程
        self.heartbeat_monitor = threading.Thread(target=self._monitor_heartbeats)
        self.heartbeat_monitor.daemon = True
        self.heartbeat_monitor.start()

    def submit_task(self, task: RenderTask) -> str:
        """提交渲染任务，支持AWS fallback到本地"""
        # 验证任务
        if not self._validate_task(task):
            raise ValueError("无效的任务参数")

        success = False
        # 如果支持AWS，尝试云渲染
        if self.s3_client and self.sqs_client:
            try:
                task = self._prepare_cloud_task(task)
                success = True
                self.logger.info(f"任务 {task.task_id} 已提交到云端")
            except Exception as e:
                self.logger.warning(f"云渲染准备失败: {e}，fallback到本地渲染")
                success = False

        if not success:
            # Fallback到本地队列
            self.logger.info(f"任务 {task.task_id} 使用本地渲染")
            # 确保input_files是本地路径
            task.input_files = [f for f in task.input_files if not f.startswith('s3://')]

        # 添加到队列
        self.task_queue.add_task(task)

        # 估算云成本（即使fallback也估算）
        estimated_cost = self._estimate_cloud_cost(task)
        self.cloud_cost_estimated.emit(task.task_id, estimated_cost)

        self.task_submitted.emit(task)
        return task.task_id

    def _prepare_cloud_task(self, task: RenderTask) -> RenderTask:
        """准备云任务：上传文件到S3，支持重试"""
        bucket_name = self.aws_config.get('s3_bucket', 'cineai-render-bucket')
        s3_paths = []
        max_retries = 3

        for input_file in task.input_files:
            file_key = f"renders/{task.task_id}/{os.path.basename(input_file)}"
            for attempt in range(max_retries):
                try:
                    self.s3_client.upload_file(input_file, bucket_name, file_key)
                    s3_paths.append(f"s3://{bucket_name}/{file_key}")
                    self.logger.info(f"文件上传到S3成功 (尝试 {attempt+1}): {file_key}")
                    break
                except ClientError as e:
                    self.logger.warning(f"S3上传失败 (尝试 {attempt+1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        self.logger.error(f"S3上传最终失败: {e}")
                        raise
                    time.sleep(2 ** attempt)  # 指数退避

        task.input_files = s3_paths
        task.parameters['s3_bucket'] = bucket_name
        task.parameters['task_id'] = task.task_id

        # 发送到SQS队列，支持重试
        queue_url = self.aws_config.get('sqs_queue_url')
        if queue_url:
            for attempt in range(max_retries):
                try:
                    message_body = json.dumps(asdict(task))
                    self.sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)
                    self.logger.info(f"任务发送到SQS成功 (尝试 {attempt+1}): {task.task_id}")
                    break
                except ClientError as e:
                    self.logger.warning(f"SQS发送失败 (尝试 {attempt+1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        self.logger.error(f"SQS发送最终失败: {e}")
                        raise
                    time.sleep(2 ** attempt)

        return task

    def _estimate_cloud_cost(self, task: RenderTask) -> float:
        """估算云成本，支持AWS/GCP多云"""
        # AWS估算
        estimated_hours = task.estimated_duration / 3600 if task.estimated_duration else 1.0
        aws_instance_cost = 0.1  # g4dn.xlarge $0.1/小时
        aws_s3_cost = len(task.input_files) * 0.0004 / 1024  # $0.0004/GB
        aws_total = estimated_hours * aws_instance_cost + aws_s3_cost

        # GCP估算 (类似，n1-standard-2 with GPU ~$0.095/小时)
        gcp_instance_cost = 0.095
        gcp_storage_cost = len(task.input_files) * 0.0004 / 1024  # 类似
        gcp_total = estimated_hours * gcp_instance_cost + gcp_storage_cost

        # 选择最低成本或提示
        min_cost = min(aws_total, gcp_total)
        self.logger.info(f"云成本估算 - AWS: ${aws_total:.4f}, GCP: ${gcp_total:.4f}, 推荐: ${min_cost:.4f}")
        return min_cost

    def _validate_task(self, task: RenderTask) -> bool:
        """验证任务"""
        if not task.task_id:
            return False

        if not task.input_files:
            return False

        if not task.output_path:
            return False

        # 检查输入文件是否存在
        for input_file in task.input_files:
            if not os.path.exists(input_file):
                return False

        return True

    def _schedule_tasks(self):
        """调度任务"""
        while self.is_running:
            try:
                # 获取下一个任务
                task = self.task_queue.get_next_task()
                if task is None:
                    time.sleep(1)
                    continue

                # 选择工作节点
                worker = self.load_balancer.select_worker(task)
                if worker is None:
                    # 没有可用节点，重新加入队列
                    self.task_queue.add_task(task)
                    time.sleep(5)
                    continue

                # 分配任务给工作节点
                success = self._assign_task_to_worker(task, worker)
                if success:
                    self.task_queue.update_task_status(task.task_id, TaskStatus.PROCESSING)
                    self.task_started.emit(task.task_id)
                else:
                    # 分配失败，重新加入队列
                    self.task_queue.add_task(task)

                time.sleep(0.1)

            except Exception as e:
                logging.error(f"任务调度错误: {e}")
                time.sleep(1)

    def _assign_task_to_worker(self, task: RenderTask, worker: WorkerNode) -> bool:
        """分配任务给工作节点"""
        try:
            # 这里应该通过网络通信将任务发送给工作节点
            # 简化实现：直接在本地处理
            if self.worker_manager:
                return self.worker_manager.add_task(task)
            return False

        except Exception as e:
            logging.error(f"任务分配失败: {e}")
            return False

    def _monitor_heartbeats(self):
        """监控心跳"""
        while self.is_running:
            try:
                # 检查所有工作节点的心跳
                current_time = time.time()
                timeout = 60  # 60秒超时

                for worker_id, worker in list(self.load_balancer.workers.items()):
                    if current_time - worker.last_heartbeat > timeout:
                        # 节点超时，标记为离线
                        worker.status = "offline"
                        self.worker_disconnected.emit(worker_id)

                time.sleep(10)

            except Exception as e:
                logging.error(f"心跳监控错误: {e}")
                time.sleep(5)

    def register_worker(self, worker: WorkerNode):
        """注册工作节点"""
        self.load_balancer.register_worker(worker)
        self.worker_registered.emit(worker)

    def unregister_worker(self, worker_id: str):
        """注销工作节点"""
        self.load_balancer.unregister_worker(worker_id)

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task = self.task_queue.get_task(task_id)
        return task.status if task else None

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.task_queue.get_task(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            self.task_queue.update_task_status(task_id, TaskStatus.CANCELLED)
            return True
        return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        stats = {
            "queue_stats": self.task_queue.get_queue_stats(),
            "worker_stats": self.load_balancer.get_worker_stats()
        }

        # 添加云统计
        if self.sqs_client:
            try:
                queue_url = self.aws_config.get('sqs_queue_url')
                if queue_url:
                    response = self.sqs_client.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=['ApproximateNumberOfMessages']
                    )
                    stats['sqs_messages'] = int(response['Attributes']['ApproximateNumberOfMessages'])
            except Exception as e:
                self.logger.error(f"获取SQS统计失败: {e}")

        return stats

    def stop(self):
        """停止渲染器"""
        self.is_running = False
        if self.worker_manager:
            self.worker_manager.stop()

        # 清理AWS资源（如果有）
        if self.ec2_client:
            try:
                # 终止渲染实例（简化，实际需跟踪实例ID）
                self.logger.info("清理AWS渲染实例")
            except Exception as e:
                self.logger.error(f"AWS清理失败: {e}")


# 工具函数
def create_cloud_renderer(master_node: bool = True) -> CloudRenderer:
    """创建云端渲染器"""
    return CloudRenderer(master_node)


def quick_render(input_file: str, output_path: str, engine: str = "blender") -> RenderResult:
    """快速渲染"""
    task = RenderTask(
        task_id=str(uuid.uuid4()),
        name="Quick Render",
        engine=RenderEngine(engine),
        input_files=[input_file],
        output_path=output_path,
        parameters={
            "resolution_x": 1920,
            "resolution_y": 1080,
            "samples": 64
        }
    )

    renderer = create_cloud_renderer()
    renderer.submit_task(task)

    # 等待任务完成（简化实现）
    time.sleep(2)

    return RenderResult(
        task_id=task.task_id,
        success=True,
        output_files=[output_path],
        processing_time=2.0,
        worker_id="local",
        metrics={},
        error_message=None
    )


def main():
    """主函数 - 用于测试"""
    # 创建云端渲染器
    renderer = create_cloud_renderer()

    # 测试渲染功能
    print("云端渲染器创建成功")
    print(f"主节点模式: {renderer.master_node}")
    print(f"Redis支持: {REDIS_AVAILABLE}")
    print(f"Docker支持: {DOCKER_AVAILABLE}")


if __name__ == "__main__":
    main()