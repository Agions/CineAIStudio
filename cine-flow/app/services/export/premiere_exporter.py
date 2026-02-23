#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Adobe Premiere Pro 项目导出器 (Premiere Exporter)

将 ClipFlow 项目导出为 Premiere Pro 项目文件 (.prproj)

Premiere Pro 项目文件是 XML 格式的，包含：
- 项目设置
- 序列（时间线）
- 素材引用
- 轨道和片段

使用示例:
    from app.services.export import PremiereExporter

    exporter = PremiereExporter()
    project_path = exporter.export(project, output_dir)
    print(f"项目已导出: {project_path}")
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class PremiereVersion(Enum):
    """Premiere Pro 版本"""
    CC2024 = "2024"
    CC2023 = "2023"
    CC2022 = "2022"
    CC2021 = "2021"
    CC2020 = "2020"


class VideoStandard(Enum):
    """视频标准"""
    NTSC = "NTSC"
    PAL = "PAL"


@dataclass
class PremiereConfig:
    """Premiere 导出配置"""
    version: PremiereVersion = PremiereVersion.CC2024
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    video_standard: VideoStandard = VideoStandard.NTSC
    audio_sample_rate: int = 48000
    audio_channels: int = 2


@dataclass
class PremiereClip:
    """Premiere 片段"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()).upper())
    name: str = ""
    path: str = ""
    start: float = 0.0          # 在时间线上的开始位置（秒）
    end: float = 0.0            # 在时间线上的结束位置（秒）
    in_point: float = 0.0       # 素材入点（秒）
    out_point: float = 0.0      # 素材出点（秒）
    track: int = 1              # 轨道编号
    type: str = "video"         # video, audio, text


@dataclass
class PremiereTrack:
    """Premiere 轨道"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()).upper())
    name: str = ""
    type: str = "video"         # video, audio
    index: int = 1
    clips: List[PremiereClip] = field(default_factory=list)


@dataclass
class PremiereSequence:
    """Premiere 序列（时间线）"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()).upper())
    name: str = "Sequence 01"
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    duration: float = 0.0       # 总时长（秒）
    video_tracks: List[PremiereTrack] = field(default_factory=list)
    audio_tracks: List[PremiereTrack] = field(default_factory=list)


@dataclass
class PremiereProject:
    """Premiere 项目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()).upper())
    name: str = "ClipFlow Project"
    version: PremiereVersion = PremiereVersion.CC2024
    sequences: List[PremiereSequence] = field(default_factory=list)
    clips: List[PremiereClip] = field(default_factory=list)


class PremiereExporter:
    """
    Adobe Premiere Pro 项目导出器

    生成 .prproj 文件，可在 Premiere Pro 中直接打开

    使用示例:
        exporter = PremiereExporter()

        # 创建项目
        project = exporter.create_project("我的项目")

        # 添加序列
        sequence = exporter.create_sequence("主序列")

        # 添加视频片段
        clip = PremiereClip(
            name="视频片段",
            path="/path/to/video.mp4",
            start=0.0,
            end=10.0,
            in_point=0.0,
            out_point=10.0,
        )
        sequence.video_tracks[0].clips.append(clip)

        # 导出
        exporter.export(project, "/path/to/output")
    """

    # Premiere 项目文件版本号
    VERSION_MAP = {
        PremiereVersion.CC2024: "42",
        PremiereVersion.CC2023: "41",
        PremiereVersion.CC2022: "40",
        PremiereVersion.CC2021: "39",
        PremiereVersion.CC2020: "38",
    }

    def __init__(self, config: Optional[PremiereConfig] = None):
        """
        初始化导出器

        Args:
            config: Premiere 配置
        """
        self.config = config or PremiereConfig()

    def create_project(self, name: str) -> PremiereProject:
        """
        创建新项目

        Args:
            name: 项目名称

        Returns:
            Premiere 项目
        """
        return PremiereProject(
            name=name,
            version=self.config.version,
        )

    def create_sequence(
        self,
        name: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[float] = None,
    ) -> PremiereSequence:
        """
        创建新序列

        Args:
            name: 序列名称
            width: 宽度
            height: 高度
            fps: 帧率

        Returns:
            Premiere 序列
        """
        sequence = PremiereSequence(
            name=name,
            width=width or self.config.width,
            height=height or self.config.height,
            fps=fps or self.config.fps,
        )

        # 添加默认轨道
        sequence.video_tracks.append(PremiereTrack(
            name="Video 1",
            type="video",
            index=1,
        ))

        sequence.audio_tracks.append(PremiereTrack(
            name="Audio 1",
            type="audio",
            index=1,
        ))

        return sequence

    def export(self, project: PremiereProject, output_dir: str) -> str:
        """
        导出项目为 .prproj 文件

        Args:
            project: Premiere 项目
            output_dir: 输出目录

        Returns:
            项目文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成安全的文件名
        safe_name = self._safe_filename(project.name)
        project_file = output_path / f"{safe_name}.prproj"

        # 生成 XML
        root = self._build_xml(project)

        # 格式化并写入
        xml_string = self._prettify_xml(root)

        with open(project_file, 'w', encoding='utf-8') as f:
            f.write(xml_string)

        return str(project_file)

    def _build_xml(self, project: PremiereProject) -> ET.Element:
        """构建 Premiere 项目 XML"""
        # Premiere 项目文件结构
        root = ET.Element("PremiereData")
        root.set("Version", self.VERSION_MAP.get(project.version, "42"))

        # 项目信息
        project_elem = ET.SubElement(root, "Project")
        project_elem.set("Name", project.name)
        project_elem.set("ID", project.id)

        # 项目设置
        settings = ET.SubElement(project_elem, "Settings")
        self._add_video_settings(settings)
        self._add_audio_settings(settings)

        # 素材箱（素材列表）
        bins = ET.SubElement(project_elem, "Bins")
        root_bin = ET.SubElement(bins, "Bin")
        root_bin.set("Name", "Root")

        # 添加素材
        for clip in project.clips:
            clip_elem = ET.SubElement(root_bin, "Clip")
            clip_elem.set("ID", clip.id)
            clip_elem.set("Name", clip.name)
            clip_elem.set("Path", clip.path)
            clip_elem.set("Type", clip.type)

        # 序列
        sequences = ET.SubElement(project_elem, "Sequences")
        for sequence in project.sequences:
            seq_elem = ET.SubElement(sequences, "Sequence")
            seq_elem.set("ID", sequence.id)
            seq_elem.set("Name", sequence.name)
            seq_elem.set("Width", str(sequence.width))
            seq_elem.set("Height", str(sequence.height))
            seq_elem.set("FrameRate", str(sequence.fps))

            # 视频轨道
            video_tracks = ET.SubElement(seq_elem, "VideoTracks")
            for track in sequence.video_tracks:
                track_elem = ET.SubElement(video_tracks, "Track")
                track_elem.set("ID", track.id)
                track_elem.set("Name", track.name)
                track_elem.set("Index", str(track.index))

                # 片段
                for clip in track.clips:
                    clip_elem = ET.SubElement(track_elem, "ClipInstance")
                    clip_elem.set("ClipID", clip.id)
                    clip_elem.set("Start", str(self._seconds_to_ticks(clip.start, sequence.fps)))
                    clip_elem.set("End", str(self._seconds_to_ticks(clip.end, sequence.fps)))
                    clip_elem.set("InPoint", str(self._seconds_to_ticks(clip.in_point, sequence.fps)))
                    clip_elem.set("OutPoint", str(self._seconds_to_ticks(clip.out_point, sequence.fps)))

            # 音频轨道
            audio_tracks = ET.SubElement(seq_elem, "AudioTracks")
            for track in sequence.audio_tracks:
                track_elem = ET.SubElement(audio_tracks, "Track")
                track_elem.set("ID", track.id)
                track_elem.set("Name", track.name)
                track_elem.set("Index", str(track.index))

        return root

    def _add_video_settings(self, parent: ET.Element) -> None:
        """添加视频设置"""
        video = ET.SubElement(parent, "VideoSettings")
        ET.SubElement(video, "Width").text = str(self.config.width)
        ET.SubElement(video, "Height").text = str(self.config.height)
        ET.SubElement(video, "FrameRate").text = str(self.config.fps)
        ET.SubElement(video, "PixelAspectRatio").text = "1.0"
        ET.SubElement(video, "FieldType").text = "Progressive"

    def _add_audio_settings(self, parent: ET.Element) -> None:
        """添加音频设置"""
        audio = ET.SubElement(parent, "AudioSettings")
        ET.SubElement(audio, "SampleRate").text = str(self.config.audio_sample_rate)
        ET.SubElement(audio, "Channels").text = str(self.config.audio_channels)

    def _seconds_to_ticks(self, seconds: float, fps: float) -> int:
        """将秒转换为 Premiere 的 tick 单位"""
        # Premiere 使用 254016000000 ticks per second
        ticks_per_second = 254016000000
        return int(seconds * ticks_per_second)

    def _ticks_to_seconds(self, ticks: int, fps: float) -> float:
        """将 tick 转换为秒"""
        ticks_per_second = 254016000000
        return ticks / ticks_per_second

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
        sequence: PremiereSequence,
        video_path: str,
        start: float,
        duration: float,
        in_point: float = 0.0,
        track_index: int = 0,
    ) -> PremiereClip:
        """
        便捷方法：添加视频片段

        Args:
            sequence: 序列
            video_path: 视频路径
            start: 在时间线上的开始位置（秒）
            duration: 持续时间（秒）
            in_point: 素材入点（秒）
            track_index: 轨道索引

        Returns:
            创建的片段
        """
        clip = PremiereClip(
            name=Path(video_path).name,
            path=video_path,
            start=start,
            end=start + duration,
            in_point=in_point,
            out_point=in_point + duration,
            track=track_index + 1,
            type="video",
        )

        # 确保轨道存在
        while len(sequence.video_tracks) <= track_index:
            sequence.video_tracks.append(PremiereTrack(
                name=f"Video {len(sequence.video_tracks) + 1}",
                type="video",
                index=len(sequence.video_tracks) + 1,
            ))

        sequence.video_tracks[track_index].clips.append(clip)

        # 更新序列时长
        sequence.duration = max(sequence.duration, start + duration)

        return clip

    def add_audio_clip(
        self,
        sequence: PremiereSequence,
        audio_path: str,
        start: float,
        duration: float,
        in_point: float = 0.0,
        track_index: int = 0,
    ) -> PremiereClip:
        """
        便捷方法：添加音频片段

        Args:
            sequence: 序列
            audio_path: 音频路径
            start: 在时间线上的开始位置（秒）
            duration: 持续时间（秒）
            in_point: 素材入点（秒）
            track_index: 轨道索引

        Returns:
            创建的片段
        """
        clip = PremiereClip(
            name=Path(audio_path).name,
            path=audio_path,
            start=start,
            end=start + duration,
            in_point=in_point,
            out_point=in_point + duration,
            track=track_index + 1,
            type="audio",
        )

        # 确保轨道存在
        while len(sequence.audio_tracks) <= track_index:
            sequence.audio_tracks.append(PremiereTrack(
                name=f"Audio {len(sequence.audio_tracks) + 1}",
                type="audio",
                index=len(sequence.audio_tracks) + 1,
            ))

        sequence.audio_tracks[track_index].clips.append(clip)

        return clip

    def export_from_commentary_project(
        self,
        commentary_project: Any,
        output_dir: str,
    ) -> str:
        """
        从解说项目导出到 Premiere

        Args:
            commentary_project: CommentaryProject 对象
            output_dir: 输出目录

        Returns:
            项目文件路径
        """
        # 创建项目
        project = self.create_project(commentary_project.name)

        # 创建序列
        sequence = self.create_sequence("主序列")
        project.sequences.append(sequence)

        # 添加视频片段
        current_time = 0.0
        for segment in commentary_project.segments:
            # 视频
            self.add_video_clip(
                sequence,
                commentary_project.source_video,
                current_time,
                segment.audio_duration,
                segment.video_start,
                track_index=0,
            )

            # 音频
            if segment.audio_path:
                self.add_audio_clip(
                    sequence,
                    segment.audio_path,
                    current_time,
                    segment.audio_duration,
                    0.0,
                    track_index=0,
                )

            current_time += segment.audio_duration

        # 导出
        return self.export(project, output_dir)


def demo_export():
    """演示 Premiere 导出"""
    print("=" * 60)
    print("🎬 Adobe Premiere Pro 导出器")
    print("=" * 60)

    exporter = PremiereExporter()

    # 创建项目
    project = exporter.create_project("我的AI解说视频")

    # 创建序列
    sequence = exporter.create_sequence("主序列", width=1920, height=1080, fps=30.0)
    project.sequences.append(sequence)

    # 添加片段
    exporter.add_video_clip(
        sequence,
        "/path/to/video.mp4",
        start=0.0,
        duration=10.0,
        track_index=0,
    )

    exporter.add_audio_clip(
        sequence,
        "/path/to/audio.mp3",
        start=0.0,
        duration=10.0,
        track_index=0,
    )

    # 导出
    output_dir = "./output/premiere"
    project_path = exporter.export(project, output_dir)

    print(f"\n✅ 项目已导出: {project_path}")
    print(f"   序列: {sequence.name}")
    print(f"   分辨率: {sequence.width}x{sequence.height}")
    print(f"   帧率: {sequence.fps}fps")
    print(f"   视频轨道: {len(sequence.video_tracks)}")
    print(f"   音频轨道: {len(sequence.audio_tracks)}")


if __name__ == '__main__':
    demo_export()
