#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio Professional Color Grading System
专业色彩分级系统，提供DaVinci Resolve级别的色彩处理能力
"""

import os
import numpy as np
import cv2
import time
import threading
import queue
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
import logging

from ..core.logger import get_logger
from ..core.event_system import EventBus
from ..core.hardware_acceleration import get_hardware_acceleration
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import get_ffmpeg_utils, VideoInfo, VideoCodec
from .video_engine import get_video_engine


class ColorSpace(Enum):
    """色彩空间枚举"""
    SRGB = "srgb"
    REC709 = "rec709"
    REC2020 = "rec2020"
    DCI_P3 = "dci_p3"
    ADOBE_RGB = "adobe_rgb"
    CIE_XYZ = "cie_xyz"
    CIE_LAB = "cie_lab"
    LINEAR_RGB = "linear_rgb"
    LOG_C = "log_c"
    LOG_3G10 = "log_3g10"
    S_LOG3 = "s_log3"
    V_LOG = "v_log"


class HDRStandard(Enum):
    """HDR标准枚举"""
    NONE = "none"
    HDR10 = "hdr10"
    HDR10_PLUS = "hdr10_plus"
    DOLBY_VISION = "dolby_vision"
    HLG = "hlg"


class ColorGradingTool(Enum):
    """色彩校正工具枚举"""
    WHEEL = "wheel"  # 色轮
    CURVE = "curve"  # 曲线
    LUT = "lut"  # LUT应用
    HSL = "hsl"  # HSL调整
    RGB = "rgb"  # RGB调整
    CONTRAST = "contrast"  # 对比度
    SATURATION = "saturation"  # 饱和度
    EXPOSURE = "exposure"  # 曝光
    WHITE_BALANCE = "white_balance"  # 白平衡
    SHADOWS_HIGHLIGHTS = "shadows_highlights"  # 阴影高光
    VIBRANCE = "vibrance"  # 鲜艳度
    COLOR_MATCH = "color_match"  # 色彩匹配
    WAVEFORM = "waveform"  # 波形图
    VECTORSCOPE = "vectorscope"  # 矢量图
    HISTOGRAM = "histogram"  # 直方图


@dataclass
class ColorWheelAdjustment:
    """色轮调整数据类"""
    shadows: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # 阴影 (hue, saturation, lift)
    midtones: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # 中间调 (hue, saturation, gamma)
    highlights: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # 高光 (hue, saturation, gain)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'shadows': self.shadows,
            'midtones': self.midtones,
            'highlights': self.highlights
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorWheelAdjustment':
        """从字典创建"""
        return cls(
            shadows=tuple(data.get('shadows', (0.0, 0.0, 0.0))),
            midtones=tuple(data.get('midtones', (0.0, 0.0, 0.0))),
            highlights=tuple(data.get('highlights', (0.0, 0.0, 0.0)))
        )


@dataclass
class CurvePoint:
    """曲线点数据类"""
    x: float
    y: float

    def to_dict(self) -> Dict[str, float]:
        return {'x': self.x, 'y': self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'CurvePoint':
        return cls(x=data['x'], y=data['y'])


@dataclass
class ColorCurve:
    """色彩曲线数据类"""
    curve_type: str  # 'luma', 'red', 'green', 'blue', 'rgb'
    points: List[CurvePoint] = field(default_factory=list)
    spline_degree: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            'curve_type': self.curve_type,
            'points': [point.to_dict() for point in self.points],
            'spline_degree': self.spline_degree
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorCurve':
        return cls(
            curve_type=data['curve_type'],
            points=[CurvePoint.from_dict(point) for point in data.get('points', [])],
            spline_degree=data.get('spline_degree', 3)
        )


@dataclass
class LUTInfo:
    """LUT信息数据类"""
    name: str
    path: str
    size: int = 33  # LUT尺寸 (17, 33, 65等)
    format: str = "cube"  # cube, 3dl, mga
    input_space: ColorSpace = ColorSpace.REC709
    output_space: ColorSpace = ColorSpace.REC709
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'path': self.path,
            'size': self.size,
            'format': self.format,
            'input_space': self.input_space.value,
            'output_space': self.output_space.value,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LUTInfo':
        return cls(
            name=data['name'],
            path=data['path'],
            size=data.get('size', 33),
            format=data.get('format', 'cube'),
            input_space=ColorSpace(data.get('input_space', 'rec709')),
            output_space=ColorSpace(data.get('output_space', 'rec709')),
            description=data.get('description', '')
        )


@dataclass
class ColorGradePreset:
    """色彩分级预设数据类"""
    name: str
    description: str
    adjustments: Dict[str, Any] = field(default_factory=dict)
    lut_info: Optional[LUTInfo] = None
    curves: List[ColorCurve] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'adjustments': self.adjustments,
            'lut_info': self.lut_info.to_dict() if self.lut_info else None,
            'curves': [curve.to_dict() for curve in self.curves],
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorGradePreset':
        return cls(
            name=data['name'],
            description=data['description'],
            adjustments=data.get('adjustments', {}),
            lut_info=LUTInfo.from_dict(data['lut_info']) if data.get('lut_info') else None,
            curves=[ColorCurve.from_dict(curve) for curve in data.get('curves', [])],
            tags=data.get('tags', [])
        )


@dataclass
class ColorGradingSettings:
    """色彩分级设置数据类"""
    color_space: ColorSpace = ColorSpace.REC709
    hdr_standard: HDRStandard = HDRStandard.NONE
    bit_depth: int = 8  # 8, 10, 12, 16
    chroma_subsampling: str = "4:2:0"  # 4:4:4, 4:2:2, 4:2:0, 4:1:1
    color_range: str = "limited"  # limited, full
    gamma: float = 2.2
    use_gpu: bool = True
    real_time_preview: bool = True
    preview_quality: int = 75  # 预览质量百分比
    cache_enabled: bool = True
    max_cache_size: int = 2048 * 1024 * 1024  # 2GB

    def to_dict(self) -> Dict[str, Any]:
        return {
            'color_space': self.color_space.value,
            'hdr_standard': self.hdr_standard.value,
            'bit_depth': self.bit_depth,
            'chroma_subsampling': self.chroma_subsampling,
            'color_range': self.color_range,
            'gamma': self.gamma,
            'use_gpu': self.use_gpu,
            'real_time_preview': self.real_time_preview,
            'preview_quality': self.preview_quality,
            'cache_enabled': self.cache_enabled,
            'max_cache_size': self.max_cache_size
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorGradingSettings':
        return cls(
            color_space=ColorSpace(data.get('color_space', 'rec709')),
            hdr_standard=HDRStandard(data.get('hdr_standard', 'none')),
            bit_depth=data.get('bit_depth', 8),
            chroma_subsampling=data.get('chroma_subsampling', '4:2:0'),
            color_range=data.get('color_range', 'limited'),
            gamma=data.get('gamma', 2.2),
            use_gpu=data.get('use_gpu', True),
            real_time_preview=data.get('real_time_preview', True),
            preview_quality=data.get('preview_quality', 75),
            cache_enabled=data.get('cache_enabled', True),
            max_cache_size=data.get('max_cache_size', 2048 * 1024 * 1024)
        )


@dataclass
class ColorGradingOperation:
    """色彩分级操作数据类"""
    id: str
    operation_type: ColorGradingTool
    parameters: Dict[str, Any]
    enabled: bool = True
    opacity: float = 1.0
    mask_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'operation_type': self.operation_type.value,
            'parameters': self.parameters,
            'enabled': self.enabled,
            'opacity': self.opacity,
            'mask_path': self.mask_path
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorGradingOperation':
        return cls(
            id=data['id'],
            operation_type=ColorGradingTool(data['operation_type']),
            parameters=data['parameters'],
            enabled=data.get('enabled', True),
            opacity=data.get('opacity', 1.0),
            mask_path=data.get('mask_path')
        )


class ColorGradingEngine:
    """专业色彩分级引擎"""

    def __init__(self, settings: Optional[ColorGradingSettings] = None, logger=None):
        """初始化色彩分级引擎"""
        self.logger = logger or get_logger("ColorGradingEngine")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.video_engine = get_video_engine()
        self.ffmpeg_utils = get_ffmpeg_utils()
        self.hardware_acceleration = get_hardware_acceleration()

        # 设置
        self.settings = settings or ColorGradingSettings()
        self.is_initialized = False

        # 色彩校正操作栈
        self.operation_stack: List[ColorGradingOperation] = []
        self.operation_lock = threading.Lock()

        # LUT管理
        self.available_luts: Dict[str, LUTInfo] = {}
        self.loaded_luts: Dict[str, np.ndarray] = {}
        self.lut_lock = threading.Lock()

        # 预设管理
        self.presets: Dict[str, ColorGradePreset] = {}
        self.preset_lock = threading.Lock()

        # 缓存系统
        self.frame_cache: Dict[str, np.ndarray] = {}
        self.cache_lock = threading.Lock()

        # 性能监控
        self.performance_metrics = {
            'operations_per_second': 0.0,
            'average_processing_time': 0.0,
            'cache_hit_rate': 0.0,
            'gpu_usage': 0.0,
            'memory_usage': 0
        }

        # 处理线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.processing_queue = queue.Queue()
        self.is_processing = False

        # 色彩空间转换矩阵
        self.color_matrices = self._init_color_matrices()

        # 初始化
        self._initialize()

    def _initialize(self) -> None:
        """初始化引擎"""
        try:
            # 加载内置LUT
            self._load_builtin_luts()

            # 加载内置预设
            self._load_builtin_presets()

            # 启动处理线程
            self._start_processing_thread()

            # 初始化硬件加速
            self._init_hardware_acceleration()

            self.is_initialized = True
            self.logger.info("色彩分级引擎初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"色彩分级引擎初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ColorGradingEngine",
                    operation="initialize"
                ),
                user_message="色彩分级引擎初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _init_color_matrices(self) -> Dict[str, np.ndarray]:
        """初始化色彩空间转换矩阵"""
        matrices = {}

        # sRGB to XYZ (D65)
        matrices['srgb_to_xyz'] = np.array([
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041]
        ])

        # XYZ to sRGB (D65)
        matrices['xyz_to_srgb'] = np.array([
            [3.2404542, -1.5371385, -0.4985314],
            [-0.9692660,  1.8760108,  0.0415560],
            [0.0556434, -0.2040259,  1.0572252]
        ])

        # Rec.709 to XYZ
        matrices['rec709_to_xyz'] = np.array([
            [0.412391, 0.357584, 0.180481],
            [0.212639, 0.715169, 0.072192],
            [0.019331, 0.119195, 0.950532]
        ])

        # XYZ to Rec.709
        matrices['xyz_to_rec709'] = np.array([
            [3.240970, -1.537383, -0.498611],
            [-0.969244,  1.875968,  0.041555],
            [0.055630, -0.203977,  1.056972]
        ])

        # DCI-P3 to XYZ
        matrices['dci_p3_to_xyz'] = np.array([
            [0.4451698, 0.2771344, 0.1722827],
            [0.2094922, 0.7215953, 0.0689131],
            [0.0000000, 0.0470606, 0.9073554]
        ])

        # XYZ to DCI-P3
        matrices['xyz_to_dci_p3'] = np.array([
            [2.725394, -1.018003, -0.440163],
            [-0.795168,  1.689732,  0.022647],
            [0.041242, -0.087639,  1.100930]
        ])

        return matrices

    def _init_hardware_acceleration(self) -> None:
        """初始化硬件加速"""
        try:
            if self.settings.use_gpu:
                # 检查CUDA是否可用
                if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                    self.logger.info("CUDA加速已启用")
                else:
                    self.logger.warning("CUDA不可用，将使用CPU处理")
                    self.settings.use_gpu = False

        except Exception as e:
            self.logger.error(f"硬件加速初始化失败: {str(e)}")
            self.settings.use_gpu = False

    def _load_builtin_luts(self) -> None:
        """加载内置LUT"""
        try:
            # 创建内置LUT路径
            lut_dir = os.path.join(os.path.dirname(__file__), "luts")
            os.makedirs(lut_dir, exist_ok=True)

            # 这里会加载一些基础的内置LUT
            # 在实际实现中，会从文件系统加载

            self.logger.info(f"内置LUT加载完成，共{len(self.available_luts)}个LUT")

        except Exception as e:
            self.logger.error(f"内置LUT加载失败: {str(e)}")

    def _load_builtin_presets(self) -> None:
        """加载内置预设"""
        try:
            # 创建一些基础预设
            presets = [
                ColorGradePreset(
                    name="cinematic",
                    description="电影风格",
                    adjustments={
                        'contrast': 1.2,
                        'saturation': 0.9,
                        'vibrance': 1.1,
                        'shadows': -0.2,
                        'highlights': 0.1
                    },
                    tags=['cinematic', 'film', 'dramatic']
                ),
                ColorGradePreset(
                    name="vintage",
                    description="复古风格",
                    adjustments={
                        'contrast': 1.1,
                        'saturation': 0.7,
                        'warmth': 0.3,
                        'fade': 0.2
                    },
                    tags=['vintage', 'retro', 'warm']
                ),
                ColorGradePreset(
                    name="vibrant",
                    description="鲜艳风格",
                    adjustments={
                        'contrast': 1.3,
                        'saturation': 1.4,
                        'vibrance': 1.2,
                        'clarity': 0.8
                    },
                    tags=['vibrant', 'colorful', 'bright']
                )
            ]

            with self.preset_lock:
                for preset in presets:
                    self.presets[preset.name] = preset

            self.logger.info(f"内置预设加载完成，共{len(self.presets)}个预设")

        except Exception as e:
            self.logger.error(f"内置预设加载失败: {str(e)}")

    def _start_processing_thread(self) -> None:
        """启动处理线程"""
        self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
        self.processing_thread.start()
        self.logger.info("色彩分级处理线程已启动")

    def _processing_worker(self) -> None:
        """处理工作线程"""
        while True:
            try:
                task = self.processing_queue.get(timeout=1.0)
                try:
                    result = self._process_frame_task(task)
                    if result is not None:
                        self.event_bus.publish("frame_processed", result)
                except Exception as e:
                    self.logger.error(f"帧处理失败: {str(e)}")
                finally:
                    self.processing_queue.task_done()
            except queue.Empty:
                continue

    def _process_frame_task(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理帧任务"""
        try:
            frame = task.get('frame')
            if frame is None:
                return None

            operations = task.get('operations', [])

            # 应用色彩分级操作
            processed_frame = self._apply_operations(frame, operations)

            return {
                'frame_id': task.get('frame_id'),
                'processed_frame': processed_frame,
                'processing_time': time.time() - task.get('start_time', time.time())
            }

        except Exception as e:
            self.logger.error(f"帧处理任务失败: {str(e)}")
            return None

    def convert_color_space(self, frame: np.ndarray,
                          from_space: ColorSpace,
                          to_space: ColorSpace) -> np.ndarray:
        """色彩空间转换"""
        try:
            if from_space == to_space:
                return frame.copy()

            # 确保帧是float32格式，范围0-1
            if frame.dtype != np.float32:
                frame = frame.astype(np.float32) / 255.0

            # 根据色彩空间进行转换
            if from_space == ColorSpace.SRGB and to_space == ColorSpace.CIE_XYZ:
                # sRGB -> XYZ
                gamma_frame = self._srgb_to_linear(frame)
                xyz_frame = self._apply_color_matrix(gamma_frame, self.color_matrices['srgb_to_xyz'])
                return xyz_frame

            elif from_space == ColorSpace.CIE_XYZ and to_space == ColorSpace.SRGB:
                # XYZ -> sRGB
                srgb_frame = self._apply_color_matrix(frame, self.color_matrices['xyz_to_srgb'])
                linear_frame = self._linear_to_srgb(srgb_frame)
                return linear_frame

            elif from_space == ColorSpace.REC709 and to_space == ColorSpace.DCI_P3:
                # Rec.709 -> XYZ -> DCI-P3
                xyz_frame = self._apply_color_matrix(frame, self.color_matrices['rec709_to_xyz'])
                p3_frame = self._apply_color_matrix(xyz_frame, self.color_matrices['xyz_to_dci_p3'])
                return p3_frame

            elif from_space == ColorSpace.DCI_P3 and to_space == ColorSpace.REC709:
                # DCI-P3 -> XYZ -> Rec.709
                xyz_frame = self._apply_color_matrix(frame, self.color_matrices['dci_p3_to_xyz'])
                rec709_frame = self._apply_color_matrix(xyz_frame, self.color_matrices['xyz_to_rec709'])
                return rec709_frame

            else:
                # 默认使用OpenCV的色彩空间转换
                conversion_map = {
                    (ColorSpace.SRGB, ColorSpace.REC709): cv2.COLOR_RGB2YCrCb,
                    (ColorSpace.REC709, ColorSpace.SRGB): cv2.COLOR_YCrCb2RGB,
                    (ColorSpace.SRGB, ColorSpace.CIE_LAB): cv2.COLOR_RGB2Lab,
                    (ColorSpace.CIE_LAB, ColorSpace.SRGB): cv2.COLOR_Lab2RGB,
                    (ColorSpace.SRGB, ColorSpace.HSV): cv2.COLOR_RGB2HSV,
                    (ColorSpace.HSV, ColorSpace.SRGB): cv2.COLOR_HSV2RGB,
                }

                conversion = conversion_map.get((from_space, to_space))
                if conversion:
                    return cv2.cvtColor(frame, conversion)
                else:
                    self.logger.warning(f"不支持的色彩空间转换: {from_space.value} -> {to_space.value}")
                    return frame.copy()

        except Exception as e:
            self.logger.error(f"色彩空间转换失败: {str(e)}")
            return frame.copy()

    def _srgb_to_linear(self, frame: np.ndarray) -> np.ndarray:
        """sRGB转线性RGB"""
        # sRGB伽马校正逆变换
        linear = np.where(frame <= 0.04045,
                         frame / 12.92,
                         np.power((frame + 0.055) / 1.055, 2.4))
        return linear

    def _linear_to_srgb(self, frame: np.ndarray) -> np.ndarray:
        """线性RGB转sRGB"""
        # sRGB伽马校正
        srgb = np.where(frame <= 0.0031308,
                       frame * 12.92,
                       1.055 * np.power(frame, 1.0/2.4) - 0.055)
        return np.clip(srgb, 0, 1)

    def _apply_color_matrix(self, frame: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """应用色彩转换矩阵"""
        # 确保帧是3通道的
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            h, w, c = frame.shape
            flat_frame = frame.reshape(-1, 3)
            converted = np.dot(flat_frame, matrix.T)
            return converted.reshape(h, w, c)
        else:
            return frame

    def apply_color_wheel(self, frame: np.ndarray,
                         adjustment: ColorWheelAdjustment) -> np.ndarray:
        """应用色轮调整"""
        try:
            # 转换到HSV色彩空间
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            h, s, v = cv2.split(hsv_frame)

            # 应用阴影调整
            shadow_mask = v < 0.33
            if np.any(shadow_mask):
                hue_shift, sat_shift, lift_shift = adjustment.shadows
                h[shadow_mask] = (h[shadow_mask] + hue_shift) % 180
                s[shadow_mask] = np.clip(s[shadow_mask] * (1 + sat_shift), 0, 255)
                v[shadow_mask] = np.clip(v[shadow_mask] * (1 + lift_shift), 0, 255)

            # 应用中间调调整
            midtone_mask = (v >= 0.33) & (v < 0.67)
            if np.any(midtone_mask):
                hue_shift, sat_shift, gamma_shift = adjustment.midtones
                h[midtone_mask] = (h[midtone_mask] + hue_shift) % 180
                s[midtone_mask] = np.clip(s[midtone_mask] * (1 + sat_shift), 0, 255)
                v[midtone_mask] = np.clip(v[midtone_mask] * (1 + gamma_shift), 0, 255)

            # 应用高光调整
            highlight_mask = v >= 0.67
            if np.any(highlight_mask):
                hue_shift, sat_shift, gain_shift = adjustment.highlights
                h[highlight_mask] = (h[highlight_mask] + hue_shift) % 180
                s[highlight_mask] = np.clip(s[highlight_mask] * (1 + sat_shift), 0, 255)
                v[highlight_mask] = np.clip(v[highlight_mask] * (1 + gain_shift), 0, 255)

            # 合并通道并转换回RGB
            hsv_adjusted = cv2.merge([h, s, v])
            rgb_frame = cv2.cvtColor(hsv_adjusted, cv2.COLOR_HSV2RGB)

            return rgb_frame

        except Exception as e:
            self.logger.error(f"色轮调整失败: {str(e)}")
            return frame.copy()

    def apply_color_curve(self, frame: np.ndarray,
                         curve: ColorCurve) -> np.ndarray:
        """应用色彩曲线"""
        try:
            if not curve.points:
                return frame.copy()

            # 根据曲线类型应用不同的调整
            if curve.curve_type == 'luma':
                # 亮度曲线
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                adjusted_gray = self._apply_curve_to_channel(gray, curve)
                # 按比例调整RGB通道
                ratio = adjusted_gray.astype(np.float32) / (gray.astype(np.float32) + 1e-8)
                adjusted_frame = frame.astype(np.float32) * ratio[:, :, np.newaxis]
                return np.clip(adjusted_frame, 0, 255).astype(np.uint8)

            elif curve.curve_type in ['red', 'green', 'blue']:
                # 单通道曲线
                channel_idx = {'red': 0, 'green': 1, 'blue': 2}[curve.curve_type]
                channels = list(cv2.split(frame))
                channels[channel_idx] = self._apply_curve_to_channel(channels[channel_idx], curve)
                return cv2.merge(channels)

            elif curve.curve_type == 'rgb':
                # RGB曲线（应用到所有通道）
                channels = cv2.split(frame)
                adjusted_channels = [self._apply_curve_to_channel(ch, curve) for ch in channels]
                return cv2.merge(adjusted_channels)

            else:
                self.logger.warning(f"未知的曲线类型: {curve.curve_type}")
                return frame.copy()

        except Exception as e:
            self.logger.error(f"曲线调整失败: {str(e)}")
            return frame.copy()

    def _apply_curve_to_channel(self, channel: np.ndarray,
                               curve: ColorCurve) -> np.ndarray:
        """对单个通道应用曲线"""
        try:
            # 创建曲线查找表
            lut = np.zeros(256, dtype=np.uint8)

            # 对曲线点进行样条插值
            if len(curve.points) >= 2:
                x_points = [int(p.x * 255) for p in curve.points]
                y_points = [int(p.y * 255) for p in curve.points]

                # 确保点按x坐标排序
                sorted_pairs = sorted(zip(x_points, y_points))
                x_points, y_points = zip(*sorted_pairs)

                # 线性插值
                for i in range(256):
                    # 找到i所在的区间
                    for j in range(len(x_points) - 1):
                        if x_points[j] <= i <= x_points[j + 1]:
                            # 线性插值
                            ratio = (i - x_points[j]) / (x_points[j + 1] - x_points[j])
                            y_interp = y_points[j] + ratio * (y_points[j + 1] - y_points[j])
                            lut[i] = int(np.clip(y_interp, 0, 255))
                            break
                    else:
                        # 如果i不在任何区间内，使用最近邻
                        lut[i] = y_points[0] if i < x_points[0] else y_points[-1]
            else:
                # 如果没有足够的点，使用线性映射
                lut = np.arange(256, dtype=np.uint8)

            # 应用查找表
            return cv2.LUT(channel, lut)

        except Exception as e:
            self.logger.error(f"通道曲线应用失败: {str(e)}")
            return channel.copy()

    def load_lut(self, lut_info: LUTInfo) -> bool:
        """加载LUT文件"""
        try:
            if not os.path.exists(lut_info.path):
                self.logger.error(f"LUT文件不存在: {lut_info.path}")
                return False

            # 根据格式加载LUT
            if lut_info.format == 'cube':
                lut_data = self._load_cube_lut(lut_info.path, lut_info.size)
            elif lut_info.format == '3dl':
                lut_data = self._load_3dl_lut(lut_info.path, lut_info.size)
            else:
                self.logger.error(f"不支持的LUT格式: {lut_info.format}")
                return False

            # 存储LUT数据
            with self.lut_lock:
                self.available_luts[lut_info.name] = lut_info
                self.loaded_luts[lut_info.name] = lut_data

            self.logger.info(f"LUT加载成功: {lut_info.name}")
            return True

        except Exception as e:
            self.logger.error(f"LUT加载失败: {str(e)}")
            return False

    def _load_cube_lut(self, lut_path: str, size: int) -> np.ndarray:
        """加载CUBE格式LUT"""
        try:
            with open(lut_path, 'r') as f:
                lines = f.readlines()

            # 解析LUT数据
            lut_data = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('TITLE'):
                    values = line.split()
                    if len(values) == 3:
                        r, g, b = map(float, values)
                        lut_data.append([r, g, b])

            # 转换为numpy数组
            lut_array = np.array(lut_data, dtype=np.float32)

            # 重塑为3D LUT
            lut_3d = lut_array.reshape(size, size, size, 3)

            return lut_3d

        except Exception as e:
            self.logger.error(f"CUBE LUT加载失败: {str(e)}")
            raise

    def _load_3dl_lut(self, lut_path: str, size: int) -> np.ndarray:
        """加载3DL格式LUT"""
        try:
            with open(lut_path, 'r') as f:
                lines = f.readlines()

            # 解析LUT数据
            lut_data = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    values = line.split()
                    if len(values) == 3:
                        r, g, b = map(float, values)
                        lut_data.append([r, g, b])

            # 转换为numpy数组
            lut_array = np.array(lut_data, dtype=np.float32)

            # 重塑为3D LUT
            lut_3d = lut_array.reshape(size, size, size, 3)

            return lut_3d

        except Exception as e:
            self.logger.error(f"3DL LUT加载失败: {str(e)}")
            raise

    def apply_lut(self, frame: np.ndarray, lut_name: str) -> np.ndarray:
        """应用LUT到帧"""
        try:
            with self.lut_lock:
                if lut_name not in self.loaded_luts:
                    self.logger.error(f"LUT未加载: {lut_name}")
                    return frame.copy()

                lut_data = self.loaded_luts[lut_name]
                lut_info = self.available_luts[lut_name]

            # 色彩空间转换
            if lut_info.input_space != self.settings.color_space:
                frame = self.convert_color_space(
                    frame,
                    self.settings.color_space,
                    lut_info.input_space
                )

            # 确保帧是float32格式
            if frame.dtype != np.float32:
                frame = frame.astype(np.float32) / 255.0

            # 应用LUT
            # 这里使用简化的LUT应用方法
            # 在实际实现中，应该使用更精确的三线性插值
            h, w, c = frame.shape
            flat_frame = frame.reshape(-1, c)

            # 简化的LUT应用（最近邻）
            size = lut_data.shape[0]
            indices = (flat_frame * (size - 1)).astype(int)
            indices = np.clip(indices, 0, size - 1)

            # 应用LUT
            lut_frame = np.zeros_like(flat_frame)
            for i in range(len(flat_frame)):
                r_idx, g_idx, b_idx = indices[i]
                lut_frame[i] = lut_data[r_idx, g_idx, b_idx]

            result_frame = lut_frame.reshape(h, w, c)

            # 转换回目标色彩空间
            if lut_info.output_space != self.settings.color_space:
                result_frame = self.convert_color_space(
                    result_frame,
                    lut_info.output_space,
                    self.settings.color_space
                )

            # 转换回uint8
            result_frame = (result_frame * 255).astype(np.uint8)

            return result_frame

        except Exception as e:
            self.logger.error(f"LUT应用失败: {str(e)}")
            return frame.copy()

    def apply_hsl_adjustment(self, frame: np.ndarray,
                           hue_shift: float = 0.0,
                           saturation: float = 1.0,
                           lightness: float = 1.0) -> np.ndarray:
        """应用HSL调整"""
        try:
            # 转换到HSL色彩空间
            hsl_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2HLS)
            h, l, s = cv2.split(hsl_frame)

            # 调整色相
            h = (h + hue_shift * 180) % 180

            # 调整饱和度
            s = np.clip(s * saturation, 0, 255)

            # 调整亮度
            l = np.clip(l * lightness, 0, 255)

            # 合并通道
            hsl_adjusted = cv2.merge([h, l, s])
            rgb_frame = cv2.cvtColor(hsl_adjusted, cv2.COLOR_HLS2RGB)

            return rgb_frame

        except Exception as e:
            self.logger.error(f"HSL调整失败: {str(e)}")
            return frame.copy()

    def apply_rgb_adjustment(self, frame: np.ndarray,
                           red_offset: float = 0.0,
                           green_offset: float = 0.0,
                           blue_offset: float = 0.0,
                           red_gain: float = 1.0,
                           green_gain: float = 1.0,
                           blue_gain: float = 1.0) -> np.ndarray:
        """应用RGB调整"""
        try:
            channels = list(cv2.split(frame))

            # 调整红色通道
            if len(channels) > 0:
                channels[0] = np.clip(channels[0] * red_gain + red_offset, 0, 255)

            # 调整绿色通道
            if len(channels) > 1:
                channels[1] = np.clip(channels[1] * green_gain + green_offset, 0, 255)

            # 调整蓝色通道
            if len(channels) > 2:
                channels[2] = np.clip(channels[2] * blue_gain + blue_offset, 0, 255)

            return cv2.merge(channels)

        except Exception as e:
            self.logger.error(f"RGB调整失败: {str(e)}")
            return frame.copy()

    def apply_contrast_brightness(self, frame: np.ndarray,
                                contrast: float = 1.0,
                                brightness: float = 0.0) -> np.ndarray:
        """应用对比度和亮度调整"""
        try:
            # 应用对比度和亮度
            adjusted = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)
            return adjusted

        except Exception as e:
            self.logger.error(f"对比度亮度调整失败: {str(e)}")
            return frame.copy()

    def apply_shadows_highlights(self, frame: np.ndarray,
                               shadows_amount: float = 0.0,
                               highlights_amount: float = 0.0,
                               shadows_tone_width: float = 50.0,
                               highlights_tone_width: float = 50.0) -> np.ndarray:
        """应用阴影高光调整"""
        try:
            # 转换为LAB色彩空间
            lab_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab_frame)

            # 归一化L通道到0-1
            l_norm = l.astype(np.float32) / 255.0

            # 创建阴影和高光蒙版
            shadow_mask = 1.0 - np.clip((l_norm - 0.5) / shadows_tone_width + 0.5, 0, 1)
            highlight_mask = np.clip((l_norm - 0.5) / highlights_tone_width + 0.5, 0, 1)

            # 应用阴影调整
            if shadows_amount != 0.0:
                l_adjusted = l + shadow_mask * shadows_amount * 50
                l = np.clip(l_adjusted, 0, 255).astype(np.uint8)

            # 应用高光调整
            if highlights_amount != 0.0:
                l_adjusted = l + highlight_mask * highlights_amount * 50
                l = np.clip(l_adjusted, 0, 255).astype(np.uint8)

            # 合并通道
            lab_adjusted = cv2.merge([l, a, b])
            rgb_frame = cv2.cvtColor(lab_adjusted, cv2.COLOR_LAB2RGB)

            return rgb_frame

        except Exception as e:
            self.logger.error(f"阴影高光调整失败: {str(e)}")
            return frame.copy()

    def generate_waveform(self, frame: np.ndarray,
                         width: int = 256,
                         height: int = 256) -> np.ndarray:
        """生成波形图"""
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

            # 计算波形图
            waveform = np.zeros((height, width), dtype=np.uint8)

            # 按列计算亮度分布
            for x in range(width):
                # 获取对应列的像素
                col_idx = int(x * frame.shape[1] / width)
                col_pixels = gray[:, col_idx]

                # 计算亮度直方图
                hist = np.histogram(col_pixels, bins=height, range=(0, 256))[0]

                # 归一化并绘制
                if hist.max() > 0:
                    hist_normalized = (hist / hist.max() * height).astype(int)
                    for y, intensity in enumerate(hist_normalized):
                        if intensity > 0:
                            waveform[height-intensity:height, x] = 255

            return waveform

        except Exception as e:
            self.logger.error(f"波形图生成失败: {str(e)}")
            return np.zeros((height, width), dtype=np.uint8)

    def generate_vectorscope(self, frame: np.ndarray,
                           width: int = 256,
                           height: int = 256) -> np.ndarray:
        """生成矢量图"""
        try:
            # 转换为YCrCb色彩空间
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_RGB2YCrCb)
            cr, cb = ycrcb[:, :, 1], ycrcb[:, :, 2]

            # 创建矢量图
            vectorscope = np.zeros((height, width), dtype=np.uint8)

            # 归一化CrCb到图像坐标
            cr_norm = ((cr - 128) / 128 * width/2 + width/2).astype(int)
            cb_norm = ((cb - 128) / 128 * height/2 + height/2).astype(int)

            # 确保坐标在范围内
            cr_norm = np.clip(cr_norm, 0, width-1)
            cb_norm = np.clip(cb_norm, 0, height-1)

            # 绘制点
            for i in range(len(cr_norm)):
                for j in range(len(cb_norm)):
                    vectorscope[cb_norm[i, j], cr_norm[i, j]] += 1

            # 归一化显示
            if vectorscope.max() > 0:
                vectorscope = (vectorscope / vectorscope.max() * 255).astype(np.uint8)

            return vectorscope

        except Exception as e:
            self.logger.error(f"矢量图生成失败: {str(e)}")
            return np.zeros((height, width), dtype=np.uint8)

    def generate_histogram(self, frame: np.ndarray,
                          width: int = 256,
                          height: int = 100) -> np.ndarray:
        """生成直方图"""
        try:
            # 分离通道
            channels = cv2.split(frame)
            colors = ['red', 'green', 'blue']

            # 创建直方图图像
            hist_image = np.zeros((height, width, 3), dtype=np.uint8)

            # 绘制每个通道的直方图
            for i, (channel, color) in enumerate(zip(channels, colors)):
                hist = cv2.calcHist([channel], [0], None, [256], [0, 256])

                # 归一化直方图
                if hist.max() > 0:
                    hist = hist / hist.max() * height

                # 绘制直方图
                hist_normalized = hist.astype(int)
                for x in range(width):
                    y = hist_normalized[x]
                    if y > 0:
                        color_val = 255 if color == 'red' else (255 if color == 'green' else 255)
                        hist_image[height-y:height, x] = [
                            color_val if color == 'red' else 0,
                            color_val if color == 'green' else 0,
                            color_val if color == 'blue' else 0
                        ]

            return hist_image

        except Exception as e:
            self.logger.error(f"直方图生成失败: {str(e)}")
            return np.zeros((height, width, 3), dtype=np.uint8)

    def _apply_operations(self, frame: np.ndarray,
                         operations: List[ColorGradingOperation]) -> np.ndarray:
        """应用色彩分级操作栈"""
        try:
            result_frame = frame.copy()

            for operation in operations:
                if not operation.enabled:
                    continue

                # 根据操作类型应用不同的调整
                if operation.operation_type == ColorGradingTool.WHEEL:
                    adjustment = ColorWheelAdjustment.from_dict(operation.parameters)
                    result_frame = self.apply_color_wheel(result_frame, adjustment)

                elif operation.operation_type == ColorGradingTool.CURVE:
                    curve = ColorCurve.from_dict(operation.parameters)
                    result_frame = self.apply_color_curve(result_frame, curve)

                elif operation.operation_type == ColorGradingTool.LUT:
                    lut_name = operation.parameters.get('lut_name')
                    if lut_name:
                        result_frame = self.apply_lut(result_frame, lut_name)

                elif operation.operation_type == ColorGradingTool.HSL:
                    result_frame = self.apply_hsl_adjustment(
                        result_frame,
                        hue_shift=operation.parameters.get('hue_shift', 0.0),
                        saturation=operation.parameters.get('saturation', 1.0),
                        lightness=operation.parameters.get('lightness', 1.0)
                    )

                elif operation.operation_type == ColorGradingTool.RGB:
                    result_frame = self.apply_rgb_adjustment(
                        result_frame,
                        red_offset=operation.parameters.get('red_offset', 0.0),
                        green_offset=operation.parameters.get('green_offset', 0.0),
                        blue_offset=operation.parameters.get('blue_offset', 0.0),
                        red_gain=operation.parameters.get('red_gain', 1.0),
                        green_gain=operation.parameters.get('green_gain', 1.0),
                        blue_gain=operation.parameters.get('blue_gain', 1.0)
                    )

                elif operation.operation_type == ColorGradingTool.CONTRAST:
                    result_frame = self.apply_contrast_brightness(
                        result_frame,
                        contrast=operation.parameters.get('contrast', 1.0),
                        brightness=operation.parameters.get('brightness', 0.0)
                    )

                elif operation.operation_type == ColorGradingTool.SHADOWS_HIGHLIGHTS:
                    result_frame = self.apply_shadows_highlights(
                        result_frame,
                        shadows_amount=operation.parameters.get('shadows_amount', 0.0),
                        highlights_amount=operation.parameters.get('highlights_amount', 0.0),
                        shadows_tone_width=operation.parameters.get('shadows_tone_width', 50.0),
                        highlights_tone_width=operation.parameters.get('highlights_tone_width', 50.0)
                    )

                # 应用透明度
                if operation.opacity < 1.0:
                    result_frame = cv2.addWeighted(
                        frame, 1 - operation.opacity,
                        result_frame, operation.opacity,
                        0
                    )

                # 更新帧用于下一个操作
                frame = result_frame.copy()

            return result_frame

        except Exception as e:
            self.logger.error(f"操作应用失败: {str(e)}")
            return frame.copy()

    def process_frame(self, frame: np.ndarray,
                     operations: Optional[List[ColorGradingOperation]] = None,
                     frame_id: Optional[str] = None) -> np.ndarray:
        """处理单帧"""
        try:
            if operations is None:
                with self.operation_lock:
                    operations = self.operation_stack.copy()

            # 检查缓存
            if self.settings.cache_enabled and frame_id:
                cache_key = f"{frame_id}_{hash(str(operations))}"
                with self.cache_lock:
                    if cache_key in self.frame_cache:
                        return self.frame_cache[cache_key]

            # 处理帧
            processed_frame = self._apply_operations(frame, operations)

            # 缓存结果
            if self.settings.cache_enabled and frame_id:
                with self.cache_lock:
                    self.frame_cache[cache_key] = processed_frame

                    # 清理缓存
                    if len(self.frame_cache) > 1000:  # 限制缓存大小
                        oldest_key = next(iter(self.frame_cache))
                        del self.frame_cache[oldest_key]

            return processed_frame

        except Exception as e:
            self.logger.error(f"帧处理失败: {str(e)}")
            return frame.copy()

    def add_operation(self, operation: ColorGradingOperation) -> None:
        """添加色彩分级操作"""
        with self.operation_lock:
            self.operation_stack.append(operation)

        self.event_bus.publish("operation_added", operation)
        self.logger.info(f"色彩分级操作已添加: {operation.operation_type.value}")

    def remove_operation(self, operation_id: str) -> bool:
        """移除色彩分级操作"""
        with self.operation_lock:
            for i, operation in enumerate(self.operation_stack):
                if operation.id == operation_id:
                    removed_operation = self.operation_stack.pop(i)
                    self.event_bus.publish("operation_removed", removed_operation)
                    self.logger.info(f"色彩分级操作已移除: {operation.operation_type.value}")
                    return True

        return False

    def get_operations(self) -> List[ColorGradingOperation]:
        """获取当前操作栈"""
        with self.operation_lock:
            return self.operation_stack.copy()

    def clear_operations(self) -> None:
        """清空操作栈"""
        with self.operation_lock:
            self.operation_stack.clear()

        self.event_bus.publish("operations_cleared", None)
        self.logger.info("色彩分级操作栈已清空")

    def save_preset(self, name: str, description: str = "") -> bool:
        """保存当前设置为预设"""
        try:
            with self.operation_lock:
                preset_operations = [op.to_dict() for op in self.operation_stack]

            preset = ColorGradePreset(
                name=name,
                description=description,
                adjustments={'operations': preset_operations}
            )

            with self.preset_lock:
                self.presets[name] = preset

            self.event_bus.publish("preset_saved", preset)
            self.logger.info(f"预设已保存: {name}")
            return True

        except Exception as e:
            self.logger.error(f"预设保存失败: {str(e)}")
            return False

    def load_preset(self, name: str) -> bool:
        """加载预设"""
        try:
            with self.preset_lock:
                if name not in self.presets:
                    self.logger.error(f"预设不存在: {name}")
                    return False

                preset = self.presets[name]

            # 清空当前操作
            self.clear_operations()

            # 加载预设操作
            operations_data = preset.adjustments.get('operations', [])
            operations = []

            for op_data in operations_data:
                operation = ColorGradingOperation.from_dict(op_data)
                operations.append(operation)

            with self.operation_lock:
                self.operation_stack.extend(operations)

            self.event_bus.publish("preset_loaded", preset)
            self.logger.info(f"预设已加载: {name}")
            return True

        except Exception as e:
            self.logger.error(f"预设加载失败: {str(e)}")
            return False

    def get_available_presets(self) -> List[str]:
        """获取可用预设列表"""
        with self.preset_lock:
            return list(self.presets.keys())

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.performance_metrics.copy()

    def optimize_performance(self) -> None:
        """优化性能"""
        try:
            # 根据硬件配置调整设置
            if self.hardware_acceleration:
                hw_metrics = self.hardware_acceleration.get_performance_metrics()

                # 根据GPU使用率调整处理线程数
                if hw_metrics.gpu_usage > 80:
                    self.thread_pool._max_workers = max(1, self.thread_pool._max_workers - 1)
                elif hw_metrics.gpu_usage < 30:
                    self.thread_pool._max_workers = min(8, self.thread_pool._max_workers + 1)

            self.logger.info("性能优化完成")

        except Exception as e:
            self.logger.error(f"性能优化失败: {str(e)}")

    def export_settings(self, file_path: str) -> bool:
        """导出设置到文件"""
        try:
            settings_data = {
                'engine_settings': self.settings.to_dict(),
                'operations': [op.to_dict() for op in self.get_operations()],
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
        """从文件导入设置"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"设置文件不存在: {file_path}")
                return False

            with open(file_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)

            # 导入引擎设置
            if 'engine_settings' in settings_data:
                self.settings = ColorGradingSettings.from_dict(settings_data['engine_settings'])

            # 导入操作
            if 'operations' in settings_data:
                self.clear_operations()
                operations = []
                for op_data in settings_data['operations']:
                    operation = ColorGradingOperation.from_dict(op_data)
                    operations.append(operation)

                with self.operation_lock:
                    self.operation_stack.extend(operations)

            # 导入预设
            if 'presets' in settings_data:
                with self.preset_lock:
                    for name, preset_data in settings_data['presets'].items():
                        self.presets[name] = ColorGradePreset.from_dict(preset_data)

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
            with self.cache_lock:
                self.frame_cache.clear()

            # 清理LUT
            with self.lut_lock:
                self.loaded_luts.clear()

            self.logger.info("色彩分级引擎清理完成")

        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局色彩分级引擎实例
_color_grading_engine: Optional[ColorGradingEngine] = None


def get_color_grading_engine(settings: Optional[ColorGradingSettings] = None) -> ColorGradingEngine:
    """获取全局色彩分级引擎实例"""
    global _color_grading_engine
    if _color_grading_engine is None:
        _color_grading_engine = ColorGradingEngine(settings)
    return _color_grading_engine


def cleanup_color_grading_engine() -> None:
    """清理全局色彩分级引擎实例"""
    global _color_grading_engine
    if _color_grading_engine is not None:
        _color_grading_engine.cleanup()
        _color_grading_engine = None