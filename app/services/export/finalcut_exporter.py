#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Final Cut Pro 项目导出器 (Final Cut Exporter)

将 ClipFlow 项目导出为 Final Cut Pro 项目文件 (.fcpxml)

Final Cut Pro 使用 FCPXML 格式，包含：
- 项目设置
- 事件（素材库）
- 项目（时间线）
- 素材引用
- 片段和转场

使用示例:
    from app.services.export import FinalCutExporter

    exporter = FinalCutExporter()
    project_path = exporter.export(project, output_dir)
    print(f"项目已导出: {project_path}")
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class FCPVersion(Enum):
    """FCPXML 版本"""
    V1_10 = "1.10"  # Final Cut Pro 10.6+
    V1_9 = "1.9"    # Final Cut Pro 10.5
    V1_8 = "1.8"    # Final Cut Pro 10.4


class VideoFormat(Enum):
    """视频格式"""
    HD_1080 = "FFVideoFormat1080p30"
    HD_720 = "FFVideoFormat720p30"
    UHD_4K = "FFVideoFormat3840x2160p30"
    SD_480 = "FFVideoFormatDV720x480i5994"


@dataclass
class FCPConfig:
    """Final Cut 导出配置"""
    version: FCPVersion = FCPVersion.V1_10
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    video_format: VideoFormat = VideoFormat.HD_1080
    audio_sample_rate: int = 48000
    audio_channels: int = 2


@dataclass
class FCPClip:
    """Final Cut 片段"""
    id: str = field(default_factory=lambda: f"r{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    path: str = ""
    start: int = 0            # 在时间线上的开始位置（单位：1/秒）
    duration: int = 0         # 持续时间
    offset: int = 0           # 素材偏移
    lane: int = 0             # 轨道（lane）
    type: str = "video"       # video, audio, title


@dataclass
class FCPAsset:
    """Final Cut 素材"""
    id: str = field(default_factory=lambda: f"r{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    path: str = ""
    duration: int = 0
    has_video: bool = True
    has_audio: bool = True
    width: int = 1920
    height: int = 1080
    fps: float = 30.0


@dataclass
class FCPProject:
    """Final Cut 项目（时间线）"""
    id: str = field(default_factory=lambda: f"r{uuid.uuid4().hex[:8].upper()}")
    name: str = "Project"
    sequence_id: str = field(default_factory=lambda: f"r{uuid.uuid4().hex[:8].upper()}")
    duration: int = 0
    clips: List[FCPClip] = field(default_factory=list)


@dataclass
class FCPEvent:
    """Final Cut 事件（素材库）"""
    id: str = field(default_factory=lambda: f"r{uuid.uuid4().hex[:8].upper()}")
    name: str = "ClipFlow Event"
    assets: List[FCPAsset] = field(default_factory=list)
    projects: List[FCPProject] = field(default_factory=list)


@dataclass
class FCPLibrary:
    """Final Cut 资源库"""
    id: str = field(default_factory=lambda: f"r{uuid.uuid4().hex[:8].upper()}")
    name: str = "ClipFlow Library"
    events: List[FCPEvent] = field(default_factory=list)


class FinalCutExporter:
    """
    Final Cut Pro 项目导出器

    生成 .fcpxml 文件，可在 Final Cut Pro 中直接导入

    使用示例:
        exporter = FinalCutExporter()

        # 创建资源库
        library = exporter.create_library("我的资源库")

        # 创建事件
        event = exporter.create_event("主事件")
        library.events.append(event)

        # 添加素材
        asset = FCPAsset(
            name="视频.mp4",
            path="/path/to/video.mp4",
            duration=300,  # 10秒 @ 30fps
        )
        event.assets.append(asset)

        # 创建项目（时间线）
        project = exporter.create_project("主项目")

        # 添加片段
        clip = FCPClip(
            name="视频.mp4",
            path="/path/to/video.mp4",
            start=0,
            duration=300,
            offset=0,
        )
        project.clips.append(clip)
        event.projects.append(project)

        # 导出
        exporter.export(library, "/path/to/output")
    """

    # 帧率映射
    FPS_MAP = {
        23.976: "23.976",
        24.0: "24",
        25.0: "25",
        29.97: "29.97",
        30.0: "30",
        50.0: "50",
        59.94: "59.94",
        60.0: "60",
    }

    def __init__(self, config: Optional[FCPConfig] = None):
        """
        初始化导出器

        Args:
            config: Final Cut 配置
        """
        self.config = config or FCPConfig()

    def create_library(self, name: str) -> FCPLibrary:
        """
        创建新资源库

        Args:
            name: 资源库名称

        Returns:
            Final Cut 资源库
        """
        return FCPLibrary(name=name)

    def create_event(self, name: str) -> FCPEvent:
        """
        创建新事件

        Args:
            name: 事件名称

        Returns:
            Final Cut 事件
        """
        return FCPEvent(name=name)

    def create_project(self, name: str) -> FCPProject:
        """
        创建新项目（时间线）

        Args:
            name: 项目名称

        Returns:
            Final Cut 项目
        """
        return FCPProject(name=name)

    def export(self, library: FCPLibrary, output_dir: str) -> str:
        """
        导出资源库为 .fcpxml 文件

        Args:
            library: Final Cut 资源库
            output_dir: 输出目录

        Returns:
            项目文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成安全的文件名
        safe_name = self._safe_filename(library.name)
        project_file = output_path / f"{safe_name}.fcpxml"

        # 生成 FCPXML
        root = self._build_fcpxml(library)

        # 格式化并写入
        xml_string = self._prettify_xml(root)

        with open(project_file, 'w', encoding='utf-8') as f:
            f.write(xml_string)

        return str(project_file)

    def _build_fcpxml(self, library: FCPLibrary) -> ET.Element:
        """构建 FCPXML"""
        # FCPXML 根元素
        root = ET.Element("fcpxml")
        root.set("version", self.config.version.value)

        # 添加资源（素材定义）
        resources = ET.SubElement(root, "resources")

        # 添加格式定义
        format_id = self._add_format_resource(resources)

        # 添加素材资源
        for event in library.events:
            for asset in event.assets:
                self._add_asset_resource(resources, asset, format_id)

        # 添加库
        lib_elem = ET.SubElement(root, "library")
        lib_elem.set("location", f"file:///Users/user/Movies/{library.name}.fcpbundle")

        for event in library.events:
            event_elem = ET.SubElement(lib_elem, "event")
            event_elem.set("name", event.name)
            event_elem.set("uid", event.id)

            # 添加项目（时间线）
            for project in event.projects:
                self._add_project(event_elem, project, format_id)

        return root

    def _add_format_resource(self, resources: ET.Element) -> str:
        """添加格式资源"""
        format_id = "r0"
        format_elem = ET.SubElement(resources, "format")
        format_elem.set("id", format_id)
        format_elem.set("name", self.config.video_format.value)
        format_elem.set("frameDuration", self._frame_duration())
        format_elem.set("width", str(self.config.width))
        format_elem.set("height", str(self.config.height))
        return format_id

    def _add_asset_resource(
        self,
        resources: ET.Element,
        asset: FCPAsset,
        format_id: str,
    ) -> None:
        """添加素材资源"""
        asset_elem = ET.SubElement(resources, "asset")
        asset_elem.set("id", asset.id)
        asset_elem.set("name", asset.name)
        asset_elem.set("uid", f"{asset.id}/{uuid.uuid4().hex}")
        asset_elem.set("src", f"file://{asset.path}")
        asset_elem.set("start", "0s")
        asset_elem.set("duration", self._ticks_to_time(asset.duration))
        asset_elem.set("hasVideo", str(asset.has_video).lower())
        asset_elem.set("hasAudio", str(asset.has_audio).lower())
        asset_elem.set("format", format_id)

    def _add_project(
        self,
        event_elem: ET.Element,
        project: FCPProject,
        format_id: str,
    ) -> None:
        """添加项目（时间线）"""
        project_elem = ET.SubElement(event_elem, "project")
        project_elem.set("name", project.name)
        project_elem.set("uid", project.id)

        # 序列
        sequence = ET.SubElement(project_elem, "sequence")
        sequence.set("duration", self._ticks_to_time(project.duration))
        sequence.set("format", format_id)
        sequence.set("tcStart", "0s")
        sequence.set("tcFormat", "NDF")
        sequence.set("audioLayout", "stereo")
        sequence.set("audioRate", "48k")

        # 主轴（主 storyline）
        spine = ET.SubElement(sequence, "spine")

        # 添加片段
        for clip in project.clips:
            self._add_clip_to_spine(spine, clip)

    def _add_clip_to_spine(self, spine: ET.Element, clip: FCPClip) -> None:
        """添加片段到主轴"""
        clip_elem = ET.SubElement(spine, "clip")
        clip_elem.set("name", clip.name)
        clip_elem.set("offset", self._ticks_to_time(clip.start))
        clip_elem.set("duration", self._ticks_to_time(clip.duration))
        clip_elem.set("tcStart", self._ticks_to_time(clip.offset))

        # 视频源
        if clip.type == "video":
            video = ET.SubElement(clip_elem, "video")
            video.set("duration", self._ticks_to_time(clip.duration))

            # 素材实例
            asset_clip = ET.SubElement(video, "asset-clip")
            asset_clip.set("ref", clip.id)
            asset_clip.set("duration", self._ticks_to_time(clip.duration))

    def _frame_duration(self) -> str:
        """计算帧持续时间"""
        # 1/30s, 1/24s, etc.
        fps = self.config.fps
        if fps == 30.0:
            return "1001/30000s" if self.config.video_format == VideoFormat.HD_1080 else "1/30s"
        elif fps == 24.0:
            return "1/24s"
        elif fps == 25.0:
            return "1/25s"
        elif fps == 60.0:
            return "1/60s"
        else:
            return f"1/{int(fps)}s"

    def _seconds_to_ticks(self, seconds: float) -> int:
        """将秒转换为 tick"""
        # FCP 使用 1/秒 作为时间单位
        return int(seconds * self.config.fps)

    def _ticks_to_time(self, ticks: int) -> str:
        """将 tick 转换为 FCP 时间格式"""
        # FCP 格式: 3000/30000s (100帧 @ 30fps)
        return f"{ticks}/{int(self.config.fps * 1000)}s"

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

    def _prettify_xml(self, elem: ET.Element) -> str:
        """格式化 XML"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    # =========== 便捷方法 ===========

    def add_video_clip(
        self,
        project: FCPProject,
        asset: FCPAsset,
        start: float,
        duration: float,
        offset: float = 0.0,
    ) -> FCPClip:
        """
        便捷方法：添加视频片段

        Args:
            project: 项目
            asset: 素材
            start: 在时间线上的开始位置（秒）
            duration: 持续时间（秒）
            offset: 素材偏移（秒）

        Returns:
            创建的片段
        """
        clip = FCPClip(
            id=asset.id,
            name=asset.name,
            path=asset.path,
            start=self._seconds_to_ticks(start),
            duration=self._seconds_to_ticks(duration),
            offset=self._seconds_to_ticks(offset),
            type="video",
        )

        project.clips.append(clip)
        project.duration = max(project.duration, clip.start + clip.duration)

        return clip

    def create_asset(
        self,
        name: str,
        path: str,
        duration: float,
        width: int = 1920,
        height: int = 1080,
    ) -> FCPAsset:
        """
        便捷方法：创建素材

        Args:
            name: 素材名称
            path: 文件路径
            duration: 持续时间（秒）
            width: 宽度
            height: 高度

        Returns:
            创建的素材
        """
        return FCPAsset(
            name=name,
            path=path,
            duration=self._seconds_to_ticks(duration),
            width=width,
            height=height,
            fps=self.config.fps,
        )

    def export_from_commentary_project(
        self,
        commentary_project: Any,
        output_dir: str,
    ) -> str:
        """
        从解说项目导出到 Final Cut Pro

        Args:
            commentary_project: CommentaryProject 对象
            output_dir: 输出目录

        Returns:
            项目文件路径
        """
        # 创建资源库
        library = self.create_library(f"{commentary_project.name}")

        # 创建事件
        event = self.create_event("主事件")
        library.events.append(event)

        # 创建项目（时间线）
        project = self.create_project("主项目")

        # 创建视频素材
        video_asset = self.create_asset(
            name=Path(commentary_project.source_video).name,
            path=commentary_project.source_video,
            duration=commentary_project.video_duration,
        )
        event.assets.append(video_asset)

        # 添加片段
        current_time = 0.0
        for segment in commentary_project.segments:
            # 视频片段
            self.add_video_clip(
                project,
                video_asset,
                current_time,
                segment.audio_duration,
                segment.video_start,
            )

            # 音频素材和片段
            if segment.audio_path:
                audio_asset = self.create_asset(
                    name=Path(segment.audio_path).name,
                    path=segment.audio_path,
                    duration=segment.audio_duration,
                )
                event.assets.append(audio_asset)

                self.add_video_clip(
                    project,
                    audio_asset,
                    current_time,
                    segment.audio_duration,
                    0.0,
                )

            current_time += segment.audio_duration

        event.projects.append(project)

        # 导出
        return self.export(library, output_dir)


def demo_export():
    """演示 Final Cut Pro 导出"""
    print("=" * 60)
    print("🎬 Final Cut Pro 导出器")
    print("=" * 60)

    exporter = FinalCutExporter()

    # 创建资源库
    library = exporter.create_library("我的AI解说视频")

    # 创建事件
    event = exporter.create_event("主事件")
    library.events.append(event)

    # 创建素材
    video_asset = exporter.create_asset(
        name="video.mp4",
        path="/path/to/video.mp4",
        duration=60.0,
    )
    event.assets.append(video_asset)

    audio_asset = exporter.create_asset(
        name="voiceover.mp3",
        path="/path/to/voiceover.mp3",
        duration=60.0,
    )
    event.assets.append(audio_asset)

    # 创建项目
    project = exporter.create_project("主项目")

    # 添加片段
    exporter.add_video_clip(project, video_asset, 0.0, 30.0, 0.0)
    exporter.add_video_clip(project, audio_asset, 0.0, 30.0, 0.0)

    event.projects.append(project)

    # 导出
    output_dir = "./output/finalcut"
    project_path = exporter.export(library, output_dir)

    print(f"\n✅ 项目已导出: {project_path}")
    print(f"   资源库: {library.name}")
    print(f"   事件: {event.name}")
    print(f"   项目: {project.name}")
    print(f"   素材数量: {len(event.assets)}")
    print(f"   片段数量: {len(project.clips)}")


if __name__ == '__main__':
    demo_export()
