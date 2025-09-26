#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 关键帧系统模块
专业级关键帧动画系统，支持多种插值算法、缓动函数和实时预览
"""

import time
import math
import threading
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import copy
import json
from abc import ABC, abstractmethod

from .logger import get_logger
from .event_system import EventBus
from .service_container import ServiceContainer
from .timeline_engine import TimelineEngine, Clip, Keyframe
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler


class InterpolationType(Enum):
    """插值类型枚举"""
    LINEAR = "linear"
    STEP = "step"
    BEZIER = "bezier"
    SPLINE = "spline"
    CATMULL_ROM = "catmull_rom"
    HERMITE = "hermite"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    BACK = "back"
    POWER = "power"
    EXPONENTIAL = "exponential"
    CIRCULAR = "circular"


class EasingFunction(Enum):
    """缓动函数枚举"""
    LINEAR = "linear"
    QUAD_IN = "quad_in"
    QUAD_OUT = "quad_out"
    QUAD_IN_OUT = "quad_in_out"
    CUBIC_IN = "cubic_in"
    CUBIC_OUT = "cubic_out"
    CUBIC_IN_OUT = "cubic_in_out"
    QUART_IN = "quart_in"
    QUART_OUT = "quart_out"
    QUART_IN_OUT = "quart_in_out"
    QUINT_IN = "quint_in"
    QUINT_OUT = "quint_out"
    QUINT_IN_OUT = "quint_in_out"
    SINE_IN = "sine_in"
    SINE_OUT = "sine_out"
    SINE_IN_OUT = "sine_in_out"
    EXP_IN = "exp_in"
    EXP_OUT = "exp_out"
    EXP_IN_OUT = "exp_in_out"
    CIRC_IN = "circ_in"
    CIRC_OUT = "circ_out"
    CIRC_IN_OUT = "circ_in_out"
    ELASTIC_IN = "elastic_in"
    ELASTIC_OUT = "elastic_out"
    ELASTIC_IN_OUT = "elastic_in_out"
    BACK_IN = "back_in"
    BACK_OUT = "back_out"
    BACK_IN_OUT = "back_in_out"
    BOUNCE_IN = "bounce_in"
    BOUNCE_OUT = "bounce_out"
    BOUNCE_IN_OUT = "bounce_in_out"


class KeyframeOperation(Enum):
    """关键帧操作枚举"""
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"
    MOVE = "move"
    COPY = "copy"
    PASTE = "paste"
    MIRROR = "mirror"
    REVERSE = "reverse"
    SMOOTH = "smooth"
    SIMPLIFY = "simplify"


@dataclass
class BezierControlPoint:
    """贝塞尔控制点"""
    x: float
    y: float


@dataclass
class BezierKeyframe(Keyframe):
    """贝塞尔关键帧"""
    control_point_in: BezierControlPoint = field(default_factory=lambda: BezierControlPoint(0.0, 0.0))
    control_point_out: BezierControlPoint = field(default_factory=lambda: BezierControlPoint(1.0, 1.0))


@dataclass
class KeyframeTrack:
    """关键帧轨道"""
    id: str
    name: str
    property_name: str
    keyframes: List[Keyframe] = field(default_factory=list)
    interpolation_type: InterpolationType = InterpolationType.LINEAR
    easing_function: EasingFunction = EasingFunction.LINEAR
    enabled: bool = True
    loop: bool = False
    ping_pong: bool = False
    min_value: float = 0.0
    max_value: float = 1.0


@dataclass
class KeyframeAnimation:
    """关键帧动画"""
    id: str
    name: str
    clip_id: str
    tracks: Dict[str, KeyframeTrack] = field(default_factory=dict)
    duration: float = 0.0
    start_time: float = 0.0
    enabled: bool = True
    loop_count: int = 1
    playback_speed: float = 1.0


class Interpolator(ABC):
    """插值器抽象基类"""

    @abstractmethod
    def interpolate(self, keyframes: List[Keyframe], time: float) -> Any:
        """插值计算"""
        pass


class LinearInterpolator(Interpolator):
    """线性插值器"""

    def interpolate(self, keyframes: List[Keyframe], time: float) -> Any:
        """线性插值"""
        if not keyframes:
            return None

        # 找到时间点前后的关键帧
        prev_keyframe = None
        next_keyframe = None

        for keyframe in keyframes:
            if keyframe.time <= time:
                prev_keyframe = keyframe
            else:
                next_keyframe = keyframe
                break

        if prev_keyframe is None:
            return keyframes[0].value
        if next_keyframe is None:
            return prev_keyframe.value

        # 线性插值
        t = (time - prev_keyframe.time) / (next_keyframe.time - prev_keyframe.time)
        return prev_keyframe.value + (next_keyframe.value - prev_keyframe.value) * t


class BezierInterpolator(Interpolator):
    """贝塞尔插值器"""

    def interpolate(self, keyframes: List[Keyframe], time: float) -> Any:
        """贝塞尔插值"""
        if not keyframes:
            return None

        # 找到时间点前后的关键帧
        prev_keyframe = None
        next_keyframe = None

        for keyframe in keyframes:
            if keyframe.time <= time:
                prev_keyframe = keyframe
            else:
                next_keyframe = keyframe
                break

        if prev_keyframe is None:
            return keyframes[0].value
        if next_keyframe is None:
            return prev_keyframe.value

        # 贝塞尔插值
        if isinstance(prev_keyframe, BezierKeyframe) and isinstance(next_keyframe, BezierKeyframe):
            t = (time - prev_keyframe.time) / (next_keyframe.time - prev_keyframe.time)
            return self._bezier_interpolate(
                prev_keyframe.value,
                prev_keyframe.control_point_out.y,
                next_keyframe.control_point_in.y,
                next_keyframe.value,
                t
            )
        else:
            # 退化为线性插值
            t = (time - prev_keyframe.time) / (next_keyframe.time - prev_keyframe.time)
            return prev_keyframe.value + (next_keyframe.value - prev_keyframe.value) * t

    def _bezier_interpolate(self, p0: float, p1: float, p2: float, p3: float, t: float) -> float:
        """三次贝塞尔插值"""
        mt = 1 - t
        return (mt * mt * mt * p0 +
                3 * mt * mt * t * p1 +
                3 * mt * t * t * p2 +
                t * t * t * p3)


class SplineInterpolator(Interpolator):
    """样条插值器"""

    def interpolate(self, keyframes: List[Keyframe], time: float) -> Any:
        """样条插值"""
        if not keyframes:
            return None

        if len(keyframes) < 2:
            return keyframes[0].value

        # 找到时间点前后的关键帧
        prev_keyframe = None
        next_keyframe = None
        prev_prev_keyframe = None
        next_next_keyframe = None

        for i, keyframe in enumerate(keyframes):
            if keyframe.time <= time:
                prev_keyframe = keyframe
                prev_prev_keyframe = keyframes[i - 1] if i > 0 else None
            else:
                next_keyframe = keyframe
                next_next_keyframe = keyframes[i + 1] if i < len(keyframes) - 1 else None
                break

        if prev_keyframe is None:
            return keyframes[0].value
        if next_keyframe is None:
            return prev_keyframe.value

        # Catmull-Rom样条插值
        t = (time - prev_keyframe.time) / (next_keyframe.time - prev_keyframe.time)
        return self._catmull_rom_interpolate(
            prev_prev_keyframe.value if prev_prev_keyframe else prev_keyframe.value,
            prev_keyframe.value,
            next_keyframe.value,
            next_next_keyframe.value if next_next_keyframe else next_keyframe.value,
            t
        )

    def _catmull_rom_interpolate(self, p0: float, p1: float, p2: float, p3: float, t: float) -> float:
        """Catmull-Rom样条插值"""
        t2 = t * t
        t3 = t2 * t

        return 0.5 * (
            (2 * p1) +
            (-p0 + p2) * t +
            (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
            (-p0 + 3 * p1 - 3 * p2 + p3) * t3
        )


class EasingFunctions:
    """缓动函数集合"""

    @staticmethod
    def linear(t: float) -> float:
        """线性缓动"""
        return t

    @staticmethod
    def quad_in(t: float) -> float:
        """二次缓入"""
        return t * t

    @staticmethod
    def quad_out(t: float) -> float:
        """二次缓出"""
        return t * (2 - t)

    @staticmethod
    def quad_in_out(t: float) -> float:
        """二次缓入缓出"""
        return t * t * (3 - 2 * t)

    @staticmethod
    def cubic_in(t: float) -> float:
        """三次缓入"""
        return t * t * t

    @staticmethod
    def cubic_out(t: float) -> float:
        """三次缓出"""
        t = t - 1
        return t * t * t + 1

    @staticmethod
    def cubic_in_out(t: float) -> float:
        """三次缓入缓出"""
        t = t * 2
        if t < 1:
            return 0.5 * t * t * t
        t = t - 2
        return 0.5 * (t * t * t + 2)

    @staticmethod
    def sine_in(t: float) -> float:
        """正弦缓入"""
        return 1 - math.cos(t * math.pi / 2)

    @staticmethod
    def sine_out(t: float) -> float:
        """正弦缓出"""
        return math.sin(t * math.pi / 2)

    @staticmethod
    def sine_in_out(t: float) -> float:
        """正弦缓入缓出"""
        return -0.5 * (math.cos(math.pi * t) - 1)

    @staticmethod
    def exp_in(t: float) -> float:
        """指数缓入"""
        return math.pow(2, 10 * (t - 1))

    @staticmethod
    def exp_out(t: float) -> float:
        """指数缓出"""
        return -math.pow(2, -10 * t) + 1

    @staticmethod
    def exp_in_out(t: float) -> float:
        """指数缓入缓出"""
        t = t * 2
        if t < 1:
            return 0.5 * math.pow(2, 10 * (t - 1))
        return 0.5 * (-math.pow(2, -10 * (t - 1)) + 2)

    @staticmethod
    def circ_in(t: float) -> float:
        """圆形缓入"""
        return 1 - math.sqrt(1 - t * t)

    @staticmethod
    def circ_out(t: float) -> float:
        """圆形缓出"""
        t = t - 1
        return math.sqrt(1 - t * t)

    @staticmethod
    def circ_in_out(t: float) -> float:
        """圆形缓入缓出"""
        t = t * 2
        if t < 1:
            return -0.5 * (math.sqrt(1 - t * t) - 1)
        t = t - 2
        return 0.5 * (math.sqrt(1 - t * t) + 1)

    @staticmethod
    def elastic_in(t: float) -> float:
        """弹性缓入"""
        return -math.pow(2, 10 * (t - 1)) * math.sin((t - 1.075) * 2 * math.pi / 0.3)

    @staticmethod
    def elastic_out(t: float) -> float:
        """弹性缓出"""
        return math.pow(2, -10 * t) * math.sin((t - 0.075) * 2 * math.pi / 0.3) + 1

    @staticmethod
    def elastic_in_out(t: float) -> float:
        """弹性缓入缓出"""
        t = t * 2
        if t < 1:
            return -0.5 * math.pow(2, 10 * (t - 1)) * math.sin((t - 1.075) * 2 * math.pi / 0.3)
        return 0.5 * math.pow(2, -10 * (t - 1)) * math.sin((t - 1.075) * 2 * math.pi / 0.3) + 1

    @staticmethod
    def back_in(t: float) -> float:
        """回弹缓入"""
        s = 1.70158
        return t * t * ((s + 1) * t - s)

    @staticmethod
    def back_out(t: float) -> float:
        """回弹缓出"""
        s = 1.70158
        t = t - 1
        return t * t * ((s + 1) * t + s) + 1

    @staticmethod
    def back_in_out(t: float) -> float:
        """回弹缓入缓出"""
        s = 1.70158 * 1.525
        t = t * 2
        if t < 1:
            return 0.5 * (t * t * ((s + 1) * t - s))
        t = t - 2
        return 0.5 * (t * t * ((s + 1) * t + s) + 2)

    @staticmethod
    def bounce_in(t: float) -> float:
        """弹跳缓入"""
        return 1 - EasingFunctions.bounce_out(1 - t)

    @staticmethod
    def bounce_out(t: float) -> float:
        """弹跳缓出"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t = t - 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t = t - 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t = t - 2.625 / 2.75
            return 7.5625 * t * t + 0.984375

    @staticmethod
    def bounce_in_out(t: float) -> float:
        """弹跳缓入缓出"""
        if t < 0.5:
            return EasingFunctions.bounce_in(t * 2) * 0.5
        return EasingFunctions.bounce_out(t * 2 - 1) * 0.5 + 0.5


class KeyframeSystem:
    """关键帧系统核心类"""

    def __init__(self, timeline_engine: Optional[TimelineEngine] = None, logger=None):
        """初始化关键帧系统"""
        self.logger = logger or get_logger("KeyframeSystem")
        self.error_handler = get_global_error_handler()
        self.event_bus = EventBus()
        self.service_container = ServiceContainer()
        self.timeline_engine = timeline_engine or get_timeline_engine()

        # 插值器
        self.interpolators: Dict[InterpolationType, Interpolator] = {
            InterpolationType.LINEAR: LinearInterpolator(),
            InterpolationType.BEZIER: BezierInterpolator(),
            InterpolationType.SPLINE: SplineInterpolator(),
            InterpolationType.CATMULL_ROM: SplineInterpolator(),
            InterpolationType.HERMITE: SplineInterpolator()
        }

        # 动画管理
        self.animations: Dict[str, KeyframeAnimation] = {}
        self.active_animations: Dict[str, threading.Thread] = {}
        self.animation_stop_events: Dict[str, threading.Event] = {}

        # 预览系统
        self.preview_enabled = True
        self.preview_thread: Optional[threading.Thread] = None
        self.preview_stop_event = threading.Event()

        # 缓存
        self.keyframe_cache: Dict[str, Dict[str, List[Keyframe]]] = {}
        self.interpolation_cache: Dict[str, Dict[float, Any]] = {}

        # 性能监控
        self.performance_stats = {
            'total_keyframes': 0,
            'total_animations': 0,
            'interpolation_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'processing_time': 0.0
        }

        # 初始化
        self._initialize()

    def _initialize(self) -> None:
        """初始化关键帧系统"""
        try:
            # 注册服务
            self._register_services()

            # 设置事件处理器
            self._setup_event_handlers()

            # 启动预览线程
            self._start_preview_thread()

            self.logger.info("关键帧系统初始化完成")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"关键帧系统初始化失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="KeyframeSystem",
                    operation="initialize"
                ),
                user_message="关键帧系统初始化失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _register_services(self) -> None:
        """注册服务"""
        try:
            self.service_container.register(KeyframeSystem, self)
            self.service_container.register(EventBus, self.event_bus)
            self.logger.info("服务注册完成")
        except Exception as e:
            self.logger.error(f"服务注册失败: {str(e)}")

    def _setup_event_handlers(self) -> None:
        """设置事件处理器"""
        try:
            self.event_bus.subscribe("keyframe_added", self._on_keyframe_added)
            self.event_bus.subscribe("keyframe_removed", self._on_keyframe_removed)
            self.event_bus.subscribe("keyframe_modified", self._on_keyframe_modified)
            self.event_bus.subscribe("animation_started", self._on_animation_started)
            self.event_bus.subscribe("animation_stopped", self._on_animation_stopped)
            self.logger.info("事件处理器设置完成")
        except Exception as e:
            self.logger.error(f"事件处理器设置失败: {str(e)}")

    def _start_preview_thread(self) -> None:
        """启动预览线程"""
        self.preview_thread = threading.Thread(target=self._preview_worker, daemon=True)
        self.preview_thread.start()

    def _preview_worker(self) -> None:
        """预览工作线程"""
        while not self.preview_stop_event.is_set():
            try:
                if self.preview_enabled and self.active_animations:
                    # 更新所有活动动画
                    current_time = time.time()
                    for animation_id, animation in self.animations.items():
                        if animation.enabled and animation_id in self.active_animations:
                            self._update_animation(animation_id, current_time)

                time.sleep(0.016)  # 约60FPS

            except Exception as e:
                self.logger.error(f"预览线程异常: {e}")
                time.sleep(0.1)

    def create_keyframe_track(self, clip_id: str, property_name: str,
                             interpolation_type: InterpolationType = InterpolationType.LINEAR,
                             easing_function: EasingFunction = EasingFunction.LINEAR) -> Optional[KeyframeTrack]:
        """创建关键帧轨道"""
        try:
            # 检查是否已存在轨道
            animation = self.animations.get(clip_id)
            if not animation:
                # 创建新动画
                animation = KeyframeAnimation(
                    id=str(uuid.uuid4()),
                    name=f"Animation_{clip_id}",
                    clip_id=clip_id
                )
                self.animations[clip_id] = animation

            if property_name in animation.tracks:
                return animation.tracks[property_name]

            # 创建轨道
            track = KeyframeTrack(
                id=str(uuid.uuid4()),
                name=f"{property_name}_track",
                property_name=property_name,
                interpolation_type=interpolation_type,
                easing_function=easing_function
            )

            animation.tracks[property_name] = track

            # 更新缓存
            if clip_id not in self.keyframe_cache:
                self.keyframe_cache[clip_id] = {}
            self.keyframe_cache[clip_id][property_name] = []

            # 发送事件
            self.event_bus.publish("track_created", {
                'clip_id': clip_id,
                'track_id': track.id,
                'property_name': property_name
            })

            self.logger.info(f"创建关键帧轨道: {property_name} for {clip_id}")
            return track

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"创建关键帧轨道失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="KeyframeSystem",
                    operation="create_keyframe_track"
                ),
                user_message="无法创建关键帧轨道"
            )
            self.error_handler.handle_error(error_info)
            return None

    def add_keyframe(self, clip_id: str, property_name: str, time: float, value: Any,
                    interpolation_type: Optional[InterpolationType] = None,
                    easing_function: Optional[EasingFunction] = None) -> Optional[Keyframe]:
        """添加关键帧"""
        try:
            # 获取或创建轨道
            track = self._get_or_create_track(clip_id, property_name, interpolation_type, easing_function)
            if not track:
                return None

            # 创建关键帧
            keyframe = Keyframe(
                id=str(uuid.uuid4()),
                time=time,
                property_name=property_name,
                value=value,
                interpolation=track.interpolation_type.value,
                easing=track.easing_function.value
            )

            # 添加关键帧
            track.keyframes.append(keyframe)
            track.keyframes.sort(key=lambda k: k.time)

            # 更新缓存
            if clip_id in self.keyframe_cache and property_name in self.keyframe_cache[clip_id]:
                self.keyframe_cache[clip_id][property_name].append(keyframe)
                self.keyframe_cache[clip_id][property_name].sort(key=lambda k: k.time)

            # 清除插值缓存
            self._clear_interpolation_cache(clip_id, property_name)

            # 更新性能统计
            self.performance_stats['total_keyframes'] += 1

            # 发送事件
            self.event_bus.publish("keyframe_added", {
                'clip_id': clip_id,
                'keyframe_id': keyframe.id,
                'property_name': property_name,
                'time': time,
                'value': value
            })

            self.logger.info(f"添加关键帧: {property_name} @ {time:.2f} = {value}")
            return keyframe

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"添加关键帧失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="KeyframeSystem",
                    operation="add_keyframe"
                ),
                user_message="无法添加关键帧"
            )
            self.error_handler.handle_error(error_info)
            return None

    def _get_or_create_track(self, clip_id: str, property_name: str,
                           interpolation_type: Optional[InterpolationType] = None,
                           easing_function: Optional[EasingFunction] = None) -> Optional[KeyframeTrack]:
        """获取或创建轨道"""
        animation = self.animations.get(clip_id)
        if not animation:
            # 创建新动画
            animation = KeyframeAnimation(
                id=str(uuid.uuid4()),
                name=f"Animation_{clip_id}",
                clip_id=clip_id
            )
            self.animations[clip_id] = animation

        if property_name in animation.tracks:
            return animation.tracks[property_name]

        # 创建轨道
        track = KeyframeTrack(
            id=str(uuid.uuid4()),
            name=f"{property_name}_track",
            property_name=property_name,
            interpolation_type=interpolation_type or InterpolationType.LINEAR,
            easing_function=easing_function or EasingFunction.LINEAR
        )

        animation.tracks[property_name] = track

        # 更新缓存
        if clip_id not in self.keyframe_cache:
            self.keyframe_cache[clip_id] = {}
        self.keyframe_cache[clip_id][property_name] = []

        return track

    def remove_keyframe(self, clip_id: str, property_name: str, keyframe_id: str) -> bool:
        """移除关键帧"""
        try:
            animation = self.animations.get(clip_id)
            if not animation:
                return False

            track = animation.tracks.get(property_name)
            if not track:
                return False

            # 查找并移除关键帧
            for i, keyframe in enumerate(track.keyframes):
                if keyframe.id == keyframe_id:
                    track.keyframes.pop(i)

                    # 更新缓存
                    if clip_id in self.keyframe_cache and property_name in self.keyframe_cache[clip_id]:
                        for i, kf in enumerate(self.keyframe_cache[clip_id][property_name]):
                            if kf.id == keyframe_id:
                                self.keyframe_cache[clip_id][property_name].pop(i)
                                break

                    # 清除插值缓存
                    self._clear_interpolation_cache(clip_id, property_name)

                    # 发送事件
                    self.event_bus.publish("keyframe_removed", {
                        'clip_id': clip_id,
                        'keyframe_id': keyframe_id,
                        'property_name': property_name
                    })

                    self.logger.info(f"移除关键帧: {keyframe_id}")
                    return True

            return False

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"移除关键帧失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="KeyframeSystem",
                    operation="remove_keyframe"
                ),
                user_message="无法移除关键帧"
            )
            self.error_handler.handle_error(error_info)
            return False

    def get_keyframe_value(self, clip_id: str, property_name: str, time: float) -> Optional[Any]:
        """获取关键帧值"""
        try:
            # 检查缓存
            cache_key = f"{clip_id}_{property_name}"
            if cache_key in self.interpolation_cache and time in self.interpolation_cache[cache_key]:
                self.performance_stats['cache_hits'] += 1
                return self.interpolation_cache[cache_key][time]

            self.performance_stats['cache_misses'] += 1

            # 获取动画和轨道
            animation = self.animations.get(clip_id)
            if not animation:
                return None

            track = animation.tracks.get(property_name)
            if not track or not track.enabled or not track.keyframes:
                return None

            # 获取插值器
            interpolator = self.interpolators.get(track.interpolation_type)
            if not interpolator:
                return None

            # 执行插值
            start_time = time.time()
            value = interpolator.interpolate(track.keyframes, time)

            # 应用缓动函数
            if track.easing_function != EasingFunction.LINEAR and len(track.keyframes) >= 2:
                # 计算相对时间
                first_keyframe = track.keyframes[0]
                last_keyframe = track.keyframes[-1]
                if time >= first_keyframe.time and time <= last_keyframe.time:
                    t = (time - first_keyframe.time) / (last_keyframe.time - first_keyframe.time)
                    easing_factor = self._apply_easing_function(track.easing_function, t)

                    # 应用缓动到值
                    if isinstance(value, (int, float)):
                        min_val = min(kf.value for kf in track.keyframes)
                        max_val = max(kf.value for kf in track.keyframes)
                        value = min_val + (max_val - min_val) * easing_factor

            # 更新缓存
            self.performance_stats['processing_time'] += time.time() - start_time
            self.performance_stats['interpolation_calls'] += 1

            if cache_key not in self.interpolation_cache:
                self.interpolation_cache[cache_key] = {}
            self.interpolation_cache[cache_key][time] = value

            return value

        except Exception as e:
            self.logger.error(f"获取关键帧值失败: {e}")
            return None

    def _apply_easing_function(self, easing_function: EasingFunction, t: float) -> float:
        """应用缓动函数"""
        easing_methods = {
            EasingFunction.LINEAR: EasingFunctions.linear,
            EasingFunction.QUAD_IN: EasingFunctions.quad_in,
            EasingFunction.QUAD_OUT: EasingFunctions.quad_out,
            EasingFunction.QUAD_IN_OUT: EasingFunctions.quad_in_out,
            EasingFunction.CUBIC_IN: EasingFunctions.cubic_in,
            EasingFunction.CUBIC_OUT: EasingFunctions.cubic_out,
            EasingFunction.CUBIC_IN_OUT: EasingFunctions.cubic_in_out,
            EasingFunction.SINE_IN: EasingFunctions.sine_in,
            EasingFunction.SINE_OUT: EasingFunctions.sine_out,
            EasingFunction.SINE_IN_OUT: EasingFunctions.sine_in_out,
            EasingFunction.EXP_IN: EasingFunctions.exp_in,
            EasingFunction.EXP_OUT: EasingFunctions.exp_out,
            EasingFunction.EXP_IN_OUT: EasingFunctions.exp_in_out,
            EasingFunction.CIRC_IN: EasingFunctions.circ_in,
            EasingFunction.CIRC_OUT: EasingFunctions.circ_out,
            EasingFunction.CIRC_IN_OUT: EasingFunctions.circ_in_out,
            EasingFunction.ELASTIC_IN: EasingFunctions.elastic_in,
            EasingFunction.ELASTIC_OUT: EasingFunctions.elastic_out,
            EasingFunction.ELASTIC_IN_OUT: EasingFunctions.elastic_in_out,
            EasingFunction.BACK_IN: EasingFunctions.back_in,
            EasingFunction.BACK_OUT: EasingFunctions.back_out,
            EasingFunction.BACK_IN_OUT: EasingFunctions.back_in_out,
            EasingFunction.BOUNCE_IN: EasingFunctions.bounce_in,
            EasingFunction.BOUNCE_OUT: EasingFunctions.bounce_out,
            EasingFunction.BOUNCE_IN_OUT: EasingFunctions.bounce_in_out
        }

        method = easing_methods.get(easing_function, EasingFunctions.linear)
        return method(t)

    def _clear_interpolation_cache(self, clip_id: str, property_name: str) -> None:
        """清除插值缓存"""
        cache_key = f"{clip_id}_{property_name}"
        if cache_key in self.interpolation_cache:
            del self.interpolation_cache[cache_key]

    def modify_keyframe(self, clip_id: str, property_name: str, keyframe_id: str,
                      new_time: Optional[float] = None, new_value: Optional[Any] = None) -> bool:
        """修改关键帧"""
        try:
            animation = self.animations.get(clip_id)
            if not animation:
                return False

            track = animation.tracks.get(property_name)
            if not track:
                return False

            # 查找关键帧
            for keyframe in track.keyframes:
                if keyframe.id == keyframe_id:
                    # 修改关键帧
                    if new_time is not None:
                        keyframe.time = new_time
                    if new_value is not None:
                        keyframe.value = new_value

                    # 重新排序
                    track.keyframes.sort(key=lambda k: k.time)

                    # 更新缓存
                    if clip_id in self.keyframe_cache and property_name in self.keyframe_cache[clip_id]:
                        for kf in self.keyframe_cache[clip_id][property_name]:
                            if kf.id == keyframe_id:
                                if new_time is not None:
                                    kf.time = new_time
                                if new_value is not None:
                                    kf.value = new_value
                                break
                        self.keyframe_cache[clip_id][property_name].sort(key=lambda k: k.time)

                    # 清除插值缓存
                    self._clear_interpolation_cache(clip_id, property_name)

                    # 发送事件
                    self.event_bus.publish("keyframe_modified", {
                        'clip_id': clip_id,
                        'keyframe_id': keyframe_id,
                        'property_name': property_name,
                        'new_time': new_time,
                        'new_value': new_value
                    })

                    self.logger.info(f"修改关键帧: {keyframe_id}")
                    return True

            return False

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"修改关键帧失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="KeyframeSystem",
                    operation="modify_keyframe"
                ),
                user_message="无法修改关键帧"
            )
            self.error_handler.handle_error(error_info)
            return False

    def set_interpolation_type(self, clip_id: str, property_name: str, interpolation_type: InterpolationType) -> bool:
        """设置插值类型"""
        try:
            animation = self.animations.get(clip_id)
            if not animation:
                return False

            track = animation.tracks.get(property_name)
            if not track:
                return False

            old_type = track.interpolation_type
            track.interpolation_type = interpolation_type

            # 清除插值缓存
            self._clear_interpolation_cache(clip_id, property_name)

            # 发送事件
            self.event_bus.publish("interpolation_changed", {
                'clip_id': clip_id,
                'property_name': property_name,
                'old_type': old_type.value,
                'new_type': interpolation_type.value
            })

            self.logger.info(f"设置插值类型: {property_name} -> {interpolation_type.value}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"设置插值类型失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="KeyframeSystem",
                    operation="set_interpolation_type"
                ),
                user_message="无法设置插值类型"
            )
            self.error_handler.handle_error(error_info)
            return False

    def set_easing_function(self, clip_id: str, property_name: str, easing_function: EasingFunction) -> bool:
        """设置缓动函数"""
        try:
            animation = self.animations.get(clip_id)
            if not animation:
                return False

            track = animation.tracks.get(property_name)
            if not track:
                return False

            old_function = track.easing_function
            track.easing_function = easing_function

            # 清除插值缓存
            self._clear_interpolation_cache(clip_id, property_name)

            # 发送事件
            self.event_bus.publish("easing_changed", {
                'clip_id': clip_id,
                'property_name': property_name,
                'old_function': old_function.value,
                'new_function': easing_function.value
            })

            self.logger.info(f"设置缓动函数: {property_name} -> {easing_function.value}")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"设置缓动函数失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="KeyframeSystem",
                    operation="set_easing_function"
                ),
                user_message="无法设置缓动函数"
            )
            self.error_handler.handle_error(error_info)
            return False

    def smooth_keyframes(self, clip_id: str, property_name: str, smooth_factor: float = 0.5) -> bool:
        """平滑关键帧"""
        try:
            animation = self.animations.get(clip_id)
            if not animation:
                return False

            track = animation.tracks.get(property_name)
            if not track or len(track.keyframes) < 3:
                return False

            # 应用平滑算法
            smoothed_values = []
            for i, keyframe in enumerate(track.keyframes):
                if i == 0 or i == len(track.keyframes) - 1:
                    smoothed_values.append(keyframe.value)
                else:
                    prev_value = track.keyframes[i - 1].value
                    curr_value = keyframe.value
                    next_value = track.keyframes[i + 1].value

                    # 三点平滑
                    smoothed_value = (prev_value + curr_value + next_value) / 3
                    smoothed_value = curr_value * (1 - smooth_factor) + smoothed_value * smooth_factor
                    smoothed_values.append(smoothed_value)

            # 更新关键帧值
            for i, keyframe in enumerate(track.keyframes):
                keyframe.value = smoothed_values[i]

            # 清除插值缓存
            self._clear_interpolation_cache(clip_id, property_name)

            # 发送事件
            self.event_bus.publish("keyframes_smoothed", {
                'clip_id': clip_id,
                'property_name': property_name,
                'smooth_factor': smooth_factor
            })

            self.logger.info(f"平滑关键帧: {property_name} (factor: {smooth_factor})")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                message=f"平滑关键帧失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="KeyframeSystem",
                    operation="smooth_keyframes"
                ),
                user_message="无法平滑关键帧"
            )
            self.error_handler.handle_error(error_info)
            return False

    def copy_keyframes(self, clip_id: str, property_name: str, start_time: float, end_time: float) -> Optional[List[Keyframe]]:
        """复制关键帧"""
        try:
            animation = self.animations.get(clip_id)
            if not animation:
                return None

            track = animation.tracks.get(property_name)
            if not track:
                return None

            # 复制时间范围内的关键帧
            copied_keyframes = []
            for keyframe in track.keyframes:
                if start_time <= keyframe.time <= end_time:
                    copied_keyframes.append(copy.deepcopy(keyframe))

            self.logger.info(f"复制关键帧: {len(copied_keyframes)} 个关键帧")
            return copied_keyframes

        except Exception as e:
            self.logger.error(f"复制关键帧失败: {e}")
            return None

    def paste_keyframes(self, clip_id: str, property_name: str, keyframes: List[Keyframe], offset_time: float = 0.0) -> bool:
        """粘贴关键帧"""
        try:
            # 获取或创建轨道
            track = self._get_or_create_track(clip_id, property_name)
            if not track:
                return False

            # 粘贴关键帧
            for keyframe in keyframes:
                new_keyframe = copy.deepcopy(keyframe)
                new_keyframe.id = str(uuid.uuid4())
                new_keyframe.time += offset_time
                track.keyframes.append(new_keyframe)

            # 重新排序
            track.keyframes.sort(key=lambda k: k.time)

            # 更新缓存
            if clip_id not in self.keyframe_cache:
                self.keyframe_cache[clip_id] = {}
            if property_name not in self.keyframe_cache[clip_id]:
                self.keyframe_cache[clip_id][property_name] = []

            for keyframe in keyframes:
                new_keyframe = copy.deepcopy(keyframe)
                new_keyframe.id = str(uuid.uuid4())
                new_keyframe.time += offset_time
                self.keyframe_cache[clip_id][property_name].append(new_keyframe)

            self.keyframe_cache[clip_id][property_name].sort(key=lambda k: k.time)

            # 清除插值缓存
            self._clear_interpolation_cache(clip_id, property_name)

            # 发送事件
            self.event_bus.publish("keyframes_pasted", {
                'clip_id': clip_id,
                'property_name': property_name,
                'keyframe_count': len(keyframes),
                'offset_time': offset_time
            })

            self.logger.info(f"粘贴关键帧: {len(keyframes)} 个关键帧")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"粘贴关键帧失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="KeyframeSystem",
                    operation="paste_keyframes"
                ),
                user_message="无法粘贴关键帧"
            )
            self.error_handler.handle_error(error_info)
            return False

    def get_keyframe_statistics(self) -> Dict[str, Any]:
        """获取关键帧统计信息"""
        total_keyframes = sum(len(track.keyframes) for animation in self.animations.values() for track in animation.tracks.values())
        total_tracks = sum(len(animation.tracks) for animation in self.animations.values())
        total_animations = len(self.animations)

        # 按插值类型统计
        interpolation_stats = {}
        for animation in self.animations.values():
            for track in animation.tracks.values():
                interp_type = track.interpolation_type.value
                interpolation_stats[interp_type] = interpolation_stats.get(interp_type, 0) + 1

        # 按缓动函数统计
        easing_stats = {}
        for animation in self.animations.values():
            for track in animation.tracks.values():
                easing_func = track.easing_function.value
                easing_stats[easing_func] = easing_stats.get(easing_func, 0) + 1

        return {
            'total_keyframes': total_keyframes,
            'total_tracks': total_tracks,
            'total_animations': total_animations,
            'active_animations': len(self.active_animations),
            'interpolation_types': interpolation_stats,
            'easing_functions': easing_stats,
            'performance': self.performance_stats.copy()
        }

    def _update_animation(self, animation_id: str, current_time: float) -> None:
        """更新动画"""
        try:
            animation = self.animations.get(animation_id)
            if not animation or not animation.enabled:
                return

            # 更新所有轨道
            for track in animation.tracks.values():
                if track.enabled:
                    # 计算动画时间
                    animation_time = (current_time - animation.start_time) * animation.playback_speed

                    # 检查是否在动画范围内
                    if 0 <= animation_time <= animation.duration:
                        value = self.get_keyframe_value(animation.clip_id, track.property_name, animation_time)
                        if value is not None:
                            # 更新剪辑属性
                            self._update_clip_property(animation.clip_id, track.property_name, value)

        except Exception as e:
            self.logger.error(f"更新动画失败: {e}")

    def _update_clip_property(self, clip_id: str, property_name: str, value: Any) -> None:
        """更新剪辑属性"""
        try:
            # 通过时间线引擎更新剪辑属性
            clip = self.timeline_engine.get_clip(clip_id)
            if clip:
                if property_name == "opacity":
                    clip.opacity = value
                elif property_name == "volume":
                    clip.volume = value
                elif property_name == "position":
                    clip.position = value
                elif property_name == "scale":
                    clip.scale = value
                elif property_name == "rotation":
                    clip.rotation = value

                # 发送属性更新事件
                self.event_bus.publish("clip_property_updated", {
                    'clip_id': clip_id,
                    'property_name': property_name,
                    'value': value
                })

        except Exception as e:
            self.logger.error(f"更新剪辑属性失败: {e}")

    def _on_keyframe_added(self, data: Any) -> None:
        """处理关键帧添加事件"""
        self.logger.debug(f"关键帧添加: {data}")

    def _on_keyframe_removed(self, data: Any) -> None:
        """处理关键帧移除事件"""
        self.logger.debug(f"关键帧移除: {data}")

    def _on_keyframe_modified(self, data: Any) -> None:
        """处理关键帧修改事件"""
        self.logger.debug(f"关键帧修改: {data}")

    def _on_animation_started(self, data: Any) -> None:
        """处理动画开始事件"""
        self.logger.debug(f"动画开始: {data}")

    def _on_animation_stopped(self, data: Any) -> None:
        """处理动画停止事件"""
        self.logger.debug(f"动画停止: {data}")

    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 停止预览线程
            self.preview_stop_event.set()
            if self.preview_thread:
                self.preview_thread.join(timeout=5.0)

            # 停止所有活动动画
            for animation_id in list(self.active_animations.keys()):
                stop_event = self.animation_stop_events.get(animation_id)
                if stop_event:
                    stop_event.set()

                animation_thread = self.active_animations.get(animation_id)
                if animation_thread:
                    animation_thread.join(timeout=1.0)

            # 清理缓存
            self.keyframe_cache.clear()
            self.interpolation_cache.clear()

            self.logger.info("关键帧系统资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")

    def __del__(self):
        """析构函数"""
        self.cleanup()


# 全局关键帧系统实例
_keyframe_system: Optional[KeyframeSystem] = None


def get_keyframe_system(timeline_engine: Optional[TimelineEngine] = None) -> KeyframeSystem:
    """获取全局关键帧系统实例"""
    global _keyframe_system
    if _keyframe_system is None:
        _keyframe_system = KeyframeSystem(timeline_engine)
    return _keyframe_system


def cleanup_keyframe_system() -> None:
    """清理全局关键帧系统实例"""
    global _keyframe_system
    if _keyframe_system is not None:
        _keyframe_system.cleanup()
        _keyframe_system = None