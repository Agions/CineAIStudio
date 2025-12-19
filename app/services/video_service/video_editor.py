#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频编辑核心服务
实现视频剪辑、拼接、特效添加等功能
"""

import os
import sys
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field

import numpy as np
import cv2
# MoviePy 2.x的导入 - 作为可选依赖
moviepy_available = False
VideoFileClip = None
AudioFileClip = None
concatenate_videoclips = None
CompositeVideoClip = None
concatenate_audioclips = None
vfx = None

try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.audio.AudioClip import concatenate_audioclips
    from moviepy.video.fx import all as vfx
    moviepy_available = True
except ImportError as e:
    pass
from PIL import Image


class EffectProcessor:
    """特效处理器，负责应用各种视频特效"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def apply_effect(self, clip, effect: Dict[str, Any]) -> Any:
        """应用单个特效到视频片段"""
        try:
            effect_name = effect.get('name')
            if effect_name == 'grayscale':
                return clip.fx(vfx.blackwhite)
            elif effect_name == 'blur':
                blur_amount = effect.get('amount', 1.0)
                return clip.fx(vfx.blur, blur_amount)
            elif effect_name == 'brightness':
                brightness_factor = effect.get('factor', 1.0)
                return clip.fx(vfx.colorx, brightness_factor)
            elif effect_name == 'crop':
                x = effect.get('x', 0)
                y = effect.get('y', 0)
                width = effect.get('width', clip.w)
                height = effect.get('height', clip.h)
                return clip.crop(x=x, y=y, width=width, height=height)
            elif effect_name == 'rotate':
                rotation_angle = effect.get('angle', 0.0)
                return clip.rotate(rotation_angle)
            elif effect_name == 'flip':
                flip_direction = effect.get('direction', 'horizontal')
                if flip_direction == 'horizontal':
                    return clip.fx(vfx.mirror_x)
                elif flip_direction == 'vertical':
                    return clip.fx(vfx.mirror_y)
            elif effect_name == 'speed':
                speed_factor = effect.get('factor', 1.0)
                return clip.fx(vfx.speedx, speed_factor)
            elif effect_name == 'volume':
                volume_factor = effect.get('factor', 1.0)
                if hasattr(clip, 'audio') and clip.audio:
                    return clip.volumex(volume_factor)
            elif effect_name == 'contrast':
                contrast_factor = effect.get('factor', 1.0)
                return clip.fx(vfx.lum_contrast, contrast=contrast_factor*100)
            elif effect_name == 'saturation':
                saturation_factor = effect.get('factor', 1.0)
                return clip.fx(vfx.colorx, saturation_factor)
            elif effect_name == 'zoom':
                zoom_amount = effect.get('amount', 1.0)
                return clip.fx(vfx.resize, zoom_amount)
            
            # 如果没有匹配的特效，返回原片段
            return clip
        except Exception as e:
            if self.logger:
                self.logger.error(f"应用特效 {effect.get('name')} 失败: {e}")
            return clip
    
    def apply_effects(self, clip, effects: List[Dict[str, Any]]) -> Any:
        """应用多个特效到视频片段"""
        for effect in effects:
            clip = self.apply_effect(clip, effect)
        return clip


@dataclass
class MediaItem:
    """媒体项数据类"""
    id: str
    file_path: str
    media_type: str  # video, audio, image
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    audio_bitrate: str = "128k"
    video_bitrate: str = "8000k"
    codec: str = "libx264"


@dataclass
class Transition:
    """转场效果数据类"""
    id: str
    type: str  # fade, slide, dissolve, etc.
    duration: float = 1.0
    start_clip_id: str = ""
    end_clip_id: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoClip:
    """视频片段数据类"""
    id: str
    media_item: MediaItem
    start_time: float = 0.0
    end_time: float = 0.0
    x: int = 0
    y: int = 0
    scale: float = 1.0
    opacity: float = 1.0
    rotation: float = 0.0
    effects: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AudioClip:
    """音频片段数据类"""
    id: str
    media_item: MediaItem
    start_time: float = 0.0
    end_time: float = 0.0
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0


@dataclass
class Project:
    """项目数据类"""
    id: str
    name: str
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    video_clips: List[VideoClip] = field(default_factory=list)
    audio_clips: List[AudioClip] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)
    duration: float = 0.0
    # 帧缓存设置
    enable_frame_caching: bool = True
    frame_cache_size: int = 1000  # 缓存帧数
    preview_quality: str = "medium"  # low, medium, high
    use_gpu_acceleration: bool = True  # 是否使用GPU加速


class VideoEditorService:
    """视频编辑服务"""

    def __init__(self):
        """初始化视频编辑服务"""
        self.current_project: Optional[Project] = None
        self.logger = None
        self.effect_processor = None

    def set_logger(self, logger):
        """设置日志记录器"""
        self.logger = logger
        # 初始化特效处理器
        self.effect_processor = EffectProcessor(logger)

    def create_project(self, project_id: str, name: str, width: int = 1920, height: int = 1080, fps: float = 30.0,
                       enable_frame_caching: bool = True, frame_cache_size: int = 1000, preview_quality: str = "medium",
                       use_gpu_acceleration: bool = True) -> Project:
        """创建新项目"""
        self.current_project = Project(
            id=project_id,
            name=name,
            width=width,
            height=height,
            fps=fps,
            enable_frame_caching=enable_frame_caching,
            frame_cache_size=frame_cache_size,
            preview_quality=preview_quality,
            use_gpu_acceleration=use_gpu_acceleration
        )
        if self.logger:
            self.logger.info(f"创建项目: {name} (ID: {project_id})")
            self.logger.info(f"项目设置: 分辨率 {width}x{height}, 帧率 {fps}, 预览质量 {preview_quality}")
        return self.current_project

    def open_project(self, project_path: str) -> Optional[Project]:
        """打开现有项目"""
        # TODO: 实现项目打开逻辑
        if self.logger:
            self.logger.info(f"打开项目: {project_path}")
        return None

    def save_project(self, project: Project, project_path: str) -> bool:
        """保存项目"""
        # TODO: 实现项目保存逻辑
        if self.logger:
            self.logger.info(f"保存项目: {project.name} 到 {project_path}")
        return True

    def import_media(self, file_path: str) -> Optional[MediaItem]:
        """导入媒体文件"""
        try:
            if not os.path.exists(file_path):
                if self.logger:
                    self.logger.error(f"文件不存在: {file_path}")
                return None

            # 获取文件扩展名
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            # 确定媒体类型
            if ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
                media_type = 'video'
                media_item = self._import_video(file_path)
            elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
                media_type = 'audio'
                media_item = self._import_audio(file_path)
            elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
                media_type = 'image'
                media_item = self._import_image(file_path)
            else:
                if self.logger:
                    self.logger.error(f"不支持的文件类型: {ext}")
                return None

            if self.logger:
                self.logger.info(f"导入媒体文件成功: {file_path} ({media_type})")
            return media_item

        except Exception as e:
            if self.logger:
                self.logger.error(f"导入媒体文件失败: {file_path}, 错误: {e}")
            return None

    def _import_video(self, file_path: str) -> MediaItem:
        """导入视频文件"""
        try:
            # 使用OpenCV获取视频信息
            cap = cv2.VideoCapture(file_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps if fps > 0 else 0
            cap.release()

            return MediaItem(
                id=f"video_{os.path.basename(file_path).replace('.', '_')}",
                file_path=file_path,
                media_type='video',
                duration=duration,
                width=width,
                height=height,
                fps=fps
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"导入视频文件失败: {file_path}, 错误: {e}")
            # 使用默认值
            return MediaItem(
                id=f"video_{os.path.basename(file_path).replace('.', '_')}",
                file_path=file_path,
                media_type='video',
                duration=0.0,
                width=1920,
                height=1080,
                fps=30.0
            )

    def _import_audio(self, file_path: str) -> MediaItem:
        """导入音频文件"""
        try:
            # 使用moviepy获取音频信息
            audio_clip = AudioFileClip(file_path)
            duration = audio_clip.duration
            audio_clip.close()

            return MediaItem(
                id=f"audio_{os.path.basename(file_path).replace('.', '_')}",
                file_path=file_path,
                media_type='audio',
                duration=duration
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"导入音频文件失败: {file_path}, 错误: {e}")
            # 使用默认值
            return MediaItem(
                id=f"audio_{os.path.basename(file_path).replace('.', '_')}",
                file_path=file_path,
                media_type='audio',
                duration=0.0
            )

    def _import_image(self, file_path: str) -> MediaItem:
        """导入图片文件"""
        try:
            # 使用PIL获取图片信息
            with Image.open(file_path) as img:
                width, height = img.size

            return MediaItem(
                id=f"image_{os.path.basename(file_path).replace('.', '_')}",
                file_path=file_path,
                media_type='image',
                duration=5.0,  # 图片默认持续时间5秒
                width=width,
                height=height
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"导入图片文件失败: {file_path}, 错误: {e}")
            # 使用默认值
            return MediaItem(
                id=f"image_{os.path.basename(file_path).replace('.', '_')}",
                file_path=file_path,
                media_type='image',
                duration=5.0,
                width=1920,
                height=1080
            )

    def add_video_clip(self, media_item: MediaItem, start_time: float = 0.0, end_time: float = 0.0) -> VideoClip:
        """添加视频片段到项目"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        # 如果结束时间未指定，使用媒体项的完整时长
        if end_time <= 0:
            end_time = media_item.duration

        clip = VideoClip(
            id=f"clip_{len(self.current_project.video_clips) + 1}",
            media_item=media_item,
            start_time=start_time,
            end_time=end_time
        )

        self.current_project.video_clips.append(clip)
        # 更新项目时长
        self._update_project_duration()

        if self.logger:
            self.logger.info(f"添加视频片段: {media_item.file_path} 到项目")
        return clip

    def add_audio_clip(self, media_item: MediaItem, start_time: float = 0.0, end_time: float = 0.0) -> AudioClip:
        """添加音频片段到项目"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        # 如果结束时间未指定，使用媒体项的完整时长
        if end_time <= 0:
            end_time = media_item.duration

        clip = AudioClip(
            id=f"audio_clip_{len(self.current_project.audio_clips) + 1}",
            media_item=media_item,
            start_time=start_time,
            end_time=end_time
        )

        self.current_project.audio_clips.append(clip)
        # 更新项目时长
        self._update_project_duration()

        if self.logger:
            self.logger.info(f"添加音频片段: {media_item.file_path} 到项目")
        return clip

    def remove_video_clip(self, clip_id: str) -> bool:
        """从项目中移除视频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for i, clip in enumerate(self.current_project.video_clips):
            if clip.id == clip_id:
                del self.current_project.video_clips[i]
                self._update_project_duration()
                if self.logger:
                    self.logger.info(f"移除视频片段: {clip_id}")
                return True
        return False

    def remove_audio_clip(self, clip_id: str) -> bool:
        """从项目中移除音频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for i, clip in enumerate(self.current_project.audio_clips):
            if clip.id == clip_id:
                del self.current_project.audio_clips[i]
                self._update_project_duration()
                if self.logger:
                    self.logger.info(f"移除音频片段: {clip_id}")
                return True
        return False

    def split_audio_clip(self, clip_id: str, split_time: float) -> Tuple[Optional[AudioClip], Optional[AudioClip]]:
        """分割音频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for i, clip in enumerate(self.current_project.audio_clips):
            if clip.id == clip_id:
                # 检查分割时间是否有效
                if split_time <= clip.start_time or split_time >= clip.end_time:
                    if self.logger:
                        self.logger.error(f"分割时间无效: {split_time}，必须在片段范围内")
                    return (None, None)

                # 创建第一个片段（从开始到分割点）
                first_clip = AudioClip(
                    id=f"audio_clip_{len(self.current_project.audio_clips) + 1}",
                    media_item=clip.media_item,
                    start_time=clip.start_time,
                    end_time=split_time,
                    volume=clip.volume,
                    fade_in=clip.fade_in,
                    fade_out=0.0  # 重置淡出效果
                )

                # 创建第二个片段（从分割点到结束）
                second_clip = AudioClip(
                    id=f"audio_clip_{len(self.current_project.audio_clips) + 2}",
                    media_item=clip.media_item,
                    start_time=split_time,
                    end_time=clip.end_time,
                    volume=clip.volume,
                    fade_in=0.0,  # 重置淡入效果
                    fade_out=clip.fade_out
                )

                # 替换原片段为两个新片段
                self.current_project.audio_clips.pop(i)
                self.current_project.audio_clips.insert(i, first_clip)
                self.current_project.audio_clips.insert(i + 1, second_clip)

                # 更新项目时长
                self._update_project_duration()

                if self.logger:
                    self.logger.info(f"分割音频片段: {clip_id} 在时间 {split_time}秒")
                return (first_clip, second_clip)
        return (None, None)

    def copy_audio_clip(self, clip_id: str) -> Optional[AudioClip]:
        """复制音频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for clip in self.current_project.audio_clips:
            if clip.id == clip_id:
                # 创建新的剪辑ID
                new_clip_id = f"audio_clip_{len(self.current_project.audio_clips) + 1}"
                
                # 复制片段
                copied_clip = AudioClip(
                    id=new_clip_id,
                    media_item=clip.media_item,
                    start_time=clip.start_time,
                    end_time=clip.end_time,
                    volume=clip.volume,
                    fade_in=clip.fade_in,
                    fade_out=clip.fade_out
                )

                if self.logger:
                    self.logger.info(f"复制音频片段: {clip_id} 为 {new_clip_id}")
                return copied_clip
        return None

    def paste_audio_clip(self, copied_clip: AudioClip, insert_index: int = -1) -> Optional[AudioClip]:
        """粘贴音频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        # 更新片段ID
        new_clip_id = f"audio_clip_{len(self.current_project.audio_clips) + 1}"
        copied_clip.id = new_clip_id

        # 插入到指定位置，默认为末尾
        if insert_index < 0 or insert_index > len(self.current_project.audio_clips):
            self.current_project.audio_clips.append(copied_clip)
        else:
            self.current_project.audio_clips.insert(insert_index, copied_clip)

        # 更新项目时长
        self._update_project_duration()

        if self.logger:
            self.logger.info(f"粘贴音频片段: {new_clip_id} 到位置 {insert_index}")
        return copied_clip

    def duplicate_audio_clip(self, clip_id: str) -> Optional[AudioClip]:
        """复制并粘贴音频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        # 复制片段
        copied_clip = self.copy_audio_clip(clip_id)
        if not copied_clip:
            return None

        # 粘贴片段到末尾
        return self.paste_audio_clip(copied_clip)

    def adjust_audio_volume(self, clip_id: str, volume: float) -> Optional[AudioClip]:
        """调整音频音量"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for clip in self.current_project.audio_clips:
            if clip.id == clip_id:
                clip.volume = volume
                if self.logger:
                    self.logger.info(f"调整音频音量: {clip_id}，音量: {volume}")
                return clip
        return None

    def set_audio_fade(self, clip_id: str, fade_in: float = 0.0, fade_out: float = 0.0) -> Optional[AudioClip]:
        """设置音频淡入淡出效果"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for clip in self.current_project.audio_clips:
            if clip.id == clip_id:
                clip.fade_in = fade_in
                clip.fade_out = fade_out
                if self.logger:
                    self.logger.info(f"设置音频淡入淡出: {clip_id}，淡入: {fade_in}秒，淡出: {fade_out}秒")
                return clip
        return None

    def edit_video_clip(self, clip_id: str, **kwargs) -> Optional[VideoClip]:
        """编辑视频片段属性"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for clip in self.current_project.video_clips:
            if clip.id == clip_id:
                # 更新片段属性
                if 'start_time' in kwargs:
                    clip.start_time = kwargs['start_time']
                if 'end_time' in kwargs:
                    clip.end_time = kwargs['end_time']
                if 'x' in kwargs:
                    clip.x = kwargs['x']
                if 'y' in kwargs:
                    clip.y = kwargs['y']
                if 'scale' in kwargs:
                    clip.scale = kwargs['scale']
                if 'opacity' in kwargs:
                    clip.opacity = kwargs['opacity']
                if 'rotation' in kwargs:
                    clip.rotation = kwargs['rotation']
                if 'effects' in kwargs:
                    clip.effects = kwargs['effects']

                # 更新项目时长
                self._update_project_duration()
                if self.logger:
                    self.logger.info(f"编辑视频片段: {clip_id}")
                return clip
        return None

    def edit_audio_clip(self, clip_id: str, **kwargs) -> Optional[AudioClip]:
        """编辑音频片段属性"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for clip in self.current_project.audio_clips:
            if clip.id == clip_id:
                # 更新片段属性
                if 'start_time' in kwargs:
                    clip.start_time = kwargs['start_time']
                if 'end_time' in kwargs:
                    clip.end_time = kwargs['end_time']
                if 'volume' in kwargs:
                    clip.volume = kwargs['volume']
                if 'fade_in' in kwargs:
                    clip.fade_in = kwargs['fade_in']
                if 'fade_out' in kwargs:
                    clip.fade_out = kwargs['fade_out']

                # 更新项目时长
                self._update_project_duration()
                if self.logger:
                    self.logger.info(f"编辑音频片段: {clip_id}")
                return clip
        return None

    def add_effect_to_clip(self, clip_id: str, effect: Dict[str, Any]) -> bool:
        """向视频片段添加特效"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for clip in self.current_project.video_clips:
            if clip.id == clip_id:
                clip.effects.append(effect)
                if self.logger:
                    self.logger.info(f"向片段 {clip_id} 添加特效: {effect.get('name', 'Unknown')}")
                return True
        return False

    def remove_effect_from_clip(self, clip_id: str, effect_index: int) -> bool:
        """从视频片段移除特效"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for clip in self.current_project.video_clips:
            if clip.id == clip_id:
                if 0 <= effect_index < len(clip.effects):
                    del clip.effects[effect_index]
                    if self.logger:
                        self.logger.info(f"从片段 {clip_id} 移除特效, 索引: {effect_index}")
                    return True
        return False

    def update_effect(self, clip_id: str, effect_index: int, effect_params: Dict[str, Any]) -> bool:
        """更新视频片段的特效参数
        
        Args:
            clip_id: 视频片段ID
            effect_index: 特效索引
            effect_params: 要更新的特效参数
            
        Returns:
            如果更新成功返回True，否则返回False
        """
        if not self.current_project:
            raise ValueError("没有当前项目")
        
        for clip in self.current_project.video_clips:
            if clip.id == clip_id:
                if 0 <= effect_index < len(clip.effects):
                    # 更新特效参数
                    clip.effects[effect_index].update(effect_params)
                    if self.logger:
                        self.logger.info(f"更新片段 {clip_id} 的特效, 索引: {effect_index}")
                    return True
        return False

    def get_effect(self, clip_id: str, effect_index: int) -> Optional[Dict[str, Any]]:
        """获取视频片段的特效
        
        Args:
            clip_id: 视频片段ID
            effect_index: 特效索引
            
        Returns:
            特效参数字典，如果不存在则返回None
        """
        if not self.current_project:
            raise ValueError("没有当前项目")
        
        for clip in self.current_project.video_clips:
            if clip.id == clip_id:
                if 0 <= effect_index < len(clip.effects):
                    return clip.effects[effect_index]
        return None

    def get_all_effects(self, clip_id: str) -> List[Dict[str, Any]]:
        """获取视频片段的所有特效
        
        Args:
            clip_id: 视频片段ID
            
        Returns:
            特效列表
        """
        if not self.current_project:
            raise ValueError("没有当前项目")
        
        for clip in self.current_project.video_clips:
            if clip.id == clip_id:
                return clip.effects.copy()
        return []

    def clear_effects(self, clip_id: str) -> bool:
        """清除视频片段的所有特效
        
        Args:
            clip_id: 视频片段ID
            
        Returns:
            如果清除成功返回True，否则返回False
        """
        if not self.current_project:
            raise ValueError("没有当前项目")
        
        for clip in self.current_project.video_clips:
            if clip.id == clip_id:
                clip.effects.clear()
                if self.logger:
                    self.logger.info(f"清除片段 {clip_id} 的所有特效")
                return True
        return False

    def split_video_clip(self, clip_id: str, split_time: float) -> Tuple[Optional[VideoClip], Optional[VideoClip]]:
        """分割视频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for i, clip in enumerate(self.current_project.video_clips):
            if clip.id == clip_id:
                # 检查分割时间是否有效
                if split_time <= clip.start_time or split_time >= clip.end_time:
                    if self.logger:
                        self.logger.error(f"分割时间无效: {split_time}，必须在片段范围内")
                    return (None, None)

                # 创建第一个片段（从开始到分割点）
                first_clip = VideoClip(
                    id=f"clip_{len(self.current_project.video_clips) + 1}",
                    media_item=clip.media_item,
                    start_time=clip.start_time,
                    end_time=split_time,
                    x=clip.x,
                    y=clip.y,
                    scale=clip.scale,
                    opacity=clip.opacity,
                    rotation=clip.rotation,
                    effects=clip.effects.copy()
                )

                # 创建第二个片段（从分割点到结束）
                second_clip = VideoClip(
                    id=f"clip_{len(self.current_project.video_clips) + 2}",
                    media_item=clip.media_item,
                    start_time=split_time,
                    end_time=clip.end_time,
                    x=clip.x,
                    y=clip.y,
                    scale=clip.scale,
                    opacity=clip.opacity,
                    rotation=clip.rotation,
                    effects=clip.effects.copy()
                )

                # 替换原片段为两个新片段
                self.current_project.video_clips.pop(i)
                self.current_project.video_clips.insert(i, first_clip)
                self.current_project.video_clips.insert(i + 1, second_clip)

                # 更新项目时长
                self._update_project_duration()

                if self.logger:
                    self.logger.info(f"分割视频片段: {clip_id} 在时间 {split_time}秒")
                return (first_clip, second_clip)
        return (None, None)

    def crop_video_clip(self, clip_id: str, x: int, y: int, width: int, height: int) -> Optional[VideoClip]:
        """裁剪视频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for clip in self.current_project.video_clips:
            if clip.id == clip_id:
                # 添加裁剪特效
                crop_effect = {
                    'name': 'crop',
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height
                }
                
                # 检查是否已有裁剪特效，如果有则替换
                for i, effect in enumerate(clip.effects):
                    if effect.get('name') == 'crop':
                        clip.effects[i] = crop_effect
                        break
                else:
                    clip.effects.append(crop_effect)

                if self.logger:
                    self.logger.info(f"裁剪视频片段: {clip_id}，区域: ({x}, {y}, {width}, {height})")
                return clip
        return None

    def copy_video_clip(self, clip_id: str) -> Optional[VideoClip]:
        """复制视频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for clip in self.current_project.video_clips:
            if clip.id == clip_id:
                # 创建新的剪辑ID
                new_clip_id = f"clip_{len(self.current_project.video_clips) + 1}"
                
                # 复制片段
                copied_clip = VideoClip(
                    id=new_clip_id,
                    media_item=clip.media_item,
                    start_time=clip.start_time,
                    end_time=clip.end_time,
                    x=clip.x + 10,  # 稍微偏移一点，方便区分
                    y=clip.y + 10,
                    scale=clip.scale,
                    opacity=clip.opacity,
                    rotation=clip.rotation,
                    effects=clip.effects.copy()
                )

                if self.logger:
                    self.logger.info(f"复制视频片段: {clip_id} 为 {new_clip_id}")
                return copied_clip
        return None

    def paste_video_clip(self, copied_clip: VideoClip, insert_index: int = -1) -> Optional[VideoClip]:
        """粘贴视频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        # 更新片段ID
        new_clip_id = f"clip_{len(self.current_project.video_clips) + 1}"
        copied_clip.id = new_clip_id

        # 插入到指定位置，默认为末尾
        if insert_index < 0 or insert_index > len(self.current_project.video_clips):
            self.current_project.video_clips.append(copied_clip)
        else:
            self.current_project.video_clips.insert(insert_index, copied_clip)

        # 更新项目时长
        self._update_project_duration()

        if self.logger:
            self.logger.info(f"粘贴视频片段: {new_clip_id} 到位置 {insert_index}")
        return copied_clip

    def reorder_video_clips(self, clip_ids: List[str]) -> bool:
        """重新排序视频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        # 检查所有片段ID是否存在
        existing_ids = {clip.id for clip in self.current_project.video_clips}
        for clip_id in clip_ids:
            if clip_id not in existing_ids:
                if self.logger:
                    self.logger.error(f"片段ID不存在: {clip_id}")
                return False

        # 创建新的片段列表
        new_video_clips = []
        for clip_id in clip_ids:
            for clip in self.current_project.video_clips:
                if clip.id == clip_id:
                    new_video_clips.append(clip)
                    break

        # 更新项目的片段列表
        self.current_project.video_clips = new_video_clips

        if self.logger:
            self.logger.info(f"重新排序视频片段: {clip_ids}")
        return True

    def duplicate_video_clip(self, clip_id: str) -> Optional[VideoClip]:
        """复制并粘贴视频片段"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        # 复制片段
        copied_clip = self.copy_video_clip(clip_id)
        if not copied_clip:
            return None

        # 粘贴片段到末尾
        return self.paste_video_clip(copied_clip)

    def merge_video_clips(self, clip_ids: List[str]) -> Optional[VideoClip]:
        """合并视频片段
        
        Args:
            clip_ids: 要合并的视频片段ID列表
            
        Returns:
            合并后的新视频片段，如果合并失败则返回None
        """
        if not self.current_project:
            raise ValueError("没有当前项目")
        
        if len(clip_ids) < 2:
            if self.logger:
                self.logger.error("至少需要2个片段才能合并")
            return None
        
        # 获取所有要合并的片段
        clips_to_merge = []
        for clip_id in clip_ids:
            clip_found = False
            for clip in self.current_project.video_clips:
                if clip.id == clip_id:
                    clips_to_merge.append(clip)
                    clip_found = True
                    break
            if not clip_found:
                if self.logger:
                    self.logger.error(f"片段ID不存在: {clip_id}")
                return None
        
        # 检查所有片段是否属于同一个媒体文件
        media_item = clips_to_merge[0].media_item
        for clip in clips_to_merge[1:]:
            if clip.media_item.id != media_item.id:
                if self.logger:
                    self.logger.error("只能合并来自同一媒体文件的片段")
                return None
        
        # 按时间顺序排序片段
        clips_to_merge.sort(key=lambda x: x.start_time)
        
        # 检查片段是否连续（可选）
        for i in range(1, len(clips_to_merge)):
            prev_clip = clips_to_merge[i-1]
            curr_clip = clips_to_merge[i]
            if prev_clip.end_time != curr_clip.start_time:
                if self.logger:
                    self.logger.warning(f"片段 {prev_clip.id} 和 {curr_clip.id} 不连续，将创建一个包含间隙的合并片段")
        
        # 创建合并后的新片段
        new_clip = VideoClip(
            id=f"clip_{len(self.current_project.video_clips) + 1}",
            media_item=media_item,
            start_time=clips_to_merge[0].start_time,
            end_time=clips_to_merge[-1].end_time,
            x=clips_to_merge[0].x,
            y=clips_to_merge[0].y,
            scale=clips_to_merge[0].scale,
            opacity=clips_to_merge[0].opacity,
            rotation=clips_to_merge[0].rotation,
            effects=clips_to_merge[0].effects.copy()
        )
        
        # 添加新片段到项目
        self.current_project.video_clips.append(new_clip)
        
        # 更新项目时长
        self._update_project_duration()
        
        if self.logger:
            self.logger.info(f"合并视频片段成功: {clip_ids} -> {new_clip.id}")
        
        return new_clip

    def concatenate_video_clips(self, clip_ids: List[str]) -> Optional[VideoClip]:
        """拼接视频片段（与merge_video_clips功能相同，为了兼容不同命名习惯）
        
        Args:
            clip_ids: 要拼接的视频片段ID列表
            
        Returns:
            拼接后的新视频片段，如果拼接失败则返回None
        """
        return self.merge_video_clips(clip_ids)

    def add_transition(self, start_clip_id: str, end_clip_id: str, transition_type: str, duration: float = 1.0, parameters: Dict[str, Any] = None) -> Optional[Transition]:
        """添加转场效果"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        # 检查片段是否存在
        start_clip = None
        end_clip = None
        for clip in self.current_project.video_clips:
            if clip.id == start_clip_id:
                start_clip = clip
            if clip.id == end_clip_id:
                end_clip = clip
            if start_clip and end_clip:
                break

        if not start_clip or not end_clip:
            if self.logger:
                self.logger.error(f"片段不存在: start_clip_id={start_clip_id}, end_clip_id={end_clip_id}")
            return None

        # 创建转场效果
        transition = Transition(
            id=f"transition_{len(self.current_project.transitions) + 1}",
            type=transition_type,
            duration=duration,
            start_clip_id=start_clip_id,
            end_clip_id=end_clip_id,
            parameters=parameters or {}
        )

        self.current_project.transitions.append(transition)
        if self.logger:
            self.logger.info(f"添加转场效果: {transition_type} 从片段 {start_clip_id} 到 {end_clip_id}")
        return transition

    def edit_transition(self, transition_id: str, **kwargs) -> Optional[Transition]:
        """编辑转场效果"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for transition in self.current_project.transitions:
            if transition.id == transition_id:
                # 更新转场属性
                if 'type' in kwargs:
                    transition.type = kwargs['type']
                if 'duration' in kwargs:
                    transition.duration = kwargs['duration']
                if 'start_clip_id' in kwargs:
                    transition.start_clip_id = kwargs['start_clip_id']
                if 'end_clip_id' in kwargs:
                    transition.end_clip_id = kwargs['end_clip_id']
                if 'parameters' in kwargs:
                    transition.parameters = kwargs['parameters']

                if self.logger:
                    self.logger.info(f"编辑转场效果: {transition_id}")
                return transition
        return None

    def remove_transition(self, transition_id: str) -> bool:
        """删除转场效果"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for i, transition in enumerate(self.current_project.transitions):
            if transition.id == transition_id:
                del self.current_project.transitions[i]
                if self.logger:
                    self.logger.info(f"删除转场效果: {transition_id}")
                return True
        return False

    def get_transition(self, transition_id: str) -> Optional[Transition]:
        """获取转场效果"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        for transition in self.current_project.transitions:
            if transition.id == transition_id:
                return transition
        return None

    def get_transitions_between_clips(self, start_clip_id: str, end_clip_id: str) -> List[Transition]:
        """获取两个片段之间的转场效果"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        transitions = []
        for transition in self.current_project.transitions:
            if transition.start_clip_id == start_clip_id and transition.end_clip_id == end_clip_id:
                transitions.append(transition)
        return transitions

    def clear_transitions(self) -> None:
        """清除所有转场效果"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        self.current_project.transitions.clear()
        if self.logger:
            self.logger.info("清除所有转场效果")

    def render_video(self, output_path: str, quality: str = "medium") -> bool:
        """渲染视频"""
        if not self.current_project:
            raise ValueError("没有当前项目")

        try:
            # 检查moviepy是否可用
            if not moviepy_available:
                if self.logger:
                    self.logger.error("MoviePy不可用，无法渲染视频")
                return False

            if self.logger:
                self.logger.info(f"开始渲染视频: {output_path}, 质量: {quality}")

            # 使用moviepy进行视频渲染
            # 1. 加载所有视频片段
            video_clips = []
            for video_clip in self.current_project.video_clips:
                # 加载视频文件
                clip = VideoFileClip(video_clip.media_item.file_path)
                
                # 截取片段
                clip = clip.subclip(video_clip.start_time, video_clip.end_time)
                
                # 应用变换
                if video_clip.scale != 1.0:
                    clip = clip.resize(video_clip.scale)
                
                if video_clip.opacity != 1.0:
                    clip = clip.set_opacity(video_clip.opacity)
                
                if video_clip.rotation != 0.0:
                    clip = clip.rotate(video_clip.rotation)
                
                # 移动位置
                if video_clip.x != 0 or video_clip.y != 0:
                    clip = clip.set_position((video_clip.x, video_clip.y))
                
                # 应用特效
                if self.effect_processor:
                    clip = self.effect_processor.apply_effects(clip, video_clip.effects)
                else:
                    # 后备方案：如果特效处理器未初始化，手动应用特效
                    for effect in video_clip.effects:
                        effect_name = effect.get('name')
                        if effect_name == 'grayscale':
                            clip = clip.fx(vfx.blackwhite)
                        elif effect_name == 'blur':
                            blur_amount = effect.get('amount', 1.0)
                            clip = clip.fx(vfx.blur, blur_amount)
                        elif effect_name == 'brightness':
                            brightness_factor = effect.get('factor', 1.0)
                            clip = clip.fx(vfx.colorx, brightness_factor)
                        elif effect_name == 'crop':
                            x = effect.get('x', 0)
                            y = effect.get('y', 0)
                            width = effect.get('width', clip.w)
                            height = effect.get('height', clip.h)
                            clip = clip.crop(x=x, y=y, width=width, height=height)
                        elif effect_name == 'rotate':
                            rotation_angle = effect.get('angle', 0.0)
                            clip = clip.rotate(rotation_angle)
                        elif effect_name == 'flip':
                            flip_direction = effect.get('direction', 'horizontal')
                            if flip_direction == 'horizontal':
                                clip = clip.fx(vfx.mirror_x)
                            elif flip_direction == 'vertical':
                                clip = clip.fx(vfx.mirror_y)
                        elif effect_name == 'speed':
                            speed_factor = effect.get('factor', 1.0)
                            clip = clip.fx(vfx.speedx, speed_factor)
                        elif effect_name == 'volume':
                            volume_factor = effect.get('factor', 1.0)
                            if clip.audio:
                                clip = clip.volumex(volume_factor)
                        elif effect_name == 'contrast':
                            contrast_factor = effect.get('factor', 1.0)
                            clip = clip.fx(vfx.lum_contrast, contrast=contrast_factor*100)
                        elif effect_name == 'saturation':
                            saturation_factor = effect.get('factor', 1.0)
                            clip = clip.fx(vfx.colorx, saturation_factor)
                        elif effect_name == 'zoom':
                            zoom_amount = effect.get('amount', 1.0)
                            clip = clip.fx(vfx.resize, zoom_amount)
                
                video_clips.append(clip)
            
            # 2. 合并视频片段
            if video_clips:
                # 如果只有一个片段，直接使用
                final_video = video_clips[0]
            else:
                if self.logger:
                    self.logger.error("没有视频片段可渲染")
                return False
            
            # 3. 合并音频片段
            audio_clips = []
            for audio_clip in self.current_project.audio_clips:
                # 加载音频文件
                clip = AudioFileClip(audio_clip.media_item.file_path)
                
                # 截取片段
                clip = clip.subclip(audio_clip.start_time, audio_clip.end_time)
                
                # 应用音量调整
                clip = clip.volumex(audio_clip.volume)
                
                # 应用淡入淡出
                if audio_clip.fade_in > 0:
                    clip = clip.fadein(audio_clip.fade_in)
                if audio_clip.fade_out > 0:
                    clip = clip.fadeout(audio_clip.fade_out)
                
                # 设置音频开始时间
                clip = clip.set_start(audio_clip.start_time)
                
                audio_clips.append(clip)
            
            # 4. 组合视频和音频
            if audio_clips:
                # 设置视频音频（简单方式）
                final_audio = audio_clips[0]
                final_video = final_video.set_audio(final_audio)
            
            # 5. 根据质量设置参数
            quality_settings = {
                "low": {
                    "fps": 24,
                    "bitrate": "2000k",
                    "preset": "ultrafast"
                },
                "medium": {
                    "fps": 30,
                    "bitrate": "5000k",
                    "preset": "fast"
                },
                "high": {
                    "fps": 60,
                    "bitrate": "8000k",
                    "preset": "medium"
                }
            }
            
            # 获取质量设置
            settings = quality_settings.get(quality, quality_settings["medium"])
            settings["fps"] = self.current_project.fps
            
            # 获取系统CPU核心数
            import multiprocessing
            threads = multiprocessing.cpu_count()
            
            # 6. 分片渲染优化：对于长视频，分割成多个小片段并行渲染
            import os
            from concurrent.futures import ThreadPoolExecutor
            
            final_duration = final_video.duration
            is_long_video = final_duration > 60  # 超过60秒的视频视为长视频
            use_tiling = getattr(self.current_project, 'use_gpu_acceleration', True) and is_long_video
            
            if use_tiling:
                # 计算分片数量，每20秒一个片段
                num_tiles = int(final_duration // 20) + 1
                self.logger.info(f"检测到长视频 ({final_duration:.1f}秒)，使用分片渲染，共{num_tiles}个片段")
                
                # 分割视频片段
                tile_clips = []
                for i in range(num_tiles):
                    start_time = i * 20
                    end_time = min((i + 1) * 20, final_duration)
                    
                    # 截取片段
                    tile_clip = final_video.subclip(start_time, end_time)
                    tile_clips.append(tile_clip)
                
                # 使用并行处理渲染每个片段
                rendered_tiles = []
                
                def render_tile(clip, index):
                    """渲染单个视频片段"""
                    try:
                        tile_output = f"{output_path}.tile{index}.mp4"
                        
                        # GPU加速支持
                        use_gpu = getattr(self.current_project, 'use_gpu_acceleration', True)
                        gpu_codec = "h264_nvenc" if use_gpu else "libx264"
                        
                        clip.write_videofile(
                            tile_output,
                            fps=settings["fps"],
                            bitrate=settings["bitrate"],
                            preset=settings["preset"],
                            codec=gpu_codec,
                            audio_bitrate="128k",
                            threads=1,  # 每个片段使用1个线程
                            verbose=False,
                            logger=None
                        )
                        return tile_output
                    except Exception as e:
                        self.logger.error(f"渲染片段{index}失败: {e}")
                        return None
                
                # 使用线程池并行渲染
                with ThreadPoolExecutor(max_workers=min(threads, num_tiles)) as executor:
                    results = list(executor.map(render_tile, tile_clips, range(num_tiles)))
                
                # 收集成功渲染的片段
                rendered_tiles = [r for r in results if r]
                
                if len(rendered_tiles) == num_tiles:
                    # 所有片段渲染成功，合并成最终视频
                    self.logger.info("所有片段渲染成功，开始合并...")
                    
                    # 使用ffmpeg合并片段
                    import subprocess
                    
                    # 创建文件列表
                    file_list_path = f"{output_path}.filelist.txt"
                    with open(file_list_path, 'w') as f:
                        for tile in rendered_tiles:
                            f.write(f"file '{os.path.abspath(tile)}'\n")
                    
                    # 使用ffmpeg合并
                    merge_cmd = [
                        'ffmpeg',
                        '-f', 'concat',
                        '-safe', '0',
                        '-i', file_list_path,
                        '-c', 'copy',
                        '-y',
                        output_path
                    ]
                    
                    try:
                        result = subprocess.run(merge_cmd, capture_output=True, text=True, check=True)
                        self.logger.info("视频合并成功")
                        
                        # 清理临时文件
                        for tile in rendered_tiles:
                            if os.path.exists(tile):
                                os.remove(tile)
                        if os.path.exists(file_list_path):
                            os.remove(file_list_path)
                        
                        # 释放资源
                        final_video.close()
                        for clip in video_clips:
                            clip.close()
                        for clip in audio_clips:
                            clip.close()
                        for clip in tile_clips:
                            clip.close()
                        
                        return True
                    except Exception as e:
                        self.logger.error(f"合并视频失败: {e}")
                        # 清理临时文件
                        for tile in rendered_tiles:
                            if os.path.exists(tile):
                                os.remove(tile)
                        if os.path.exists(file_list_path):
                            os.remove(file_list_path)
                else:
                    self.logger.error(f"只有{len(rendered_tiles)}个片段渲染成功，总共需要{num_tiles}个片段")
                    # 清理临时文件
                    for tile in rendered_tiles:
                        if os.path.exists(tile):
                            os.remove(tile)
                    
                    # 继续使用原始渲染方式
                    use_tiling = False
            
            # 6. 导出视频
            import os
            # 根据系统CPU核心数动态调整线程数，最多使用8个线程
            threads = min(os.cpu_count() or 4, 8)
            
            # 检查是否支持GPU加速
            use_gpu = getattr(self.current_project, 'use_gpu_acceleration', True)
            
            # 检测GPU类型并选择合适的编码器
            def detect_gpu_type() -> str:
                """检测GPU类型"""
                import subprocess
                import platform
                
                gpu_type = "none"
                system = platform.system()
                
                try:
                    if system == "Windows":
                        # Windows系统使用wmic检测GPU
                        result = subprocess.run(["wmic", "path", "win32_VideoController", "get", "Name"], 
                                             capture_output=True, text=True, check=True)
                        gpu_name = result.stdout.upper()
                    elif system == "Darwin":
                        # macOS系统使用system_profiler检测GPU
                        result = subprocess.run(["system_profiler", "SPDisplaysDataType"], 
                                             capture_output=True, text=True, check=True)
                        gpu_name = result.stdout.upper()
                    else:
                        # Linux系统使用lspci检测GPU
                        result = subprocess.run(["lspci"], capture_output=True, text=True, check=True)
                        gpu_name = result.stdout.upper()
                    
                    if "NVIDIA" in gpu_name:
                        gpu_type = "nvidia"
                    elif "AMD" in gpu_name or "RADEON" in gpu_name:
                        gpu_type = "amd"
                    elif "INTEL" in gpu_name and "GRAPHICS" in gpu_name:
                        gpu_type = "intel"
                    elif "APPLE M" in gpu_name:
                        gpu_type = "apple_silicon"
                except:
                    pass
                
                return gpu_type
            
            gpu_type = detect_gpu_type() if use_gpu else "none"
            
            # 根据视频分辨率选择合适的编码预设
            video_resolution = getattr(self.current_project, 'width', 1920) * getattr(self.current_project, 'height', 1080)
            is_4k = video_resolution >= 3840 * 2160
            is_2k = video_resolution >= 2560 * 1440
            
            # 根据GPU类型和视频分辨率选择合适的编码器
            if use_gpu:
                if gpu_type == "nvidia":
                    # NVIDIA GPU使用NVENC编码器
                    gpu_codec = "h265_nvenc" if is_4k else "h264_nvenc"
                elif gpu_type == "amd":
                    # AMD GPU使用AMF编码器
                    gpu_codec = "hevc_amf" if is_4k else "h264_amf"
                elif gpu_type == "intel":
                    # Intel GPU使用QSV编码器
                    gpu_codec = "hevc_qsv" if is_4k else "h264_qsv"
                elif gpu_type == "apple_silicon":
                    # Apple Silicon使用VideoToolbox编码器
                    gpu_codec = "hevc_videotoolbox" if is_4k else "h264_videotoolbox"
                else:
                    # 未知GPU类型，使用CPU编码
                    gpu_codec = "libx265" if is_4k else "libx264"
            else:
                # CPU编码
                gpu_codec = "libx265" if is_4k else "libx264"
            
            write_kwargs = {
                'fps': settings["fps"],
                'bitrate': settings["bitrate"],
                'preset': settings["preset"],
                'codec': gpu_codec,
                'audio_bitrate': self.current_project.audio_clips[0].media_item.audio_bitrate if self.current_project.audio_clips else "128k",
                'threads': threads,
                'verbose': False,
                'logger': None
            }
            
            # 添加GPU加速参数
            gpu_codecs = ["h264_nvenc", "h265_nvenc", "h264_amf", "hevc_amf", "h264_qsv", "hevc_qsv", "h264_videotoolbox", "hevc_videotoolbox"]
            if use_gpu and gpu_codec in gpu_codecs:
                write_kwargs['threads'] = 1  # GPU编码时，使用较少的CPU线程
                write_kwargs['preset'] = "fast"  # GPU编码预设
            
            # 智能缓存管理：根据视频时长和分辨率动态调整缓存大小
            if hasattr(final_video, 'cache') and hasattr(self.current_project, 'frame_cache_size'):
                # 获取基础缓存大小
                base_cache_size = getattr(self.current_project, 'frame_cache_size', 1000)
                
                # 获取视频时长（秒）
                video_duration = final_video.duration
                
                # 根据视频分辨率计算基础系数
                if is_4k:
                    resolution_factor = 0.5  # 4K视频缓存减半
                    resolution_limit = 500   # 4K视频最大缓存帧数
                elif is_2k:
                    resolution_factor = 0.75  # 2K视频缓存减少25%
                    resolution_limit = 750    # 2K视频最大缓存帧数
                else:
                    resolution_factor = 1.0   # 1080p及以下视频使用完整缓存
                    resolution_limit = 1000   # 1080p视频最大缓存帧数
                
                # 根据视频时长计算时长系数（视频越长，缓存越小）
                if video_duration > 1200:  # 20分钟以上
                    duration_factor = 0.3
                elif video_duration > 600:   # 10-20分钟
                    duration_factor = 0.5
                elif video_duration > 300:   # 5-10分钟
                    duration_factor = 0.7
                elif video_duration > 120:   # 2-5分钟
                    duration_factor = 0.8
                else:                       # 2分钟以下
                    duration_factor = 1.0
                
                # 计算最终缓存大小
                cache_size = int(base_cache_size * resolution_factor * duration_factor)
                
                # 确保缓存大小在合理范围内
                cache_size = max(100, min(cache_size, resolution_limit))
                
                self.logger.info(f"智能缓存管理：设置缓存大小为 {cache_size} 帧")
                final_video.cache = cache_size
            
            self.logger.info(f"使用{gpu_codec}编码器，{'GPU加速' if use_gpu else 'CPU编码'}")
            final_video.write_videofile(
                output_path,
                **write_kwargs
            )
            
            # 7. 释放资源
            final_video.close()
            for clip in video_clips:
                clip.close()
            for clip in audio_clips:
                clip.close()

            if self.logger:
                self.logger.info(f"视频渲染完成: {output_path}")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"视频渲染失败: {output_path}, 错误: {e}")
            return False

    def _update_project_duration(self) -> None:
        """更新项目时长"""
        if not self.current_project:
            return

        max_duration = 0.0

        # 计算视频片段的最大结束时间
        for clip in self.current_project.video_clips:
            clip_duration = clip.start_time + (clip.end_time - clip.media_item.start_time)
            if clip_duration > max_duration:
                max_duration = clip_duration

        # 计算音频片段的最大结束时间
        for clip in self.current_project.audio_clips:
            clip_duration = clip.start_time + (clip.end_time - clip.media_item.start_time)
            if clip_duration > max_duration:
                max_duration = clip_duration

        self.current_project.duration = max_duration

    def get_project_duration(self) -> float:
        """获取项目时长"""
        if self.current_project:
            return self.current_project.duration
        return 0.0

    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        if not self.current_project:
            return None

        return {
            "id": self.current_project.id,
            "name": self.current_project.name,
            "width": self.current_project.width,
            "height": self.current_project.height,
            "fps": self.current_project.fps,
            "duration": self.current_project.duration,
            "video_clips_count": len(self.current_project.video_clips),
            "audio_clips_count": len(self.current_project.audio_clips)
        }

    def cleanup(self) -> None:
        """清理资源"""
        self.current_project = None
        if self.logger:
            self.logger.info("视频编辑服务已清理")
