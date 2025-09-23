#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
剪映Draft文件生成器
专门用于生成符合剪映草稿格式的JSON文件
"""

import json
import uuid
import time
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging

from ..core.logger import Logger


@dataclass
class JianyingMaterial:
    """剪映素材"""
    id: str
    name: str
    type: str  # "video", "audio", "image", "text"
    path: str
    duration: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JianyingTrack:
    """剪映轨道"""
    id: str
    type: str  # "video", "audio", "text", "effect"
    materials: List[JianyingMaterial] = field(default_factory=list)
    enabled: bool = True
    locked: bool = False
    volume: float = 1.0
    effects: List[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class JianyingEffect:
    """剪映特效"""
    id: str
    name: str
    type: str
    start_time: float
    duration: float
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JianyingTextOverlay:
    """剪映文字叠加"""
    id: str
    text: str
    font: str = "Arial"
    size: int = 24
    color: str = "#FFFFFF"
    position: Tuple[float, float] = (0.5, 0.5)
    start_time: float = 0.0
    duration: float = 5.0
    effects: List[Dict[str, Any]] = field(default_factory=dict)


class JianyingDraftGenerator:
    """剪映Draft文件生成器"""

    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.version = "1.0"
        self.materials: List[JianyingMaterial] = []
        self.tracks: List[JianyingTrack] = []
        self.effects: List[JianyingEffect] = []
        self.text_overlays: List[JianyingTextOverlay] = []

    def add_video_material(self,
                          path: str,
                          name: str = None,
                          start_time: float = 0.0,
                          end_time: float = None) -> str:
        """添加视频素材"""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Video file not found: {path}")

            # 获取视频信息
            duration = self._get_video_duration(path)
            if end_time is None:
                end_time = duration

            material = JianyingMaterial(
                id=str(uuid.uuid4()),
                name=name or os.path.basename(path),
                type="video",
                path=path,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "width": self._get_video_width(path),
                    "height": self._get_video_height(path),
                    "fps": self._get_video_fps(path)
                }
            )

            self.materials.append(material)
            self.logger.info(f"Added video material: {material.name}")
            return material.id

        except Exception as e:
            self.logger.error(f"Failed to add video material: {e}")
            raise

    def add_audio_material(self,
                          path: str,
                          name: str = None,
                          start_time: float = 0.0,
                          end_time: float = None) -> str:
        """添加音频素材"""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Audio file not found: {path}")

            # 获取音频信息
            duration = self._get_audio_duration(path)
            if end_time is None:
                end_time = duration

            material = JianyingMaterial(
                id=str(uuid.uuid4()),
                name=name or os.path.basename(path),
                type="audio",
                path=path,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "sample_rate": self._get_audio_sample_rate(path),
                    "channels": self._get_audio_channels(path)
                }
            )

            self.materials.append(material)
            self.logger.info(f"Added audio material: {material.name}")
            return material.id

        except Exception as e:
            self.logger.error(f"Failed to add audio material: {e}")
            raise

    def add_image_material(self,
                          path: str,
                          name: str = None,
                          duration: float = 5.0) -> str:
        """添加图片素材"""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Image file not found: {path}")

            material = JianyingMaterial(
                id=str(uuid.uuid4()),
                name=name or os.path.basename(path),
                type="image",
                path=path,
                duration=duration,
                metadata={
                    "width": self._get_image_width(path),
                    "height": self._get_image_height(path)
                }
            )

            self.materials.append(material)
            self.logger.info(f"Added image material: {material.name}")
            return material.id

        except Exception as e:
            self.logger.error(f"Failed to add image material: {e}")
            raise

    def add_text_material(self,
                         text: str,
                         name: str = None,
                         duration: float = 5.0) -> str:
        """添加文字素材"""
        try:
            material = JianyingMaterial(
                id=str(uuid.uuid4()),
                name=name or f"Text: {text[:20]}...",
                type="text",
                path="",
                duration=duration,
                metadata={"text": text}
            )

            self.materials.append(material)
            self.logger.info(f"Added text material: {material.name}")
            return material.id

        except Exception as e:
            self.logger.error(f"Failed to add text material: {e}")
            raise

    def create_track(self, track_type: str) -> str:
        """创建轨道"""
        track = JianyingTrack(
            id=str(uuid.uuid4()),
            type=track_type
        )

        self.tracks.append(track)
        self.logger.info(f"Created track: {track.id} ({track_type})")
        return track.id

    def add_material_to_track(self,
                            track_id: str,
                            material_id: str,
                            start_time: float = 0.0) -> bool:
        """将素材添加到轨道"""
        try:
            # 查找轨道
            track = None
            for t in self.tracks:
                if t.id == track_id:
                    track = t
                    break

            if not track:
                raise ValueError(f"Track not found: {track_id}")

            # 查找素材
            material = None
            for m in self.materials:
                if m.id == material_id:
                    material = m
                    break

            if not material:
                raise ValueError(f"Material not found: {material_id}")

            # 设置素材开始时间
            material.start_time = start_time
            material.end_time = start_time + material.duration

            # 添加到轨道
            track.materials.append(material)
            self.logger.info(f"Added material to track: {material.name} -> {track.id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add material to track: {e}")
            return False

    def add_effect(self,
                  name: str,
                  effect_type: str,
                  start_time: float,
                  duration: float,
                  parameters: Dict[str, Any] = None) -> str:
        """添加特效"""
        try:
            effect = JianyingEffect(
                id=str(uuid.uuid4()),
                name=name,
                type=effect_type,
                start_time=start_time,
                duration=duration,
                parameters=parameters or {}
            )

            self.effects.append(effect)
            self.logger.info(f"Added effect: {effect.name}")
            return effect.id

        except Exception as e:
            self.logger.error(f"Failed to add effect: {e}")
            raise

    def add_text_overlay(self,
                        text: str,
                        start_time: float,
                        duration: float,
                        position: Tuple[float, float] = (0.5, 0.5),
                        font: str = "Arial",
                        size: int = 24,
                        color: str = "#FFFFFF") -> str:
        """添加文字叠加"""
        try:
            text_overlay = JianyingTextOverlay(
                id=str(uuid.uuid4()),
                text=text,
                font=font,
                size=size,
                color=color,
                position=position,
                start_time=start_time,
                duration=duration
            )

            self.text_overlays.append(text_overlay)
            self.logger.info(f"Added text overlay: {text[:20]}...")
            return text_overlay.id

        except Exception as e:
            self.logger.error(f"Failed to add text overlay: {e}")
            raise

    def generate_draft(self,
                      project_name: str,
                      output_path: str,
                      fps: float = 30.0,
                      resolution: Tuple[int, int] = (1920, 1080),
                      audio_sample_rate: int = 48000) -> bool:
        """生成Draft文件"""
        try:
            # 计算项目持续时间
            project_duration = self._calculate_project_duration()

            # 构建Draft数据结构
            draft_data = {
                "version": self.version,
                "project_info": {
                    "name": project_name,
                    "created_by": "CineAIStudio",
                    "created_at": time.time(),
                    "modified_at": time.time()
                },
                "settings": {
                    "fps": fps,
                    "resolution": {
                        "width": resolution[0],
                        "height": resolution[1]
                    },
                    "audio_sample_rate": audio_sample_rate,
                    "duration": project_duration
                },
                "materials": self._serialize_materials(),
                "tracks": self._serialize_tracks(),
                "effects": self._serialize_effects(),
                "text_overlays": self._serialize_text_overlays(),
                "metadata": {
                    "total_materials": len(self.materials),
                    "total_tracks": len(self.tracks),
                    "total_effects": len(self.effects),
                    "total_text_overlays": len(self.text_overlays)
                }
            }

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 保存Draft文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Generated draft file: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate draft: {e}")
            return False

    def _calculate_project_duration(self) -> float:
        """计算项目持续时间"""
        if not self.tracks:
            return 0.0

        max_duration = 0.0
        for track in self.tracks:
            for material in track.materials:
                end_time = material.start_time + material.duration
                max_duration = max(max_duration, end_time)

        return max_duration

    def _serialize_materials(self) -> List[Dict[str, Any]]:
        """序列化素材"""
        materials_data = []
        for material in self.materials:
            material_data = {
                "id": material.id,
                "name": material.name,
                "type": material.type,
                "path": material.path,
                "duration": material.duration,
                "start_time": material.start_time,
                "end_time": material.end_time,
                "metadata": material.metadata
            }
            materials_data.append(material_data)
        return materials_data

    def _serialize_tracks(self) -> List[Dict[str, Any]]:
        """序列化轨道"""
        tracks_data = []
        for track in self.tracks:
            track_data = {
                "id": track.id,
                "type": track.type,
                "enabled": track.enabled,
                "locked": track.locked,
                "volume": track.volume,
                "materials": [m.id for m in track.materials],
                "effects": track.effects
            }
            tracks_data.append(track_data)
        return tracks_data

    def _serialize_effects(self) -> List[Dict[str, Any]]:
        """序列化特效"""
        effects_data = []
        for effect in self.effects:
            effect_data = {
                "id": effect.id,
                "name": effect.name,
                "type": effect.type,
                "start_time": effect.start_time,
                "duration": effect.duration,
                "parameters": effect.parameters
            }
            effects_data.append(effect_data)
        return effects_data

    def _serialize_text_overlays(self) -> List[Dict[str, Any]]:
        """序列化文字叠加"""
        overlays_data = []
        for overlay in self.text_overlays:
            overlay_data = {
                "id": overlay.id,
                "text": overlay.text,
                "font": overlay.font,
                "size": overlay.size,
                "color": overlay.color,
                "position": overlay.position,
                "start_time": overlay.start_time,
                "duration": overlay.duration,
                "effects": overlay.effects
            }
            overlays_data.append(overlay_data)
        return overlays_data

    def _get_video_duration(self, path: str) -> float:
        """获取视频时长"""
        try:
            # 这里应该使用FFmpeg或其他库获取视频信息
            # 为了演示，返回默认值
            return 10.0
        except:
            return 10.0

    def _get_video_width(self, path: str) -> int:
        """获取视频宽度"""
        try:
            return 1920
        except:
            return 1920

    def _get_video_height(self, path: str) -> int:
        """获取视频高度"""
        try:
            return 1080
        except:
            return 1080

    def _get_video_fps(self, path: str) -> float:
        """获取视频帧率"""
        try:
            return 30.0
        except:
            return 30.0

    def _get_audio_duration(self, path: str) -> float:
        """获取音频时长"""
        try:
            return 10.0
        except:
            return 10.0

    def _get_audio_sample_rate(self, path: str) -> int:
        """获取音频采样率"""
        try:
            return 48000
        except:
            return 48000

    def _get_audio_channels(self, path: str) -> int:
        """获取音频声道数"""
        try:
            return 2
        except:
            return 2

    def _get_image_width(self, path: str) -> int:
        """获取图片宽度"""
        try:
            return 1920
        except:
            return 1920

    def _get_image_height(self, path: str) -> int:
        """获取图片高度"""
        try:
            return 1080
        except:
            return 1080

    def clear(self):
        """清空所有数据"""
        self.materials.clear()
        self.tracks.clear()
        self.effects.clear()
        self.text_overlays.clear()
        self.logger.info("Cleared all draft data")


class JianyingDraftParser:
    """剪映Draft文件解析器"""

    def __init__(self):
        self.logger = Logger.get_logger(__name__)

    def parse_draft(self, draft_path: str) -> Dict[str, Any]:
        """解析Draft文件"""
        try:
            if not os.path.exists(draft_path):
                raise FileNotFoundError(f"Draft file not found: {draft_path}")

            with open(draft_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)

            self.logger.info(f"Parsed draft file: {draft_path}")
            return draft_data

        except Exception as e:
            self.logger.error(f"Failed to parse draft: {e}")
            raise

    def validate_draft(self, draft_data: Dict[str, Any]) -> bool:
        """验证Draft文件格式"""
        required_fields = [
            "version",
            "project_info",
            "settings",
            "materials",
            "tracks"
        ]

        for field in required_fields:
            if field not in draft_data:
                self.logger.error(f"Missing required field: {field}")
                return False

        return True

    def get_project_info(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取项目信息"""
        return draft_data.get("project_info", {})

    def get_settings(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取项目设置"""
        return draft_data.get("settings", {})

    def get_materials(self, draft_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取素材列表"""
        return draft_data.get("materials", [])

    def get_tracks(self, draft_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取轨道列表"""
        return draft_data.get("tracks", [])

    def export_to_edl(self, draft_data: Dict[str, Any], output_path: str) -> bool:
        """导出为EDL格式"""
        try:
            tracks = self.get_tracks(draft_data)
            materials = self.get_materials(draft_data)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# CineAIStudio EDL Export\n")
                f.write(f"# Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                for track in tracks:
                    if track.get("type") == "video":
                        f.write(f"# Video Track: {track.get('id')}\n")
                        for material_id in track.get("materials", []):
                            material = next((m for m in materials if m.get("id") == material_id), None)
                            if material:
                                f.write(f"001  {material.get('name')} V     C        ")
                                f.write(f"{self._time_to_edl(material.get('start_time', 0))} ")
                                f.write(f"{self._time_to_edl(material.get('end_time', 0))} ")
                                f.write(f"{self._time_to_edl(0)} ")
                                f.write(f"{self._time_to_edl(material.get('duration', 0))}\n")
                        f.write("\n")

            self.logger.info(f"Exported EDL: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export EDL: {e}")
            return False

    def _time_to_edl(self, seconds: float) -> str:
        """将秒数转换为EDL时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        frames = int((seconds % 1) * 30)  # 假设30fps
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"