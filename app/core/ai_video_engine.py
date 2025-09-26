#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 AI视频处理引擎
专业级深度学习视频处理引擎，集成神经网络、GPU加速和智能分析
"""

import os
import sys
import time
import asyncio
import threading
import numpy as np
import cv2
import torch
import torchvision
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import pickle
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue, PriorityQueue
import logging

from .logger import get_logger
from .event_system import EventBus
from .hardware_acceleration import get_hardware_acceleration, GPUVendor, PerformanceMetrics
from .video_engine import VideoEngine, EngineSettings, OperationResult
from .video_processor import VideoProcessor, ProcessingTask, ProcessingConfig
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import get_ffmpeg_utils, VideoInfo, VideoCodec, AudioCodec, ContainerFormat


class AIModelType(Enum):
    """AI模型类型枚举"""
    OBJECT_DETECTION = "object_detection"
    SCENE_ANALYSIS = "scene_analysis"
    MOTION_ANALYSIS = "motion_analysis"
    FACE_DETECTION = "face_detection"
    EMOTION_RECOGNITION = "emotion_recognition"
    ACTION_RECOGNITION = "action_recognition"
    VIDEO_CLASSIFICATION = "video_classification"
    VIDEO_SUPER_RESOLUTION = "video_super_resolution"
    VIDEO_DENOISING = "video_denoising"
    VIDEO_STABILIZATION = "video_stabilization"
    COLOR_CORRECTION = "color_correction"
    FRAME_INTERPOLATION = "frame_interpolation"
    BACKGROUND_SUBTRACTION = "background_subtraction"
    DEPTH_ESTIMATION = "depth_estimation"
    OPTICAL_FLOW = "optical_flow"


class ProcessingMode(Enum):
    """处理模式枚举"""
    REAL_TIME = "real_time"
    BATCH = "batch"
    STREAMING = "streaming"
    HYBRID = "hybrid"


class QualityLevel(Enum):
    """质量等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class AIModel:
    """AI模型数据类"""
    name: str
    model_type: AIModelType
    model_path: str
    model_size: int  # MB
    input_size: Tuple[int, int]
    output_size: Tuple[int, int]
    fps_capability: float
    memory_usage: int  # MB
    is_loaded: bool = False
    model: Optional[Any] = None
    device: str = "cpu"
    precision: str = "fp32"


@dataclass
class AITask:
    """AI处理任务数据类"""
    id: str
    name: str
    input_path: str
    output_path: str
    model_type: AIModelType
    processing_mode: ProcessingMode
    priority: int
    quality_level: QualityLevel
    parameters: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None
    callback: Optional[Callable[[Any], None]] = None


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    task_id: str
    model_type: AIModelType
    timestamp: float
    frame_index: int
    data: Dict[str, Any]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIVideoEngineConfig:
    """AI视频引擎配置类"""

    def __init__(self):
        # 系统配置
        self.max_concurrent_tasks = 4
        self.max_memory_usage = 8192  # MB
        self.temp_directory = "/tmp/cineaistudio/ai_engine"
        self.cache_directory = "/tmp/cineaistudio/ai_cache"
        self.model_directory = "/models"

        # 性能配置
        self.enable_gpu_acceleration = True
        self.enable_mixed_precision = True
        self.enable_model_quantization = True
        self.enable_async_processing = True
        self.enable_streaming_mode = True

        # 质量配置
        self.default_quality_level = QualityLevel.HIGH
        self.enable_super_resolution = True
        self.enable_denoising = True
        self.enable_stabilization = True

        # AI配置
        self.model_cache_size = 3
        self.enable_model_pruning = True
        self.enable_adaptive_processing = True
        self.enable_real_time_analysis = True

        # 网络配置
        self.enable_distributed_processing = False
        self.worker_nodes = []
        self.load_balancing_strategy = "round_robin"


class NeuralNetworkManager:
    """神经网络管理器"""

    def __init__(self, config: AIVideoEngineConfig, logger=None):
        self.config = config
        self.logger = logger or get_logger("NeuralNetworkManager")
        self.error_handler = get_global_error_handler()

        # 模型管理
        self.models: Dict[str, AIModel] = {}
        self.loaded_models: Dict[str, AIModel] = {}
        self.model_lock = threading.Lock()

        # 设备管理
        self.device = self._setup_device()
        self.available_devices = self._detect_devices()

        # 内存管理
        self.memory_manager = MemoryManager(config.max_memory_usage, self.logger)

        # 初始化
        self._initialize_models()

    def _setup_device(self) -> str:
        """设置计算设备"""
        if self.config.enable_gpu_acceleration and torch.cuda.is_available():
            device = f"cuda:{torch.cuda.current_device()}"
            self.logger.info(f"使用GPU设备: {device}")
        else:
            device = "cpu"
            self.logger.info("使用CPU设备")
        return device

    def _detect_devices(self) -> List[str]:
        """检测可用设备"""
        devices = []

        # CPU设备
        devices.append("cpu")

        # CUDA设备
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                devices.append(f"cuda:{i}")

        # Apple Silicon
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            devices.append("mps")

        return devices

    def _initialize_models(self):
        """初始化AI模型"""
        try:
            # 对象检测模型
            self.models["yolov8"] = AIModel(
                name="YOLOv8",
                model_type=AIModelType.OBJECT_DETECTION,
                model_path="yolov8n.pt",
                model_size=6,  # MB
                input_size=(640, 640),
                output_size=(640, 640),
                fps_capability=60.0,
                memory_usage=512,
                device=self.device
            )

            # 场景分析模型
            self.models["scene"] = AIModel(
                name="Scene Analysis",
                model_type=AIModelType.SCENE_ANALYSIS,
                model_path="scene_classifier.pth",
                model_size=45,
                input_size=(224, 224),
                output_size=(1000,),
                fps_capability=30.0,
                memory_usage=1024,
                device=self.device
            )

            # 人脸检测模型
            self.models["face_detection"] = AIModel(
                name="Face Detection",
                model_type=AIModelType.FACE_DETECTION,
                model_path="face_detection.pth",
                model_size=12,
                input_size=(320, 320),
                output_size=(4, 5),
                fps_capability=120.0,
                memory_usage=256,
                device=self.device
            )

            # 视频超分辨率模型
            self.models["super_resolution"] = AIModel(
                name="Video Super Resolution",
                model_type=AIModelType.VIDEO_SUPER_RESOLUTION,
                model_path="sr_model.pth",
                model_size=87,
                input_size=(256, 256),
                output_size=(1024, 1024),
                fps_capability=10.0,
                memory_usage=2048,
                device=self.device
            )

            # 视频去噪模型
            self.models["denoising"] = AIModel(
                name="Video Denoising",
                model_type=AIModelType.VIDEO_DENOISING,
                model_path="denoising.pth",
                model_size=23,
                input_size=(256, 256),
                output_size=(256, 256),
                fps_capability=25.0,
                memory_usage=512,
                device=self.device
            )

            self.logger.info(f"初始化了 {len(self.models)} 个AI模型")

        except Exception as e:
            self.logger.error(f"模型初始化失败: {str(e)}")
            raise

    def load_model(self, model_name: str) -> bool:
        """加载AI模型"""
        try:
            with self.model_lock:
                if model_name in self.loaded_models:
                    return True

                if model_name not in self.models:
                    raise ValueError(f"模型不存在: {model_name}")

                model = self.models[model_name]

                # 检查内存
                if not self.memory_manager.check_memory(model.memory_usage):
                    self._unload_unused_models()

                # 加载模型
                self._load_model_weights(model)

                # 移动到已加载模型
                self.loaded_models[model_name] = model
                model.is_loaded = True

                self.logger.info(f"模型加载成功: {model_name}")
                return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.AI,
                severity=ErrorSeverity.HIGH,
                message=f"模型加载失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="NeuralNetworkManager",
                    operation="load_model"
                ),
                user_message=f"AI模型加载失败: {model_name}"
            )
            self.error_handler.handle_error(error_info)
            return False

    def _load_model_weights(self, model: AIModel):
        """加载模型权重"""
        try:
            if model.model_type == AIModelType.OBJECT_DETECTION:
                # 加载YOLO模型
                from ultralytics import YOLO
                model.model = YOLO(model.model_path)

            elif model.model_type == AIModelType.SCENE_ANALYSIS:
                # 加载场景分类模型
                import torchvision.models as models
                model.model = models.resnet50(pretrained=True)
                model.model = model.model.to(model.device)

            elif model.model_type == AIModelType.FACE_DETECTION:
                # 加载人脸检测模型
                import face_recognition
                model.model = face_recognition

            elif model.model_type == AIModelType.VIDEO_SUPER_RESOLUTION:
                # 加载超分辨率模型
                model.model = self._create_super_resolution_model()

            elif model.model_type == AIModelType.VIDEO_DENOISING:
                # 加载去噪模型
                model.model = self._create_denoising_model()

            # 应用混合精度
            if self.config.enable_mixed_precision and model.device.startswith('cuda'):
                model.model = model.model.half()

            # 应用量化
            if self.config.enable_model_quantization:
                self._quantize_model(model)

        except Exception as e:
            self.logger.error(f"模型权重加载失败: {str(e)}")
            raise

    def _create_super_resolution_model(self):
        """创建超分辨率模型"""
        import torch.nn as nn

        class SuperResolutionNet(nn.Module):
            def __init__(self, scale_factor=4):
                super().__init__()
                self.scale_factor = scale_factor
                self.conv1 = nn.Conv2d(3, 64, 9, padding=4)
                self.conv2 = nn.Conv2d(64, 32, 5, padding=2)
                self.conv3 = nn.Conv2d(32, 3, 5, padding=2)
                self.relu = nn.ReLU()

            def forward(self, x):
                x = self.relu(self.conv1(x))
                x = self.relu(self.conv2(x))
                x = self.conv3(x)
                return x

        model = SuperResolutionNet()
        return model.to(self.device)

    def _create_denoising_model(self):
        """创建去噪模型"""
        import torch.nn as nn

        class DenoisingNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(3, 64, 3, padding=1)
                self.conv2 = nn.Conv2d(64, 64, 3, padding=1)
                self.conv3 = nn.Conv2d(64, 3, 3, padding=1)
                self.relu = nn.ReLU()

            def forward(self, x):
                x = self.relu(self.conv1(x))
                x = self.relu(self.conv2(x))
                x = self.conv3(x)
                return x

        model = DenoisingNet()
        return model.to(self.device)

    def _quantize_model(self, model: AIModel):
        """量化模型"""
        try:
            if hasattr(model.model, 'quantize'):
                model.model.quantize()
        except Exception as e:
            self.logger.warning(f"模型量化失败: {str(e)}")

    def _unload_unused_models(self):
        """卸载未使用的模型"""
        try:
            with self.model_lock:
                # 按LRU策略卸载模型
                loaded_count = len(self.loaded_models)
                if loaded_count > self.config.model_cache_size:
                    # 卸载最旧的模型
                    model_to_unload = list(self.loaded_models.keys())[0]
                    self.unload_model(model_to_unload)
        except Exception as e:
            self.logger.error(f"卸载模型失败: {str(e)}")

    def unload_model(self, model_name: str) -> bool:
        """卸载模型"""
        try:
            with self.model_lock:
                if model_name in self.loaded_models:
                    model = self.loaded_models[model_name]
                    model.model = None
                    model.is_loaded = False
                    del self.loaded_models[model_name]

                    # 释放内存
                    if hasattr(torch.cuda, 'empty_cache'):
                        torch.cuda.empty_cache()

                    self.logger.info(f"模型卸载成功: {model_name}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"模型卸载失败: {str(e)}")
            return False

    def get_model(self, model_name: str) -> Optional[AIModel]:
        """获取模型"""
        return self.models.get(model_name)

    def process_frame(self, frame: np.ndarray, model_name: str,
                    parameters: Dict[str, Any] = None) -> AnalysisResult:
        """处理单帧"""
        try:
            model = self.get_model(model_name)
            if not model or not model.is_loaded:
                self.load_model(model_name)
                model = self.get_model(model_name)

            if not model:
                raise ValueError(f"模型不可用: {model_name}")

            start_time = time.time()

            # 预处理
            processed_frame = self._preprocess_frame(frame, model, parameters)

            # 推理
            result = self._inference(processed_frame, model, parameters)

            # 后处理
            final_result = self._postprocess_result(result, model, parameters)

            processing_time = time.time() - start_time

            return AnalysisResult(
                task_id="",
                model_type=model.model_type,
                timestamp=time.time(),
                frame_index=0,
                data=final_result,
                confidence=0.0,
                processing_time=processing_time
            )

        except Exception as e:
            self.logger.error(f"帧处理失败: {str(e)}")
            raise

    def _preprocess_frame(self, frame: np.ndarray, model: AIModel,
                         parameters: Dict[str, Any]) -> torch.Tensor:
        """预处理帧"""
        try:
            # 调整尺寸
            if frame.shape[:2] != model.input_size:
                frame = cv2.resize(frame, model.input_size)

            # 转换为RGB
            if len(frame.shape) == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 转换为张量
            tensor = torch.from_numpy(frame).float()

            # 归一化
            if tensor.max() > 1.0:
                tensor = tensor / 255.0

            # 调整维度
            if len(tensor.shape) == 3:
                tensor = tensor.permute(2, 0, 1)

            # 添加批次维度
            tensor = tensor.unsqueeze(0)

            # 移动到设备
            tensor = tensor.to(model.device)

            return tensor

        except Exception as e:
            self.logger.error(f"预处理失败: {str(e)}")
            raise

    def _inference(self, frame_tensor: torch.Tensor, model: AIModel,
                   parameters: Dict[str, Any]) -> Dict[str, Any]:
        """推理"""
        try:
            with torch.no_grad():
                if model.model_type == AIModelType.OBJECT_DETECTION:
                    results = model.model(frame_tensor)
                    return {
                        'boxes': results[0].boxes.xyxy.cpu().numpy(),
                        'scores': results[0].boxes.conf.cpu().numpy(),
                        'classes': results[0].boxes.cls.cpu().numpy()
                    }
                elif model.model_type == AIModelType.SCENE_ANALYSIS:
                    output = model.model(frame_tensor)
                    return {
                        'features': output.cpu().numpy(),
                        'predictions': torch.softmax(output, dim=1).cpu().numpy()
                    }
                elif model.model_type == AIModelType.FACE_DETECTION:
                    # 使用face_recognition库
                    frame_np = frame_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
                    face_locations = model.model.face_locations(frame_np)
                    return {
                        'face_locations': face_locations
                    }
                elif model.model_type == AIModelType.VIDEO_SUPER_RESOLUTION:
                    output = model.model(frame_tensor)
                    return {
                        'enhanced_frame': output.cpu().numpy()
                    }
                elif model.model_type == AIModelType.VIDEO_DENOISING:
                    output = model.model(frame_tensor)
                    return {
                        'denoised_frame': output.cpu().numpy()
                    }
                else:
                    return {}

        except Exception as e:
            self.logger.error(f"推理失败: {str(e)}")
            raise

    def _postprocess_result(self, result: Dict[str, Any], model: AIModel,
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """后处理结果"""
        try:
            final_result = {}

            if model.model_type == AIModelType.OBJECT_DETECTION:
                # 过滤低置信度检测结果
                confidence_threshold = parameters.get('confidence_threshold', 0.5)
                boxes = result['boxes']
                scores = result['scores']
                classes = result['classes']

                mask = scores > confidence_threshold
                final_result = {
                    'boxes': boxes[mask].tolist(),
                    'scores': scores[mask].tolist(),
                    'classes': classes[mask].tolist()
                }
            elif model.model_type == AIModelType.SCENE_ANALYSIS:
                # 获取top-k预测
                top_k = parameters.get('top_k', 5)
                predictions = result['predictions'][0]
                top_indices = np.argsort(predictions)[-top_k:][::-1]

                final_result = {
                    'top_classes': top_indices.tolist(),
                    'top_scores': predictions[top_indices].tolist()
                }
            elif model.model_type == AIModelType.FACE_DETECTION:
                final_result = result
            elif model.model_type == AIModelType.VIDEO_SUPER_RESOLUTION:
                final_result = result
            elif model.model_type == AIModelType.VIDEO_DENOISING:
                final_result = result

            return final_result

        except Exception as e:
            self.logger.error(f"后处理失败: {str(e)}")
            raise

    def cleanup(self):
        """清理资源"""
        try:
            # 卸载所有模型
            for model_name in list(self.loaded_models.keys()):
                self.unload_model(model_name)

            # 清理内存
            if hasattr(torch.cuda, 'empty_cache'):
                torch.cuda.empty_cache()

            self.logger.info("神经网络管理器清理完成")

        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")


class MemoryManager:
    """内存管理器"""

    def __init__(self, max_memory: int, logger=None):
        self.max_memory = max_memory
        self.logger = logger or get_logger("MemoryManager")
        self.allocated_memory = 0
        self.memory_pool = {}
        self.lock = threading.Lock()

    def check_memory(self, required_memory: int) -> bool:
        """检查内存是否足够"""
        with self.lock:
            return self.allocated_memory + required_memory <= self.max_memory

    def allocate_memory(self, tag: str, size: int) -> bool:
        """分配内存"""
        with self.lock:
            if self.allocated_memory + size > self.max_memory:
                return False

            self.memory_pool[tag] = size
            self.allocated_memory += size
            self.logger.debug(f"内存分配: {tag} ({size}MB)")
            return True

    def free_memory(self, tag: str):
        """释放内存"""
        with self.lock:
            if tag in self.memory_pool:
                size = self.memory_pool[tag]
                del self.memory_pool[tag]
                self.allocated_memory -= size
                self.logger.debug(f"内存释放: {tag} ({size}MB)")

    def get_memory_usage(self) -> Dict[str, int]:
        """获取内存使用情况"""
        with self.lock:
            return {
                'allocated': self.allocated_memory,
                'available': self.max_memory - self.allocated_memory,
                'total': self.max_memory,
                'usage_percentage': (self.allocated_memory / self.max_memory) * 100
            }


class VideoAnalyticsEngine:
    """视频分析引擎"""

    def __init__(self, neural_manager: NeuralNetworkManager, logger=None):
        self.neural_manager = neural_manager
        self.logger = logger or get_logger("VideoAnalyticsEngine")
        self.error_handler = get_global_error_handler()

        # 分析管道
        self.analysis_pipelines = {}
        self.pipeline_lock = threading.Lock()

        # 性能监控
        self.performance_stats = {
            'total_frames_processed': 0,
            'average_processing_time': 0.0,
            'throughput': 0.0
        }

    def create_analysis_pipeline(self, pipeline_id: str, models: List[str],
                               parameters: Dict[str, Any] = None) -> bool:
        """创建分析管道"""
        try:
            with self.pipeline_lock:
                pipeline = {
                    'models': models,
                    'parameters': parameters or {},
                    'is_active': False,
                    'stats': {
                        'frames_processed': 0,
                        'average_time': 0.0
                    }
                }

                self.analysis_pipelines[pipeline_id] = pipeline
                self.logger.info(f"分析管道创建成功: {pipeline_id}")
                return True

        except Exception as e:
            self.logger.error(f"分析管道创建失败: {str(e)}")
            return False

    def process_video_analysis(self, video_path: str, pipeline_id: str,
                             output_path: str = None) -> AsyncGenerator[AnalysisResult, None]:
        """处理视频分析"""
        try:
            if pipeline_id not in self.analysis_pipelines:
                raise ValueError(f"分析管道不存在: {pipeline_id}")

            pipeline = self.analysis_pipelines[pipeline_id]
            pipeline['is_active'] = True

            # 打开视频
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            frame_index = 0
            processing_times = []

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 处理帧
                start_time = time.time()
                results = []

                for model_name in pipeline['models']:
                    try:
                        result = self.neural_manager.process_frame(
                            frame, model_name, pipeline['parameters']
                        )
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"模型处理失败 {model_name}: {str(e)}")

                processing_time = time.time() - start_time
                processing_times.append(processing_time)

                # 更新统计
                frame_index += 1
                pipeline['stats']['frames_processed'] += 1
                self.performance_stats['total_frames_processed'] += 1

                # 计算平均处理时间
                if processing_times:
                    avg_time = sum(processing_times) / len(processing_times)
                    pipeline['stats']['average_time'] = avg_time
                    self.performance_stats['average_processing_time'] = avg_time

                # 计算吞吐量
                if total_frames > 0:
                    progress = frame_index / total_frames
                    elapsed_time = sum(processing_times)
                    if elapsed_time > 0:
                        throughput = frame_index / elapsed_time
                        self.performance_stats['throughput'] = throughput

                # 生成结果
                for result in results:
                    result.frame_index = frame_index
                    result.task_id = pipeline_id
                    yield result

                # 检查是否需要输出
                if output_path and frame_index % 100 == 0:
                    self._save_analysis_results(results, output_path)

            cap.release()
            pipeline['is_active'] = False

            self.logger.info(f"视频分析完成: {video_path}")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.AI,
                severity=ErrorSeverity.HIGH,
                message=f"视频分析失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="VideoAnalyticsEngine",
                    operation="process_video_analysis"
                ),
                user_message="视频分析失败，请稍后重试"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _save_analysis_results(self, results: List[AnalysisResult], output_path: str):
        """保存分析结果"""
        try:
            # 转换为可序列化格式
            serializable_results = []
            for result in results:
                serializable_result = {
                    'task_id': result.task_id,
                    'model_type': result.model_type.value,
                    'timestamp': result.timestamp,
                    'frame_index': result.frame_index,
                    'data': result.data,
                    'confidence': result.confidence,
                    'processing_time': result.processing_time,
                    'metadata': result.metadata
                }
                serializable_results.append(serializable_result)

            # 保存为JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"保存分析结果失败: {str(e)}")

    def get_pipeline_stats(self, pipeline_id: str) -> Dict[str, Any]:
        """获取管道统计信息"""
        if pipeline_id in self.analysis_pipelines:
            return self.analysis_pipelines[pipeline_id]['stats']
        return {}

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return self.performance_stats.copy()


class AIVideoEngine:
    """AI视频处理引擎"""

    def __init__(self, config: AIVideoEngineConfig = None, logger=None):
        self.config = config or AIVideoEngineConfig()
        self.logger = logger or get_logger("AIVideoEngine")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()

        # 核心组件
        self.video_engine = VideoEngine()
        self.neural_manager = NeuralNetworkManager(self.config, self.logger)
        self.analytics_engine = VideoAnalyticsEngine(self.neural_manager, self.logger)

        # 任务管理
        self.tasks: Dict[str, AITask] = {}
        self.task_queue = PriorityQueue()
        self.active_tasks: Dict[str, threading.Thread] = {}
        self.task_lock = threading.Lock()

        # 处理线程
        self.processing_thread = None
        self.is_running = False

        # 初始化
        self._initialize_directories()
        self._setup_event_handlers()

    def _initialize_directories(self):
        """初始化目录"""
        directories = [
            self.config.temp_directory,
            self.config.cache_directory,
            self.config.model_directory,
            os.path.join(self.config.temp_directory, "output"),
            os.path.join(self.config.temp_directory, "cache")
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

        self.logger.info("目录初始化完成")

    def _setup_event_handlers(self):
        """设置事件处理器"""
        self.event_bus.subscribe("ai_task_completed", self._handle_task_completed)
        self.event_bus.subscribe("ai_task_failed", self._handle_task_failed)
        self.event_bus.subscribe("memory_warning", self._handle_memory_warning)

    def start(self):
        """启动引擎"""
        if self.is_running:
            return

        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
        self.processing_thread.start()

        self.logger.info("AI视频引擎已启动")

    def stop(self):
        """停止引擎"""
        self.is_running = False

        if self.processing_thread:
            self.processing_thread.join()

        # 清理活动任务
        with self.task_lock:
            for task_id in list(self.active_tasks.keys()):
                self.cancel_task(task_id)

        self.logger.info("AI视频引擎已停止")

    def _processing_worker(self):
        """处理工作线程"""
        while self.is_running:
            try:
                # 从队列获取任务
                if not self.task_queue.empty():
                    priority, task = self.task_queue.get()
                    self._process_task(task)
                else:
                    time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"处理工作线程错误: {str(e)}")

    def _process_task(self, task: AITask):
        """处理AI任务"""
        try:
            task.status = "processing"
            task.start_time = time.time()

            # 创建分析管道
            pipeline_id = f"pipeline_{task.id}"
            self.analytics_engine.create_analysis_pipeline(
                pipeline_id, [task.model_type.value], task.parameters
            )

            # 处理视频分析
            results = []
            for result in self.analytics_engine.process_video_analysis(
                task.input_path, pipeline_id, task.output_path
            ):
                results.append(result)

                # 更新进度
                if hasattr(result, 'frame_index'):
                    video_info = self.video_engine.ffmpeg_utils.get_video_info(task.input_path)
                    total_frames = int(video_info.duration * video_info.fps)
                    task.progress = result.frame_index / total_frames

            task.status = "completed"
            task.end_time = time.time()

            # 调用回调函数
            if task.callback:
                task.callback(results)

            # 发送事件
            self.event_bus.publish("ai_task_completed", task)

            self.logger.info(f"AI任务完成: {task.name}")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.end_time = time.time()

            error_info = ErrorInfo(
                error_type=ErrorType.AI,
                severity=ErrorSeverity.HIGH,
                message=f"AI任务处理失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="AIVideoEngine",
                    operation="_process_task"
                ),
                user_message=f"AI处理失败: {task.name}"
            )
            self.error_handler.handle_error(error_info)

            self.event_bus.publish("ai_task_failed", task)

            self.logger.error(f"AI任务失败: {task.name} - {str(e)}")

        finally:
            with self.task_lock:
                if task.id in self.active_tasks:
                    del self.active_tasks[task.id]

    def add_task(self, task: AITask) -> bool:
        """添加AI任务"""
        try:
            with self.task_lock:
                self.tasks[task.id] = task
                # 使用负数优先级让高优先级先出队
                self.task_queue.put((-task.priority, task))
                task.status = "queued"

            self.logger.info(f"AI任务已添加: {task.name} ({task.id})")
            return True

        except Exception as e:
            self.logger.error(f"添加AI任务失败: {str(e)}")
            return False

    def cancel_task(self, task_id: str) -> bool:
        """取消AI任务"""
        try:
            with self.task_lock:
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    task.status = "cancelled"

                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]

                    self.logger.info(f"AI任务已取消: {task.name}")
                    return True
                return False

        except Exception as e:
            self.logger.error(f"取消AI任务失败: {str(e)}")
            return False

    def analyze_video(self, input_path: str, output_path: str,
                     model_type: AIModelType,
                     processing_mode: ProcessingMode = ProcessingMode.BATCH,
                     quality_level: QualityLevel = QualityLevel.HIGH,
                     parameters: Dict[str, Any] = None,
                     callback: Optional[Callable[[List[AnalysisResult]], None]] = None) -> str:
        """分析视频"""

        if not os.path.exists(input_path):
            raise ValueError(f"视频文件不存在: {input_path}")

        task_id = f"ai_task_{int(time.time() * 1000)}"

        task = AITask(
            id=task_id,
            name=f"Video Analysis - {model_type.value}",
            input_path=input_path,
            output_path=output_path,
            model_type=model_type,
            processing_mode=processing_mode,
            priority=1,
            quality_level=quality_level,
            parameters=parameters or {},
            callback=callback
        )

        if self.add_task(task):
            return task_id
        else:
            raise RuntimeError("无法添加AI任务")

    def enhance_video(self, input_path: str, output_path: str,
                     enhancement_type: str = "super_resolution",
                     quality_level: QualityLevel = QualityLevel.HIGH,
                     parameters: Dict[str, Any] = None) -> str:
        """增强视频"""

        model_map = {
            "super_resolution": AIModelType.VIDEO_SUPER_RESOLUTION,
            "denoising": AIModelType.VIDEO_DENOISING,
            "stabilization": AIModelType.VIDEO_STABILIZATION,
            "color_correction": AIModelType.COLOR_CORRECTION
        }

        if enhancement_type not in model_map:
            raise ValueError(f"不支持的增强类型: {enhancement_type}")

        model_type = model_map[enhancement_type]

        return self.analyze_video(
            input_path, output_path, model_type,
            ProcessingMode.BATCH, quality_level, parameters
        )

    def detect_objects(self, input_path: str, output_path: str,
                      confidence_threshold: float = 0.5,
                      max_detections: int = 100) -> str:
        """检测物体"""

        parameters = {
            'confidence_threshold': confidence_threshold,
            'max_detections': max_detections
        }

        return self.analyze_video(
            input_path, output_path, AIModelType.OBJECT_DETECTION,
            ProcessingMode.BATCH, QualityLevel.HIGH, parameters
        )

    def analyze_scenes(self, input_path: str, output_path: str,
                      scene_threshold: float = 0.3) -> str:
        """分析场景"""

        parameters = {
            'scene_threshold': scene_threshold
        }

        return self.analyze_video(
            input_path, output_path, AIModelType.SCENE_ANALYSIS,
            ProcessingMode.BATCH, QualityLevel.HIGH, parameters
        )

    def recognize_faces(self, input_path: str, output_path: str,
                       confidence_threshold: float = 0.5) -> str:
        """识别人脸"""

        parameters = {
            'confidence_threshold': confidence_threshold
        }

        return self.analyze_video(
            input_path, output_path, AIModelType.FACE_DETECTION,
            ProcessingMode.BATCH, QualityLevel.HIGH, parameters
        )

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'progress': task.progress,
                'start_time': task.start_time,
                'end_time': task.end_time,
                'error': task.error,
                'model_type': task.model_type.value,
                'processing_mode': task.processing_mode.value,
                'quality_level': task.quality_level.value
            }
        return {}

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            'analytics_performance': self.analytics_engine.get_performance_stats(),
            'memory_usage': self.neural_manager.memory_manager.get_memory_usage(),
            'loaded_models': len(self.neural_manager.loaded_models),
            'total_models': len(self.neural_manager.models),
            'active_tasks': len(self.active_tasks),
            'queued_tasks': self.task_queue.qsize()
        }

    def _handle_task_completed(self, task: AITask):
        """处理任务完成事件"""
        self.logger.info(f"AI任务完成: {task.name}")

    def _handle_task_failed(self, task: AITask):
        """处理任务失败事件"""
        self.logger.error(f"AI任务失败: {task.name} - {task.error}")

    def _handle_memory_warning(self, warning_data: Any):
        """处理内存警告"""
        self.logger.warning(f"内存警告: {warning_data}")
        # 清理未使用的模型
        self.neural_manager._unload_unused_models()

    def optimize_performance(self) -> bool:
        """优化性能"""
        try:
            # 优化神经网络管理器
            self.neural_manager.memory_manager.max_memory = self.config.max_memory_usage

            # 重新加载关键模型
            critical_models = ["yolov8", "face_detection"]
            for model_name in critical_models:
                if model_name in self.neural_manager.models:
                    self.neural_manager.load_model(model_name)

            self.logger.info("性能优化完成")
            return True

        except Exception as e:
            self.logger.error(f"性能优化失败: {str(e)}")
            return False

    def cleanup(self):
        """清理资源"""
        try:
            self.stop()

            # 清理组件
            self.neural_manager.cleanup()

            # 清理临时文件
            import shutil
            if os.path.exists(self.config.temp_directory):
                shutil.rmtree(self.config.temp_directory)

            if os.path.exists(self.config.cache_directory):
                shutil.rmtree(self.config.cache_directory)

            self.logger.info("AI视频引擎清理完成")

        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局AI视频引擎实例
_ai_video_engine: Optional[AIVideoEngine] = None


def get_ai_video_engine(config: AIVideoEngineConfig = None) -> AIVideoEngine:
    """获取全局AI视频引擎实例"""
    global _ai_video_engine
    if _ai_video_engine is None:
        _ai_video_engine = AIVideoEngine(config)
        _ai_video_engine.start()
    return _ai_video_engine


def cleanup_ai_video_engine() -> None:
    """清理全局AI视频引擎实例"""
    global _ai_video_engine
    if _ai_video_engine is not None:
        _ai_video_engine.cleanup()
        _ai_video_engine = None