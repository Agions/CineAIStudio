#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio HDR Processing Engine
专业HDR处理引擎，提供HDR10、HDR10+、Dolby Vision和HLG支持
"""

import os
import numpy as np
import cv2
import math
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import logging

from .logger import get_logger
from .event_system import EventBus
from .hardware_acceleration import get_hardware_acceleration
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import get_ffmpeg_utils
from .color_grading_engine import ColorSpace, HDRStandard
from .color_science import ColorScienceEngine, TransferFunction, Illuminant


class HDRMetadataFormat(Enum):
    """HDR元数据格式枚举"""
    NONE = "none"
    STATIC_HDR10 = "static_hdr10"
    DYNAMIC_HDR10_PLUS = "dynamic_hdr10_plus"
    DOLBY_VISION = "dolby_vision"
    HLG = "hlg"


class ToneMappingMethod(Enum):
    """色调映射方法枚举"""
    REINHARD = "reinhard"
    FILMIC = "filmic"
    ACES = "aces"
    HABLE = "hable"
    DRAGO = "drago"
    DURAND = "durand"
    MANTIUK = "mantiuk"


@dataclass
class HDRMetadata:
    """HDR元数据数据类"""
    format: HDRMetadataFormat = HDRMetadataFormat.STATIC_HDR10
    max_luminance: float = 1000.0  # cd/m²
    min_luminance: float = 0.0001   # cd/m²
    max_fall: float = 0.0          # Frame Average Light Level
    max_cll: float = 0.0           # Content Light Level
    mastering_display_primaries: Tuple[float, float, float, float, float, float] = (0.640, 0.330, 0.300, 0.600, 0.150, 0.060)
    mastering_display_white_point: Tuple[float, float] = (0.3127, 0.3290)
    target_display_primaries: Optional[Tuple[float, float, float, float, float, float]] = None
    target_display_white_point: Optional[Tuple[float, float]] = None
    content_type: str = "movie"
    ootf: str = "reference"  # OOTF (Opto-Optical Transfer Function)
    transfer_function: str = "pq"  # pq, hlg, etc.

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'format': self.format.value,
            'max_luminance': self.max_luminance,
            'min_luminance': self.min_luminance,
            'max_fall': self.max_fall,
            'max_cll': self.max_cll,
            'mastering_display_primaries': self.mastering_display_primaries,
            'mastering_display_white_point': self.mastering_display_white_point,
            'target_display_primaries': self.target_display_primaries,
            'target_display_white_point': self.target_display_white_point,
            'content_type': self.content_type,
            'ootf': self.ootf,
            'transfer_function': self.transfer_function
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HDRMetadata':
        """从字典创建"""
        return cls(
            format=HDRMetadataFormat(data.get('format', 'static_hdr10')),
            max_luminance=data.get('max_luminance', 1000.0),
            min_luminance=data.get('min_luminance', 0.0001),
            max_fall=data.get('max_fall', 0.0),
            max_cll=data.get('max_cll', 0.0),
            mastering_display_primaries=data.get('mastering_display_primaries', (0.640, 0.330, 0.300, 0.600, 0.150, 0.060)),
            mastering_display_white_point=data.get('mastering_display_white_point', (0.3127, 0.3290)),
            target_display_primaries=data.get('target_display_primaries'),
            target_display_white_point=data.get('target_display_white_point'),
            content_type=data.get('content_type', 'movie'),
            ootf=data.get('ootf', 'reference'),
            transfer_function=data.get('transfer_function', 'pq')
        )


@dataclass
class ToneMappingSettings:
    """色调映射设置数据类"""
    method: ToneMappingMethod = ToneMappingMethod.REINHARD
    target_peak_luminance: float = 100.0  # cd/m²
    target_system_gamma: float = 2.4
    preserve_saturation: float = 1.0
    preserve_details: float = 1.0
    contrast_boost: float = 1.0
    shoulder_strength: float = 0.0
    linear_strength: float = 0.0
    linear_slope: float = 0.0
    toe_strength: float = 0.0
    toe_numerator: float = 0.0
    toe_denominator: float = 0.0
    exposure_bias: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'method': self.method.value,
            'target_peak_luminance': self.target_peak_luminance,
            'target_system_gamma': self.target_system_gamma,
            'preserve_saturation': self.preserve_saturation,
            'preserve_details': self.preserve_details,
            'contrast_boost': self.contrast_boost,
            'shoulder_strength': self.shoulder_strength,
            'linear_strength': self.linear_strength,
            'linear_slope': self.linear_slope,
            'toe_strength': self.toe_strength,
            'toe_numerator': self.toe_numerator,
            'toe_denominator': self.toe_denominator,
            'exposure_bias': self.exposure_bias
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToneMappingSettings':
        """从字典创建"""
        return cls(
            method=ToneMappingMethod(data.get('method', 'reinhard')),
            target_peak_luminance=data.get('target_peak_luminance', 100.0),
            target_system_gamma=data.get('target_system_gamma', 2.4),
            preserve_saturation=data.get('preserve_saturation', 1.0),
            preserve_details=data.get('preserve_details', 1.0),
            contrast_boost=data.get('contrast_boost', 1.0),
            shoulder_strength=data.get('shoulder_strength', 0.0),
            linear_strength=data.get('linear_strength', 0.0),
            linear_slope=data.get('linear_slope', 0.0),
            toe_strength=data.get('toe_strength', 0.0),
            toe_numerator=data.get('toe_numerator', 0.0),
            toe_denominator=data.get('toe_denominator', 0.0),
            exposure_bias=data.get('exposure_bias', 0.0)
        )


@dataclass
class HDRProcessingConfig:
    """HDR处理配置数据类"""
    enable_gpu_acceleration: bool = True
    enable_tone_mapping: bool = True
    enable_metadata_analysis: bool = True
    enable_color_space_conversion: bool = True
    enable_hdr10_plus_support: bool = True
    enable_dolby_vision_support: bool = True
    enable_hlg_support: bool = True
    enable_real_time_processing: bool = True
    cache_processed_frames: bool = True
    max_cache_size: int = 1024 * 1024 * 1024  # 1GB
    thread_pool_size: int = 4
    default_tone_mapping_settings: ToneMappingSettings = field(default_factory=ToneMappingSettings)
    default_hdr_metadata: HDRMetadata = field(default_factory=HDRMetadata)


class HDRProcessingEngine:
    """HDR处理引擎"""

    def __init__(self, config: Optional[HDRProcessingConfig] = None, logger=None):
        """初始化HDR处理引擎"""
        self.logger = logger or get_logger("HDRProcessingEngine")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.ffmpeg_utils = get_ffmpeg_utils()
        self.hardware_acceleration = get_hardware_acceleration()
        self.color_science = ColorScienceEngine()

        # 配置
        self.config = config or HDRProcessingConfig()
        self.is_initialized = False

        # HDR元数据
        self.current_hdr_metadata: Optional[HDRMetadata] = None
        self.metadata_cache: Dict[str, HDRMetadata] = {}

        # 色调映射设置
        self.tone_mapping_settings = self.config.default_tone_mapping_settings

        # 缓存系统
        self.frame_cache: Dict[str, np.ndarray] = {}
        self.metadata_cache: Dict[str, HDRMetadata] = {}

        # 处理线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.thread_pool_size)
        self.processing_queue = []
        self.processing_lock = threading.Lock()

        # 性能监控
        self.performance_metrics = {
            'frames_processed': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'cache_hit_rate': 0.0,
            'gpu_usage': 0.0,
            'memory_usage': 0.0
        }

        # 初始化
        self._initialize()

    def _initialize(self) -> None:
        """初始化引擎"""
        try:
            # 初始化硬件加速
            self._init_hardware_acceleration()

            # 启动处理线程
            self._start_processing_threads()

            # 加载预设
            self._load_presets()

            self.is_initialized = True
            self.logger.info("HDR处理引擎初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"HDR处理引擎初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="HDRProcessingEngine",
                    operation="initialize"
                ),
                user_message="HDR处理引擎初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _init_hardware_acceleration(self) -> None:
        """初始化硬件加速"""
        try:
            if self.config.enable_gpu_acceleration:
                # 检查CUDA是否可用
                if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                    self.logger.info("CUDA加速已启用")
                else:
                    self.logger.warning("CUDA不可用，将使用CPU处理")
                    self.config.enable_gpu_acceleration = False

        except Exception as e:
            self.logger.error(f"硬件加速初始化失败: {str(e)}")
            self.config.enable_gpu_acceleration = False

    def _start_processing_threads(self) -> None:
        """启动处理线程"""
        # 启动元数据分析线程
        self.metadata_thread = threading.Thread(target=self._metadata_worker, daemon=True)
        self.metadata_thread.start()

        self.logger.info("HDR处理线程已启动")

    def _load_presets(self) -> None:
        """加载预设"""
        try:
            # 创建预设配置
            self.presets = {
                'cinematic_hdr': ToneMappingSettings(
                    method=ToneMappingMethod.FILMIC,
                    target_peak_luminance=100.0,
                    preserve_saturation=1.2,
                    preserve_details=1.1,
                    contrast_boost=1.1
                ),
                'natural_hdr': ToneMappingSettings(
                    method=ToneMappingMethod.REINHARD,
                    target_peak_luminance=120.0,
                    preserve_saturation=0.9,
                    preserve_details=1.0
                ),
                'vibrant_hdr': ToneMappingSettings(
                    method=ToneMappingMethod.HABLE,
                    target_peak_luminance=150.0,
                    preserve_saturation=1.5,
                    preserve_details=0.9,
                    contrast_boost=1.2
                ),
                'dolby_vision': ToneMappingSettings(
                    method=ToneMappingMethod.ACES,
                    target_peak_luminance=100.0,
                    preserve_saturation=1.0,
                    preserve_details=1.0
                )
            }

            self.logger.info(f"预设加载完成，共{len(self.presets)}个预设")

        except Exception as e:
            self.logger.error(f"预设加载失败: {str(e)}")

    def analyze_hdr_metadata(self, video_path: str) -> Optional[HDRMetadata]:
        """分析HDR元数据"""
        try:
            cache_key = f"metadata_{video_path}"
            if cache_key in self.metadata_cache:
                return self.metadata_cache[cache_key]

            # 使用FFmpeg分析HDR元数据
            cmd = [
                self.ffmpeg_utils.ffprobe_path,
                "-v", "error",
                "-show_frames",
                "-select_streams", "v:0",
                "-show_entries", "frame=side_data_list,pix_fmt,color_space,color_range,color_transfer,color_primaries",
                "-of", "json",
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=30, text=True)

            if result.returncode != 0:
                self.logger.warning(f"无法分析HDR元数据: {result.stderr}")
                return None

            # 解析元数据
            data = json.loads(result.stdout)
            metadata = self._parse_hdr_metadata(data)

            # 缓存结果
            self.metadata_cache[cache_key] = metadata

            return metadata

        except Exception as e:
            self.logger.error(f"HDR元数据分析失败: {str(e)}")
            return None

    def _parse_hdr_metadata(self, data: Dict[str, Any]) -> HDRMetadata:
        """解析HDR元数据"""
        try:
            # 默认元数据
            metadata = HDRMetadata()

            # 解析帧数据
            frames = data.get('frames', [])
            if frames:
                frame = frames[0]  # 使用第一帧的元数据

                # 检查HDR类型
                side_data = frame.get('side_data_list', [])
                for side in side_data:
                    if side.get('side_data_type') == 'Mastering display metadata':
                        # 解析 mastering display metadata
                        display_metadata = side.get('display_metadata', {})
                        if display_metadata:
                            metadata.mastering_display_primaries = (
                                display_metadata.get('red_x', 0.640),
                                display_metadata.get('red_y', 0.330),
                                display_metadata.get('green_x', 0.300),
                                display_metadata.get('green_y', 0.600),
                                display_metadata.get('blue_x', 0.150),
                                display_metadata.get('blue_y', 0.060)
                            )
                            metadata.mastering_display_white_point = (
                                display_metadata.get('white_x', 0.3127),
                                display_metadata.get('white_y', 0.3290)
                            )
                            metadata.max_luminance = display_metadata.get('max_luminance', 1000.0)
                            metadata.min_luminance = display_metadata.get('min_luminance', 0.0001)

                    elif side.get('side_data_type') == 'Content light level metadata':
                        # 解析 content light level metadata
                        content_metadata = side.get('content_metadata', {})
                        if content_metadata:
                            metadata.max_cll = content_metadata.get('max_cll', 0.0)
                            metadata.max_fall = content_metadata.get('max_fall', 0.0)

                # 检测HDR类型
                color_transfer = frame.get('color_transfer')
                if color_transfer:
                    if color_transfer in ['smpte2084', 'arib-std-b67']:
                        if color_transfer == 'smpte2084':
                            metadata.format = HDRMetadataFormat.STATIC_HDR10
                            metadata.transfer_function = 'pq'
                        elif color_transfer == 'arib-std-b67':
                            metadata.format = HDRMetadataFormat.HLG
                            metadata.transfer_function = 'hlg'

            return metadata

        except Exception as e:
            self.logger.error(f"HDR元数据解析失败: {str(e)}")
            return HDRMetadata()

    def _metadata_worker(self) -> None:
        """元数据工作线程"""
        while True:
            try:
                # 处理元数据任务
                time.sleep(1)  # 避免CPU占用过高

            except Exception as e:
                self.logger.error(f"元数据处理失败: {str(e)}")

    def tone_map_frame(self, frame: np.ndarray,
                      metadata: Optional[HDRMetadata] = None,
                      settings: Optional[ToneMappingSettings] = None) -> np.ndarray:
        """帧色调映射"""
        try:
            start_time = time.time()

            # 使用提供的设置或默认设置
            tone_settings = settings or self.tone_mapping_settings
            hdr_metadata = metadata or self.current_hdr_metadata

            if hdr_metadata is None:
                # 使用默认HDR元数据
                hdr_metadata = HDRMetadata(
                    max_luminance=1000.0,
                    min_luminance=0.0001
                )

            # 确保帧是float32格式
            if frame.dtype != np.float32:
                frame = frame.astype(np.float32) / 255.0

            # 根据HDR类型进行色调映射
            if hdr_metadata.transfer_function == 'pq':
                # HDR10 / PQ
                processed_frame = self._tone_map_pq(frame, hdr_metadata, tone_settings)
            elif hdr_metadata.transfer_function == 'hlg':
                # HLG
                processed_frame = self._tone_map_hlg(frame, hdr_metadata, tone_settings)
            else:
                # 默认处理
                processed_frame = self._tone_map_default(frame, hdr_metadata, tone_settings)

            # 转换回uint8
            processed_frame = (processed_frame * 255).astype(np.uint8)

            # 更新性能指标
            processing_time = time.time() - start_time
            self._update_performance_metrics(processing_time)

            return processed_frame

        except Exception as e:
            self.logger.error(f"色调映射失败: {str(e)}")
            return frame.copy()

    def _tone_map_pq(self, frame: np.ndarray,
                    metadata: HDRMetadata,
                    settings: ToneMappingSettings) -> np.ndarray:
        """PQ (HDR10) 色调映射"""
        try:
            # 转换为线性光
            linear_frame = self.color_science._st2084_eotf(frame)

            # 应用色调映射算法
            if settings.method == ToneMappingMethod.REINHARD:
                mapped_frame = self._reinhard_tone_mapping(linear_frame, metadata, settings)
            elif settings.method == ToneMappingMethod.FILMIC:
                mapped_frame = self._filmic_tone_mapping(linear_frame, metadata, settings)
            elif settings.method == ToneMappingMethod.ACES:
                mapped_frame = self._aces_tone_mapping(linear_frame, metadata, settings)
            elif settings.method == ToneMappingMethod.HABLE:
                mapped_frame = self._hable_tone_mapping(linear_frame, metadata, settings)
            elif settings.method == ToneMappingMethod.DRAGO:
                mapped_frame = self._drago_tone_mapping(linear_frame, metadata, settings)
            elif settings.method == ToneMappingMethod.DURAND:
                mapped_frame = self._durand_tone_mapping(linear_frame, metadata, settings)
            elif settings.method == ToneMappingMethod.MANTIUK:
                mapped_frame = self._mantiuk_tone_mapping(linear_frame, metadata, settings)
            else:
                mapped_frame = self._reinhard_tone_mapping(linear_frame, metadata, settings)

            # 应用SDR传递函数
            sdr_frame = self.color_science._rec709_oetf(mapped_frame)

            return sdr_frame

        except Exception as e:
            self.logger.error(f"PQ色调映射失败: {str(e)}")
            return frame.copy()

    def _tone_map_hlg(self, frame: np.ndarray,
                    metadata: HDRMetadata,
                    settings: ToneMappingSettings) -> np.ndarray:
        """HLG色调映射"""
        try:
            # HLG到线性转换
            linear_frame = self.color_science._hlg_eotf(frame)

            # 应用色调映射
            target_luminance = settings.target_peak_luminance
            system_gamma = settings.target_system_gamma

            # HLG系统伽马调整
            mapped_frame = np.power(linear_frame * (target_luminance / 1000.0), 1/system_gamma)

            # 应用SDR传递函数
            sdr_frame = self.color_science._rec709_oetf(mapped_frame)

            return sdr_frame

        except Exception as e:
            self.logger.error(f"HLG色调映射失败: {str(e)}")
            return frame.copy()

    def _tone_map_default(self, frame: np.ndarray,
                        metadata: HDRMetadata,
                        settings: ToneMappingSettings) -> np.ndarray:
        """默认色调映射"""
        try:
            # 简单的线性压缩
            max_luminance = metadata.max_luminance
            target_luminance = settings.target_peak_luminance

            compression_ratio = target_luminance / max_luminance
            mapped_frame = frame * compression_ratio

            # 应用SDR传递函数
            sdr_frame = self.color_science._rec709_oetf(mapped_frame)

            return sdr_frame

        except Exception as e:
            self.logger.error(f"默认色调映射失败: {str(e)}")
            return frame.copy()

    def _reinhard_tone_mapping(self, frame: np.ndarray,
                             metadata: HDRMetadata,
                             settings: ToneMappingSettings) -> np.ndarray:
        """Reinhard色调映射"""
        try:
            # 计算关键值
            luminance = self._calculate_luminance(frame)
            key_value = np.exp(np.mean(np.log(luminance + 1e-8)))

            # 计算缩放因子
            max_luminance = metadata.max_luminance
            target_luminance = settings.target_peak_luminance
            scale = (target_luminance / 10000.0) / key_value

            # 应用Reinhard操作符
            mapped_luminance = (luminance * scale) / (1 + luminance * scale)

            # 保持色彩关系
            ratio = mapped_luminance / (luminance + 1e-8)
            if len(frame.shape) == 3:
                mapped_frame = frame * ratio[:, :, np.newaxis]
            else:
                mapped_frame = mapped_luminance

            # 应用饱和度保持
            if settings.preserve_saturation != 1.0:
                mapped_frame = self._apply_saturation_preservation(
                    mapped_frame, frame, settings.preserve_saturation
                )

            return np.clip(mapped_frame, 0, 1)

        except Exception as e:
            self.logger.error(f"Reinhard色调映射失败: {str(e)}")
            return frame.copy()

    def _filmic_tone_mapping(self, frame: np.ndarray,
                           metadata: HDRMetadata,
                           settings: ToneMappingSettings) -> np.ndarray:
        """Filmic色调映射"""
        try:
            # Filmic曲线参数
            A = settings.shoulder_strength if settings.shoulder_strength > 0 else 0.22
            B = settings.linear_strength if settings.linear_strength > 0 else 0.30
            C = settings.linear_slope if settings.linear_slope > 0 else 0.10
            D = settings.toe_strength if settings.toe_strength > 0 else 0.20
            E = settings.toe_numerator if settings.toe_numerator > 0 else 0.01
            F = settings.toe_denominator if settings.toe_denominator > 0 else 0.30

            # 应用filmic曲线
            def filmic_curve(x):
                return ((x * (A*x + C*B) + D*E) / (x * (A*x + B) + D*F)) - E/F

            # 归一化到0-1范围
            max_luminance = metadata.max_luminance
            target_luminance = settings.target_peak_luminance
            normalized_frame = frame / max_luminance

            # 应用曲线
            mapped_frame = filmic_curve(normalized_frame * settings.exposure_bias)

            # 缩放到目标亮度
            mapped_frame = mapped_frame * (target_luminance / max_luminance)

            return np.clip(mapped_frame, 0, 1)

        except Exception as e:
            self.logger.error(f"Filmic色调映射失败: {str(e)}")
            return frame.copy()

    def _aces_tone_mapping(self, frame: np.ndarray,
                          metadata: HDRMetadata,
                          settings: ToneMappingSettings) -> np.ndarray:
        """ACES色调映射"""
        try:
            # ACES变换参数
            a = 2.51
            b = 0.03
            c = 2.43
            d = 0.59
            e = 0.14

            # ACES曲线
            def aces_curve(x):
                return (x * (a*x + b)) / (x * (c*x + d) + e)

            # 归一化
            max_luminance = metadata.max_luminance
            target_luminance = settings.target_peak_luminance
            normalized_frame = frame / max_luminance

            # 应用ACES曲线
            mapped_frame = aces_curve(normalized_frame * settings.exposure_bias)

            # 缩放到目标亮度
            mapped_frame = mapped_frame * (target_luminance / max_luminance)

            return np.clip(mapped_frame, 0, 1)

        except Exception as e:
            self.logger.error(f"ACES色调映射失败: {str(e)}")
            return frame.copy()

    def _hable_tone_mapping(self, frame: np.ndarray,
                          metadata: HDRMetadata,
                          settings: ToneMappingSettings) -> np.ndarray:
        """Hable色调映射（Uncharted 2）"""
        try:
            # Hable曲线参数
            A = 0.22
            B = 0.30
            C = 0.10
            D = 0.20
            E = 0.01
            F = 0.30
            W = 11.2

            def hable_curve(x):
                return ((x * (A*x + C*B) + D*E) / (x * (A*x + B) + D*F)) - E/F

            def hable_inv_curve(x):
                return ((x * (A*x + B) + D*F) / (x * (A*x + C*B) + D*E)) + E/F

            # 归一化
            max_luminance = metadata.max_luminance
            target_luminance = settings.target_peak_luminance
            normalized_frame = frame / max_luminance

            # 应用Hable曲线
            mapped_frame = hable_curve(normalized_frame * settings.exposure_bias) / hable_inv_curve(W)

            # 缩放到目标亮度
            mapped_frame = mapped_frame * (target_luminance / max_luminance)

            return np.clip(mapped_frame, 0, 1)

        except Exception as e:
            self.logger.error(f"Hable色调映射失败: {str(e)}")
            return frame.copy()

    def _drago_tone_mapping(self, frame: np.ndarray,
                          metadata: HDRMetadata,
                          settings: ToneMappingSettings) -> np.ndarray:
        """Drago色调映射"""
        try:
            # Drago算法参数
            max_luminance = metadata.max_luminance
            target_luminance = settings.target_peak_luminance
            bias = np.log(2.0) / np.log(10.0)  # 可以调整

            # 计算亮度
            luminance = self._calculate_luminance(frame)

            # 计算对数平均亮度
            log_avg_luminance = np.exp(np.mean(np.log(luminance + 1e-8)))

            # Drago变换
            normalized_luminance = (bias * np.log(luminance / log_avg_luminance + 1e-8)) / np.log(max_luminance / log_avg_luminance + 1e-8)
            mapped_luminance = normalized_luminance * target_luminance / max_luminance

            # 保持色彩关系
            ratio = mapped_luminance / (luminance + 1e-8)
            if len(frame.shape) == 3:
                mapped_frame = frame * ratio[:, :, np.newaxis]
            else:
                mapped_frame = mapped_luminance

            return np.clip(mapped_frame, 0, 1)

        except Exception as e:
            self.logger.error(f"Drago色调映射失败: {str(e)}")
            return frame.copy()

    def _durand_tone_mapping(self, frame: np.ndarray,
                           metadata: HDRMetadata,
                           settings: ToneMappingSettings) -> np.ndarray:
        """Durand色调映射（双边滤波）"""
        try:
            # Durand算法参数
            max_luminance = metadata.max_luminance
            target_luminance = settings.target_peak_luminance
            spatial = 2.0  # 空间参数
            range = 0.4   # 范围参数

            # 转换为对数域
            log_frame = np.log(frame + 1e-8)

            # 计算亮度
            luminance = self._calculate_luminance(log_frame)

            # 应用双边滤波
            # 注意：这里简化了双边滤波，实际实现应该使用cv2.bilateralFilter
            filtered_luminance = self._simplified_bilateral_filter(luminance, spatial, range)

            # 计算细节层
            detail_layer = luminance - filtered_luminance

            # 压缩基础层
            max_log_luminance = np.log(max_luminance)
            min_log_luminance = np.log(target_luminance)
            compression_ratio = (min_log_luminance - max_log_luminance) / max_log_luminance

            compressed_base = filtered_luminance * (1 + compression_ratio)

            # 重建图像
            reconstructed_luminance = compressed_base + detail_layer

            # 转换回线性域
            mapped_luminance = np.exp(reconstructed_luminance)

            # 保持色彩关系
            original_luminance = self._calculate_luminance(frame)
            ratio = mapped_luminance / (original_luminance + 1e-8)
            if len(frame.shape) == 3:
                mapped_frame = frame * ratio[:, :, np.newaxis]
            else:
                mapped_frame = mapped_luminance

            return np.clip(mapped_frame, 0, 1)

        except Exception as e:
            self.logger.error(f"Durand色调映射失败: {str(e)}")
            return frame.copy()

    def _mantiuk_tone_mapping(self, frame: np.ndarray,
                            metadata: HDRMetadata,
                            settings: ToneMappingSettings) -> np.ndarray:
        """Mantiuk色调映射"""
        try:
            # Mantiuk算法参数
            max_luminance = metadata.max_luminance
            target_luminance = settings.target_peak_luminance
            contrast_enhancement = settings.contrast_boost
            saturation_factor = settings.preserve_saturation

            # 转换为对比度域
            # 简化的Mantiuk实现
            luminance = self._calculate_luminance(frame)
            log_luminance = np.log(luminance + 1e-8)

            # 计算对比度
            contrast = self._calculate_contrast(log_luminance)

            # 增强对比度
            enhanced_contrast = contrast * contrast_enhancement

            # 重建亮度
            mapped_luminance = self._reconstruct_from_contrast(enhanced_contrast, log_luminance)

            # 应用压缩
            compression_ratio = target_luminance / max_luminance
            mapped_luminance = mapped_luminance * compression_ratio

            # 转换回线性域
            mapped_luminance = np.exp(mapped_luminance)

            # 保持色彩关系
            ratio = mapped_luminance / (luminance + 1e-8)
            if len(frame.shape) == 3:
                mapped_frame = frame * ratio[:, :, np.newaxis]
            else:
                mapped_frame = mapped_luminance

            return np.clip(mapped_frame, 0, 1)

        except Exception as e:
            self.logger.error(f"Mantiuk色调映射失败: {str(e)}")
            return frame.copy()

    def _calculate_luminance(self, frame: np.ndarray) -> np.ndarray:
        """计算亮度"""
        if len(frame.shape) == 3:
            # 使用Rec.709亮度公式
            return 0.2126 * frame[:, :, 0] + 0.7152 * frame[:, :, 1] + 0.0722 * frame[:, :, 2]
        else:
            return frame

    def _apply_saturation_preservation(self, mapped_frame: np.ndarray,
                                     original_frame: np.ndarray,
                                     saturation_factor: float) -> np.ndarray:
        """应用饱和度保持"""
        try:
            # 转换到HSV色彩空间
            if len(mapped_frame.shape) == 3:
                original_hsv = cv2.cvtColor((original_frame * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
                mapped_hsv = cv2.cvtColor((mapped_frame * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)

                # 调整饱和度
                h, s, v = cv2.split(mapped_hsv)
                original_s = original_hsv[:, :, 1]

                # 混合饱和度
                adjusted_s = original_s * saturation_factor + s * (1 - saturation_factor)
                adjusted_s = np.clip(adjusted_s, 0, 255)

                # 重建HSV图像
                adjusted_hsv = cv2.merge([h, adjusted_s, v])
                adjusted_frame = cv2.cvtColor(adjusted_hsv, cv2.COLOR_HSV2RGB)

                return adjusted_frame.astype(np.float32) / 255.0
            else:
                return mapped_frame

        except Exception as e:
            self.logger.error(f"饱和度保持失败: {str(e)}")
            return mapped_frame

    def _simplified_bilateral_filter(self, image: np.ndarray,
                                   spatial: float,
                                   range_val: float) -> np.ndarray:
        """简化的双边滤波"""
        # 这是一个简化的实现，实际应用中应该使用cv2.bilateralFilter
        try:
            # 应用高斯滤波作为空间滤波
            spatial_filtered = cv2.GaussianBlur(image, (int(spatial * 3), int(spatial * 3)), spatial)

            # 简单的范围滤波
            range_filtered = image.copy()
            for i in range(image.shape[0]):
                for j in range(image.shape[1]):
                    diff = np.abs(image[i, j] - spatial_filtered[i, j])
                    weight = np.exp(-diff * diff / (2 * range_val * range_val))
                    range_filtered[i, j] = image[i, j] * weight + spatial_filtered[i, j] * (1 - weight)

            return range_filtered

        except Exception as e:
            self.logger.error(f"双边滤波失败: {str(e)}")
            return image.copy()

    def _calculate_contrast(self, image: np.ndarray) -> np.ndarray:
        """计算对比度"""
        try:
            # 使用Sobel算子计算梯度
            grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
            contrast = np.sqrt(grad_x**2 + grad_y**2)
            return contrast

        except Exception as e:
            self.logger.error(f"对比度计算失败: {str(e)}")
            return np.zeros_like(image)

    def _reconstruct_from_contrast(self, contrast: np.ndarray,
                                base_image: np.ndarray) -> np.ndarray:
        """从对比度重建图像"""
        try:
            # 这是一个简化的重建方法
            # 实际应用中应该使用更复杂的算法
            reconstructed = base_image + contrast * 0.1
            return reconstructed

        except Exception as e:
            self.logger.error(f"图像重建失败: {str(e)}")
            return base_image.copy()

    def generate_hdr_metadata(self, frame: np.ndarray,
                           frame_format: HDRMetadataFormat = HDRMetadataFormat.STATIC_HDR10) -> HDRMetadata:
        """生成HDR元数据"""
        try:
            # 分析帧以生成元数据
            if frame.dtype != np.float32:
                frame = frame.astype(np.float32) / 255.0

            # 计算亮度统计
            luminance = self._calculate_luminance(frame)
            max_lum = np.max(luminance)
            min_lum = np.min(luminance[luminance > 0])
            avg_lum = np.mean(luminance)

            # 计算色彩统计
            if len(frame.shape) == 3:
                # 计算最大色彩级别
                max_cll = np.max(frame) * 10000  # 转换为cd/m²
                max_fall = avg_lum * 10000
            else:
                max_cll = max_lum * 10000
                max_fall = avg_lum * 10000

            # 创建元数据
            metadata = HDRMetadata(
                format=frame_format,
                max_luminance=max_lum * 10000,
                min_luminance=min_lum * 10000,
                max_fall=max_fall,
                max_cll=max_cll,
                transfer_function='pq' if frame_format == HDRMetadataFormat.STATIC_HDR10 else 'hlg'
            )

            return metadata

        except Exception as e:
            self.logger.error(f"HDR元数据生成失败: {str(e)}")
            return HDRMetadata()

    def create_hdr_from_sdr(self, frame: np.ndarray,
                          target_hdr_standard: HDRStandard = HDRStandard.HDR10,
                          metadata: Optional[HDRMetadata] = None) -> np.ndarray:
        """从SDR创建HDR"""
        try:
            if frame.dtype != np.float32:
                frame = frame.astype(np.float32) / 255.0

            # 应用逆SDR传递函数
            linear_frame = self.color_science._rec709_eotf(frame)

            # 根据目标HDR标准进行处理
            if target_hdr_standard == HDRStandard.HDR10:
                # HDR10处理
                if metadata is None:
                    metadata = HDRMetadata(
                        max_luminance=1000.0,
                        min_luminance=0.0001
                    )

                # 扩展动态范围
                expansion_factor = metadata.max_luminance / 100.0
                expanded_frame = linear_frame * expansion_factor

                # 应用PQ传递函数
                hdr_frame = self.color_science._st2084_oetf(expanded_frame)

            elif target_hdr_standard == HDRStandard.HLG:
                # HLG处理
                hlg_params = self.color_science.hdr_parameters['hlg']
                ref_white = hlg_params['reference_white']

                # 扩展动态范围
                expansion_factor = ref_white / 100.0
                expanded_frame = linear_frame * expansion_factor

                # 应用HLG传递函数
                hdr_frame = self.color_science._hlg_oetf(expanded_frame)

            else:
                # 默认处理
                hdr_frame = linear_frame

            return np.clip(hdr_frame, 0, 1)

        except Exception as e:
            self.logger.error(f"SDR转HDR失败: {str(e)}")
            return frame.copy()

    def process_video_hdr_to_sdr(self, input_path: str, output_path: str,
                               settings: Optional[ToneMappingSettings] = None) -> bool:
        """处理视频HDR到SDR转换"""
        try:
            # 分析HDR元数据
            metadata = self.analyze_hdr_metadata(input_path)
            if metadata is None:
                self.logger.warning("无法分析HDR元数据，使用默认设置")
                metadata = HDRMetadata()

            # 使用FFmpeg进行视频处理
            cmd = [
                self.ffmpeg_utils.ffmpeg_path,
                "-i", input_path,
                "-vf", self._build_ffmpeg_tone_mapping_filter(metadata, settings),
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "copy",
                "-y",
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=3600, text=True)

            if result.returncode != 0:
                self.logger.error(f"视频处理失败: {result.stderr}")
                return False

            self.logger.info(f"视频HDR到SDR转换完成: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"视频HDR到SDR转换失败: {str(e)}")
            return False

    def _build_ffmpeg_tone_mapping_filter(self, metadata: HDRMetadata,
                                        settings: Optional[ToneMappingSettings]) -> str:
        """构建FFmpeg色调映射滤镜"""
        try:
            tone_settings = settings or self.tone_mapping_settings

            if metadata.transfer_function == 'pq':
                # HDR10 PQ色调映射
                filter_str = (
                    "tonemap=tonemap={}:param={}:desat={}:peak={}"
                ).format(
                    tone_settings.method.value,
                    tone_settings.exposure_bias,
                    tone_settings.preserve_saturation,
                    metadata.max_luminance
                )
            elif metadata.transfer_function == 'hlg':
                # HLG色调映射
                filter_str = (
                    "tonemap=tonemap=hlg:desat={}:peak={}"
                ).format(
                    tone_settings.preserve_saturation,
                    metadata.max_luminance
                )
            else:
                # 默认色调映射
                filter_str = "scale=1920:1080"  # 简单缩放

            return filter_str

        except Exception as e:
            self.logger.error(f"FFmpeg滤镜构建失败: {str(e)}")
            return "scale=1920:1080"

    def get_available_presets(self) -> List[str]:
        """获取可用预设列表"""
        return list(self.presets.keys())

    def load_preset(self, preset_name: str) -> bool:
        """加载预设"""
        try:
            if preset_name in self.presets:
                self.tone_mapping_settings = self.presets[preset_name]
                self.logger.info(f"预设已加载: {preset_name}")
                return True
            else:
                self.logger.warning(f"预设不存在: {preset_name}")
                return False

        except Exception as e:
            self.logger.error(f"预设加载失败: {str(e)}")
            return False

    def save_preset(self, preset_name: str, settings: ToneMappingSettings) -> bool:
        """保存预设"""
        try:
            self.presets[preset_name] = settings
            self.logger.info(f"预设已保存: {preset_name}")
            return True

        except Exception as e:
            self.logger.error(f"预设保存失败: {str(e)}")
            return False

    def _update_performance_metrics(self, processing_time: float) -> None:
        """更新性能指标"""
        self.performance_metrics['frames_processed'] += 1
        self.performance_metrics['total_processing_time'] += processing_time
        self.performance_metrics['average_processing_time'] = (
            self.performance_metrics['total_processing_time'] /
            self.performance_metrics['frames_processed']
        )

        # 更新缓存命中率
        if hasattr(self, 'cache_hits') and hasattr(self, 'cache_misses'):
            total_requests = self.cache_hits + self.cache_misses
            if total_requests > 0:
                self.performance_metrics['cache_hit_rate'] = self.cache_hits / total_requests

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.performance_metrics.copy()

    def optimize_performance(self) -> None:
        """优化性能"""
        try:
            # 根据硬件性能调整设置
            if self.hardware_acceleration:
                hw_metrics = self.hardware_acceleration.get_performance_metrics()

                # 调整线程池大小
                if hw_metrics.gpu_usage > 80:
                    new_size = max(1, self.config.thread_pool_size - 1)
                    self.thread_pool._max_workers = new_size
                elif hw_metrics.gpu_usage < 30:
                    new_size = min(8, self.config.thread_pool_size + 1)
                    self.thread_pool._max_workers = new_size

                self.logger.info("性能优化完成")

        except Exception as e:
            self.logger.error(f"性能优化失败: {str(e)}")

    def export_settings(self, file_path: str) -> bool:
        """导出设置"""
        try:
            settings_data = {
                'config': self.config.__dict__,
                'tone_mapping_settings': self.tone_mapping_settings.to_dict(),
                'presets': {name: preset.to_dict() for name, preset in self.presets.items()}
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"设置已导出: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"设置导出失败: {str(e)}")
            return False

    def import_settings(self, file_path: str) -> bool:
        """导入设置"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"设置文件不存在: {file_path}")
                return False

            with open(file_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)

            # 导入配置
            if 'config' in settings_data:
                config_data = settings_data['config']
                self.config = HDRProcessingConfig(**config_data)

            # 导入色调映射设置
            if 'tone_mapping_settings' in settings_data:
                self.tone_mapping_settings = ToneMappingSettings.from_dict(
                    settings_data['tone_mapping_settings']
                )

            # 导入预设
            if 'presets' in settings_data:
                self.presets = {}
                for name, preset_data in settings_data['presets'].items():
                    self.presets[name] = ToneMappingSettings.from_dict(preset_data)

            self.logger.info(f"设置已导入: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"设置导入失败: {str(e)}")
            return False

    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 关闭线程池
            self.thread_pool.shutdown(wait=True)

            # 清理缓存
            self.frame_cache.clear()
            self.metadata_cache.clear()

            self.logger.info("HDR处理引擎清理完成")

        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局HDR处理引擎实例
_hdr_processing_engine: Optional[HDRProcessingEngine] = None


def get_hdr_processing_engine(config: Optional[HDRProcessingConfig] = None) -> HDRProcessingEngine:
    """获取全局HDR处理引擎实例"""
    global _hdr_processing_engine
    if _hdr_processing_engine is None:
        _hdr_processing_engine = HDRProcessingEngine(config)
    return _hdr_processing_engine


def cleanup_hdr_processing_engine() -> None:
    """清理全局HDR处理引擎实例"""
    global _hdr_processing_engine
    if _hdr_processing_engine is not None:
        _hdr_processing_engine.cleanup()
        _hdr_processing_engine = None


# 导入缺失的模块
import subprocess