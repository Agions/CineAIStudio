#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字幕数据模型
定义字幕相关的数据结构
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import timedelta


@dataclass
class SubtitleSegment:
    """字幕片段"""
    
    start_time: float  # 开始时间(秒)
    end_time: float    # 结束时间(秒)
    text: str          # 字幕文本
    confidence: float = 1.0  # 置信度(0-1)
    speaker_id: Optional[str] = None  # 说话人ID
    language: str = "zh"  # 语言代码
    style: Optional[Dict[str, Any]] = None  # 样式信息
    
    @property
    def duration(self) -> float:
        """获取片段时长"""
        return self.end_time - self.start_time
    
    @property
    def start_timedelta(self) -> timedelta:
        """获取开始时间的timedelta对象"""
        return timedelta(seconds=self.start_time)
    
    @property
    def end_timedelta(self) -> timedelta:
        """获取结束时间的timedelta对象"""
        return timedelta(seconds=self.end_time)
    
    def to_srt_format(self, index: int) -> str:
        """转换为SRT格式"""
        start_time = self._format_srt_time(self.start_time)
        end_time = self._format_srt_time(self.end_time)
        
        return f"{index}\n{start_time} --> {end_time}\n{self.text}\n"
    
    def to_vtt_format(self) -> str:
        """转换为VTT格式"""
        start_time = self._format_vtt_time(self.start_time)
        end_time = self._format_vtt_time(self.end_time)
        
        return f"{start_time} --> {end_time}\n{self.text}\n"
    
    def _format_srt_time(self, seconds: float) -> str:
        """格式化SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """格式化VTT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"


@dataclass
class SubtitleTrack:
    """字幕轨道"""
    
    segments: List[SubtitleSegment]
    language: str = "zh"
    title: Optional[str] = None
    source: str = "unknown"  # 来源: ocr, speech, manual
    
    def __post_init__(self):
        """初始化后处理"""
        # 按时间排序
        self.segments.sort(key=lambda x: x.start_time)
    
    @property
    def duration(self) -> float:
        """获取总时长"""
        if not self.segments:
            return 0.0
        return self.segments[-1].end_time
    
    @property
    def segment_count(self) -> int:
        """获取片段数量"""
        return len(self.segments)
    
    def add_segment(self, segment: SubtitleSegment):
        """添加字幕片段"""
        self.segments.append(segment)
        # 重新排序
        self.segments.sort(key=lambda x: x.start_time)
    
    def get_text_at_time(self, time: float) -> Optional[str]:
        """获取指定时间的字幕文本"""
        for segment in self.segments:
            if segment.start_time <= time <= segment.end_time:
                return segment.text
        return None
    
    def get_segments_in_range(self, start_time: float, end_time: float) -> List[SubtitleSegment]:
        """获取时间范围内的字幕片段"""
        result = []
        for segment in self.segments:
            # 检查是否有重叠
            if (segment.start_time < end_time and segment.end_time > start_time):
                result.append(segment)
        return result
    
    def merge_segments(self, max_gap: float = 0.5) -> 'SubtitleTrack':
        """合并相近的字幕片段"""
        if not self.segments:
            return SubtitleTrack([], self.language, self.title, self.source)
        
        merged_segments = []
        current_segment = self.segments[0]
        
        for next_segment in self.segments[1:]:
            # 如果间隔小于阈值，合并片段
            if next_segment.start_time - current_segment.end_time <= max_gap:
                current_segment = SubtitleSegment(
                    start_time=current_segment.start_time,
                    end_time=next_segment.end_time,
                    text=f"{current_segment.text} {next_segment.text}",
                    confidence=min(current_segment.confidence, next_segment.confidence),
                    speaker_id=current_segment.speaker_id,
                    language=current_segment.language
                )
            else:
                merged_segments.append(current_segment)
                current_segment = next_segment
        
        merged_segments.append(current_segment)
        
        return SubtitleTrack(merged_segments, self.language, self.title, self.source)
    
    def filter_by_confidence(self, min_confidence: float = 0.5) -> 'SubtitleTrack':
        """根据置信度过滤字幕片段"""
        filtered_segments = [
            segment for segment in self.segments 
            if segment.confidence >= min_confidence
        ]
        
        return SubtitleTrack(filtered_segments, self.language, self.title, self.source)
    
    def to_srt(self) -> str:
        """导出为SRT格式"""
        srt_content = ""
        for i, segment in enumerate(self.segments, 1):
            srt_content += segment.to_srt_format(i) + "\n"
        return srt_content
    
    def to_vtt(self) -> str:
        """导出为VTT格式"""
        vtt_content = "WEBVTT\n\n"
        for segment in self.segments:
            vtt_content += segment.to_vtt_format() + "\n"
        return vtt_content
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "language": self.language,
            "title": self.title,
            "source": self.source,
            "segments": [
                {
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "text": seg.text,
                    "confidence": seg.confidence,
                    "speaker_id": seg.speaker_id,
                    "language": seg.language
                }
                for seg in self.segments
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubtitleTrack':
        """从字典创建字幕轨道"""
        segments = [
            SubtitleSegment(
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                text=seg["text"],
                confidence=seg.get("confidence", 1.0),
                speaker_id=seg.get("speaker_id"),
                language=seg.get("language", "zh")
            )
            for seg in data["segments"]
        ]
        
        return cls(
            segments=segments,
            language=data.get("language", "zh"),
            title=data.get("title"),
            source=data.get("source", "unknown")
        )


class SubtitleExtractorResult:
    """字幕提取结果"""
    
    def __init__(self):
        self.tracks: List[SubtitleTrack] = []
        self.metadata: Dict[str, Any] = {}
        self.processing_time: float = 0.0
        self.success: bool = True
        self.error_message: Optional[str] = None
    
    def add_track(self, track: SubtitleTrack):
        """添加字幕轨道"""
        self.tracks.append(track)
    
    def get_primary_track(self) -> Optional[SubtitleTrack]:
        """获取主要字幕轨道"""
        if not self.tracks:
            return None
        
        # 优先返回语音识别的轨道
        for track in self.tracks:
            if track.source == "speech":
                return track
        
        # 其次返回OCR轨道
        for track in self.tracks:
            if track.source == "ocr":
                return track
        
        # 返回第一个轨道
        return self.tracks[0]
    
    def get_combined_text(self) -> str:
        """获取合并的文本内容"""
        primary_track = self.get_primary_track()
        if not primary_track:
            return ""
        
        return " ".join(segment.text for segment in primary_track.segments)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "tracks": [track.to_dict() for track in self.tracks],
            "metadata": self.metadata,
            "processing_time": self.processing_time,
            "success": self.success,
            "error_message": self.error_message
        }
