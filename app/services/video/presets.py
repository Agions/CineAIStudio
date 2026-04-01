#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频制作预设配置
统一管理视频制作的预设配置
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class QualityPreset(Enum):
    """质量预设"""
    LOW = "low"           # 快速导出
    STANDARD = "standard" # 标准质量
    HIGH = "high"        # 高质量
    ULTRA = "ultra"      # 最高质量


class OutputFormat(Enum):
    """输出格式"""
    MP4 = "mp4"
    MOV = "mov"
    WEBM = "webm"
    MKV = "mkv"
    AVI = "avi"


class VideoCodec(Enum):
    """视频编码"""
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    AV1 = "av1"
    PRORES = "prores"


class AudioCodec(Enum):
    """音频编码"""
    AAC = "aac"
    MP3 = "mp3"
    OPUS = "opus"
    FLAC = "flac"
    PCM = "pcm"


@dataclass
class Resolution:
    """分辨率"""
    width: int
    height: int
    
    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height
    
    @property
    def name(self) -> str:
        if self.height >= 2160:
            return "4K"
        elif self.height >= 1440:
            return "2K"
        elif self.height >= 1080:
            return "1080P"
        elif self.height >= 720:
            return "720P"
        elif self.height >= 480:
            return "480P"
        else:
            return "SD"
    
    # 常用分辨率
    SD_480 = None
    HD_720 = None
    FHD_1080 = None
    QHD_1440 = None
    UHD_4K = None
    UHD_8K = None


# 初始化常用分辨率
Resolution.SD_480 = Resolution(854, 480)
Resolution.HD_720 = Resolution(1280, 720)
Resolution.FHD_1080 = Resolution(1920, 1080)
Resolution.QHD_1440 = Resolution(2560, 1440)
Resolution.UHD_4K = Resolution(3840, 2160)
Resolution.UHD_8K = Resolution(7680, 4320)


@dataclass
class EncodingConfig:
    """编码配置"""
    # 视频
    codec: VideoCodec = VideoCodec.H264
    bitrate: str = "8M"          # 如 "8M", "15M"
    fps: float = 30.0
    resolution: Resolution = field(default_factory=lambda: Resolution.FHD_1080)
    preset: str = "medium"       # x264 preset: ultrafast..veryslow
    profile: str = "high"        # H264 profile
    pixel_format: str = "yuv420p"
    
    # 音频
    audio_codec: AudioCodec = AudioCodec.AAC
    audio_bitrate: str = "192k"
    sample_rate: int = 48000
    channels: int = 2
    
    # 质量
    crf: int = 23                 # 质量控制 (0-51, 越低越好)
    quality: QualityPreset = QualityPreset.STANDARD
    
    # 高级
    two_pass: bool = False
    fast_start: bool = True      # MP4 FastStart
    hardware_accel: bool = False  # 硬件加速
    
    @classmethod
    def from_preset(cls, preset: QualityPreset) -> "EncodingConfig":
        """从预设创建配置"""
        configs = {
            QualityPreset.LOW: cls(
                codec=VideoCodec.H264,
                bitrate="2M",
                fps=24,
                resolution=Resolution.HD_720,
                crf=28,
                preset="fast",
            ),
            QualityPreset.STANDARD: cls(
                codec=VideoCodec.H264,
                bitrate="8M",
                fps=30,
                resolution=Resolution.FHD_1080,
                crf=23,
                preset="medium",
            ),
            QualityPreset.HIGH: cls(
                codec=VideoCodec.H265,
                bitrate="15M",
                fps=60,
                resolution=Resolution.FHD_1080,
                crf=20,
                preset="slow",
            ),
            QualityPreset.ULTRA: cls(
                codec=VideoCodec.H265,
                bitrate="25M",
                fps=60,
                resolution=Resolution.UHD_4K,
                crf=18,
                preset="slower",
                two_pass=True,
            ),
        }
        return configs.get(preset, cls())


@dataclass
class Preset:
    """平台预设"""
    name: str
    description: str
    resolution: Resolution
    fps: float
    bitrate: str
    max_duration: Optional[float] = None
    formats: List[OutputFormat] = field(default_factory=lambda: [OutputFormat.MP4])
    
    # 平台特定
    aspect_ratio: float = 16/9
    vertical: bool = False
    
    @classmethod
    def get_defaults(cls) -> Dict[str, "Preset"]:
        """获取默认平台预设"""
        return {
            "bilibili": cls(
                name="B站",
                description="B站投稿标准",
                resolution=Resolution.FHD_1080,
                fps=60,
                bitrate="8M",
                max_duration=3600,  # 1小时
            ),
            "youtube": cls(
                name="YouTube",
                description="YouTube上传标准",
                resolution=Resolution.UHD_4K,
                fps=60,
                bitrate="25M",
                max_duration=None,
            ),
            "twitter": cls(
                name="Twitter/X",
                description="Twitter视频",
                resolution=Resolution.FHD_1080,
                fps=30,
                bitrate="4M",
                max_duration=140,  # 2分20秒
            ),
            "tiktok": cls(
                name="TikTok",
                description="抖音/快手",
                resolution=Resolution(1080, 1920),  # 竖屏
                fps=30,
                bitrate="6M",
                max_duration=180,  # 3分钟
                vertical=True,
                aspect_ratio=9/16,
            ),
            "xiaohongshu": cls(
                name="小红书",
                description="小红书视频",
                resolution=Resolution(1080, 1920),
                fps=30,
                bitrate="6M",
                max_duration=300,
                vertical=True,
            ),
            "wechat": cls(
                name="微信",
                description="微信传输",
                resolution=Resolution.FHD_1080,
                fps=30,
                bitrate="2M",
                max_duration=600,
            ),
            "instagram": cls(
                name="Instagram",
                description="Instagram Reels",
                resolution=Resolution(1080, 1920),
                fps=30,
                bitrate="4M",
                max_duration=60,
                vertical=True,
            ),
            "weibo": cls(
                name="微博",
                description="微博视频",
                resolution=Resolution.FHD_1080,
                fps=30,
                bitrate="5M",
                max_duration=600,
            ),
        }


@dataclass
class CommentaryConfig:
    """解说视频配置"""
    # 主题
    topic: str = ""
    style: str = "explainer"  # explainer/review/storytelling/educational
    
    # AI 配置
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    
    # 语音配置
    voice: str = "alloy"
    voice_speed: float = 1.0
    voice_pitch: float = 1.0
    
    # 字幕配置
    caption_style: str = "viral"
    caption_size: int = 24
    caption_position: str = "bottom"  # top/bottom/center
    
    # 输出配置
    encoding: EncodingConfig = field(default_factory=EncodingConfig)
    output_format: OutputFormat = OutputFormat.MP4


@dataclass
class MashupConfig:
    """混剪视频配置"""
    # 主题
    theme: str = ""
    target_duration: float = 60.0  # 目标时长
    
    # 素材
    min_clip_duration: float = 3.0  # 最小片段时长
    max_clip_duration: float = 15.0  # 最大片段时长
    transition_duration: float = 0.5  # 转场时长
    
    # BPM
    bpm: float = 120.0
    beat_match: bool = True
    
    # AI 配置
    provider: str = "openai"
    model: str = "gpt-4o"
    
    # 语音
    voice: str = ""
    background_music: str = ""
    background_volume: float = 0.3
    
    # 输出
    encoding: EncodingConfig = field(default_factory=EncodingConfig)
    output_format: OutputFormat = OutputFormat.MP4


@dataclass
class MonologueConfig:
    """独白视频配置"""
    # 主题
    topic: str = ""
    emotion: str = "neutral"  # neutral/happy/sad/excited
    
    # 画面
    frame_analysis: bool = True
    frame_interval: float = 5.0  # 关键帧间隔
    
    # AI 配置
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.8
    
    # 语音
    voice: str = "shimmer"
    voice_speed: float = 0.95
    
    # 字幕
    caption_style: str = "cinematic"
    caption_font: str = "思源黑体"
    
    # 输出
    encoding: EncodingConfig = field(default_factory=EncodingConfig)
    output_format: OutputFormat = OutputFormat.MP4


# 预设工厂
class PresetFactory:
    """预设工厂"""
    
    @staticmethod
    def get_encoding(preset: QualityPreset) -> EncodingConfig:
        return EncodingConfig.from_preset(preset)
    
    @staticmethod
    def get_platform(name: str) -> Optional["Preset"]:
        return Preset.get_defaults().get(name)
    
    @staticmethod
    def get_all_platforms() -> Dict[str, "Preset"]:
        return Preset.get_defaults()
    
    @staticmethod
    def create_commentary_config(
        topic: str,
        style: str = "explainer",
        platform: str = "bilibili",
    ) -> CommentaryConfig:
        """创建解说配置"""
        platform_preset = PresetFactory.get_platform(platform)
        
        config = CommentaryConfig(
            topic=topic,
            style=style,
        )
        
        if platform_preset:
            config.encoding = EncodingConfig(
                fps=platform_preset.fps,
                resolution=platform_preset.resolution,
                bitrate=platform_preset.bitrate,
            )
        
        return config
    
    @staticmethod
    def create_mashup_config(
        theme: str,
        duration: float = 60.0,
        platform: str = "bilibili",
    ) -> MashupConfig:
        """创建混剪配置"""
        platform_preset = PresetFactory.get_platform(platform)
        
        config = MashupConfig(
            theme=theme,
            target_duration=duration,
        )
        
        if platform_preset:
            config.encoding = EncodingConfig(
                fps=platform_preset.fps,
                resolution=platform_preset.resolution,
                bitrate=platform_preset.bitrate,
            )
        
        return config
    
    @staticmethod
    def create_monologue_config(
        topic: str,
        emotion: str = "neutral",
        platform: str = "bilibili",
    ) -> MonologueConfig:
        """创建独白配置"""
        platform_preset = PresetFactory.get_platform(platform)
        
        config = MonologueConfig(
            topic=topic,
            emotion=emotion,
        )
        
        if platform_preset:
            config.encoding = EncodingConfig(
                fps=platform_preset.fps,
                resolution=platform_preset.resolution,
                bitrate=platform_preset.bitrate,
            )
        
        return config


__all__ = [
    "QualityPreset",
    "OutputFormat",
    "VideoCodec",
    "AudioCodec",
    "Resolution",
    "EncodingConfig",
    "Preset",
    "CommentaryConfig",
    "MashupConfig",
    "MonologueConfig",
    "PresetFactory",
]
