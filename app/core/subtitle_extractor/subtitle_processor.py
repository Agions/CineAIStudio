#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字幕处理器
提供字幕后处理、合并、优化等功能
"""

import re
import time
from typing import List, Optional, Dict, Any, Tuple
from difflib import SequenceMatcher

from .subtitle_models import SubtitleSegment, SubtitleTrack, SubtitleExtractorResult


class SubtitleProcessor:
    """字幕处理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化字幕处理器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 配置参数
        self.merge_threshold = self.config.get('merge_threshold', 0.5)  # 合并阈值
        self.min_duration = self.config.get('min_duration', 0.3)  # 最小持续时间
        self.max_duration = self.config.get('max_duration', 10.0)  # 最大持续时间
        self.similarity_threshold = self.config.get('similarity_threshold', 0.8)  # 相似度阈值
        
        # 文本清理规则
        self.cleanup_patterns = [
            (r'\s+', ' '),  # 多个空格合并为一个
            (r'^[^\w\u4e00-\u9fff]+', ''),  # 移除开头的非文字字符
            (r'[^\w\u4e00-\u9fff]+$', ''),  # 移除结尾的非文字字符
            (r'[【】\[\]()（）]', ''),  # 移除括号
            (r'[.。]{2,}', '...'),  # 多个句号替换为省略号
        ]
    
    def process_extraction_result(self, result: SubtitleExtractorResult) -> SubtitleExtractorResult:
        """
        处理字幕提取结果
        
        Args:
            result: 原始提取结果
            
        Returns:
            处理后的结果
        """
        processed_result = SubtitleExtractorResult()
        processed_result.metadata = result.metadata.copy()
        processed_result.processing_time = result.processing_time
        
        try:
            for track in result.tracks:
                processed_track = self.process_track(track)
                if processed_track.segments:  # 只添加非空轨道
                    processed_result.add_track(processed_track)
            
            processed_result.success = True
            
        except Exception as e:
            processed_result.success = False
            processed_result.error_message = str(e)
        
        return processed_result
    
    def process_track(self, track: SubtitleTrack) -> SubtitleTrack:
        """
        处理单个字幕轨道
        
        Args:
            track: 原始字幕轨道
            
        Returns:
            处理后的字幕轨道
        """
        if not track.segments:
            return track
        
        # 1. 文本清理
        cleaned_segments = [self._clean_segment(seg) for seg in track.segments]
        
        # 2. 过滤空白和无效片段
        valid_segments = [seg for seg in cleaned_segments if self._is_valid_segment(seg)]
        
        # 3. 去重
        deduplicated_segments = self._remove_duplicates(valid_segments)
        
        # 4. 合并相近片段
        merged_segments = self._merge_nearby_segments(deduplicated_segments)
        
        # 5. 时间轴优化
        optimized_segments = self._optimize_timing(merged_segments)
        
        # 6. 文本后处理
        final_segments = [self._post_process_text(seg) for seg in optimized_segments]
        
        return SubtitleTrack(
            segments=final_segments,
            language=track.language,
            title=track.title,
            source=track.source
        )
    
    def _clean_segment(self, segment: SubtitleSegment) -> SubtitleSegment:
        """清理单个字幕片段"""
        text = segment.text
        
        # 应用清理规则
        for pattern, replacement in self.cleanup_patterns:
            text = re.sub(pattern, replacement, text)
        
        # 去除首尾空白
        text = text.strip()
        
        return SubtitleSegment(
            start_time=segment.start_time,
            end_time=segment.end_time,
            text=text,
            confidence=segment.confidence,
            speaker_id=segment.speaker_id,
            language=segment.language,
            style=segment.style
        )
    
    def _is_valid_segment(self, segment: SubtitleSegment) -> bool:
        """检查片段是否有效"""
        # 检查文本
        if not segment.text or len(segment.text.strip()) < 2:
            return False
        
        # 检查时间
        if segment.end_time <= segment.start_time:
            return False
        
        # 检查持续时间
        duration = segment.duration
        if duration < self.min_duration or duration > self.max_duration:
            return False
        
        # 检查置信度
        if segment.confidence < 0.3:
            return False
        
        return True
    
    def _remove_duplicates(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """去除重复片段"""
        if not segments:
            return segments
        
        unique_segments = []
        
        for segment in segments:
            is_duplicate = False
            
            for existing in unique_segments:
                # 检查时间重叠和文本相似度
                if self._segments_overlap(segment, existing):
                    similarity = self._text_similarity(segment.text, existing.text)
                    if similarity > self.similarity_threshold:
                        # 保留置信度更高的片段
                        if segment.confidence > existing.confidence:
                            unique_segments.remove(existing)
                            unique_segments.append(segment)
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_segments.append(segment)
        
        return sorted(unique_segments, key=lambda x: x.start_time)
    
    def _segments_overlap(self, seg1: SubtitleSegment, seg2: SubtitleSegment) -> bool:
        """检查两个片段是否重叠"""
        return not (seg1.end_time <= seg2.start_time or seg2.end_time <= seg1.start_time)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _merge_nearby_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """合并相近的片段"""
        if not segments:
            return segments
        
        merged_segments = []
        current_segment = segments[0]
        
        for next_segment in segments[1:]:
            # 计算间隔
            gap = next_segment.start_time - current_segment.end_time
            
            # 如果间隔小于阈值且是同一说话人，合并片段
            if (gap <= self.merge_threshold and 
                current_segment.speaker_id == next_segment.speaker_id):
                
                # 合并文本
                merged_text = f"{current_segment.text} {next_segment.text}"
                
                # 计算新的置信度（加权平均）
                total_duration = (current_segment.duration + next_segment.duration)
                new_confidence = (
                    (current_segment.confidence * current_segment.duration +
                     next_segment.confidence * next_segment.duration) / total_duration
                )
                
                current_segment = SubtitleSegment(
                    start_time=current_segment.start_time,
                    end_time=next_segment.end_time,
                    text=merged_text,
                    confidence=new_confidence,
                    speaker_id=current_segment.speaker_id,
                    language=current_segment.language
                )
            else:
                merged_segments.append(current_segment)
                current_segment = next_segment
        
        merged_segments.append(current_segment)
        return merged_segments
    
    def _optimize_timing(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """优化时间轴"""
        if not segments:
            return segments
        
        optimized_segments = []
        
        for i, segment in enumerate(segments):
            start_time = segment.start_time
            end_time = segment.end_time
            
            # 调整开始时间（避免与前一个片段重叠）
            if i > 0:
                prev_segment = segments[i-1]
                if start_time < prev_segment.end_time:
                    start_time = prev_segment.end_time + 0.1
            
            # 调整结束时间（避免与下一个片段重叠）
            if i < len(segments) - 1:
                next_segment = segments[i+1]
                if end_time > next_segment.start_time:
                    end_time = next_segment.start_time - 0.1
            
            # 确保最小持续时间
            if end_time - start_time < self.min_duration:
                end_time = start_time + self.min_duration
            
            optimized_segment = SubtitleSegment(
                start_time=start_time,
                end_time=end_time,
                text=segment.text,
                confidence=segment.confidence,
                speaker_id=segment.speaker_id,
                language=segment.language,
                style=segment.style
            )
            
            optimized_segments.append(optimized_segment)
        
        return optimized_segments
    
    def _post_process_text(self, segment: SubtitleSegment) -> SubtitleSegment:
        """文本后处理"""
        text = segment.text
        
        # 添加标点符号
        text = self._add_punctuation(text)
        
        # 文本纠错
        text = self._correct_text(text)
        
        # 格式化
        text = self._format_text(text)
        
        return SubtitleSegment(
            start_time=segment.start_time,
            end_time=segment.end_time,
            text=text,
            confidence=segment.confidence,
            speaker_id=segment.speaker_id,
            language=segment.language,
            style=segment.style
        )
    
    def _add_punctuation(self, text: str) -> str:
        """智能添加标点符号"""
        # 简单的标点符号添加逻辑
        text = text.strip()
        
        if not text:
            return text
        
        # 如果结尾没有标点符号，添加句号
        if text[-1] not in '。！？.!?':
            # 根据语调判断添加什么标点
            if '吗' in text or '呢' in text or text.endswith('?'):
                text += '？'
            elif '!' in text or '啊' in text or '哇' in text:
                text += '！'
            else:
                text += '。'
        
        return text
    
    def _correct_text(self, text: str) -> str:
        """文本纠错"""
        # 这里可以集成更复杂的文本纠错算法
        # 目前只做简单的替换
        corrections = {
            '的的': '的',
            '了了': '了',
            '是是': '是',
            '在在': '在',
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def _format_text(self, text: str) -> str:
        """格式化文本"""
        # 确保首字母大写（对于英文）
        if text and text[0].isalpha():
            text = text[0].upper() + text[1:]
        
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def merge_tracks(self, tracks: List[SubtitleTrack]) -> SubtitleTrack:
        """
        合并多个字幕轨道
        
        Args:
            tracks: 字幕轨道列表
            
        Returns:
            合并后的字幕轨道
        """
        if not tracks:
            return SubtitleTrack([], source="merged")
        
        if len(tracks) == 1:
            return tracks[0]
        
        # 收集所有片段
        all_segments = []
        for track in tracks:
            all_segments.extend(track.segments)
        
        # 按时间排序
        all_segments.sort(key=lambda x: x.start_time)
        
        # 去重和合并
        processed_segments = self._remove_duplicates(all_segments)
        processed_segments = self._merge_nearby_segments(processed_segments)
        
        return SubtitleTrack(
            segments=processed_segments,
            language=tracks[0].language,
            title="合并轨道",
            source="merged"
        )
    
    def split_by_speaker(self, track: SubtitleTrack) -> List[SubtitleTrack]:
        """
        按说话人分割字幕轨道
        
        Args:
            track: 原始字幕轨道
            
        Returns:
            按说话人分割的轨道列表
        """
        speaker_segments = {}
        
        for segment in track.segments:
            speaker_id = segment.speaker_id or "unknown"
            if speaker_id not in speaker_segments:
                speaker_segments[speaker_id] = []
            speaker_segments[speaker_id].append(segment)
        
        tracks = []
        for speaker_id, segments in speaker_segments.items():
            speaker_track = SubtitleTrack(
                segments=segments,
                language=track.language,
                title=f"说话人 {speaker_id}",
                source=track.source
            )
            tracks.append(speaker_track)
        
        return tracks
    
    def extract_keywords(self, track: SubtitleTrack, top_k: int = 10) -> List[Tuple[str, int]]:
        """
        提取关键词
        
        Args:
            track: 字幕轨道
            top_k: 返回前k个关键词
            
        Returns:
            关键词列表 [(词, 频次)]
        """
        # 合并所有文本
        all_text = " ".join(segment.text for segment in track.segments)
        
        # 简单的词频统计
        import jieba
        words = jieba.lcut(all_text)
        
        # 过滤停用词
        stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '这', '那', '有', '和', '与'}
        words = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 统计词频
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # 排序并返回前k个
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:top_k]
