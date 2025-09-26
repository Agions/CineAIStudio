#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 高级特效系统模块
专业级视频特效处理系统，支持实时GPU加速、复杂特效链和 After Effects 级别的特效处理
"""

import os
import time
import math
import numpy as np
import cv2
import threading
import uuid
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from pathlib import Path
import json
import copy
import weakref
from contextlib import contextmanager

from .logger import get_logger
from .event_system import EventBus
from .service_container import ServiceContainer
from .video_engine import get_video_engine, EngineState
from .timeline_engine import get_timeline_engine, TimelineEngine, Clip, Track
from .keyframe_system import get_keyframe_system, KeyframeSystem, Keyframe
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import get_ffmpeg_utils, VideoInfo


class EffectType(Enum):
    """特效类型枚举"""
    BLUR = "blur"
    SHARPEN = "sharpen"
    GLOW = "glow"
    DISTORT = "distort"
    COLOR_CORRECTION = "color_correction"
    TRANSITION = "transition"
    PARTICLE = "particle"
    MOTION_GRAPHICS = "motion_graphics"
    TEXT_ANIMATION = "text_animation"
    CHROMA_KEY = "chroma_key"
    MASKING = "masking"
    STABILIZATION = "stabilization"
    TRACKING = "tracking"
    COLOR_GRADING = "color_grading"
    NOISE_REDUCTION = "noise_reduction"
    MOTION_BLUR = "motion_blur"
    DEPTH_OF_FIELD = "depth_of_field"
    LENS_FLARE = "lens_flare"
    GLITCH = "glitch"
    VIGNETTE = "vignette"


class BlendMode(Enum):
    """混合模式枚举"""
    NORMAL = "normal"
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"
    DARKEN = "darken"
    LIGHTEN = "lighten"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"
    DIFFERENCE = "difference"
    EXCLUSION = "exclusion"
    HUE = "hue"
    SATURATION = "saturation"
    COLOR = "color"
    LUMINOSITY = "luminosity"


class TransitionType(Enum):
    """转场类型枚举"""
    DISSOLVE = "dissolve"
    FADE = "fade"
    WIPE = "wipe"
    SLIDE = "slide"
    PUSH = "push"
    ZOOM = "zoom"
    ROTATE = "rotate"
    FLIP = "flip"
    MORPH = "morph"
    PARTICLE_DISSOLVE = "particle_dissolve"
    LIQUID = "liquid"
    GLITCH = "glitch"
    LIGHT_LEAK = "light_leak"
    FILM_BURN = "film_burn"
    SHAPE_TRANSITION = "shape_transition"


class ParticleSystemType(Enum):
    """粒子系统类型枚举"""
    FIRE = "fire"
    SMOKE = "smoke"
    SPARKS = "sparks"
    SNOW = "snow"
    RAIN = "rain"
    BUBBLES = "bubbles"
    STARS = "stars"
    CONFETTI = "confetti"
    MAGIC_DUST = "magic_dust"
    ENERGY = "energy"
    PLASMA = "plasma"


@dataclass
class EffectParameter:
    """特效参数"""
    name: str
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Any = None
    type: str = "float"  # float, int, bool, string, color
    description: str = ""
    keyframable: bool = True
    animated: bool = False


@dataclass
class EffectSettings:
    """特效设置"""
    enabled: bool = True
    intensity: float = 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    opacity: float = 1.0
    mask_enabled: bool = False
    mask_path: Optional[str] = None
    invert_mask: bool = False
    feather_edges: float = 0.0
    gpu_accelerated: bool = True
    quality: str = "high"  # low, medium, high, ultra
    preview_quality: str = "medium"


@dataclass
class GPUShader:
    """GPU着色器"""
    vertex_shader: str
    fragment_shader: str
    compute_shader: Optional[str] = None
    uniform_vars: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EffectChain:
    """特效链"""
    id: str
    name: str
    effects: List[str] = field(default_factory=list)  # effect IDs
    enabled: bool = True
    global_settings: EffectSettings = field(default_factory=EffectSettings)
    render_order: List[str] = field(default_factory=list)


@dataclass
class Transition:
    """转场效果"""
    id: str
    name: str
    transition_type: TransitionType
    duration: float = 1.0
    settings: Dict[str, Any] = field(default_factory=dict)
    ease_function: str = "ease_in_out"
    preview_frame: Optional[np.ndarray] = None


@dataclass
class Particle:
    """粒子"""
    id: str
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: float = 0.0
    rotation_speed: float = 0.0
    scale: float = 1.0
    life: float = 1.0
    max_life: float = 1.0
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    size: float = 1.0
    mass: float = 1.0
    custom_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParticleSystem:
    """粒子系统"""
    id: str
    name: str
    system_type: ParticleSystemType
    particles: List[Particle] = field(default_factory=list)
    max_particles: int = 1000
    emission_rate: float = 10.0
    lifetime: float = 5.0
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity_range: Tuple[Tuple[float, float, float], Tuple[float, float, float]] = ((-1, -1, -1), (1, 1, 1))
    size_range: Tuple[float, float] = (0.1, 1.0)
    color_range: Tuple[Tuple[float, float, float, float], Tuple[float, float, float, float]] = ((1, 1, 1, 1), (1, 1, 1, 1))
    gravity: float = 0.0
    wind: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    enabled: bool = True
    loop: bool = True
    gpu_accelerated: bool = True


class Effect(ABC):
    """特效抽象基类"""

    def __init__(self, effect_id: str, name: str, effect_type: EffectType):
        self.id = effect_id
        self.name = name
        self.type = effect_type
        self.settings = EffectSettings()
        self.parameters: Dict[str, EffectParameter] = {}
        self.keyframe_system = get_keyframe_system()
        self.logger = get_logger(f"Effect_{name}")
        self.gpu_available = False
        self.shader: Optional[GPUShader] = None
        self._initialize_parameters()

    @abstractmethod
    def _initialize_parameters(self) -> None:
        """初始化特效参数"""
        pass

    @abstractmethod
    def apply(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用特效到帧"""
        pass

    @abstractmethod
    def apply_gpu(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        """使用GPU应用特效"""
        pass

    def get_parameter_value(self, param_name: str, time: float = 0.0) -> Any:
        """获取参数值（支持关键帧）"""
        param = self.parameters.get(param_name)
        if not param:
            return None

        if param.animated:
            # 从关键帧系统获取值
            return self.keyframe_system.get_keyframe_value(self.id, param_name, time)
        else:
            return param.value

    def set_parameter_value(self, param_name: str, value: Any) -> bool:
        """设置参数值"""
        param = self.parameters.get(param_name)
        if not param:
            return False

        param.value = value
        return True

    def add_keyframe(self, param_name: str, time: float, value: Any) -> bool:
        """添加关键帧"""
        param = self.parameters.get(param_name)
        if not param or not param.keyframable:
            return False

        return self.keyframe_system.add_keyframe(self.id, param_name, time, value) is not None

    def remove_keyframe(self, param_name: str, keyframe_id: str) -> bool:
        """移除关键帧"""
        return self.keyframe_system.remove_keyframe(self.id, param_name, keyframe_id)

    def compile_shader(self) -> bool:
        """编译着色器"""
        if not self.shader:
            return False

        try:
            # 这里应该实现实际的着色器编译逻辑
            # 使用 OpenGL/Vulkan/Metal 等 API
            self.gpu_available = True
            return True
        except Exception as e:
            self.logger.error(f"着色器编译失败: {e}")
            return False

    def process(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        """处理帧"""
        if self.settings.gpu_accelerated and self.gpu_available:
            return self.apply_gpu(frame, time)
        else:
            return self.apply(frame, time)


class BlurEffect(Effect):
    """模糊特效"""

    def __init__(self, effect_id: str):
        super().__init__(effect_id, "Gaussian Blur", EffectType.BLUR)
        self.kernel_size = 5
        self.sigma = 1.0

    def _initialize_parameters(self) -> None:
        self.parameters['radius'] = EffectParameter(
            name="radius",
            value=5.0,
            min_value=0.1,
            max_value=50.0,
            default_value=5.0,
            type="float",
            description="模糊半径",
            keyframable=True
        )
        self.parameters['quality'] = EffectParameter(
            name="quality",
            value=3,
            min_value=1,
            max_value=5,
            default_value=3,
            type="int",
            description="模糊质量",
            keyframable=False
        )

    def apply(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        radius = self.get_parameter_value('radius', time)
        quality = int(self.get_parameter_value('quality', time))

        # 动态计算核大小
        ksize = int(radius * 2) + 1
        if ksize % 2 == 0:
            ksize += 1

        # 多次迭代提高质量
        result = frame.copy()
        for _ in range(quality):
            result = cv2.GaussianBlur(result, (ksize, ksize), radius)

        return result

    def apply_gpu(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        # GPU 实现会使用 OpenGL/Vulkan/Metal 着色器
        return self.apply(frame, time)


class GlowEffect(Effect):
    """发光特效"""

    def __init__(self, effect_id: str):
        super().__init__(effect_id, "Glow", EffectType.GLOW)
        self.threshold = 0.5
        self.intensity = 1.0
        self.color = (255, 255, 255)

    def _initialize_parameters(self) -> None:
        self.parameters['threshold'] = EffectParameter(
            name="threshold",
            value=0.5,
            min_value=0.0,
            max_value=1.0,
            default_value=0.5,
            type="float",
            description="发光阈值",
            keyframable=True
        )
        self.parameters['intensity'] = EffectParameter(
            name="intensity",
            value=1.0,
            min_value=0.0,
            max_value=10.0,
            default_value=1.0,
            type="float",
            description="发光强度",
            keyframable=True
        )
        self.parameters['color'] = EffectParameter(
            name="color",
            value=(255, 255, 255),
            type="color",
            description="发光颜色",
            keyframable=True
        )
        self.parameters['blur_radius'] = EffectParameter(
            name="blur_radius",
            value=10.0,
            min_value=1.0,
            max_value=100.0,
            default_value=10.0,
            type="float",
            description="模糊半径",
            keyframable=True
        )

    def apply(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        threshold = self.get_parameter_value('threshold', time)
        intensity = self.get_parameter_value('intensity', time)
        color = self.get_parameter_value('color', time)
        blur_radius = self.get_parameter_value('blur_radius', time)

        # 转换为 float32 处理
        frame_float = frame.astype(np.float32) / 255.0

        # 创建发光层
        gray = cv2.cvtColor(frame_float, cv2.COLOR_BGR2GRAY)
        mask = np.where(gray > threshold, 1.0, 0.0)

        # 应用颜色
        color_normalized = np.array(color) / 255.0
        glow_layer = np.zeros_like(frame_float)
        for i in range(3):
            glow_layer[:, :, i] = mask * color_normalized[i]

        # 模糊发光层
        ksize = int(blur_radius * 2) + 1
        if ksize % 2 == 0:
            ksize += 1
        glow_layer = cv2.GaussianBlur(glow_layer, (ksize, ksize), blur_radius)

        # 混合发光效果
        result = frame_float + glow_layer * intensity
        result = np.clip(result, 0, 1)

        return (result * 255).astype(np.uint8)

    def apply_gpu(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        return self.apply(frame, time)


class ChromaKeyEffect(Effect):
    """绿屏抠像特效"""

    def __init__(self, effect_id: str):
        super().__init__(effect_id, "Chroma Key", EffectType.CHROMA_KEY)
        self.key_color = (0, 255, 0)  # 绿色
        self.tolerance = 0.3
        self.softness = 0.1
        self.spill_reduction = 0.2

    def _initialize_parameters(self) -> None:
        self.parameters['key_color'] = EffectParameter(
            name="key_color",
            value=(0, 255, 0),
            type="color",
            description="抠像颜色",
            keyframable=True
        )
        self.parameters['tolerance'] = EffectParameter(
            name="tolerance",
            value=0.3,
            min_value=0.0,
            max_value=1.0,
            default_value=0.3,
            type="float",
            description="颜色容差",
            keyframable=True
        )
        self.parameters['softness'] = EffectParameter(
            name="softness",
            value=0.1,
            min_value=0.0,
            max_value=1.0,
            default_value=0.1,
            type="float",
            description="边缘柔和度",
            keyframable=True
        )
        self.parameters['spill_reduction'] = EffectParameter(
            name="spill_reduction",
            value=0.2,
            min_value=0.0,
            max_value=1.0,
            default_value=0.2,
            type="float",
            description="溢出抑制",
            keyframable=True
        )

    def apply(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        key_color = self.get_parameter_value('key_color', time)
        tolerance = self.get_parameter_value('tolerance', time)
        softness = self.get_parameter_value('softness', time)
        spill_reduction = self.get_parameter_value('spill_reduction', time)

        # 转换为 float32
        frame_float = frame.astype(np.float32) / 255.0
        key_color_float = np.array(key_color) / 255.0

        # 计算颜色差异
        diff = np.sqrt(np.sum((frame_float - key_color_float) ** 2, axis=2))

        # 创建蒙版
        mask = 1.0 - np.clip((diff - tolerance + softness) / softness, 0, 1)

        # 应用蒙版
        result = frame_float.copy()
        for i in range(3):
            result[:, :, i] *= mask

        # 溢出抑制
        if spill_reduction > 0:
            green_channel = frame_float[:, :, 1]
            spill_mask = np.maximum(0, green_channel - np.max(frame_float[:, :, [0, 2]], axis=2))
            result[:, :, 1] -= spill_mask * spill_reduction

        return (np.clip(result, 0, 1) * 255).astype(np.uint8)

    def apply_gpu(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        return self.apply(frame, time)


class TransitionEffect(Effect):
    """转场特效基类"""

    def __init__(self, effect_id: str, transition_type: TransitionType):
        super().__init__(effect_id, f"Transition_{transition_type.value}", EffectType.TRANSITION)
        self.transition_type = transition_type
        self.duration = 1.0
        self.progress = 0.0

    def _initialize_parameters(self) -> None:
        self.parameters['duration'] = EffectParameter(
            name="duration",
            value=1.0,
            min_value=0.1,
            max_value=10.0,
            default_value=1.0,
            type="float",
            description="转场持续时间",
            keyframable=False
        )
        self.parameters['progress'] = EffectParameter(
            name="progress",
            value=0.0,
            min_value=0.0,
            max_value=1.0,
            default_value=0.0,
            type="float",
            description="转场进度",
            keyframable=True
        )
        self.parameters['ease_function'] = EffectParameter(
            name="ease_function",
            value="ease_in_out",
            type="string",
            description="缓动函数",
            keyframable=False
        )

    def apply_transition(self, from_frame: np.ndarray, to_frame: np.ndarray, progress: float) -> np.ndarray:
        """应用转场效果"""
        raise NotImplementedError


class DissolveTransition(TransitionEffect):
    """溶解转场"""

    def __init__(self, effect_id: str):
        super().__init__(effect_id, TransitionType.DISSOLVE)

    def apply(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        progress = self.get_parameter_value('progress', time)
        # 溶解转场需要两帧，这里简化处理
        return frame

    def apply_transition(self, from_frame: np.ndarray, to_frame: np.ndarray, progress: float) -> np.ndarray:
        # 线性插值
        result = from_frame.astype(np.float32) * (1 - progress) + to_frame.astype(np.float32) * progress
        return np.clip(result, 0, 255).astype(np.uint8)

    def apply_gpu(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        return self.apply(frame, time)


class ParticleEffect(Effect):
    """粒子特效"""

    def __init__(self, effect_id: str, particle_system: ParticleSystem):
        super().__init__(effect_id, f"Particles_{particle_system.system_type.value}", EffectType.PARTICLE)
        self.particle_system = particle_system
        self.particle_positions = np.zeros((particle_system.max_particles, 2))
        self.particle_velocities = np.zeros((particle_system.max_particles, 2))
        self.particle_lives = np.zeros(particle_system.max_particles)
        self.particle_colors = np.zeros((particle_system.max_particles, 4))
        self.last_time = 0.0

    def _initialize_parameters(self) -> None:
        self.parameters['emission_rate'] = EffectParameter(
            name="emission_rate",
            value=10.0,
            min_value=0.1,
            max_value=1000.0,
            default_value=10.0,
            type="float",
            description="发射速率",
            keyframable=True
        )
        self.parameters['particle_lifetime'] = EffectParameter(
            name="particle_lifetime",
            value=5.0,
            min_value=0.1,
            max_value=100.0,
            default_value=5.0,
            type="float",
            description="粒子生命周期",
            keyframable=True
        )
        self.parameters['gravity'] = EffectParameter(
            name="gravity",
            value=0.0,
            min_value=-100.0,
            max_value=100.0,
            default_value=0.0,
            type="float",
            description="重力",
            keyframable=True
        )

    def update_particles(self, dt: float, frame_shape: Tuple[int, int]) -> None:
        """更新粒子系统"""
        emission_rate = self.get_parameter_value('emission_rate', 0.0)
        particle_lifetime = self.get_parameter_value('particle_lifetime', 0.0)
        gravity = self.get_parameter_value('gravity', 0.0)

        # 发射新粒子
        num_emit = int(emission_rate * dt)
        for i in range(self.particle_system.max_particles):
            if self.particle_lives[i] <= 0 and num_emit > 0:
                # 重置粒子
                self.particle_positions[i] = np.random.rand(2) * [frame_shape[1], frame_shape[0]]
                self.particle_velocities[i] = (np.random.rand(2) - 0.5) * 100
                self.particle_lives[i] = particle_lifetime
                self.particle_colors[i] = np.random.rand(4)
                self.particle_colors[i][3] = 1.0  # Alpha = 1
                num_emit -= 1

        # 更新粒子
        for i in range(self.particle_system.max_particles):
            if self.particle_lives[i] > 0:
                # 更新位置
                self.particle_positions[i] += self.particle_velocities[i] * dt
                self.particle_velocities[i][1] += gravity * dt  # 重力

                # 更新生命
                self.particle_lives[i] -= dt
                self.particle_colors[i][3] = max(0, self.particle_lives[i] / particle_lifetime)

                # 边界检查
                if (self.particle_positions[i][0] < 0 or self.particle_positions[i][0] >= frame_shape[1] or
                    self.particle_positions[i][1] < 0 or self.particle_positions[i][1] >= frame_shape[0]):
                    self.particle_lives[i] = 0

    def render_particles(self, frame: np.ndarray) -> np.ndarray:
        """渲染粒子到帧"""
        result = frame.copy()
        height, width = frame.shape[:2]

        for i in range(self.particle_system.max_particles):
            if self.particle_lives[i] > 0:
                x, y = int(self.particle_positions[i][0]), int(self.particle_positions[i][1])
                if 0 <= x < width and 0 <= y < height:
                    color = self.particle_colors[i]
                    alpha = color[3]

                    # 简单的圆形粒子
                    radius = 3
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            if dx*dx + dy*dy <= radius*radius:
                                px, py = x + dx, y + dy
                                if 0 <= px < width and 0 <= py < height:
                                    # 混合颜色
                                    blend_factor = alpha * (1 - (dx*dx + dy*dy) / (radius*radius))
                                    for c in range(3):
                                        result[py, px, c] = int(result[py, px, c] * (1 - blend_factor) + color[c] * 255 * blend_factor)

        return result

    def apply(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        dt = time - self.last_time
        self.last_time = time

        if dt > 0:
            self.update_particles(dt, frame.shape[:2])

        return self.render_particles(frame)

    def apply_gpu(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        return self.apply(frame, time)


class EffectProcessor:
    """特效处理器"""

    def __init__(self):
        self.logger = get_logger("EffectProcessor")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.service_container = ServiceContainer()

        # 特效管理
        self.effects: Dict[str, Effect] = {}
        self.effect_chains: Dict[str, EffectChain] = {}
        self.transitions: Dict[str, Transition] = {}
        self.particle_systems: Dict[str, ParticleSystem] = {}

        # GPU 加速
        self.gpu_context = None
        self.gpu_available = self._init_gpu()

        # 缓存
        self.frame_cache: Dict[str, np.ndarray] = {}
        self.effect_cache: Dict[str, Dict[float, np.ndarray]] = {}

        # 性能监控
        self.performance_stats = {
            'total_effects': 0,
            'active_effects': 0,
            'gpu_effects': 0,
            'cpu_effects': 0,
            'render_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # 初始化
        self._initialize()

    def _init_gpu(self) -> bool:
        """初始化GPU上下文"""
        try:
            # 检查 GPU 可用性
            # 这里可以集成 CUDA、OpenCL、Metal 等
            self.gpu_available = False  # 临时设置为 False，实际应该检测硬件
            return self.gpu_available
        except Exception as e:
            self.logger.error(f"GPU 初始化失败: {e}")
            return False

    def _initialize(self) -> None:
        """初始化特效处理器"""
        try:
            # 注册服务
            self._register_services()

            # 设置事件处理器
            self._setup_event_handlers()

            # 创建内置特效
            self._create_builtin_effects()

            self.logger.info("特效处理器初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"特效处理器初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="EffectProcessor",
                    operation="initialize"
                ),
                user_message="特效处理器初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _register_services(self) -> None:
        """注册服务"""
        try:
            self.service_container.register(EffectProcessor, self)
            self.service_container.register(EventBus, self.event_bus)
            self.logger.info("服务注册完成")
        except Exception as e:
            self.logger.error(f"服务注册失败: {e}")

    def _setup_event_handlers(self) -> None:
        """设置事件处理器"""
        try:
            self.event_bus.subscribe("effect_added", self._on_effect_added)
            self.event_bus.subscribe("effect_removed", self._on_effect_removed)
            self.event_bus.subscribe("effect_modified", self._on_effect_modified)
            self.logger.info("事件处理器设置完成")
        except Exception as e:
            self.logger.error(f"事件处理器设置失败: {e}")

    def _create_builtin_effects(self) -> None:
        """创建内置特效"""
        try:
            # 创建模糊特效
            blur_effect = BlurEffect("builtin_blur")
            self.effects[blur_effect.id] = blur_effect

            # 创建发光特效
            glow_effect = GlowEffect("builtin_glow")
            self.effects[glow_effect.id] = glow_effect

            # 创建绿屏抠像特效
            chroma_key_effect = ChromaKeyEffect("builtin_chroma_key")
            self.effects[chroma_key_effect.id] = chroma_key_effect

            # 创建溶解转场
            dissolve_transition = DissolveTransition("builtin_dissolve")
            self.transitions[dissolve_transition.id] = dissolve_transition

            # 创建粒子系统
            particle_system = ParticleSystem(
                id="builtin_particles",
                name="Fire Particles",
                system_type=ParticleSystemType.FIRE,
                max_particles=500,
                emission_rate=50.0,
                lifetime=2.0
            )
            particle_effect = ParticleEffect("builtin_particle_effect", particle_system)
            self.effects[particle_effect.id] = particle_effect
            self.particle_systems[particle_system.id] = particle_system

            self.logger.info(f"创建了 {len(self.effects)} 个内置特效")

        except Exception as e:
            self.logger.error(f"创建内置特效失败: {e}")

    def create_effect(self, effect_type: EffectType, name: str, settings: Optional[Dict[str, Any]] = None) -> Optional[Effect]:
        """创建特效"""
        try:
            effect_id = str(uuid.uuid4())

            # 根据类型创建特效
            if effect_type == EffectType.BLUR:
                effect = BlurEffect(effect_id)
            elif effect_type == EffectType.GLOW:
                effect = GlowEffect(effect_id)
            elif effect_type == EffectType.CHROMA_KEY:
                effect = ChromaKeyEffect(effect_id)
            else:
                self.logger.error(f"不支持的特效类型: {effect_type}")
                return None

            # 应用设置
            if settings:
                for param_name, value in settings.items():
                    effect.set_parameter_value(param_name, value)

            # 编译着色器（如果支持GPU）
            if self.gpu_available:
                effect.compile_shader()

            self.effects[effect_id] = effect

            # 更新性能统计
            self.performance_stats['total_effects'] += 1

            # 发送事件
            self.event_bus.publish("effect_added", {
                'effect_id': effect_id,
                'effect_type': effect_type.value,
                'name': name
            })

            self.logger.info(f"创建特效: {name} ({effect_type.value})")
            return effect

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"创建特效失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="EffectProcessor",
                    operation="create_effect"
                ),
                user_message="无法创建特效"
            )
            self.error_handler.handle_error(error_info)
            return None

    def remove_effect(self, effect_id: str) -> bool:
        """移除特效"""
        try:
            if effect_id not in self.effects:
                return False

            effect = self.effects[effect_id]
            del self.effects[effect_id]

            # 清理缓存
            if effect_id in self.effect_cache:
                del self.effect_cache[effect_id]

            # 更新性能统计
            self.performance_stats['total_effects'] -= 1

            # 发送事件
            self.event_bus.publish("effect_removed", {
                'effect_id': effect_id,
                'effect_type': effect.type.value
            })

            self.logger.info(f"移除特效: {effect.name}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"移除特效失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="EffectProcessor",
                    operation="remove_effect"
                ),
                user_message="无法移除特效"
            )
            self.error_handler.handle_error(error_info)
            return False

    def create_effect_chain(self, name: str, effect_ids: List[str]) -> Optional[EffectChain]:
        """创建特效链"""
        try:
            chain_id = str(uuid.uuid4())
            chain = EffectChain(
                id=chain_id,
                name=name,
                effects=effect_ids.copy()
            )

            self.effect_chains[chain_id] = chain

            # 发送事件
            self.event_bus.publish("effect_chain_created", {
                'chain_id': chain_id,
                'name': name,
                'effect_count': len(effect_ids)
            })

            self.logger.info(f"创建特效链: {name} ({len(effect_ids)} 个特效)")
            return chain

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"创建特效链失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="EffectProcessor",
                    operation="create_effect_chain"
                ),
                user_message="无法创建特效链"
            )
            self.error_handler.handle_error(error_info)
            return None

    def apply_effect_chain(self, chain_id: str, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用特效链"""
        try:
            chain = self.effect_chains.get(chain_id)
            if not chain or not chain.enabled:
                return frame

            result = frame.copy()

            # 按顺序应用特效
            for effect_id in chain.effects:
                effect = self.effects.get(effect_id)
                if effect and effect.settings.enabled:
                    result = effect.process(result, time)

            return result

        except Exception as e:
            self.logger.error(f"应用特效链失败: {e}")
            return frame

    def apply_transition(self, transition_id: str, from_frame: np.ndarray, to_frame: np.ndarray, progress: float) -> np.ndarray:
        """应用转场效果"""
        try:
            transition = self.transitions.get(transition_id)
            if not transition:
                return to_frame

            if isinstance(transition, TransitionEffect):
                return transition.apply_transition(from_frame, to_frame, progress)
            else:
                return to_frame

        except Exception as e:
            self.logger.error(f"应用转场失败: {e}")
            return to_frame

    def process_frame(self, frame: np.ndarray, effect_chain_ids: List[str], time: float = 0.0) -> np.ndarray:
        """处理帧（应用多个特效链）"""
        start_time = time.time()

        try:
            result = frame.copy()

            # 应用所有特效链
            for chain_id in effect_chain_ids:
                result = self.apply_effect_chain(chain_id, result, time)

            # 更新性能统计
            processing_time = time.time() - start_time
            self.performance_stats['render_time'] += processing_time

            return result

        except Exception as e:
            self.logger.error(f"处理帧失败: {e}")
            return frame

    def create_particle_system(self, system_type: ParticleSystemType, name: str, settings: Optional[Dict[str, Any]] = None) -> Optional[ParticleSystem]:
        """创建粒子系统"""
        try:
            system_id = str(uuid.uuid4())

            particle_system = ParticleSystem(
                id=system_id,
                name=name,
                system_type=system_type
            )

            # 应用设置
            if settings:
                for key, value in settings.items():
                    if hasattr(particle_system, key):
                        setattr(particle_system, key, value)

            self.particle_systems[system_id] = particle_system

            # 发送事件
            self.event_bus.publish("particle_system_created", {
                'system_id': system_id,
                'name': name,
                'system_type': system_type.value
            })

            self.logger.info(f"创建粒子系统: {name} ({system_type.value})")
            return particle_system

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"创建粒子系统失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="EffectProcessor",
                    operation="create_particle_system"
                ),
                user_message="无法创建粒子系统"
            )
            self.error_handler.handle_error(error_info)
            return None

    def render_realtime_preview(self, frame: np.ndarray, effect_chain_ids: List[str], time: float = 0.0) -> np.ndarray:
        """实时预览渲染"""
        try:
            # 使用较低的渲染质量进行预览
            if frame.shape[0] > 720 or frame.shape[1] > 1280:
                # 缩小帧尺寸以提高性能
                scale = min(720 / frame.shape[0], 1280 / frame.shape[1])
                preview_frame = cv2.resize(frame, None, fx=scale, fy=scale)
            else:
                preview_frame = frame.copy()

            # 应用特效
            result = self.process_frame(preview_frame, effect_chain_ids, time)

            # 恢复原始尺寸
            if result.shape != frame.shape:
                result = cv2.resize(result, (frame.shape[1], frame.shape[0]))

            return result

        except Exception as e:
            self.logger.error(f"实时预览渲染失败: {e}")
            return frame

    def optimize_performance(self) -> Dict[str, Any]:
        """性能优化"""
        try:
            optimizations = {}

            # 清理缓存
            cache_size_before = len(self.effect_cache)
            self.effect_cache.clear()
            optimizations['cache_cleared'] = cache_size_before

            # 优化GPU使用
            if self.gpu_available:
                # 重新编译所有着色器
                for effect in self.effects.values():
                    if effect.shader:
                        effect.compile_shader()
                optimizations['gpu_shaders_recompiled'] = len(self.effects)

            # 更新性能统计
            optimizations['performance_stats'] = self.performance_stats.copy()

            self.logger.info("性能优化完成")
            return optimizations

        except Exception as e:
            self.logger.error(f"性能优化失败: {e}")
            return {}

    def get_effect_info(self, effect_id: str) -> Optional[Dict[str, Any]]:
        """获取特效信息"""
        effect = self.effects.get(effect_id)
        if not effect:
            return None

        return {
            'id': effect.id,
            'name': effect.name,
            'type': effect.type.value,
            'parameters': {name: {
                'value': param.value,
                'type': param.type,
                'min_value': param.min_value,
                'max_value': param.max_value,
                'keyframable': param.keyframable
            } for name, param in effect.parameters.items()},
            'settings': {
                'enabled': effect.settings.enabled,
                'intensity': effect.settings.intensity,
                'blend_mode': effect.settings.blend_mode.value,
                'gpu_accelerated': effect.settings.gpu_accelerated
            },
            'gpu_available': effect.gpu_available
        }

    def get_effect_statistics(self) -> Dict[str, Any]:
        """获取特效统计信息"""
        effect_types = {}
        for effect in self.effects.values():
            effect_type = effect.type.value
            effect_types[effect_type] = effect_types.get(effect_type, 0) + 1

        return {
            'total_effects': len(self.effects),
            'total_chains': len(self.effect_chains),
            'total_transitions': len(self.transitions),
            'total_particle_systems': len(self.particle_systems),
            'effect_types': effect_types,
            'gpu_available': self.gpu_available,
            'performance_stats': self.performance_stats.copy()
        }

    def _on_effect_added(self, data: Any) -> None:
        """处理特效添加事件"""
        self.logger.debug(f"特效添加: {data}")

    def _on_effect_removed(self, data: Any) -> None:
        """处理特效移除事件"""
        self.logger.debug(f"特效移除: {data}")

    def _on_effect_modified(self, data: Any) -> None:
        """处理特效修改事件"""
        self.logger.debug(f"特效修改: {data}")

    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 清理特效
            self.effects.clear()
            self.effect_chains.clear()
            self.transitions.clear()
            self.particle_systems.clear()

            # 清理缓存
            self.frame_cache.clear()
            self.effect_cache.clear()

            self.logger.info("特效处理器资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局特效处理器实例
_effect_processor: Optional[EffectProcessor] = None


def get_effect_processor() -> EffectProcessor:
    """获取全局特效处理器实例"""
    global _effect_processor
    if _effect_processor is None:
        _effect_processor = EffectProcessor()
    return _effect_processor


def cleanup_effect_processor() -> None:
    """清理全局特效处理器实例"""
    global _effect_processor
    if _effect_processor is not None:
        _effect_processor.cleanup()
        _effect_processor = None