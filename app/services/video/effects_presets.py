#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频效果预设
内置常用视频效果配置
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class TransitionType(Enum):
    """转场类型"""
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    SLIDE = "slide"
    ZOOM = "zoom"
    BLUR = "blur"
    GLITCH = "glitch"


class EffectType(Enum):
    """效果类型"""
    BLUR = "blur"
    SHARPEN = "sharpen"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    SATURATION = "saturation"
    VIGNETTE = "vignette"
    GRAIN = "grain"
    COLOR_GRADE = "color_grade"
    LUT = "lut"


@dataclass
class TransitionPreset:
    """转场预设"""
    name: str
    type: TransitionType
    duration: float = 0.5
    
    # 方向 (用于 wipe/slide)
    direction: str = "left"  # left/right/up/down
    
    # 缓动
    easing: str = "ease-in-out"
    
    @classmethod
    def get_defaults(cls) -> Dict[str, "TransitionPreset"]:
        return {
            "fade": cls("淡入淡出", TransitionType.FADE, 0.5),
            "dissolve": cls("溶解", TransitionType.DISSOLVE, 0.8),
            "slide_left": cls("左滑", TransitionType.SLIDE, 0.4, "left"),
            "slide_right": cls("右滑", TransitionType.SLIDE, 0.4, "right"),
            "wipe_left": cls("左擦除", TransitionType.WIPE, 0.5, "left"),
            "zoom_in": cls("缩放进入", TransitionType.ZOOM, 0.4),
            "blur": cls("模糊转场", TransitionType.BLUR, 0.5),
            "glitch": cls("故障效果", TransitionType.GLITCH, 0.3),
        }


@dataclass
class FilterPreset:
    """滤镜预设"""
    name: str
    description: str
    
    # 基础调整
    brightness: float = 0      # -1 to 1
    contrast: float = 0        # -1 to 1
    saturation: float = 0      # -1 to 1
    gamma: float = 1.0         # 0.1 to 3
    
    # 效果
    blur: float = 0            # 0 to 20
    sharpen: float = 0         # 0 to 5
    vignette: float = 0        # 0 to 1
    
    # 颜色分级
    temperature: float = 0     # -1 to 1 (cool to warm)
    tint: float = 0            # -1 to 1 (green to magenta)
    
    # 预设滤镜
    @classmethod
    def get_defaults(cls) -> Dict[str, "FilterPreset"]:
        return {
            "vivid": cls(
                name="鲜艳",
                description="增强色彩饱和度",
                saturation=0.3,
                contrast=0.1,
                brightness=0.05,
            ),
            "warm": cls(
                name="暖色调",
                description="温馨暖色",
                temperature=0.3,
                saturation=0.1,
            ),
            "cool": cls(
                name="冷色调",
                description="清新冷色",
                temperature=-0.3,
                saturation=-0.1,
            ),
            "vintage": cls(
                name="复古",
                description="怀旧风格",
                contrast=0.2,
                saturation=-0.2,
                vignette=0.3,
                gamma=1.1,
            ),
            "noir": cls(
                name="黑白",
                description="黑白电影",
                saturation=-1.0,
                contrast=0.3,
                vignette=0.4,
            ),
            "cinematic": cls(
                name="电影感",
                description="专业电影调色",
                contrast=0.2,
                saturation=-0.1,
                temperature=-0.05,
                tint=0.05,
                vignette=0.3,
            ),
            "glow": cls(
                name="发光",
                description="梦幻发光效果",
                brightness=0.15,
                saturation=0.2,
                gamma=1.1,
            ),
            "dramatic": cls(
                name="戏剧性",
                description="高对比度戏剧效果",
                contrast=0.5,
                brightness=-0.1,
                saturation=0.1,
                vignette=0.5,
            ),
        }


@dataclass
class TextStylePreset:
    """文字样式预设"""
    name: str
    
    # 字体
    font_family: str = "思源黑体"
    font_size: int = 32
    font_weight: str = "bold"
    
    # 颜色
    text_color: str = "#FFFFFF"
    stroke_color: str = "#000000"
    stroke_width: float = 2.0
    shadow_color: str = "#000000"
    shadow_offset: float = 2.0
    
    # 背景
    bg_color: str = ""
    bg_opacity: float = 0
    
    # 对齐
    alignment: str = "center"  # left/center/right
    
    # 动画
    animation: str = "none"  # none/fade/slide/type
    
    @classmethod
    def get_defaults(cls) -> Dict[str, "TextStylePreset"]:
        return {
            "title": cls(
                name="标题",
                font_size=48,
                font_weight="bold",
                stroke_width=3,
            ),
            "subtitle": cls(
                name="副标题",
                font_size=32,
                font_weight="semi-bold",
                stroke_width=2,
            ),
            "caption": cls(
                name="说明文字",
                font_size=24,
                font_weight="normal",
                stroke_width=1.5,
            ),
            "subtitle_bottom": cls(
                name="底部字幕",
                font_size=28,
                font_weight="medium",
                bg_color="#000000",
                bg_opacity=0.6,
                alignment="center",
            ),
            "watermark": cls(
                name="水印",
                font_size=18,
                font_weight="light",
                text_color="#FFFFFF",
                opacity=0.7,
            ),
        }


@dataclass
class ColorPalette:
    """调色板"""
    name: str
    colors: List[str]  # HEX 颜色列表
    
    @classmethod
    def get_defaults(cls) -> Dict[str, "ColorPalette"]:
        return {
            "sunset": cls(
                name="日落",
                colors=["#FF6B6B", "#FFA07A", "#FFD93D", "#6BCB77"],
            ),
            "ocean": cls(
                name="海洋",
                colors=["#4ECDC4", "#44A08D", "#093028", "#2C3E50"],
            ),
            "neon": cls(
                name="霓虹",
                colors=["#FF00FF", "#00FFFF", "#FF0080", "#8000FF"],
            ),
            "pastel": cls(
                name="粉彩",
                colors=["#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9"],
            ),
            "corporate": cls(
                name="商务",
                colors=["#2C3E50", "#34495E", "#3498DB", "#ECF0F1"],
            ),
        }


# 导出
__all__ = [
    "TransitionType",
    "EffectType",
    "TransitionPreset",
    "FilterPreset",
    "TextStylePreset",
    "ColorPalette",
]
