#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EDL (Edit Decision List) 导出器

将 VideoForge 项目导出为 CMX 3600 格式的 EDL 文件。

EDL 格式说明:
- CMX 3600 是最广泛支持的 EDL 格式
- 被 Adobe Premiere, DaVinci Resolve, Avid 等支持
- 是行业标准的项目交换格式

EDL 文件结构:
    TITLE: 项目名称
    FCID: 000000
    ...
    001  001      V     C        00:00:00:00 00:00:05:02 00:00:00:00 00:00:05:02
    ...

使用示例:
    from app.services.export import EDLExporter
    
    exporter = EDLExporter()
    edl_path = exporter.export(project, output_dir)
    print(f"EDL 已导出: {edl_path}")
"""

import re
import logging
from pathlib import Path

# 获取 logger
logger = logging.getLogger(__name__)
from typing import List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class EDLFieldLengths:
    """EDL 字段长度定义 (CMX 3600 格式)"""
    EVENT_NUM = 3        # 事件编号
    REEL_NAME = 8        # 磁带名称/素材名
    TRACK_TYPE = 1       # 轨道类型 (V/A)
    EDIT_TYPE = 2        # 编辑类型 (C=剪切, D=叠化, etc)
    SRC_START = 11       # 源开始时间码
    SRC_END = 11         # 源结束时间码
    REC_START = 11       # 录制开始时间码
    REC_END = 11         # 录制结束时间码


class EditType(Enum):
    """编辑类型"""
    CUT = "C"            # 硬切
    DISSOLVE = "D"       # 叠化
    WIPE = "K"           # 划像
    KEY = "K"            # 键控 (与划像相同代码)


@dataclass
class EDLClip:
    """EDL 片段"""
    event_num: int = 1              # 事件编号
    reel_name: str = "AX"           # 磁带/素材名称
    track_type: str = "V"           # V=视频, A=音频
    edit_type: str = "C"            # 编辑类型
    src_start: float = 0.0          # 源开始时间（秒）
    src_end: float = 0.0            # 源结束时间（秒）
    rec_start: float = 0.0          # 录制开始时间（秒）
    rec_end: float = 0.0            # 录制结束时间（秒）
    
    # 扩展字段（EDL 变体格式支持）
    clip_name: str = ""             # 片段名称
    frame_rate: float = 30.0        # 帧率
    

@dataclass
class EDLConfig:
    """EDL 导出配置"""
    title: str = "VideoForge Project"  # 项目标题
    frame_rate: float = 30.0         # 帧率 (23.976, 24, 25, 29.97, 30, 60)
    video_reel: str = "AX"          # 视频默认磁带名
    audio_reel: str = "AA"         # 音频默认磁带名
    timecode_format: str = "ms"     # "ms"=毫秒, "tc"=时间码
    version: str = "VideoForge v2.0"  # 生成版本


class EDLExporter:
    """
    EDL (CMX 3600) 导出器
    
    支持:
    - 标准 CMX 3600 格式
    - 多轨道导出（视频轨 + 音频轨）
    - 时间码和毫秒两种格式
    """
    
    def __init__(self, config: Optional[EDLConfig] = None):
        self.config = config or EDLConfig()
    
    def export(
        self,
        project: Any,
        output_path: str,
    ) -> str:
        """
        导出 EDL 文件
        
        Args:
            project: 项目对象（支持多种格式）
            output_path: 输出文件路径
            
        Returns:
            EDL 文件路径
        """
        clips = self._convert_project_to_clips(project)
        
        edl_content = self._generate_edl(clips)
        
        output_path = Path(output_path)
        if not output_path.suffix.lower() == '.edl':
            output_path = output_path.with_suffix('.edl')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(edl_content)
        
        return str(output_path)
    
    def _convert_project_to_clips(self, project: Any) -> List[EDLClip]:
        """将项目转换为 EDL 片段列表"""
        clips = []
        
        # 支持从不同格式的项目对象提取片段
        if hasattr(project, 'segments'):
            # 通用片段格式
            clips.extend(self._extract_from_segments(project.segments, "V"))
        
        if hasattr(project, 'audio_segments'):
            clips.extend(self._extract_from_segments(project.audio_segments, "A"))
        
        if hasattr(project, 'video_tracks'):
            # 轨道格式
            for track in project.video_tracks:
                if hasattr(track, 'clips'):
                    clips.extend(self._extract_from_segments(track.clips, "V"))
        
        if hasattr(project, 'audio_tracks'):
            for track in project.audio_tracks:
                if hasattr(track, 'clips'):
                    clips.extend(self._extract_from_segments(track.clips, "A"))
        
        # 如果项目本身就是片段列表
        if isinstance(project, list):
            for item in project:
                if hasattr(item, 'source_path'):
                    clips.append(self._create_clip_from_segment(item, "V"))
        
        # 按录制时间排序
        clips.sort(key=lambda c: c.rec_start)
        
        # 重新编号
        for i, clip in enumerate(clips):
            clip.event_num = i + 1
        
        return clips
    
    def _extract_from_segments(self, segments: List, track_type: str) -> List[EDLClip]:
        """从片段列表提取"""
        clips = []
        rec_time = 0.0
        
        for seg in segments:
            clip = self._create_clip_from_segment(seg, track_type)
            
            if clip:
                # 更新录制时间（连续排列）
                duration = clip.rec_end - clip.rec_start
                clip.rec_start = rec_time
                clip.rec_end = rec_time + duration
                rec_time += duration
                
                clips.append(clip)
        
        return clips
    
    def _create_clip_from_segment(self, seg: Any, track_type: str) -> Optional[EDLClip]:
        """从片段对象创建 EDL 片段"""
        try:
            # 尝试多种属性名
            src_start = getattr(seg, 'source_start', 
                       getattr(seg, 'src_start', 
                       getattr(seg, 'in_point', 0)))
            
            src_end = getattr(seg, 'source_end',
                     getattr(seg, 'src_end',
                     getattr(seg, 'out_point',
                     getattr(seg, 'start', 0) + getattr(seg, 'duration', 5))))
            
            # 获取素材名称
            source_path = getattr(seg, 'source_path',
                         getattr(seg, 'path',
                         getattr(seg, 'file_path', "")))
            
            reel_name = Path(source_path).stem if source_path else "AX"
            # EDL 磁带名最长 8 字符
            reel_name = reel_name[:8].upper().ljust(8)
            
            clip = EDLClip(
                event_num=1,
                reel_name=reel_name,
                track_type=track_type,
                edit_type="C",  # 默认硬切
                src_start=float(src_start),
                src_end=float(src_end),
                rec_start=0.0,
                rec_end=float(src_end - src_start),
            )
            
            return clip
            
        except Exception as e:
            logger.warning(f"创建 EDL 片段失败: {e}")
            return None
    
    def _timecode_to_edl_format(self, seconds: float, fps: float = 30.0) -> str:
        """
        将秒数转换为 EDL 时间码格式
        
        Args:
            seconds: 秒数
            fps: 帧率
            
        Returns:
            HH:MM:SS:FF 格式字符串
        """
        total_frames = int(seconds * fps)
        frames = total_frames % int(fps)
        total_seconds = total_frames // int(fps)
        seconds = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        hours = total_minutes // 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
    
    def _milliseconds_to_edl_format(self, ms: float) -> str:
        """
        将毫秒转换为 EDL 格式 (SMPTE 时间码)
        
        Args:
            ms: 毫秒
            
        Returns:
            HH:MM:SS:FF 格式字符串
        """
        seconds = ms / 1000.0
        fps = self.config.frame_rate
        
        total_frames = int(seconds * fps)
        frames = total_frames % int(fps)
        total_seconds = total_frames // int(fps)
        secs = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        hours = total_minutes // 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"
    
    def _generate_edl(self, clips: List[EDLClip]) -> str:
        """生成 EDL 文件内容"""
        lines = []
        
        # 标题头
        lines.append(f"TITLE: {self.config.title}")
        lines.append(f"FCID: 000000")
        lines.append(f"")  # 空行
        
        # 字段头（可选，某些编辑器需要）
        field_header = (
            f"{'EVENT':<8}"
            f"{'REEL':<10}"
            f"{'TRACK':<7}"
            f"{'TYPE':<6}"
            f"{'SRC IN':<12}"
            f"{'SRC OUT':<12}"
            f"{'REC IN':<12}"
            f"{'REC OUT':<12}"
        )
        # lines.append(field_header)
        
        # 生成片段行
        for clip in clips:
            line = self._format_clip_line(clip)
            lines.append(line)
        
        return "\n".join(lines)
    
    def _format_clip_line(self, clip: EDLClip) -> str:
        """
        格式化单个片段为 EDL 行
        
        CMX 3600 格式:
        001  AX      V     C        00:00:00:00 00:00:05:02 00:00:00:00 00:00:05:02
        """
        # 事件编号 (3位，右对齐)
        event = f"{clip.event_num:03d}"
        
        # 磁带名 (8字符)
        reel = clip.reel_name[:8].ljust(8)
        
        # 轨道类型
        track = clip.track_type
        
        # 编辑类型
        edit_type = clip.edit_type
        
        # 时间码格式
        if self.config.timecode_format == "tc":
            src_in = self._timecode_to_edl_format(clip.src_start, self.config.frame_rate)
            src_out = self._timecode_to_edl_format(clip.src_end, self.config.frame_rate)
            rec_in = self._timecode_to_edl_format(clip.rec_start, self.config.frame_rate)
            rec_out = self._timecode_to_edl_format(clip.rec_end, self.config.frame_rate)
        else:
            # 毫秒格式
            src_in = self._milliseconds_to_edl_format(clip.src_start * 1000)
            src_out = self._milliseconds_to_edl_format(clip.src_end * 1000)
            rec_in = self._milliseconds_to_edl_format(clip.rec_start * 1000)
            rec_out = self._milliseconds_to_edl_format(clip.rec_end * 1000)
        
        # 组合行
        # 格式: NNN  RRRRRRRR  T  TT  SSSSSSSSSS SSSSSSSSSS SSSSSSSSSS SSSSSSSSSS
        line = (
            f"{event}  "
            f"{reel}  "
            f"{track}  "
            f"{edit_type}  "
            f"{src_in}  "
            f"{src_out}  "
            f"{rec_in}  "
            f"{rec_out}"
        )
        
        return line
    
    def export_with_comments(
        self,
        project: Any,
        output_path: str,
        comments: Optional[List[str]] = None,
    ) -> str:
        """
        导出带注释的 EDL 文件
        
        Args:
            project: 项目对象
            output_path: 输出路径
            comments: 额外的注释列表
            
        Returns:
            EDL 文件路径
        """
        clips = self._convert_project_to_clips(project)
        
        lines = []
        
        # 标题
        lines.append(f"TITLE: {self.config.title}")
        lines.append(f"FCID: 000000")
        lines.append(f"")
        
        # 注释区
        if comments:
            lines.append("* FROM CLIPFLOW")
            lines.append(f"* EXPORTED: {self._get_timestamp()}")
            lines.append(f"* FRAME RATE: {self.config.frame_rate}")
            for comment in comments:
                lines.append(f"* {comment}")
            lines.append("")
        
        # 生成片段行
        for clip in clips:
            # 添加片段注释（如果有名称）
            if clip.clip_name:
                lines.append(f"* CLIP: {clip.clip_name}")
            
            line = self._format_clip_line(clip)
            lines.append(line)
        
        output_path = Path(output_path)
        if not output_path.suffix.lower() == '.edl':
            output_path = output_path.with_suffix('.edl')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        return str(output_path)
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def parse_edl(self, edl_path: str) -> List[EDLClip]:
        """
        解析 EDL 文件（反向转换）
        
        Args:
            edl_path: EDL 文件路径
            
        Returns:
            EDL 片段列表
        """
        clips = []
        
        with open(edl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 跳过空行和注释
                if not line or line.startswith('*') or line.startswith('TITLE'):
                    continue
                
                # 解析 CMX 3600 格式行
                # 001  AX      V     C        00:00:00:00 00:00:05:02 00:00:00:00 00:00:05:02
                parts = re.split(r'\s+', line)
                
                if len(parts) >= 8:
                    try:
                        clip = EDLClip()
                        clip.event_num = int(parts[0])
                        clip.reel_name = parts[1]
                        clip.track_type = parts[2]
                        clip.edit_type = parts[3]
                        
                        # 解析时间码
                        clip.src_start = self._parse_timecode(parts[4])
                        clip.src_end = self._parse_timecode(parts[5])
                        clip.rec_start = self._parse_timecode(parts[6])
                        clip.rec_end = self._parse_timecode(parts[7])
                        
                        clips.append(clip)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"解析 EDL 行失败: {line[:50]}... - {e}")
                        continue
        
        return clips
    
    def _parse_timecode(self, tc: str) -> float:
        """解析 EDL 时间码为秒数"""
        # 格式: HH:MM:SS:FF
        try:
            parts = tc.split(':')
            if len(parts) == 4:
                hours, minutes, seconds, frames = map(int, parts)
                total_seconds = hours * 3600 + minutes * 60 + seconds + frames / self.config.frame_rate
                return total_seconds
            elif len(parts) == 3:
                # 可能是 SS:FF 或 MM:SS:FF
                if self.config.frame_rate <= 30:
                    minutes, seconds, frames = map(int, parts)
                    return minutes * 60 + seconds + frames / self.config.frame_rate
                else:
                    hours, minutes, seconds = map(int, parts)
                    return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            pass
        
        try:
            # 尝试直接解析为秒数
            return float(tc)
        except ValueError:
            return 0.0


def export_to_edl(
    project: Any,
    output_path: str,
    title: str = "VideoForge Project",
    frame_rate: float = 30.0,
) -> str:
    """
    便捷的 EDL 导出函数
    
    Args:
        project: 项目对象
        output_path: 输出路径
        title: 项目标题
        frame_rate: 帧率
        
    Returns:
        EDL 文件路径
    """
    config = EDLConfig(title=title, frame_rate=frame_rate)
    exporter = EDLExporter(config)
    return exporter.export(project, output_path)


# ========== 使用示例 ==========

def demo_export():
    """演示 EDL 导出"""
    from dataclasses import dataclass
    
    # 创建模拟项目
    @dataclass
    class MockSegment:
        source_path: str = "video001.mp4"
        source_start: float = 0.0
        source_end: float = 5.0
    
    project = [
        MockSegment("clip_a.mp4", 0.0, 5.0),
        MockSegment("clip_b.mp4", 2.0, 8.0),
        MockSegment("clip_c.mp4", 1.0, 4.0),
    ]
    
    # 导出 EDL
    exporter = EDLExporter(EDLConfig(
        title="Demo Project",
        frame_rate=30.0,
    ))
    
    output = exporter.export(project, "./demo_export.edl")
    print(f"EDL 已导出: {output}")
    
    # 读取并解析
    clips = exporter.parse_edl(output)
    print(f"\n解析到 {len(clips)} 个片段:")
    for clip in clips:
        print(f"  事件 {clip.event_num}: {clip.reel_name.strip()} "
              f"REC {clip.rec_start:.2f}s - {clip.rec_end:.2f}s")


if __name__ == '__main__':
    demo_export()
