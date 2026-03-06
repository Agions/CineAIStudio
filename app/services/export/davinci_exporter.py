#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
达芬奇 (DaVinci Resolve) 项目导出器
生成 .drp 兼容的 XML/OTIO 格式
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DaVinciClip:
    """达芬奇时间线片段"""
    name: str
    file_path: str
    start: float          # 秒
    end: float
    in_point: float = 0.0
    out_point: float = 0.0
    track: int = 1


@dataclass
class DaVinciTimeline:
    """达芬奇时间线"""
    name: str = "ClipFlow Export"
    fps: float = 30.0
    width: int = 1920
    height: int = 1080
    video_clips: List[DaVinciClip] = None
    audio_clips: List[DaVinciClip] = None
    subtitles: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.video_clips is None:
            self.video_clips = []
        if self.audio_clips is None:
            self.audio_clips = []
        if self.subtitles is None:
            self.subtitles = []


class DaVinciExporter:
    """
    达芬奇导出器

    导出为 FCPXML (Final Cut Pro XML) 格式，
    达芬奇可以直接导入 FCPXML。
    """

    def export(self, timeline: DaVinciTimeline,
               output_path: str) -> str:
        """
        导出为 FCPXML 格式（达芬奇兼容）

        Args:
            timeline: 时间线数据
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix not in ('.fcpxml', '.xml'):
            output_path = output_path.with_suffix('.fcpxml')

        root = self._build_fcpxml(timeline)
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(str(output_path), encoding="utf-8", xml_declaration=True)

        return str(output_path)

    def _build_fcpxml(self, timeline: DaVinciTimeline) -> ET.Element:
        """构建 FCPXML 文档"""
        fcpxml = ET.Element("fcpxml", version="1.9")

        # Resources
        resources = ET.SubElement(fcpxml, "resources")

        # Format
        format_elem = ET.SubElement(resources, "format", {
            "id": "r1",
            "name": f"FFVideoFormat{timeline.height}p{int(timeline.fps)}",
            "frameDuration": self._frame_duration(timeline.fps),
            "width": str(timeline.width),
            "height": str(timeline.height),
        })

        # Media assets
        asset_map = {}
        for i, clip in enumerate(timeline.video_clips + timeline.audio_clips):
            asset_id = f"r{i + 2}"
            ET.SubElement(resources, "asset", {
                "id": asset_id,
                "name": clip.name,
                "src": f"file://{clip.file_path}",
                "hasVideo": "1",
                "hasAudio": "1",
            })
            asset_map[clip.file_path] = asset_id

        # Library > Event > Project
        library = ET.SubElement(fcpxml, "library")
        event = ET.SubElement(library, "event", name="ClipFlow Export")
        project = ET.SubElement(event, "project", name=timeline.name)

        # Sequence
        sequence = ET.SubElement(project, "sequence", {
            "format": "r1",
            "duration": self._to_time(self._total_duration(timeline), timeline.fps),
            "tcStart": "0s",
            "tcFormat": "NDF",
        })

        spine = ET.SubElement(sequence, "spine")

        # Video clips
        for clip in timeline.video_clips:
            asset_id = asset_map.get(clip.file_path, "r2")
            clip_elem = ET.SubElement(spine, "asset-clip", {
                "ref": asset_id,
                "name": clip.name,
                "offset": self._to_time(clip.start, timeline.fps),
                "duration": self._to_time(clip.end - clip.start, timeline.fps),
                "start": self._to_time(clip.in_point, timeline.fps),
            })

        # Subtitles as titles
        for sub in timeline.subtitles:
            title = ET.SubElement(spine, "title", {
                "name": sub.get("text", "")[:30],
                "offset": self._to_time(sub.get("start", 0), timeline.fps),
                "duration": self._to_time(
                    sub.get("end", 0) - sub.get("start", 0), timeline.fps
                ),
            })
            text_elem = ET.SubElement(title, "text")
            text_style = ET.SubElement(text_elem, "text-style", {
                "font": "PingFang SC",
                "fontSize": "48",
                "fontColor": "1 1 1 1",
            })
            text_style.text = sub.get("text", "")

        return fcpxml

    def _total_duration(self, timeline: DaVinciTimeline) -> float:
        """计算总时长"""
        max_end = 0.0
        for clip in timeline.video_clips + timeline.audio_clips:
            max_end = max(max_end, clip.end)
        return max_end

    @staticmethod
    def _frame_duration(fps: float) -> str:
        """帧时长（FCPXML 格式）"""
        if fps == 30.0:
            return "100/3000s"
        elif fps == 24.0:
            return "100/2400s"
        elif fps == 25.0:
            return "100/2500s"
        elif fps == 60.0:
            return "100/6000s"
        else:
            return f"100/{int(fps * 100)}s"

    @staticmethod
    def _to_time(seconds: float, fps: float) -> str:
        """秒转 FCPXML 时间格式"""
        frames = int(seconds * fps)
        return f"{frames * 100}/{int(fps * 100)}s"


class SubtitleExporter:
    """
    字幕独立导出器
    支持 SRT 和 ASS 格式
    """

    @staticmethod
    def export_srt(subtitles: List[Dict[str, Any]],
                   output_path: str) -> str:
        """
        导出 SRT 字幕文件

        Args:
            subtitles: [{"start": 1.0, "end": 3.5, "text": "你好"}]
            output_path: 输出路径
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix != '.srt':
            path = path.with_suffix('.srt')

        lines = []
        for i, sub in enumerate(subtitles, 1):
            start = SubtitleExporter._format_srt_time(sub["start"])
            end = SubtitleExporter._format_srt_time(sub["end"])
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(sub["text"])
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    @staticmethod
    def export_ass(subtitles: List[Dict[str, Any]],
                   output_path: str,
                   style: str = "Default",
                   font: str = "PingFang SC",
                   fontsize: int = 48) -> str:
        """
        导出 ASS 字幕文件

        Args:
            subtitles: [{"start": 1.0, "end": 3.5, "text": "你好"}]
            output_path: 输出路径
            style: 样式名称
            font: 字体
            fontsize: 字体大小
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix != '.ass':
            path = path.with_suffix('.ass')

        header = f"""[Script Info]
Title: ClipFlow Export
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: {style},{font},{fontsize},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for sub in subtitles:
            start = SubtitleExporter._format_ass_time(sub["start"])
            end = SubtitleExporter._format_ass_time(sub["end"])
            text = sub["text"].replace("\n", "\\N")
            events.append(
                f"Dialogue: 0,{start},{end},{style},,0,0,0,,{text}"
            )

        content = header + "\n".join(events) + "\n"
        path.write_text(content, encoding="utf-8")
        return str(path)

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """格式化 SRT 时间 00:00:00,000"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        """格式化 ASS 时间 0:00:00.00"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
