"""
专业效果处理系统 - 视频效果、音频效果和转场效果的统一管理
提供GPU加速、实时预览和专业级效果处理能力
"""

import os
import json
import time
import threading
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QImage, QPixmap

from app.core.logger import Logger
from app.core.video_engine import VideoEngine, EngineSettings
from app.core.hardware_acceleration import HardwareAcceleration
from app.utils.error_handler import handle_exception, safe_execute
from app.utils.ffmpeg_utils import FFmpegUtils


class EffectType(Enum):
    """效果类型"""
    VIDEO = "video"
    AUDIO = "audio"
    TRANSITION = "transition"
    COLOR = "color"
    STABILIZATION = "stabilization"
    TRACKING = "tracking"


class EffectCategory(Enum):
    """效果类别"""
    BASIC = "basic"          # 基础效果
    COLOR = "color"          # 颜色效果
    BLUR = "blur"            # 模糊效果
    SHARPEN = "sharpen"      # 锐化效果
    TRANSFORM = "transform"  # 变换效果
    AUDIO = "audio"          # 音频效果
    TRANSITION = "transition" # 转场效果
    STABILIZATION = "stabilization"  # 稳定效果
    TRACKING = "tracking"    # 跟踪效果
    AI = "ai"               # AI效果


@dataclass
class EffectParameter:
    """效果参数"""
    name: str
    type: str  # float, int, bool, string, color
    default_value: Any
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    step: Optional[float] = None
    description: str = ""
    unit: str = ""


@dataclass
class EffectPreset:
    """效果预设"""
    name: str
    parameters: Dict[str, Any]
    description: str = ""
    thumbnail: Optional[str] = None


@dataclass
class EffectInfo:
    """效果信息"""
    id: str
    name: str
    type: EffectType
    category: EffectCategory
    description: str
    parameters: List[EffectParameter]
    presets: List[EffectPreset]
    gpu_accelerated: bool = False
    real_time: bool = True
    requires_gpu: bool = False
    processing_time: float = 0.0  # 预估处理时间（秒/帧）


class EffectInstance:
    """效果实例"""

    def __init__(self, effect_info: EffectInfo, parameters: Dict[str, Any] = None):
        self.effect_info = effect_info
        self.parameters = parameters or {}
        self.enabled = True
        self.intensity = 1.0  # 效果强度
        self.start_time = 0.0
        self.end_time = 0.0
        self.keyframes = {}  # 关键帧动画

        # 设置默认参数
        for param in effect_info.parameters:
            if param.name not in self.parameters:
                self.parameters[param.name] = param.default_value

    def set_parameter(self, name: str, value: Any):
        """设置参数值"""
        if name in self.parameters:
            self.parameters[name] = value
        else:
            raise ValueError(f"Unknown parameter: {name}")

    def get_parameter(self, name: str) -> Any:
        """获取参数值"""
        return self.parameters.get(name)

    def add_keyframe(self, time: float, parameters: Dict[str, Any]):
        """添加关键帧"""
        self.keyframes[time] = parameters.copy()

    def get_parameters_at_time(self, time: float) -> Dict[str, Any]:
        """获取指定时间的参数值"""
        if not self.keyframes:
            return self.parameters.copy()

        # 简单的线性插值
        times = sorted(self.keyframes.keys())
        if time <= times[0]:
            return self.keyframes[times[0]]
        if time >= times[-1]:
            return self.keyframes[times[-1]]

        # 找到前后两个关键帧
        for i in range(len(times) - 1):
            if times[i] <= time <= times[i + 1]:
                t1, t2 = times[i], times[i + 1]
                alpha = (time - t1) / (t2 - t1)

                result = {}
                for key in self.keyframes[t1]:
                    v1 = self.keyframes[t1][key]
                    v2 = self.keyframes[t2][key]
                    if isinstance(v1, (int, float)):
                        result[key] = v1 + alpha * (v2 - v1)
                    else:
                        result[key] = v2  # 非数值类型直接使用
                return result

        return self.parameters.copy()


class EffectsEngine(QObject):
    """效果处理引擎"""

    effect_processed = pyqtSignal(str, bool)  # effect_id, success
    preview_updated = pyqtSignal(str, QImage)  # effect_id, preview_image
    progress_updated = pyqtSignal(str, float)  # effect_id, progress

    def __init__(self, video_engine: VideoEngine = None):
        super().__init__()
        self.logger = Logger.get_logger("EffectsEngine")
        self.video_engine = video_engine or VideoEngine()
        self.hardware_acceleration = HardwareAcceleration()
        self.ffmpeg_utils = FFmpegUtils()

        # 效果数据库
        self.effects_db = {}
        self.active_effects = {}

        # 处理线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # 加载内置效果
        self._load_builtin_effects()

        # 创建效果缓存目录
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".cineaistudio", "effects_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def _load_builtin_effects(self):
        """加载内置效果"""
        # 视频效果
        self._add_video_effects()

        # 音频效果
        self._add_audio_effects()

        # 转场效果
        self._add_transition_effects()

        # 颜色效果
        self._add_color_effects()

        self.logger.info(f"Loaded {len(self.effects_db)} builtin effects")

    def _add_video_effects(self):
        """添加视频效果"""
        # 模糊效果
        blur_params = [
            EffectParameter("radius", "float", 5.0, 0.0, 20.0, 0.1, "模糊半径", "px"),
            EffectParameter("iterations", "int", 1, 1, 10, 1, "迭代次数", "")
        ]

        self.effects_db["blur"] = EffectInfo(
            id="blur", name="高斯模糊", type=EffectType.VIDEO,
            category=EffectCategory.BLUR, description="高斯模糊效果",
            parameters=blur_params, presets=[], gpu_accelerated=True
        )

        # 锐化效果
        sharpen_params = [
            EffectParameter("amount", "float", 1.0, 0.0, 3.0, 0.1, "锐化强度", ""),
            EffectParameter("radius", "float", 1.0, 0.5, 5.0, 0.1, "锐化半径", "px")
        ]

        self.effects_db["sharpen"] = EffectInfo(
            id="sharpen", name="锐化", type=EffectType.VIDEO,
            category=EffectCategory.SHARPEN, description="视频锐化效果",
            parameters=sharpen_params, presets=[], gpu_accelerated=True
        )

        # 亮度/对比度
        brightness_params = [
            EffectParameter("brightness", "float", 0.0, -100.0, 100.0, 1.0, "亮度", ""),
            EffectParameter("contrast", "float", 1.0, 0.0, 3.0, 0.1, "对比度", "")
        ]

        self.effects_db["brightness_contrast"] = EffectInfo(
            id="brightness_contrast", name="亮度对比度", type=EffectType.VIDEO,
            category=EffectCategory.BASIC, description="调整亮度和对比度",
            parameters=brightness_params, presets=[], gpu_accelerated=True, real_time=True
        )

        # 缩放效果
        scale_params = [
            EffectParameter("scale_x", "float", 1.0, 0.1, 3.0, 0.1, "X轴缩放", ""),
            EffectParameter("scale_y", "float", 1.0, 0.1, 3.0, 0.1, "Y轴缩放", ""),
            EffectParameter("center_x", "float", 0.5, 0.0, 1.0, 0.01, "中心X", ""),
            EffectParameter("center_y", "float", 0.5, 0.0, 1.0, 0.01, "中心Y", "")
        ]

        self.effects_db["scale"] = EffectInfo(
            id="scale", name="缩放", type=EffectType.VIDEO,
            category=EffectCategory.TRANSFORM, description="视频缩放效果",
            parameters=scale_params, presets=[], gpu_accelerated=True, real_time=True
        )

    def _add_audio_effects(self):
        """添加音频效果"""
        # 音量调整
        volume_params = [
            EffectParameter("volume", "float", 1.0, 0.0, 5.0, 0.1, "音量", "dB"),
            EffectParameter("fade_in", "float", 0.0, 0.0, 10.0, 0.1, "淡入时间", "s"),
            EffectParameter("fade_out", "float", 0.0, 0.0, 10.0, 0.1, "淡出时间", "s")
        ]

        self.effects_db["volume"] = EffectInfo(
            id="volume", name="音量", type=EffectType.AUDIO,
            category=EffectCategory.AUDIO, description="音频音量调整",
            parameters=volume_params, presets=[], real_time=True
        )

        # 均衡器
        eq_params = [
            EffectParameter("low_freq", "float", 0.0, -20.0, 20.0, 0.1, "低频", "dB"),
            EffectParameter("mid_freq", "float", 0.0, -20.0, 20.0, 0.1, "中频", "dB"),
            EffectParameter("high_freq", "float", 0.0, -20.0, 20.0, 0.1, "高频", "dB")
        ]

        self.effects_db["equalizer"] = EffectInfo(
            id="equalizer", name="均衡器", type=EffectType.AUDIO,
            category=EffectCategory.AUDIO, description="三段均衡器",
            parameters=eq_params, presets=[], real_time=True
        )

        # 混响
        reverb_params = [
            EffectParameter("room_size", "float", 0.5, 0.0, 1.0, 0.01, "房间大小", ""),
            EffectParameter("damping", "float", 0.5, 0.0, 1.0, 0.01, "阻尼", ""),
            EffectParameter("wet_level", "float", 0.3, 0.0, 1.0, 0.01, "混响强度", "")
        ]

        self.effects_db["reverb"] = EffectInfo(
            id="reverb", name="混响", type=EffectType.AUDIO,
            category=EffectCategory.AUDIO, description="混响效果",
            parameters=reverb_params, presets=[], real_time=True
        )

    def _add_transition_effects(self):
        """添加转场效果"""
        # 淡入淡出
        fade_params = [
            EffectParameter("duration", "float", 1.0, 0.1, 5.0, 0.1, "持续时间", "s"),
            EffectParameter("direction", "string", "in", None, None, None, "方向", "")
        ]

        self.effects_db["fade"] = EffectInfo(
            id="fade", name="淡入淡出", type=EffectType.TRANSITION,
            category=EffectCategory.TRANSITION, description="淡入淡出转场",
            parameters=fade_params, presets=[], real_time=True
        )

        # 滑动转场
        slide_params = [
            EffectParameter("duration", "float", 1.0, 0.1, 5.0, 0.1, "持续时间", "s"),
            EffectParameter("direction", "string", "left", None, None, None, "方向", "")
        ]

        self.effects_db["slide"] = EffectInfo(
            id="slide", name="滑动", type=EffectType.TRANSITION,
            category=EffectCategory.TRANSITION, description="滑动转场效果",
            parameters=slide_params, presets=[], real_time=True
        )

        # 缩放转场
        zoom_params = [
            EffectParameter("duration", "float", 1.0, 0.1, 5.0, 0.1, "持续时间", "s"),
            EffectParameter("scale", "float", 2.0, 0.5, 5.0, 0.1, "缩放比例", "")
        ]

        self.effects_db["zoom"] = EffectInfo(
            id="zoom", name="缩放", type=EffectType.TRANSITION,
            category=EffectCategory.TRANSITION, description="缩放转场效果",
            parameters=zoom_params, presets=[], real_time=True
        )

    def _add_color_effects(self):
        """添加颜色效果"""
        # 色相饱和度
        hsl_params = [
            EffectParameter("hue", "float", 0.0, -180.0, 180.0, 1.0, "色相", "°"),
            EffectParameter("saturation", "float", 1.0, 0.0, 3.0, 0.1, "饱和度", ""),
            EffectParameter("lightness", "float", 0.0, -100.0, 100.0, 1.0, "亮度", "")
        ]

        self.effects_db["hsl"] = EffectInfo(
            id="hsl", name="色相饱和度", type=EffectType.COLOR,
            category=EffectCategory.COLOR, description="色相、饱和度、亮度调整",
            parameters=hsl_params, presets=[], gpu_accelerated=True, real_time=True
        )

        # 色彩平衡
        balance_params = [
            EffectParameter("cyan_red", "float", 0.0, -100.0, 100.0, 1.0, "青红", ""),
            EffectParameter("magenta_green", "float", 0.0, -100.0, 100.0, 1.0, "洋绿", ""),
            EffectParameter("yellow_blue", "float", 0.0, -100.0, 100.0, 1.0, "黄蓝", "")
        ]

        self.effects_db["color_balance"] = EffectInfo(
            id="color_balance", name="色彩平衡", type=EffectType.COLOR,
            category=EffectCategory.COLOR, description="色彩平衡调整",
            parameters=balance_params, presets=[], gpu_accelerated=True, real_time=True
        )

        # 色阶
        levels_params = [
            EffectParameter("input_black", "float", 0.0, 0.0, 255.0, 1.0, "输入黑场", ""),
            EffectParameter("input_white", "float", 255.0, 0.0, 255.0, 1.0, "输入白场", ""),
            EffectParameter("output_black", "float", 0.0, 0.0, 255.0, 1.0, "输出黑场", ""),
            EffectParameter("output_white", "float", 255.0, 0.0, 255.0, 1.0, "输出白场", "")
        ]

        self.effects_db["levels"] = EffectInfo(
            id="levels", name="色阶", type=EffectType.COLOR,
            category=EffectCategory.COLOR, description="色阶调整",
            parameters=levels_params, presets=[], gpu_accelerated=True, real_time=True
        )

    def get_effect_info(self, effect_id: str) -> Optional[EffectInfo]:
        """获取效果信息"""
        return self.effects_db.get(effect_id)

    def list_effects(self, effect_type: EffectType = None, category: EffectCategory = None) -> List[EffectInfo]:
        """列出效果"""
        effects = list(self.effects_db.values())

        if effect_type:
            effects = [e for e in effects if e.type == effect_type]

        if category:
            effects = [e for e in effects if e.category == category]

        return effects

    def create_effect(self, effect_id: str, parameters: Dict[str, Any] = None) -> Optional[EffectInstance]:
        """创建效果实例"""
        effect_info = self.effects_db.get(effect_id)
        if not effect_info:
            self.logger.error(f"Effect not found: {effect_id}")
            return None

        return EffectInstance(effect_info, parameters)

    def apply_effect(self, effect_instance: EffectInstance, input_path: str, output_path: str,
                    start_time: float = 0.0, duration: float = 0.0) -> bool:
        """应用效果到视频"""
        try:
            effect_info = effect_instance.effect_info

            # 构建FFmpeg滤镜链
            filter_chain = self._build_filter_chain(effect_instance, start_time, duration)

            # 使用视频引擎处理
            result = self.video_engine.apply_filters(
                input_path, output_path, filter_chain,
                start_time=start_time, duration=duration
            )

            if result:
                self.effect_processed.emit(effect_info.id, True)
                self.logger.info(f"Applied effect {effect_info.name} to {input_path}")
            else:
                self.effect_processed.emit(effect_info.id, False)
                self.logger.error(f"Failed to apply effect {effect_info.name}")

            return result

        except Exception as e:
            self.logger.error(f"Error applying effect: {e}")
            self.effect_processed.emit(effect_instance.effect_info.id, False)
            return False

    def _build_filter_chain(self, effect_instance: EffectInstance, start_time: float, duration: float) -> str:
        """构建FFmpeg滤镜链"""
        effect_id = effect_instance.effect_info.id
        params = effect_instance.parameters

        filter_chain = ""

        # 根据效果类型构建滤镜
        if effect_id == "blur":
            radius = params.get("radius", 5.0)
            iterations = params.get("iterations", 1)
            filter_chain = f"boxblur=luma_radius={radius}:chroma_radius={radius}:luma_power={iterations}"

        elif effect_id == "sharpen":
            amount = params.get("amount", 1.0)
            filter_chain = f"unsharp=luma_msize_x=7:luma_msize_y=7:luma_amount={amount}"

        elif effect_id == "brightness_contrast":
            brightness = params.get("brightness", 0.0)
            contrast = params.get("contrast", 1.0)
            filter_chain = f"eq=brightness={brightness}:contrast={contrast}"

        elif effect_id == "scale":
            scale_x = params.get("scale_x", 1.0)
            scale_y = params.get("scale_y", 1.0)
            filter_chain = f"scale=iw*{scale_x}:ih*{scale_y}"

        elif effect_id == "hsl":
            hue = params.get("hue", 0.0)
            saturation = params.get("saturation", 1.0)
            lightness = params.get("lightness", 0.0)
            filter_chain = f"hue=h={hue}:s={saturation}:l={lightness}"

        elif effect_id == "color_balance":
            cr = params.get("cyan_red", 0.0)
            mg = params.get("magenta_green", 0.0)
            yb = params.get("yellow_blue", 0.0)
            filter_chain = f"colorbalance=rs={cr}:gs={mg}:bs={yb}"

        elif effect_id == "levels":
            in_black = params.get("input_black", 0.0)
            in_white = params.get("input_white", 255.0)
            out_black = params.get("output_black", 0.0)
            out_white = params.get("output_white", 255.0)
            filter_chain = f"levels=in={in_black}:{in_white}:out={out_black}:{out_white}"

        return filter_chain

    def apply_transition(self, transition_effect: EffectInstance,
                        clip1_path: str, clip2_path: str,
                        output_path: str, duration: float) -> bool:
        """应用转场效果"""
        try:
            filter_chain = self._build_transition_filter(transition_effect, duration)

            # 使用FFmpeg进行转场
            cmd = [
                'ffmpeg',
                '-i', clip1_path,
                '-i', clip2_path,
                '-filter_complex', filter_chain,
                '-t', str(duration),
                '-y', output_path
            ]

            result = self.ffmpeg_utils.run_ffmpeg_command(cmd)

            if result:
                self.effect_processed.emit(transition_effect.effect_info.id, True)
                self.logger.info(f"Applied transition {transition_effect.effect_info.name}")
            else:
                self.effect_processed.emit(transition_effect.effect_info.id, False)
                self.logger.error(f"Failed to apply transition")

            return result

        except Exception as e:
            self.logger.error(f"Error applying transition: {e}")
            return False

    def _build_transition_filter(self, transition_effect: EffectInstance, duration: float) -> str:
        """构建转场滤镜"""
        effect_id = transition_effect.effect_info.id
        params = transition_effect.parameters

        if effect_id == "fade":
            direction = params.get("direction", "in")
            if direction == "in":
                return f"[0:v]fade=t=in:st=0:d={duration}[outv]"
            else:
                return f"[0:v]fade=t=out:st=0:d={duration}[outv]"

        elif effect_id == "slide":
            direction = params.get("direction", "left")
            return f"[0:v][1:v]xfade=transition=slideleft:duration={duration}:offset=0[outv]"

        elif effect_id == "zoom":
            scale = params.get("scale", 2.0)
            return f"[0:v][1:v]xfade=transition=zoom:duration={duration}:offset=0[outv]"

        return ""

    def generate_preview(self, effect_instance: EffectInstance, input_path: str,
                        timestamp: float = 0.0) -> Optional[QImage]:
        """生成效果预览"""
        try:
            # 生成预览文件名
            preview_path = os.path.join(self.cache_dir, f"preview_{effect_instance.effect_info.id}.jpg")

            # 提取一帧并应用效果
            filter_chain = self._build_filter_chain(effect_instance, 0.0, 0.0)

            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', input_path,
                '-vframes', '1',
                '-vf', filter_chain,
                '-y', preview_path
            ]

            if self.ffmpeg_utils.run_ffmpeg_command(cmd):
                preview = QImage(preview_path)
                self.preview_updated.emit(effect_instance.effect_info.id, preview)
                return preview

        except Exception as e:
            self.logger.error(f"Failed to generate preview: {e}")

        return None

    def batch_process(self, effect_instances: List[EffectInstance],
                     input_path: str, output_path: str) -> bool:
        """批量处理多个效果"""
        try:
            # 构建复合滤镜链
            filter_parts = []
            for i, effect in enumerate(effect_instances):
                filter_chain = self._build_filter_chain(effect, 0.0, 0.0)
                if filter_chain:
                    filter_parts.append(filter_chain)

            if not filter_parts:
                return False

            combined_filter = ",".join(filter_parts)

            # 应用复合滤镜
            result = self.video_engine.apply_filters(input_path, output_path, combined_filter)

            if result:
                for effect in effect_instances:
                    self.effect_processed.emit(effect.effect_info.id, True)
            else:
                for effect in effect_instances:
                    self.effect_processed.emit(effect.effect_info.id, False)

            return result

        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            return False

    def get_gpu_acceleration_status(self) -> Dict[str, bool]:
        """获取GPU加速状态"""
        return {
            "cuda_available": self.hardware_acceleration.cuda_available,
            "opencl_available": self.hardware_acceleration.opencl_available,
            "metal_available": self.hardware_acceleration.metal_available,
            "vaapi_available": self.hardware_acceleration.vaapi_available
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            "total_effects": len(self.effects_db),
            "active_effects": len(self.active_effects),
            "cache_size": self._get_cache_size(),
            "gpu_acceleration": self.get_gpu_acceleration_status()
        }

    def _get_cache_size(self) -> int:
        """获取缓存大小"""
        total_size = 0
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size

    def cleanup_cache(self):
        """清理缓存"""
        try:
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            self.logger.info("Effects cache cleaned")
        except Exception as e:
            self.logger.error(f"Failed to cleanup cache: {e}")

    def shutdown(self):
        """关闭效果引擎"""
        self.thread_pool.shutdown(wait=True)
        self.cleanup_cache()
        self.logger.info("Effects engine shutdown complete")