#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频片段定义
用于构建完整故事视频
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class SegmentType(Enum):
    """片段类型"""
    ORIGINAL = "original"      # 原片片段
    AI_NARRATION = "ai_narration"  # AI 解说
    AI_MONOLOGUE = "ai_monologue"  # AI 独白
    BGM = "bgm"               # 背景音乐
    TRANSITION = "transition"  # 转场


@dataclass
class VideoSegment:
    """
    视频片段
    
    用于构建完整故事视频
    原片 + AI 内容交替呈现
    """
    # 基本信息
    segment_id: str
    segment_type: SegmentType
    
    # 时间信息
    start_time: float = 0.0    # 在最终视频中的开始时间
    duration: float = 0.0       # 持续时间
    
    # 原片信息 (SegmentType.ORIGINAL)
    source_video: str = ""     # 源视频路径
    source_start: float = 0.0   # 源视频开始时间
    source_end: float = 0.0     # 源视频结束时间
    
    # AI 内容 (SegmentType.AI_*)
    script: str = ""            # 脚本/文案
    voice_path: str = ""        # AI 配音文件
    captions_path: str = ""    # 字幕文件
    
    # 背景音乐 (SegmentType.BGM)
    bgm_path: str = ""
    bgm_volume: float = 0.3     # BGM 音量
    
    # 转场 (SegmentType.TRANSITION)
    transition_type: str = "fade"
    transition_duration: float = 0.5
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def end_time(self) -> float:
        return self.start_time + self.duration
    
    @property
    def is_original(self) -> bool:
        return self.segment_type == SegmentType.ORIGINAL
    
    @property
    def is_ai_content(self) -> bool:
        return self.segment_type in [SegmentType.AI_NARRATION, SegmentType.AI_MONOLOGUE]


@dataclass
class StoryLine:
    """
    故事线
    
    由多个片段组成完整故事视频
    原片 + AI 内容交替呈现
    """
    title: str = ""
    total_duration: float = 0.0
    segments: List[VideoSegment] = field(default_factory=list)
    
    def add_segment(self, segment: VideoSegment):
        """添加片段"""
        # 设置开始时间
        if self.segments:
            segment.start_time = self.segments[-1].end_time
        else:
            segment.start_time = 0
        
        # 设置持续时间
        if segment.duration == 0:
            if segment.is_original:
                segment.duration = segment.source_end - segment.source_start
            elif segment.is_ai_content and segment.voice_path:
                # 估算配音时长：字数 / 语速
                text = segment.script or ""
                segment.duration = self._estimate_voice_duration(text)
        
        self._update_duration()
    
    def _estimate_voice_duration(self, text: str, words_per_minute: float = 150.0) -> float:
        """
        估算配音时长
        
        Args:
            text: 文本内容
            words_per_minute: 语速 (默认150字/分钟)
            
        Returns:
            估算时长(秒)
        """
        if not text:
            return 3.0
        
        # 中文字数 / 英文字数
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = sum(1 for c in text if c.isalpha())
        
        # 估算
        total_units = chinese_chars + english_words
        duration_minutes = total_units / words_per_minute
        
        return max(2.0, duration_minutes * 60)  # 至少2秒
    
    def _update_duration(self):
        """更新总时长"""
        if self.segments:
            self.total_duration = self.segments[-1].end_time
        else:
            self.total_duration = 0
    
    def get_original_segments(self) -> List[VideoSegment]:
        """获取所有原片片段"""
        return [s for s in self.segments if s.is_original]
    
    def get_ai_segments(self) -> List[VideoSegment]:
        """获取所有 AI 内容片段"""
        return [s for s in self.segments if s.is_ai_content]
    
    def to_timeline(self) -> List[Dict]:
        """转换为时间线格式"""
        return [
            {
                "id": s.segment_id,
                "type": s.segment_type.value,
                "start": s.start_time,
                "end": s.end_time,
                "duration": s.duration,
                "source": s.source_video if s.is_original else None,
                "script": s.script if s.is_ai_content else None,
            }
            for s in self.segments
        ]


class StoryBuilder:
    """
    故事构建器
    
    帮助构建"原片+AI内容"交替的完整故事
    """
    
    def __init__(self):
        self._story = StoryLine()
        self._segment_counter = 0
    
    def add_original(
        self,
        source_video: str,
        start: float,
        end: float,
        description: str = "",
    ) -> "StoryBuilder":
        """添加原片片段"""
        self._segment_counter += 1
        
        segment = VideoSegment(
            segment_id=f"seg_{self._segment_counter}",
            segment_type=SegmentType.ORIGINAL,
            source_video=source_video,
            source_start=start,
            source_end=end,
            metadata={"description": description},
        )
        
        self._story.add_segment(segment)
        return self
    
    def add_narration(
        self,
        script: str,
        voice_path: str = "",
    ) -> "StoryBuilder":
        """添加 AI 解说"""
        self._segment_counter += 1
        
        segment = VideoSegment(
            segment_id=f"nar_{self._segment_counter}",
            segment_type=SegmentType.AI_NARRATION,
            script=script,
            voice_path=voice_path,
        )
        
        self._story.add_segment(segment)
        return self
    
    def add_monologue(
        self,
        script: str,
        voice_path: str = "",
    ) -> "StoryBuilder":
        """添加 AI 独白"""
        self._segment_counter += 1
        
        segment = VideoSegment(
            segment_id=f"mono_{self._segment_counter}",
            segment_type=SegmentType.AI_MONOLOGUE,
            script=script,
            voice_path=voice_path,
        )
        
        self._story.add_segment(segment)
        return self
    
    def add_bgm(
        self,
        bgm_path: str,
        volume: float = 0.3,
    ) -> "StoryBuilder":
        """添加背景音乐"""
        self._segment_counter += 1
        
        # BGM 贯穿整个视频
        segment = VideoSegment(
            segment_id=f"bgm_{self._segment_counter}",
            segment_type=SegmentType.BGM,
            bgm_path=bgm_path,
            bgm_volume=volume,
            duration=self._story.total_duration,  # 持续整个视频
        )
        
        self._story.add_segment(segment)
        return self
    
    def add_transition(
        self,
        transition_type: str = "fade",
        duration: float = 0.5,
    ) -> "StoryBuilder":
        """添加转场"""
        self._segment_counter += 1
        
        segment = VideoSegment(
            segment_id=f"trans_{self._segment_counter}",
            segment_type=SegmentType.TRANSITION,
            transition_type=transition_type,
            transition_duration=duration,
        )
        
        self._story.add_segment(segment)
        return self
    
    def build(self) -> StoryLine:
        """构建故事"""
        return self._story
    
    def reset(self) -> "StoryBuilder":
        """重置"""
        self._story = StoryLine()
        self._segment_counter = 0
        return self


# 便捷函数
def create_story(
    original_clips: List[Dict],
    ai_contents: List[str],
    title: str = "",
) -> StoryLine:
    """
    快速创建故事
    
    交替插入原片和 AI 内容
    
    Args:
        original_clips: 原片片段列表 [{"video": path, "start": 0, "end": 10}, ...]
        ai_contents: AI 内容列表 ["解说1", "解说2", ...]
        title: 标题
        
    Returns:
        StoryLine
    """
    builder = StoryBuilder()
    
    for i, clip in enumerate(original_clips):
        # 添加原片
        builder.add_original(
            source_video=clip["video"],
            start=clip.get("start", 0),
            end=clip.get("end", 10),
            description=clip.get("description", ""),
        )
        
        # 添加对应的 AI 内容 (如果有)
        if i < len(ai_contents):
            builder.add_narration(script=ai_contents[i])
        
        # 添加转场
        builder.add_transition("fade", 0.5)
    
    story = builder.build()
    story.title = title
    return story


__all__ = [
    "SegmentType",
    "VideoSegment",
    "StoryLine",
    "StoryBuilder",
    "create_story",
]
