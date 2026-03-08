#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
爆款字幕生成器
生成适合短视频的动态字幕
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import re


class CaptionStyle(Enum):
    """字幕风格"""
    STANDARD = "standard"       # 标准
    BOLD = "bold"             # 粗体醒目
    CINEMATIC = "cinematic"   # 电影感
    DYNAMIC = "dynamic"       # 动态弹出
    MINIMAL = "minimal"        # 简洁


@dataclass
class CaptionSegment:
    """字幕片段"""
    text: str
    start: float          # 开始时间(秒)
    end: float            # 结束时间(秒)
    style: str = "default"  # 样式
    position: str = "bottom"  # 位置


@dataclass  
class ViralCaptionConfig:
    """爆款字幕配置"""
    style: CaptionStyle = CaptionStyle.DYNAMIC
    
    # 字体
    font_name: str = "思源黑体"
    font_size: int = 32
    font_weight: str = "bold"
    
    # 颜色
    text_color: str = "#FFFFFF"
    stroke_color: str = "#000000"
    stroke_width: float = 2.0
    bg_color: str = ""
    bg_opacity: float = 0
    
    # 位置
    position: str = "bottom"
    margin_bottom: int = 80
    
    # 动画
    animation: str = "pop"  # pop/fade/slide
    animation_duration: float = 0.2
    
    # 特效
    highlight_words: List[str] = field(default_factory=list)
    highlight_color: str = "#FFD700"  # 金色高亮


class ViralCaptionGenerator:
    """
    爆款字幕生成器
    
    生成适合短视频平台的动态字幕
    """
    
    # 字幕模板
    TEMPLATES = {
        "hook": {
            "animation": "pop",
            "font_size": 36,
            "stroke_width": 3,
            "highlight_color": "#FF6B6B",
        },
        "emphasis": {
            "animation": "scale",
            "font_size": 34,
            "stroke_width": 2.5,
            "highlight_color": "#FFD700",
        },
        "normal": {
            "animation": "fade",
            "font_size": 30,
            "stroke_width": 2,
            "highlight_color": "#FFFFFF",
        },
        "cta": {
            "animation": "pop",
            "font_size": 32,
            "stroke_width": 2,
            "highlight_color": "#4ECDC4",
        },
    }
    
    def __init__(self):
        self._config = ViralCaptionConfig()
    
    def set_config(self, config: ViralCaptionConfig):
        """设置配置"""
        self._config = config
    
    def generate_from_script(
        self, 
        script: str,
        duration: float,
    ) -> List[CaptionSegment]:
        """
        从脚本生成字幕
        
        Args:
            script: 视频脚本
            duration: 总时长(秒)
            
        Returns:
            字幕片段列表
        """
        segments = []
        
        # 分割脚本为句子
        sentences = self._split_sentences(script)
        
        # 计算每句时长
        avg_duration = duration / len(sentences) if sentences else 2.0
        
        current_time = 0.0
        for i, sentence in enumerate(sentences):
            # 确定类型
            if i == 0:
                caption_type = "hook"
            elif i == len(sentences) - 1:
                caption_type = "cta"
            elif self._is_emphasis(sentence):
                caption_type = "emphasis"
            else:
                caption_type = "normal"
            
            # 创建字幕片段
            segment = CaptionSegment(
                text=sentence,
                start=current_time,
                end=current_time + avg_duration,
                style=caption_type,
                position=self._config.position,
            )
            
            segments.append(segment)
            current_time += avg_duration
        
        return segments
    
    def _split_sentences(self, script: str) -> List[str]:
        """分割句子"""
        # 清理脚本
        script = script.strip()
        
        # 按标点分割
        sentences = re.split(r'[。！？\n]', script)
        
        # 过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 合并过短的句子
        merged = []
        current = ""
        
        for s in sentences:
            if len(current) + len(s) < 30:
                current += s
            else:
                if current:
                    merged.append(current)
                current = s
        
        if current:
            merged.append(current)
        
        return merged if merged else sentences[:10]  # 至少10句
    
    def _is_emphasis(self, text: str) -> bool:
        """判断是否需要强调"""
        emphasis_keywords = [
            "一定", "必须", "记住", "注意", "关键",
            "重点", "特别", "竟然", "没想到", "竟然",
            "!", "！", "?", "？",
        ]
        return any(kw in text for kw in emphasis_keywords)
    
    def add_highlights(
        self, 
        segments: List[CaptionSegment],
    ) -> List[CaptionSegment]:
        """添加关键词高亮"""
        for segment in segments:
            # 查找关键词
            for keyword in self._config.highlight_words:
                if keyword in segment.text:
                    # 添加高亮标记
                    segment.text = segment.text.replace(
                        keyword,
                        f"[HL]{keyword}[/HL]"
                    )
        
        return segments
    
    def generate_ass(
        self, 
        segments: List[CaptionSegment],
    ) -> str:
        """
        生成 ASS 字幕格式
        
        Args:
            segments: 字幕片段
            
        Returns:
            ASS 格式字幕
        """
        ass_lines = [
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 1920",
            "PlayResY: 1080",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,{self._config.font_name},{self._config.font_size}&H{self._config.text_color[1:]}&,{self._config.stroke_color[1:]}&,{self._config.stroke_width},0,{1 if self._config.font_weight == 'bold' else 0},0,0,0,100,100,0,0,1,{self._config.stroke_width},0,2,20,20,20,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
        
        for segment in segments:
            start_time = self._format_ass_time(segment.start)
            end_time = self._format_ass_time(segment.end)
            
            # 处理高亮
            text = segment.text
            if "[HL]" in text:
                text = text.replace("[HL]", "{\\c&HFFD700&}")
                text = text.replace("[/HL]", "{\\c&HFFFFFF&}")
            
            ass_lines.append(
                f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}"
            )
        
        return "\n".join(ass_lines)
    
    def generate_srt(
        self, 
        segments: List[CaptionSegment],
    ) -> str:
        """生成 SRT 字幕格式"""
        lines = []
        
        for i, segment in enumerate(segments, 1):
            # 序号
            lines.append(str(i))
            
            # 时间
            start_time = self._format_srt_time(segment.start)
            end_time = self._format_srt_time(segment.end)
            lines.append(f"{start_time} --> {end_time}")
            
            # 内容
            lines.append(segment.text)
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_ass_time(self, seconds: float) -> str:
        """格式化 ASS 时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        centisecs = int((secs - int(secs)) * 100)
        return f"{hours}:{minutes:02d}:{int(secs):02d}.{centisecs:02d}"
    
    def _format_srt_time(self, seconds: float) -> str:
        """格式化 SRT 时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        millisecs = int((secs - int(secs)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def generate_word_timestamps(
        self,
        text: str,
        duration: float,
    ) -> List[Dict]:
        """
        生成每个词的时间戳
        
        Args:
            text: 文本
            duration: 总时长
            
        Returns:
            [{word, start, end}, ...]
        """
        # 简单按字符分割
        words = list(text)
        
        if not words:
            return []
        
        word_duration = duration / len(words)
        
        timestamps = []
        current_time = 0.0
        
        for word in words:
            timestamps.append({
                "word": word,
                "start": current_time,
                "end": current_time + word_duration,
            })
            current_time += word_duration
        
        return timestamps


# 全局实例
_caption_generator = ViralCaptionGenerator()


def generate_viral_captions(
    script: str,
    duration: float,
    style: str = "dynamic",
) -> List[CaptionSegment]:
    """生成爆款字幕"""
    config = ViralCaptionConfig(
        style=CaptionStyle[style.upper()],
    )
    _caption_generator.set_config(config)
    return _caption_generator.generate_from_script(script, duration)


def export_captions_ass(segments: List[CaptionSegment]) -> str:
    """导出 ASS 字幕"""
    return _caption_generator.generate_ass(segments)


def export_captions_srt(segments: List[CaptionSegment]) -> str:
    """导出 SRT 字幕"""
    return _caption_generator.generate_srt(segments)


__all__ = [
    "CaptionStyle",
    "CaptionSegment",
    "ViralCaptionConfig",
    "ViralCaptionGenerator",
    "generate_viral_captions",
    "export_captions_ass",
    "export_captions_srt",
]
