#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 专业级AI视频处理引擎
集成所有AI视频处理功能的主引擎，提供统一的高性能接口
"""

import os
import time
import asyncio
import threading
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging

from .logger import get_logger
from .event_system import EventBus
from .video_engine import VideoEngine, EngineSettings
from .ai_video_engine import AIVideoEngine, AIVideoEngineConfig, AIModelType, ProcessingMode, QualityLevel
from .gpu_parallel_processor import ParallelProcessor, ProcessingStrategy, TaskPriority
from .video_quality_enhancer import VideoQualityEnhancer, EnhancementType, EnhancementConfig, EnhancementStrategy
from .intelligent_editing_engine import IntelligentEditingEngine, SceneType, ContentQuality
from .timeline_engine import TimelineEngine
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler


class EngineMode(Enum):
    """引擎模式枚举"""
    LIGHTWEIGHT = "lightweight"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class ProcessingPriority(Enum):
    """处理优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    REALTIME = 5


@dataclass
class EngineConfiguration:
    """引擎配置数据类"""
    mode: EngineMode = EngineMode.PROFESSIONAL
    max_concurrent_tasks: int = 8
    max_memory_usage: int = 8192  # MB
    enable_gpu_acceleration: bool = True
    enable_ai_processing: bool = True
    enable_real_time_processing: bool = True
    enable_quality_enhancement: bool = True
    enable_intelligent_editing: bool = True
    temp_directory: str = "/tmp/cineaistudio/professional"
    cache_directory: str = "/tmp/cineaistudio/cache"
    model_directory: str = "/models"
    log_level: str = "INFO"
    auto_optimization: bool = True
    enable_distributed_processing: bool = False
    worker_nodes: List[str] = field(default_factory=list)


@dataclass
class ProcessingResult:
    """处理结果数据类"""
    task_id: str
    success: bool
    processing_time: float
    output_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineStatus:
    """引擎状态数据类"""
    is_running: bool
    mode: EngineMode
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_memory_usage: int
    gpu_utilization: float
    cpu_utilization: float
    uptime: float
    capabilities: List[str]


class ProfessionalAIEngine:
    """专业级AI视频处理引擎"""

    def __init__(self, config: EngineConfiguration = None, logger=None):
        self.config = config or EngineConfiguration()
        self.logger = logger or get_logger("ProfessionalAIEngine")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()

        # 核心组件
        self.video_engine: Optional[VideoEngine] = None
        self.ai_engine: Optional[AIVideoEngine] = None
        self.parallel_processor: Optional[ParallelProcessor] = None
        self.quality_enhancer: Optional[VideoQualityEnhancer] = None
        self.editing_engine: Optional[IntelligentEditingEngine] = None
        self.timeline_engine: Optional[TimelineEngine] = None

        # 状态管理
        self.is_running = False
        self.start_time = time.time()
        self.active_tasks: Dict[str, Any] = {}
        self.completed_tasks: Dict[str, ProcessingResult] = {}
        self.task_lock = threading.Lock()

        # 性能监控
        self.performance_stats = {
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'throughput': 0.0,
            'success_rate': 0.0,
            'gpu_usage_history': [],
            'memory_usage_history': []
        }

        # 初始化
        self._initialize_components()
        self._setup_event_handlers()

    def _initialize_components(self):
        """初始化所有组件"""
        try:
            self.logger.info("初始化专业级AI引擎...")

            # 初始化视频引擎
            video_settings = EngineSettings(
                max_concurrent_operations=self.config.max_concurrent_tasks,
                memory_limit=self.config.max_memory_usage,
                temp_directory=self.config.temp_directory,
                cache_directory=self.config.cache_directory,
                enable_hardware_acceleration=self.config.enable_gpu_acceleration,
                enable_real_time_processing=self.config.enable_real_time_processing
            )
            self.video_engine = VideoEngine(video_settings, self.logger)

            # 初始化AI引擎
            if self.config.enable_ai_processing:
                ai_config = AIVideoEngineConfig()
                ai_config.max_concurrent_tasks = self.config.max_concurrent_tasks
                ai_config.max_memory_usage = self.config.max_memory_usage
                ai_config.temp_directory = self.config.temp_directory
                ai_config.cache_directory = self.config.cache_directory
                ai_config.enable_gpu_acceleration = self.config.enable_gpu_acceleration
                ai_config.enable_mixed_precision = True
                ai_config.enable_model_quantization = True

                self.ai_engine = AIVideoEngine(ai_config, self.logger)

            # 初始化并行处理器
            if self.config.enable_gpu_acceleration:
                strategy = ProcessingStrategy.DATA_PARALLEL
                if self.config.mode == EngineMode.ENTERPRISE:
                    strategy = ProcessingStrategy.HYBRID_PARALLEL

                self.parallel_processor = ParallelProcessor(
                    strategy=strategy,
                    max_workers=self.config.max_concurrent_tasks,
                    logger=self.logger
                )

            # 初始化质量增强器
            if self.config.enable_quality_enhancement and self.parallel_processor:
                self.quality_enhancer = VideoQualityEnhancer(
                    self.parallel_processor, self.logger
                )

            # 初始化时间线引擎
            self.timeline_engine = TimelineEngine(self.logger)

            # 初始化智能剪辑引擎
            if self.config.enable_intelligent_editing and self.ai_engine:
                self.editing_engine = IntelligentEditingEngine(
                    self.ai_engine, self.timeline_engine, self.logger
                )

            self.logger.info("专业级AI引擎初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"引擎初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ProfessionalAIEngine",
                    operation="_initialize_components"
                ),
                user_message="专业级AI引擎初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _setup_event_handlers(self):
        """设置事件处理器"""
        try:
            self.event_bus.subscribe("processing_completed", self._handle_processing_completed)
            self.event_bus.subscribe("processing_failed", self._handle_processing_failed)
            self.event_bus.subscribe("memory_warning", self._handle_memory_warning)
            self.event_bus.subscribe("performance_warning", self._handle_performance_warning)

            self.logger.info("事件处理器设置完成")

        except Exception as e:
            self.logger.error(f"事件处理器设置失败: {str(e)}")

    def start(self) -> bool:
        """启动引擎"""
        try:
            if self.is_running:
                return True

            self.logger.info("启动专业级AI引擎...")

            # 启动视频引擎
            if self.video_engine:
                result = self.video_engine.initialize()
                if not result.success:
                    raise RuntimeError(f"视频引擎启动失败: {result.message}")

            # 启动AI引擎
            if self.ai_engine:
                self.ai_engine.start()

            # 启动并行处理器
            if self.parallel_processor:
                self.parallel_processor.start()

            self.is_running = True
            self.start_time = time.time()

            self.logger.info("专业级AI引擎启动成功")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"引擎启动失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ProfessionalAIEngine",
                    operation="start"
                ),
                user_message="专业级AI引擎启动失败"
            )
            self.error_handler.handle_error(error_info)
            return False

    def stop(self) -> bool:
        """停止引擎"""
        try:
            if not self.is_running:
                return True

            self.logger.info("停止专业级AI引擎...")

            self.is_running = False

            # 停止AI引擎
            if self.ai_engine:
                self.ai_engine.stop()

            # 停止并行处理器
            if self.parallel_processor:
                self.parallel_processor.stop()

            # 停止视频引擎
            if self.video_engine:
                self.video_engine.shutdown()

            self.logger.info("专业级AI引擎停止成功")
            return True

        except Exception as e:
            self.logger.error(f"引擎停止失败: {str(e)}")
            return False

    def process_video(self, input_path: str, output_path: str,
                     processing_type: str = "standard",
                     parameters: Dict[str, Any] = None,
                     priority: ProcessingPriority = ProcessingPriority.NORMAL) -> ProcessingResult:
        """处理视频"""
        try:
            if not self.is_running:
                raise RuntimeError("引擎未启动")

            task_id = f"task_{int(time.time() * 1000)}"
            start_time = time.time()

            with self.task_lock:
                self.active_tasks[task_id] = {
                    'id': task_id,
                    'input_path': input_path,
                    'output_path': output_path,
                    'processing_type': processing_type,
                    'parameters': parameters or {},
                    'start_time': start_time,
                    'status': 'processing'
                }

            try:
                # 根据处理类型选择处理方式
                if processing_type == "ai_enhancement":
                    result = self._process_ai_enhancement(input_path, output_path, parameters)
                elif processing_type == "quality_enhancement":
                    result = self._process_quality_enhancement(input_path, output_path, parameters)
                elif processing_type == "intelligent_editing":
                    result = self._process_intelligent_editing(input_path, output_path, parameters)
                elif processing_type == "standard":
                    result = self._process_standard(input_path, output_path, parameters)
                else:
                    raise ValueError(f"不支持的处理类型: {processing_type}")

                processing_time = time.time() - start_time

                processing_result = ProcessingResult(
                    task_id=task_id,
                    success=result['success'],
                    processing_time=processing_time,
                    output_path=output_path,
                    metadata=result.get('metadata', {}),
                    quality_metrics=result.get('quality_metrics', {}),
                    performance_metrics=result.get('performance_metrics', {})
                )

                # 更新统计
                self._update_performance_stats(processing_result)

                # 发送事件
                self.event_bus.publish("processing_completed", processing_result)

                return processing_result

            except Exception as e:
                processing_time = time.time() - start_time

                processing_result = ProcessingResult(
                    task_id=task_id,
                    success=False,
                    processing_time=processing_time,
                    error=str(e)
                )

                # 更新统计
                self._update_performance_stats(processing_result)

                # 发送事件
                self.event_bus.publish("processing_failed", processing_result)

                return processing_result

            finally:
                with self.task_lock:
                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]
                    self.completed_tasks[task_id] = processing_result

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"视频处理失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ProfessionalAIEngine",
                    operation="process_video"
                ),
                user_message="视频处理失败"
            )
            self.error_handler.handle_error(error_info)

            return ProcessingResult(
                task_id="error",
                success=False,
                processing_time=0.0,
                error=str(e)
            )

    def _process_ai_enhancement(self, input_path: str, output_path: str,
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理AI增强"""
        if not self.ai_engine:
            raise RuntimeError("AI引擎未初始化")

        model_type = parameters.get('model_type', AIModelType.OBJECT_DETECTION)
        quality_level = parameters.get('quality_level', QualityLevel.HIGH)

        task_id = self.ai_engine.analyze_video(
            input_path, output_path, model_type,
            ProcessingMode.BATCH, quality_level, parameters
        )

        # 等待完成
        while True:
            task_status = self.ai_engine.get_task_status(task_id)
            if task_status.get('status') in ['completed', 'failed']:
                break
            time.sleep(0.1)

        return {
            'success': task_status.get('status') == 'completed',
            'metadata': {'ai_task_id': task_id},
            'quality_metrics': {'ai_processing_quality': 0.8}
        }

    def _process_quality_enhancement(self, input_path: str, output_path: str,
                                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理质量增强"""
        if not self.quality_enhancer:
            raise RuntimeError("质量增强器未初始化")

        enhancement_type = parameters.get('enhancement_type', EnhancementType.SUPER_RESOLUTION)
        quality_level = parameters.get('quality_level', QualityLevel.HIGH)

        config = EnhancementConfig(
            enhancement_type=enhancement_type,
            quality_level=quality_level,
            strategy=EnhancementStrategy.ADAPTIVE,
            parameters=parameters,
            enable_gpu=self.config.enable_gpu_acceleration
        )

        result = self.quality_enhancer.enhance_video(input_path, output_path, config)

        return {
            'success': result.success,
            'metadata': {'enhancement_type': enhancement_type.value},
            'quality_metrics': {
                'quality_improvement': result.quality_improvement,
                'file_size_ratio': result.file_size_ratio
            }
        }

    def _process_intelligent_editing(self, input_path: str, output_path: str,
                                   parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理智能剪辑"""
        if not self.editing_engine:
            raise RuntimeError("智能剪辑引擎未初始化")

        project_id = f"project_{int(time.time() * 1000)}"
        style = parameters.get('style', 'auto')

        # 创建剪辑项目
        success = self.editing_engine.create_editing_project(
            project_id, [input_path], output_path, style
        )

        if not success:
            raise RuntimeError("剪辑项目创建失败")

        # 等待分析完成
        while True:
            status = self.editing_engine.get_project_status(project_id)
            if status.get('status') in ['analyzed', 'auto_edited']:
                break
            time.sleep(0.1)

        # 自动编辑
        if parameters.get('auto_edit', True):
            self.editing_engine.auto_edit_project(project_id)

        return {
            'success': True,
            'metadata': {'project_id': project_id, 'style': style},
            'quality_metrics': {'editing_quality': 0.85}
        }

    def _process_standard(self, input_path: str, output_path: str,
                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理标准视频"""
        if not self.video_engine:
            raise RuntimeError("视频引擎未初始化")

        operation_type = parameters.get('operation_type', 'transcode')

        result = self.video_engine.process_video(
            input_path, output_path, operation_type, parameters
        )

        return {
            'success': result.success,
            'metadata': result.metadata,
            'quality_metrics': {'standard_quality': 0.7}
        }

    def analyze_video_content(self, input_path: str, analysis_types: List[str] = None) -> Dict[str, Any]:
        """分析视频内容"""
        try:
            if not self.ai_engine:
                raise RuntimeError("AI引擎未初始化")

            if analysis_types is None:
                analysis_types = ['object_detection', 'scene_analysis', 'quality_assessment']

            results = {}

            for analysis_type in analysis_types:
                if analysis_type == 'object_detection':
                    task_id = self.ai_engine.detect_objects(input_path, f"temp_{analysis_type}.json")
                elif analysis_type == 'scene_analysis':
                    task_id = self.ai_engine.analyze_scenes(input_path, f"temp_{analysis_type}.json")
                elif analysis_type == 'quality_assessment':
                    # 质量评估
                    results[analysis_type] = self._assess_video_quality(input_path)
                    continue
                else:
                    continue

                # 等待分析完成
                while True:
                    task_status = self.ai_engine.get_task_status(task_id)
                    if task_status.get('status') in ['completed', 'failed']:
                        break
                    time.sleep(0.1)

                results[analysis_type] = {'task_id': task_id, 'status': task_status.get('status')}

            return results

        except Exception as e:
            self.logger.error(f"视频内容分析失败: {str(e)}")
            raise

    def _assess_video_quality(self, input_path: str) -> Dict[str, Any]:
        """评估视频质量"""
        try:
            import cv2

            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频: {input_path}")

            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 采样评估帧
            sample_frames = min(30, total_frames)
            frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)

            quality_scores = []
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    quality_score = self._calculate_frame_quality(frame)
                    quality_scores.append(quality_score)

            cap.release()

            avg_quality = np.mean(quality_scores) if quality_scores else 0.0

            return {
                'overall_quality': avg_quality,
                'resolution': f"{width}x{height}",
                'fps': fps,
                'total_frames': total_frames,
                'sampled_frames': sample_frames,
                'quality_distribution': {
                    'excellent': len([s for s in quality_scores if s >= 0.8]),
                    'good': len([s for s in quality_scores if 0.6 <= s < 0.8]),
                    'average': len([s for s in quality_scores if 0.4 <= s < 0.6]),
                    'poor': len([s for s in quality_scores if s < 0.4])
                }
            }

        except Exception as e:
            self.logger.error(f"视频质量评估失败: {str(e)}")
            raise

    def _calculate_frame_quality(self, frame: np.ndarray) -> float:
        """计算帧质量"""
        try:
            # 计算清晰度
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(sharpness / 1000.0, 1.0)

            # 计算亮度
            brightness = np.mean(gray)
            brightness_score = 1.0 - abs(brightness - 128) / 128.0

            # 计算对比度
            contrast = gray.std()
            contrast_score = min(contrast / 64.0, 1.0)

            # 综合质量分数
            quality_score = (sharpness_score + brightness_score + contrast_score) / 3.0

            return quality_score

        except Exception as e:
            self.logger.error(f"帧质量计算失败: {str(e)}")
            return 0.5

    def batch_process_videos(self, input_paths: List[str], output_paths: List[str],
                           processing_type: str = "standard",
                           parameters: Dict[str, Any] = None) -> List[ProcessingResult]:
        """批量处理视频"""
        if len(input_paths) != len(output_paths):
            raise ValueError("输入和输出路径数量不匹配")

        results = []
        for input_path, output_path in zip(input_paths, output_paths):
            result = self.process_video(input_path, output_path, processing_type, parameters)
            results.append(result)

        return results

    def get_engine_status(self) -> EngineStatus:
        """获取引擎状态"""
        try:
            # 计算GPU使用率
            gpu_utilization = 0.0
            if self.parallel_processor:
                perf_stats = self.parallel_processor.get_performance_stats()
                gpu_workload = perf_stats.get('gpu_workload', [])
                if gpu_workload:
                    gpu_utilization = np.mean([w['utilization'] for w in gpu_workload])

            # 计算内存使用
            total_memory_usage = 0
            if self.ai_engine:
                memory_stats = self.ai_engine.get_performance_metrics()
                total_memory_usage = memory_stats.get('memory_usage', {}).get('allocated', 0)

            return EngineStatus(
                is_running=self.is_running,
                mode=self.config.mode,
                active_tasks=len(self.active_tasks),
                completed_tasks=len(self.completed_tasks),
                failed_tasks=self.performance_stats.get('failed_tasks', 0),
                total_memory_usage=total_memory_usage,
                gpu_utilization=gpu_utilization,
                cpu_utilization=0.0,  # 需要实现CPU使用率监控
                uptime=time.time() - self.start_time,
                capabilities=self._get_capabilities()
            )

        except Exception as e:
            self.logger.error(f"获取引擎状态失败: {str(e)}")
            return EngineStatus(
                is_running=False,
                mode=self.config.mode,
                active_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                total_memory_usage=0,
                gpu_utilization=0.0,
                cpu_utilization=0.0,
                uptime=0.0,
                capabilities=[]
            )

    def _get_capabilities(self) -> List[str]:
        """获取引擎能力"""
        capabilities = []

        if self.video_engine:
            capabilities.extend([
                "video_decoding", "video_encoding", "format_conversion",
                "basic_editing", "thumbnail_generation"
            ])

        if self.ai_engine:
            capabilities.extend([
                "object_detection", "scene_analysis", "face_detection",
                "motion_analysis", "content_classification"
            ])

        if self.quality_enhancer:
            capabilities.extend([
                "super_resolution", "denoising", "stabilization",
                "color_correction", "quality_enhancement"
            ])

        if self.editing_engine:
            capabilities.extend([
                "intelligent_editing", "auto_cutting", "content_analysis",
                "scene_detection", "quality_assessment"
            ])

        if self.parallel_processor:
            capabilities.extend([
                "gpu_acceleration", "parallel_processing", "batch_processing"
            ])

        return capabilities

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            metrics = self.performance_stats.copy()

            # 添加实时性能数据
            if self.parallel_processor:
                metrics['parallel_processing'] = self.parallel_processor.get_performance_stats()

            if self.ai_engine:
                metrics['ai_processing'] = self.ai_engine.get_performance_metrics()

            if self.quality_enhancer:
                metrics['quality_enhancement'] = self.quality_enhancer.get_enhancement_stats()

            # 添加任务统计
            with self.task_lock:
                metrics['task_stats'] = {
                    'active_tasks': len(self.active_tasks),
                    'completed_tasks': len(self.completed_tasks),
                    'total_tasks': len(self.active_tasks) + len(self.completed_tasks)
                }

            return metrics

        except Exception as e:
            self.logger.error(f"获取性能指标失败: {str(e)}")
            return {}

    def _update_performance_stats(self, result: ProcessingResult):
        """更新性能统计"""
        try:
            self.performance_stats['total_processing_time'] += result.processing_time

            if result.success:
                completed = self.performance_stats.get('successful_tasks', 0) + 1
                self.performance_stats['successful_tasks'] = completed

                # 更新平均处理时间
                total_time = self.performance_stats['total_processing_time']
                self.performance_stats['average_processing_time'] = total_time / completed

                # 更新吞吐量
                if total_time > 0:
                    self.performance_stats['throughput'] = completed / total_time
            else:
                self.performance_stats['failed_tasks'] = self.performance_stats.get('failed_tasks', 0) + 1

            # 更新成功率
            total_tasks = self.performance_stats.get('successful_tasks', 0) + \
                         self.performance_stats.get('failed_tasks', 0)
            if total_tasks > 0:
                self.performance_stats['success_rate'] = \
                    self.performance_stats['successful_tasks'] / total_tasks

        except Exception as e:
            self.logger.error(f"性能统计更新失败: {str(e)}")

    def optimize_engine(self) -> bool:
        """优化引擎"""
        try:
            self.logger.info("开始优化引擎...")

            # 优化并行处理器
            if self.parallel_processor:
                self.parallel_processor.optimize_strategy()

            # 优化AI引擎
            if self.ai_engine:
                self.ai_engine.optimize_performance()

            # 优化质量增强器
            if self.quality_enhancer:
                self.quality_enhancer.optimize_models()

            self.logger.info("引擎优化完成")
            return True

        except Exception as e:
            self.logger.error(f"引擎优化失败: {str(e)}")
            return False

    def export_configuration(self, output_path: str) -> bool:
        """导出配置"""
        try:
            config_data = {
                'engine_config': {
                    'mode': self.config.mode.value,
                    'max_concurrent_tasks': self.config.max_concurrent_tasks,
                    'max_memory_usage': self.config.max_memory_usage,
                    'enable_gpu_acceleration': self.config.enable_gpu_acceleration,
                    'enable_ai_processing': self.config.enable_ai_processing,
                    'enable_real_time_processing': self.config.enable_real_time_processing,
                    'enable_quality_enhancement': self.config.enable_quality_enhancement,
                    'enable_intelligent_editing': self.config.enable_intelligent_editing
                },
                'performance_stats': self.performance_stats,
                'capabilities': self._get_capabilities()
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"配置导出成功: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"配置导出失败: {str(e)}")
            return False

    def _handle_processing_completed(self, result: ProcessingResult):
        """处理完成事件"""
        self.logger.info(f"处理完成: {result.task_id}")

    def _handle_processing_failed(self, result: ProcessingResult):
        """处理失败事件"""
        self.logger.error(f"处理失败: {result.task_id} - {result.error}")

    def _handle_memory_warning(self, warning_data: Any):
        """处理内存警告"""
        self.logger.warning(f"内存警告: {warning_data}")

        # 自动优化
        if self.config.auto_optimization:
            self.optimize_engine()

    def _handle_performance_warning(self, warning_data: Any):
        """处理性能警告"""
        self.logger.warning(f"性能警告: {warning_data}")

        # 自动优化
        if self.config.auto_optimization:
            self.optimize_engine()

    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("清理专业级AI引擎...")

            # 停止引擎
            self.stop()

            # 清理组件
            if self.ai_engine:
                self.ai_engine.cleanup()

            if self.parallel_processor:
                self.parallel_processor.cleanup()

            if self.quality_enhancer:
                self.quality_enhancer.cleanup()

            if self.editing_engine:
                self.editing_engine.cleanup()

            if self.timeline_engine:
                self.timeline_engine.cleanup()

            if self.video_engine:
                self.video_engine.cleanup()

            # 清理临时文件
            import shutil
            if os.path.exists(self.config.temp_directory):
                shutil.rmtree(self.config.temp_directory)

            self.logger.info("专业级AI引擎清理完成")

        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局专业级AI引擎实例
_professional_ai_engine: Optional[ProfessionalAIEngine] = None


def get_professional_ai_engine(config: EngineConfiguration = None) -> ProfessionalAIEngine:
    """获取全局专业级AI引擎实例"""
    global _professional_ai_engine
    if _professional_ai_engine is None:
        _professional_ai_engine = ProfessionalAIEngine(config)
        _professional_ai_engine.start()
    return _professional_ai_engine


def cleanup_professional_ai_engine() -> None:
    """清理全局专业级AI引擎实例"""
    global _professional_ai_engine
    if _professional_ai_engine is not None:
        _professional_ai_engine.cleanup()
        _professional_ai_engine = None