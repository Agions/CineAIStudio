#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio Advanced Color Science Module
高级色彩科学模块，提供专业色彩管理、HDR处理和色彩匹配算法
"""

import numpy as np
import cv2
import math
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum
import logging

from .logger import get_logger
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from .color_grading_engine import ColorSpace, HDRStandard


class TransferFunction(Enum):
    """传递函数枚举"""
    LINEAR = "linear"
    GAMMA_22 = "gamma_22"
    GAMMA_24 = "gamma_24"
    SRGB = "srgb"
    REC709 = "rec709"
    REC2020 = "rec2020"
    ST2084 = "st2084"  # PQ (HDR10)
    HLG = "hlg"
    LOG_C = "log_c"
    S_LOG3 = "s_log3"
    V_LOG = "v_log"
    CINEON = "cineon"


class Illuminant(Enum):
    """光源枚举"""
    D50 = "d50"  # 5000K
    D55 = "d55"  # 5500K
    D65 = "d65"  # 6500K
    D75 = "d75"  # 7500K
    A = "a"      # 2856K
    B = "b"      # 4874K
    C = "c"      # 6774K


@dataclass
class ColorPrimaries:
    """色彩原点数据类"""
    name: str
    red: Tuple[float, float]  # x, y
    green: Tuple[float, float]  # x, y
    blue: Tuple[float, float]  # x, y
    white: Tuple[float, float]  # x, y

    def get_xyz_matrix(self) -> np.ndarray:
        """获取XYZ转换矩阵"""
        return self._calculate_xyz_matrix()

    def _calculate_xyz_matrix(self) -> np.ndarray:
        """计算XYZ转换矩阵"""
        # 获取原点坐标
        xr, yr = self.red
        xg, yg = self.green
        xb, yb = self.blue
        xw, yw = self.white

        # 计算RGB到XYZ的转换矩阵
        # 使用Bradford变换
        XYZ_w = self._xy_to_xyz(xw, yw)
        XYZ_r = self._xy_to_xyz(xr, yr)
        XYZ_g = self._xy_to_xyz(xg, yg)
        XYZ_b = self._xy_to_xyz(xb, yb)

        # 构建矩阵
        RGB = np.array([XYZ_r, XYZ_g, XYZ_b]).T
        S = np.linalg.inv(RGB) @ XYZ_w

        # RGB -> XYZ 转换矩阵
        M = RGB * S

        return M

    def _xy_to_xyz(self, x: float, y: float) -> np.ndarray:
        """xy坐标转XYZ"""
        Y = 1.0
        X = (x * Y) / y
        Z = ((1 - x - y) * Y) / y
        return np.array([X, Y, Z])


@dataclass
class ColorProfile:
    """色彩配置文件数据类"""
    name: str
    primaries: ColorPrimaries
    transfer_function: TransferFunction
    illuminant: Illuminant
    bit_depth: int
    description: str = ""


class ColorScienceEngine:
    """色彩科学引擎"""

    def __init__(self, logger=None):
        """初始化色彩科学引擎"""
        self.logger = logger or get_logger("ColorScienceEngine")
        self.error_handler = get_global_error_handler()

        # 初始化色彩配置文件
        self.color_profiles = self._init_color_profiles()

        # 初始化转换矩阵
        self.conversion_matrices = self._init_conversion_matrices()

        # 初始化传递函数
        self.transfer_functions = self._init_transfer_functions()

        # HDR处理参数
        self.hdr_parameters = self._init_hdr_parameters()

    def _init_color_profiles(self) -> Dict[str, ColorProfile]:
        """初始化色彩配置文件"""
        profiles = {}

        # sRGB
        profiles['srgb'] = ColorProfile(
            name="sRGB",
            primaries=ColorPrimaries(
                name="sRGB",
                red=(0.6400, 0.3300),
                green=(0.3000, 0.6000),
                blue=(0.1500, 0.0600),
                white=(0.3127, 0.3290)
            ),
            transfer_function=TransferFunction.SRGB,
            illuminant=Illuminant.D65,
            bit_depth=8,
            description="Standard RGB color space"
        )

        # Rec.709
        profiles['rec709'] = ColorProfile(
            name="Rec.709",
            primaries=ColorPrimaries(
                name="Rec.709",
                red=(0.6400, 0.3300),
                green=(0.3000, 0.6000),
                blue=(0.1500, 0.0600),
                white=(0.3127, 0.3290)
            ),
            transfer_function=TransferFunction.REC709,
            illuminant=Illuminant.D65,
            bit_depth=10,
            description="ITU-R BT.709"
        )

        # DCI-P3
        profiles['dci_p3'] = ColorProfile(
            name="DCI-P3",
            primaries=ColorPrimaries(
                name="DCI-P3",
                red=(0.6800, 0.3200),
                green=(0.2650, 0.6900),
                blue=(0.1500, 0.0600),
                white=(0.3140, 0.3510)
            ),
            transfer_function=TransferFunction.GAMMA_24,
            illuminant=Illuminant.D65,
            bit_depth=12,
            description="DCI-P3 color space"
        )

        # Rec.2020
        profiles['rec2020'] = ColorProfile(
            name="Rec.2020",
            primaries=ColorPrimaries(
                name="Rec.2020",
                red=(0.7080, 0.2920),
                green=(0.1700, 0.7970),
                blue=(0.1310, 0.0460),
                white=(0.3127, 0.3290)
            ),
            transfer_function=TransferFunction.REC2020,
            illuminant=Illuminant.D65,
            bit_depth=10,
            description="ITU-R BT.2020"
        )

        # Adobe RGB
        profiles['adobe_rgb'] = ColorProfile(
            name="Adobe RGB",
            primaries=ColorPrimaries(
                name="Adobe RGB",
                red=(0.6400, 0.3300),
                green=(0.2100, 0.7100),
                blue=(0.1500, 0.0600),
                white=(0.3127, 0.3290)
            ),
            transfer_function=TransferFunction.GAMMA_22,
            illuminant=Illuminant.D65,
            bit_depth=8,
            description="Adobe RGB color space"
        )

        return profiles

    def _init_conversion_matrices(self) -> Dict[str, np.ndarray]:
        """初始化转换矩阵"""
        matrices = {}

        # RGB to XYZ matrices
        for profile_name, profile in self.color_profiles.items():
            matrices[f'{profile_name}_to_xyz'] = profile.primaries.get_xyz_matrix()

        # XYZ to RGB matrices (inverse)
        for profile_name, profile in self.color_profiles.items():
            rgb_to_xyz = matrices[f'{profile_name}_to_xyz']
            matrices[f'xyz_to_{profile_name}'] = np.linalg.inv(rgb_to_xyz)

        # Chromatic adaptation matrices (Bradford)
        matrices['bradford_d65_to_d50'] = self._get_bradford_adaptation_matrix(
            Illuminant.D65, Illuminant.D50
        )
        matrices['bradford_d50_to_d65'] = self._get_bradford_adaptation_matrix(
            Illuminant.D50, Illuminant.D65
        )

        return matrices

    def _init_transfer_functions(self) -> Dict[str, Callable]:
        """初始化传递函数"""
        return {
            'linear': lambda x: x,
            'linear_inv': lambda x: x,
            'gamma_22': lambda x: np.power(x, 1/2.2),
            'gamma_22_inv': lambda x: np.power(x, 2.2),
            'gamma_24': lambda x: np.power(x, 1/2.4),
            'gamma_24_inv': lambda x: np.power(x, 2.4),
            'srgb': self._srgb_oetf,
            'srgb_inv': self._srgb_eotf,
            'rec709': self._rec709_oetf,
            'rec709_inv': self._rec709_eotf,
            'st2084': self._st2084_oetf,
            'st2084_inv': self._st2084_eotf,
            'hlg': self._hlg_oetf,
            'hlg_inv': self._hlg_eotf,
            's_log3': self._s_log3_oetf,
            's_log3_inv': self._s_log3_eotf,
            'v_log': self._v_log_oetf,
            'v_log_inv': self._v_log_eotf,
        }

    def _init_hdr_parameters(self) -> Dict[str, Any]:
        """初始化HDR参数"""
        return {
            'st2084': {
                'm1': 2610 / 4096 * 1/4,
                'm2': 2523 / 4096 * 128,
                'c1': 3424 / 4096,
                'c2': 2413 / 4096 * 32,
                'c3': 2392 / 4096 * 32,
                'max_luminance': 10000,  # cd/m²
                'min_luminance': 0.0001   # cd/m²
            },
            'hlg': {
                'a': 0.17883277,
                'b': 0.28466892,
                'c': 0.55991073,
                'reference_white': 1000,  # cd/m²
                'system_gamma': 1.2
            }
        }

    def _srgb_oetf(self, x: np.ndarray) -> np.ndarray:
        """sRGB光电转换函数"""
        return np.where(x <= 0.0031308,
                      x * 12.92,
                      1.055 * np.power(x, 1/2.4) - 0.055)

    def _srgb_eotf(self, x: np.ndarray) -> np.ndarray:
        """sRGB电光转换函数"""
        return np.where(x <= 0.04045,
                      x / 12.92,
                      np.power((x + 0.055) / 1.055, 2.4))

    def _rec709_oetf(self, x: np.ndarray) -> np.ndarray:
        """Rec.709光电转换函数"""
        return np.where(x <= 0.018,
                      x * 4.5,
                      1.099 * np.power(x, 0.45) - 0.099)

    def _rec709_eotf(self, x: np.ndarray) -> np.ndarray:
        """Rec.709电光转换函数"""
        return np.where(x <= 0.081,
                      x / 4.5,
                      np.power((x + 0.099) / 1.099, 1/0.45))

    def _st2084_oetf(self, x: np.ndarray) -> np.ndarray:
        """ST2084 (PQ) 光电转换函数"""
        params = self.hdr_parameters['st2084']
        m1, m2, c1, c2, c3 = params['m1'], params['m2'], params['c1'], params['c2'], params['c3']
        max_lum, min_lum = params['max_luminance'], params['min_luminance']

        # 归一化到0-1范围
        x_norm = np.clip(x / max_lum, min_lum / max_lum, 1.0)

        # ST2084公式
        y_p = np.power(m1 * x_norm + m2, 1/2) / (c1 * x_norm + c2)
        y = np.power(y_p - c3, 1/2)

        return np.clip(y, 0, 1)

    def _st2084_eotf(self, x: np.ndarray) -> np.ndarray:
        """ST2084 (PQ) 电光转换函数"""
        params = self.hdr_parameters['st2084']
        m1, m2, c1, c2, c3 = params['m1'], params['m2'], params['c1'], params['c2'], params['c3']
        max_lum = params['max_luminance']

        # ST2084逆变换
        y_p = np.power(x, 2) + c3
        x_norm = np.power(y_p, 2) / (m1 * np.power(y_p, 2) - m2)

        # 反归一化
        return x_norm * max_lum

    def _hlg_oetf(self, x: np.ndarray) -> np.ndarray:
        """HLG光电转换函数"""
        params = self.hdr_parameters['hlg']
        a, b, c = params['a'], params['b'], params['c']
        ref_white = params['reference_white']

        # 归一化到0-1范围
        x_norm = np.clip(x / ref_white, 0, 12)

        # HLG公式
        y = np.where(x_norm <= 1/12,
                    np.sqrt(3 * x_norm),
                    a * np.log(12 * x_norm - b) + c)

        return np.clip(y, 0, 1)

    def _hlg_eotf(self, x: np.ndarray) -> np.ndarray:
        """HLG电光转换函数"""
        params = self.hdr_parameters['hlg']
        a, b, c = params['a'], params['b'], params['c']
        ref_white = params['reference_white']
        system_gamma = params['system_gamma']

        # HLG逆变换
        y = np.where(x <= 0.5,
                   x * x / 3,
                   (np.exp((x - c) / a) + b) / 12)

        # 应用系统伽马
        y = np.power(y * ref_white, system_gamma)

        return y

    def _s_log3_oetf(self, x: np.ndarray) -> np.ndarray:
        """S-Log3光电转换函数"""
        # S-Log3公式
        return np.where(x <= 0.01125000,
                      (x * (420.0 / 219.0) + (0.01125000 * (420.0 / 219.0) - 0.0929000)) * (3.636363636363636),
                      (np.log10((x + 0.01125000) / (0.18 + 0.01125000)) * 261.5 / 1023.0 + 0.4205) * (3.636363636363636))

    def _s_log3_eotf(self, x: np.ndarray) -> np.ndarray:
        """S-Log3电光转换函数"""
        # S-Log3逆变换
        return np.where(x <= 0.0929000,
                      (x / 3.636363636363636 - (0.01125000 * (420.0 / 219.0) - 0.0929000)) * (219.0 / 420.0),
                      (np.power(10, ((x / 3.636363636363636) - 0.4205) * 1023.0 / 261.5) - 0.01125000) * (0.18 + 0.01125000))

    def _v_log_oetf(self, x: np.ndarray) -> np.ndarray:
        """V-Log光电转换函数"""
        # V-Log公式
        return np.where(x <= 0.01,
                      5.6 * x + 0.125,
                      np.log10(x + 0.01) * 5.6 + 0.125)

    def _v_log_eotf(self, x: np.ndarray) -> np.ndarray:
        """V-Log电光转换函数"""
        # V-Log逆变换
        return np.where(x <= 0.181,
                      (x - 0.125) / 5.6,
                      np.power(10, (x - 0.125) / 5.6) - 0.01)

    def _get_bradford_adaptation_matrix(self,
                                      from_illuminant: Illuminant,
                                      to_illuminant: Illuminant) -> np.ndarray:
        """获取Bradford色适应矩阵"""
        # Bradford变换矩阵
        bradford = np.array([
            [0.8951, 0.2664, -0.1614],
            [-0.7502, 1.7135, 0.0367],
            [0.0389, -0.0685, 1.0296]
        ])

        # 光源XYZ坐标
        illuminant_xyz = {
            Illuminant.D50: np.array([0.9642, 1.0000, 0.8251]),
            Illuminant.D55: np.array([0.9568, 1.0000, 0.9214]),
            Illuminant.D65: np.array([0.9504, 1.0000, 1.0888]),
            Illuminant.D75: np.array([0.9497, 1.0000, 1.2262]),
            Illuminant.A: np.array([1.0985, 1.0000, 0.3558]),
            Illuminant.B: np.array([0.9907, 1.0000, 0.8523]),
            Illuminant.C: np.array([0.9807, 1.0000, 1.1822])
        }

        # 转换光源
        src_xyz = illuminant_xyz[from_illuminant]
        dst_xyz = illuminant_xyz[to_illuminant]

        # Bradford变换
        src_cone = bradford @ src_xyz
        dst_cone = bradford @ dst_xyz

        # 色适应矩阵
        adaptation = np.diag(dst_cone / src_cone)

        # 完整变换矩阵
        adaptation_matrix = np.linalg.inv(bradford) @ adaptation @ bradford

        return adaptation_matrix

    def convert_color_space(self, frame: np.ndarray,
                          from_profile: str,
                          to_profile: str) -> np.ndarray:
        """色彩空间转换"""
        try:
            if from_profile == to_profile:
                return frame.copy()

            if from_profile not in self.color_profiles:
                raise ValueError(f"未知的源色彩配置: {from_profile}")

            if to_profile not in self.color_profiles:
                raise ValueError(f"未知的目标色彩配置: {to_profile}")

            # 获取配置文件
            src_profile = self.color_profiles[from_profile]
            dst_profile = self.color_profiles[to_profile]

            # 确保帧是float32格式
            if frame.dtype != np.float32:
                frame = frame.astype(np.float32) / 255.0

            # 应用电光转换函数
            eotf_func = self.transfer_functions.get(f'{src_profile.transfer_function.value}_inv')
            if eotf_func:
                frame = eotf_func(frame)

            # 转换到XYZ
            rgb_to_xyz = self.conversion_matrices.get(f'{from_profile}_to_xyz')
            if rgb_to_xyz is not None:
                frame = self._apply_color_matrix(frame, rgb_to_xyz)

            # 如果需要色适应
            if src_profile.illuminant != dst_profile.illuminant:
                adaptation_key = f'bradford_{src_profile.illuminant.value}_to_{dst_profile.illuminant.value}'
                adaptation_matrix = self.conversion_matrices.get(adaptation_key)
                if adaptation_matrix is not None:
                    frame = self._apply_color_matrix(frame, adaptation_matrix)

            # 转换到目标RGB
            xyz_to_rgb = self.conversion_matrices.get(f'xyz_to_{to_profile}')
            if xyz_to_rgb is not None:
                frame = self._apply_color_matrix(frame, xyz_to_rgb)

            # 应用光电转换函数
            oetf_func = self.transfer_functions.get(f'{dst_profile.transfer_function.value}')
            if oetf_func:
                frame = oetf_func(frame)

            # 确保值在有效范围内
            frame = np.clip(frame, 0, 1)

            return frame

        except Exception as e:
            self.logger.error(f"色彩空间转换失败: {str(e)}")
            return frame.copy()

    def _apply_color_matrix(self, frame: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """应用色彩转换矩阵"""
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            h, w, c = frame.shape
            flat_frame = frame.reshape(-1, c)
            converted = flat_frame @ matrix.T
            return converted.reshape(h, w, c)
        else:
            return frame

    def tone_map_hdr_to_sdr(self, frame: np.ndarray,
                           hdr_standard: HDRStandard,
                           target_luminance: float = 100.0) -> np.ndarray:
        """HDR到SDR色调映射"""
        try:
            if hdr_standard == HDRStandard.HDR10 or hdr_standard == HDRStandard.HDR10_PLUS:
                return self._tone_map_pq_to_sdr(frame, target_luminance)
            elif hdr_standard == HDRStandard.HLG:
                return self._tone_map_hlg_to_sdr(frame, target_luminance)
            else:
                self.logger.warning(f"不支持的HDR标准: {hdr_standard.value}")
                return frame.copy()

        except Exception as e:
            self.logger.error(f"HDR到SDR色调映射失败: {str(e)}")
            return frame.copy()

    def _tone_map_pq_to_sdr(self, frame: np.ndarray,
                           target_luminance: float = 100.0) -> np.ndarray:
        """PQ (HDR10) 到SDR色调映射"""
        try:
            # 转换为线性光
            linear_frame = self._st2084_eotf(frame)

            # 应用色调映射算法 (Reinhard)
            mapped_frame = self._reinhard_tone_mapping(linear_frame, target_luminance)

            # 应用SDR传递函数
            sdr_frame = self._rec709_oetf(mapped_frame)

            return sdr_frame

        except Exception as e:
            self.logger.error(f"PQ到SDR色调映射失败: {str(e)}")
            return frame.copy()

    def _tone_map_hlg_to_sdr(self, frame: np.ndarray,
                           target_luminance: float = 100.0) -> np.ndarray:
        """HLG到SDR色调映射"""
        try:
            # HLG已经设计为向后兼容
            # 这里使用简单的缩放
            hlg_params = self.hdr_parameters['hlg']
            ref_white = hlg_params['reference_white']
            system_gamma = hlg_params['system_gamma']

            # 应用HLG逆变换
            linear_frame = self._hlg_eotf(frame)

            # 缩放到目标亮度
            scaled_frame = linear_frame * (target_luminance / ref_white)

            # 应用SDR传递函数
            sdr_frame = self._rec709_oetf(scaled_frame)

            return sdr_frame

        except Exception as e:
            self.logger.error(f"HLG到SDR色调映射失败: {str(e)}")
            return frame.copy()

    def _reinhard_tone_mapping(self, frame: np.ndarray,
                             target_luminance: float = 100.0) -> np.ndarray:
        """Reinhard色调映射算法"""
        try:
            # 确保帧是float32
            if frame.dtype != np.float32:
                frame = frame.astype(np.float32)

            # 计算亮度
            luminance = self._calculate_luminance(frame)

            # 计算关键值（对数平均亮度）
            key_value = np.exp(np.mean(np.log(luminance + 1e-8)))

            # 计算缩放因子
            scale = (target_luminance / 10000.0) / key_value

            # 应用Reinhard操作符
            mapped_luminance = (luminance * scale) / (1 + luminance * scale)

            # 调整RGB值
            if len(frame.shape) == 3:
                # 保持色彩关系
                ratio = mapped_luminance / (luminance + 1e-8)
                mapped_frame = frame * ratio[:, :, np.newaxis]
            else:
                mapped_frame = mapped_luminance

            return np.clip(mapped_frame, 0, 1)

        except Exception as e:
            self.logger.error(f"Reinhard色调映射失败: {str(e)}")
            return frame.copy()

    def _calculate_luminance(self, frame: np.ndarray) -> np.ndarray:
        """计算亮度"""
        if len(frame.shape) == 3:
            # 使用Rec.709亮度公式
            return 0.2126 * frame[:, :, 0] + 0.7152 * frame[:, :, 1] + 0.0722 * frame[:, :, 2]
        else:
            return frame

    def gamut_mapping(self, frame: np.ndarray,
                     src_profile: str,
                     dst_profile: str,
                     method: str = 'perceptual') -> np.ndarray:
        """色域映射"""
        try:
            if src_profile == dst_profile:
                return frame.copy()

            # 转换到XYZ色彩空间
            xyz_frame = self.convert_color_space(frame, src_profile, 'rec709')  # 使用Rec.709作为中间空间

            # 根据映射方法应用不同的算法
            if method == 'perceptual':
                mapped_frame = self._perceptual_gamut_mapping(xyz_frame, src_profile, dst_profile)
            elif method == 'relative_colorimetric':
                mapped_frame = self._relative_colorimetric_mapping(xyz_frame, src_profile, dst_profile)
            elif method == 'absolute_colorimetric':
                mapped_frame = self._absolute_colorimetric_mapping(xyz_frame, src_profile, dst_profile)
            elif method == 'saturation':
                mapped_frame = self._saturation_mapping(xyz_frame, src_profile, dst_profile)
            else:
                self.logger.warning(f"未知的色域映射方法: {method}")
                mapped_frame = xyz_frame

            # 转换到目标色彩空间
            result_frame = self.convert_color_space(mapped_frame, 'rec709', dst_profile)

            return result_frame

        except Exception as e:
            self.logger.error(f"色域映射失败: {str(e)}")
            return frame.copy()

    def _perceptual_gamut_mapping(self, xyz_frame: np.ndarray,
                                src_profile: str,
                                dst_profile: str) -> np.ndarray:
        """感知色域映射"""
        try:
            # 获取源和目标色域边界
            src_gamut = self._calculate_gamut_boundary(src_profile)
            dst_gamut = self._calculate_gamut_boundary(dst_profile)

            # 简化的色域映射算法
            # 在实际实现中，这里应该使用更复杂的算法

            # 计算色度坐标
            x = xyz_frame[:, :, 0] / (xyz_frame[:, :, 0] + xyz_frame[:, :, 1] + xyz_frame[:, :, 2] + 1e-8)
            y = xyz_frame[:, :, 1] / (xyz_frame[:, :, 0] + xyz_frame[:, :, 1] + xyz_frame[:, :, 2] + 1e-8)

            # 简单的压缩映射
            mapped_x = np.clip(x * 0.8 + 0.1, 0, 1)
            mapped_y = np.clip(y * 0.8 + 0.1, 0, 1)

            # 重建XYZ
            sum_xyz = xyz_frame[:, :, 0] + xyz_frame[:, :, 1] + xyz_frame[:, :, 2]
            mapped_frame = np.zeros_like(xyz_frame)
            mapped_frame[:, :, 0] = mapped_x * sum_xyz
            mapped_frame[:, :, 1] = mapped_y * sum_xyz
            mapped_frame[:, :, 2] = (1 - mapped_x - mapped_y) * sum_xyz

            return mapped_frame

        except Exception as e:
            self.logger.error(f"感知色域映射失败: {str(e)}")
            return xyz_frame.copy()

    def _relative_colorimetric_mapping(self, xyz_frame: np.ndarray,
                                       src_profile: str,
                                       dst_profile: str) -> np.ndarray:
        """相对比色映射"""
        try:
            # 获取白点坐标
            src_white = self.color_profiles[src_profile].primaries.white
            dst_white = self.color_profiles[dst_profile].primaries.white

            # 转换到xyY
            sum_xyz = xyz_frame[:, :, 0] + xyz_frame[:, :, 1] + xyz_frame[:, :, 2]
            x = xyz_frame[:, :, 0] / (sum_xyz + 1e-8)
            y = xyz_frame[:, :, 1] / (sum_xyz + 1e-8)
            Y = xyz_frame[:, :, 1]

            # 调整白点
            scale_x = dst_white[0] / src_white[0]
            scale_y = dst_white[1] / src_white[1]

            mapped_x = x * scale_x
            mapped_y = y * scale_y

            # 重建XYZ
            mapped_frame = np.zeros_like(xyz_frame)
            mapped_frame[:, :, 0] = mapped_x * Y / mapped_y
            mapped_frame[:, :, 1] = Y
            mapped_frame[:, :, 2] = (1 - mapped_x - mapped_y) * Y / mapped_y

            return mapped_frame

        except Exception as e:
            self.logger.error(f"相对比色映射失败: {str(e)}")
            return xyz_frame.copy()

    def _absolute_colorimetric_mapping(self, xyz_frame: np.ndarray,
                                      src_profile: str,
                                      dst_profile: str) -> np.ndarray:
        """绝对比色映射"""
        # 绝对比色映射保持原始XYZ坐标不变
        return xyz_frame.copy()

    def _saturation_mapping(self, xyz_frame: np.ndarray,
                           src_profile: str,
                           dst_profile: str) -> np.ndarray:
        """饱和度映射"""
        try:
            # 转换到xyY
            sum_xyz = xyz_frame[:, :, 0] + xyz_frame[:, :, 1] + xyz_frame[:, :, 2]
            x = xyz_frame[:, :, 0] / (sum_xyz + 1e-8)
            y = xyz_frame[:, :, 1] / (sum_xyz + 1e-8)
            Y = xyz_frame[:, :, 1]

            # 计算色度中心
            center_x = (x.min() + x.max()) / 2
            center_y = (y.min() + y.max()) / 2

            # 饱和度缩放
            saturation_scale = 0.8  # 可以调整

            mapped_x = center_x + (x - center_x) * saturation_scale
            mapped_y = center_y + (y - center_y) * saturation_scale

            # 重建XYZ
            mapped_frame = np.zeros_like(xyz_frame)
            mapped_frame[:, :, 0] = mapped_x * Y / mapped_y
            mapped_frame[:, :, 1] = Y
            mapped_frame[:, :, 2] = (1 - mapped_x - mapped_y) * Y / mapped_y

            return mapped_frame

        except Exception as e:
            self.logger.error(f"饱和度映射失败: {str(e)}")
            return xyz_frame.copy()

    def _calculate_gamut_boundary(self, profile: str) -> np.ndarray:
        """计算色域边界"""
        # 简化的色域边界计算
        # 在实际实现中，应该使用更精确的方法
        if profile == 'srgb':
            return np.array([
                [0.6400, 0.3300],  # 红色
                [0.3000, 0.6000],  # 绿色
                [0.1500, 0.0600],  # 蓝色
                [0.3127, 0.3290]   # 白色
            ])
        elif profile == 'dci_p3':
            return np.array([
                [0.6800, 0.3200],  # 红色
                [0.2650, 0.6900],  # 绿色
                [0.1500, 0.0600],  # 蓝色
                [0.3140, 0.3510]   # 白色
            ])
        else:
            return np.array([
                [0.6400, 0.3300],  # 默认使用sRGB
                [0.3000, 0.6000],
                [0.1500, 0.0600],
                [0.3127, 0.3290]
            ])

    def color_match_frames(self, reference_frame: np.ndarray,
                          target_frame: np.ndarray,
                          method: str = 'histogram_matching') -> np.ndarray:
        """色彩匹配"""
        try:
            if method == 'histogram_matching':
                return self._histogram_matching(reference_frame, target_frame)
            elif method == 'color_transfer':
                return self._color_transfer(reference_frame, target_frame)
            elif method == 'reinhard_color':
                return self._reinhard_color_matching(reference_frame, target_frame)
            else:
                self.logger.warning(f"未知的色彩匹配方法: {method}")
                return target_frame.copy()

        except Exception as e:
            self.logger.error(f"色彩匹配失败: {str(e)}")
            return target_frame.copy()

    def _histogram_matching(self, reference_frame: np.ndarray,
                           target_frame: np.ndarray) -> np.ndarray:
        """直方图匹配"""
        try:
            if len(reference_frame.shape) == 3:
                matched_channels = []
                for i in range(reference_frame.shape[2]):
                    ref_channel = reference_frame[:, :, i]
                    target_channel = target_frame[:, :, i]
                    matched_channel = self._match_histogram(ref_channel, target_channel)
                    matched_channels.append(matched_channel)
                return np.stack(matched_channels, axis=2)
            else:
                return self._match_histogram(reference_frame, target_frame)

        except Exception as e:
            self.logger.error(f"直方图匹配失败: {str(e)}")
            return target_frame.copy()

    def _match_histogram(self, reference: np.ndarray, target: np.ndarray) -> np.ndarray:
        """单通道直方图匹配"""
        try:
            # 确保输入是uint8
            if reference.dtype != np.uint8:
                reference = (reference * 255).astype(np.uint8)
            if target.dtype != np.uint8:
                target = (target * 255).astype(np.uint8)

            # 计算参考图像和目标图像的直方图
            ref_hist = cv2.calcHist([reference], [0], None, [256], [0, 256])
            target_hist = cv2.calcHist([target], [0], None, [256], [0, 256])

            # 计算累积分布函数
            ref_cdf = ref_hist.cumsum()
            ref_cdf = ref_cdf / ref_cdf[-1]

            target_cdf = target_hist.cumsum()
            target_cdf = target_cdf / target_cdf[-1]

            # 创建查找表
            lookup_table = np.zeros(256, dtype=np.uint8)
            for i in range(256):
                # 找到目标CDF中最接近参考CDF的值
                diff = np.abs(target_cdf - ref_cdf[i])
                idx = np.argmin(diff)
                lookup_table[i] = idx

            # 应用查找表
            matched = cv2.LUT(target, lookup_table)

            return matched.astype(np.float32) / 255.0

        except Exception as e:
            self.logger.error(f"直方图匹配失败: {str(e)}")
            return target.copy()

    def _color_transfer(self, reference_frame: np.ndarray,
                        target_frame: np.ndarray) -> np.ndarray:
        """颜色传递"""
        try:
            # 转换到LAB色彩空间
            ref_lab = cv2.cvtColor(reference_frame, cv2.COLOR_RGB2LAB)
            target_lab = cv2.cvtColor(target_frame, cv2.COLOR_RGB2LAB)

            # 计算统计量
            ref_mean = np.mean(ref_lab, axis=(0, 1))
            ref_std = np.std(ref_lab, axis=(0, 1))
            target_mean = np.mean(target_lab, axis=(0, 1))
            target_std = np.std(target_lab, axis=(0, 1))

            # 颜色传递
            transferred = target_lab.astype(np.float32)
            for i in range(3):
                transferred[:, :, i] = (transferred[:, :, i] - target_mean[i]) / (target_std[i] + 1e-8)
                transferred[:, :, i] = transferred[:, :, i] * ref_std[i] + ref_mean[i]

            # 确保值在有效范围内
            transferred = np.clip(transferred, 0, 255).astype(np.uint8)

            # 转换回RGB
            matched = cv2.cvtColor(transferred, cv2.COLOR_LAB2RGB)

            return matched.astype(np.float32) / 255.0

        except Exception as e:
            self.logger.error(f"颜色传递失败: {str(e)}")
            return target_frame.copy()

    def _reinhard_color_matching(self, reference_frame: np.ndarray,
                                target_frame: np.ndarray) -> np.ndarray:
        """Reinhard颜色匹配"""
        try:
            # 转换到线性RGB
            ref_linear = self._srgb_eotf(reference_frame)
            target_linear = self._srgb_eotf(target_frame)

            # 计算几何平均
            ref_gmean = np.exp(np.mean(np.log(ref_linear + 1e-8), axis=(0, 1)))
            target_gmean = np.exp(np.mean(np.log(target_linear + 1e-8), axis=(0, 1)))

            # 颜色匹配
            matched = target_linear * (ref_gmean / (target_gmean + 1e-8))

            # 转换回sRGB
            matched = self._srgb_oetf(matched)

            return matched

        except Exception as e:
            self.logger.error(f"Reinhard颜色匹配失败: {str(e)}")
            return target_frame.copy()

    def generate_lut_from_operations(self, operations: List[Dict[str, Any]],
                                   lut_size: int = 33,
                                   input_profile: str = 'rec709',
                                   output_profile: str = 'rec709') -> np.ndarray:
        """从操作生成LUT"""
        try:
            # 创建3D LUT网格
            lut = np.zeros((lut_size, lut_size, lut_size, 3), dtype=np.float32)

            # 生成RGB网格点
            step = 1.0 / (lut_size - 1)
            for r in range(lut_size):
                for g in range(lut_size):
                    for b in range(lut_size):
                        # 创建测试像素
                        test_pixel = np.array([
                            [r * step, g * step, b * step]
                        ], dtype=np.float32)

                        # 应用操作
                        processed_pixel = test_pixel.copy()
                        for operation in operations:
                            processed_pixel = self._apply_lut_operation(processed_pixel, operation)

                        # 存储到LUT
                        lut[r, g, b] = processed_pixel[0]

            return lut

        except Exception as e:
            self.logger.error(f"LUT生成失败: {str(e)}")
            return np.zeros((lut_size, lut_size, lut_size, 3), dtype=np.float32)

    def _apply_lut_operation(self, pixel: np.ndarray,
                           operation: Dict[str, Any]) -> np.ndarray:
        """应用LUT操作"""
        operation_type = operation.get('type')
        params = operation.get('parameters', {})

        if operation_type == 'contrast':
            contrast = params.get('contrast', 1.0)
            brightness = params.get('brightness', 0.0)
            return pixel * contrast + brightness
        elif operation_type == 'saturation':
            # 转换到HSV并调整饱和度
            hsv = cv2.cvtColor(pixel.reshape(1, 1, 3), cv2.COLOR_RGB2HSV)
            hsv[:, :, 1] *= params.get('saturation', 1.0)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).reshape(1, 3)
        elif operation_type == 'hsl':
            return self._apply_hsl_adjustment(pixel, params)
        else:
            return pixel

    def _apply_hsl_adjustment(self, pixel: np.ndarray,
                             params: Dict[str, Any]) -> np.ndarray:
        """应用HSL调整"""
        hue_shift = params.get('hue_shift', 0.0)
        saturation = params.get('saturation', 1.0)
        lightness = params.get('lightness', 1.0)

        # 转换到HSL
        hsl = cv2.cvtColor(pixel.reshape(1, 1, 3), cv2.COLOR_RGB2HLS)
        h, l, s = cv2.split(hsl)

        # 调整
        h = (h + hue_shift * 180) % 180
        s = np.clip(s * saturation, 0, 255)
        l = np.clip(l * lightness, 0, 255)

        # 转换回RGB
        hsl_adjusted = cv2.merge([h, l, s])
        rgb = cv2.cvtColor(hsl_adjusted, cv2.COLOR_HLS2RGB)

        return rgb.reshape(1, 3)

    def get_color_profile_info(self, profile_name: str) -> Dict[str, Any]:
        """获取色彩配置文件信息"""
        if profile_name not in self.color_profiles:
            return {}

        profile = self.color_profiles[profile_name]
        return {
            'name': profile.name,
            'primaries': {
                'red': profile.primaries.red,
                'green': profile.primaries.green,
                'blue': profile.primaries.blue,
                'white': profile.primaries.white
            },
            'transfer_function': profile.transfer_function.value,
            'illuminant': profile.illuminant.value,
            'bit_depth': profile.bit_depth,
            'description': profile.description
        }

    def analyze_color_accuracy(self, frame: np.ndarray,
                              reference_profile: str) -> Dict[str, Any]:
        """分析色彩准确性"""
        try:
            if reference_profile not in self.color_profiles:
                return {}

            profile = self.color_profiles[reference_profile]

            # 转换到标准色彩空间
            if frame.dtype != np.float32:
                frame = frame.astype(np.float32) / 255.0

            # 计算色彩统计
            stats = {
                'mean_rgb': np.mean(frame, axis=(0, 1)).tolist(),
                'std_rgb': np.std(frame, axis=(0, 1)).tolist(),
                'min_rgb': np.min(frame, axis=(0, 1)).tolist(),
                'max_rgb': np.max(frame, axis=(0, 1)).tolist(),
                'gamut_coverage': self._calculate_gamut_coverage(frame, reference_profile),
                'color_temperature': self._estimate_color_temperature(frame),
                'dynamic_range': self._calculate_dynamic_range(frame)
            }

            return stats

        except Exception as e:
            self.logger.error(f"色彩准确性分析失败: {str(e)}")
            return {}

    def _calculate_gamut_coverage(self, frame: np.ndarray, profile: str) -> float:
        """计算色域覆盖率"""
        try:
            # 简化的色域覆盖率计算
            # 在实际实现中，应该使用更精确的方法
            profile_info = self.get_color_profile_info(profile)
            if not profile_info:
                return 0.0

            # 转换到xy色度图
            sum_rgb = np.sum(frame, axis=2)
            x = np.mean(frame[:, :, 0] / (sum_rgb + 1e-8))
            y = np.mean(frame[:, :, 1] / (sum_rgb + 1e-8))

            # 计算到色域边界的距离
            primaries = profile_info['primaries']
            distances = [
                np.sqrt((x - primaries['red'][0])**2 + (y - primaries['red'][1])**2),
                np.sqrt((x - primaries['green'][0])**2 + (y - primaries['green'][1])**2),
                np.sqrt((x - primaries['blue'][0])**2 + (y - primaries['blue'][1])**2)
            ]

            # 简化的覆盖率计算
            coverage = 1.0 - min(distances) / 0.5  # 假设最大距离为0.5
            return max(0.0, min(1.0, coverage))

        except Exception as e:
            self.logger.error(f"色域覆盖率计算失败: {str(e)}")
            return 0.0

    def _estimate_color_temperature(self, frame: np.ndarray) -> float:
        """估计色温"""
        try:
            # 计算白点
            mean_rgb = np.mean(frame, axis=(0, 1))
            sum_rgb = np.sum(mean_rgb)
            x = mean_rgb[0] / (sum_rgb + 1e-8)
            y = mean_rgb[1] / (sum_rgb + 1e-8)

            # 使用McCamy公式估计色温
            n = (x - 0.3320) / (y - 0.1858)
            cct = 449 * n**3 + 3525 * n**2 + 6823.3 * n + 5520.33

            return max(1000, min(40000, cct))

        except Exception as e:
            self.logger.error(f"色温估计失败: {str(e)}")
            return 6500.0

    def _calculate_dynamic_range(self, frame: np.ndarray) -> float:
        """计算动态范围"""
        try:
            # 计算亮度
            luminance = self._calculate_luminance(frame)

            # 计算动态范围（对数）
            min_lum = np.min(luminance[luminance > 0])
            max_lum = np.max(luminance)

            if min_lum > 0 and max_lum > 0:
                dynamic_range = 20 * np.log10(max_lum / min_lum)
                return max(0, dynamic_range)
            else:
                return 0.0

        except Exception as e:
            self.logger.error(f"动态范围计算失败: {str(e)}")
            return 0.0


# 全局色彩科学引擎实例
_color_science_engine: Optional[ColorScienceEngine] = None


def get_color_science_engine() -> ColorScienceEngine:
    """获取全局色彩科学引擎实例"""
    global _color_science_engine
    if _color_science_engine is None:
        _color_science_engine = ColorScienceEngine()
    return _color_science_engine


def cleanup_color_science_engine() -> None:
    """清理全局色彩科学引擎实例"""
    global _color_science_engine
    if _color_science_engine is not None:
        _color_science_engine = None