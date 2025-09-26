#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 高级特效和转场库
提供专业级的视频特效和转场效果
"""

import numpy as np
import cv2
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import math
import time
from threading import Thread
from queue import Queue, Empty
import asyncio

try:
    import cupy as cp
    HAS_CUDA = True
except ImportError:
    HAS_CUDA = False

try:
    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileProgram, compileShader
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False


class EffectType(Enum):
    """特效类型"""
    COLOR_CORRECTION = "color_correction"
    BLUR = "blur"
    SHARPEN = "sharpen"
    GLOW = "glow"
    DISTORTION = "distortion"
    PARTICLES = "particles"
    GREEN_SCREEN = "green_screen"
    STABILIZATION = "stabilization"
    MOTION_BLUR = "motion_blur"
    CHROMATIC_ABBERRATION = "chromatic_aberration"
    VIGNETTE = "vignette"
    FILM_GRAIN = "film_grain"


class TransitionType(Enum):
    """转场类型"""
    DISSOLVE = "dissolve"
    FADE = "fade"
    WIPE = "wipe"
    PUSH = "push"
    SLIDE = "slide"
    ROTATE = "rotate"
    ZOOM = "zoom"
    CIRCLE = "circle"
    BLUR = "blur"
    MORPH = "morph"
    PARTICLE = "particle"


class BlendMode(Enum):
    """混合模式"""
    NORMAL = "normal"
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"


@dataclass
class Keyframe:
    """关键帧"""
    time: float
    value: float
    easing: str = "linear"  # linear, ease_in, ease_out, ease_in_out
    interpolation: str = "linear"  # linear, bezier, step


@dataclass
class EffectParameter:
    """特效参数"""
    name: str
    value: Any
    min_value: Any = None
    max_value: Any = None
    type: str = "float"  # float, int, bool, color, vector2, vector3
    keyframes: List[Keyframe] = None
    animated: bool = False


class EffectEngine:
    """特效引擎"""

    def __init__(self):
        self.effects: Dict[str, 'VideoEffect'] = {}
        self.transitions: Dict[str, 'VideoTransition'] = {}
        self.gpu_enabled = HAS_CUDA
        self.opengl_enabled = HAS_OPENGL

        # 初始化特效
        self._initialize_effects()
        self._initialize_transitions()

        # 性能优化
        self.cache_size = 100
        self.effect_cache: Dict[str, Any] = {}

    def _initialize_effects(self):
        """初始化特效"""
        self.effects['blur'] = BlurEffect()
        self.effects['sharpen'] = SharpenEffect()
        self.effects['glow'] = GlowEffect()
        self.effects['distortion'] = DistortionEffect()
        self.effects['green_screen'] = GreenScreenEffect()
        self.effects['motion_blur'] = MotionBlurEffect()
        self.effects['chromatic_aberration'] = ChromaticAberrationEffect()
        self.effects['vignette'] = VignetteEffect()
        self.effects['film_grain'] = FilmGrainEffect()
        self.effects['color_correction'] = ColorCorrectionEffect()

    def _initialize_transitions(self):
        """初始化转场"""
        self.transitions['dissolve'] = DissolveTransition()
        self.transitions['fade'] = FadeTransition()
        self.transitions['wipe'] = WipeTransition()
        self.transitions['push'] = PushTransition()
        self.transitions['slide'] = SlideTransition()
        self.transitions['rotate'] = RotateTransition()
        self.transitions['zoom'] = ZoomTransition()
        self.transitions['circle'] = CircleTransition()
        self.transitions['blur'] = BlurTransition()

    def apply_effect(self, frame: np.ndarray, effect_name: str,
                    parameters: Dict[str, Any] = None) -> np.ndarray:
        """应用特效"""
        if effect_name not in self.effects:
            return frame

        effect = self.effects[effect_name]
        return effect.apply(frame, parameters or {})

    def apply_transition(self, frame1: np.ndarray, frame2: np.ndarray,
                       transition_name: str, progress: float,
                       parameters: Dict[str, Any] = None) -> np.ndarray:
        """应用转场"""
        if transition_name not in self.transitions:
            return frame1 if progress < 0.5 else frame2

        transition = self.transitions[transition_name]
        return transition.apply(frame1, frame2, progress, parameters or {})


class VideoEffect:
    """视频特效基类"""

    def __init__(self, name: str):
        self.name = name
        self.parameters: Dict[str, EffectParameter] = {}
        self.enabled = True

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """应用特效"""
        raise NotImplementedError

    def get_parameters(self) -> Dict[str, EffectParameter]:
        """获取参数定义"""
        return self.parameters

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        for name, param in self.parameters.items():
            if name in parameters:
                value = parameters[name]
                if param.min_value is not None and value < param.min_value:
                    return False
                if param.max_value is not None and value > param.max_value:
                    return False
        return True


class BlurEffect(VideoEffect):
    """模糊特效"""

    def __init__(self):
        super().__init__("blur")
        self.parameters = {
            'radius': EffectParameter('radius', 5.0, 0.1, 50.0),
            'iterations': EffectParameter('iterations', 1, 1, 10, 'int'),
            'blur_type': EffectParameter('blur_type', 'gaussian', None, None, 'str')
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        radius = parameters.get('radius', 5.0)
        iterations = parameters.get('iterations', 1)
        blur_type = parameters.get('blur_type', 'gaussian')

        if HAS_CUDA:
            return self._apply_gpu_blur(frame, radius, iterations, blur_type)
        else:
            return self._apply_cpu_blur(frame, radius, iterations, blur_type)

    def _apply_cpu_blur(self, frame: np.ndarray, radius: float,
                        iterations: int, blur_type: str) -> np.ndarray:
        """CPU模糊处理"""
        kernel_size = int(radius * 2) + 1
        kernel_size = max(3, min(kernel_size, 51))  # 限制kernel大小

        if kernel_size % 2 == 0:
            kernel_size += 1

        result = frame.copy()
        for _ in range(iterations):
            if blur_type == 'gaussian':
                result = cv2.GaussianBlur(result, (kernel_size, kernel_size), 0)
            elif blur_type == 'box':
                result = cv2.blur(result, (kernel_size, kernel_size))
            elif blur_type == 'median':
                result = cv2.medianBlur(result, kernel_size)

        return result

    def _apply_gpu_blur(self, frame: np.ndarray, radius: float,
                        iterations: int, blur_type: str) -> np.ndarray:
        """GPU模糊处理"""
        if not HAS_CUDA:
            return self._apply_cpu_blur(frame, radius, iterations, blur_type)

        frame_gpu = cp.asarray(frame)

        for _ in range(iterations):
            if blur_type == 'gaussian':
                # 使用高斯滤波器
                kernel_size = int(radius * 2) + 1
                kernel_size = max(3, min(kernel_size, 51))
                sigma = radius / 3.0

                # 创建高斯核
                x = cp.linspace(-radius, radius, kernel_size)
                y = cp.linspace(-radius, radius, kernel_size)
                X, Y = cp.meshgrid(x, y)

                kernel = cp.exp(-(X**2 + Y**2) / (2 * sigma**2))
                kernel = kernel / cp.sum(kernel)

                # 应用卷积
                if len(frame.shape) == 3:
                    result = cp.zeros_like(frame_gpu)
                    for i in range(frame.shape[2]):
                        result[:, :, i] = self._convolve2d(frame_gpu[:, :, i], kernel)
                    frame_gpu = result
                else:
                    frame_gpu = self._convolve2d(frame_gpu, kernel)

        if HAS_CUDA:
            return cp.asnumpy(frame_gpu)
        else:
            return frame_gpu

    def _convolve2d(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """2D卷积"""
        if HAS_CUDA:
            from cupyx.scipy.ndimage import convolve
            return convolve(cp.asarray(image), cp.asarray(kernel), mode='reflect')
        else:
            # CPU回退方案
            from scipy.ndimage import convolve
            return convolve(image, kernel, mode='reflect')


class SharpenEffect(VideoEffect):
    """锐化特效"""

    def __init__(self):
        super().__init__("sharpen")
        self.parameters = {
            'intensity': EffectParameter('intensity', 1.0, 0.0, 5.0),
            'radius': EffectParameter('radius', 1.0, 0.1, 5.0)
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        intensity = parameters.get('intensity', 1.0)
        radius = parameters.get('radius', 1.0)

        # 创建锐化核
        kernel_size = int(radius * 2) + 1
        if kernel_size % 2 == 0:
            kernel_size += 1

        # 创建拉普拉斯核
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]], dtype=np.float32)

        if kernel_size > 3:
            # 对于更大的核，使用高斯差分
            kernel = self._create_difference_of_gaussians(kernel_size, radius)

        # 应用锐化
        sharpened = cv2.filter2D(frame, -1, kernel * intensity)

        # 混合原图和锐化结果
        return cv2.addWeighted(frame, 1.0 - intensity, sharpened, intensity, 0)

    def _create_difference_of_gaussians(self, size: int, sigma: float) -> np.ndarray:
        """创建高斯差分核"""
        x = np.linspace(-size//2, size//2, size)
        y = np.linspace(-size//2, size//2, size)
        X, Y = np.meshgrid(x, y)

        # 创建两个高斯核
        sigma1 = sigma
        sigma2 = sigma * 1.6

        gaussian1 = np.exp(-(X**2 + Y**2) / (2 * sigma1**2))
        gaussian1 = gaussian1 / np.sum(gaussian1)

        gaussian2 = np.exp(-(X**2 + Y**2) / (2 * sigma2**2))
        gaussian2 = gaussian2 / np.sum(gaussian2)

        return gaussian1 - gaussian2


class GlowEffect(VideoEffect):
    """发光特效"""

    def __init__(self):
        super().__init__("glow")
        self.parameters = {
            'intensity': EffectParameter('intensity', 1.0, 0.0, 3.0),
            'radius': EffectParameter('radius', 10.0, 1.0, 50.0),
            'threshold': EffectParameter('threshold', 0.5, 0.0, 1.0),
            'color': EffectParameter('color', [255, 255, 255], None, None, 'vector3')
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        intensity = parameters.get('intensity', 1.0)
        radius = parameters.get('radius', 10.0)
        threshold = parameters.get('threshold', 0.5)
        color = parameters.get('color', [255, 255, 255])

        # 转换为浮点型
        frame_float = frame.astype(np.float32) / 255.0

        # 提取亮部
        brightness = np.mean(frame_float, axis=2)
        mask = (brightness > threshold).astype(np.float32)

        # 创建发光效果
        glow = frame_float.copy()
        for i in range(3):
            glow[:, :, i] *= mask

        # 模糊处理
        kernel_size = int(radius * 2) + 1
        if kernel_size % 2 == 0:
            kernel_size += 1

        glow = cv2.GaussianBlur(glow, (kernel_size, kernel_size), 0)

        # 应用颜色
        color_norm = np.array(color, dtype=np.float32) / 255.0
        for i in range(3):
            glow[:, :, i] *= color_norm[i]

        # 混合发光效果
        result = frame_float + glow * intensity
        result = np.clip(result, 0, 1)

        return (result * 255).astype(np.uint8)


class DistortionEffect(VideoEffect):
    """变形特效"""

    def __init__(self):
        super().__init__("distortion")
        self.parameters = {
            'type': EffectParameter('type', 'ripple', None, None, 'str'),
            'amplitude': EffectParameter('amplitude', 10.0, 0.0, 100.0),
            'frequency': EffectParameter('frequency', 0.1, 0.01, 1.0),
            'phase': EffectParameter('phase', 0.0, 0.0, 360.0)
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        distortion_type = parameters.get('type', 'ripple')
        amplitude = parameters.get('amplitude', 10.0)
        frequency = parameters.get('frequency', 0.1)
        phase = parameters.get('phase', 0.0)

        height, width = frame.shape[:2]

        # 创建坐标网格
        x, y = np.meshgrid(np.arange(width), np.arange(height))

        # 计算变形偏移
        if distortion_type == 'ripple':
            # 波纹效果
            center_x, center_y = width // 2, height // 2
            dx = x - center_x
            dy = y - center_y
            distance = np.sqrt(dx**2 + dy**2)

            angle = np.arctan2(dy, dx)
            offset = amplitude * np.sin(distance * frequency + np.radians(phase))

            x_new = x + offset * np.cos(angle)
            y_new = y + offset * np.sin(angle)

        elif distortion_type == 'wave':
            # 波浪效果
            x_new = x + amplitude * np.sin(y * frequency + np.radians(phase))
            y_new = y

        elif distortion_type == 'bulge':
            # 膨胀效果
            center_x, center_y = width // 2, height // 2
            dx = x - center_x
            dy = y - center_y
            distance = np.sqrt(dx**2 + dy**2)

            scale = 1 + amplitude / 1000.0
            x_new = center_x + dx * scale
            y_new = center_y + dy * scale

        else:
            return frame

        # 应用变形
        x_new = np.clip(x_new, 0, width - 1).astype(np.float32)
        y_new = np.clip(y_new, 0, height - 1).astype(np.float32)

        if len(frame.shape) == 3:
            result = np.zeros_like(frame)
            for i in range(frame.shape[2]):
                result[:, :, i] = cv2.remap(frame[:, :, i], x_new, y_new, cv2.INTER_LINEAR)
        else:
            result = cv2.remap(frame, x_new, y_new, cv2.INTER_LINEAR)

        return result


class GreenScreenEffect(VideoEffect):
    """绿屏抠像特效"""

    def __init__(self):
        super().__init__("green_screen")
        self.parameters = {
            'key_color': EffectParameter('key_color', [0, 255, 0], None, None, 'vector3'),
            'tolerance': EffectParameter('tolerance', 30.0, 0.0, 100.0),
            'edge_feather': EffectParameter('edge_feather', 2.0, 0.0, 10.0),
            'spill_suppression': EffectParameter('spill_suppression', 0.5, 0.0, 1.0)
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        key_color = np.array(parameters.get('key_color', [0, 255, 0]))
        tolerance = parameters.get('tolerance', 30.0)
        edge_feather = parameters.get('edge_feather', 2.0)
        spill_suppression = parameters.get('spill_suppression', 0.5)

        # 计算到关键色的距离
        frame_float = frame.astype(np.float32)
        distance = np.sqrt(np.sum((frame_float - key_color)**2, axis=2))

        # 创建alpha通道
        alpha = (distance / tolerance).clip(0, 1)

        # 边缘羽化
        if edge_feather > 0:
            alpha = cv2.GaussianBlur(alpha, (int(edge_feather * 2 + 1), int(edge_feather * 2 + 1)), 0)

        # 色溢抑制
        if spill_suppression > 0:
            green_channel = frame[:, :, 1]
            spill_mask = (green_channel > (frame[:, :, 0] + frame[:, :, 2]) / 2).astype(np.float32)
            spill_mask = cv2.GaussianBlur(spill_mask, (5, 5), 0)

            frame[:, :, 1] = frame[:, :, 1] * (1 - spill_mask * spill_suppression)

        # 应用alpha通道
        result = frame.copy()
        result = np.dstack([result, (alpha * 255).astype(np.uint8)])

        return result


class MotionBlurEffect(VideoEffect):
    """运动模糊特效"""

    def __init__(self):
        super().__init__("motion_blur")
        self.parameters = {
            'direction': EffectParameter('direction', 0.0, 0.0, 360.0),
            'length': EffectParameter('length', 10.0, 0.0, 100.0),
            'samples': EffectParameter('samples', 10, 2, 50, 'int')
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        direction = parameters.get('direction', 0.0)
        length = parameters.get('length', 10.0)
        samples = parameters.get('samples', 10)

        if length == 0:
            return frame

        # 计算运动向量
        angle_rad = np.radians(direction)
        dx = length * np.cos(angle_rad)
        dy = length * np.sin(angle_rad)

        # 创建运动模糊核
        kernel_size = int(length) + 2
        if kernel_size % 2 == 0:
            kernel_size += 1

        kernel = np.zeros((kernel_size, kernel_size))
        center = kernel_size // 2

        for i in range(samples):
            t = i / (samples - 1)
            x = int(center + dx * t - dx / 2)
            y = int(center + dy * t - dy / 2)

            if 0 <= x < kernel_size and 0 <= y < kernel_size:
                kernel[y, x] = 1.0 / samples

        # 应用运动模糊
        return cv2.filter2D(frame, -1, kernel)


class ChromaticAberrationEffect(VideoEffect):
    """色差特效"""

    def __init__(self):
        super().__init__("chromatic_aberration")
        self.parameters = {
            'intensity': EffectParameter('intensity', 5.0, 0.0, 20.0),
            'direction': EffectParameter('direction', 0.0, 0.0, 360.0)
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        intensity = parameters.get('intensity', 5.0)
        direction = parameters.get('direction', 0.0)

        if intensity == 0:
            return frame

        height, width = frame.shape[:2]

        # 计算偏移
        angle_rad = np.radians(direction)
        dx_red = intensity * np.cos(angle_rad)
        dy_red = intensity * np.sin(angle_rad)
        dx_blue = -dx_red
        dy_blue = -dy_red

        # 创建坐标网格
        x, y = np.meshgrid(np.arange(width), np.arange(height))

        # 应用色差
        result = np.zeros_like(frame)

        # 红色通道偏移
        x_red = np.clip(x + dx_red, 0, width - 1).astype(np.float32)
        y_red = np.clip(y + dy_red, 0, height - 1).astype(np.float32)
        result[:, :, 0] = cv2.remap(frame[:, :, 0], x_red, y_red, cv2.INTER_LINEAR)

        # 绿色通道保持原位
        result[:, :, 1] = frame[:, :, 1]

        # 蓝色通道偏移
        x_blue = np.clip(x + dx_blue, 0, width - 1).astype(np.float32)
        y_blue = np.clip(y + dy_blue, 0, height - 1).astype(np.float32)
        result[:, :, 2] = cv2.remap(frame[:, :, 2], x_blue, y_blue, cv2.INTER_LINEAR)

        return result


class VignetteEffect(VideoEffect):
    """暗角特效"""

    def __init__(self):
        super().__init__("vignette")
        self.parameters = {
            'intensity': EffectParameter('intensity', 0.5, 0.0, 1.0),
            'radius': EffectParameter('radius', 0.5, 0.1, 1.0),
            'feather': EffectParameter('feather', 0.3, 0.0, 1.0),
            'center_x': EffectParameter('center_x', 0.5, 0.0, 1.0),
            'center_y': EffectParameter('center_y', 0.5, 0.0, 1.0)
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        intensity = parameters.get('intensity', 0.5)
        radius = parameters.get('radius', 0.5)
        feather = parameters.get('feather', 0.3)
        center_x = parameters.get('center_x', 0.5)
        center_y = parameters.get('center_y', 0.5)

        height, width = frame.shape[:2]

        # 创建渐变mask
        x = np.linspace(0, 1, width)
        y = np.linspace(0, 1, height)
        X, Y = np.meshgrid(x, y)

        # 计算到中心的距离
        dx = X - center_x
        dy = Y - center_y
        distance = np.sqrt(dx**2 + dy**2)

        # 创建渐变
        gradient = np.where(distance < radius,
                          1.0,
                          1.0 - ((distance - radius) / (1.0 - radius))**2)

        # 应用羽化
        gradient = np.clip(gradient / feather, 0, 1)

        # 应用暗角效果
        result = frame.astype(np.float32) / 255.0
        for i in range(result.shape[2]):
            result[:, :, i] *= gradient

        # 混合原图
        result = result * intensity + (frame.astype(np.float32) / 255.0) * (1 - intensity)

        return (result * 255).astype(np.uint8)


class FilmGrainEffect(VideoEffect):
    """胶片颗粒特效"""

    def __init__(self):
        super().__init__("film_grain")
        self.parameters = {
            'intensity': EffectParameter('intensity', 0.5, 0.0, 1.0),
            'size': EffectParameter('size', 1.0, 0.5, 5.0),
            'roughness': EffectParameter('roughness', 0.5, 0.0, 1.0)
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        intensity = parameters.get('intensity', 0.5)
        size = parameters.get('size', 1.0)
        roughness = parameters.get('roughness', 0.5)

        height, width = frame.shape[:2]

        # 生成噪声
        noise = np.random.normal(0, 1, (height, width))

        # 调整噪声大小
        if size > 1:
            noise = cv2.resize(noise, (int(width // size), int(height // size)))
            noise = cv2.resize(noise, (width, height))

        # 应用粗糙度
        noise = np.sign(noise) * np.abs(noise) ** (1 + roughness)

        # 归一化噪声
        noise = (noise - noise.min()) / (noise.max() - noise.min())

        # 应用噪声
        result = frame.astype(np.float32) / 255.0
        grain = noise.reshape(height, width, 1)
        grain = np.repeat(grain, frame.shape[2], axis=2)

        result = result + (grain - 0.5) * intensity * 0.3
        result = np.clip(result, 0, 1)

        return (result * 255).astype(np.uint8)


class ColorCorrectionEffect(VideoEffect):
    """色彩校正特效"""

    def __init__(self):
        super().__init__("color_correction")
        self.parameters = {
            'brightness': EffectParameter('brightness', 0.0, -1.0, 1.0),
            'contrast': EffectParameter('contrast', 1.0, 0.0, 2.0),
            'saturation': EffectParameter('saturation', 1.0, 0.0, 2.0),
            'hue': EffectParameter('hue', 0.0, -180.0, 180.0),
            'gamma': EffectParameter('gamma', 1.0, 0.1, 3.0)
        }

    def apply(self, frame: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        brightness = parameters.get('brightness', 0.0)
        contrast = parameters.get('contrast', 1.0)
        saturation = parameters.get('saturation', 1.0)
        hue = parameters.get('hue', 0.0)
        gamma = parameters.get('gamma', 1.0)

        # 转换为浮点型
        result = frame.astype(np.float32) / 255.0

        # 亮度调整
        result = result + brightness

        # 对比度调整
        result = (result - 0.5) * contrast + 0.5

        # Gamma校正
        if gamma != 1.0:
            result = np.power(result, 1.0 / gamma)

        # 色相和饱和度调整
        if saturation != 1.0 or hue != 0.0:
            # 转换到HSV
            hsv = cv2.cvtColor(result, cv2.COLOR_RGB2HSV)

            # 调整饱和度
            hsv[:, :, 1] = hsv[:, :, 1] * saturation
            hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 1)

            # 调整色相
            if hue != 0.0:
                hsv[:, :, 0] = (hsv[:, :, 0] + hue / 360.0) % 1.0

            # 转换回RGB
            result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        # 限制范围
        result = np.clip(result, 0, 1)

        return (result * 255).astype(np.uint8)


class VideoTransition:
    """视频转场基类"""

    def __init__(self, name: str):
        self.name = name
        self.parameters: Dict[str, EffectParameter] = {}

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        """应用转场"""
        raise NotImplementedError


class DissolveTransition(VideoTransition):
    """溶解转场"""

    def __init__(self):
        super().__init__("dissolve")
        self.parameters = {
            'duration': EffectParameter('duration', 1.0, 0.1, 5.0),
            'ease': EffectParameter('ease', 'linear', None, None, 'str')
        }

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        # 应用缓动函数
        ease_type = parameters.get('ease', 'linear')
        if ease_type == 'ease_in':
            progress = progress * progress
        elif ease_type == 'ease_out':
            progress = 1 - (1 - progress) * (1 - progress)
        elif ease_type == 'ease_in_out':
            progress = progress * progress * (3 - 2 * progress)

        # 混合两帧
        return cv2.addWeighted(frame1, 1 - progress, frame2, progress, 0)


class FadeTransition(VideoTransition):
    """淡入淡出转场"""

    def __init__(self):
        super().__init__("fade")
        self.parameters = {
            'fade_to_color': EffectParameter('fade_to_color', [0, 0, 0], None, None, 'vector3'),
            'mid_point': EffectParameter('mid_point', 0.5, 0.0, 1.0)
        }

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        fade_color = np.array(parameters.get('fade_to_color', [0, 0, 0]))
        mid_point = parameters.get('mid_point', 0.5)

        if progress < mid_point:
            # 淡出到颜色
            alpha = progress / mid_point
            return cv2.addWeighted(frame1, 1 - alpha,
                                 np.full_like(frame1, fade_color), alpha, 0)
        else:
            # 从颜色淡入
            alpha = (progress - mid_point) / (1 - mid_point)
            return cv2.addWeighted(np.full_like(frame2, fade_color), 1 - alpha,
                                 frame2, alpha, 0)


class WipeTransition(VideoTransition):
    """擦除转场"""

    def __init__(self):
        super().__init__("wipe")
        self.parameters = {
            'direction': EffectParameter('direction', 'left', None, None, 'str'),
            'softness': EffectParameter('softness', 0.0, 0.0, 1.0)
        }

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        direction = parameters.get('direction', 'left')
        softness = parameters.get('softness', 0.0)

        height, width = frame.shape[:2]

        # 创建擦除mask
        mask = np.zeros((height, width), dtype=np.float32)

        if direction == 'left':
            mask[:, :int(width * progress)] = 1.0
        elif direction == 'right':
            mask[:, int(width * (1 - progress)):] = 1.0
        elif direction == 'top':
            mask[:int(height * progress), :] = 1.0
        elif direction == 'bottom':
            mask[int(height * (1 - progress)):, :] = 1.0
        elif direction == 'diagonal':
            for y in range(height):
                for x in range(width):
                    if (x / width + y / height) / 2 < progress:
                        mask[y, x] = 1.0

        # 应用软边缘
        if softness > 0:
            mask = cv2.GaussianBlur(mask, (int(softness * 20 + 1), int(softness * 20 + 1)), 0)

        # 应用转场
        mask = np.repeat(mask[:, :, np.newaxis], 3, axis=2)
        return frame1 * (1 - mask) + frame2 * mask


class PushTransition(VideoTransition):
    """推动转场"""

    def __init__(self):
        super().__init__("push")
        self.parameters = {
            'direction': EffectParameter('direction', 'left', None, None, 'str'),
            'smoothness': EffectParameter('smoothness', 0.5, 0.0, 1.0)
        }

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        direction = parameters.get('direction', 'left')
        smoothness = parameters.get('smoothness', 0.5)

        height, width = frame.shape[:2]
        result = np.zeros_like(frame1)

        # 计算偏移量
        if direction == 'left':
            offset_x = int(width * progress)
            # frame1 向左移动
            if offset_x < width:
                result[:, :width - offset_x] = frame1[:, offset_x:]
            # frame2 从右侧进入
            if offset_x > 0:
                result[:, offset_x:] = frame2[:, :width - offset_x]

        elif direction == 'right':
            offset_x = int(width * progress)
            # frame1 向右移动
            if offset_x < width:
                result[:, offset_x:] = frame1[:, :width - offset_x]
            # frame2 从左侧进入
            if offset_x > 0:
                result[:, :width - offset_x] = frame2[:, offset_x:]

        elif direction == 'top':
            offset_y = int(height * progress)
            # frame1 向上移动
            if offset_y < height:
                result[:height - offset_y, :] = frame1[offset_y:, :]
            # frame2 从下方进入
            if offset_y > 0:
                result[offset_y:, :] = frame2[:height - offset_y, :]

        elif direction == 'bottom':
            offset_y = int(height * progress)
            # frame1 向下移动
            if offset_y < height:
                result[offset_y:, :] = frame1[:height - offset_y, :]
            # frame2 从上方进入
            if offset_y > 0:
                result[:height - offset_y, :] = frame2[offset_y:, :]

        return result.astype(np.uint8)


class SlideTransition(VideoTransition):
    """滑动转场"""

    def __init__(self):
        super().__init__("slide")
        self.parameters = {
            'direction': EffectParameter('direction', 'left', None, None, 'str'),
            'slide_in': EffectParameter('slide_in', True, None, None, 'bool')
        }

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        direction = parameters.get('direction', 'left')
        slide_in = parameters.get('slide_in', True)

        height, width = frame.shape[:2]
        result = frame1.copy()

        # 计算位置
        if direction == 'left':
            offset_x = int(width * progress)
            if slide_in:
                # frame2 从左侧滑入
                if offset_x > 0:
                    result[:, :offset_x] = frame2[:, width - offset_x:]
            else:
                # frame1 向左滑出
                if offset_x < width:
                    result[:, :width - offset_x] = frame1[:, offset_x:]

        elif direction == 'right':
            offset_x = int(width * progress)
            if slide_in:
                # frame2 从右侧滑入
                if offset_x > 0:
                    result[:, offset_x:] = frame2[:, :width - offset_x]
            else:
                # frame1 向右滑出
                if offset_x < width:
                    result[:, offset_x:] = frame1[:, :width - offset_x]

        return result


class RotateTransition(VideoTransition):
    """旋转转场"""

    def __init__(self):
        super().__init__("rotate")
        self.parameters = {
            'direction': EffectParameter('direction', 'clockwise', None, None, 'str'),
            'center_x': EffectParameter('center_x', 0.5, 0.0, 1.0),
            'center_y': EffectParameter('center_y', 0.5, 0.0, 1.0)
        }

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        direction = parameters.get('direction', 'clockwise')
        center_x = parameters.get('center_x', 0.5)
        center_y = parameters.get('center_y', 0.5)

        height, width = frame.shape[:2]
        center = (int(width * center_x), int(height * center_y))

        # 计算旋转角度
        angle = progress * 90
        if direction == 'counterclockwise':
            angle = -angle

        # 创建旋转矩阵
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        # 旋转frame1
        rotated_frame1 = cv2.warpAffine(frame1, rotation_matrix, (width, height))

        # 旋转frame2（反向）
        rotation_matrix2 = cv2.getRotationMatrix2D(center, -angle, 1.0)
        rotated_frame2 = cv2.warpAffine(frame2, rotation_matrix2, (width, height))

        # 混合结果
        return cv2.addWeighted(rotated_frame1, 1 - progress, rotated_frame2, progress, 0)


class ZoomTransition(VideoTransition):
    """缩放转场"""

    def __init__(self):
        super().__init__("zoom")
        self.parameters = {
            'direction': EffectParameter('direction', 'in', None, None, 'str'),
            'center_x': EffectParameter('center_x', 0.5, 0.0, 1.0),
            'center_y': EffectParameter('center_y', 0.5, 0.0, 1.0)
        }

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        direction = parameters.get('direction', 'in')
        center_x = parameters.get('center_x', 0.5)
        center_y = parameters.get('center_y', 0.5)

        height, width = frame.shape[:2]
        center = (int(width * center_x), int(height * center_y))

        if direction == 'in':
            # 从frame1缩小到frame2放大
            scale1 = 1.0 - progress * 0.5
            scale2 = 0.5 + progress * 0.5
        else:
            # 从frame1放大到frame2缩小
            scale1 = 1.0 + progress * 0.5
            scale2 = 1.0 - progress * 0.5

        # 缩放frame1
        matrix1 = cv2.getRotationMatrix2D(center, 0, scale1)
        scaled_frame1 = cv2.warpAffine(frame1, matrix1, (width, height))

        # 缩放frame2
        matrix2 = cv2.getRotationMatrix2D(center, 0, scale2)
        scaled_frame2 = cv2.warpAffine(frame2, matrix2, (width, height))

        # 混合结果
        return cv2.addWeighted(scaled_frame1, 1 - progress, scaled_frame2, progress, 0)


class CircleTransition(VideoTransition):
    """圆形转场"""

    def __init__(self):
        super().__init__("circle")
        self.parameters = {
            'direction': EffectParameter('direction', 'out', None, None, 'str'),
            'center_x': EffectParameter('center_x', 0.5, 0.0, 1.0),
            'center_y': EffectParameter('center_y', 0.5, 0.0, 1.0),
            'softness': EffectParameter('softness', 0.1, 0.0, 1.0)
        }

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        direction = parameters.get('direction', 'out')
        center_x = parameters.get('center_x', 0.5)
        center_y = parameters.get('center_y', 0.5)
        softness = parameters.get('softness', 0.1)

        height, width = frame.shape[:2]
        center = (int(width * center_x), int(height * center_y))

        # 创建圆形mask
        y, x = np.ogrid[:height, :width]
        distance = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        max_radius = np.sqrt(width**2 + height**2) / 2

        if direction == 'out':
            # 从中心向外扩展
            radius = progress * max_radius
            mask = (distance <= radius).astype(np.float32)
        else:
            # 从外向内收缩
            radius = (1 - progress) * max_radius
            mask = (distance >= radius).astype(np.float32)

        # 应用软边缘
        if softness > 0:
            edge_width = max_radius * softness
            edge_mask = np.abs(distance - radius) / edge_width
            edge_mask = np.clip(edge_mask, 0, 1)
            mask = mask * (1 - edge_mask) + edge_mask * 0.5

        # 应用转场
        mask = np.repeat(mask[:, :, np.newaxis], 3, axis=2)
        return frame1 * (1 - mask) + frame2 * mask


class BlurTransition(VideoTransition):
    """模糊转场"""

    def __init__(self):
        super().__init__("blur")
        self.parameters = {
            'max_blur': EffectParameter('max_blur', 20.0, 1.0, 50.0),
            'blur_type': EffectParameter('blur_type', 'gaussian', None, None, 'str')
        }

    def apply(self, frame1: np.ndarray, frame2: np.ndarray,
              progress: float, parameters: Dict[str, Any]) -> np.ndarray:
        max_blur = parameters.get('max_blur', 20.0)
        blur_type = parameters.get('blur_type', 'gaussian')

        # 模糊frame1
        blur_amount = max_blur * (1 - progress)
        if blur_amount > 0:
            kernel_size = int(blur_amount * 2) + 1
            if kernel_size % 2 == 0:
                kernel_size += 1

            if blur_type == 'gaussian':
                blurred_frame1 = cv2.GaussianBlur(frame1, (kernel_size, kernel_size), 0)
            else:
                blurred_frame1 = cv2.blur(frame1, (kernel_size, kernel_size))
        else:
            blurred_frame1 = frame1

        # 混合结果
        return cv2.addWeighted(blurred_frame1, 1 - progress, frame2, progress, 0)


class EffectChain:
    """特效链"""

    def __init__(self, engine: EffectEngine):
        self.engine = engine
        self.effects: List[Tuple[str, Dict[str, Any]]] = []

    def add_effect(self, effect_name: str, parameters: Dict[str, Any] = None):
        """添加特效"""
        if effect_name in self.engine.effects:
            self.effects.append((effect_name, parameters or {}))

    def remove_effect(self, index: int):
        """移除特效"""
        if 0 <= index < len(self.effects):
            self.effects.pop(index)

    def apply(self, frame: np.ndarray) -> np.ndarray:
        """应用特效链"""
        result = frame.copy()
        for effect_name, parameters in self.effects:
            result = self.engine.apply_effect(result, effect_name, parameters)
        return result

    def clear(self):
        """清空特效链"""
        self.effects.clear()


class KeyframeAnimator:
    """关键帧动画器"""

    def __init__(self):
        self.keyframes: Dict[str, List[Keyframe]] = {}
        self.duration = 0.0

    def add_keyframe(self, parameter_name: str, time: float, value: float,
                   easing: str = 'linear', interpolation: str = 'linear'):
        """添加关键帧"""
        if parameter_name not in self.keyframes:
            self.keyframes[parameter_name] = []

        keyframe = Keyframe(time, value, easing, interpolation)
        self.keyframes[parameter_name].append(keyframe)
        self.keyframes[parameter_name].sort(key=lambda k: k.time)

        if time > self.duration:
            self.duration = time

    def get_value(self, parameter_name: str, time: float) -> float:
        """获取指定时间的参数值"""
        if parameter_name not in self.keyframes:
            return 0.0

        keyframes = self.keyframes[parameter_name]
        if not keyframes:
            return 0.0

        # 找到当前时间对应的关键帧
        for i in range(len(keyframes) - 1):
            if keyframes[i].time <= time <= keyframes[i + 1].time:
                k1 = keyframes[i]
                k2 = keyframes[i + 1]

                # 计算进度
                progress = (time - k1.time) / (k2.time - k1.time)

                # 应用缓动
                progress = self._apply_easing(progress, k1.easing)

                # 插值
                return self._interpolate(k1.value, k2.value, progress, k1.interpolation)

        # 如果超出范围，返回最近的关键帧值
        if time <= keyframes[0].time:
            return keyframes[0].value
        else:
            return keyframes[-1].value

    def _apply_easing(self, progress: float, easing: str) -> float:
        """应用缓动函数"""
        if easing == 'linear':
            return progress
        elif easing == 'ease_in':
            return progress * progress
        elif easing == 'ease_out':
            return 1 - (1 - progress) * (1 - progress)
        elif easing == 'ease_in_out':
            return progress * progress * (3 - 2 * progress)
        else:
            return progress

    def _interpolate(self, value1: float, value2: float,
                    progress: float, interpolation: str) -> float:
        """插值"""
        if interpolation == 'linear':
            return value1 + (value2 - value1) * progress
        elif interpolation == 'step':
            return value2 if progress >= 0.5 else value1
        else:
            return value1 + (value2 - value1) * progress


class ParticleSystem:
    """粒子系统"""

    def __init__(self):
        self.particles: List[Dict[str, Any]] = []
        self.max_particles = 1000
        self.emission_rate = 10
        self.particle_lifetime = 2.0

    def emit(self, position: Tuple[float, float], velocity: Tuple[float, float],
             color: Tuple[int, int, int], size: float, lifetime: float):
        """发射粒子"""
        if len(self.particles) < self.max_particles:
            particle = {
                'position': list(position),
                'velocity': list(velocity),
                'color': color,
                'size': size,
                'lifetime': lifetime,
                'age': 0.0
            }
            self.particles.append(particle)

    def update(self, dt: float):
        """更新粒子系统"""
        for particle in self.particles[:]:
            particle['age'] += dt

            if particle['age'] >= particle['lifetime']:
                self.particles.remove(particle)
                continue

            # 更新位置
            particle['position'][0] += particle['velocity'][0] * dt
            particle['position'][1] += particle['velocity'][1] * dt

            # 应用重力
            particle['velocity'][1] += 9.8 * dt

    def render(self, frame: np.ndarray) -> np.ndarray:
        """渲染粒子"""
        result = frame.copy()

        for particle in self.particles:
            x, y = int(particle['position'][0]), int(particle['position'][1])

            if 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
                # 计算透明度
                alpha = 1.0 - (particle['age'] / particle['lifetime'])

                # 绘制粒子
                cv2.circle(result, (x, y), int(particle['size']),
                         particle['color'], -1)

        return result


# 初始化特效引擎
effect_engine = EffectEngine()

# 导出主要类和函数
__all__ = [
    'EffectEngine',
    'VideoEffect',
    'VideoTransition',
    'EffectChain',
    'KeyframeAnimator',
    'ParticleSystem',
    'EffectType',
    'TransitionType',
    'BlendMode',
    'Keyframe',
    'EffectParameter',
    'effect_engine'
]