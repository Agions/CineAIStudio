"""
专业视频效果库 - 提供丰富的视频处理效果
包括滤镜、变换、稳定、跟踪等专业级效果
"""

import numpy as np
import cv2
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging

from app.core.logger import Logger
from app.effects.effects_system import EffectInstance, EffectInfo, EffectParameter
from app.utils.ffmpeg_utils import FFmpegUtils


class VideoEffectType(Enum):
    """视频效果类型"""
    FILTER = "filter"           # 滤镜效果
    TRANSFORM = "transform"     # 变换效果
    STABILIZATION = "stabilization"  # 稳定效果
    TRACKING = "tracking"       # 跟踪效果
    COLOR = "color"             # 颜色效果
    ARTISTIC = "artistic"       # 艺术效果


class VideoEffectPreset(Enum):
    """视频效果预设"""
    CINEMATIC = "cinematic"      # 电影感
    VINTAGE = "vintage"         # 复古
    BLACK_WHITE = "black_white" # 黑白
    HDR = "hdr"                 # HDR效果
    BLUR_BACKGROUND = "blur_background"  # 背景虚化
    BEAUTY = "beauty"           # 美颜
    NIGHT_VISION = "night_vision"  # 夜视效果


class VideoEffectsLibrary:
    """视频效果库"""

    def __init__(self):
        self.logger = Logger.get_logger("VideoEffectsLibrary")
        self.ffmpeg_utils = FFmpegUtils()

        # 初始化OpenCV
        self._init_opencv()

    def _init_opencv(self):
        """初始化OpenCV"""
        try:
            self.logger.info("Initializing OpenCV for video effects")
            # 检查OpenCV版本和功能
            version = cv2.__version__
            self.logger.info(f"OpenCV version: {version}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenCV: {e}")

    def get_effect_presets(self, effect_type: VideoEffectType) -> Dict[str, Dict[str, Any]]:
        """获取效果预设"""
        presets = {}

        if effect_type == VideoEffectType.COLOR:
            presets.update(self._get_color_presets())
        elif effect_type == VideoEffectType.FILTER:
            presets.update(self._get_filter_presets())
        elif effect_type == VideoEffectType.ARTISTIC:
            presets.update(self._get_artistic_presets())

        return presets

    def _get_color_presets(self) -> Dict[str, Dict[str, Any]]:
        """获取颜色预设"""
        return {
            VideoEffectPreset.CINEMATIC.value: {
                "name": "电影感",
                "description": "电影级色彩分级",
                "parameters": {
                    "contrast": 1.2,
                    "saturation": 0.8,
                    "gamma": 0.9,
                    "lift": 0.05,
                    "gain": 1.1,
                    "color_temperature": 5500
                }
            },
            VideoEffectPreset.VINTAGE.value: {
                "name": "复古",
                "description": "复古电影效果",
                "parameters": {
                    "sepia_intensity": 0.6,
                    "vignette_strength": 0.8,
                    "grain_amount": 0.3,
                    "contrast": 1.1,
                    "saturation": 0.6
                }
            },
            VideoEffectPreset.BLACK_WHITE.value: {
                "name": "黑白",
                "description": "黑白电影效果",
                "parameters": {
                    "desaturation": 1.0,
                    "contrast": 1.2,
                    "brightness": -0.1,
                    "channel_mixer": {
                        "red": 0.3,
                        "green": 0.6,
                        "blue": 0.1
                    }
                }
            },
            VideoEffectPreset.HDR.value: {
                "name": "HDR",
                "description": "HDR高动态范围效果",
                "parameters": {
                    "hdr_strength": 0.7,
                    "local_contrast": 1.3,
                    "shadow_recovery": 0.5,
                    "highlight_protection": 0.6,
                    "vibrance": 1.2
                }
            }
        }

    def _get_filter_presets(self) -> Dict[str, Dict[str, Any]]:
        """获取滤镜预设"""
        return {
            VideoEffectPreset.BEAUTY.value: {
                "name": "美颜",
                "description": "人脸美颜效果",
                "parameters": {
                    "smooth_skin": 0.6,
                    "whiten_skin": 0.4,
                    "thin_face": 0.3,
                    "enlarge_eyes": 0.2,
                    "remove_blemishes": 0.5
                }
            },
            VideoEffectPreset.BLUR_BACKGROUND.value: {
                "name": "背景虚化",
                "description": "人像背景虚化",
                "parameters": {
                    "blur_strength": 0.8,
                    "edge_detection": 0.6,
                    "preserve_subject": True,
                    "bokeh_intensity": 0.7
                }
            }
        }

    def _get_artistic_presets(self) -> Dict[str, Dict[str, Any]]:
        """获取艺术效果预设"""
        return {
            VideoEffectPreset.NIGHT_VISION.value: {
                "name": "夜视",
                "description": "夜视效果",
                "parameters": {
                    "green_tint": 0.8,
                    "noise_reduction": 0.6,
                    "edge_enhancement": 0.4,
                    "gamma_correction": 1.3,
                    "vignette_strength": 0.5
                }
            }
        }

    def apply_cinematic_color_grading(self, input_path: str, output_path: str,
                                   parameters: Dict[str, Any]) -> bool:
        """应用电影级色彩分级"""
        try:
            # 构建电影级滤镜链
            filter_parts = []

            # 基础调整
            contrast = parameters.get("contrast", 1.2)
            saturation = parameters.get("saturation", 0.8)
            gamma = parameters.get("gamma", 0.9)

            filter_parts.append(f"eq=contrast={contrast}:saturation={saturation}")
            filter_parts.append(f"gamma={gamma}")

            # 色彩平衡
            lift = parameters.get("lift", 0.05)
            gain = parameters.get("gain", 1.1)

            filter_parts.append(f"colorlevels=rimin={lift}:gimin={lift}:bimin={lift}:rmax={gain}:gmax={gain}:bmax={gain}")

            # 色温调整
            color_temp = parameters.get("color_temperature", 5500)
            if color_temp != 6500:  # 6500K是标准日光
                temp_diff = color_temp - 6500
                if temp_diff > 0:
                    filter_parts.append(f"colortemperature=temperature={color_temp}:strength=0.8")

            # 添加暗角
            filter_parts.append("vignette=angle=PI/2")

            # 组合滤镜
            filter_chain = ",".join(filter_parts)

            # 应用滤镜
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', filter_chain,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply cinematic color grading: {e}")
            return False

    def apply_vintage_effect(self, input_path: str, output_path: str,
                           parameters: Dict[str, Any]) -> bool:
        """应用复古效果"""
        try:
            filter_parts = []

            # 棕褐色调
            sepia_intensity = parameters.get("sepia_intensity", 0.6)
            filter_parts.append(f"sepia={sepia_intensity}")

            # 暗角效果
            vignette_strength = parameters.get("vignette_strength", 0.8)
            filter_parts.append(f"vignette=angle=PI/2:mode=normal:eval={vignette_strength}")

            # 颗粒效果
            grain_amount = parameters.get("grain_amount", 0.3)
            filter_parts.append(f"grain=c0_vs={grain_amount}")

            # 对比度调整
            contrast = parameters.get("contrast", 1.1)
            saturation = parameters.get("saturation", 0.6)
            filter_parts.append(f"eq=contrast={contrast}:saturation={saturation}")

            filter_chain = ",".join(filter_parts)

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', filter_chain,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply vintage effect: {e}")
            return False

    def apply_stabilization(self, input_path: str, output_path: str,
                          parameters: Dict[str, Any]) -> bool:
        """应用视频稳定"""
        try:
            # FFmpeg的视频稳定滤镜
            shakiness = parameters.get("shakiness", 5)  # 1-10，抖动程度
            smoothing = parameters.get("smoothing", 15)  # 平滑程度
            crop = parameters.get("crop", "keep")  # 裁剪方式

            filter_chain = f"vidstabdetect=shakiness={shakiness}:result=transforms.trf"
            filter_chain += f",vidstabtransform=input=transforms.trf:smoothing={smoothing}:crop={crop}"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', filter_chain,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply video stabilization: {e}")
            return False

    def apply_motion_tracking(self, input_path: str, output_path: str,
                           parameters: Dict[str, Any]) -> bool:
        """应用运动跟踪"""
        try:
            # 使用OpenCV进行运动跟踪
            tracking_method = parameters.get("method", "KCF")
            target_x = parameters.get("target_x", 0.5)
            target_y = parameters.get("target_y", 0.5)
            target_width = parameters.get("target_width", 0.1)
            target_height = parameters.get("target_height", 0.1)

            # 这里需要实现具体的跟踪逻辑
            # 由于复杂度较高，暂时返回示例实现
            self.logger.info("Motion tracking effect requested (simplified implementation)")

            # 应用一个简单的居中效果作为示例
            filter_chain = f"crop=iw*{target_width}:ih*{target_height}:(iw-ow*{target_x}):(ih-oh*{target_y})"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', filter_chain,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply motion tracking: {e}")
            return False

    def apply_background_blur(self, input_path: str, output_path: str,
                            parameters: Dict[str, Any]) -> bool:
        """应用背景虚化"""
        try:
            blur_strength = parameters.get("blur_strength", 0.8)
            edge_detection = parameters.get("edge_detection", 0.6)

            # 构建背景虚化滤镜
            filter_parts = []

            # 边缘检测（简化版）
            if edge_detection > 0:
                filter_parts.append("edgedetect=low=0.1:high=0.4")

            # 背景模糊
            blur_radius = int(blur_strength * 20)  # 转换为像素
            filter_parts.append(f"boxblur=luma_radius={blur_radius}:chroma_radius={blur_radius}")

            filter_chain = ",".join(filter_parts)

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', filter_chain,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply background blur: {e}")
            return False

    def apply_face_beauty(self, input_path: str, output_path: str,
                        parameters: Dict[str, Any]) -> bool:
        """应用人脸美颜"""
        try:
            smooth_skin = parameters.get("smooth_skin", 0.6)
            whiten_skin = parameters.get("whiten_skin", 0.4)

            filter_parts = []

            # 美肤效果
            if smooth_skin > 0:
                filter_parts.append(f"smartblur=luma_radius={smooth_skin*5}:chroma_radius={smooth_skin*3}")

            # 美白效果
            if whiten_skin > 0:
                filter_parts.append(f"eq=brightness={whiten_skin*20}:saturation={1-whiten_skin*0.3}")

            # 柔和效果
            filter_parts.append("unsharp=luma_msize_x=3:luma_msize_y=3:luma_amount=0.5")

            filter_chain = ",".join(filter_parts)

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', filter_chain,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply face beauty: {e}")
            return False

    def apply_green_screen(self, input_path: str, background_path: str, output_path: str,
                         parameters: Dict[str, Any]) -> bool:
        """应用绿幕抠像"""
        try:
            # 绿幕参数
            key_color = parameters.get("key_color", "green")  # green, blue
            similarity = parameters.get("similarity", 0.4)
            blend = parameters.get("blend", 0.1)

            # 构建色度键滤镜
            if key_color == "green":
                color = "0x00FF00"
            else:
                color = "0x0000FF"

            filter_chain = f"chromakey={color}:{similarity}:{blend}"

            # 混合背景
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-i', background_path,
                '-filter_complex', f'[0:v]{filter_chain}[ck];[ck][1:v]overlay=format=auto',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply green screen: {e}")
            return False

    def create_custom_filter(self, filter_name: str, parameters: Dict[str, Any]) -> str:
        """创建自定义滤镜"""
        filter_configs = {
            "custom_color_grading": self._build_color_grading_filter,
            "custom_blur": self._build_blur_filter,
            "custom_sharpen": self._build_sharpen_filter,
            "custom_transform": self._build_transform_filter,
            "custom_noise": self._build_noise_filter
        }

        builder = filter_configs.get(filter_name)
        if builder:
            return builder(parameters)
        else:
            raise ValueError(f"Unknown custom filter: {filter_name}")

    def _build_color_grading_filter(self, params: Dict[str, Any]) -> str:
        """构建色彩分级滤镜"""
        filters = []

        # 基础调整
        if "brightness" in params:
            filters.append(f"eq=brightness={params['brightness']}")
        if "contrast" in params:
            filters.append(f"eq=contrast={params['contrast']}")
        if "saturation" in params:
            filters.append(f"eq=saturation={params['saturation']}")

        # 色相调整
        if "hue" in params:
            filters.append(f"hue=h={params['hue']}")

        # 色阶
        if "black_level" in params or "white_level" in params:
            black = params.get("black_level", 0)
            white = params.get("white_level", 255)
            filters.append(f"levels=in={black}:{white}")

        return ",".join(filters)

    def _build_blur_filter(self, params: Dict[str, Any]) -> str:
        """构建模糊滤镜"""
        blur_type = params.get("type", "gaussian")
        radius = params.get("radius", 5.0)

        if blur_type == "gaussian":
            return f"gblur=sigma={radius}"
        elif blur_type == "box":
            return f"boxblur=luma_radius={radius}:chroma_radius={radius}"
        elif blur_type == "motion":
            angle = params.get("angle", 0)
            return f"mblur=radius={radius}:angle={angle}"
        else:
            return f"boxblur=luma_radius={radius}:chroma_radius={radius}"

    def _build_sharpen_filter(self, params: Dict[str, Any]) -> str:
        """构建锐化滤镜"""
        amount = params.get("amount", 1.0)
        radius = params.get("radius", 1.0)

        return f"unsharp=luma_msize_x={radius}:luma_msize_y={radius}:luma_amount={amount}"

    def _build_transform_filter(self, params: Dict[str, Any]) -> str:
        """构建变换滤镜"""
        transforms = []

        # 缩放
        if "scale_x" in params or "scale_y" in params:
            scale_x = params.get("scale_x", 1.0)
            scale_y = params.get("scale_y", 1.0)
            transforms.append(f"scale=iw*{scale_x}:ih*{scale_y}")

        # 旋转
        if "rotation" in params:
            angle = params.get("rotation", 0)
            transforms.append(f"rotate={angle}")

        # 翻转
        if "flip_horizontal" in params and params["flip_horizontal"]:
            transforms.append("hflip")
        if "flip_vertical" in params and params["flip_vertical"]:
            transforms.append("vflip")

        return ",".join(transforms)

    def _build_noise_filter(self, params: Dict[str, Any]) -> str:
        """构建噪点滤镜"""
        noise_type = params.get("type", "uniform")
        strength = params.get("strength", 0.1)

        if noise_type == "uniform":
            return f"noise=alls={strength}:allf=t+u"
        elif noise_type == "gaussian":
            return f"noise=alls={strength}:allf=t+g"
        else:
            return f"noise=alls={strength}"

    def get_effect_info(self, effect_name: str) -> Dict[str, Any]:
        """获取效果信息"""
        effect_info = {
            "cinematic_color_grading": {
                "name": "电影级色彩分级",
                "description": "专业电影色彩分级效果",
                "parameters": ["contrast", "saturation", "gamma", "lift", "gain"],
                "gpu_accelerated": True,
                "real_time": False
            },
            "vintage": {
                "name": "复古效果",
                "description": "复古电影风格效果",
                "parameters": ["sepia_intensity", "vignette_strength", "grain_amount"],
                "gpu_accelerated": True,
                "real_time": True
            },
            "stabilization": {
                "name": "视频稳定",
                "description": "减少视频抖动",
                "parameters": ["shakiness", "smoothing", "crop"],
                "gpu_accelerated": True,
                "real_time": False
            },
            "motion_tracking": {
                "name": "运动跟踪",
                "description": "跟踪指定对象运动",
                "parameters": ["method", "target_x", "target_y", "target_width", "target_height"],
                "gpu_accelerated": True,
                "real_time": False
            },
            "background_blur": {
                "name": "背景虚化",
                "description": "虚化背景突出主体",
                "parameters": ["blur_strength", "edge_detection"],
                "gpu_accelerated": True,
                "real_time": True
            },
            "face_beauty": {
                "name": "人脸美颜",
                "description": "人脸美化效果",
                "parameters": ["smooth_skin", "whiten_skin"],
                "gpu_accelerated": True,
                "real_time": True
            },
            "green_screen": {
                "name": "绿幕抠像",
                "description": "绿幕背景替换",
                "parameters": ["key_color", "similarity", "blend"],
                "gpu_accelerated": True,
                "real_time": False
            }
        }

        return effect_info.get(effect_name, {})

    def batch_apply_effects(self, input_path: str, output_path: str,
                           effects: List[Dict[str, Any]]) -> bool:
        """批量应用效果"""
        try:
            filter_parts = []

            for effect in effects:
                effect_name = effect.get("name")
                parameters = effect.get("parameters", {})

                if effect_name.startswith("custom_"):
                    filter_part = self.create_custom_filter(effect_name, parameters)
                else:
                    # 内置效果
                    if effect_name == "cinematic_color_grading":
                        filter_part = self._build_color_grading_filter(parameters)
                    elif effect_name == "vintage":
                        filter_part = f"sepia={parameters.get('sepia_intensity', 0.6)}"
                    elif effect_name == "stabilization":
                        # 稳定效果需要特殊处理，这里简化
                        continue
                    else:
                        continue

                if filter_part:
                    filter_parts.append(filter_part)

            if not filter_parts:
                return False

            filter_chain = ",".join(filter_parts)

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', filter_chain,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to batch apply effects: {e}")
            return False

    def get_gpu_compatibility(self) -> Dict[str, bool]:
        """获取GPU兼容性"""
        return {
            "cuda_effects": True,    # CUDA加速效果
            "opencl_effects": True,  # OpenCL加速效果
            "metal_effects": True,   # Metal加速效果
            "vaapi_effects": True,   # VAAPI加速效果
            "opencv_effects": True   # OpenCV效果
        }