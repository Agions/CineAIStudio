#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio LUT Manager System
专业LUT管理系统，提供LUT生成、应用、分析和转换功能
"""

import os
import numpy as np
import cv2
import json
import math
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import logging

from .logger import get_logger
from .event_system import EventBus
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from .color_grading_engine import ColorSpace, ColorGradingTool, ColorCurve
from .color_science import ColorScienceEngine
from .hdr_processing_engine import HDRProcessingEngine


class LUTFormat(Enum):
    """LUT格式枚举"""
    CUBE = "cube"      # .cube格式
    THREE_DL = "3dl"   # .3dl格式
    LOOK = "look"      # .look格式
    CSP = "csp"        # .csp格式
    MGA = "mga"        # .mga格式
    ICC = "icc"        # .icc配置文件


class LUTType(Enum):
    """LUT类型枚举"""
    ONE_D = "1d"       # 1D LUT
    THREE_D = "3d"     # 3D LUT
    SHAPER = "shaper"  # Shaper LUT
    MATRIX = "matrix"  # 矩阵LUT


class LUTInterpolation(Enum):
    """LUT插值方法枚举"""
    NEAREST = "nearest"
    LINEAR = "linear"
    TETRAHEDRAL = "tetrahedral"
    TRILINEAR = "trilinear"


@dataclass
class LUTInfo:
    """LUT信息数据类"""
    name: str
    path: str
    format: LUTFormat
    type: LUTType
    size: int = 33
    input_bit_depth: int = 8
    output_bit_depth: int = 8
    input_space: ColorSpace = ColorSpace.REC709
    output_space: ColorSpace = ColorSpace.REC709
    title: str = ""
    description: str = ""
    manufacturer: str = ""
    created_date: str = ""
    modified_date: str = ""
    interpolation: LUTInterpolation = LUTInterpolation.TRILINEAR
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'path': self.path,
            'format': self.format.value,
            'type': self.type.value,
            'size': self.size,
            'input_bit_depth': self.input_bit_depth,
            'output_bit_depth': self.output_bit_depth,
            'input_space': self.input_space.value,
            'output_space': self.output_space.value,
            'title': self.title,
            'description': self.description,
            'manufacturer': self.manufacturer,
            'created_date': self.created_date,
            'modified_date': self.modified_date,
            'interpolation': self.interpolation.value,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LUTInfo':
        """从字典创建"""
        return cls(
            name=data['name'],
            path=data['path'],
            format=LUTFormat(data['format']),
            type=LUTType(data['type']),
            size=data.get('size', 33),
            input_bit_depth=data.get('input_bit_depth', 8),
            output_bit_depth=data.get('output_bit_depth', 8),
            input_space=ColorSpace(data.get('input_space', 'rec709')),
            output_space=ColorSpace(data.get('output_space', 'rec709')),
            title=data.get('title', ''),
            description=data.get('description', ''),
            manufacturer=data.get('manufacturer', ''),
            created_date=data.get('created_date', ''),
            modified_date=data.get('modified_date', ''),
            interpolation=LUTInterpolation(data.get('interpolation', 'trilinear')),
            metadata=data.get('metadata', {})
        )


@dataclass
class LUTGenerationParams:
    """LUT生成参数数据类"""
    size: int = 33
    input_space: ColorSpace = ColorSpace.REC709
    output_space: ColorSpace = ColorSpace.REC709
    interpolation: LUTInterpolation = LUTInterpolation.TRILINEAR
    bit_depth: int = 32
    include_metadata: bool = True
    include_title: bool = True
    precision: int = 6  # 小数位数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'size': self.size,
            'input_space': self.input_space.value,
            'output_space': self.output_space.value,
            'interpolation': self.interpolation.value,
            'bit_depth': self.bit_depth,
            'include_metadata': self.include_metadata,
            'include_title': self.include_title,
            'precision': self.precision
        }


class LUTManager:
    """LUT管理器"""

    def __init__(self, logger=None):
        """初始化LUT管理器"""
        self.logger = logger or get_logger("LUTManager")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.color_science = ColorScienceEngine()
        self.hdr_engine = HDRProcessingEngine()

        # LUT存储
        self.available_luts: Dict[str, LUTInfo] = {}
        self.loaded_luts: Dict[str, np.ndarray] = {}
        self.lut_cache: Dict[str, np.ndarray] = {}

        # 生成参数
        self.default_generation_params = LUTGenerationParams()

        # 线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.processing_lock = threading.Lock()

        # 性能监控
        self.performance_metrics = {
            'luts_loaded': 0,
            'luts_generated': 0,
            'total_processing_time': 0.0,
            'cache_hit_rate': 0.0
        }

        # 初始化
        self._initialize()

    def _initialize(self) -> None:
        """初始化LUT管理器"""
        try:
            # 创建LUT目录
            self.lut_dir = os.path.join(os.path.dirname(__file__), "luts")
            os.makedirs(self.lut_dir, exist_ok=True)

            # 创建临时目录
            self.temp_dir = os.path.join(self.lut_dir, "temp")
            os.makedirs(self.temp_dir, exist_ok=True)

            # 扫描现有LUT
            self._scan_existing_luts()

            self.logger.info("LUT管理器初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"LUT管理器初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="LUTManager",
                    operation="initialize"
                ),
                user_message="LUT管理器初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _scan_existing_luts(self) -> None:
        """扫描现有LUT文件"""
        try:
            lut_count = 0

            # 扫描.cube文件
            for cube_file in Path(self.lut_dir).glob("*.cube"):
                try:
                    lut_info = self._analyze_cube_lut(str(cube_file))
                    self.available_luts[lut_info.name] = lut_info
                    lut_count += 1
                except Exception as e:
                    self.logger.warning(f"无法分析LUT文件 {cube_file}: {str(e)}")

            # 扫描.3dl文件
            for _3dl_file in Path(self.lut_dir).glob("*.3dl"):
                try:
                    lut_info = self._analyze_3dl_lut(str(_3dl_file))
                    self.available_luts[lut_info.name] = lut_info
                    lut_count += 1
                except Exception as e:
                    self.logger.warning(f"无法分析LUT文件 {_3dl_file}: {str(e)}")

            self.logger.info(f"扫描完成，发现 {lut_count} 个LUT文件")

        except Exception as e:
            self.logger.error(f"LUT扫描失败: {str(e)}")

    def load_lut(self, lut_path: str, lut_name: Optional[str] = None) -> bool:
        """加载LUT文件"""
        try:
            if not os.path.exists(lut_path):
                self.logger.error(f"LUT文件不存在: {lut_path}")
                return False

            start_time = time.time()

            # 确定LUT格式
            file_ext = Path(lut_path).suffix.lower()
            if file_ext == '.cube':
                lut_data, lut_info = self._load_cube_lut(lut_path)
            elif file_ext == '.3dl':
                lut_data, lut_info = self._load_3dl_lut(lut_path)
            else:
                self.logger.error(f"不支持的LUT格式: {file_ext}")
                return False

            # 使用提供的名称或从文件名生成
            if lut_name:
                lut_info.name = lut_name
            elif not lut_info.name:
                lut_info.name = Path(lut_path).stem

            lut_info.path = lut_path

            # 存储LUT
            with self.processing_lock:
                self.available_luts[lut_info.name] = lut_info
                self.loaded_luts[lut_info.name] = lut_data

            # 更新性能指标
            processing_time = time.time() - start_time
            self._update_performance_metrics('load', processing_time)

            self.logger.info(f"LUT加载成功: {lut_info.name}")
            return True

        except Exception as e:
            self.logger.error(f"LUT加载失败: {str(e)}")
            return False

    def _load_cube_lut(self, lut_path: str) -> Tuple[np.ndarray, LUTInfo]:
        """加载CUBE格式LUT"""
        try:
            with open(lut_path, 'r') as f:
                lines = f.readlines()

            # 解析LUT信息
            lut_info = LUTInfo(
                name="",
                path=lut_path,
                format=LUTFormat.CUBE,
                type=LUTType.THREE_D,
                interpolation=LUTInterpolation.TRILINEAR
            )

            lut_data = []
            size = 0

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 解析标题行
                if line.startswith('TITLE'):
                    lut_info.title = line.split('"')[1] if '"' in line else line.split(' ', 1)[1]

                # 解析LUT尺寸
                elif line.startswith('LUT_3D_SIZE'):
                    size = int(line.split(' ')[1])
                    lut_info.size = size

                # 解析数据行
                elif ' ' in line and not line.startswith(('TITLE', 'LUT_3D_SIZE')):
                    values = line.split()
                    if len(values) == 3:
                        r, g, b = map(float, values)
                        lut_data.append([r, g, b])

            # 转换为3D数组
            lut_array = np.array(lut_data, dtype=np.float32)
            if size > 0:
                lut_array = lut_array.reshape(size, size, size, 3)

            return lut_array, lut_info

        except Exception as e:
            self.logger.error(f"CUBE LUT加载失败: {str(e)}")
            raise

    def _load_3dl_lut(self, lut_path: str) -> Tuple[np.ndarray, LUTInfo]:
        """加载3DL格式LUT"""
        try:
            with open(lut_path, 'r') as f:
                lines = f.readlines()

            lut_info = LUTInfo(
                name="",
                path=lut_path,
                format=LUTFormat.THREE_DL,
                type=LUTType.THREE_D,
                interpolation=LUTInterpolation.TRILINEAR
            )

            lut_data = []
            size = 0

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 解析网格信息
                if line.startswith('3DMESH'):
                    parts = line.split()
                    if len(parts) >= 4:
                        size = int(parts[1])
                        lut_info.size = size

                # 解析数据行
                elif '\t' in line or '   ' in line:
                    values = line.replace('\t', ' ').split()
                    if len(values) == 3:
                        r, g, b = map(float, values)
                        lut_data.append([r, g, b])

            # 转换为3D数组
            lut_array = np.array(lut_data, dtype=np.float32)
            if size > 0:
                lut_array = lut_array.reshape(size, size, size, 3)

            return lut_array, lut_info

        except Exception as e:
            self.logger.error(f"3DL LUT加载失败: {str(e)}")
            raise

    def _analyze_cube_lut(self, lut_path: str) -> LUTInfo:
        """分析CUBE LUT文件信息"""
        try:
            with open(lut_path, 'r') as f:
                content = f.read()

            lut_info = LUTInfo(
                name=Path(lut_path).stem,
                path=lut_path,
                format=LUTFormat.CUBE,
                type=LUTType.THREE_D,
                size=33,
                interpolation=LUTInterpolation.TRILINEAR
            )

            # 解析标题
            if 'TITLE' in content:
                title_line = [line for line in content.split('\n') if line.startswith('TITLE')]
                if title_line:
                    title = title_line[0]
                    if '"' in title:
                        lut_info.title = title.split('"')[1]
                    else:
                        lut_info.title = title.split(' ', 1)[1]

            # 解析尺寸
            if 'LUT_3D_SIZE' in content:
                size_line = [line for line in content.split('\n') if line.startswith('LUT_3D_SIZE')]
                if size_line:
                    lut_info.size = int(size_line[0].split(' ')[1])

            return lut_info

        except Exception as e:
            self.logger.error(f"CUBE LUT分析失败: {str(e)}")
            return LUTInfo(name=Path(lut_path).stem, path=lut_path, format=LUTFormat.CUBE, type=LUTType.THREE_D)

    def _analyze_3dl_lut(self, lut_path: str) -> LUTInfo:
        """分析3DL LUT文件信息"""
        try:
            with open(lut_path, 'r') as f:
                content = f.read()

            lut_info = LUTInfo(
                name=Path(lut_path).stem,
                path=lut_path,
                format=LUTFormat.THREE_DL,
                type=LUTType.THREE_D,
                size=33,
                interpolation=LUTInterpolation.TRILINEAR
            )

            # 解析网格信息
            if '3DMESH' in content:
                mesh_line = [line for line in content.split('\n') if line.startswith('3DMESH')]
                if mesh_line:
                    parts = mesh_line[0].split()
                    if len(parts) >= 4:
                        lut_info.size = int(parts[1])

            return lut_info

        except Exception as e:
            self.logger.error(f"3DL LUT分析失败: {str(e)}")
            return LUTInfo(name=Path(lut_path).stem, path=lut_path, format=LUTFormat.THREE_DL, type=LUTType.THREE_D)

    def generate_lut_from_operations(self, operations: List[Dict[str, Any]],
                                  params: Optional[LUTGenerationParams] = None) -> Tuple[np.ndarray, LUTInfo]:
        """从操作生成LUT"""
        try:
            start_time = time.time()

            # 使用提供的参数或默认参数
            generation_params = params or self.default_generation_params

            # 创建3D LUT网格
            lut_data = self._create_3d_lut_grid(generation_params.size)

            # 应用操作到每个网格点
            processed_lut = self._apply_operations_to_lut(lut_data, operations, generation_params)

            # 创建LUT信息
            lut_info = LUTInfo(
                name=f"generated_{int(time.time())}",
                path="",
                format=LUTFormat.CUBE,
                type=LUTType.THREE_D,
                size=generation_params.size,
                input_space=generation_params.input_space,
                output_space=generation_params.output_space,
                interpolation=generation_params.interpolation,
                title="Generated LUT",
                description=f"Generated from {len(operations)} operations",
                created_date=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={
                    'generation_params': generation_params.to_dict(),
                    'operations': operations,
                    'generated_by': 'CineAIStudio'
                }
            )

            # 更新性能指标
            processing_time = time.time() - start_time
            self._update_performance_metrics('generate', processing_time)

            return processed_lut, lut_info

        except Exception as e:
            self.logger.error(f"LUT生成失败: {str(e)}")
            raise

    def _create_3d_lut_grid(self, size: int) -> np.ndarray:
        """创建3D LUT网格"""
        try:
            # 创建RGB网格点
            grid_points = []
            step = 1.0 / (size - 1)

            for r in range(size):
                for g in range(size):
                    for b in range(size):
                        grid_points.append([
                            r * step,
                            g * step,
                            b * step
                        ])

            return np.array(grid_points, dtype=np.float32)

        except Exception as e:
            self.logger.error(f"3D LUT网格创建失败: {str(e)}")
            raise

    def _apply_operations_to_lut(self, lut_data: np.ndarray,
                                 operations: List[Dict[str, Any]],
                                 params: LUTGenerationParams) -> np.ndarray:
        """将操作应用到LUT数据"""
        try:
            processed_data = lut_data.copy()

            for operation in operations:
                operation_type = operation.get('type')
                operation_params = operation.get('parameters', {})

                if operation_type == 'color_wheel':
                    processed_data = self._apply_color_wheel_to_lut(processed_data, operation_params)
                elif operation_type == 'curve':
                    processed_data = self._apply_curve_to_lut(processed_data, operation_params)
                elif operation_type == 'contrast':
                    processed_data = self._apply_contrast_to_lut(processed_data, operation_params)
                elif operation_type == 'hsl':
                    processed_data = self._apply_hsl_to_lut(processed_data, operation_params)
                elif operation_type == 'rgb':
                    processed_data = self._apply_rgb_to_lut(processed_data, operation_params)
                elif operation_type == 'lut':
                    processed_data = self._apply_lut_to_lut(processed_data, operation_params)
                elif operation_type == 'tone_mapping':
                    processed_data = self._apply_tone_mapping_to_lut(processed_data, operation_params)

            # 色彩空间转换
            if params.input_space != params.output_space:
                processed_data = self._apply_color_space_conversion_to_lut(
                    processed_data, params.input_space, params.output_space
                )

            # 重塑为3D数组
            size = params.size
            processed_3d = processed_data.reshape(size, size, size, 3)

            return processed_3d

        except Exception as e:
            self.logger.error(f"操作应用到LUT失败: {str(e)}")
            raise

    def _apply_color_wheel_to_lut(self, lut_data: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """应用色轮调整到LUT"""
        try:
            shadows = params.get('shadows', (0.0, 0.0, 0.0))
            midtones = params.get('midtones', (0.0, 0.0, 0.0))
            highlights = params.get('highlights', (0.0, 0.0, 0.0))

            # 简化的色轮应用
            # 在实际实现中，应该使用更精确的方法
            processed_data = lut_data.copy()

            # 应用中间调调整（简化）
            hue_shift, sat_shift, gamma_shift = midtones
            if hue_shift != 0.0 or sat_shift != 0.0 or gamma_shift != 0.0:
                # 转换到HSV色彩空间
                hsv_data = self._rgb_to_hsv(processed_data)
                hsv_data[:, 0] = (hsv_data[:, 0] + hue_shift * 180) % 180
                hsv_data[:, 1] = np.clip(hsv_data[:, 1] * (1 + sat_shift), 0, 255)
                hsv_data[:, 2] = np.clip(hsv_data[:, 2] * (1 + gamma_shift), 0, 255)
                processed_data = self._hsv_to_rgb(hsv_data)

            return processed_data

        except Exception as e:
            self.logger.error(f"色轮应用到LUT失败: {str(e)}")
            return lut_data.copy()

    def _apply_curve_to_lut(self, lut_data: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """应用曲线调整到LUT"""
        try:
            curve_type = params.get('curve_type', 'luma')
            points = params.get('points', [])

            if not points:
                return lut_data.copy()

            # 创建曲线查找表
            lut_size = 256
            curve_lut = np.zeros(lut_size, dtype=np.float32)

            # 插值曲线点
            x_points = [int(p[0] * 255) for p in points]
            y_points = [int(p[1] * 255) for p in points]

            # 线性插值
            for i in range(lut_size):
                for j in range(len(x_points) - 1):
                    if x_points[j] <= i <= x_points[j + 1]:
                        ratio = (i - x_points[j]) / (x_points[j + 1] - x_points[j])
                        y_interp = y_points[j] + ratio * (y_points[j + 1] - y_points[j])
                        curve_lut[i] = y_interp / 255.0
                        break

            # 应用曲线
            processed_data = lut_data.copy()
            if curve_type == 'luma':
                # 亮度曲线
                luminance = self._calculate_luminance(processed_data)
                adjusted_luminance = curve_lut[(luminance * 255).astype(int)]
                ratio = adjusted_luminance / (luminance + 1e-8)
                processed_data = processed_data * ratio[:, np.newaxis]

            elif curve_type in ['red', 'green', 'blue']:
                # 单通道曲线
                channel_idx = {'red': 0, 'green': 1, 'blue': 2}[curve_type]
                processed_data[:, channel_idx] = curve_lut[(processed_data[:, channel_idx] * 255).astype(int)]

            elif curve_type == 'rgb':
                # RGB曲线
                for i in range(3):
                    processed_data[:, i] = curve_lut[(processed_data[:, i] * 255).astype(int)]

            return processed_data

        except Exception as e:
            self.logger.error(f"曲线应用到LUT失败: {str(e)}")
            return lut_data.copy()

    def _apply_contrast_to_lut(self, lut_data: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """应用对比度调整到LUT"""
        try:
            contrast = params.get('contrast', 1.0)
            brightness = params.get('brightness', 0.0)

            # 应用对比度和亮度
            processed_data = lut_data * contrast + brightness

            return np.clip(processed_data, 0, 1)

        except Exception as e:
            self.logger.error(f"对比度应用到LUT失败: {str(e)}")
            return lut_data.copy()

    def _apply_hsl_to_lut(self, lut_data: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """应用HSL调整到LUT"""
        try:
            hue_shift = params.get('hue_shift', 0.0)
            saturation = params.get('saturation', 1.0)
            lightness = params.get('lightness', 1.0)

            # 转换到HSL色彩空间
            hsv_data = self._rgb_to_hsv(lut_data)
            hsv_data[:, 0] = (hsv_data[:, 0] + hue_shift * 180) % 180
            hsv_data[:, 1] = np.clip(hsv_data[:, 1] * saturation, 0, 255)
            hsv_data[:, 2] = np.clip(hsv_data[:, 2] * lightness, 0, 255)
            processed_data = self._hsv_to_rgb(hsv_data)

            return processed_data

        except Exception as e:
            self.logger.error(f"HSL应用到LUT失败: {str(e)}")
            return lut_data.copy()

    def _apply_rgb_to_lut(self, lut_data: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """应用RGB调整到LUT"""
        try:
            red_offset = params.get('red_offset', 0.0)
            green_offset = params.get('green_offset', 0.0)
            blue_offset = params.get('blue_offset', 0.0)
            red_gain = params.get('red_gain', 1.0)
            green_gain = params.get('green_gain', 1.0)
            blue_gain = params.get('blue_gain', 1.0)

            processed_data = lut_data.copy()
            processed_data[:, 0] = np.clip(processed_data[:, 0] * red_gain + red_offset, 0, 1)
            processed_data[:, 1] = np.clip(processed_data[:, 1] * green_gain + green_offset, 0, 1)
            processed_data[:, 2] = np.clip(processed_data[:, 2] * blue_gain + blue_offset, 0, 1)

            return processed_data

        except Exception as e:
            self.logger.error(f"RGB应用到LUT失败: {str(e)}")
            return lut_data.copy()

    def _apply_lut_to_lut(self, lut_data: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """应用LUT到LUT"""
        try:
            lut_name = params.get('lut_name')
            if not lut_name or lut_name not in self.loaded_luts:
                return lut_data.copy()

            source_lut = self.loaded_luts[lut_name]
            lut_intensity = params.get('intensity', 1.0)

            # 应用LUT
            processed_data = self._apply_3d_lut(lut_data, source_lut, lut_intensity)

            return processed_data

        except Exception as e:
            self.logger.error(f"LUT应用到LUT失败: {str(e)}")
            return lut_data.copy()

    def _apply_tone_mapping_to_lut(self, lut_data: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """应用色调映射到LUT"""
        try:
            method = params.get('method', 'reinhard')
            target_luminance = params.get('target_luminance', 100.0)

            # 简化的色调映射
            processed_data = lut_data.copy()

            if method == 'reinhard':
                # Reinhard色调映射
                luminance = self._calculate_luminance(processed_data)
                mapped_luminance = luminance / (1 + luminance)
                ratio = mapped_luminance / (luminance + 1e-8)
                processed_data = processed_data * ratio[:, np.newaxis]

            # 缩放到目标亮度
            processed_data = processed_data * (target_luminance / 1000.0)

            return np.clip(processed_data, 0, 1)

        except Exception as e:
            self.logger.error(f"色调映射应用到LUT失败: {str(e)}")
            return lut_data.copy()

    def _apply_color_space_conversion_to_lut(self, lut_data: np.ndarray,
                                            input_space: ColorSpace,
                                            output_space: ColorSpace) -> np.ndarray:
        """应用色彩空间转换到LUT"""
        try:
            # 使用色彩科学引擎进行转换
            processed_data = np.zeros_like(lut_data)

            for i in range(len(lut_data)):
                pixel = lut_data[i].reshape(1, 1, 3)
                converted_pixel = self.color_science.convert_color_space(
                    pixel, input_space.value, output_space.value
                )
                processed_data[i] = converted_pixel.reshape(3)

            return processed_data

        except Exception as e:
            self.logger.error(f"色彩空间转换到LUT失败: {str(e)}")
            return lut_data.copy()

    def _rgb_to_hsv(self, rgb_data: np.ndarray) -> np.ndarray:
        """RGB转HSV"""
        try:
            # 转换为uint8格式
            rgb_uint8 = (rgb_data * 255).astype(np.uint8)
            # 转换为HSV
            hsv_data = cv2.cvtColor(rgb_uint8.reshape(1, -1, 3), cv2.COLOR_RGB2HSV)
            return hsv_data.reshape(-1, 3)

        except Exception as e:
            self.logger.error(f"RGB转HSV失败: {str(e)}")
            return rgb_data

    def _hsv_to_rgb(self, hsv_data: np.ndarray) -> np.ndarray:
        """HSV转RGB"""
        try:
            # 转换为RGB
            rgb_uint8 = cv2.cvtColor(hsv_data.reshape(1, -1, 3), cv2.COLOR_HSV2RGB)
            # 转换为float32格式
            return rgb_uint8.reshape(-1, 3).astype(np.float32) / 255.0

        except Exception as e:
            self.logger.error(f"HSV转RGB失败: {str(e)}")
            return hsv_data

    def _calculate_luminance(self, data: np.ndarray) -> np.ndarray:
        """计算亮度"""
        return 0.2126 * data[:, 0] + 0.7152 * data[:, 1] + 0.0722 * data[:, 2]

    def _apply_3d_lut(self, data: np.ndarray, lut_3d: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        """应用3D LUT"""
        try:
            processed_data = np.zeros_like(data)
            size = lut_3d.shape[0]

            for i, pixel in enumerate(data):
                # 计算LUT坐标
                coords = pixel * (size - 1)
                r_idx, g_idx, b_idx = coords.astype(int)
                r_idx = np.clip(r_idx, 0, size - 1)
                g_idx = np.clip(g_idx, 0, size - 1)
                b_idx = np.clip(b_idx, 0, size - 1)

                # 获取LUT值
                lut_value = lut_3d[r_idx, g_idx, b_idx]

                # 混合原始值和LUT值
                processed_data[i] = pixel * (1 - intensity) + lut_value * intensity

            return processed_data

        except Exception as e:
            self.logger.error(f"3D LUT应用失败: {str(e)}")
            return data

    def save_lut(self, lut_data: np.ndarray, lut_info: LUTInfo,
                output_path: str, format: LUTFormat = LUTFormat.CUBE) -> bool:
        """保存LUT文件"""
        try:
            start_time = time.time()

            if format == LUTFormat.CUBE:
                success = self._save_cube_lut(lut_data, lut_info, output_path)
            elif format == LUTFormat.THREE_DL:
                success = self._save_3dl_lut(lut_data, lut_info, output_path)
            else:
                self.logger.error(f"不支持的保存格式: {format.value}")
                return False

            if success:
                # 更新LUT信息
                lut_info.path = output_path
                lut_info.format = format
                lut_info.modified_date = time.strftime("%Y-%m-%d %H:%M:%S")

                # 添加到可用LUT
                with self.processing_lock:
                    self.available_luts[lut_info.name] = lut_info
                    self.loaded_luts[lut_info.name] = lut_data

                # 更新性能指标
                processing_time = time.time() - start_time
                self._update_performance_metrics('save', processing_time)

                self.logger.info(f"LUT保存成功: {output_path}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"LUT保存失败: {str(e)}")
            return False

    def _save_cube_lut(self, lut_data: np.ndarray, lut_info: LUTInfo, output_path: str) -> bool:
        """保存CUBE格式LUT"""
        try:
            with open(output_path, 'w') as f:
                # 写入标题
                if lut_info.title:
                    f.write(f'TITLE "{lut_info.title}"\n')

                # 写入LUT信息
                f.write('\n')
                if lut_info.metadata:
                    for key, value in lut_info.metadata.items():
                        f.write(f'# {key}: {value}\n')
                f.write('\n')

                # 写入LUT尺寸
                size = lut_data.shape[0]
                f.write(f'LUT_3D_SIZE {size}\n\n')

                # 写入LUT数据
                precision = getattr(lut_info.metadata.get('generation_params', {}), 'precision', 6)
                for r in range(size):
                    for g in range(size):
                        for b in range(size):
                            pixel = lut_data[r, g, b]
                            f.write(f'{pixel[0]:.{precision}f} {pixel[1]:.{precision}f} {pixel[2]:.{precision}f}\n')

            return True

        except Exception as e:
            self.logger.error(f"CUBE LUT保存失败: {str(e)}")
            return False

    def _save_3dl_lut(self, lut_data: np.ndarray, lut_info: LUTInfo, output_path: str) -> bool:
        """保存3DL格式LUT"""
        try:
            with open(output_path, 'w') as f:
                # 写入标题和元数据
                if lut_info.title:
                    f.write(f'# {lut_info.title}\n')
                f.write('# Generated by CineAIStudio\n')
                f.write(f'# Size: {lut_info.size}\n\n')

                # 写入网格信息
                size = lut_data.shape[0]
                f.write(f'3DMESH {size} {size} {size}\n\n')

                # 写入LUT数据
                precision = getattr(lut_info.metadata.get('generation_params', {}), 'precision', 6)
                for r in range(size):
                    for g in range(size):
                        for b in range(size):
                            pixel = lut_data[r, g, b]
                            f.write(f'{pixel[0]:.{precision}f}\t{pixel[1]:.{precision}f}\t{pixel[2]:.{precision}f}\n')

            return True

        except Exception as e:
            self.logger.error(f"3DL LUT保存失败: {str(e)}")
            return False

    def apply_lut_to_frame(self, frame: np.ndarray, lut_name: str,
                           intensity: float = 1.0) -> np.ndarray:
        """应用LUT到帧"""
        try:
            if lut_name not in self.loaded_luts:
                self.logger.error(f"LUT未加载: {lut_name}")
                return frame.copy()

            lut_data = self.loaded_luts[lut_name]
            lut_info = self.available_luts[lut_name]

            # 色彩空间转换
            processed_frame = frame.copy()
            if processed_frame.dtype != np.float32:
                processed_frame = processed_frame.astype(np.float32) / 255.0

            # 应用LUT
            if lut_info.type == LUTType.THREE_D:
                processed_frame = self._apply_3d_lut_to_frame(processed_frame, lut_data, intensity)
            elif lut_info.type == LUTType.ONE_D:
                processed_frame = self._apply_1d_lut_to_frame(processed_frame, lut_data, intensity)

            # 转换回uint8
            processed_frame = (processed_frame * 255).astype(np.uint8)

            return processed_frame

        except Exception as e:
            self.logger.error(f"LUT应用到帧失败: {str(e)}")
            return frame.copy()

    def _apply_3d_lut_to_frame(self, frame: np.ndarray, lut_3d: np.ndarray,
                             intensity: float = 1.0) -> np.ndarray:
        """应用3D LUT到帧"""
        try:
            h, w, c = frame.shape
            processed_frame = np.zeros_like(frame)
            size = lut_3d.shape[0]

            # 简化的LUT应用（最近邻）
            for y in range(h):
                for x in range(w):
                    pixel = frame[y, x]

                    # 计算LUT坐标
                    coords = pixel * (size - 1)
                    r_idx, g_idx, b_idx = coords.astype(int)
                    r_idx = np.clip(r_idx, 0, size - 1)
                    g_idx = np.clip(g_idx, 0, size - 1)
                    b_idx = np.clip(b_idx, 0, size - 1)

                    # 获取LUT值
                    lut_value = lut_3d[r_idx, g_idx, b_idx]

                    # 混合原始值和LUT值
                    processed_frame[y, x] = pixel * (1 - intensity) + lut_value * intensity

            return processed_frame

        except Exception as e:
            self.logger.error(f"3D LUT应用到帧失败: {str(e)}")
            return frame

    def _apply_1d_lut_to_frame(self, frame: np.ndarray, lut_1d: np.ndarray,
                             intensity: float = 1.0) -> np.ndarray:
        """应用1D LUT到帧"""
        try:
            processed_frame = frame.copy()
            size = lut_1d.shape[0]

            # 为每个通道应用1D LUT
            for i in range(frame.shape[2]):
                channel = frame[:, :, i]
                # 应用查找表
                coords = (channel * (size - 1)).astype(int)
                coords = np.clip(coords, 0, size - 1)
                processed_channel = lut_1d[coords]

                # 混合原始值和LUT值
                processed_frame[:, :, i] = channel * (1 - intensity) + processed_channel * intensity

            return processed_frame

        except Exception as e:
            self.logger.error(f"1D LUT应用到帧失败: {str(e)}")
            return frame

    def analyze_lut(self, lut_name: str) -> Dict[str, Any]:
        """分析LUT"""
        try:
            if lut_name not in self.loaded_luts:
                self.logger.error(f"LUT未加载: {lut_name}")
                return {}

            lut_data = self.loaded_luts[lut_name]
            lut_info = self.available_luts[lut_name]

            analysis = {
                'name': lut_info.name,
                'format': lut_info.format.value,
                'type': lut_info.type.value,
                'size': lut_info.size,
                'input_space': lut_info.input_space.value,
                'output_space': lut_info.output_space.value,
                'data_range': {
                    'min': np.min(lut_data).tolist(),
                    'max': np.max(lut_data).tolist(),
                    'mean': np.mean(lut_data).tolist(),
                    'std': np.std(lut_data).tolist()
                },
                'color_shift': self._analyze_color_shift(lut_data),
                'saturation_change': self._analyze_saturation_change(lut_data),
                'contrast_change': self._analyze_contrast_change(lut_data),
                'gamma_curve': self._analyze_gamma_curve(lut_data)
            }

            return analysis

        except Exception as e:
            self.logger.error(f"LUT分析失败: {str(e)}")
            return {}

    def _analyze_color_shift(self, lut_data: np.ndarray) -> Dict[str, float]:
        """分析色彩偏移"""
        try:
            # 创建中性色测试点
            neutral_points = []
            for i in range(5):
                value = i / 4.0
                neutral_points.append([value, value, value])

            neutral_points = np.array(neutral_points)

            # 应用LUT
            if len(lut_data.shape) == 4:  # 3D LUT
                size = lut_data.shape[0]
                processed_neutral = []
                for point in neutral_points:
                    coords = point * (size - 1)
                    r_idx, g_idx, b_idx = coords.astype(int)
                    processed_neutral.append(lut_data[r_idx, g_idx, b_idx])
                processed_neutral = np.array(processed_neutral)
            else:
                processed_neutral = neutral_points  # 简化处理

            # 计算色度偏移
            avg_hue_shift = np.mean(processed_neutral - neutral_points, axis=0)

            return {
                'red_shift': float(avg_hue_shift[0]),
                'green_shift': float(avg_hue_shift[1]),
                'blue_shift': float(avg_hue_shift[2])
            }

        except Exception as e:
            self.logger.error(f"色彩偏移分析失败: {str(e)}")
            return {'red_shift': 0.0, 'green_shift': 0.0, 'blue_shift': 0.0}

    def _analyze_saturation_change(self, lut_data: np.ndarray) -> Dict[str, float]:
        """分析饱和度变化"""
        try:
            # 创建测试点
            test_points = []
            for r in range(0, 256, 32):
                for g in range(0, 256, 32):
                    for b in range(0, 256, 32):
                        if r == g == b:
                            continue  # 跳过中性色
                        test_points.append([r/255.0, g/255.0, b/255.0])

            test_points = np.array(test_points)

            # 计算原始饱和度
            original_sat = self._calculate_saturation(test_points)

            # 应用LUT
            if len(lut_data.shape) == 4:  # 3D LUT
                size = lut_data.shape[0]
                processed_points = []
                for point in test_points:
                    coords = point * (size - 1)
                    r_idx, g_idx, b_idx = coords.astype(int)
                    processed_points.append(lut_data[r_idx, g_idx, b_idx])
                processed_points = np.array(processed_points)
            else:
                processed_points = test_points

            # 计算处理后饱和度
            processed_sat = self._calculate_saturation(processed_points)

            # 计算饱和度变化
            sat_change = np.mean(processed_sat - original_sat)

            return {
                'average_change': float(sat_change),
                'max_increase': float(np.max(processed_sat - original_sat)),
                'max_decrease': float(np.max(original_sat - processed_sat))
            }

        except Exception as e:
            self.logger.error(f"饱和度变化分析失败: {str(e)}")
            return {'average_change': 0.0, 'max_increase': 0.0, 'max_decrease': 0.0}

    def _analyze_contrast_change(self, lut_data: np.ndarray) -> Dict[str, float]:
        """分析对比度变化"""
        try:
            # 创建灰度测试点
            gray_points = []
            for i in range(256):
                value = i / 255.0
                gray_points.append([value, value, value])

            gray_points = np.array(gray_points)

            # 应用LUT
            if len(lut_data.shape) == 4:  # 3D LUT
                size = lut_data.shape[0]
                processed_gray = []
                for point in gray_points:
                    coords = point * (size - 1)
                    r_idx, g_idx, b_idx = coords.astype(int)
                    processed_gray.append(lut_data[r_idx, g_idx, b_idx])
                processed_gray = np.array(processed_gray)
            else:
                processed_gray = gray_points

            # 计算对比度
            original_contrast = np.std(gray_points)
            processed_contrast = np.std(processed_gray)

            return {
                'original_contrast': float(original_contrast),
                'processed_contrast': float(processed_contrast),
                'contrast_ratio': float(processed_contrast / original_contrast) if original_contrast > 0 else 1.0
            }

        except Exception as e:
            self.logger.error(f"对比度变化分析失败: {str(e)}")
            return {'original_contrast': 0.0, 'processed_contrast': 0.0, 'contrast_ratio': 1.0}

    def _analyze_gamma_curve(self, lut_data: np.ndarray) -> Dict[str, float]:
        """分析伽马曲线"""
        try:
            # 创建灰度测试点
            gray_points = []
            for i in range(256):
                value = i / 255.0
                gray_points.append([value, value, value])

            gray_points = np.array(gray_points)

            # 应用LUT
            if len(lut_data.shape) == 4:  # 3D LUT
                size = lut_data.shape[0]
                processed_gray = []
                for point in gray_points:
                    coords = point * (size - 1)
                    r_idx, g_idx, b_idx = coords.astype(int)
                    processed_gray.append(lut_data[r_idx, g_idx, b_idx])
                processed_gray = np.array(processed_gray)
            else:
                processed_gray = gray_points

            # 计算伽马值（简化计算）
            original_values = gray_points[:, 0]
            processed_values = processed_gray[:, 0]

            # 使用对数回归计算伽马
            log_original = np.log(original_values[original_values > 0])
            log_processed = np.log(processed_values[original_values > 0])

            if len(log_original) > 0:
                gamma = np.mean(log_processed / log_original)
            else:
                gamma = 1.0

            return {
                'gamma': float(gamma),
                'mid_tone_gamma': float(gamma),  # 简化处理
                'shadow_gamma': float(gamma),     # 简化处理
                'highlight_gamma': float(gamma)  # 简化处理
            }

        except Exception as e:
            self.logger.error(f"伽马曲线分析失败: {str(e)}")
            return {'gamma': 1.0, 'mid_tone_gamma': 1.0, 'shadow_gamma': 1.0, 'highlight_gamma': 1.0}

    def _calculate_saturation(self, rgb_data: np.ndarray) -> np.ndarray:
        """计算饱和度"""
        try:
            max_val = np.max(rgb_data, axis=1)
            min_val = np.min(rgb_data, axis=1)
            delta = max_val - min_val

            saturation = np.where(max_val > 0, delta / max_val, 0)
            return saturation

        except Exception as e:
            self.logger.error(f"饱和度计算失败: {str(e)}")
            return np.zeros(len(rgb_data))

    def get_available_luts(self) -> List[str]:
        """获取可用LUT列表"""
        return list(self.available_luts.keys())

    def get_lut_info(self, lut_name: str) -> Optional[LUTInfo]:
        """获取LUT信息"""
        return self.available_luts.get(lut_name)

    def unload_lut(self, lut_name: str) -> bool:
        """卸载LUT"""
        try:
            if lut_name in self.loaded_luts:
                del self.loaded_luts[lut_name]
                self.logger.info(f"LUT已卸载: {lut_name}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"LUT卸载失败: {str(e)}")
            return False

    def batch_convert_lut(self, input_dir: str, output_dir: str,
                         input_format: LUTFormat,
                         output_format: LUTFormat) -> int:
        """批量转换LUT格式"""
        try:
            converted_count = 0

            for file_path in Path(input_dir).glob(f"*.{input_format.value}"):
                try:
                    # 加载LUT
                    lut_data, lut_info = self.load_lut_from_path(str(file_path))

                    # 生成输出路径
                    output_path = Path(output_dir) / f"{file_path.stem}.{output_format.value}"

                    # 保存LUT
                    if self.save_lut(lut_data, lut_info, str(output_path), output_format):
                        converted_count += 1

                except Exception as e:
                    self.logger.error(f"转换LUT失败 {file_path}: {str(e)}")

            self.logger.info(f"批量转换完成，转换了 {converted_count} 个LUT文件")
            return converted_count

        except Exception as e:
            self.logger.error(f"批量转换失败: {str(e)}")
            return 0

    def load_lut_from_path(self, file_path: str) -> Tuple[np.ndarray, LUTInfo]:
        """从文件路径加载LUT"""
        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.cube':
            return self._load_cube_lut(file_path)
        elif file_ext == '.3dl':
            return self._load_3dl_lut(file_path)
        else:
            raise ValueError(f"不支持的LUT格式: {file_ext}")

    def create_preset_luts(self) -> Dict[str, np.ndarray]:
        """创建预设LUT"""
        try:
            preset_luts = {}

            # 电影风格LUT
            cinematic_operations = [
                {
                    'type': 'contrast',
                    'parameters': {'contrast': 1.2, 'brightness': -0.05}
                },
                {
                    'type': 'hsl',
                    'parameters': {'saturation': 0.9, 'lightness': 0.95}
                },
                {
                    'type': 'tone_mapping',
                    'parameters': {'method': 'reinhard', 'target_luminance': 80.0}
                }
            ]

            cinematic_lut, _ = self.generate_lut_from_operations(cinematic_operations)
            preset_luts['cinematic'] = cinematic_lut

            # 复古风格LUT
            vintage_operations = [
                {
                    'type': 'contrast',
                    'parameters': {'contrast': 1.1, 'brightness': 0.1}
                },
                {
                    'type': 'hsl',
                    'parameters': {'hue_shift': 0.05, 'saturation': 0.7, 'lightness': 1.1}
                }
            ]

            vintage_lut, _ = self.generate_lut_from_operations(vintage_operations)
            preset_luts['vintage'] = vintage_lut

            # 鲜艳风格LUT
            vibrant_operations = [
                {
                    'type': 'contrast',
                    'parameters': {'contrast': 1.3, 'brightness': 0.0}
                },
                {
                    'type': 'hsl',
                    'parameters': {'saturation': 1.4, 'lightness': 0.95}
                }
            ]

            vibrant_lut, _ = self.generate_lut_from_operations(vibrant_operations)
            preset_luts['vibrant'] = vibrant_lut

            self.logger.info(f"预设LUT创建完成，共{len(preset_luts)}个")
            return preset_luts

        except Exception as e:
            self.logger.error(f"预设LUT创建失败: {str(e)}")
            return {}

    def _update_performance_metrics(self, operation: str, processing_time: float) -> None:
        """更新性能指标"""
        if operation == 'load':
            self.performance_metrics['luts_loaded'] += 1
        elif operation == 'generate':
            self.performance_metrics['luts_generated'] += 1

        self.performance_metrics['total_processing_time'] += processing_time

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.performance_metrics.copy()

    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 关闭线程池
            self.thread_pool.shutdown(wait=True)

            # 清理缓存
            self.lut_cache.clear()

            # 清理临时文件
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)

            self.logger.info("LUT管理器清理完成")

        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局LUT管理器实例
_lut_manager: Optional[LUTManager] = None


def get_lut_manager() -> LUTManager:
    """获取全局LUT管理器实例"""
    global _lut_manager
    if _lut_manager is None:
        _lut_manager = LUTManager()
    return _lut_manager


def cleanup_lut_manager() -> None:
    """清理全局LUT管理器实例"""
    global _lut_manager
    if _lut_manager is not None:
        _lut_manager.cleanup()
        _lut_manager = None